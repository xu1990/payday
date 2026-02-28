#!/usr/bin/env python3
"""
修复订单状态脚本

将 payment_status='paid' 但 status='pending' 的订单状态更新为 'completed'

使用方法：
    cd backend
    python3 scripts/fix_order_status.py
"""
import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db


async def fix_order_status():
    """修复订单状态"""
    async for session in get_db():
        # 先查看有多少订单需要修复
        check_sql = text("""
            SELECT COUNT(*) as count
            FROM point_orders
            WHERE payment_status = 'paid' AND status = 'pending'
        """)
        result = await session.execute(check_sql)
        row = result.fetchone()
        count = row[0] if row else 0

        if count == 0:
            print("没有需要修复的订单")
            return

        print(f"发现 {count} 个订单需要修复")

        # 显示需要修复的订单详情
        detail_sql = text("""
            SELECT id, order_number, payment_status, status, payment_mode, created_at
            FROM point_orders
            WHERE payment_status = 'paid' AND status = 'pending'
            LIMIT 10
        """)
        result = await session.execute(detail_sql)
        rows = result.fetchall()

        print("\n待修复订单示例（前10个）：")
        print("-" * 100)
        for row in rows:
            print(f"ID: {row[0][:8]}... | 订单号: {row[1]} | 支付状态: {row[2]} | 订单状态: {row[3]} | 支付模式: {row[4]} | 创建时间: {row[5]}")

        # 执行更新
        update_sql = text("""
            UPDATE point_orders
            SET status = 'completed', updated_at = datetime('now')
            WHERE payment_status = 'paid' AND status = 'pending'
        """)

        await session.execute(update_sql)
        await session.commit()

        print(f"\n已成功修复 {count} 个订单的状态")


async def main():
    print("=" * 50)
    print("订单状态修复脚本")
    print("=" * 50)

    try:
        await fix_order_status()
    except Exception as e:
        print(f"执行出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("\n脚本执行完成")


if __name__ == "__main__":
    asyncio.run(main())
