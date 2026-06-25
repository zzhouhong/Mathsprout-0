"""
Authentication API routes.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr
from typing import Optional

from app.core.security import (
    DEMO_USERS,
    verify_password,
    create_access_token,
    create_parent_token,
    verify_parent_access,
    get_current_user,
    get_current_teacher,
)

router = APIRouter()


# ─── Request Schemas ────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: str
    password: str


class ParentAccessRequest(BaseModel):
    access_code: str
    child_id: Optional[int] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


# ─── Routes ─────────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
async def teacher_login(request: LoginRequest):
    """
    Teacher/admin login with email + password.

    Demo credentials:
    - teacher@kindergarten.cn / demo123
    - admin@kindergarten.cn / admin123
    """
    user = DEMO_USERS.get(request.email)
    if not user or not verify_password(request.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误。",
        )

    token = create_access_token(
        data={
            "sub": request.email,
            "user_id": user["id"],
            "name": user["name"],
            "role": user["role"],
        }
    )

    return TokenResponse(
        access_token=token,
        user={
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "role": user["role"],
        },
    )


@router.post("/parent", response_model=TokenResponse)
async def parent_access(request: ParentAccessRequest):
    """
    Parent access via access code (no password required).
    The access code is provided by the teacher.
    """
    if not verify_parent_access(request.child_id or 0, request.access_code):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="访问码无效。请联系老师获取正确的访问码。",
        )

    token = create_parent_token(
        child_id=request.child_id or 0,
        access_code=request.access_code,
    )

    return TokenResponse(
        access_token=token,
        user={
            "role": "parent",
            "child_id": request.child_id,
        },
    )


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    Get current authenticated user info.
    """
    return {
        "authenticated": True,
        "user": {
            "sub": current_user.get("sub"),
            "role": current_user.get("role"),
            "name": current_user.get("name"),
            "user_id": current_user.get("user_id"),
        },
    }


@router.get("/verify")
async def verify_token(current_user: dict = Depends(get_current_teacher)):
    """
    Verify the current token is valid (teacher only).
    Useful for frontend auth guards.
    """
    return {
        "valid": True,
        "user": current_user,
    }
