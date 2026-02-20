"""测试协议 API 返回格式"""
import asyncio
from sqlalchemy import select
from app.core.database import async_session_maker
from app.models.miniprogram_config import MiniprogramConfig
from app.core.exceptions import success_response
from app.api.v1.config import AgreementResponse


async def test_agreement_data():
    """测试协议数据"""
    async with async_session_maker() as db:
        # 获取用户协议
        user_result = await db.execute(
            select(MiniprogramConfig).where(MiniprogramConfig.key == 'user_agreement')
        )
        user_config = user_result.scalar_one_or_none()

        # 获取隐私协议
        privacy_result = await db.execute(
            select(MiniprogramConfig).where(MiniprogramConfig.key == 'privacy_agreement')
        )
        privacy_config = privacy_result.scalar_one_or_none()

        print("=== 数据库中的数据 ===")
        print(f"user_config: {user_config}")
        print(f"user_config.value: {user_config.value if user_config else 'N/A'}")
        print(f"privacy_config: {privacy_config}")
        print(f"privacy_config.value: {privacy_config.value if privacy_config else 'N/A'}")

        # 测试 Pydantic 模型
        user_agreement = user_config.value if user_config else ""
        privacy_agreement = privacy_config.value if privacy_config else ""

        print("\n=== 处理后的数据 ===")
        print(f"user_agreement: {repr(user_agreement[:50] if user_agreement else 'empty')}...")
        print(f"privacy_agreement: {repr(privacy_agreement[:50] if privacy_agreement else 'empty')}...")

        # 测试 AgreementResponse
        print("\n=== AgreementResponse.model_dump() ===")
        response = AgreementResponse(
            user_agreement=user_agreement,
            privacy_agreement=privacy_agreement
        )
        print(response.model_dump())

        # 测试 success_response
        print("\n=== success_response 格式 ===")
        resp = success_response(
            data={
                "user_agreement": user_agreement,
                "privacy_agreement": privacy_agreement
            },
            message="获取协议成功"
        )
        print(f"Status: {resp.status_code}")
        import json
        print(f"Body: {json.loads(resp.body.decode())}")


if __name__ == "__main__":
    asyncio.run(test_agreement_data())
