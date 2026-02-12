"""工资记录服务集成测试"""
import pytest
from datetime import date, datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.salary_service import (
    create,
    list_by_user,
    get_by_id,
    update,
    delete,
    record_to_response,
    get_by_id_for_admin,
    delete_for_admin,
    update_risk_for_admin,
    list_all_for_admin,
)
from app.schemas.salary import SalaryRecordCreate, SalaryRecordUpdate
from app.core.exceptions import NotFoundException, ValidationException
from tests.test_utils import TestDataFactory


class TestRecordToResponse:
    """测试数据库记录转换为响应字典"""

    @pytest.mark.asyncio
    async def test_record_to_response_decrypts_amount(self, db_session: AsyncSession):
        """测试转换函数正确解密金额"""
        # 创建测试用户
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

        # 创建薪资记录（金额已加密）
        original_amount = 15000.50
        salary = await TestDataFactory.create_salary(
            db_session,
            user_id=user.id,
            config_id=config.id,
            amount=original_amount
        )

        # 转换为响应
        response = record_to_response(salary)

        # 验证解密后的金额正确
        assert response["id"] == salary.id
        assert response["user_id"] == user.id
        assert response["config_id"] == config.id
        assert response["amount"] == original_amount
        assert response["payday_date"] == salary.payday_date
        assert response["salary_type"] == salary.salary_type
        assert response["mood"] == salary.mood
        assert response["risk_status"] == "pending"
        assert response["created_at"] == salary.created_at


class TestCreateSalary:
    """测试创建工资记录"""

    @pytest.mark.asyncio
    async def test_create_salary_success(self, db_session: AsyncSession):
        """测试成功创建工资记录"""
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

        # 创建数据
        salary_data = SalaryRecordCreate(
            config_id=config.id,
            amount=12000.00,
            payday_date=date(2024, 1, 15),
            salary_type="normal",
            mood="happy",
            note="测试工资"
        )

        # 调用创建函数
        record = await create(db_session, user.id, salary_data)

        # 验证创建成功
        assert record.id is not None
        assert record.user_id == user.id
        assert record.config_id == config.id
        assert record.payday_date == date(2024, 1, 15)
        assert record.salary_type == "normal"
        assert record.mood == "happy"
        assert record.note == "测试工资"
        assert record.risk_status == "pending"

        # 验证金额已加密（存储的不是明文）
        assert record.amount_encrypted != "12000.0"
        assert record.encryption_salt is not None
        assert len(record.encryption_salt) > 0

        # 验证可以解密
        from app.utils.encryption import decrypt_amount
        decrypted_amount = decrypt_amount(record.amount_encrypted, record.encryption_salt)
        assert decrypted_amount == 12000.00

    @pytest.mark.asyncio
    async def test_create_salary_with_bonus_type(self, db_session: AsyncSession):
        """测试创建奖金类型的工资记录"""
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

        salary_data = SalaryRecordCreate(
            config_id=config.id,
            amount=5000.00,
            payday_date=date(2024, 2, 1),
            salary_type="bonus",
            mood="expect",
            images=["https://example.com/slip.jpg"]
        )

        record = await create(db_session, user.id, salary_data)

        assert record.salary_type == "bonus"
        assert record.mood == "expect"
        assert record.images == ["https://example.com/slip.jpg"]

    @pytest.mark.asyncio
    async def test_create_salary_with_all_mood_types(self, db_session: AsyncSession):
        """测试所有心情类型的工资记录"""
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

        moods = ["happy", "relief", "sad", "angry", "expect"]

        for mood in moods:
            salary_data = SalaryRecordCreate(
                config_id=config.id,
                amount=8000.00,
                payday_date=date(2024, 1, 15),
                salary_type="normal",
                mood=mood
            )

            record = await create(db_session, user.id, salary_data)
            assert record.mood == mood

    @pytest.mark.asyncio
    async def test_create_salary_with_all_salary_types(self, db_session: AsyncSession):
        """测试所有薪资类型"""
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

        salary_types = ["normal", "bonus", "allowance", "other"]

        for salary_type in salary_types:
            salary_data = SalaryRecordCreate(
                config_id=config.id,
                amount=10000.00,
                payday_date=date(2024, 1, 15),
                salary_type=salary_type,
                mood="happy"
            )

            record = await create(db_session, user.id, salary_data)
            assert record.salary_type == salary_type


class TestListByUser:
    """测试获取用户工资记录列表"""

    @pytest.mark.asyncio
    async def test_list_user_salaries_empty(self, db_session: AsyncSession):
        """测试获取空列表"""
        user = await TestDataFactory.create_user(db_session)

        salaries = await list_by_user(db_session, user.id)

        assert salaries == []

    @pytest.mark.asyncio
    async def test_list_user_salaries_success(self, db_session: AsyncSession):
        """测试成功获取用户工资记录"""
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

        # 创建多条工资记录
        await TestDataFactory.create_salary(
            db_session, user.id, config.id,
            payday_date=date(2024, 3, 15)
        )
        await TestDataFactory.create_salary(
            db_session, user.id, config.id,
            payday_date=date(2024, 2, 15)
        )
        await TestDataFactory.create_salary(
            db_session, user.id, config.id,
            payday_date=date(2024, 1, 15)
        )

        # 获取列表
        salaries = await list_by_user(db_session, user.id)

        # 验证
        assert len(salaries) == 3
        # 默认按发薪日期倒序
        assert salaries[0].payday_date == date(2024, 3, 15)
        assert salaries[1].payday_date == date(2024, 2, 15)
        assert salaries[2].payday_date == date(2024, 1, 15)

    @pytest.mark.asyncio
    async def test_list_user_salaries_with_pagination(self, db_session: AsyncSession):
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

        # 创建5条记录
        for i in range(5):
            await TestDataFactory.create_salary(
                db_session, user.id, config.id,
                payday_date=date(2024, i + 1, 15)
            )

        # 测试分页
        page1 = await list_by_user(db_session, user.id, limit=2, offset=0)
        page2 = await list_by_user(db_session, user.id, limit=2, offset=2)
        page3 = await list_by_user(db_session, user.id, limit=2, offset=4)

        assert len(page1) == 2
        assert len(page2) == 2
        assert len(page3) == 1

    @pytest.mark.asyncio
    async def test_list_user_salaries_filter_by_config(self, db_session: AsyncSession):
        """测试按配置ID筛选"""
        user = await TestDataFactory.create_user(db_session)

        # 创建两个不同的 config
        from app.models.payday import PaydayConfig
        config1 = PaydayConfig(
            user_id=user.id,
            job_name="工作1",
            payday=25,
        )
        config2 = PaydayConfig(
            user_id=user.id,
            job_name="工作2",
            payday=15,
        )
        db_session.add(config1)
        db_session.add(config2)
        await db_session.commit()
        await db_session.refresh(config1)
        await db_session.refresh(config2)

        # 为两个 config 创建工资记录
        await TestDataFactory.create_salary(db_session, user.id, config1.id)
        await TestDataFactory.create_salary(db_session, user.id, config1.id)
        await TestDataFactory.create_salary(db_session, user.id, config2.id)

        # 筛选 config1
        salaries = await list_by_user(db_session, user.id, config_id=config1.id)

        assert len(salaries) == 2
        assert all(s.config_id == config1.id for s in salaries)

    @pytest.mark.asyncio
    async def test_list_user_salaries_filter_by_date_range(self, db_session: AsyncSession):
        """测试按日期范围筛选"""
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

        # 创建不同日期的记录
        await TestDataFactory.create_salary(
            db_session, user.id, config.id,
            payday_date=date(2024, 1, 15)
        )
        await TestDataFactory.create_salary(
            db_session, user.id, config.id,
            payday_date=date(2024, 2, 15)
        )
        await TestDataFactory.create_salary(
            db_session, user.id, config.id,
            payday_date=date(2024, 3, 15)
        )

        # 筛选 2月记录
        salaries = await list_by_user(
            db_session, user.id,
            from_date="2024-02-01",
            to_date="2024-02-29"
        )

        assert len(salaries) == 1
        assert salaries[0].payday_date == date(2024, 2, 15)

    @pytest.mark.asyncio
    async def test_list_user_salaries_isolation(self, db_session: AsyncSession):
        """测试用户数据隔离"""
        user1 = await TestDataFactory.create_user(db_session)
        user2 = await TestDataFactory.create_user(db_session)

        # 创建 payday config
        from app.models.payday import PaydayConfig
        config1 = PaydayConfig(user_id=user1.id, job_name="工作1", payday=25)
        config2 = PaydayConfig(user_id=user2.id, job_name="工作2", payday=15)
        db_session.add(config1)
        db_session.add(config2)
        await db_session.commit()
        await db_session.refresh(config1)
        await db_session.refresh(config2)

        # 为两个用户创建记录
        await TestDataFactory.create_salary(db_session, user1.id, config1.id)
        await TestDataFactory.create_salary(db_session, user1.id, config1.id)
        await TestDataFactory.create_salary(db_session, user2.id, config2.id)

        # user1 只能看到自己的记录
        user1_salaries = await list_by_user(db_session, user1.id)
        assert len(user1_salaries) == 2
        assert all(s.user_id == user1.id for s in user1_salaries)

        # user2 只能看到自己的记录
        user2_salaries = await list_by_user(db_session, user2.id)
        assert len(user2_salaries) == 1
        assert user2_salaries[0].user_id == user2.id


class TestGetById:
    """测试获取单条工资记录"""

    @pytest.mark.asyncio
    async def test_get_salary_by_id_success(self, db_session: AsyncSession):
        """测试成功获取工资记录"""
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

        # 创建记录
        salary = await TestDataFactory.create_salary(
            db_session, user.id, config.id
        )

        # 获取记录
        found = await get_by_id(db_session, salary.id, user.id)

        assert found is not None
        assert found.id == salary.id
        assert found.user_id == user.id

    @pytest.mark.asyncio
    async def test_get_salary_by_id_not_found(self, db_session: AsyncSession):
        """测试获取不存在的记录"""
        user = await TestDataFactory.create_user(db_session)

        found = await get_by_id(db_session, "nonexistent_id", user.id)

        assert found is None

    @pytest.mark.asyncio
    async def test_get_salary_by_id_wrong_user(self, db_session: AsyncSession):
        """测试用户不能访问其他用户的记录"""
        user1 = await TestDataFactory.create_user(db_session)
        user2 = await TestDataFactory.create_user(db_session)

        # 创建 payday config
        from app.models.payday import PaydayConfig
        config1 = PaydayConfig(user_id=user1.id, job_name="工作1", payday=25)
        db_session.add(config1)
        await db_session.commit()
        await db_session.refresh(config1)

        # user1 创建记录
        salary = await TestDataFactory.create_salary(
            db_session, user1.id, config1.id
        )

        # user2 尝试获取 user1 的记录
        found = await get_by_id(db_session, salary.id, user2.id)

        # 应该返回 None（其他用户的记录）
        assert found is None


class TestUpdateSalary:
    """测试更新工资记录"""

    @pytest.mark.asyncio
    async def test_update_salary_success(self, db_session: AsyncSession):
        """测试成功更新工资记录"""
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

        # 创建记录
        salary = await TestDataFactory.create_salary(
            db_session, user.id, config.id,
            mood="happy"
        )

        # 更新数据
        update_data = SalaryRecordUpdate(
            mood="sad",
            note="更新后的备注"
        )

        updated = await update(db_session, salary.id, user.id, update_data)

        assert updated is not None
        assert updated.mood == "sad"
        assert updated.note == "更新后的备注"

    @pytest.mark.asyncio
    async def test_update_salary_amount_reencrypts(self, db_session: AsyncSession):
        """测试更新金额时重新加密"""
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

        # 创建记录
        salary = await TestDataFactory.create_salary(
            db_session, user.id, config.id,
            amount=10000
        )

        # 保存旧的加密数据
        old_encrypted = salary.amount_encrypted
        old_salt = salary.encryption_salt

        # 更新金额
        update_data = SalaryRecordUpdate(amount=15000.50)

        updated = await update(db_session, salary.id, user.id, update_data)

        # 验证加密数据已改变
        assert updated.amount_encrypted != old_encrypted
        assert updated.encryption_salt != old_salt

        # 验证新金额正确
        from app.utils.encryption import decrypt_amount
        decrypted = decrypt_amount(updated.amount_encrypted, updated.encryption_salt)
        assert decrypted == 15000.50

    @pytest.mark.asyncio
    async def test_update_salary_partial_fields(self, db_session: AsyncSession):
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

        # 创建记录
        salary = await TestDataFactory.create_salary(
            db_session, user.id, config.id,
            mood="happy",
            note="原始备注"
        )

        # 只更新 mood
        update_data = SalaryRecordUpdate(mood="angry")

        updated = await update(db_session, salary.id, user.id, update_data)

        assert updated.mood == "angry"
        assert updated.note == "原始备注"  # note 保持不变

    @pytest.mark.asyncio
    async def test_update_salary_not_found(self, db_session: AsyncSession):
        """测试更新不存在的记录"""
        user = await TestDataFactory.create_user(db_session)

        update_data = SalaryRecordUpdate(mood="sad")

        with pytest.raises(NotFoundException) as exc_info:
            await update(db_session, "nonexistent_id", user.id, update_data)

        assert "工资记录不存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_salary_wrong_user(self, db_session: AsyncSession):
        """测试用户不能更新其他用户的记录"""
        user1 = await TestDataFactory.create_user(db_session)
        user2 = await TestDataFactory.create_user(db_session)

        # 创建 payday config
        from app.models.payday import PaydayConfig
        config1 = PaydayConfig(user_id=user1.id, job_name="工作1", payday=25)
        db_session.add(config1)
        await db_session.commit()
        await db_session.refresh(config1)

        # user1 创建记录
        salary = await TestDataFactory.create_salary(
            db_session, user1.id, config1.id
        )

        # user2 尝试更新
        update_data = SalaryRecordUpdate(mood="sad")

        with pytest.raises(NotFoundException):
            await update(db_session, salary.id, user2.id, update_data)

    @pytest.mark.asyncio
    async def test_update_salary_all_fields(self, db_session: AsyncSession):
        """测试更新所有可更新字段"""
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

        # 创建记录
        salary = await TestDataFactory.create_salary(
            db_session, user.id, config.id,
            salary_type="normal",
            mood="happy"
        )

        # 更新所有字段
        update_data = SalaryRecordUpdate(
            amount=20000.00,
            payday_date=date(2024, 6, 1),
            salary_type="bonus",
            mood="relief",
            images=["https://example.com/new.jpg"],
            note="完全更新的记录"
        )

        updated = await update(db_session, salary.id, user.id, update_data)

        assert updated.payday_date == date(2024, 6, 1)
        assert updated.salary_type == "bonus"
        assert updated.mood == "relief"
        assert updated.images == ["https://example.com/new.jpg"]
        assert updated.note == "完全更新的记录"


class TestDeleteSalary:
    """测试删除工资记录"""

    @pytest.mark.asyncio
    async def test_delete_salary_success(self, db_session: AsyncSession):
        """测试成功删除工资记录"""
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

        # 创建记录
        salary = await TestDataFactory.create_salary(
            db_session, user.id, config.id
        )

        # 删除
        result = await delete(db_session, salary.id, user.id)

        assert result is True

        # 验证已删除
        found = await get_by_id(db_session, salary.id, user.id)
        assert found is None

    @pytest.mark.asyncio
    async def test_delete_salary_not_found(self, db_session: AsyncSession):
        """测试删除不存在的记录"""
        user = await TestDataFactory.create_user(db_session)

        result = await delete(db_session, "nonexistent_id", user.id)

        assert result is False

    @pytest.mark.asyncio
    async def test_delete_salary_wrong_user(self, db_session: AsyncSession):
        """测试用户不能删除其他用户的记录"""
        user1 = await TestDataFactory.create_user(db_session)
        user2 = await TestDataFactory.create_user(db_session)

        # 创建 payday config
        from app.models.payday import PaydayConfig
        config1 = PaydayConfig(user_id=user1.id, job_name="工作1", payday=25)
        db_session.add(config1)
        await db_session.commit()
        await db_session.refresh(config1)

        # user1 创建记录
        salary = await TestDataFactory.create_salary(
            db_session, user1.id, config1.id
        )

        # user2 尝试删除
        result = await delete(db_session, salary.id, user2.id)

        assert result is False

        # 验证记录仍然存在
        found = await get_by_id(db_session, salary.id, user1.id)
        assert found is not None


class TestAdminFunctions:
    """测试管理员功能"""

    @pytest.mark.asyncio
    async def test_get_by_id_for_admin(self, db_session: AsyncSession):
        """测试管理员获取任意记录"""
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

        # 创建记录
        salary = await TestDataFactory.create_salary(
            db_session, user.id, config.id
        )

        # 管理员获取（不需要 user_id）
        found = await get_by_id_for_admin(db_session, salary.id)

        assert found is not None
        assert found.id == salary.id

    @pytest.mark.asyncio
    async def test_get_by_id_for_admin_not_found(self, db_session: AsyncSession):
        """测试管理员获取不存在的记录"""
        found = await get_by_id_for_admin(db_session, "nonexistent_id")

        assert found is None

    @pytest.mark.asyncio
    async def test_delete_for_admin(self, db_session: AsyncSession):
        """测试管理员删除任意记录"""
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

        # 创建记录
        salary = await TestDataFactory.create_salary(
            db_session, user.id, config.id
        )

        # 管理员删除
        result = await delete_for_admin(db_session, salary.id)

        assert result is True

        # 验证已删除
        found = await get_by_id_for_admin(db_session, salary.id)
        assert found is None

    @pytest.mark.asyncio
    async def test_delete_for_admin_not_found(self, db_session: AsyncSession):
        """测试管理员删除不存在的记录"""
        result = await delete_for_admin(db_session, "nonexistent_id")

        assert result is False

    @pytest.mark.asyncio
    async def test_update_risk_for_admin_approve(self, db_session: AsyncSession):
        """测试管理员审核通过"""
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

        # 创建记录
        salary = await TestDataFactory.create_salary(
            db_session, user.id, config.id
        )

        # 管理员审核通过
        updated = await update_risk_for_admin(db_session, salary.id, "approved")

        assert updated is not None
        assert updated.risk_status == "approved"
        assert updated.risk_check_time is not None

    @pytest.mark.asyncio
    async def test_update_risk_for_admin_reject(self, db_session: AsyncSession):
        """测试管理员审核拒绝"""
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

        # 创建记录
        salary = await TestDataFactory.create_salary(
            db_session, user.id, config.id
        )

        # 管理员审核拒绝
        updated = await update_risk_for_admin(db_session, salary.id, "rejected")

        assert updated is not None
        assert updated.risk_status == "rejected"
        assert updated.risk_check_time is not None

    @pytest.mark.asyncio
    async def test_update_risk_for_admin_not_found(self, db_session: AsyncSession):
        """测试管理员审核不存在的记录"""
        with pytest.raises(NotFoundException) as exc_info:
            await update_risk_for_admin(db_session, "nonexistent_id", "approved")

        assert "工资记录不存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_risk_for_admin_invalid_status(self, db_session: AsyncSession):
        """测试管理员使用无效的状态"""
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

        # 创建记录
        salary = await TestDataFactory.create_salary(
            db_session, user.id, config.id
        )

        # 使用无效的状态
        with pytest.raises(ValidationException) as exc_info:
            await update_risk_for_admin(db_session, salary.id, "invalid_status")

        assert "risk_status 必须是 approved 或 rejected" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_list_all_for_admin(self, db_session: AsyncSession):
        """测试管理员获取所有工资记录"""
        # 创建多个用户
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

        # 创建记录
        await TestDataFactory.create_salary(db_session, user1.id, config1.id)
        await TestDataFactory.create_salary(db_session, user1.id, config1.id)
        await TestDataFactory.create_salary(db_session, user2.id, config2.id)

        # 管理员获取所有记录
        records, total = await list_all_for_admin(db_session)

        assert len(records) == 3
        assert total == 3
        # 验证返回的是字典（已解密）
        assert all(isinstance(r, dict) for r in records)
        assert all("amount" in r for r in records)

    @pytest.mark.asyncio
    async def test_list_all_for_admin_pagination(self, db_session: AsyncSession):
        """测试管理员分页获取记录"""
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

        # 创建5条记录
        for i in range(5):
            await TestDataFactory.create_salary(db_session, user.id, config.id)

        # 分页获取
        page1, total1 = await list_all_for_admin(db_session, limit=2, offset=0)
        page2, total2 = await list_all_for_admin(db_session, limit=2, offset=2)
        page3, total3 = await list_all_for_admin(db_session, limit=2, offset=4)

        assert len(page1) == 2
        assert len(page2) == 2
        assert len(page3) == 1
        assert total1 == total2 == total3 == 5

    @pytest.mark.asyncio
    async def test_list_all_for_admin_ordering(self, db_session: AsyncSession):
        """测试管理员记录排序"""
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

        # 创建多条记录（创建时间会有差异）
        import time
        salaries = []
        for i in range(3):
            salary = await TestDataFactory.create_salary(
                db_session, user.id, config.id
            )
            salaries.append(salary)
            time.sleep(0.01)  # 确保创建时间不同

        # 获取记录
        records, total = await list_all_for_admin(db_session)

        # 验证按创建时间倒序（最新的在前）
        assert total == 3
        assert records[0]["id"] == salaries[2].id
        assert records[1]["id"] == salaries[1].id
        assert records[2]["id"] == salaries[0].id
