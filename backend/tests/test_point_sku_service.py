"""
测试积分商品SKU服务 - TDD
"""
import pytest
import json
from sqlalchemy import select
from app.models.point_product import PointProduct
from app.models.point_sku import PointSpecification, PointSpecificationValue, PointProductSKU
from app.services.point_sku_service import (
    create_specification,
    list_specifications,
    delete_specification,
    create_spec_value,
    delete_spec_value,
    create_sku,
    list_skus,
    update_sku,
    delete_sku,
    batch_update_skus,
)
from app.core.exceptions import NotFoundException, ValidationException, BusinessException


@pytest.mark.asyncio
class TestSpecificationManagement:
    """测试规格管理"""

    async def test_create_specification(self, db_session):
        """测试创建规格"""
        # 创建商品
        product = PointProduct(
            name="测试商品",
            points_cost=100,
            stock=10,
        )
        db_session.add(product)
        await db_session.commit()

        # 创建规格
        spec = await create_specification(
            db_session,
            product_id=product.id,
            name="颜色",
            sort_order=1,
        )

        assert spec.product_id == product.id
        assert spec.name == "颜色"
        assert spec.sort_order == 1

    async def test_create_specification_invalid_product(self, db_session):
        """测试创建规格时商品不存在"""
        with pytest.raises(NotFoundException, match="商品不存在"):
            await create_specification(
                db_session,
                product_id="nonexistent_id",
                name="颜色",
            )

    async def test_list_specifications(self, db_session):
        """测试获取规格列表"""
        # 创建商品
        product = PointProduct(name="测试商品", points_cost=100, stock=10)
        db_session.add(product)
        await db_session.commit()

        # 创建多个规格
        await create_specification(db_session, product_id=product.id, name="颜色", sort_order=1)
        await create_specification(db_session, product_id=product.id, name="尺寸", sort_order=2)

        # 获取列表
        specs = await list_specifications(db_session, product_id=product.id)
        assert len(specs) == 2
        assert specs[0].name == "颜色"
        assert specs[1].name == "尺寸"

    async def test_delete_specification(self, db_session):
        """测试删除规格"""
        # 创建商品和规格
        product = PointProduct(name="测试商品", points_cost=100, stock=10)
        db_session.add(product)
        await db_session.commit()

        spec = await create_specification(
            db_session, product_id=product.id, name="颜色"
        )

        # 删除规格
        result = await delete_specification(db_session, spec_id=spec.id)
        assert result is True

        # 验证已删除
        result = await db_session.execute(
            select(PointSpecification).where(PointSpecification.id == spec.id)
        )
        assert result.scalar_one_or_none() is None

    async def test_delete_specification_with_values(self, db_session):
        """测试删除有值的规格应该失败"""
        # 创建商品和规格
        product = PointProduct(name="测试商品", points_cost=100, stock=10)
        db_session.add(product)
        await db_session.commit()

        spec = await create_specification(
            db_session, product_id=product.id, name="颜色"
        )
        await create_spec_value(db_session, specification_id=spec.id, value="红色")

        # 尝试删除
        with pytest.raises(BusinessException, match="规格下有值，无法删除"):
            await delete_specification(db_session, spec_id=spec.id)


@pytest.mark.asyncio
class TestSpecificationValueManagement:
    """测试规格值管理"""

    async def test_create_spec_value(self, db_session):
        """测试创建规格值"""
        # 创建商品和规格
        product = PointProduct(name="测试商品", points_cost=100, stock=10)
        db_session.add(product)
        await db_session.commit()

        spec = await create_specification(
            db_session, product_id=product.id, name="颜色"
        )

        # 创建规格值
        value = await create_spec_value(
            db_session, specification_id=spec.id, value="红色", sort_order=1
        )

        assert value.specification_id == spec.id
        assert value.value == "红色"
        assert value.sort_order == 1

    async def test_create_spec_value_invalid_spec(self, db_session):
        """测试创建规格值时规格不存在"""
        with pytest.raises(NotFoundException, match="规格不存在"):
            await create_spec_value(
                db_session, specification_id="nonexistent_id", value="红色"
            )

    async def test_delete_spec_value(self, db_session):
        """测试删除规格值"""
        # 创建商品、规格和规格值
        product = PointProduct(name="测试商品", points_cost=100, stock=10)
        db_session.add(product)
        await db_session.commit()

        spec = await create_specification(
            db_session, product_id=product.id, name="颜色"
        )
        value = await create_spec_value(db_session, specification_id=spec.id, value="红色")

        # 删除规格值
        result = await delete_spec_value(db_session, value_id=value.id)
        assert result is True

        # 验证已删除
        result = await db_session.execute(
            select(PointSpecificationValue).where(
                PointSpecificationValue.id == value.id
            )
        )
        assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
class TestSKUManagement:
    """测试SKU管理"""

    async def test_create_sku(self, db_session):
        """测试创建SKU"""
        # 创建商品
        product = PointProduct(name="测试商品", points_cost=100, stock=10)
        db_session.add(product)
        await db_session.commit()

        # 创建SKU
        specs = {"颜色": "红色", "尺寸": "L"}
        sku = await create_sku(
            db_session,
            product_id=product.id,
            sku_code="RED-L",
            specs=specs,
            points_cost=100,
            stock=10,
            stock_unlimited=False,
        )

        assert sku.product_id == product.id
        assert sku.sku_code == "RED-L"
        assert json.loads(sku.specs) == specs
        assert sku.points_cost == 100
        assert sku.stock == 10
        assert sku.stock_unlimited is False

    async def test_create_sku_invalid_product(self, db_session):
        """测试创建SKU时商品不存在"""
        with pytest.raises(NotFoundException, match="商品不存在"):
            await create_sku(
                db_session,
                product_id="nonexistent_id",
                sku_code="TEST",
                specs={"颜色": "红色"},
                points_cost=100,
            )

    async def test_create_sku_duplicate_code(self, db_session):
        """测试创建重复SKU编码"""
        # 创建商品
        product = PointProduct(name="测试商品", points_cost=100, stock=10)
        db_session.add(product)
        await db_session.commit()

        # 创建第一个SKU
        await create_sku(
            db_session,
            product_id=product.id,
            sku_code="RED-L",
            specs={"颜色": "红色"},
            points_cost=100,
        )

        # 尝试创建重复编码
        with pytest.raises(BusinessException, match="SKU编码已存在"):
            await create_sku(
                db_session,
                product_id=product.id,
                sku_code="RED-L",
                specs={"颜色": "蓝色"},
                points_cost=100,
            )

    async def test_list_skus(self, db_session):
        """测试获取SKU列表"""
        # 创建商品
        product = PointProduct(name="测试商品", points_cost=100, stock=10)
        db_session.add(product)
        await db_session.commit()

        # 创建多个SKU
        await create_sku(
            db_session,
            product_id=product.id,
            sku_code="RED-L",
            specs={"颜色": "红色", "尺寸": "L"},
            points_cost=100,
            sort_order=1,
        )
        await create_sku(
            db_session,
            product_id=product.id,
            sku_code="BLUE-M",
            specs={"颜色": "蓝色", "尺寸": "M"},
            points_cost=100,
            sort_order=2,
        )

        # 获取列表
        skus = await list_skus(db_session, product_id=product.id)
        assert len(skus) == 2
        assert skus[0].sku_code == "RED-L"
        assert skus[1].sku_code == "BLUE-M"

    async def test_list_skus_active_only(self, db_session):
        """测试只获取启用的SKU"""
        # 创建商品
        product = PointProduct(name="测试商品", points_cost=100, stock=10)
        db_session.add(product)
        await db_session.commit()

        # 创建SKU
        sku = await create_sku(
            db_session,
            product_id=product.id,
            sku_code="RED-L",
            specs={"颜色": "红色"},
            points_cost=100,
        )

        # 禁用SKU
        await update_sku(db_session, sku_id=sku.id, is_active=False)

        # 获取启用列表
        skus = await list_skus(db_session, product_id=product.id, active_only=True)
        assert len(skus) == 0

        # 获取全部列表
        all_skus = await list_skus(db_session, product_id=product.id, active_only=False)
        assert len(all_skus) == 1

    async def test_update_sku(self, db_session):
        """测试更新SKU"""
        # 创建商品和SKU
        product = PointProduct(name="测试商品", points_cost=100, stock=10)
        db_session.add(product)
        await db_session.commit()

        sku = await create_sku(
            db_session,
            product_id=product.id,
            sku_code="RED-L",
            specs={"颜色": "红色"},
            points_cost=100,
            stock=10,
        )

        # 更新SKU
        updated = await update_sku(
            db_session,
            sku_id=sku.id,
            points_cost=150,
            stock=20,
            image_url="http://example.com/image.jpg",
        )

        assert updated.points_cost == 150
        assert updated.stock == 20
        assert updated.image_url == "http://example.com/image.jpg"

    async def test_update_sku_invalid_id(self, db_session):
        """测试更新不存在的SKU"""
        with pytest.raises(NotFoundException, match="SKU不存在"):
            await update_sku(db_session, sku_id="nonexistent_id", points_cost=150)

    async def test_delete_sku(self, db_session):
        """测试删除SKU（软删除）"""
        # 创建商品和SKU
        product = PointProduct(name="测试商品", points_cost=100, stock=10)
        db_session.add(product)
        await db_session.commit()

        sku = await create_sku(
            db_session,
            product_id=product.id,
            sku_code="RED-L",
            specs={"颜色": "红色"},
            points_cost=100,
        )

        # 删除SKU
        result = await delete_sku(db_session, sku_id=sku.id)
        assert result is True

        # 验证已禁用
        result = await db_session.execute(
            select(PointProductSKU).where(PointProductSKU.id == sku.id)
        )
        deleted_sku = result.scalar_one_or_none()
        assert deleted_sku is not None
        assert deleted_sku.is_active is False

    async def test_batch_update_skus(self, db_session):
        """测试批量更新SKU"""
        # 创建商品
        product = PointProduct(name="测试商品", points_cost=100, stock=10)
        db_session.add(product)
        await db_session.commit()

        # 创建多个SKU
        sku1 = await create_sku(
            db_session,
            product_id=product.id,
            sku_code="RED-L",
            specs={"颜色": "红色"},
            points_cost=100,
            stock=10,
        )
        sku2 = await create_sku(
            db_session,
            product_id=product.id,
            sku_code="BLUE-M",
            specs={"颜色": "蓝色"},
            points_cost=100,
            stock=15,
        )

        # 批量更新
        updates = [
            {"id": sku1.id, "stock": 5, "points_cost": 120},
            {"id": sku2.id, "stock": 8, "points_cost": 130},
        ]
        await batch_update_skus(db_session, updates=updates)

        # 验证更新
        result = await db_session.execute(
            select(PointProductSKU).where(PointProductSKU.id == sku1.id)
        )
        updated_sku1 = result.scalar_one()
        assert updated_sku1.stock == 5
        assert updated_sku1.points_cost == 120

        result = await db_session.execute(
            select(PointProductSKU).where(PointProductSKU.id == sku2.id)
        )
        updated_sku2 = result.scalar_one()
        assert updated_sku2.stock == 8
        assert updated_sku2.points_cost == 130

    async def test_batch_update_skus_partial_failure(self, db_session):
        """测试批量更新时部分SKU不存在"""
        # 创建商品
        product = PointProduct(name="测试商品", points_cost=100, stock=10)
        db_session.add(product)
        await db_session.commit()

        # 创建SKU
        sku = await create_sku(
            db_session,
            product_id=product.id,
            sku_code="RED-L",
            specs={"颜色": "红色"},
            points_cost=100,
            stock=10,
        )

        # 批量更新，包含不存在的SKU
        updates = [
            {"id": sku.id, "stock": 5},
            {"id": "nonexistent_id", "stock": 8},
        ]

        with pytest.raises(NotFoundException, match="SKU不存在"):
            await batch_update_skus(db_session, updates=updates)
