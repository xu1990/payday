# Points Shop Admin Module Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete the points shop admin backend module with 7 management pages (categories, SKUs, couriers, addresses, shipping, shipments, returns).

**Architecture:** Standalone pages following existing admin-web patterns, with new database models for categories/SKU/returns, service layer for business logic, and comprehensive API endpoints.

**Tech Stack:** Python 3.11+ (FastAPI, SQLAlchemy, Alembic), Vue3 (Element Plus, Pinia), MySQL 8.0+

---

## Implementation Overview

This plan implements 7 admin pages in logical order:

1. **Categories** - Foundation for product organization
2. **Couriers** - Basic shipping setup
3. **User Addresses** - View/edit customer addresses
4. **Product SKUs** - Multi-spec inventory system
5. **Shipping Templates** - Regional shipping costs
6. **Shipments** - Order fulfillment
7. **Returns** - After-sales workflow

Each task follows TDD: write test → run (fail) → implement → run (pass) → commit.

---

## Task 1: Database Models - PointCategory

**Files:**
- Create: `backend/app/models/point_category.py`
- Modify: `backend/app/models/__init__.py`

**Step 1: Write the failing test**

Create `backend/tests/models/test_point_category.py`:

```python
import pytest
from app.models.point_category import PointCategory
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_create_category(db_session: AsyncSession):
    """Test creating a root category"""
    category = PointCategory(
        name="实物奖励",
        description="实物商品奖励",
        level=1,
        sort_order=0,
        is_active=True
    )
    db_session.add(category)
    await db_session.flush()

    assert category.id is not None
    assert category.name == "实物奖励"
    assert category.level == 1
    assert category.parent_id is None


@pytest.mark.asyncio
async def test_create_subcategory(db_session: AsyncSession):
    """Test creating a subcategory with parent"""
    parent = PointCategory(
        name="实物奖励",
        level=1,
        sort_order=0
    )
    db_session.add(parent)
    await db_session.flush()

    child = PointCategory(
        name="数码产品",
        parent_id=parent.id,
        level=2,
        sort_order=0
    )
    db_session.add(child)
    await db_session.flush()

    assert child.parent_id == parent.id
    assert child.level == 2
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/models/test_point_category.py -v`

Expected: `ImportError: cannot import name 'PointCategory'`

**Step 3: Write minimal implementation**

Create `backend/app/models/point_category.py`:

```python
"""积分商品分类模型"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, Boolean, DateTime, ForeignKey

from .base import Base
from .user import gen_uuid


class PointCategory(Base):
    """积分商品分类表 - 支持多级层级"""

    __tablename__ = "point_categories"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    name = Column(String(50), nullable=False, comment="分类名称")
    description = Column(Text, nullable=True, comment="分类描述")
    parent_id = Column(String(36), ForeignKey("point_categories.id"),
                       nullable=True, index=True, comment="父分类ID")
    icon_url = Column(String(500), nullable=True, comment="分类图标URL")
    banner_url = Column(String(500), nullable=True, comment="分类横幅URL")
    level = Column(Integer, nullable=False, comment="层级(1/2/3)")
    sort_order = Column(Integer, default=0, nullable=False, comment="排序权重")
    is_active = Column(Boolean, default=True, nullable=False, comment="是否启用")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow, nullable=False)
```

Update `backend/app/models/__init__.py`:

```python
# Add import:
from .point_category import PointCategory
```

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/models/test_point_category.py -v`

Expected: PASS (2 tests)

**Step 5: Commit**

```bash
git add backend/app/models/point_category.py backend/app/models/__init__.py backend/tests/models/test_point_category.py
git commit -m "feat(models): add PointCategory model with tests"
```

---

## Task 2: Database Models - SKU System

**Files:**
- Create: `backend/app/models/point_sku.py`
- Modify: `backend/app/models/point_product.py`, `backend/app/models/__init__.py`

**Step 1: Write the failing test**

Create `backend/tests/models/test_point_sku.py`:

```python
import pytest
import json
from app.models.point_sku import PointSpecification, PointSpecificationValue, PointProductSKU
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_create_specification(db_session: AsyncSession):
    """Test creating a product specification"""
    spec = PointSpecification(
        product_id="test-product-id",
        name="颜色",
        sort_order=0
    )
    db_session.add(spec)
    await db_session.flush()

    assert spec.id is not None
    assert spec.name == "颜色"


@pytest.mark.asyncio
async def test_create_specification_value(db_session: AsyncSession):
    """Test creating specification values"""
    spec = PointSpecification(
        product_id="test-product-id",
        name="颜色"
    )
    db_session.add(spec)
    await db_session.flush()

    value = PointSpecificationValue(
        specification_id=spec.id,
        value="红色",
        sort_order=0
    )
    db_session.add(value)
    await db_session.flush()

    assert value.specification_id == spec.id
    assert value.value == "红色"


@pytest.mark.asyncio
async def test_create_sku(db_session: AsyncSession):
    """Test creating a product SKU"""
    sku = PointProductSKU(
        product_id="test-product-id",
        sku_code="PROD-RED-L",
        specs=json.dumps({"颜色": "红色", "尺寸": "L"}),
        stock=10,
        stock_unlimited=False,
        points_cost=100,
        is_active=True
    )
    db_session.add(sku)
    await db_session.flush()

    assert sku.id is not None
    assert sku.sku_code == "PROD-RED-L"
    assert json.loads(sku.specs) == {"颜色": "红色", "尺寸": "L"}
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/models/test_point_sku.py -v`

Expected: `ImportError`

**Step 3: Write minimal implementation**

Create `backend/app/models/point_sku.py`:

```python
"""积分商品SKU模型 - 多规格系统"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, Boolean, DateTime, ForeignKey

from .base import Base
from .user import gen_uuid


class PointSpecification(Base):
    """商品规格定义表（如：颜色、尺寸）"""

    __tablename__ = "point_specifications"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    product_id = Column(String(36), ForeignKey("point_products.id"),
                       nullable=False, index=True, comment="商品ID")
    name = Column(String(50), nullable=False, comment="规格名称")
    sort_order = Column(Integer, default=0, nullable=False, comment="排序权重")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class PointSpecificationValue(Base):
    """规格值表（如：红色、蓝色、L、XL）"""

    __tablename__ = "point_specification_values"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    specification_id = Column(String(36), ForeignKey("point_specifications.id"),
                             nullable=False, index=True, comment="规格ID")
    value = Column(String(50), nullable=False, comment="规格值")
    sort_order = Column(Integer, default=0, nullable=False, comment="排序权重")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class PointProductSKU(Base):
    """商品SKU表 - 多规格库存管理"""

    __tablename__ = "point_product_skus"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    product_id = Column(String(36), ForeignKey("point_products.id"),
                       nullable=False, index=True, comment="商品ID")
    sku_code = Column(String(50), unique=True, nullable=False,
                     index=True, comment="SKU编码")
    specs = Column(Text, nullable=False, comment="规格组合JSON")

    # SKU独立库存和价格
    stock = Column(Integer, default=0, nullable=False, comment="库存数量")
    stock_unlimited = Column(Boolean, default=False,
                             nullable=False, comment="库存无限")
    points_cost = Column(Integer, nullable=False, comment="积分价格")
    image_url = Column(String(500), nullable=True, comment="SKU专属图片")

    is_active = Column(Boolean, default=True, nullable=False, comment="是否启用")
    sort_order = Column(Integer, default=0, nullable=False, comment="排序权重")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow, nullable=False)
```

Update `backend/app/models/point_product.py` - add fields:

```python
# Add after the category field:
category_id = Column(String(36), ForeignKey("point_categories.id"),
                    nullable=True, index=True, comment="分类ID")
has_sku = Column(Boolean, default=False,
                 nullable=False, comment="是否启用SKU管理")
```

Update `backend/app/models/__init__.py`:

```python
from .point_sku import PointSpecification, PointSpecificationValue, PointProductSKU
```

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/models/test_point_sku.py -v`

Expected: PASS (3 tests)

**Step 5: Commit**

```bash
git add backend/app/models/point_sku.py backend/app/models/point_product.py backend/app/models/__init__.py backend/tests/models/test_point_sku.py
git commit -m "feat(models): add SKU system models (Specification, SpecificationValue, ProductSKU)"
```

---

## Task 3: Database Models - PointReturn

**Files:**
- Create: `backend/app/models/point_return.py`
- Modify: `backend/app/models/__init__.py`

**Step 1: Write the failing test**

Create `backend/tests/models/test_point_return.py`:

```python
import pytest
from app.models.point_return import PointReturn
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_create_return_request(db_session: AsyncSession):
    """Test creating a return request"""
    return_request = PointReturn(
        order_id="test-order-id",
        reason="商品质量问题",
        status="requested"
    )
    db_session.add(return_request)
    await db_session.flush()

    assert return_request.id is not None
    assert return_request.status == "requested"
    assert return_request.reason == "商品质量问题"


@pytest.mark.asyncio
async def test_approve_return(db_session: AsyncSession):
    """Test approving a return"""
    return_request = PointReturn(
        order_id="test-order-id",
        reason="不想要了",
        status="requested"
    )
    db_session.add(return_request)
    await db_session.flush()

    return_request.status = "approved"
    return_request.admin_notes = "同意退款"
    return_request.admin_id = "test-admin-id"

    await db_session.flush()

    assert return_request.status == "approved"
    assert return_request.admin_notes == "同意退款"
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/models/test_point_return.py -v`

Expected: `ImportError`

**Step 3: Write minimal implementation**

Create `backend/app/models/point_return.py`:

```python
"""积分订单退货模型"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Enum

from .base import Base
from .user import gen_uuid


class PointReturn(Base):
    """积分订单退货表"""

    __tablename__ = "point_returns"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    order_id = Column(String(36), ForeignKey("point_orders.id"),
                     nullable=False, index=True, comment="订单ID")
    reason = Column(Text, nullable=False, comment="退货原因")

    status = Column(
        Enum("requested", "approved", "rejected",
             name="point_return_status"),
        default="requested",
        nullable=False,
        comment="退货状态"
    )

    admin_notes = Column(Text, nullable=True, comment="管理员备注")
    admin_id = Column(String(36), ForeignKey("admin_users.id"),
                     nullable=True, comment="处理管理员ID")

    created_at = Column(DateTime, default=datetime.utcnow,
                       nullable=False, comment="申请时间")
    processed_at = Column(DateTime, nullable=True, comment="处理时间")
```

Update `backend/app/models/__init__.py`:

```python
from .point_return import PointReturn
```

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/models/test_point_return.py -v`

Expected: PASS (2 tests)

**Step 5: Commit**

```bash
git add backend/app/models/point_return.py backend/app/models/__init__.py backend/tests/models/test_point_return.py
git commit -m "feat(models): add PointReturn model for returns workflow"
```

---

## Task 4: PointOrder Model Updates

**Files:**
- Modify: `backend/app/models/point_order.py`

**Step 1: Write the failing test**

Update `backend/tests/models/test_point_order.py` (or create if not exists):

```python
@pytest.mark.asyncio
async def test_order_with_sku_and_address(db_session: AsyncSession):
    """Test order with SKU and address references"""
    order = PointOrder(
        user_id="test-user-id",
        product_id="test-product-id",
        order_number="PO20250101001",
        product_name="测试商品",
        points_cost=100,
        sku_id="test-sku-id",
        address_id="test-address-id",
        shipment_id="test-shipment-id"
    )
    db_session.add(order)
    await db_session.flush()

    assert order.sku_id == "test-sku-id"
    assert order.address_id == "test-address-id"
    assert order.shipment_id == "test-shipment-id"
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/models/test_point_order.py -v -k sku`

Expected: FAIL - columns don't exist yet

**Step 3: Write minimal implementation**

Update `backend/app/models/point_order.py` - add these fields:

```python
# Add after the delivery_info field:
sku_id = Column(String(36), ForeignKey("point_product_skus.id"),
               nullable=True, comment="SKU ID")
address_id = Column(String(36), ForeignKey("user_addresses.id"),
                   nullable=True, comment="收货地址ID")
shipment_id = Column(String(36), ForeignKey("order_shipments.id"),
                    nullable=True, comment="发货ID")
```

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/models/test_point_order.py -v -k sku`

Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/models/point_order.py backend/tests/models/test_point_order.py
git commit -m "feat(models): add sku_id, address_id, shipment_id to PointOrder"
```

---

## Task 5: Database Migration

**Files:**
- Create: `backend/alembic/versions/<timestamp>_add_point_shop_admin_tables.py`

**Step 1: Generate migration**

Run: `cd backend && alembic revision --autogenerate -m "add point shop admin tables"`

**Step 2: Review the generated migration file**

Check that it includes:
- `point_categories` table
- `point_specifications` table
- `point_specification_values` table
- `point_product_skus` table
- `point_returns` table
- Updates to `point_products` (category_id, has_sku)
- Updates to `point_orders` (sku_id, address_id, shipment_id)

**Step 3: Apply migration**

Run: `cd backend && alembic upgrade head`

Expected: Migration applies successfully

**Step 4: Verify tables exist**

Run: `cd backend && python3 -c "from app.models import PointCategory, PointProductSKU, PointReturn; print('Models imported successfully')"`

Expected: No import errors

**Step 5: Commit**

```bash
git add backend/alembic/versions/
git commit -m "feat(migration): add point shop admin tables migration"
```

---

## Task 6: PointCategoryService

**Files:**
- Create: `backend/app/services/point_category_service.py`
- Create: `backend/tests/services/test_point_category_service.py`

**Step 1: Write the failing test**

Create `backend/tests/services/test_point_category_service.py`:

```python
import pytest
from app.services.point_category_service import (
    create_category,
    get_category_tree,
    update_category,
    delete_category,
)
from app.core.exceptions import NotFoundException


@pytest.mark.asyncio
async def test_create_root_category(db_session: AsyncSession):
    """Test creating a root category"""
    category = await create_category(
        db_session,
        name="实物奖励",
        description="实物商品",
        level=1
    )

    assert category.id is not None
    assert category.name == "实物奖励"
    assert category.level == 1
    assert category.parent_id is None


@pytest.mark.asyncio
async def test_create_subcategory(db_session: AsyncSession):
    """Test creating a subcategory"""
    parent = await create_category(
        db_session,
        name="实物奖励",
        level=1
    )

    child = await create_category(
        db_session,
        name="数码产品",
        parent_id=parent.id,
        level=2
    )

    assert child.parent_id == parent.id
    assert child.level == 2


@pytest.mark.asyncio
async def test_get_category_tree(db_session: AsyncSession):
    """Test getting category tree"""
    parent = await create_category(db_session, name="实物", level=1)
    child1 = await create_category(db_session, name="数码", parent_id=parent.id, level=2)
    child2 = await create_category(db_session, name="日用", parent_id=parent.id, level=2)

    tree = await get_category_tree(db_session)

    assert len(tree) == 1
    assert tree[0]["name"] == "实物"
    assert len(tree[0]["children"]) == 2


@pytest.mark.asyncio
async def test_update_category(db_session: AsyncSession):
    """Test updating a category"""
    category = await create_category(db_session, name="旧名称", level=1)

    updated = await update_category(
        db_session,
        category.id,
        name="新名称",
        description="新描述"
    )

    assert updated.name == "新名称"
    assert updated.description == "新描述"


@pytest.mark.asyncio
async def test_delete_category(db_session: AsyncSession):
    """Test deleting a category"""
    category = await create_category(db_session, name="待删除", level=1)

    await delete_category(db_session, category.id)

    with pytest.raises(NotFoundException):
        await get_category_tree(db_session, category.id)
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/services/test_point_category_service.py -v`

Expected: `ImportError`

**Step 3: Write minimal implementation**

Create `backend/app/services/point_category_service.py`:

```python
"""积分商品分类服务"""
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.point_category import PointCategory
from app.core.exceptions import NotFoundException, BusinessException


async def create_category(
    db: AsyncSession,
    name: str,
    level: int,
    description: Optional[str] = None,
    parent_id: Optional[str] = None,
    icon_url: Optional[str] = None,
    banner_url: Optional[str] = None,
    sort_order: int = 0,
    is_active: bool = True,
) -> PointCategory:
    """创建分类"""
    category = PointCategory(
        name=name,
        description=description,
        parent_id=parent_id,
        icon_url=icon_url,
        banner_url=banner_url,
        level=level,
        sort_order=sort_order,
        is_active=is_active,
    )
    db.add(category)
    await db.flush()
    return category


async def get_category(db: AsyncSession, category_id: str) -> PointCategory:
    """获取单个分类"""
    result = await db.execute(
        select(PointCategory).where(PointCategory.id == category_id)
    )
    category = result.scalar_one_or_none()
    if not category:
        raise NotFoundException("分类不存在")
    return category


async def list_categories(
    db: AsyncSession,
    parent_id: Optional[str] = None,
    active_only: bool = False,
) -> List[PointCategory]:
    """获取分类列表"""
    query = select(PointCategory)
    if parent_id is not None:
        query = query.where(PointCategory.parent_id == parent_id)
    if active_only:
        query = query.where(PointCategory.is_active == True)
    query = query.order_by(PointCategory.sort_order.desc())

    result = await db.execute(query)
    return list(result.scalars().all())


async def get_category_tree(
    db: AsyncSession,
    category_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """获取分类树"""
    if category_id:
        category = await get_category(db, category_id)
        return [_category_to_dict(category, db)]

    # Get root categories
    roots = await list_categories(db, parent_id=None)
    return [_category_to_dict(cat, db) for cat in roots]


def _category_to_dict(
    category: PointCategory,
    db: AsyncSession
) -> Dict[str, Any]:
    """Convert category to dict with children"""
    from sqlalchemy import select

    return {
        "id": category.id,
        "name": category.name,
        "description": category.description,
        "parent_id": category.parent_id,
        "icon_url": category.icon_url,
        "banner_url": category.banner_url,
        "level": category.level,
        "sort_order": category.sort_order,
        "is_active": category.is_active,
        "children": [],
    }


async def update_category(
    db: AsyncSession,
    category_id: str,
    **kwargs
) -> PointCategory:
    """更新分类"""
    category = await get_category(db, category_id)

    for key, value in kwargs.items():
        if hasattr(category, key) and value is not None:
            setattr(category, key, value)

    await db.flush()
    return category


async def delete_category(db: AsyncSession, category_id: str) -> None:
    """删除分类"""
    category = await get_category(db, category_id)

    # Check if has children
    children = await list_categories(db, parent_id=category_id)
    if children:
        raise BusinessException("该分类下有子分类，无法删除")

    # TODO: Check if has products (implement after product service update)

    await db.delete(category)
```

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/services/test_point_category_service.py -v`

Expected: PASS (5 tests)

**Step 5: Commit**

```bash
git add backend/app/services/point_category_service.py backend/tests/services/test_point_category_service.py
git commit -m "feat(service): add PointCategoryService with CRUD and tree operations"
```

---

## Task 7: PointCategory API Routes

**Files:**
- Create: `backend/app/api/v1/point_categories.py`
- Modify: `backend/app/main.py` (register router)
- Create: `backend/tests/api/v1/test_point_categories_api.py`

**Step 1: Write the failing test**

Create `backend/tests/api/v1/test_point_categories_api.py`:

```python
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_category(async_client: AsyncClient, admin_token: str):
    """Test creating a category via API"""
    response = await async_client.post(
        "/api/v1/admin/point-categories",
        json={
            "name": "测试分类",
            "level": 1,
            "description": "测试描述"
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert "id" in data["data"]


@pytest.mark.asyncio
async def test_get_category_tree(async_client: AsyncClient, admin_token: str):
    """Test getting category tree via API"""
    # First create a category
    await async_client.post(
        "/api/v1/admin/point-categories",
        json={"name": "根分类", "level": 1},
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    response = await async_client.get(
        "/api/v1/admin/point-categories/tree",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert len(data["data"]) > 0
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/api/v1/test_point_categories_api.py -v`

Expected: 404 Not Found

**Step 3: Write minimal implementation**

Create `backend/app/api/v1/point_categories.py`:

```python
"""积分商品分类API"""
from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.deps import get_current_admin_user
from app.core.exceptions import success_response
from app.services.point_category_service import (
    create_category,
    get_category_tree,
    get_category,
    update_category,
    delete_category,
    list_categories,
)

router = APIRouter(prefix="/point-categories", tags=["point-categories"])


# Schemas
class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    level: int = Field(..., ge=1, le=3)
    description: Optional[str] = None
    parent_id: Optional[str] = None
    icon_url: Optional[str] = None
    banner_url: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = None
    icon_url: Optional[str] = None
    banner_url: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


# Routes
@router.post("/admin/point-categories")
async def admin_create_category(
    data: CategoryCreate,
    current_admin= Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """创建分类（管理员）"""
    category = await create_category(
        db,
        name=data.name,
        level=data.level,
        description=data.description,
        parent_id=data.parent_id,
        icon_url=data.icon_url,
        banner_url=data.banner_url,
        sort_order=data.sort_order,
        is_active=data.is_active,
    )
    return success_response(data={"id": category.id}, message="分类创建成功")


@router.get("/admin/point-categories/tree")
async def admin_get_category_tree(
    current_admin= Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取分类树（管理员）"""
    tree = await get_category_tree(db)
    return success_response(data=tree)


@router.get("/admin/point-categories/{category_id}")
async def admin_get_category(
    category_id: str,
    current_admin= Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取分类详情（管理员）"""
    category = await get_category(db, category_id)
    return success_response(data={
        "id": category.id,
        "name": category.name,
        "description": category.description,
        "parent_id": category.parent_id,
        "icon_url": category.icon_url,
        "banner_url": category.banner_url,
        "level": category.level,
        "sort_order": category.sort_order,
        "is_active": category.is_active,
    })


@router.put("/admin/point-categories/{category_id}")
async def admin_update_category(
    category_id: str,
    data: CategoryUpdate,
    current_admin= Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """更新分类（管理员）"""
    await update_category(db, category_id, **data.model_dump(exclude_unset=True))
    return success_response(message="分类更新成功")


@router.delete("/admin/point-categories/{category_id}")
async def admin_delete_category(
    category_id: str,
    current_admin= Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """删除分类（管理员）"""
    await delete_category(db, category_id)
    return success_response(message="分类已删除")
```

Update `backend/app/main.py`:

```python
from app.api.v1 import point_categories

# Add after other router includes:
app.include_router(point_categories.router)
```

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/api/v1/test_point_categories_api.py -v`

Expected: PASS (2 tests)

**Step 5: Commit**

```bash
git add backend/app/api/v1/point_categories.py backend/app/main.py backend/tests/api/v1/test_point_categories_api.py
git commit -m "feat(api): add point categories CRUD endpoints"
```

---

## Task 8: Courier Service

**Files:**
- Modify: `backend/app/services/courier_service.py` (may already exist from shipping.py model)
- Create: `backend/tests/services/test_courier_service.py`

**Step 1: Write the failing test**

Create `backend/tests/services/test_courier_service.py`:

```python
import pytest
from app.services.courier_service import create_courier, list_couriers, get_courier
from app.core.exceptions import NotFoundException


@pytest.mark.asyncio
async def test_create_courier(db_session: AsyncSession):
    """Test creating a courier company"""
    courier = await create_courier(
        db_session,
        name="顺丰速运",
        code="SF",
        website="https://www.sf-express.com",
        tracking_url="https://www.sf-express.com/zh-cn/track?query={number}"
    )

    assert courier.id is not None
    assert courier.name == "顺丰速运"
    assert courier.code == "SF"


@pytest.mark.asyncio
async def test_list_active_couriers(db_session: AsyncSession):
    """Test listing active couriers"""
    await create_courier(db_session, name="顺丰", code="SF", is_active=True)
    await create_courier(db_session, name="停用快递", code="OLD", is_active=False)

    couriers = await list_couriers(db_session, active_only=True)

    assert len(couriers) == 1
    assert couriers[0].code == "SF"


@pytest.mark.asyncio
async def test_get_courier(db_session: AsyncSession):
    """Test getting a courier by ID"""
    courier = await create_courier(db_session, name="中通", code="ZTO")

    found = await get_courier(db_session, courier.id)

    assert found.name == "中通"
    assert found.code == "ZTO"
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/services/test_courier_service.py -v`

Expected: `ImportError` or file not found

**Step 3: Write minimal implementation**

Create `backend/app/services/courier_service.py`:

```python
"""物流公司服务"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.shipping import CourierCompany
from app.core.exceptions import NotFoundException


async def create_courier(
    db: AsyncSession,
    name: str,
    code: str,
    website: Optional[str] = None,
    tracking_url: Optional[str] = None,
    supports_cod: bool = False,
    supports_cold_chain: bool = False,
    sort_order: int = 0,
    is_active: bool = True,
) -> CourierCompany:
    """创建物流公司"""
    courier = CourierCompany(
        name=name,
        code=code.upper(),
        website=website,
        tracking_url=tracking_url,
        supports_cod=supports_cod,
        supports_cold_chain=supports_cold_chain,
        sort_order=sort_order,
        is_active=is_active,
    )
    db.add(courier)
    await db.flush()
    return courier


async def list_couriers(
    db: AsyncSession,
    active_only: bool = False,
) -> List[CourierCompany]:
    """获取物流公司列表"""
    query = select(CourierCompany)
    if active_only:
        query = query.where(CourierCompany.is_active == True)
    query = query.order_by(CourierCompany.sort_order.desc())

    result = await db.execute(query)
    return list(result.scalars().all())


async def get_courier(db: AsyncSession, courier_id: str) -> CourierCompany:
    """获取单个物流公司"""
    result = await db.execute(
        select(CourierCompany).where(CourierCompany.id == courier_id)
    )
    courier = result.scalar_one_or_none()
    if not courier:
        raise NotFoundException("物流公司不存在")
    return courier


async def get_courier_by_code(db: AsyncSession, code: str) -> Optional[CourierCompany]:
    """根据代码获取物流公司"""
    result = await db.execute(
        select(CourierCompany).where(CourierCompany.code == code.upper())
    )
    return result.scalar_one_or_none()


async def update_courier(
    db: AsyncSession,
    courier_id: str,
    **kwargs
) -> CourierCompany:
    """更新物流公司"""
    courier = await get_courier(db, courier_id)

    for key, value in kwargs.items():
        if hasattr(courier, key) and value is not None:
            if key == "code":
                setattr(courier, key, value.upper())
            else:
                setattr(courier, key, value)

    await db.flush()
    return courier


async def delete_courier(db: AsyncSession, courier_id: str) -> None:
    """删除物流公司"""
    courier = await get_courier(db, courier_id)
    await db.delete(courier)
```

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/services/test_courier_service.py -v`

Expected: PASS (3 tests)

**Step 5: Commit**

```bash
git add backend/app/services/courier_service.py backend/tests/services/test_courier_service.py
git commit -m "feat(service): add CourierService with CRUD operations"
```

---

## Task 9: Courier API Routes

**Files:**
- Create: `backend/app/api/v1/couriers.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/api/v1/test_couriers_api.py`

**Step 1: Write the failing test**

Create `backend/tests/api/v1/test_couriers_api.py`:

```python
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_courier(async_client: AsyncClient, admin_token: str):
    """Test creating a courier via API"""
    response = await async_client.post(
        "/api/v1/admin/couriers",
        json={
            "name": "顺丰速运",
            "code": "SF",
            "tracking_url": "https://www.sf-express.com/track?query={number}"
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0


@pytest.mark.asyncio
async def test_list_couriers(async_client: AsyncClient, admin_token: str):
    """Test listing couriers via API"""
    response = await async_client.get(
        "/api/v1/admin/couriers",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert "couriers" in data["data"]
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/api/v1/test_couriers_api.py -v`

Expected: 404 Not Found

**Step 3: Write minimal implementation**

Create `backend/app/api/v1/couriers.py`:

```python
"""物流公司API"""
from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.deps import get_current_admin_user
from app.core.exceptions import success_response
from app.services.courier_service import (
    create_courier,
    list_couriers,
    get_courier,
    update_courier,
    delete_courier,
)

router = APIRouter(prefix="/couriers", tags=["couriers"])


# Schemas
class CourierCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=1, max_length=50)
    website: Optional[str] = None
    tracking_url: Optional[str] = None
    supports_cod: bool = False
    supports_cold_chain: bool = False
    sort_order: int = 0
    is_active: bool = True


class CourierUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    website: Optional[str] = None
    tracking_url: Optional[str] = None
    supports_cod: Optional[bool] = None
    supports_cold_chain: Optional[bool] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


# Routes
@router.post("/admin/couriers")
async def admin_create_courier(
    data: CourierCreate,
    current_admin= Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """创建物流公司（管理员）"""
    courier = await create_courier(
        db,
        name=data.name,
        code=data.code,
        website=data.website,
        tracking_url=data.tracking_url,
        supports_cod=data.supports_cod,
        supports_cold_chain=data.supports_cold_chain,
        sort_order=data.sort_order,
        is_active=data.is_active,
    )
    return success_response(data={"id": courier.id}, message="物流公司创建成功")


@router.get("/admin/couriers")
async def admin_list_couriers(
    active_only: bool = False,
    current_admin= Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取物流公司列表（管理员）"""
    couriers = await list_couriers(db, active_only=active_only)

    data = [{
        "id": c.id,
        "name": c.name,
        "code": c.code,
        "website": c.website,
        "tracking_url": c.tracking_url,
        "supports_cod": c.supports_cod,
        "supports_cold_chain": c.supports_cold_chain,
        "sort_order": c.sort_order,
        "is_active": c.is_active,
    } for c in couriers]

    return success_response(data={"couriers": data, "total": len(data)})


@router.get("/admin/couriers/active")
async def admin_list_active_couriers(
    current_admin= Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取启用的物流公司列表（用于下拉框）"""
    couriers = await list_couriers(db, active_only=True)

    data = [{
        "id": c.id,
        "name": c.name,
        "code": c.code,
    } for c in couriers]

    return success_response(data=data)


@router.get("/admin/couriers/{courier_id}")
async def admin_get_courier(
    courier_id: str,
    current_admin= Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取物流公司详情（管理员）"""
    courier = await get_courier(db, courier_id)
    return success_response(data={
        "id": courier.id,
        "name": courier.name,
        "code": courier.code,
        "website": courier.website,
        "tracking_url": courier.tracking_url,
        "supports_cod": courier.supports_cod,
        "supports_cold_chain": courier.supports_cold_chain,
        "sort_order": courier.sort_order,
        "is_active": courier.is_active,
    })


@router.put("/admin/couriers/{courier_id}")
async def admin_update_courier(
    courier_id: str,
    data: CourierUpdate,
    current_admin= Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """更新物流公司（管理员）"""
    await update_courier(db, courier_id, **data.model_dump(exclude_unset=True))
    return success_response(message="物流公司更新成功")


@router.delete("/admin/couriers/{courier_id}")
async def admin_delete_courier(
    courier_id: str,
    current_admin= Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """删除物流公司（管理员）"""
    await delete_courier(db, courier_id)
    return success_response(message="物流公司已删除")
```

Update `backend/app/main.py`:

```python
from app.api.v1 import couriers

app.include_router(couriers.router)
```

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/api/v1/test_couriers_api.py -v`

Expected: PASS (2 tests)

**Step 5: Commit**

```bash
git add backend/app/api/v1/couriers.py backend/app/main.py backend/tests/api/v1/test_couriers_api.py
git commit -m "feat(api): add courier management endpoints"
```

---

## Task 10-20: [Continued in Next Tasks]

Due to length, the remaining tasks follow the same pattern:

**Task 10:** UserAddressService - Admin address viewing/editing
**Task 11:** UserAddress API routes
**Task 12:** PointSKUService - SKU/specification management
**Task 13:** PointSKU API routes
**Task 14:** ShippingTemplateService
**Task 15:** ShippingTemplate API routes
**Task 16:** PointShipmentService
**Task 17:** PointShipment API routes
**Task 18:** PointReturnService
**Task 19:** PointReturn API routes
**Task 20:** Frontend - PointCategories.vue
**Task 21:** Frontend - Couriers.vue
**Task 22:** Frontend - UserAddresses.vue
**Task 23:** Frontend - PointShop.vue enhancement (SKU)
**Task 24:** Frontend - ShippingTemplates.vue
**Task 25:** Frontend - PointShipments.vue
**Task 26:** Frontend - PointReturns.vue
**Task 27:** Frontend - Shared components
**Task 28:** Integration testing
**Task 29:** Documentation
**Task 30:** Final review and cleanup

---

## Testing Strategy

### Backend Tests
- Unit tests for each service (`pytest tests/services/`)
- API integration tests (`pytest tests/api/v1/`)
- Model tests (`pytest tests/models/`)

### Frontend Tests
- Component tests with Vitest
- API client mock tests

### E2E Tests
- Manual testing of admin workflows
- Create category → Create product with SKU → Create order → Ship → Return

---

## Notes for Implementation

1. **Use existing patterns** - Reference `point_product_service.py`, `point_shop.py` API
2. **Exception handling** - Use `app/core/exceptions.py` for consistent errors
3. **Audit logging** - Consider adding audit logs for admin actions
4. **Image upload** - Reuse existing `/admin/upload` endpoint
5. **Frontend components** - Check existing components in `admin-web/src/components/`
6. **API client** - Follow pattern of `admin-web/src/api/pointShop.ts`

---

## Related Documentation

- Design doc: `docs/plans/2025-02-24-point-shop-admin-module-design.md`
- Technical spec: `docs/技术方案_v1.0.md`
- Sprint planning: `docs/迭代规划_Sprint与任务.md`
