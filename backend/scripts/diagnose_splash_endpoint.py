#!/usr/bin/env python3
"""
诊断开屏配置端点问题的脚本

用法:
    python scripts/diagnose_splash_endpoint.py

此脚本将检查:
1. 数据库连接
2. miniprogram_configs 表是否存在
3. 表结构是否正确
4. 是否有 splash_config 记录
5. 测试端点调用
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import get_db
from app.models.miniprogram_config import MiniprogramConfig
from app.utils.logger import get_logger
from sqlalchemy import inspect, text

logger = get_logger(__name__)


async def check_database_connection():
    """检查数据库连接"""
    print("\n=== 1. 检查数据库连接 ===")
    try:
        db_gen = get_db()
        db = await db_gen.__anext__()
        print("✓ 数据库连接成功")
        return db
    except Exception as e:
        print(f"✗ 数据库连接失败: {e}")
        return None


async def check_table_exists(db):
    """检查 miniprogram_configs 表是否存在"""
    print("\n=== 2. 检查 miniprogram_configs 表是否存在 ===")
    try:
        inspector = inspect(db.bind)
        tables = inspector.get_table_names()
        if 'miniprogram_configs' in tables:
            print("✓ miniprogram_configs 表存在")
            return True
        else:
            print("✗ miniprogram_configs 表不存在")
            print(f"  现有表: {', '.join(tables)}")
            return False
    except Exception as e:
        print(f"✗ 检查表时出错: {e}")
        return False


async def check_table_structure(db):
    """检查表结构"""
    print("\n=== 3. 检查表结构 ===")
    try:
        inspector = inspect(db.bind)
        columns = inspector.get_columns('miniprogram_configs')

        print("表结构:")
        required_columns = ['id', 'key', 'value', 'description', 'is_active', 'sort_order', 'created_at', 'updated_at']
        for col in columns:
            required = " ✓" if col['name'] in required_columns else ""
            print(f"  - {col['name']}: {col['type']}{required}")

        missing = [col for col in required_columns if col not in {c['name'] for c in columns}]
        if missing:
            print(f"✗ 缺少列: {', '.join(missing)}")
            return False
        else:
            print("✓ 表结构正确")
            return True
    except Exception as e:
        print(f"✗ 检查表结构时出错: {e}")
        return False


async def check_splash_config(db):
    """检查 splash_config 记录"""
    print("\n=== 4. 检查 splash_config 记录 ===")
    try:
        from sqlalchemy import select

        result = await db.execute(
            select(MiniprogramConfig).where(MiniprogramConfig.key == 'splash_config')
        )
        config = result.scalar_one_or_none()

        if not config:
            print("✗ 没有 splash_config 记录")
            print("  提示: 需要通过管理后台创建开屏配置")
            return None
        else:
            print("✓ 找到 splash_config 记录:")
            print(f"  - ID: {config.id}")
            print(f"  - Key: {config.key}")
            print(f"  - Value: {config.value[:100] if config.value else 'None'}...")
            print(f"  - Is Active: {config.is_active}")
            print(f"  - Created: {config.created_at}")
            print(f"  - Updated: {config.updated_at}")
            return config
    except Exception as e:
        print(f"✗ 查询 splash_config 时出错: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_endpoint_logic(db):
    """测试端点逻辑"""
    print("\n=== 5. 测试端点逻辑 ===")
    try:
        import json

        from sqlalchemy import select

        result = await db.execute(
            select(MiniprogramConfig).where(MiniprogramConfig.key == 'splash_config')
        )
        config = result.scalar_one_or_none()

        # 模拟端点逻辑
        if not config:
            print("  测试: 配置不存在 → 返回 is_active=False")
            return True

        config_value = getattr(config, 'value', None)
        is_active = getattr(config, 'is_active', False)

        if not config_value:
            print(f"  测试: 配置值为空 → 返回 is_active=False")
            return True

        if not is_active:
            print(f"  测试: 配置未启用 (is_active={is_active}) → 返回 is_active=False")
            return True

        # 尝试解析 JSON
        try:
            splash_data = json.loads(config_value)
            print(f"  ✓ JSON 解析成功:")
            print(f"    - image_url: {splash_data.get('image_url', 'None')}")
            print(f"    - content: {splash_data.get('content', 'None')[:50]}...")
            print(f"    - countdown: {splash_data.get('countdown', 3)}")
            return True
        except json.JSONDecodeError as e:
            print(f"  ✗ JSON 解析失败: {e}")
            print(f"    原始值: {config_value[:200]}")
            return False

    except Exception as e:
        print(f"  ✗ 测试时出错: {e}")
        import traceback
        traceback.print_exc()
        return False


async def check_all_configs(db):
    """检查所有配置记录"""
    print("\n=== 6. 检查所有配置记录 ===")
    try:
        from sqlalchemy import select

        result = await db.execute(select(MiniprogramConfig))
        configs = result.scalars().all()

        if not configs:
            print("✗ 配置表为空")
            return False

        print(f"✓ 共有 {len(configs)} 条配置记录:")
        for config in configs:
            print(f"  - {config.key}: is_active={config.is_active}, value={'有值' if config.value else '空'}")

        return True
    except Exception as e:
        print(f"✗ 查询配置时出错: {e}")
        return False


async def main():
    """主函数"""
    print("=" * 60)
    print("开屏配置端点诊断工具")
    print("=" * 60)

    # 检查数据库连接
    db = await check_database_connection()
    if not db:
        print("\n❌ 无法连接到数据库，请检查配置")
        print("   建议:")
        print("   1. 检查 backend/.env 文件中的数据库配置")
        print("   2. 确保数据库服务正在运行")
        return 1

    # 检查表是否存在
    table_exists = await check_table_exists(db)
    if not table_exists:
        print("\n❌ miniprogram_configs 表不存在")
        print("   解决方案: 运行数据库迁移")
        print("   cd backend && alembic upgrade head")
        return 1

    # 检查表结构
    structure_ok = await check_table_structure(db)
    if not structure_ok:
        print("\n⚠️  表结构可能有问题，建议运行迁移更新")

    # 检查所有配置
    await check_all_configs(db)

    # 检查 splash_config
    config = await check_splash_config(db)

    # 测试端点逻辑
    logic_ok = await test_endpoint_logic(db)

    # 总结
    print("\n" + "=" * 60)
    print("诊断总结")
    print("=" * 60)

    issues = []

    if not table_exists:
        issues.append("❌ miniprogram_configs 表不存在 - 需要运行迁移")

    if not structure_ok:
        issues.append("⚠️  表结构可能不正确 - 建议运行迁移")

    if not config:
        issues.append("⚠️  没有 splash_config 记录 - 需要通过管理后台创建")

    if not logic_ok:
        issues.append("❌ 端点逻辑测试失败 - 需要检查代码")

    if issues:
        print("\n发现的问题:")
        for issue in issues:
            print(f"  {issue}")
        print("\n建议操作:")
        print("  1. 运行数据库迁移: alembic upgrade head")
        print("  2. 重启后端服务")
        print("  3. 通过管理后台创建开屏配置")
        return 1
    else:
        print("\n✓ 所有检查通过!")
        print("\n如果端点仍然返回 500 错误，请:")
        print("  1. 检查服务器日志: logs/app.log")
        print("  2. 临时开启 debug 模式查看详细错误信息")
        print("  3. 使用 curl 或 Postman 测试端点")
        return 0

    # 关闭数据库连接
    await db.close()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
