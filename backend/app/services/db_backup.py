"""
SQLite 数据库持久化（微信云托管容器重建兜底）。

微信云托管容器每次重建/缩容到 0 后，/var/lib 下的 SQLite 文件会丢失。
这里把数据库定期备份到「对象存储」（管理端文件，openid 留空），
冷启动时若本地库不存在则先从对象存储恢复，实现数据随容器重建保留。

依赖前置条件（同 cloud_storage.py）：
  1. 云托管服务已开启「开放接口服务」（服务管理 → 云调用 → 开放接口服务）。
  2. 微信令牌配置白名单已加入：
       /_/cos/getauth
       /_/cos/metaid/encode
  3. CLOUD_STORAGE_BUCKET / CLOUD_STORAGE_REGION 环境变量已配置。

未开启时所有调用都会优雅降级（记 warning 日志），不影响服务启动。
"""

import asyncio
import logging
import os
import shutil
import sqlite3
from pathlib import Path

from app.core.config import get_settings
from app.services import cloud_storage

logger = logging.getLogger(__name__)


def _db_path() -> Path | None:
    """从 DATABASE_URL 解析 SQLite 文件路径；非 SQLite 返回 None。"""
    url = get_settings().DATABASE_URL
    if not url.startswith("sqlite"):
        return None
    # sqlite+aiosqlite:////var/... -> /var/... ；sqlite:///./x.db -> ./x.db
    rest = url.split(":///", 1)[-1]
    if rest.startswith("//"):
        rest = rest[1:]
    return Path(rest) if rest else None


def _enabled() -> bool:
    settings = get_settings()
    if not settings.DB_BACKUP_ENABLED:
        return False
    if not (settings.CLOUD_STORAGE_BUCKET or "").strip():
        return False
    return _db_path() is not None


async def restore_db_from_cos() -> bool:
    """冷启动恢复：本地库不存在时从对象存储拉取备份。"""
    if not _enabled():
        return False
    path = _db_path()
    if path is None or path.exists():
        return False
    try:
        data = await cloud_storage.download_file(get_settings().DB_BACKUP_KEY)
    except Exception as e:
        logger.warning(
            "DB 备份恢复失败（若刚开启开放接口服务需重建版本后生效）: %s",
            e,
        )
        return False
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + ".restore")
        tmp.write_bytes(data)
        shutil.move(str(tmp), str(path))
        logger.info("✅ SQLite 数据库已从对象存储恢复: %s", path)
        return True
    except Exception as e:
        logger.warning("DB 备份恢复落盘失败: %s", e)
        return False


def _snapshot(path: Path, tmp: Path) -> None:
    """用 SQLite backup API 生成一致快照（避免复制到半事务状态）。"""
    src = sqlite3.connect(str(path))
    dst = sqlite3.connect(str(tmp))
    try:
        with dst:
            src.backup(dst)
    finally:
        dst.close()
        src.close()


async def backup_db_to_cos() -> bool:
    """把当前 SQLite 数据库快照上传到对象存储。"""
    if not _enabled():
        return False
    path = _db_path()
    if path is None or not path.exists():
        return False
    tmp = path.with_name(path.name + ".bak")
    try:
        await asyncio.to_thread(_snapshot, path, tmp)
        data = tmp.read_bytes()
        await cloud_storage.upload_bytes(
            get_settings().DB_BACKUP_KEY,
            data,
            openid="",
        )
        logger.info("💾 SQLite 数据库已备份到对象存储 (%d bytes)", len(data))
        return True
    except Exception as e:
        logger.warning("SQLite 数据库备份失败: %s", e)
        return False
    finally:
        tmp.unlink(missing_ok=True)


async def backup_loop() -> None:
    """后台周期备份任务（随 FastAPI lifespan 启停）。"""
    settings = get_settings()
    interval = max(30, settings.DB_BACKUP_INTERVAL_SECONDS)
    while True:
        await asyncio.sleep(interval)
        try:
            await backup_db_to_cos()
        except Exception as e:
            logger.warning("周期备份异常: %s", e)
