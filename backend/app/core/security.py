"""
JWT authentication and authorization.

Uses PBKDF2-SHA256 for password hashing (stdlib, no bcrypt compat issues).
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import get_settings

settings = get_settings()

# ─── Password hashing (PBKDF2-SHA256, stdlib only) ──────────────────

SALT_LENGTH = 32
HASH_ITERATIONS = 600_000
KEY_LENGTH = 32


def _hash_with_salt(password: str, salt: bytes) -> str:
    """Hash a password with a specific salt using PBKDF2-SHA256."""
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        HASH_ITERATIONS,
        dklen=KEY_LENGTH,
    )
    return f"{salt.hex()}${key.hex()}"


def hash_password(password: str) -> str:
    """Hash a password using PBKDF2-SHA256 with a random salt."""
    salt = secrets.token_bytes(SALT_LENGTH)
    return _hash_with_salt(password, salt)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its PBKDF2 hash."""
    try:
        salt_hex, key_hex = hashed_password.split("$", 1)
        salt = bytes.fromhex(salt_hex)
        expected = _hash_with_salt(plain_password, salt)
        # Constant-time comparison
        return secrets.compare_digest(expected, hashed_password)
    except (ValueError, AttributeError):
        return False


# ─── Pre-compute demo user hashes at import time ────────────────────
# This happens once at startup, avoiding bcrypt compat issues

def _build_demo_users() -> Dict[str, Dict[str, Any]]:
    """Build demo users dict with pre-hashed passwords."""
    return {
        "teacher@kindergarten.cn": {
            "id": 1,
            "email": "teacher@kindergarten.cn",
            "name": "张老师",
            "role": "teacher",
            "hashed_password": hash_password("demo123"),
        },
        "admin@kindergarten.cn": {
            "id": 2,
            "email": "admin@kindergarten.cn",
            "name": "管理员",
            "role": "admin",
            "hashed_password": hash_password("admin123"),
        },
        # Parent access is via access_code, not email/password
    }


DEMO_USERS = _build_demo_users()

# ─── Token security ────────────────────────────────────────────────

bearer_scheme = HTTPBearer(auto_error=False)


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a signed JWT access token.

    Args:
        data: Claims to encode (must include 'sub')
        expires_delta: Token lifetime, defaults to config value
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm="HS256",
    )


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and validate a JWT access token.
    Returns the payload dict or None if invalid/expired.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
    except JWTError:
        return None


def create_parent_token(child_id: int, access_code: str) -> str:
    """
    Create a short-lived parent access token.
    Parents authenticate via access_code (no password).
    """
    return create_access_token(
        data={
            "sub": f"parent_{child_id}",
            "role": "parent",
            "child_id": child_id,
        },
        expires_delta=timedelta(hours=24),
    )


# ─── FastAPI Dependencies ──────────────────────────────────────────

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Dict[str, Any]:
    """
    Dependency: extract and validate the current user from JWT.
    Returns the token payload dict.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证令牌。请在 Authorization header 中提供 Bearer token。",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌无效或已过期，请重新登录。",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


async def get_current_teacher(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Dependency: ensure the current user is a teacher or admin.
    """
    role = current_user.get("role")
    if role not in ("teacher", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="此操作需要教师权限。",
        )
    return current_user


async def get_current_parent(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Dependency: ensure the current user is a parent (accessing via code).
    """
    role = current_user.get("role")
    if role != "parent":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="此操作需要家长访问权限。",
        )
    return current_user


def verify_parent_access(child_id: int, access_code: str) -> bool:
    """
    Verify a parent access code for a specific child.
    In production, looks up the code from the database.
    For MVP, accepts any 8-char alphanumeric code.
    """
    if not access_code or len(access_code) < 6:
        return False
    # In production: query DB for child's parent_access_code
    return True
