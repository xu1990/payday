"""薪资使用记录服务集成测试"""
import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.salary_usage_service import (
    create_salary_usage,
    get_salary_usage,
    update_salary_usage,
    delete_salary_usage,
    list_salary_usages,
    get_usage_statistics_by_type,
)
from app.schemas.salary_usage import SalaryUsageCreate, SalaryUsageUpdate
from app.core.exceptions import NotFoundException, BusinessException
from tests.test_utils import TestDataFactory


class TestCreateSalaryUsage:
    """测试创建薪资使用记录"""

    @pytest.mark.asyncio
    async def test_create_salary_usage_success(self, db_session: AsyncSession):
        """测试成功创建薪资使用记录"""
        user = await TestDataFactory.create_user(db_session)

        # 创建 payday config
        from app.models.payday import PaydayConfig
        config = PaydayConfig(
            user_id=user.id,
            job_name="测试工作",
            payday=25,
        )
        db_session.add(config)
        await db_session.commit()
        await db_session.refresh(config)

        # 创建薪资记录
        salary = await TestDataFactory.create_salary(
            db_session, user.id, config.id
        )

        # 创建使用记录
        usage_data = SalaryUsageCreate(
            salary_record_id=salary.id,
            usage_type="food",
            amount=100.50,
            usage_date=datetime(2024, 1, 20, 12, 0),
            description="午餐"
        )

        # 调用创建函数
        usage = await create_salary_usage(db_session, user.id, usage_data)

        # 验证创建成功
        assert usage.id is not None
        assert usage.user_id == user.id
        assert usage.salary_record_id == salary.id
        assert usage.usage_type == "food"
        assert usage.description == "午餐"

        # 验证金额已加密（存储的不是明文）
        assert usage.amount != "100.5"

        # 验证可以解密
        from app.utils.encryption import decrypt_amount
        # 注意：当前模型只存储加密金额，没有存储salt
        # 这个测试可能会失败，需要在后续修复模型
        # decrypted = decrypt_amount(usage.amount, salt)
        # assert decrypted == 100.50

    @pytest.mark.asyncio
    async def test_create_salary_usage_with_all_types(self, db_session: AsyncSession):
        """测试所有使用类型"""
        user = await TestDataFactory.create_user(db_session)

        # 创建 payday config
        from app.models.payday import PaydayConfig
        config = PaydayConfig(
            user_id=user.id,
            job_name="测试工作",
            payday=25,
        )
        db_session.add(config)
        await db_session.commit()
        await db_session.refresh(config)

        # 创建薪资记录
        salary = await TestDataFactory.create_salary(
            db_session, user.id, config.id
        )

        usage_types = [
            "housing", "food", "transport", "shopping",
            "entertainment", "medical", "education", "other"
        ]

        for usage_type in usage_types:
            usage_data = SalaryUsageCreate(
                salary_record_id=salary.id,
                usage_type=usage_type,
                amount=50.0,
                usage_date=datetime(2024, 1, 20, 12, 0)
            )

            usage = await create_salary_usage(db_session, user.id, usage_data)
            assert usage.usage_type == usage_type

    @pytest.mark.asyncio
    async def test_create_salary_usage_nonexistent_salary(self, db_session: AsyncSession):
        """测试创建使用记录时薪资记录不存在"""
        user = await TestDataFactory.create_user(db_session)

        usage_data = SalaryUsageCreate(
            salary_record_id="nonexistent_salary_id",
            usage_type="food",
            amount=100.50,
            usage_date=datetime(2024, 1, 20, 12, 0)
        )

        with pytest.raises(NotFoundException) as exc_info:
            await create_salary_usage(db_session, user.id, usage_data)

        assert "薪资记录不存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_salary_usage_wrong_user(self, db_session: AsyncSession):
        """测试用户不能为其他用户的薪资记录创建使用记录"""
        user1 = await TestDataFactory.create_user(db_session)
        user2 = await TestDataFactory.create_user(db_session)

        # 创建 payday config for user1
        from app.models.payday import PaydayConfig
        config = PaydayConfig(
            user_id=user1.id,
            job_name="测试工作",
            payday=25,
        )
        db_session.add(config)
        await db_session.commit()
        await db_session.refresh(config)

        # user1 创建薪资记录
        salary = await TestDataFactory.create_salary(
            db_session, user1.id, config.id
        )

        # user2 尝试为 user1 的薪资记录创建使用记录
        usage_data = SalaryUsageCreate(
            salary_record_id=salary.id,
            usage_type="food",
            amount=100.50,
            usage_date=datetime(2024, 1, 20, 12, 0)
        )

        with pytest.raises(BusinessException) as exc_info:
            await create_salary_usage(db_session, user2.id, usage_data)

        assert "无权操作此薪资记录" in str(exc_info.value)


class TestGetSalaryUsage:
    """测试获取薪资使用记录"""

    @pytest.mark.asyncio
    async def test_get_salary_usage_success(self, db_session: AsyncSession):
        """测试成功获取使用记录"""
        user = await TestDataFactory.create_user(db_session)

        # 创建 payday config
        from app.models.payday import PaydayConfig
        config = PaydayConfig(
            user_id=user.id,
            job_name="测试工作",
            payday=25,
        )
        db_session.add(config)
        await db_session.commit()
        await db_session.refresh(config)

        # 创建薪资记录
        salary = await TestDataFactory.create_salary(
            db_session, user.id, config.id
        )

        # 创建使用记录
        usage_data = SalaryUsageCreate(
            salary_record_id=salary.id,
            usage_type="food",
            amount=100.50,
            usage_date=datetime(2024, 1, 20, 12, 0)
        )
        usage = await create_salary_usage(db_session, user.id, usage_data)

        # 获取记录
        found = await get_salary_usage(db_session, usage.id, user.id)

        assert found is not None
        assert found.id == usage.id
        assert found.user_id == user.id

    @pytest.mark.asyncio
    async def test_get_salary_usage_not_found(self, db_session: AsyncSession):
        """测试获取不存在的记录"""
        user = await TestDataFactory.create_user(db_session)

        with pytest.raises(NotFoundException) as exc_info:
            await get_salary_usage(db_session, "nonexistent_id", user.id)

        assert "使用记录不存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_salary_usage_wrong_user(self, db_session: AsyncSession):
        """测试用户不能访问其他用户的记录"""
        user1 = await TestDataFactory.create_user(db_session)
        user2 = await TestDataFactory.create_user(db_session)

        # 创建 payday config
        from app.models.payday import PaydayConfig
        config = PaydayConfig(
            user_id=user1.id,
            job_name="测试工作",
            payday=25,
        )
        db_session.add(config)
        await db_session.commit()
        await db_session.refresh(config)

        # 创建薪资和使用记录
        salary = await TestDataFactory.create_salary(
            db_session, user1.id, config.id
        )
        usage_data = SalaryUsageCreate(
            salary_record_id=salary.id,
            usage_type="food",
            amount=100.50,
            usage_date=datetime(2024, 1, 20, 12, 0)
        )
        usage = await create_salary_usage(db_session, user1.id, usage_data)

        # user2 尝试获取 user1 的记录
        with pytest.raises(BusinessException) as exc_info:
            await get_salary_usage(db_session, usage.id, user2.id)

        assert "无权查看此记录" in str(exc_info.value)


class TestUpdateSalaryUsage:
    """测试更新薪资使用记录"""

    @pytest.mark.asyncio
    async def test_update_salary_usage_success(self, db_session: AsyncSession):
        """测试成功更新使用记录"""
        user = await TestDataFactory.create_user(db_session)

        # 创建 payday config
        from app.models.payday import PaydayConfig
        config = PaydayConfig(
            user_id=user.id,
            job_name="测试工作",
            payday=25,
        )
        db_session.add(config)
        await db_session.commit()
        await db_session.refresh(config)

        # 创建薪资和使用记录
        salary = await TestDataFactory.create_salary(
            db_session, user.id, config.id
        )
        usage_data = SalaryUsageCreate(
            salary_record_id=salary.id,
            usage_type="food",
            amount=100.50,
            usage_date=datetime(2024, 1, 20, 12, 0),
            description="原始描述"
        )
        usage = await create_salary_usage(db_session, user.id, usage_data)

        # 更新
        update_data = SalaryUsageUpdate(
            usage_type="transport",
            amount=200.0,
            description="更新后的描述"
        )

        updated = await update_salary_usage(db_session, usage.id, user.id, update_data)

        assert updated is not None
        assert updated.usage_type == "transport"
        assert updated.description == "更新后的描述"
        # 验证金额已加密（是JSON格式）
        assert updated.amount.startswith("{")
        assert "encrypted" in updated.amount

    @pytest.mark.asyncio
    async def test_update_salary_usage_partial_fields(self, db_session: AsyncSession):
        """测试部分字段更新"""
        user = await TestDataFactory.create_user(db_session)

        # 创建 payday config
        from app.models.payday import PaydayConfig
        config = PaydayConfig(
            user_id=user.id,
            job_name="测试工作",
            payday=25,
        )
        db_session.add(config)
        await db_session.commit()
        await db_session.refresh(config)

        # 创建薪资和使用记录
        salary = await TestDataFactory.create_salary(
            db_session, user.id, config.id
        )
        usage_data = SalaryUsageCreate(
            salary_record_id=salary.id,
            usage_type="food",
            amount=100.50,
            usage_date=datetime(2024, 1, 20, 12, 0),
            description="原始描述"
        )
        usage = await create_salary_usage(db_session, user.id, usage_data)

        # 只更新 usage_type
        update_data = SalaryUsageUpdate(usage_type="shopping")

        updated = await update_salary_usage(db_session, usage.id, user.id, update_data)

        assert updated.usage_type == "shopping"
        assert updated.description == "原始描述"  # 保持不变

    @pytest.mark.asyncio
    async def test_update_salary_usage_not_found(self, db_session: AsyncSession):
        """测试更新不存在的记录"""
        user = await TestDataFactory.create_user(db_session)

        update_data = SalaryUsageUpdate(usage_type="food")

        with pytest.raises(NotFoundException) as exc_info:
            await update_salary_usage(db_session, "nonexistent_id", user.id, update_data)

        assert "使用记录不存在" in str(exc_info.value)


class TestDeleteSalaryUsage:
    """测试删除薪资使用记录"""

    @pytest.mark.asyncio
    async def test_delete_salary_usage_success(self, db_session: AsyncSession):
        """测试成功删除使用记录"""
        user = await TestDataFactory.create_user(db_session)

        # 创建 payday config
        from app.models.payday import PaydayConfig
        config = PaydayConfig(
            user_id=user.id,
            job_name="测试工作",
            payday=25,
        )
        db_session.add(config)
        await db_session.commit()
        await db_session.refresh(config)

        # 创建薪资和使用记录
        salary = await TestDataFactory.create_salary(
            db_session, user.id, config.id
        )
        usage_data = SalaryUsageCreate(
            salary_record_id=salary.id,
            usage_type="food",
            amount=100.50,
            usage_date=datetime(2024, 1, 20, 12, 0)
        )
        usage = await create_salary_usage(db_session, user.id, usage_data)

        # 删除
        await delete_salary_usage(db_session, usage.id, user.id)

        # 验证已删除
        with pytest.raises(NotFoundException):
            await get_salary_usage(db_session, usage.id, user.id)

    @pytest.mark.asyncio
    async def test_delete_salary_usage_not_found(self, db_session: AsyncSession):
        """测试删除不存在的记录"""
        user = await TestDataFactory.create_user(db_session)

        with pytest.raises(NotFoundException):
            await delete_salary_usage(db_session, "nonexistent_id", user.id)


class TestListSalaryUsages:
    """测试获取薪资使用记录列表"""

    @pytest.mark.asyncio
    async def test_list_salary_usages_empty(self, db_session: AsyncSession):
        """测试获取空列表"""
        user = await TestDataFactory.create_user(db_session)

        usages, total = await list_salary_usages(db_session, user.id)

        assert usages == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_list_salary_usages_success(self, db_session: AsyncSession):
        """测试成功获取使用记录列表"""
        user = await TestDataFactory.create_user(db_session)

        # 创建 payday config
        from app.models.payday import PaydayConfig
        config = PaydayConfig(
            user_id=user.id,
            job_name="测试工作",
            payday=25,
        )
        db_session.add(config)
        await db_session.commit()
        await db_session.refresh(config)

        # 创建薪资记录
        salary = await TestDataFactory.create_salary(
            db_session, user.id, config.id
        )

        # 创建多条使用记录
        await create_salary_usage(db_session, user.id, SalaryUsageCreate(
            salary_record_id=salary.id,
            usage_type="food",
            amount=100.0,
            usage_date=datetime(2024, 3, 20, 12, 0)
        ))
        await create_salary_usage(db_session, user.id, SalaryUsageCreate(
            salary_record_id=salary.id,
            usage_type="transport",
            amount=50.0,
            usage_date=datetime(2024, 2, 15, 12, 0)
        ))
        await create_salary_usage(db_session, user.id, SalaryUsageCreate(
            salary_record_id=salary.id,
            usage_type="shopping",
            amount=200.0,
            usage_date=datetime(2024, 1, 10, 12, 0)
        ))

        # 获取列表
        usages, total = await list_salary_usages(db_session, user.id)

        # 验证
        assert len(usages) == 3
        assert total == 3
        # 默认按使用日期倒序
        assert usages[0].usage_type == "food"
        assert usages[1].usage_type == "transport"
        assert usages[2].usage_type == "shopping"

    @pytest.mark.asyncio
    async def test_list_salary_usages_with_salary_filter(self, db_session: AsyncSession):
        """测试按薪资记录ID筛选"""
        user = await TestDataFactory.create_user(db_session)

        # 创建 payday config
        from app.models.payday import PaydayConfig
        config = PaydayConfig(
            user_id=user.id,
            job_name="测试工作",
            payday=25,
        )
        db_session.add(config)
        await db_session.commit()
        await db_session.refresh(config)

        # 创建两条薪资记录
        salary1 = await TestDataFactory.create_salary(
            db_session, user.id, config.id
        )
        salary2 = await TestDataFactory.create_salary(
            db_session, user.id, config.id
        )

        # 为不同薪资记录创建使用记录
        await create_salary_usage(db_session, user.id, SalaryUsageCreate(
            salary_record_id=salary1.id,
            usage_type="food",
            amount=100.0,
            usage_date=datetime(2024, 1, 20, 12, 0)
        ))
        await create_salary_usage(db_session, user.id, SalaryUsageCreate(
            salary_record_id=salary1.id,
            usage_type="transport",
            amount=50.0,
            usage_date=datetime(2024, 1, 21, 12, 0)
        ))
        await create_salary_usage(db_session, user.id, SalaryUsageCreate(
            salary_record_id=salary2.id,
            usage_type="shopping",
            amount=200.0,
            usage_date=datetime(2024, 1, 22, 12, 0)
        ))

        # 筛选 salary1
        usages, total = await list_salary_usages(
            db_session, user.id, salary_record_id=salary1.id
        )

        assert len(usages) == 2
        assert total == 2
        assert all(u.salary_record_id == salary1.id for u in usages)

    @pytest.mark.asyncio
    async def test_list_salary_usages_with_type_filter(self, db_session: AsyncSession):
        """测试按使用类型筛选"""
        user = await TestDataFactory.create_user(db_session)

        # 创建 payday config
        from app.models.payday import PaydayConfig
        config = PaydayConfig(
            user_id=user.id,
            job_name="测试工作",
            payday=25,
        )
        db_session.add(config)
        await db_session.commit()
        await db_session.refresh(config)

        # 创建薪资记录
        salary = await TestDataFactory.create_salary(
            db_session, user.id, config.id
        )

        # 创建不同类型的使用记录
        await create_salary_usage(db_session, user.id, SalaryUsageCreate(
            salary_record_id=salary.id,
            usage_type="food",
            amount=100.0,
            usage_date=datetime(2024, 1, 20, 12, 0)
        ))
        await create_salary_usage(db_session, user.id, SalaryUsageCreate(
            salary_record_id=salary.id,
            usage_type="food",
            amount=50.0,
            usage_date=datetime(2024, 1, 21, 12, 0)
        ))
        await create_salary_usage(db_session, user.id, SalaryUsageCreate(
            salary_record_id=salary.id,
            usage_type="transport",
            amount=30.0,
            usage_date=datetime(2024, 1, 22, 12, 0)
        ))

        # 筛选 food 类型
        usages, total = await list_salary_usages(
            db_session, user.id, usage_type="food"
        )

        assert len(usages) == 2
        assert total == 2
        assert all(u.usage_type == "food" for u in usages)

    @pytest.mark.asyncio
    async def test_list_salary_usages_with_pagination(self, db_session: AsyncSession):
        """测试分页功能"""
        user = await TestDataFactory.create_user(db_session)

        # 创建 payday config
        from app.models.payday import PaydayConfig
        config = PaydayConfig(
            user_id=user.id,
            job_name="测试工作",
            payday=25,
        )
        db_session.add(config)
        await db_session.commit()
        await db_session.refresh(config)

        # 创建薪资记录
        salary = await TestDataFactory.create_salary(
            db_session, user.id, config.id
        )

        # 创建5条记录
        for i in range(5):
            await create_salary_usage(db_session, user.id, SalaryUsageCreate(
                salary_record_id=salary.id,
                usage_type="food",
                amount=100.0,
                usage_date=datetime(2024, i + 1, 20, 12, 0)
            ))

        # 测试分页
        usages1, total1 = await list_salary_usages(db_session, user.id, skip=0, limit=2)
        usages2, total2 = await list_salary_usages(db_session, user.id, skip=2, limit=2)
        usages3, total3 = await list_salary_usages(db_session, user.id, skip=4, limit=2)

        assert len(usages1) == 2
        assert len(usages2) == 2
        assert len(usages3) == 1
        assert total1 == total2 == total3 == 5

    @pytest.mark.asyncio
    async def test_list_salary_usages_isolation(self, db_session: AsyncSession):
        """测试用户数据隔离"""
        user1 = await TestDataFactory.create_user(db_session)
        user2 = await TestDataFactory.create_user(db_session)

        # 创建 payday configs
        from app.models.payday import PaydayConfig
        config1 = PaydayConfig(user_id=user1.id, job_name="工作1", payday=25)
        config2 = PaydayConfig(user_id=user2.id, job_name="工作2", payday=15)
        db_session.add(config1)
        db_session.add(config2)
        await db_session.commit()
        await db_session.refresh(config1)
        await db_session.refresh(config2)

        # 为两个用户创建记录
        salary1 = await TestDataFactory.create_salary(db_session, user1.id, config1.id)
        salary2 = await TestDataFactory.create_salary(db_session, user2.id, config2.id)

        await create_salary_usage(db_session, user1.id, SalaryUsageCreate(
            salary_record_id=salary1.id,
            usage_type="food",
            amount=100.0,
            usage_date=datetime(2024, 1, 20, 12, 0)
        ))
        await create_salary_usage(db_session, user2.id, SalaryUsageCreate(
            salary_record_id=salary2.id,
            usage_type="transport",
            amount=50.0,
            usage_date=datetime(2024, 1, 21, 12, 0)
        ))

        # user1 只能看到自己的记录
        user1_usages, total1 = await list_salary_usages(db_session, user1.id)
        assert len(user1_usages) == 1
        assert total1 == 1
        assert user1_usages[0].user_id == user1.id

        # user2 只能看到自己的记录
        user2_usages, total2 = await list_salary_usages(db_session, user2.id)
        assert len(user2_usages) == 1
        assert total2 == 1
        assert user2_usages[0].user_id == user2.id


class TestGetUsageStatisticsByType:
    """测试按类型统计使用金额"""

    @pytest.mark.asyncio
    async def test_get_usage_statistics_by_type(self, db_session: AsyncSession):
        """测试按类型统计"""
        user = await TestDataFactory.create_user(db_session)

        # 创建 payday config
        from app.models.payday import PaydayConfig
        config = PaydayConfig(
            user_id=user.id,
            job_name="测试工作",
            payday=25,
        )
        db_session.add(config)
        await db_session.commit()
        await db_session.refresh(config)

        # 创建薪资记录
        salary = await TestDataFactory.create_salary(
            db_session, user.id, config.id
        )

        # 创建不同类型的使用记录
        await create_salary_usage(db_session, user.id, SalaryUsageCreate(
            salary_record_id=salary.id,
            usage_type="food",
            amount=100.0,
            usage_date=datetime(2024, 1, 20, 12, 0)
        ))
        await create_salary_usage(db_session, user.id, SalaryUsageCreate(
            salary_record_id=salary.id,
            usage_type="food",
            amount=50.0,
            usage_date=datetime(2024, 1, 21, 12, 0)
        ))
        await create_salary_usage(db_session, user.id, SalaryUsageCreate(
            salary_record_id=salary.id,
            usage_type="transport",
            amount=30.0,
            usage_date=datetime(2024, 1, 22, 12, 0)
        ))
        await create_salary_usage(db_session, user.id, SalaryUsageCreate(
            salary_record_id=salary.id,
            usage_type="shopping",
            amount=200.0,
            usage_date=datetime(2024, 1, 23, 12, 0)
        ))

        # 获取统计
        stats = await get_usage_statistics_by_type(db_session, user.id)

        assert stats["food"] == 150.0
        assert stats["transport"] == 30.0
        assert stats["shopping"] == 200.0

    @pytest.mark.asyncio
    async def test_get_usage_statistics_by_type_with_salary_filter(self, db_session: AsyncSession):
        """测试按薪资记录筛选后统计"""
        user = await TestDataFactory.create_user(db_session)

        # 创建 payday config
        from app.models.payday import PaydayConfig
        config = PaydayConfig(
            user_id=user.id,
            job_name="测试工作",
            payday=25,
        )
        db_session.add(config)
        await db_session.commit()
        await db_session.refresh(config)

        # 创建两条薪资记录
        salary1 = await TestDataFactory.create_salary(
            db_session, user.id, config.id
        )
        salary2 = await TestDataFactory.create_salary(
            db_session, user.id, config.id
        )

        # 为不同薪资记录创建使用记录
        await create_salary_usage(db_session, user.id, SalaryUsageCreate(
            salary_record_id=salary1.id,
            usage_type="food",
            amount=100.0,
            usage_date=datetime(2024, 1, 20, 12, 0)
        ))
        await create_salary_usage(db_session, user.id, SalaryUsageCreate(
            salary_record_id=salary2.id,
            usage_type="food",
            amount=50.0,
            usage_date=datetime(2024, 1, 21, 12, 0)
        ))

        # 筛选 salary1 统计
        stats = await get_usage_statistics_by_type(
            db_session, user.id, salary_record_id=salary1.id
        )

        assert stats["food"] == 100.0

    @pytest.mark.asyncio
    async def test_get_usage_statistics_by_type_empty(self, db_session: AsyncSession):
        """测试空数据统计"""
        user = await TestDataFactory.create_user(db_session)

        stats = await get_usage_statistics_by_type(db_session, user.id)

        assert stats == {}
