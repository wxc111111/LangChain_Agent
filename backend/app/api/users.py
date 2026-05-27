from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.user import UserCreateRequest, UserResponse, UserListResponse
from app.core.security import hash_password
from app.core.deps import require_admin

router = APIRouter(prefix="/api/users", tags=["users"])


@router.post("", response_model=UserResponse)
def create_user(body: UserCreateRequest, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    existing = db.query(User).filter(User.username == body.username).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已存在")
    if body.role not in ("admin", "user"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="角色只能是admin或user")

    user = User(
        username=body.username,
        hashed_password=hash_password(body.password),
        role=UserRole(body.role),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserResponse(
        id=user.id,
        username=user.username,
        role=user.role.value,
        is_active=user.is_active,
        created_at=user.created_at,
    )


@router.get("", response_model=UserListResponse)
def list_users(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: str = Query("", max_length=50),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    query = db.query(User)
    if search:
        query = query.filter(User.username.contains(search))
    total = query.count()
    items = query.order_by(User.id.desc()).offset((page - 1) * size).limit(size).all()
    return UserListResponse(
        total=total,
        items=[
            UserResponse(id=u.id, username=u.username, role=u.role.value, is_active=u.is_active, created_at=u.created_at)
            for u in items
        ],
    )


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    return UserResponse(
        id=user.id,
        username=user.username,
        role=user.role.value,
        is_active=user.is_active,
        created_at=user.created_at,
    )
