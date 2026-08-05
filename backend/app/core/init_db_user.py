"""
启动时执行：建专用 mathsprout 数据库用户（替换 root 账户）。

⚠️ 仅在 DATABASE_URL 是 mysql:// 形式且为 root 连接时执行；
  首次执行成功后，应把 DATABASE_URL 切到新用户的 URL。
  这是安全改进（生产不应一直用 root）。
"""
import logging
import os
import re

logger = logging.getLogger("mathsprout.init_db_user")

USER_NAME = "mathsprout"
USER_PASSWORD = "Msprout2026X"
DB_NAME = "mathsprout"


async def ensure_db_user():
    """如果用 root 连 MySQL 且 mathsprout 用户不存在，自动创建并赋权。

    跳过条件：
      - DATABASE_URL 不是 mysql+asyncmy 开头
      - URL 里已经是 mathsprout 用户
      - mathsprout 用户已存在
    """
    from app.core.config import get_settings
    settings = get_settings()
    url = settings.DATABASE_URL
    if "mysql+asyncmy" not in url:
        logger.info("Not MySQL, skip user init")
        return
    if f":{USER_PASSWORD}@" in url or f":{USER_NAME}:" in url:
        logger.info(f"Already using user {USER_NAME}, skip")
        return

    # 解析 root 连接信息
    m = re.search(r"mysql\+asyncmy://([^:]+):([^@]+)@([^:/]+):?(\d*)/(\w+)", url)
    if not m or m.group(1) != "root":
        logger.info(f"Not root connection ({m.group(1) if m else 'unparsed'}), skip")
        return

    user, password, host, port, db = m.group(1), m.group(2), m.group(3), m.group(4) or "3306", m.group(5)
    logger.info(f"Ensuring mathsprout user exists on {host}:{port}/{db}")

    # 用 asyncmy 直连（不通过 SQLAlchemy，root 连接）
    import asyncmy
    conn = await asyncmy.connect(host=host, port=int(port), user=user, password=password, db=db)
    try:
        async with conn.cursor() as cur:
            # 检查用户是否存在
            await cur.execute(
                f"SELECT COUNT(*) FROM mysql.user WHERE user = %s AND host = %s",
                (USER_NAME, "%"),
            )
            exists = (await cur.fetchone())[0] > 0
            if not exists:
                await cur.execute(
                    f"CREATE USER %s@'%%' IDENTIFIED BY %s",
                    (USER_NAME, USER_PASSWORD),
                )
                logger.info(f"Created user {USER_NAME}@'%%'")
            else:
                logger.info(f"User {USER_NAME}@'%%' already exists")
            # 赋权
            await cur.execute(
                f"GRANT ALL PRIVILEGES ON {db}.* TO %s@'%%'",
                (USER_NAME,),
            )
            await cur.execute("FLUSH PRIVILEGES")
            logger.info(f"Granted ALL on {db} to {USER_NAME}@'%%'")
        await conn.commit()
    finally:
        await conn.close()
    logger.info("✓ mathsprout user ready. Update DATABASE_URL to use this user.")
