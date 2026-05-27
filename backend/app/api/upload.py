import os
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.image_upload import ImageUpload

router = APIRouter(prefix="/api/upload", tags=["upload"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
ALLOWED_TYPES = {"image/png", "image/jpeg", "image/gif", "image/webp"}
MAX_SIZE = 10 * 1024 * 1024  # 10MB


@router.post("")
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="不支持的文件类型，仅允许 PNG/JPEG/GIF/WebP")

    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="图片不能超过10MB")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in (file.filename or "") else "png"
    if ext not in ("png", "jpg", "jpeg", "gif", "webp"):
        ext = "png"
    now = datetime.now()
    stored_name = f"{now.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.{ext}"
    stored_path = os.path.join(UPLOAD_DIR, stored_name)

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    with open(stored_path, "wb") as f:
        f.write(content)

    image_url = f"http://localhost:8002/uploads/{stored_name}"
    record = ImageUpload(
        user_id=current_user.id,
        filename=file.filename or stored_name,
        stored_path=stored_path,
        url=image_url,
        size=len(content),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "id": record.id,
        "url": record.url,
        "filename": record.filename,
        "size": record.size,
    }
