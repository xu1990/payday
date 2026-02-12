"""
首次部署时创建默认管理员（username=admin, password=changeme）。
在 backend 目录执行: python3 scripts/create_first_admin.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.admin import AdminUser
from app.models.user import gen_uuid


def main():
    db = SessionLocal()
    try:
        existing = db.query(AdminUser).filter(AdminUser.username == "admin").first()
        if existing:
            print("管理员 admin 已存在，跳过创建。")
            return
        admin = AdminUser(
            id=gen_uuid(),
            username="admin",
            password_hash=hash_password("changeme"),
        )
        db.add(admin)
        db.commit()
        print("已创建默认管理员: 用户名=admin, 密码=changeme，请首次登录后修改密码。")
    finally:
        db.close()


if __name__ == "__main__":
    main()
