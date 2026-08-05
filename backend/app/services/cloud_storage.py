"""
微信云托管对象存储访问（COS-SDK）。

小程序侧拍照后先 wx.cloud.uploadFile 到对象存储拿到 fileID，
后端容器通过「开放接口服务」获取临时密钥，再使用 COS SDK 读取文件字节。

依赖前置条件：
  1. 云托管服务已开启「开放接口服务」（服务管理 → 云调用 → 开放接口服务）。
  2. 环境变量 CLOUD_STORAGE_BUCKET 指向当前环境的存储桶
     （如 7072-prod-d6gj3mfkye02c4455-1462714319）。
"""

import asyncio
import logging

import httpx
from qcloud_cos import CosConfig, CosS3Client

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# 容器内部可达的开放接口服务地址（获取 COS 临时密钥）
# 注意：http 会 301 到 https，httpx 需显式 follow_redirects
_GETAUTH_URL = "https://api.weixin.qq.com/_/cos/getauth"
_METAID_URL = "https://api.weixin.qq.com/_/cos/metaid/encode"


async def _get_temp_credentials() -> dict:
    """通过开放接口服务获取 COS 临时密钥。"""
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        resp = await client.get(_GETAUTH_URL)
        resp.raise_for_status()
        data = resp.json()

    tmp_secret_id = data.get("TmpSecretId") or data.get("tmpSecretId")
    tmp_secret_key = data.get("TmpSecretKey") or data.get("tmpSecretKey")
    token = data.get("Token") or data.get("token")
    if not (tmp_secret_id and tmp_secret_key and token):
        raise RuntimeError(
            f"开放接口服务返回异常，无法获取 COS 临时密钥: {data}"
        )
    return {
        "secret_id": tmp_secret_id,
        "secret_key": tmp_secret_key,
        "token": token,
    }


def _parse_key(file_id_or_key: str) -> str:
    """把 wx.cloud.uploadFile 返回的 fileID 解析成 COS 对象键。

    fileID 形如:
        cloud://prod-d6gj3mfkye02c4455.7072-prod-d6gj3mfkye02c4455-1462714319/uploads/xxx.jpg
    COS 键为:
        uploads/xxx.jpg

    也兼容直接传对象键（用于测试/管理端上传）。
    """
    s = file_id_or_key.strip()
    if s.startswith("cloud://"):
        s = s[len("cloud://"):]
        # cloud:// 之后「第一个 /」之前是 env.bucket 前缀，之后才是对象键
        if "/" in s:
            return s.split("/", 1)[1]
        return ""
    return s.lstrip("/")


async def _get_meta_id(bucket: str, key: str, openid: str = "") -> str:
    """通过开放接口服务获取文件元数据（x-cos-meta-fileid），服务端上传必须携带。

    openid 留空表示管理端文件；管理端上传的文件小程序端默认不可读写，
    仅管理端（SDK/服务端）可修改，符合备份文件的权限预期。
    """
    path = f"/{key.lstrip('/')}"
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        resp = await client.post(
            _METAID_URL,
            json={"openid": openid, "bucket": bucket, "paths": [path]},
        )
        resp.raise_for_status()
        data = resp.json()
    try:
        return data["respdata"]["x_cos_meta_field_strs"][0]
    except (KeyError, IndexError, TypeError) as e:
        raise RuntimeError(f"获取文件元数据失败: {data}") from e


def _make_client(creds: dict) -> CosS3Client:
    settings = get_settings()
    config = CosConfig(
        Region=settings.CLOUD_STORAGE_REGION,
        SecretId=creds["secret_id"],
        SecretKey=creds["secret_key"],
        Token=creds["token"],
        Scheme="https",
    )
    return CosS3Client(config)


async def download_file(file_id_or_key: str) -> bytes:
    """按 fileID（或对象键）从云托管对象存储下载文件字节。"""
    settings = get_settings()
    bucket = (settings.CLOUD_STORAGE_BUCKET or "").strip()
    if not bucket:
        raise RuntimeError("CLOUD_STORAGE_BUCKET 未配置，无法读取云托管对象存储。")

    key = _parse_key(file_id_or_key)
    if not key:
        raise ValueError(f"无法从 fileID 解析对象键: {file_id_or_key!r}")

    creds = await _get_temp_credentials()
    client = _make_client(creds)

    def _get():
        resp = client.get_object(Bucket=bucket, Key=key)
        body = resp.get("Body")
        if hasattr(body, "get_raw_stream"):
            return body.get_raw_stream().read()
        if hasattr(body, "get_stream"):
            return b"".join(body.get_stream())
        return b"".join(body) if body else b""

    data = await asyncio.to_thread(_get)
    if not data:
        raise RuntimeError(f"对象存储中未读到文件内容: {key}")
    return data


async def upload_bytes(key: str, data: bytes, openid: str = "") -> bool:
    """把字节流上传到云托管对象存储（管理端，openid 留空）。"""
    settings = get_settings()
    bucket = (settings.CLOUD_STORAGE_BUCKET or "").strip()
    if not bucket:
        raise RuntimeError("CLOUD_STORAGE_BUCKET 未配置，无法写入云托管对象存储。")
    if not key:
        raise ValueError("对象键不能为空。")

    creds, meta_id = await asyncio.gather(
        _get_temp_credentials(),
        _get_meta_id(bucket, key, openid=openid),
    )
    client = _make_client(creds)

    def _put():
        resp = client.put_object(
            Bucket=bucket,
            Key=key.lstrip("/"),
            Body=data,
            ContentLength=len(data),
            StorageClass="STANDARD",
            Headers={"x-cos-meta-fileid": meta_id},
        )
        return resp.get("ETag") is not None

    ok = await asyncio.to_thread(_put)
    if not ok:
        raise RuntimeError(f"对象存储写入失败: {key}")
    return True


async def download_url(url: str) -> bytes:
    """从公网/内网 URL 下载文件字节。

    小程序侧 wx.cloud.getTempFileURL 生成的临时访问链接（*.tcb.qcloud.la）
    可被任意 HTTP 客户端读取，绕开「开放接口服务」开关。
    """
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        resp = await client.get(url)
        resp.raise_for_status()
    if not resp.content:
        raise RuntimeError(f"URL 未返回文件内容: {url[:80]}")
    return resp.content
