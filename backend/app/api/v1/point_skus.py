"""积分商品SKU管理API - Sprint 4.7 SKU管理系统"""
from typing import Optional

from app.core.database import get_db
from app.core.deps import get_current_admin_user
from app.core.exceptions import success_response
from app.models.user import User
from app.schemas.point_sku import (SKUBatchUpdate, SKUCreate, SKUResponse, SKUUpdate,
                                   SpecificationCreate, SpecificationResponse, SpecificationUpdate,
                                   SpecificationValueCreate, SpecificationValueResponse,
                                   SpecificationValueUpdate)
from app.services.point_sku_service import (batch_update_skus, create_sku, create_spec_value,
                                            create_specification, delete_sku, delete_spec_value,
                                            delete_specification, list_skus, list_specifications,
                                            update_sku)
from app.services.point_sku_service import update_specification as service_update_specification
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/admin", tags=["point-skus"])


# ============== 规格管理 ==============

@router.post("/point-products/{product_id}/specifications")
async def create_product_specification(
    product_id: str,
    body: SpecificationCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """创建商品规格（管理员）"""
    spec = await create_specification(
        db,
        product_id,
        body.name,
        body.sort_order,
    )

    return success_response(
        data={"id": spec.id},
        message="规格创建成功"
    )


@router.get("/point-products/{product_id}/specifications")
async def get_product_specifications(
    product_id: str,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取商品的规格列表（管理员）"""
    specs = await list_specifications(db, product_id)

    data = [SpecificationResponse.from_db(spec).model_dump() for spec in specs]

    return success_response(data={"specifications": data, "total": len(data)})


@router.put("/specifications/{spec_id}")
async def update_specification(
    spec_id: str,
    body: SpecificationUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """更新规格（管理员）"""
    await service_update_specification(
        db,
        spec_id,
        **body.model_dump(exclude_unset=True)
    )

    return success_response(message="规格更新成功")


@router.delete("/specifications/{spec_id}")
async def remove_specification(
    spec_id: str,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """删除规格（管理员）"""
    await delete_specification(db, spec_id)

    return success_response(message="规格已删除")


# ============== 规格值管理 ==============

@router.post("/specifications/{specification_id}/values")
async def create_specification_value(
    specification_id: str,
    body: SpecificationValueCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """创建规格值（管理员）"""
    spec_value = await create_spec_value(
        db,
        specification_id,
        body.value,
        body.sort_order,
    )

    return success_response(
        data={"id": spec_value.id},
        message="规格值创建成功"
    )


@router.get("/specifications/{specification_id}/values")
async def get_specification_values(
    specification_id: str,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取规格的值列表（管理员）"""
    from app.services.point_sku_service import list_specification_values

    values = await list_specification_values(db, specification_id)

    data = [SpecificationValueResponse.from_db(v).model_dump() for v in values]

    return success_response(data={"values": data, "total": len(data)})


@router.put("/specification-values/{value_id}")
async def update_specification_value(
    value_id: str,
    body: SpecificationValueUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """更新规格值（管理员）"""
    from app.services.point_sku_service import \
        update_specification_value as service_update_spec_value

    await service_update_spec_value(
        db,
        value_id,
        **body.model_dump(exclude_unset=True)
    )

    return success_response(message="规格值更新成功")


@router.delete("/specification-values/{value_id}")
async def remove_specification_value(
    value_id: str,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """删除规格值（管理员）"""
    await delete_spec_value(db, value_id)

    return success_response(message="规格值已删除")


# ============== SKU管理 ==============

@router.get("/point-products/{product_id}/skus")
async def get_product_skus(
    product_id: str,
    active_only: bool = False,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取商品的SKU列表（管理员）"""
    skus = await list_skus(db, product_id, active_only=active_only)

    data = [SKUResponse.from_db(sku).model_dump() for sku in skus]

    return success_response(data={"skus": data, "total": len(data)})


@router.post("/point-products/{product_id}/skus")
async def create_product_sku(
    product_id: str,
    body: SKUCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """创建SKU（管理员）"""
    sku = await create_sku(
        db,
        product_id,
        body.sku_code,
        body.specs,
        body.points_cost,
        body.stock,
        body.stock_unlimited,
        body.image_url,
        body.sort_order,
    )

    return success_response(
        data={"id": sku.id},
        message="SKU创建成功"
    )


@router.put("/skus/{sku_id}")
async def update_product_sku(
    sku_id: str,
    body: SKUUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """更新SKU（管理员）"""
    await update_sku(
        db,
        sku_id,
        **body.model_dump(exclude_unset=True)
    )

    return success_response(message="SKU更新成功")


@router.delete("/skus/{sku_id}")
async def remove_product_sku(
    sku_id: str,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """删除SKU（管理员，软删除）"""
    await delete_sku(db, sku_id)

    return success_response(message="SKU已删除")


@router.post("/skus/batch-update")
async def batch_update_product_skus(
    body: SKUBatchUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """批量更新SKU（管理员）"""
    # 转换为服务层期望的格式
    updates = [sku.model_dump(exclude_unset=True) for sku in body.skus]

    await batch_update_skus(db, updates)

    return success_response(message=f"成功更新{len(body.skus)}个SKU")
