from app.database import engine, SessionLocal, Base
from app.models.user import User, UserRole
from app.core.security import hash_password

def init():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        admin = User(
            username="admin",
            hashed_password=hash_password("admin"),
            role=UserRole.admin,
        )
        db.add(admin)
        db.commit()
        print("默认管理员账号已创建: admin / admin")
    else:
        print("管理员账号已存在，跳过")
    db.close()

if __name__ == "__main__":
    init()
