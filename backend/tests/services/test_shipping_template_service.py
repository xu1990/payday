"""
运费模板服务测试
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic_core import ValidationError

from app.services.shipping_service import ShippingTemplateService
from app.models.shipping import ShippingTemplate, ShippingTemplateRegion
from app.schemas.shipping import (
    ShippingTemplateCreate,
    ShippingTemplateUpdate,
    ShippingTemplateRegionCreate,
    ShippingTemplateRegionUpdate
)
from app.core.exceptions import NotFoundException, ValidationException, BusinessException


class TestCreateTemplate:
    """测试创建运费模板"""

    @pytest.mark.asyncio
    async def test_create_template_success(self, db_session: AsyncSession):
        """测试成功创建运费模板"""
        service = ShippingTemplateService(db_session)

        template_data = ShippingTemplateCreate(
            name="标准快递",
            description="全国标准快递服务",
            charge_type="weight",
            default_first_unit=1000,  # 1kg
            default_first_cost=1000,  # 10元
            default_continue_unit=500,  # 0.5kg
            default_continue_cost=500,  # 5元
            free_threshold=20000,  # 200元包邮
            estimate_days_min=2,
            estimate_days_max=5
        )

        template = await service.create_template(template_data)

        assert template.id is not None
        assert template.name == "标准快递"
        assert template.description == "全国标准快递服务"
        assert template.charge_type == "weight"
        assert template.default_first_unit == 1000
        assert template.default_first_cost == 1000
        assert template.default_continue_unit == 500
        assert template.default_continue_cost == 500
        assert template.free_threshold == 20000
        assert template.estimate_days_min == 2
        assert template.estimate_days_max == 5
        assert template.is_active is True
        assert template.created_at is not None

    @pytest.mark.asyncio
    async def test_create_template_missing_required_fields(self, db_session: AsyncSession):
        """测试创建模板时缺少必填字段"""
        service = ShippingTemplateService(db_session)

        # 缺少必填字段
        template_data = {
            "name": "测试模板"
            # 缺少其他必填字段
        }

        with pytest.raises(ValidationError):
            # 直接创建实例会触发Pydantic验证
            ShippingTemplateCreate(**template_data)

    @pytest.mark.asyncio
    async def test_create_template_invalid_charge_type(self, db_session: AsyncSession):
        """测试创建模板时使用无效的计费方式"""
        service = ShippingTemplateService(db_session)

        template_data = {
            "name": "测试模板",
            "charge_type": "invalid_type",
            "default_first_unit": 1000,
            "default_first_cost": 1000,
            "default_continue_unit": 500,
            "default_continue_cost": 500
        }

        with pytest.raises(ValidationError):
            # 直接创建实例会触发Pydantic验证
            ShippingTemplateCreate(**template_data)

    @pytest.mark.asyncio
    async def test_create_template_invalid_estimate_days(self, db_session: AsyncSession):
        """测试创建模板时设置无效的预计送达天数"""
        service = ShippingTemplateService(db_session)

        template_data = {
            "name": "测试模板",
            "charge_type": "weight",
            "default_first_unit": 1000,
            "default_first_cost": 1000,
            "default_continue_unit": 500,
            "default_continue_cost": 500,
            "estimate_days_min": 5,
            "estimate_days_max": 2
        }

        with pytest.raises(ValidationError):
            # 直接创建实例会触发Pydantic验证
            ShippingTemplateCreate(**template_data)


class TestListTemplates:
    """测试列出运费模板"""

    @pytest.mark.asyncio
    async def test_list_templates_empty(self, db_session: AsyncSession):
        """测试列出模板（空列表）"""
        service = ShippingTemplateService(db_session)
        templates = await service.list_templates()

        assert len(templates) == 0

    @pytest.mark.asyncio
    async def test_list_templates_with_data(self, db_session: AsyncSession):
        """测试列出模板（有数据）"""
        service = ShippingTemplateService(db_session)

        # 创建测试数据
        template_data1 = ShippingTemplateCreate(
            name="测试模板1",
            charge_type="weight",
            default_first_unit=1000,
            default_first_cost=1000,
            default_continue_unit=500,
            default_continue_cost=500
        )

        template1 = await service.create_template(template_data1)

        template_data2 = ShippingTemplateCreate(
            name="测试模板2",
            charge_type="quantity",
            default_first_unit=1,
            default_first_cost=500,
            default_continue_unit=1,
            default_continue_cost=200
        )

        template2 = await service.create_template(template_data2)

        templates = await service.list_templates()
        assert len(templates) == 2
        assert template1.name in [t.name for t in templates]
        assert template2.name in [t.name for t in templates]


class TestGetTemplate:
    """测试获取运费模板"""

    @pytest.mark.asyncio
    async def test_get_template_not_found(self, db_session: AsyncSession):
        """测试获取不存在的模板"""
        service = ShippingTemplateService(db_session)

        fake_id = "fake-template-id"
        with pytest.raises(NotFoundException):
            await service.get_template(fake_id)

    @pytest.mark.asyncio
    async def test_get_template_success(self, db_session: AsyncSession):
        """测试成功获取模板"""
        service = ShippingTemplateService(db_session)

        template_data = ShippingTemplateCreate(
            name="测试模板",
            charge_type="weight",
            default_first_unit=1000,
            default_first_cost=1000,
            default_continue_unit=500,
            default_continue_cost=500
        )

        created = await service.create_template(template_data)
        retrieved = await service.get_template(created.id)

        assert retrieved.id == created.id
        assert retrieved.name == created.name


class TestUpdateTemplate:
    """测试更新运费模板"""

    @pytest.mark.asyncio
    async def test_update_template_not_found(self, db_session: AsyncSession):
        """测试更新不存在的模板"""
        service = ShippingTemplateService(db_session)

        fake_id = "fake-template-id"
        update_data = ShippingTemplateUpdate(name="更新名称")

        with pytest.raises(NotFoundException):
            await service.update_template(fake_id, update_data)

    @pytest.mark.asyncio
    async def test_update_template_success(self, db_session: AsyncSession):
        """测试成功更新模板"""
        service = ShippingTemplateService(db_session)

        # 创建模板
        template_data = ShippingTemplateCreate(
            name="原始名称",
            charge_type="weight",
            default_first_unit=1000,
            default_first_cost=1000,
            default_continue_unit=500,
            default_continue_cost=500
        )

        created = await service.create_template(template_data)

        # 更新模板
        update_data = ShippingTemplateUpdate(
            name="更新名称",
            description="更新描述",
            free_threshold=30000
        )

        updated = await service.update_template(created.id, update_data)

        assert updated.name == "更新名称"
        assert updated.description == "更新描述"
        assert updated.free_threshold == 30000
        # 未更新的字段应该保持原值
        assert updated.charge_type == "weight"

    @pytest.mark.asyncio
    async def test_update_template_invalid_charge_type(self, db_session: AsyncSession):
        """测试更新模板时使用无效的计费方式"""
        service = ShippingTemplateService(db_session)

        # 创建模板
        template_data = ShippingTemplateCreate(
            name="测试模板",
            charge_type="weight",
            default_first_unit=1000,
            default_first_cost=1000,
            default_continue_unit=500,
            default_continue_cost=500
        )

        created = await service.create_template(template_data)

        # 尝试更新为无效的计费方式
        update_data_dict = {"charge_type": "invalid_type"}

        with pytest.raises(ValidationError):
            # 直接创建实例会触发Pydantic验证
            ShippingTemplateUpdate(**update_data_dict)


class TestDeleteTemplate:
    """测试删除运费模板"""

    @pytest.mark.asyncio
    async def test_delete_template_not_found(self, db_session: AsyncSession):
        """测试删除不存在的模板"""
        service = ShippingTemplateService(db_session)

        fake_id = "fake-template-id"
        with pytest.raises(NotFoundException):
            await service.delete_template(fake_id)

    @pytest.mark.asyncio
    async def test_delete_template_success(self, db_session: AsyncSession):
        """测试成功删除模板"""
        service = ShippingTemplateService(db_session)

        # 创建模板
        template_data = ShippingTemplateCreate(
            name="测试模板",
            charge_type="weight",
            default_first_unit=1000,
            default_first_cost=1000,
            default_continue_unit=500,
            default_continue_cost=500
        )

        created = await service.create_template(template_data)

        # 删除模板
        await service.delete_template(created.id)

        # 验证模板已被删除
        with pytest.raises(NotFoundException):
            await service.get_template(created.id)

    @pytest.mark.asyncio
    async def test_delete_template_with_regions(self, db_session: AsyncSession):
        """测试删除有区域配置的模板（软删除）"""
        service = ShippingTemplateService(db_session)

        # 创建模板
        template_data = ShippingTemplateCreate(
            name="测试模板",
            charge_type="weight",
            default_first_unit=1000,
            default_first_cost=1000,
            default_continue_unit=500,
            default_continue_cost=500
        )

        template = await service.create_template(template_data)

        # 创建区域
        region_data = ShippingTemplateRegionCreate(
            region_codes="110000",
            region_names="北京",
            first_unit=1000,
            first_cost=1000,
            continue_unit=500,
            continue_cost=500
        )

        await service.create_region(template.id, region_data)

        # 尝试删除模板（应该软删除）
        with pytest.raises(BusinessException) as exc_info:
            await service.delete_template(template.id)

        assert "模板下有1个区域配置，已将模板设置为停用状态" in str(exc_info.value)
        assert exc_info.value.code == "TEMPLATE_HAS_REGIONS"

        # 验证模板已被软删除
        retrieved = await service.get_template(template.id)
        assert retrieved.is_active is False


class TestCreateRegion:
    """测试创建运费模板区域配置"""

    @pytest.mark.asyncio
    async def test_create_region_success(self, db_session: AsyncSession):
        """测试成功创建区域"""
        service = ShippingTemplateService(db_session)

        # 先创建模板
        template_data = ShippingTemplateCreate(
            name="测试模板",
            charge_type="weight",
            default_first_unit=1000,
            default_first_cost=1000,
            default_continue_unit=500,
            default_continue_cost=500
        )

        template = await service.create_template(template_data)

        # 创建区域
        region_data = ShippingTemplateRegionCreate(
            region_codes="110000,120000,130000",  # 北京,天津,河北
            region_names="北京,天津,河北",
            first_unit=1000,
            first_cost=1200,
            continue_unit=500,
            continue_cost=600,
            free_threshold=15000
        )

        region = await service.create_region(template.id, region_data)

        assert region.id is not None
        assert region.template_id == template.id
        assert region.region_codes == "110000,120000,130000"
        assert region.region_names == "北京,天津,河北"
        assert region.first_unit == 1000
        assert region.first_cost == 1200
        assert region.continue_unit == 500
        assert region.continue_cost == 600
        assert region.free_threshold == 15000
        assert region.is_active is True

    @pytest.mark.asyncio
    async def test_create_region_template_not_found(self, db_session: AsyncSession):
        """测试为不存在的模板创建区域"""
        service = ShippingTemplateService(db_session)

        fake_template_id = "fake-template-id"
        region_data = ShippingTemplateRegionCreate(
            region_codes="110000",
            region_names="北京",
            first_unit=1000,
            first_cost=1000,
            continue_unit=500,
            continue_cost=500
        )

        with pytest.raises(NotFoundException):
            await service.create_region(fake_template_id, region_data)

    @pytest.mark.asyncio
    async def test_create_region_empty_codes(self, db_session: AsyncSession):
        """测试创建区域时区域代码为空"""
        service = ShippingTemplateService(db_session)

        # 先创建模板
        template_data = ShippingTemplateCreate(
            name="测试模板",
            charge_type="weight",
            default_first_unit=1000,
            default_first_cost=1000,
            default_continue_unit=500,
            default_continue_cost=500
        )

        template = await service.create_template(template_data)

        # 创建区域（空代码）
        region_data = {
            "region_codes": "",  # 空字符串
            "region_names": "北京",
            "first_unit": 1000,
            "first_cost": 1000,
            "continue_unit": 500,
            "continue_cost": 500
        }

        with pytest.raises(ValidationError):
            # 直接创建实例会触发Pydantic验证
            ShippingTemplateRegionCreate(**region_data)

    @pytest.mark.asyncio
    async def test_create_region_empty_names(self, db_session: AsyncSession):
        """测试创建区域时区域名称为空"""
        service = ShippingTemplateService(db_session)

        # 先创建模板
        template_data = ShippingTemplateCreate(
            name="测试模板",
            charge_type="weight",
            default_first_unit=1000,
            default_first_cost=1000,
            default_continue_unit=500,
            default_continue_cost=500
        )

        template = await service.create_template(template_data)

        # 创建区域（空名称）
        region_data = {
            "region_codes": "110000",
            "region_names": "",  # 空字符串
            "first_unit": 1000,
            "first_cost": 1000,
            "continue_unit": 500,
            "continue_cost": 500
        }

        with pytest.raises(ValidationError):
            # 直接创建实例会触发Pydantic验证
            ShippingTemplateRegionCreate(**region_data)


class TestListRegions:
    """测试列出运费模板区域配置"""

    @pytest.mark.asyncio
    async def test_list_regions_empty(self, db_session: AsyncSession):
        """测试列出区域（空列表）"""
        service = ShippingTemplateService(db_session)

        # 创建模板
        template_data = ShippingTemplateCreate(
            name="测试模板",
            charge_type="weight",
            default_first_unit=1000,
            default_first_cost=1000,
            default_continue_unit=500,
            default_continue_cost=500
        )

        template = await service.create_template(template_data)
        regions = await service.list_regions(template.id)

        assert len(regions) == 0

    @pytest.mark.asyncio
    async def test_list_regions_with_data(self, db_session: AsyncSession):
        """测试列出区域（有数据）"""
        service = ShippingTemplateService(db_session)

        # 创建模板
        template_data = ShippingTemplateCreate(
            name="测试模板",
            charge_type="weight",
            default_first_unit=1000,
            default_first_cost=1000,
            default_continue_unit=500,
            default_continue_cost=500
        )

        template = await service.create_template(template_data)

        # 创建区域
        region_data1 = ShippingTemplateRegionCreate(
            region_codes="110000",
            region_names="北京",
            first_unit=1000,
            first_cost=1200,
            continue_unit=500,
            continue_cost=600
        )

        region1 = await service.create_region(template.id, region_data1)

        region_data2 = ShippingTemplateRegionCreate(
            region_codes="310000",
            region_names="上海",
            first_unit=1000,
            first_cost=1000,
            continue_unit=500,
            continue_cost=500
        )

        region2 = await service.create_region(template.id, region_data2)

        regions = await service.list_regions(template.id)
        assert len(regions) == 2
        assert region1.region_codes in [r.region_codes for r in regions]
        assert region2.region_codes in [r.region_codes for r in regions]


class TestUpdateRegion:
    """测试更新运费模板区域配置"""

    @pytest.mark.asyncio
    async def test_update_region_not_found(self, db_session: AsyncSession):
        """测试更新不存在的区域"""
        service = ShippingTemplateService(db_session)

        fake_region_id = "fake-region-id"
        update_data = ShippingTemplateRegionUpdate(first_cost=1500)

        with pytest.raises(NotFoundException):
            await service.update_region(fake_region_id, update_data)

    @pytest.mark.asyncio
    async def test_update_region_success(self, db_session: AsyncSession):
        """测试成功更新区域"""
        service = ShippingTemplateService(db_session)

        # 创建模板和区域
        template_data = ShippingTemplateCreate(
            name="测试模板",
            charge_type="weight",
            default_first_unit=1000,
            default_first_cost=1000,
            default_continue_unit=500,
            default_continue_cost=500
        )

        template = await service.create_template(template_data)

        region_data = ShippingTemplateRegionCreate(
            region_codes="110000",
            region_names="北京",
            first_unit=1000,
            first_cost=1000,
            continue_unit=500,
            continue_cost=500
        )

        region = await service.create_region(template.id, region_data)

        # 更新区域
        update_data = ShippingTemplateRegionUpdate(
            first_cost=1500,
            free_threshold=20000
        )

        updated = await service.update_region(region.id, update_data)

        assert updated.first_cost == 1500
        assert updated.free_threshold == 20000
        # 未更新的字段应该保持原值
        assert updated.region_codes == region.region_codes


class TestDeleteRegion:
    """测试删除运费模板区域配置"""

    @pytest.mark.asyncio
    async def test_delete_region_not_found(self, db_session: AsyncSession):
        """测试删除不存在的区域"""
        service = ShippingTemplateService(db_session)

        fake_region_id = "fake-region-id"
        with pytest.raises(NotFoundException):
            await service.delete_region(fake_region_id)

    @pytest.mark.asyncio
    async def test_delete_region_success(self, db_session: AsyncSession):
        """测试成功删除区域"""
        service = ShippingTemplateService(db_session)

        # 创建模板和区域
        template_data = ShippingTemplateCreate(
            name="测试模板",
            charge_type="weight",
            default_first_unit=1000,
            default_first_cost=1000,
            default_continue_unit=500,
            default_continue_cost=500
        )

        template = await service.create_template(template_data)

        region_data = ShippingTemplateRegionCreate(
            region_codes="110000",
            region_names="北京",
            first_unit=1000,
            first_cost=1000,
            continue_unit=500,
            continue_cost=500
        )

        region = await service.create_region(template.id, region_data)

        # 删除区域
        await service.delete_region(region.id)

        # 验证区域已被删除
        with pytest.raises(NotFoundException):
            await service.get_region(region.id)