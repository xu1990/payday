"""
套餐商品管理服务 (Bundle Product Service)

处理套餐商品的完整生命周期管理：
1. create_pre_configured_bundle - 创建预配置套餐（固定组件）
2. create_custom_bundle - 创建自定义套餐（用户自选组件）
3. get_bundle_components - 获取套餐组件列表
4. calculate_bundle_price - 计算套餐总价
5. validate_bundle_stock - 验证套餐库存是否充足
6. update_bundle_stock - 更新套餐所有组件的库存

关键特性：
- 支持预配置套餐和自定义套餐两种类型
- 自动计算套餐价格（支持积分和现金）
- 库存验证和原子性更新
- 支持必选/可选组件
- 支持无限库存SKU
- 事务管理和错误回滚
- 完整的异常处理和业务规则验证

使用场景：
- 电商组合商品（如：护肤套装、数码配件包）
- 用户自定义搭配（如：自选礼盒）
- 会员专属套餐
- 促销活动组合
"""
import logging
from typing import Any, Dict, List, Optional

from app.core.exceptions import BusinessException, NotFoundException, ValidationException
from app.models.product import Product, ProductBundle, ProductPrice, ProductSKU
from app.models.user import User
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class BundleProductService:
    """
    套餐商品管理服务

    处理套餐商品（bundle products）的创建、查询、价格计算和库存管理。
    支持预配置套餐（fixed components）和自定义套餐（user-selected components）。

    Attributes:
        redis_client: Redis客户端实例（可选）

    Example:
        ```python
        service = BundleProductService()

        # 创建预配置套餐
        await service.create_pre_configured_bundle(
            db=db,
            bundle_data=[
                {"product_id": "prod_1", "sku_id": "sku_1", "quantity": 2},
                {"product_id": "prod_2", "sku_id": "sku_2", "quantity": 1}
            ]
        )

        # 获取套餐组件
        components = await service.get_bundle_components(db, bundle_id="bundle_123")

        # 计算价格
        total_price = await service.calculate_bundle_price(db, bundle_id="bundle_123")

        # 验证库存
        is_valid = await service.validate_bundle_stock(
            db=db,
            bundle_id="bundle_123",
            quantity=2
        )

        # 更新库存
        await service.update_bundle_stock(db, bundle_id="bundle_123", quantity=-2)
        ```
    """

    # 自定义套餐最大组件数量
    MAX_CUSTOM_BUNDLE_ITEMS = 20

    def __init__(self, redis_client=None):
        """
        初始化套餐商品服务

        Args:
            redis_client: Redis客户端实例（可选，用于缓存）
        """
        self.redis_client = redis_client

    # ==================== 创建套餐 ====================

    async def create_pre_configured_bundle(
        self,
        db: AsyncSession,
        bundle_data: List[Dict[str, Any]]
    ) -> bool:
        """
        创建预配置套餐

        为已存在的套餐商品添加固定组件。预配置套餐由管理员配置，
        用户无法修改组件，只能购买整个套餐。

        Args:
            db: 数据库会话
            bundle_data: 套餐组件列表
                [
                    {
                        "bundle_product_id": "套餐商品ID",
                        "product_id": "组件商品ID",
                        "sku_id": "组件SKU ID",
                        "quantity": 数量,
                        "is_required": 是否必选（默认true）
                    },
                    ...
                ]

        Returns:
            bool: 创建成功返回True

        Raises:
            ValidationException: 组件列表为空、数量无效
            NotFoundException: 套餐商品、组件商品或SKU不存在
            Exception: 数据库错误

        Example:
            ```python
            success = await service.create_pre_configured_bundle(
                db=db,
                bundle_data=[
                    {
                        "bundle_product_id": "bundle_123",
                        "product_id": "prod_1",
                        "sku_id": "sku_1",
                        "quantity": 2,
                        "is_required": True
                    }
                ]
            )
            ```
        """
        try:
            # 1. 验证输入
            if not bundle_data or len(bundle_data) == 0:
                raise ValidationException(
                    "组件列表不能为空",
                    code="EMPTY_COMPONENTS"
                )

            for item in bundle_data:
                quantity = item.get("quantity", 1)
                if not isinstance(quantity, int) or quantity <= 0:
                    raise ValidationException(
                        "数量必须大于0",
                        code="INVALID_QUANTITY",
                        details={"quantity": quantity}
                    )

            # 2. 获取套餐商品ID（从第一个组件）
            bundle_product_id = bundle_data[0].get("bundle_product_id")
            if not bundle_product_id:
                raise ValidationException(
                    "缺少bundle_product_id",
                    code="MISSING_BUNDLE_PRODUCT_ID"
                )

            # 3. 验证套餐商品存在
            result = await db.execute(
                select(Product).where(Product.id == bundle_product_id)
            )
            bundle_product = result.unique().scalars().first()

            if not bundle_product:
                raise NotFoundException(
                    "套餐商品不存在",
                    code="BUNDLE_PRODUCT_NOT_FOUND",
                    details={"bundle_product_id": bundle_product_id}
                )

            # 4. 验证套餐商品类型
            if bundle_product.item_type != "bundle":
                raise ValidationException(
                    "商品类型不是套餐",
                    code="NOT_BUNDLE_PRODUCT",
                    details={"item_type": bundle_product.item_type}
                )

            # 5. 创建组件
            for item in bundle_data:
                component_product_id = item.get("product_id")
                component_sku_id = item.get("sku_id")
                quantity = item.get("quantity", 1)
                is_required = item.get("is_required", True)

                # 验证组件商品存在
                result = await db.execute(
                    select(Product).where(Product.id == component_product_id)
                )
                component_product = result.unique().scalars().first()

                if not component_product:
                    raise NotFoundException(
                        "组件商品不存在",
                        code="COMPONENT_PRODUCT_NOT_FOUND",
                        details={"component_product_id": component_product_id}
                    )

                # 如果指定了SKU，验证SKU存在
                if component_sku_id:
                    result = await db.execute(
                        select(ProductSKU).where(
                            and_(
                                ProductSKU.id == component_sku_id,
                                ProductSKU.product_id == component_product_id
                            )
                        )
                    )
                    sku = result.unique().scalars().first()

                    if not sku:
                        raise NotFoundException(
                            "SKU不存在",
                            code="SKU_NOT_FOUND",
                            details={"sku_id": component_sku_id}
                        )

                # 创建套餐组件记录
                bundle_component = ProductBundle(
                    bundle_product_id=bundle_product_id,
                    component_product_id=component_product_id,
                    component_sku_id=component_sku_id,
                    quantity=quantity,
                    is_required=is_required
                )

                db.add(bundle_component)

            # 6. 提交事务
            await db.commit()

            logger.info(
                f"创建预配置套餐成功: bundle_product_id={bundle_product_id}, "
                f"组件数量={len(bundle_data)}"
            )

            return True

        except (ValidationException, NotFoundException):
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"创建预配置套餐失败: error={str(e)}")
            raise

    async def create_custom_bundle(
        self,
        db: AsyncSession,
        user_id: str,
        name: str,
        items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        创建自定义套餐

        用户自己选择组件创建的个性化套餐。系统会自动创建一个套餐商品，
        并将用户选择的组件添加到套餐中。

        Args:
            db: 数据库会话
            user_id: 用户ID
            name: 套餐名称
            items: 用户选择的商品列表
                [
                    {
                        "product_id": "商品ID",
                        "sku_id": "SKU ID",
                        "quantity": 数量
                    },
                    ...
                ]

        Returns:
            Dict: 创建的套餐信息
                {
                    "id": "套餐商品ID",
                    "name": "套餐名称",
                    "item_type": "bundle",
                    "bundle_type": "custom_builder",
                    "component_count": 组件数量
                }

        Raises:
            ValidationException: 商品列表为空或超限
            NotFoundException: 用户、商品或SKU不存在
            Exception: 数据库错误

        Example:
            ```python
            bundle = await service.create_custom_bundle(
                db=db,
                user_id="user_123",
                name="我的护肤套装",
                items=[
                    {"product_id": "prod_1", "sku_id": "sku_1", "quantity": 1},
                    {"product_id": "prod_2", "sku_id": "sku_2", "quantity": 2}
                ]
            )
            ```
        """
        try:
            # 1. 验证输入
            if not items or len(items) == 0:
                raise ValidationException(
                    "商品列表不能为空",
                    code="EMPTY_ITEMS"
                )

            if len(items) > self.MAX_CUSTOM_BUNDLE_ITEMS:
                raise ValidationException(
                    f"商品数量不能超过{self.MAX_CUSTOM_BUNDLE_ITEMS}个",
                    code="TOO_MANY_ITEMS",
                    details={
                        "max": self.MAX_CUSTOM_BUNDLE_ITEMS,
                        "actual": len(items)
                    }
                )

            # 2. 验证用户存在
            result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.unique().scalars().first()

            if not user:
                raise NotFoundException(
                    "用户不存在",
                    code="USER_NOT_FOUND",
                    details={"user_id": user_id}
                )

            # 3. 创建套餐商品
            from app.models.user import gen_uuid
            bundle_product_id = gen_uuid()

            bundle_product = Product(
                id=bundle_product_id,
                name=name,
                description=f"用户自定义套餐: {name}",
                product_type="point",
                item_type="bundle",
                bundle_type="custom_builder",
                is_active=True,
                is_virtual=False,
                sort_order=0
            )

            db.add(bundle_product)
            await db.flush()  # 获取ID

            # 4. 创建默认SKU
            sku_id = gen_uuid()
            bundle_sku = ProductSKU(
                id=sku_id,
                product_id=bundle_product_id,
                sku_code=f"BUNDLE-{bundle_product_id[:8].upper()}",
                name="默认规格",
                attributes={},
                stock=0,  # 自定义套餐库存由组件决定
                stock_unlimited=True,  # 虚拟库存
                is_active=True
            )

            db.add(bundle_sku)
            await db.flush()

            # 5. 验证商品和SKU，并创建组件
            for item in items:
                product_id = item.get("product_id")
                sku_id = item.get("sku_id")
                quantity = item.get("quantity", 1)

                # 验证商品存在
                result = await db.execute(
                    select(Product).where(Product.id == product_id)
                )
                product = result.unique().scalars().first()

                if not product:
                    raise NotFoundException(
                        "商品不存在",
                        code="PRODUCT_NOT_FOUND",
                        details={"product_id": product_id}
                    )

                # 验证SKU存在
                if sku_id:
                    result = await db.execute(
                        select(ProductSKU).where(
                            and_(
                                ProductSKU.id == sku_id,
                                ProductSKU.product_id == product_id
                            )
                        )
                    )
                    sku = result.unique().scalars().first()

                    if not sku:
                        raise NotFoundException(
                            "SKU不存在",
                            code="SKU_NOT_FOUND",
                            details={"sku_id": sku_id}
                        )

                # 创建套餐组件
                bundle_component = ProductBundle(
                    bundle_product_id=bundle_product_id,
                    component_product_id=product_id,
                    component_sku_id=sku_id,
                    quantity=quantity,
                    is_required=True
                )

                db.add(bundle_component)

            # 6. 提交事务
            await db.commit()
            await db.refresh(bundle_product)

            logger.info(
                f"创建自定义套餐成功: bundle_id={bundle_product_id}, "
                f"user_id={user_id}, 组件数量={len(items)}"
            )

            return {
                "id": bundle_product.id,
                "name": bundle_product.name,
                "item_type": bundle_product.item_type,
                "bundle_type": bundle_product.bundle_type,
                "component_count": len(items)
            }

        except (ValidationException, NotFoundException):
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"创建自定义套餐失败: user_id={user_id}, error={str(e)}")
            raise

    # ==================== 查询套餐组件 ====================

    async def get_bundle_components(
        self,
        db: AsyncSession,
        bundle_id: str
    ) -> List[Dict[str, Any]]:
        """
        获取套餐组件列表

        查询指定套餐商品的所有组件信息，包括组件商品、SKU、数量等。
        只返回活跃的组件（SKU is_active=True）。

        Args:
            db: 数据库会话
            bundle_id: 套餐商品ID

        Returns:
            List[Dict]: 组件列表
                [
                    {
                        "id": "组件ID",
                        "component_product_id": "组件商品ID",
                        "component_sku_id": "组件SKU ID",
                        "quantity": 数量,
                        "is_required": 是否必选,
                        "product_name": "商品名称",
                        "sku_name": "SKU名称"
                    },
                    ...
                ]

        Example:
            ```python
            components = await service.get_bundle_components(db, bundle_id="bundle_123")
            for component in components:
                print(f"{component['product_name']} x {component['quantity']}")
            ```
        """
        try:
            # 1. 查询套餐组件
            result = await db.execute(
                select(ProductBundle).where(
                    ProductBundle.bundle_product_id == bundle_id
                )
            )
            bundles = result.unique().scalars().all()

            if not bundles:
                return []

            # 2. 获取组件详细信息
            components = []
            for bundle in bundles:
                # 如果有SKU，检查SKU是否活跃
                if bundle.component_sku_id:
                    sku_result = await db.execute(
                        select(ProductSKU).where(ProductSKU.id == bundle.component_sku_id)
                    )
                    sku = sku_result.unique().scalars().first()

                    # 跳过非活跃SKU
                    if not sku or not sku.is_active:
                        continue

                    sku_name = sku.name
                else:
                    sku_name = None

                # 获取商品名称
                product_result = await db.execute(
                    select(Product).where(Product.id == bundle.component_product_id)
                )
                product = product_result.unique().scalars().first()

                if product:
                    product_name = product.name
                else:
                    product_name = "未知商品"

                components.append({
                    "id": bundle.id,
                    "component_product_id": bundle.component_product_id,
                    "component_sku_id": bundle.component_sku_id,
                    "quantity": bundle.quantity,
                    "is_required": bundle.is_required,
                    "product_name": product_name,
                    "sku_name": sku_name
                })

            logger.info(f"获取套餐组件成功: bundle_id={bundle_id}, 组件数量={len(components)}")

            return components

        except Exception as e:
            logger.error(f"获取套餐组件失败: bundle_id={bundle_id}, error={str(e)}")
            raise

    # ==================== 价格计算 ====================

    async def calculate_bundle_price(
        self,
        db: AsyncSession,
        bundle_id: str
    ) -> int:
        """
        计算套餐总价

        根据套餐的所有组件价格计算套餐总价。价格为所有组件的base价格之和。
        如果组件有多货币类型，会抛出异常（套餐内货币类型必须一致）。

        Args:
            db: 数据库会话
            bundle_id: 套餐商品ID

        Returns:
            int: 套餐总价（分为单位或积分）

        Raises:
            BusinessException: 未找到价格信息、货币类型不一致
            Exception: 其他错误

        Example:
            ```python
            total_price = await service.calculate_bundle_price(db, bundle_id="bundle_123")
            # 返回: 18000 (表示180元或18000积分)
            ```
        """
        try:
            # 1. 获取套餐组件
            components = await self.get_bundle_components(db, bundle_id)

            if not components:
                return 0

            # 2. 计算总价
            total_price = 0
            bundle_currency = None

            for component in components:
                sku_id = component.get("component_sku_id")
                quantity = component.get("quantity", 1)

                if not sku_id:
                    continue

                # 查询base价格
                result = await db.execute(
                    select(ProductPrice).where(
                        and_(
                            ProductPrice.sku_id == sku_id,
                            ProductPrice.price_type == "base",
                            ProductPrice.is_active == True
                        )
                    )
                )
                price = result.unique().scalars().first()

                if not price:
                    raise BusinessException(
                        f"未找到组件价格信息: {component['product_name']}",
                        code="PRICE_NOT_FOUND",
                        details={"component_sku_id": sku_id}
                    )

                # 检查货币类型一致性
                if bundle_currency is None:
                    bundle_currency = price.currency
                elif bundle_currency != price.currency:
                    raise BusinessException(
                        "套餐内货币类型不一致",
                        code="INCONSISTENT_CURRENCY",
                        details={
                            "expected": bundle_currency,
                            "actual": price.currency
                        }
                    )

                # 累加价格
                total_price += price.price_amount * quantity

            logger.info(
                f"计算套餐价格成功: bundle_id={bundle_id}, "
                f"总价={total_price}, 货币={bundle_currency}"
            )

            return total_price

        except BusinessException:
            raise
        except Exception as e:
            logger.error(f"计算套餐价格失败: bundle_id={bundle_id}, error={str(e)}")
            raise

    # ==================== 库存管理 ====================

    async def validate_bundle_stock(
        self,
        db: AsyncSession,
        bundle_id: str,
        quantity: int
    ) -> bool:
        """
        验证套餐库存是否充足

        检查套餐的所有组件库存是否足够满足指定数量的订单需求。
        无限库存的SKU（stock_unlimited=True）会被跳过检查。

        Args:
            db: 数据库会话
            bundle_id: 套餐商品ID
            quantity: 需要的数量

        Returns:
            bool: 库存充足返回True

        Raises:
            BusinessException: 库存不足
            Exception: 其他错误

        Example:
            ```python
            is_valid = await service.validate_bundle_stock(
                db=db,
                bundle_id="bundle_123",
                quantity=2
            )
            # 返回: True (库存充足) 或抛出异常 (库存不足)
            ```
        """
        try:
            # 数量为0时始终有效
            if quantity <= 0:
                return True

            # 1. 获取套餐组件
            components = await self.get_bundle_components(db, bundle_id)

            if not components:
                return True

            # 2. 检查每个组件的库存
            for component in components:
                sku_id = component.get("component_sku_id")
                component_quantity = component.get("quantity", 1)

                if not sku_id:
                    continue

                # 查询SKU库存
                result = await db.execute(
                    select(ProductSKU).where(ProductSKU.id == sku_id)
                )
                sku = result.unique().scalars().first()

                if not sku:
                    raise BusinessException(
                        f"组件SKU不存在: {component['product_name']}",
                        code="SKU_NOT_FOUND",
                        details={"sku_id": sku_id}
                    )

                # 跳过无限库存SKU
                if sku.stock_unlimited:
                    continue

                # 计算需要的库存
                required_stock = component_quantity * quantity

                # 检查库存是否充足
                if sku.stock < required_stock:
                    raise BusinessException(
                        f"组件库存不足: {component['product_name']} "
                        f"(需要: {required_stock}, 可用: {sku.stock})",
                        code="INSUFFICIENT_STOCK",
                        details={
                            "component_name": component['product_name'],
                            "required": required_stock,
                            "available": sku.stock
                        }
                    )

            logger.info(
                f"验证套餐库存成功: bundle_id={bundle_id}, quantity={quantity}"
            )

            return True

        except BusinessException:
            raise
        except Exception as e:
            logger.error(f"验证套餐库存失败: bundle_id={bundle_id}, error={str(e)}")
            raise

    async def update_bundle_stock(
        self,
        db: AsyncSession,
        bundle_id: str,
        quantity: int
    ) -> bool:
        """
        更新套餐所有组件的库存

        原子性地更新套餐所有组件的库存。用于订单下单扣减库存、
        订单取消恢复库存等场景。quantity为正数表示扣减库存，
        负数表示增加库存。

        Args:
            db: 数据库会话
            bundle_id: 套餐商品ID
            quantity: 更新数量（正数=扣减，负数=增加）

        Returns:
            bool: 更新成功返回True

        Raises:
            BusinessException: 库存不足（扣减时）
            Exception: 数据库错误

        Example:
            ```python
            # 下单扣减库存
            await service.update_bundle_stock(db, bundle_id="bundle_123", quantity=2)

            # 取消订单恢复库存
            await service.update_bundle_stock(db, bundle_id="bundle_123", quantity=-2)
            ```
        """
        try:
            # 数量为0时不做任何操作
            if quantity == 0:
                return True

            # 1. 先验证库存（扣减时）
            if quantity > 0:
                await self.validate_bundle_stock(db, bundle_id, quantity)

            # 2. 获取套餐组件
            components = await self.get_bundle_components(db, bundle_id)

            if not components:
                return True

            # 3. 更新每个组件的库存
            for component in components:
                sku_id = component.get("component_sku_id")
                component_quantity = component.get("quantity", 1)

                if not sku_id:
                    continue

                # 查询SKU
                result = await db.execute(
                    select(ProductSKU).where(ProductSKU.id == sku_id)
                )
                sku = result.unique().scalars().first()

                if not sku:
                    continue

                # 跳过无限库存SKU
                if sku.stock_unlimited:
                    continue

                # 更新库存
                stock_change = component_quantity * quantity
                sku.stock -= stock_change

                # 确保库存不为负
                if sku.stock < 0:
                    sku.stock = 0

                logger.debug(
                    f"更新SKU库存: sku_id={sku_id}, "
                    f"变化={stock_change}, 新库存={sku.stock}"
                )

            # 4. 提交事务
            await db.commit()

            logger.info(
                f"更新套餐库存成功: bundle_id={bundle_id}, quantity={quantity}"
            )

            return True

        except BusinessException:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"更新套餐库存失败: bundle_id={bundle_id}, error={str(e)}")
            raise
