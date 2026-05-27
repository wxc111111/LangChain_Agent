from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, RefreshRequest, AccessTokenResponse
from app.core.security import verify_password, create_access_token, create_refresh_token, decode_token
from app.core.redis_client import save_refresh_token, get_refresh_token, delete_refresh_token
from app.core.deps import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == body.username).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="账号已被禁用")

    token_data = {"sub": str(user.id), "username": user.username, "role": user.role.value}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    save_refresh_token(refresh_token, token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user={"id": user.id, "username": user.username, "role": user.role.value},
    )


@router.post("/refresh", response_model=AccessTokenResponse)
def refresh(body: RefreshRequest):
    try:
        payload = decode_token(body.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的refresh token")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的refresh token")

    stored = get_refresh_token(body.refresh_token)
    if not stored:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="refresh token已失效")

    new_token_data = {"sub": payload["sub"], "username": payload["username"], "role": payload["role"]}
    access_token = create_access_token(new_token_data)
    return AccessTokenResponse(access_token=access_token)


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    return {"message": "已登出"}


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "role": current_user.role.value,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
    }
