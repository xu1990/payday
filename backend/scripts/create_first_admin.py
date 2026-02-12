"""
首次部署时创建默认管理员。
使用环境变量 ADMIN_DEFAULT_PASSWORD 指定密码，否则随机生成。
在 backend 目录执行: python3 scripts/create_first_admin.py
"""
import os
import sys
import secrets
import string

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.admin import AdminUser
from app.models.user import gen_uuid


def generate_random_password(length=16):
    """生成安全的随机密码"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def main():
    db = SessionLocal()
    try:
        existing = db.query(AdminUser).filter(AdminUser.username == "admin").first()
        if existing:
            print("管理员 admin 已存在，跳过创建。")
            return

        # 从环境变量读取密码，或生成随机密码
        default_password = os.getenv("ADMIN_DEFAULT_PASSWORD")
        if not default_password:
            default_password = generate_random_password()
            print("=" * 60)
            print("首次部署：随机生成的管理员密码")
            print("=" * 60)
            print(f"用户名: admin")
            print(f"密码: {default_password}")
            print("=" * 60)
            print("⚠️  请妥善保管此密码，首次登录后请立即修改！")
            print("=" * 60)

            # 同时保存到文件供管理员查看
            password_file = "admin_password.txt"
            with open(password_file, "w") as f:
                f.write(f"管理员账号信息\n")
                f.write(f"=" * 30 + "\n")
                f.write(f"用户名: admin\n")
                f.write(f"密码: {default_password}\n")
                f.write(f"\n请登录后立即修改密码，并删除此文件。\n")
            print(f"密码已保存到: {password_file}")

        admin = AdminUser(
            id=gen_uuid(),
            username="admin",
            password_hash=hash_password(default_password),
        )
        db.add(admin)
        db.commit()
        print("✓ 管理员账户创建成功")
    finally:
        db.close()


if __name__ == "__main__":
    main()
