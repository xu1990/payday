"""
单元测试 - 发薪日服务 (app.services.payday_service)
"""
import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.models.payday import PaydayConfig
from app.services.payday_service import (
    list_by_user,
    get_by_id,
    create,
    update,
    delete,
)
from app.schemas.payday import PaydayConfigCreate, PaydayConfigUpdate
from app.core.exceptions import NotFoundException


@pytest.mark.asyncio
class TestListByUser:
    """测试获取用户发薪日配置列表"""

    async def test_list_empty_configs(self, db_session: AsyncSession):
        """测试空列表"""
        result = await list_by_user(db_session, user_id="test_user_id")
        assert result == []

    async def test_list_configs_by_user(self, db_session: AsyncSession):
        """测试获取用户的配置列表"""
        # 创建配置
        config1 = PaydayConfig(
            user_id="test_user_id",
            job_name="工作1",
            payday=15,
            calendar_type="solar",
            is_active=1,
        )
        config2 = PaydayConfig(
            user_id="test_user_id",
            job_name="工作2",
            payday=25,
            calendar_type="lunar",
            is_active=1,
        )
        # 创建其他用户的配置
        other_config = PaydayConfig(
            user_id="other_user_id",
            job_name="其他工作",
            payday=10,
            calendar_type="solar",
            is_active=1,
        )

        db_session.add(config1)
        db_session.add(config2)
        db_session.add(other_config)
        await db_session.commit()

        result = await list_by_user(db_session, user_id="test_user_id")

        # 应该只返回test_user_id的配置
        assert len(result) == 2
        assert all(c.user_id == "test_user_id" for c in result)

    async def test_list_sorted_by_created_at(self, db_session: AsyncSession):
        """测试按创建时间排序"""
        config1 = PaydayConfig(
            user_id="test_user_id",
            job_name="工作1",
            payday=15,
            calendar_type="solar",
            is_active=1,
        )
        db_session.add(config1)
        await db_session.commit()

        config2 = PaydayConfig(
            user_id="test_user_id",
            job_name="工作2",
            payday=25,
            calendar_type="lunar",
            is_active=1,
        )
        db_session.add(config2)
        await db_session.commit()

        result = await list_by_user(db_session, user_id="test_user_id")

        # 应该按创建时间排序
        assert len(result) == 2
        assert result[0].created_at <= result[1].created_at


@pytest.mark.asyncio
class TestGetById:
    """测试通过ID获取发薪日配置"""

    async def test_get_by_id_found(self, db_session: AsyncSession):
        """测试找到配置"""
        config = PaydayConfig(
            user_id="test_user_id",
            job_name="工作1",
            payday=15,
            calendar_type="solar",
            is_active=1,
        )
        db_session.add(config)
        await db_session.commit()
        await db_session.refresh(config)

        result = await get_by_id(db_session, config_id=config.id, user_id="test_user_id")

        assert result is not None
        assert result.id == config.id
        assert result.job_name == "工作1"

    async def test_get_by_id_not_found(self, db_session: AsyncSession):
        """测试配置不存在"""
        result = await get_by_id(db_session, config_id="nonexistent_id", user_id="test_user_id")
        assert result is None

    async def test_get_by_id_wrong_user(self, db_session: AsyncSession):
        """测试获取其他用户的配置"""
        config = PaydayConfig(
            user_id="other_user_id",
            job_name="工作1",
            payday=15,
            calendar_type="solar",
            is_active=1,
        )
        db_session.add(config)
        await db_session.commit()

        result = await get_by_id(db_session, config_id=config.id, user_id="test_user_id")

        assert result is None


@pytest.mark.asyncio
class TestCreate:
    """测试创建发薪日配置"""

    async def test_create_success(self, db_session: AsyncSession):
        """测试成功创建"""
        data = PaydayConfigCreate(
            job_name="新工作",
            payday=20,
            calendar_type="solar",
            estimated_salary=10000,
            is_active=1,
        )

        result = await create(db_session, user_id="test_user_id", data=data)

        assert result.id is not None
        assert result.user_id == "test_user_id"
        assert result.job_name == "新工作"
        assert result.payday == 20
        assert result.calendar_type == "solar"
        assert result.estimated_salary == 10000
        assert result.is_active == 1

    async def test_create_with_minimal_fields(self, db_session: AsyncSession):
        """测试只填必填字段"""
        data = PaydayConfigCreate(
            job_name="工作",
            payday=15,
            calendar_type="solar",
            is_active=1,
        )

        result = await create(db_session, user_id="test_user_id", data=data)

        assert result.id is not None
        assert result.job_name == "工作"
        assert result.estimated_salary is None

    async def test_create_rollback_on_error(self, db_session: AsyncSession):
        """测试数据库错误时回滚"""
        data = PaydayConfigCreate(
            job_name="工作",
            payday=15,
            calendar_type="solar",
            is_active=1,
        )

        # Mock commit to raise error
        async def mock_commit():
            raise SQLAlchemyError("Database error")

        db_session.commit = mock_commit

        with pytest.raises(SQLAlchemyError):
            await create(db_session, user_id="test_user_id", data=data)


@pytest.mark.asyncio
class TestUpdate:
    """测试更新发薪日配置"""

    async def test_update_success(self, db_session: AsyncSession):
        """测试成功更新"""
        config = PaydayConfig(
            user_id="test_user_id",
            job_name="工作",
            payday=15,
            calendar_type="solar",
            is_active=1,
        )
        db_session.add(config)
        await db_session.commit()
        await db_session.refresh(config)

        data = PaydayConfigUpdate(
            job_name="新工作名称",
            payday=20,
        )

        result = await update(db_session, config_id=config.id, user_id="test_user_id", data=data)

        assert result is not None
        assert result.job_name == "新工作名称"
        assert result.payday == 20
        # 未更新的字段应保持原值
        assert result.calendar_type == "solar"

    async def test_update_partial_fields(self, db_session: AsyncSession):
        """测试部分字段更新"""
        config = PaydayConfig(
            user_id="test_user_id",
            job_name="工作",
            payday=15,
            calendar_type="solar",
            estimated_salary=5000,
            is_active=1,
        )
        db_session.add(config)
        await db_session.commit()
        await db_session.refresh(config)

        # 只更新 is_active
        data = PaydayConfigUpdate(is_active=0)

        result = await update(db_session, config_id=config.id, user_id="test_user_id", data=data)

        assert result is not None
        assert result.is_active == 0
        assert result.job_name == "工作"  # 其他字段不变
        assert result.payday == 15

    async def test_update_not_found(self, db_session: AsyncSession):
        """测试更新不存在的配置"""
        data = PaydayConfigUpdate(job_name="新名称")

        with pytest.raises(NotFoundException) as exc_info:
            await update(db_session, config_id="nonexistent_id", user_id="test_user_id", data=data)

        assert "不存在" in str(exc_info.value)

    async def test_update_wrong_user(self, db_session: AsyncSession):
        """测试更新其他用户的配置"""
        config = PaydayConfig(
            user_id="other_user_id",
            job_name="工作",
            payday=15,
            calendar_type="solar",
            is_active=1,
        )
        db_session.add(config)
        await db_session.commit()

        data = PaydayConfigUpdate(job_name="新名称")

        with pytest.raises(NotFoundException):
            await update(db_session, config_id=config.id, user_id="test_user_id", data=data)

    async def test_update_rollback_on_error(self, db_session: AsyncSession):
        """测试数据库错误时回滚"""
        config = PaydayConfig(
            user_id="test_user_id",
            job_name="工作",
            payday=15,
            calendar_type="solar",
            is_active=1,
        )
        db_session.add(config)
        await db_session.commit()

        # Mock commit to raise error
        async def mock_commit():
            raise SQLAlchemyError("Database error")

        original_commit = db_session.commit
        db_session.commit = mock_commit

        try:
            data = PaydayConfigUpdate(job_name="新名称")

            with pytest.raises(SQLAlchemyError):
                await update(db_session, config_id=config.id, user_id="test_user_id", data=data)
        finally:
            db_session.commit = original_commit


@pytest.mark.asyncio
class TestDelete:
    """测试删除发薪日配置"""

    async def test_delete_success(self, db_session: AsyncSession):
        """测试成功删除"""
        config = PaydayConfig(
            user_id="test_user_id",
            job_name="工作",
            payday=15,
            calendar_type="solar",
            is_active=1,
        )
        db_session.add(config)
        await db_session.commit()

        result = await delete(db_session, config_id=config.id, user_id="test_user_id")

        assert result is True

        # 验证已删除
        deleted = await get_by_id(db_session, config_id=config.id, user_id="test_user_id")
        assert deleted is None

    async def test_delete_not_found(self, db_session: AsyncSession):
        """测试删除不存在的配置"""
        result = await delete(db_session, config_id="nonexistent_id", user_id="test_user_id")
        assert result is False

    async def test_delete_wrong_user(self, db_session: AsyncSession):
        """测试删除其他用户的配置"""
        config = PaydayConfig(
            user_id="other_user_id",
            job_name="工作",
            payday=15,
            calendar_type="solar",
            is_active=1,
        )
        db_session.add(config)
        await db_session.commit()

        result = await delete(db_session, config_id=config.id, user_id="test_user_id")

        assert result is False

        # 验证配置仍然存在
        remaining = await get_by_id(db_session, config_id=config.id, user_id="other_user_id")
        assert remaining is not None

    async def test_delete_rollback_on_error(self, db_session: AsyncSession):
        """测试数据库错误时回滚"""
        config = PaydayConfig(
            user_id="test_user_id",
            job_name="工作",
            payday=15,
            calendar_type="solar",
            is_active=1,
        )
        db_session.add(config)
        await db_session.commit()

        # Mock commit to raise error
        async def mock_commit():
            raise SQLAlchemyError("Database error")

        original_commit = db_session.commit
        db_session.commit = mock_commit

        try:
            with pytest.raises(SQLAlchemyError):
                await delete(db_session, config_id=config.id, user_id="test_user_id")
        finally:
            db_session.commit = original_commit
