"""积分商品模型 - Sprint 4.7 商品兑换系统"""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text

from .base import Base
from .user import gen_uuid


class PointProduct(Base):
    """积分商品表"""

    __tablename__ = "point_products"

    id = Column(String(36), primary_key=True, default=gen_uuid)

    # 基本信息
    name = Column(String(100), nullable=False, comment="商品名称")
    description = Column(Text, nullable=True, comment="商品描述")
    image_urls = Column(Text, nullable=True, comment="商品图片URLs (JSON数组)")

    # 价格与库存
    points_cost = Column(Integer, nullable=False, comment="积分价格")
    stock = Column(Integer, nullable=False, default=0, comment="库存数量")
    stock_unlimited = Column(Boolean, default=False, nullable=False, comment="库存无限")
    sold = Column(Integer, nullable=False, default=0, comment="已售数量")
    fake_sold = Column(Integer, nullable=False, default=0, comment="注水销量（虚拟销量）")

    # 分类与排序
    category = Column(String(50), nullable=True, comment="商品分类")
    category_id = Column(String(36), ForeignKey("point_categories.id"),
                        nullable=True, index=True, comment="分类ID")
    has_sku = Column(Boolean, default=False,
                     nullable=False, comment="是否启用SKU管理")
    sort_order = Column(Integer, default=0, nullable=False, comment="排序权重（越大越靠前）")

    # 商品类型
    product_type = Column(
        String(20),
        default="physical",
        nullable=False,
        comment="商品类型: virtual=虚拟商品, physical=实物商品, bundle=套餐商品"
    )

    # 物流方式
    shipping_method = Column(
        String(20),
        default="express",
        nullable=False,
        comment="物流方式: express=快递 delivery, self_pickup=自提, no_shipping=无需快递"
    )

    # 运费模板
    shipping_template_id = Column(
        String(36),
        ForeignKey("shipping_templates.id"),
        nullable=True,
        index=True,
        comment="运费模板ID"
    )

    # 状态
    is_active = Column(Boolean, default=True, nullable=False, comment="是否上架")
    off_shelf_reason = Column(String(255), nullable=True, comment="下架/删除原因")

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 关系
    orders = None  # relationship("PointOrder", back_populates="product")
