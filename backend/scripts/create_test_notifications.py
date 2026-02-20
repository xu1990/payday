"""
创建测试通知数据 - 用于开发/测试环境
在 backend 目录执行: python3 scripts/create_test_notifications.py

这个脚本会创建各种类型的测试通知，用于验证通知功能。
"""
import os
import sys
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.user import User
from app.models.post import Post
from app.models.comment import Comment
from app.models.notification import Notification
from sqlalchemy import select


def create_test_notifications():
    """创建测试通知数据"""
    db = SessionLocal()

    try:
        # 获取第一个用户（通常是测试用户）
        result = db.execute(select(User).limit(1))
        user = result.scalar_one_or_none()

        if not user:
            print("❌ 数据库中没有用户，请先创建用户")
            return

        print(f"✓ 找到用户: {user.id} ({user.nickname or user.anonymous_name})")

        # 创建测试通知
        notifications = [
            {
                "type": "comment",
                "title": "新评论",
                "content": "张三评论了你的帖子：这个薪资待遇不错！",
                "related_id": None,
            },
            {
                "type": "reply",
                "title": "新回复",
                "content": "李四回复了你的评论：确实如此",
                "related_id": None,
            },
            {
                "type": "like",
                "title": "新点赞",
                "content": "王五点赞了你的帖子",
                "related_id": None,
            },
            {
                "type": "like",
                "title": "新点赞",
                "content": "赵六点赞了你的评论",
                "related_id": None,
            },
            {
                "type": "system",
                "title": "系统通知",
                "content": "欢迎来到薪日 PayDay！记得按时发薪哦~",
                "related_id": None,
            },
            {
                "type": "system",
                "title": "会员权益",
                "content": "您的会员权益即将到期，请及时续费",
                "related_id": None,
            },
        ]

        created_count = 0
        for notif_data in notifications:
            notification = Notification(
                user_id=user.id,
                type=notif_data["type"],
                title=notif_data["title"],
                content=notif_data["content"],
                related_id=notif_data["related_id"],
                is_read=False,  # 默认未读
            )
            db.add(notification)
            created_count += 1

        db.commit()
        print(f"✓ 成功创建 {created_count} 条测试通知")

        # 验证创建结果
        result = db.execute(
            select(Notification).where(Notification.user_id == user.id)
        )
        all_notifications = result.scalars().all()
        print(f"\n当前用户共有 {len(all_notifications)} 条通知")

        # 统计未读数
        result = db.execute(
            select(Notification).where(
                Notification.user_id == user.id,
                Notification.is_read == False
            )
        )
        unread = result.scalars().all()
        print(f"其中未读: {len(unread)} 条")

        # 显示最新的5条通知
        result = db.execute(
            select(Notification)
            .where(Notification.user_id == user.id)
            .order_by(Notification.created_at.desc())
            .limit(5)
        )
        latest = result.scalars().all()
        print("\n最新的5条通知:")
        for notif in latest:
            read_status = "已读" if notif.is_read else "未读"
            print(f"  [{read_status}] {notif.type} - {notif.title}")
            if notif.content:
                print(f"    {notif.content}")

    except Exception as e:
        print(f"❌ 创建测试通知失败: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


async def create_realistic_notifications():
    """创建真实场景的通知（需要有多用户和帖子数据）"""
    db = SessionLocal()

    try:
        # 获取所有用户
        result = await db.execute(select(User).limit(5))
        users = result.scalars().all()

        if len(users) < 2:
            print("❌ 需要至少2个用户才能创建真实场景的通知")
            return

        print(f"✓ 找到 {len(users)} 个用户")

        # 获取帖子
        result = await db.execute(select(Post).limit(3))
        posts = result.scalars().all()

        if not posts:
            print("⚠️  没有找到帖子，跳过帖子相关通知")
        else:
            print(f"✓ 找到 {len(posts)} 个帖子")

            # 为不同用户创建点赞通知
            for i, post in enumerate(posts):
                if i + 1 < len(users):
                    liker = users[i + 1]
                    author = await db.get(User, post.user_id)

                    if author and author.id != liker.id:
                        notification = Notification(
                            user_id=author.id,
                            type="like",
                            title="新点赞",
                            content=f"{liker.nickname or liker.anonymous_name} 点赞了你的帖子",
                            related_id=post.id,
                            is_read=False,
                        )
                        db.add(notification)
                        print(f"  ✓ 创建点赞通知: {liker.nickname or liker.anonymous_name} -> {author.nickname or author.anonymous_name}")

            # 为帖子创建评论通知
            for i, post in enumerate(posts):
                if i + 1 < len(users):
                    commenter = users[i + 1]
                    author = await db.get(User, post.user_id)

                    if author and author.id != commenter.id:
                        notification = Notification(
                            user_id=author.id,
                            type="comment",
                            title="新评论",
                            content=f"{commenter.nickname or commenter.anonymous_name} 评论了你的帖子: 写得真好！",
                            related_id=post.id,
                            is_read=False,
                        )
                        db.add(notification)
                        print(f"  ✓ 创建评论通知: {commenter.nickname or commenter.anonymous_name} -> {author.nickname or author.anonymous_name}")

        # 获取评论
        result = await db.execute(select(Comment).limit(3))
        comments = result.scalars().all()

        if not comments:
            print("⚠️  没有找到评论，跳过回复相关通知")
        else:
            print(f"✓ 找到 {len(comments)} 条评论")

            # 为评论创建回复通知
            for i, comment in enumerate(comments):
                if i + 1 < len(users):
                    replier = users[i + 1]
                    comment_author = await db.get(User, comment.user_id)

                    if comment_author and comment_author.id != replier.id:
                        notification = Notification(
                            user_id=comment_author.id,
                            type="reply",
                            title="新回复",
                            content=f"{replier.nickname or replier.anonymous_name} 回复了你的评论: 同意！",
                            related_id=comment.id,
                            is_read=False,
                        )
                        db.add(notification)
                        print(f"  ✓ 创建回复通知: {replier.nickname or replier.anonymous_name} -> {comment_author.nickname or comment_author.anonymous_name}")

        await db.commit()
        print("\n✓ 真实场景通知创建完成")

        # 统计总通知数
        from sqlalchemy import func
        result = await db.execute(select(func.count()).select_from(Notification))
        total = result.scalar()
        print(f"数据库中总共 {total} 条通知")

    except Exception as e:
        print(f"❌ 创建真实场景通知失败: {e}")
        import traceback
        traceback.print_exc()
        await db.rollback()
    finally:
        await db.close()


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="创建测试通知数据")
    parser.add_argument(
        "--realistic",
        action="store_true",
        help="创建真实场景的通知（需要有多用户、帖子、评论数据）"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("创建测试通知数据")
    print("=" * 60)

    if args.realistic:
        print("模式: 真实场景通知")
        asyncio.run(create_realistic_notifications())
    else:
        print("模式: 基础测试通知")
        create_test_notifications()

    print("\n✓ 完成！")


if __name__ == "__main__":
    main()
