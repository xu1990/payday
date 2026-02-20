"""
检查并修复管理员角色
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.admin import AdminUser


def main():
    db = SessionLocal()
    try:
        admins = db.query(AdminUser).all()
        print(f"数据库中共有 {len(admins)} 个管理员账户：")
        print("-" * 60)

        for admin in admins:
            print(f"ID: {admin.id}")
            print(f"用户名: {admin.username}")
            print(f"角色: {admin.role}")
            print(f"启用状态: {admin.is_active}")
            print(f"创建时间: {admin.created_at}")
            print("-" * 60)

            # 修复缺失的角色
            if not admin.role or admin.role not in ["superadmin", "admin", "readonly"]:
                print(f"⚠️  检测到无效角色: '{admin.role}'，修复为 'admin'")
                admin.role = "admin"
                db.commit()
                print(f"✓ 已修复")

        print("\n建议：")
        print("1. 如果所有管理员的 role 都是 NULL 或无效值，请运行修复脚本")
        print("2. 确保 role 字段值为: superadmin, admin, 或 readonly")

    finally:
        db.close()


if __name__ == "__main__":
    main()
