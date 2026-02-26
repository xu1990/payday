# Shipping Template Enhancement Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Enhance shipping template with excluded regions, multiple free shipping types, volume-based charging, and simplified fixed fee mode.

**Architecture:** Gradual enhancement of existing models with new fields. Backend changes include database migration, schema updates, service logic. Frontend adds new tabs for excluded regions and free shipping rules.

**Tech Stack:** FastAPI + SQLAlchemy (backend), Vue 3 + Element Plus (admin-web), Alembic (migrations)

---

## Task 1: Database Migration - Add New Fields

**Files:**
- Create: `backend/alembic/versions/xxx_add_shipping_template_enhancements.py`

**Step 1: Create migration file**

Run: `cd backend && alembic revision -m "add_shipping_template_enhancements"`

**Step 2: Edit migration file with schema changes**

```python
"""add shipping template enhancements

Revision ID: xxx
Revises: previous_revision
Create Date: 2026-02-26
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers
revision = 'xxx'
down_revision = 'previous_revision'
branch_labels = None
depends_on = None


def upgrade():
    # ShippingTemplate new fields
    op.add_column('shipping_templates',
        sa.Column('free_shipping_type', sa.String(20), nullable=False, server_default='none',
                  comment='包邮类型: none/amount/quantity/seller'))
    op.add_column('shipping_templates',
        sa.Column('free_quantity', sa.Integer(), nullable=True,
                  comment='满件数包邮阈值'))
    op.add_column('shipping_templates',
        sa.Column('excluded_regions', sa.JSON(), nullable=True,
                  comment='不配送区域JSON'))
    op.add_column('shipping_templates',
        sa.Column('volume_unit', sa.Integer(), nullable=True,
                  comment='体积单位(cm³)'))

    # ShippingTemplateRegion new fields
    op.add_column('shipping_template_regions',
        sa.Column('free_quantity', sa.Integer(), nullable=True,
                  comment='区域满件数包邮阈值'))
    op.add_column('shipping_template_regions',
        sa.Column('is_excluded', sa.Boolean(), nullable=False, server_default='0',
                  comment='是否不配送区域'))


def downgrade():
    op.drop_column('shipping_templates', 'free_shipping_type')
    op.drop_column('shipping_templates', 'free_quantity')
    op.drop_column('shipping_templates', 'excluded_regions')
    op.drop_column('shipping_templates', 'volume_unit')
    op.drop_column('shipping_template_regions', 'free_quantity')
    op.drop_column('shipping_template_regions', 'is_excluded')
```

**Step 3: Run migration**

Run: `cd backend && alembic upgrade head`
Expected: Migration applies successfully

**Step 4: Commit**

```bash
git add backend/alembic/versions/*add_shipping_template_enhancements*.py
git commit -m "feat(shipping): add database migration for template enhancements"
```

---

## Task 2: Update Shipping Model

**Files:**
- Modify: `backend/app/models/shipping.py:14-75`

**Step 1: Update ShippingTemplate model**

Add new fields to `ShippingTemplate` class after `charge_type`:

```python
    # Free shipping configuration
    free_shipping_type = Column(
        String(20),
        nullable=False,
        default="none",
        comment="包邮类型: none/amount/quantity/seller"
    )
    free_quantity = Column(Integer, nullable=True, comment="满件数包邮阈值")

    # Excluded regions (non-deliverable areas)
    excluded_regions = Column(JSON, nullable=True, comment="不配送区域JSON")

    # Volume unit for volume-based charging
    volume_unit = Column(Integer, nullable=True, comment="体积单位(cm³)")
```

**Step 2: Update ShippingTemplateRegion model**

Add new fields to `ShippingTemplateRegion` class after `free_threshold`:

```python
    # Regional free quantity threshold
    free_quantity = Column(Integer, nullable=True, comment="区域满件数包邮阈值")

    # Excluded region flag
    is_excluded = Column(Boolean, default=False, nullable=False, comment="是否不配送区域")
```

**Step 3: Commit**

```bash
git add backend/app/models/shipping.py
git commit -m "feat(shipping): add new fields to shipping models"
```

---

## Task 3: Update Pydantic Schemas

**Files:**
- Modify: `backend/app/schemas/shipping.py:168-291`

**Step 1: Add FreeShippingType literal and update ShippingTemplateCreate**

Replace `ShippingTemplateCreate` class:

```python
FreeShippingType = Literal["none", "amount", "quantity", "seller"]
ChargeType = Literal["weight", "quantity", "fixed", "volume"]


class ShippingTemplateCreate(BaseModel):
    """创建运费模板请求"""
    name: str = Field(..., min_length=1, max_length=100, description="模板名称")
    description: Optional[str] = Field(None, max_length=200, description="模板描述")
    charge_type: ChargeType = Field(..., description="计费方式")

    # Pricing fields (optional for fixed type)
    default_first_unit: Optional[int] = Field(None, gt=0, description="首件/首重")
    default_first_cost: Optional[int] = Field(None, ge=0, description="首件运费(分)")
    default_continue_unit: Optional[int] = Field(None, gt=0, description="续件/续重")
    default_continue_cost: Optional[int] = Field(None, ge=0, description="续件运费(分)")

    # Free shipping configuration
    free_shipping_type: FreeShippingType = Field("none", description="包邮类型")
    free_threshold: Optional[int] = Field(None, ge=0, description="满金额包邮门槛(分)")
    free_quantity: Optional[int] = Field(None, ge=1, description="满件数包邮阈值")

    # Excluded regions
    excluded_regions: Optional[List[Dict[str, str]]] = Field(
        None,
        description="不配送区域 [{code, name}]"
    )

    # Volume unit
    volume_unit: Optional[int] = Field(None, gt=0, description="体积单位(cm³)")

    # Estimated delivery
    estimate_days_min: Optional[int] = Field(None, gt=0, description="预计到达最少天数")
    estimate_days_max: Optional[int] = Field(None, gt=0, description="预计到达最多天数")

    @field_validator("default_first_unit", "default_first_cost",
                     "default_continue_unit", "default_continue_cost")
    @classmethod
    def validate_pricing_fields(cls, v, info):
        """Validate pricing fields are required for non-fixed charge types"""
        if info.data.get("charge_type") != "fixed" and v is None:
            field_name = info.field_name
            raise ValueError(f"{field_name} is required for non-fixed charge types")
        return v

    @field_validator("estimate_days_max")
    @classmethod
    def validate_estimate_days(cls, v, info):
        """验证最大天数不能小于最小天数"""
        if v is not None and info.data.get("estimate_days_min") is not None:
            if v < info.data["estimate_days_min"]:
                raise ValueError("最大天数不能小于最小天数")
        return v
```

**Step 2: Update ShippingTemplateUpdate**

Add new optional fields to `ShippingTemplateUpdate`:

```python
class ShippingTemplateUpdate(BaseModel):
    """更新运费模板请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="模板名称")
    description: Optional[str] = Field(None, max_length=200, description="模板描述")
    charge_type: Optional[ChargeType] = Field(None, description="计费方式")
    default_first_unit: Optional[int] = Field(None, gt=0, description="首件/首重")
    default_first_cost: Optional[int] = Field(None, ge=0, description="首件运费(分)")
    default_continue_unit: Optional[int] = Field(None, gt=0, description="续件/续重")
    default_continue_cost: Optional[int] = Field(None, ge=0, description="续件运费(分)")
    free_shipping_type: Optional[FreeShippingType] = Field(None, description="包邮类型")
    free_threshold: Optional[int] = Field(None, ge=0, description="满金额包邮门槛(分)")
    free_quantity: Optional[int] = Field(None, ge=1, description="满件数包邮阈值")
    excluded_regions: Optional[List[Dict[str, str]]] = Field(None, description="不配送区域")
    volume_unit: Optional[int] = Field(None, gt=0, description="体积单位(cm³)")
    estimate_days_min: Optional[int] = Field(None, gt=0, description="预计到达最少天数")
    estimate_days_max: Optional[int] = Field(None, gt=0, description="预计到达最多天数")
    is_active: Optional[bool] = Field(None, description="是否启用")

    @field_validator("estimate_days_max")
    @classmethod
    def validate_estimate_days(cls, v, info):
        if v is not None and info.data.get("estimate_days_min") is not None:
            if v < info.data["estimate_days_min"]:
                raise ValueError("最大天数不能小于最小天数")
        return v
```

**Step 3: Update ShippingTemplateResponse**

Add new fields to `ShippingTemplateResponse`:

```python
class ShippingTemplateResponse(BaseModel):
    """运费模板响应"""
    id: str
    name: str
    description: Optional[str] = None
    charge_type: str
    default_first_unit: Optional[int] = None
    default_first_cost: Optional[int] = None
    default_continue_unit: Optional[int] = None
    default_continue_cost: Optional[int] = None
    free_shipping_type: str = "none"
    free_threshold: Optional[int] = None
    free_quantity: Optional[int] = None
    excluded_regions: Optional[List[Dict[str, str]]] = None
    volume_unit: Optional[int] = None
    estimate_days_min: Optional[int] = None
    estimate_days_max: Optional[int] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

**Step 4: Update ShippingTemplateRegionCreate/Update/Response**

Add new fields to region schemas:

```python
class ShippingTemplateRegionCreate(BaseModel):
    """创建运费模板区域请求"""
    region_codes: str = Field(..., min_length=1, description="区域代码列表(逗号分隔)")
    region_names: str = Field(..., min_length=1, description="区域名称列表(逗号分隔)")
    first_unit: int = Field(..., gt=0, description="首件/首重")
    first_cost: int = Field(..., ge=0, description="首件运费(分)")
    continue_unit: int = Field(..., gt=0, description="续件/续重")
    continue_cost: int = Field(..., ge=0, description="续件运费(分)")
    free_threshold: Optional[int] = Field(None, ge=0, description="包邮门槛(分)")
    free_quantity: Optional[int] = Field(None, ge=1, description="满件数包邮阈值")
    is_excluded: bool = Field(False, description="是否不配送区域")

    @field_validator("region_codes", "region_names")
    @classmethod
    def validate_region_format(cls, v):
        if not v.strip():
            raise ValueError("区域代码和名称不能为空")
        return v.strip()


class ShippingTemplateRegionUpdate(BaseModel):
    """更新运费模板区域请求"""
    region_codes: Optional[str] = Field(None, min_length=1, description="区域代码列表(逗号分隔)")
    region_names: Optional[str] = Field(None, min_length=1, description="区域名称列表(逗号分隔)")
    first_unit: Optional[int] = Field(None, gt=0, description="首件/首重")
    first_cost: Optional[int] = Field(None, ge=0, description="首件运费(分)")
    continue_unit: Optional[int] = Field(None, gt=0, description="续件/续重")
    continue_cost: Optional[int] = Field(None, ge=0, description="续件运费(分)")
    free_threshold: Optional[int] = Field(None, ge=0, description="包邮门槛(分)")
    free_quantity: Optional[int] = Field(None, ge=1, description="满件数包邮阈值")
    is_excluded: Optional[bool] = Field(None, description="是否不配送区域")
    is_active: Optional[bool] = Field(None, description="是否启用")

    @field_validator("region_codes", "region_names")
    @classmethod
    def validate_region_format(cls, v):
        if v is not None and not v.strip():
            raise ValueError("区域代码和名称不能为空")
        return v.strip() if v is not None else v


class ShippingTemplateRegionResponse(BaseModel):
    """运费模板区域响应"""
    id: str
    template_id: str
    region_codes: str
    region_names: str
    first_unit: int
    first_cost: int
    continue_unit: int
    continue_cost: int
    free_threshold: Optional[int] = None
    free_quantity: Optional[int] = None
    is_excluded: bool = False
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

**Step 5: Commit**

```bash
git add backend/app/schemas/shipping.py
git commit -m "feat(shipping): update Pydantic schemas for template enhancements"
```

---

## Task 4: Update ShippingTemplateService

**Files:**
- Modify: `backend/app/services/shipping_service.py:800-1092`

**Step 1: Update create_template method**

Update the `create_template` method to handle new fields:

```python
async def create_template(self, template_data: ShippingTemplateCreate) -> ShippingTemplate:
    """创建运费模板"""
    # Validate charge_type
    valid_charge_types = ["weight", "quantity", "fixed", "volume"]
    if template_data.charge_type not in valid_charge_types:
        raise ValidationException(
            f"计费方式必须是: {', '.join(valid_charge_types)}",
            code="INVALID_CHARGE_TYPE"
        )

    # Validate free_shipping_type
    valid_free_types = ["none", "amount", "quantity", "seller"]
    if template_data.free_shipping_type not in valid_free_types:
        raise ValidationException(
            f"包邮类型必须是: {', '.join(valid_free_types)}",
            code="INVALID_FREE_SHIPPING_TYPE"
        )

    template = ShippingTemplate(
        name=template_data.name,
        description=template_data.description,
        charge_type=template_data.charge_type,
        default_first_unit=template_data.default_first_unit,
        default_first_cost=template_data.default_first_cost,
        default_continue_unit=template_data.default_continue_unit,
        default_continue_cost=template_data.default_continue_cost,
        free_shipping_type=template_data.free_shipping_type,
        free_threshold=template_data.free_threshold,
        free_quantity=template_data.free_quantity,
        excluded_regions=template_data.excluded_regions,
        volume_unit=template_data.volume_unit,
        estimate_days_min=template_data.estimate_days_min,
        estimate_days_max=template_data.estimate_days_max,
        is_active=True
    )

    self.db.add(template)
    try:
        await self.db.commit()
        await self.db.refresh(template)
        return template
    except SQLAlchemyError:
        await self.db.rollback()
        raise
```

**Step 2: Update update_template method**

Update to handle new fields in update:

```python
async def update_template(self, template_id: str, update_data: ShippingTemplateUpdate) -> ShippingTemplate:
    """更新运费模板"""
    template = await self.get_template(template_id)

    # Validate charge_type if provided
    if update_data.charge_type:
        valid_charge_types = ["weight", "quantity", "fixed", "volume"]
        if update_data.charge_type not in valid_charge_types:
            raise ValidationException(
                f"计费方式必须是: {', '.join(valid_charge_types)}",
                code="INVALID_CHARGE_TYPE"
            )

    # Validate free_shipping_type if provided
    if update_data.free_shipping_type:
        valid_free_types = ["none", "amount", "quantity", "seller"]
        if update_data.free_shipping_type not in valid_free_types:
            raise ValidationException(
                f"包邮类型必须是: {', '.join(valid_free_types)}",
                code="INVALID_FREE_SHIPPING_TYPE"
            )

    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for k, v in update_dict.items():
        setattr(template, k, v)

    await self.db.commit()
    await self.db.refresh(template)
    return template
```

**Step 3: Update create_region method**

Add handling for new region fields:

```python
async def create_region(self, template_id: str, region_data: ShippingTemplateRegionCreate) -> ShippingTemplateRegion:
    """创建运费模板区域配置"""
    # Validate template exists
    template = await self.get_template(template_id)

    # Validate region format
    if not region_data.region_codes.strip():
        raise ValidationException("区域代码不能为空")
    if not region_data.region_names.strip():
        raise ValidationException("区域名称不能为空")

    region = ShippingTemplateRegion(
        template_id=template_id,
        region_codes=region_data.region_codes.strip(),
        region_names=region_data.region_names.strip(),
        first_unit=region_data.first_unit,
        first_cost=region_data.first_cost,
        continue_unit=region_data.continue_unit,
        continue_cost=region_data.continue_cost,
        free_threshold=region_data.free_threshold,
        free_quantity=region_data.free_quantity,
        is_excluded=region_data.is_excluded,
        is_active=True
    )

    self.db.add(region)
    try:
        await self.db.commit()
        await self.db.refresh(region)
        return region
    except SQLAlchemyError:
        await self.db.rollback()
        raise
```

**Step 4: Update calculate_shipping_cost method**

Replace the entire `calculate_shipping_cost` method:

```python
async def calculate_shipping_cost(
    self,
    template_id: str,
    region_code: Optional[str] = None,
    weight: Optional[int] = None,
    quantity: Optional[int] = None,
    volume: Optional[int] = None,
    total_amount: Optional[int] = None
) -> dict:
    """计算运费"""
    template = await self.get_template(template_id)

    # 1. Check if region is in excluded regions
    excluded_regions = template.excluded_regions or []
    excluded_codes = [r.get('code') for r in excluded_regions if isinstance(r, dict)]
    if region_code and region_code in excluded_codes:
        return {
            "deliverable": False,
            "reason": "该地区不支持配送",
            "shipping_cost": 0,
            "free_shipping": False
        }

    # 2. Find matching region configuration
    region = None
    if region_code:
        result = await self.db.execute(
            select(ShippingTemplateRegion)
            .where(
                ShippingTemplateRegion.template_id == template_id,
                ShippingTemplateRegion.is_active == True
            )
            .where(ShippingTemplateRegion.region_codes.like(f"%{region_code}%"))
        )
        region = result.scalar_one_or_none()

    # 3. Check if region is marked as excluded
    if region and region.is_excluded:
        return {
            "deliverable": False,
            "reason": "该地区不支持配送",
            "shipping_cost": 0,
            "free_shipping": False
        }

    # 4. Check seller-borne shipping
    if template.free_shipping_type == "seller":
        return {
            "deliverable": True,
            "shipping_cost": 0,
            "free_shipping": True,
            "region_name": region.region_names if region else "默认区域",
            "region_code": region_code
        }

    # 5. Check free shipping by quantity
    free_qty = region.free_quantity if region else template.free_quantity
    if template.free_shipping_type == "quantity" and quantity and free_qty:
        if quantity >= free_qty:
            return {
                "deliverable": True,
                "shipping_cost": 0,
                "free_shipping": True,
                "region_name": region.region_names if region else "默认区域",
                "region_code": region_code
            }

    # 6. Check free shipping by amount
    free_amt = region.free_threshold if region else template.free_threshold
    if template.free_shipping_type == "amount" and total_amount and free_amt:
        if total_amount >= free_amt:
            return {
                "deliverable": True,
                "shipping_cost": 0,
                "free_shipping": True,
                "region_name": region.region_names if region else "默认区域",
                "region_code": region_code
            }

    # 7. Get pricing parameters
    if not region:
        first_unit = template.default_first_unit
        first_cost = template.default_first_cost
        continue_unit = template.default_continue_unit
        continue_cost = template.default_continue_cost
    else:
        first_unit = region.first_unit
        first_cost = region.first_cost
        continue_unit = region.continue_unit
        continue_cost = region.continue_cost

    # 8. Fixed shipping cost
    if template.charge_type == "fixed":
        return {
            "deliverable": True,
            "shipping_cost": first_cost or 0,
            "free_shipping": False,
            "region_name": region.region_names if region else "默认区域",
            "region_code": region_code,
            "charge_type": template.charge_type
        }

    # 9. Calculate shipping based on charge type
    shipping_cost = 0
    measure_value = None

    if template.charge_type == "weight":
        measure_value = weight
    elif template.charge_type == "quantity":
        measure_value = quantity
    elif template.charge_type == "volume":
        measure_value = volume

    if measure_value and first_unit and continue_unit:
        if measure_value <= first_unit:
            shipping_cost = first_cost or 0
        else:
            extra_units = (measure_value - first_unit) // continue_unit
            if (measure_value - first_unit) % continue_unit > 0:
                extra_units += 1
            shipping_cost = (first_cost or 0) + extra_units * (continue_cost or 0)

    return {
        "deliverable": True,
        "shipping_cost": shipping_cost,
        "free_shipping": False,
        "region_name": region.region_names if region else "默认区域",
        "region_code": region_code,
        "charge_type": template.charge_type,
        "first_unit": first_unit,
        "first_cost": first_cost,
        "continue_unit": continue_unit,
        "continue_cost": continue_cost
    }
```

**Step 5: Commit**

```bash
git add backend/app/services/shipping_service.py
git commit -m "feat(shipping): update ShippingTemplateService with new features"
```

---

## Task 5: Update Frontend Types

**Files:**
- Modify: `admin-web/src/api/shippingTemplate.ts:1-100`

**Step 1: Update TypeScript types**

Replace the types in `shippingTemplate.ts`:

```typescript
// ==================== Types ====================

export type ChargeType = 'weight' | 'quantity' | 'fixed' | 'volume'
export type FreeShippingType = 'none' | 'amount' | 'quantity' | 'seller'

export interface ExcludedRegion {
  code: string
  name: string
}

export interface ShippingTemplate {
  id: string
  name: string
  description: string | null
  charge_type: ChargeType
  default_first_unit: number | null
  default_first_cost: number | null
  default_continue_unit: number | null
  default_continue_cost: number | null
  free_shipping_type: FreeShippingType
  free_threshold: number | null
  free_quantity: number | null
  excluded_regions: ExcludedRegion[] | null
  volume_unit: number | null
  estimate_days_min: number | null
  estimate_days_max: number | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface ShippingTemplateRegion {
  id: string
  template_id: string
  region_codes: string
  region_names: string
  first_unit: number
  first_cost: number
  continue_unit: number
  continue_cost: number
  free_threshold: number | null
  free_quantity: number | null
  is_excluded: boolean
  is_active: boolean
  created_at: string
}

export interface ShippingTemplateCreate {
  name: string
  description?: string | null
  charge_type: ChargeType
  default_first_unit?: number | null
  default_first_cost?: number | null
  default_continue_unit?: number | null
  default_continue_cost?: number | null
  free_shipping_type?: FreeShippingType
  free_threshold?: number | null
  free_quantity?: number | null
  excluded_regions?: ExcludedRegion[] | null
  volume_unit?: number | null
  estimate_days_min?: number | null
  estimate_days_max?: number | null
}

export interface ShippingTemplateUpdate {
  name?: string
  description?: string | null
  charge_type?: ChargeType
  default_first_unit?: number | null
  default_first_cost?: number | null
  default_continue_unit?: number | null
  default_continue_cost?: number | null
  free_shipping_type?: FreeShippingType
  free_threshold?: number | null
  free_quantity?: number | null
  excluded_regions?: ExcludedRegion[] | null
  volume_unit?: number | null
  estimate_days_min?: number | null
  estimate_days_max?: number | null
  is_active?: boolean
}

export interface ShippingTemplateRegionCreate {
  region_codes: string
  region_names: string
  first_unit: number
  first_cost: number
  continue_unit: number
  continue_cost: number
  free_threshold?: number | null
  free_quantity?: number | null
  is_excluded?: boolean
}

export interface ShippingTemplateRegionUpdate {
  region_codes?: string
  region_names?: string
  first_unit?: number
  first_cost?: number
  continue_unit?: number
  continue_cost?: number
  free_threshold?: number | null
  free_quantity?: number | null
  is_excluded?: boolean
  is_active?: boolean
}
```

**Step 2: Update helper functions**

Update the helper functions:

```typescript
// ==================== Helpers ====================

/** Convert cents to yuan (for display) */
export function centsToYuan(cents: number): number {
  return cents / 100
}

/** Convert yuan to cents (for API) */
export function yuanToCents(yuan: number): number {
  return Math.round(yuan * 100)
}

/** Format charge type for display */
export function formatChargeType(type: ChargeType): string {
  const types: Record<ChargeType, string> = {
    weight: '按重量',
    quantity: '按件数',
    fixed: '固定运费',
    volume: '按体积',
  }
  return types[type] || type
}

/** Get unit label based on charge type */
export function getUnitLabel(chargeType: ChargeType): string {
  const labels: Record<ChargeType, string> = {
    weight: 'g',
    quantity: '件',
    fixed: '',
    volume: 'cm³',
  }
  return labels[chargeType] || ''
}

/** Format free shipping type for display */
export function formatFreeShippingType(type: FreeShippingType): string {
  const types: Record<FreeShippingType, string> = {
    none: '不包邮',
    amount: '满金额包邮',
    quantity: '满件数包邮',
    seller: '卖家承担运费',
  }
  return types[type] || type
}
```

**Step 3: Commit**

```bash
git add admin-web/src/api/shippingTemplate.ts
git commit -m "feat(admin-web): update shipping template types"
```

---

## Task 6: Update Frontend Component - Basic Info Tab

**Files:**
- Modify: `admin-web/src/views/ShippingTemplates.vue:47-145`

**Step 1: Update form ref type**

Update the form ref to include new fields:

```typescript
// Basic form
const form = ref<ShippingTemplateCreate>({
  name: '',
  description: '',
  charge_type: 'weight',
  default_first_unit: 500,
  default_first_cost: 500,
  default_continue_unit: 1000,
  default_continue_cost: 10,
  free_shipping_type: 'none',
  free_threshold: null,
  free_quantity: null,
  excluded_regions: null,
  volume_unit: null,
  estimate_days_min: null,
  estimate_days_max: null,
})
```

**Step 2: Add excluded regions ref**

```typescript
// Excluded regions management
const excludedProvinces = ref<string[]>([])

// Free shipping form
const freeShippingType = ref<FreeShippingType>('none')
```

**Step 3: Update computed for charge type**

```typescript
// Computed to check if pricing fields should be shown
const showPricingFields = computed(() => form.value.charge_type !== 'fixed')

const chargeTypeUnit = computed(() => getUnitLabel(form.value.charge_type))
const chargeTypeLabel = computed(() => formatChargeType(form.value.charge_type))
```

**Step 4: Update openCreate function**

```typescript
function openCreate() {
  dialogMode.value = 'create'
  editId.value = null
  activeTab.value = 'basic'
  form.value = {
    name: '',
    description: '',
    charge_type: 'weight',
    default_first_unit: 500,
    default_first_cost: 500,
    default_continue_unit: 1000,
    default_continue_cost: 10,
    free_shipping_type: 'none',
    free_threshold: null,
    free_quantity: null,
    excluded_regions: null,
    volume_unit: null,
    estimate_days_min: null,
    estimate_days_max: null,
  }
  freeShippingType.value = 'none'
  excludedProvinces.value = []
  regions.value = []
  showDialog.value = true
}
```

**Step 5: Update openEdit function**

```typescript
async function openEdit(item: ShippingTemplate) {
  dialogMode.value = 'edit'
  editId.value = item.id
  activeTab.value = 'basic'

  try {
    const res = await getShippingTemplate(item.id)
    const template = res.data

    form.value = {
      name: template.name,
      description: template.description || '',
      charge_type: template.charge_type,
      default_first_unit: template.default_first_unit,
      default_first_cost: template.default_first_cost,
      default_continue_unit: template.default_continue_unit,
      default_continue_cost: template.default_continue_cost,
      free_shipping_type: template.free_shipping_type || 'none',
      free_threshold: template.free_threshold,
      free_quantity: template.free_quantity,
      excluded_regions: template.excluded_regions,
      volume_unit: template.volume_unit,
      estimate_days_min: template.estimate_days_min,
      estimate_days_max: template.estimate_days_max,
    }

    freeShippingType.value = template.free_shipping_type || 'none'

    // Load excluded provinces
    if (template.excluded_regions) {
      excludedProvinces.value = template.excluded_regions.map(r => r.code)
    } else {
      excludedProvinces.value = []
    }

    // Load regions
    await loadRegions(item.id)
    showDialog.value = true
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : '加载模板失败'
    ElMessage.error(errorMessage)
  }
}
```

**Step 6: Commit**

```bash
git add admin-web/src/views/ShippingTemplates.vue
git commit -m "feat(admin-web): update shipping template form logic"
```

---

## Task 7: Update Frontend Component - Template UI

**Files:**
- Modify: `admin-web/src/views/ShippingTemplates.vue:396-620`

**Step 1: Update template dialog tabs**

Replace the dialog content section (from `el-tabs` to `el-tab-pane` for basic info):

```vue
<!-- Create/Edit Dialog -->
<el-dialog
  v-model="showDialog"
  :title="dialogMode === 'create' ? '新建运费模板' : '编辑运费模板'"
  width="900px"
  @close="activeTab = 'basic'"
>
  <el-tabs v-model="activeTab">
    <!-- Basic Info Tab -->
    <el-tab-pane label="基本信息" name="basic">
      <el-form :model="form" label-width="120px">
        <el-form-item label="模板名称" required>
          <el-input v-model="form.name" placeholder="请输入模板名称" />
        </el-form-item>
        <el-form-item label="模板描述">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="2"
            placeholder="请输入模板描述"
          />
        </el-form-item>
        <el-form-item label="计费方式" required>
          <el-select v-model="form.charge_type" placeholder="请选择计费方式">
            <el-option label="按重量" value="weight" />
            <el-option label="按件数" value="quantity" />
            <el-option label="固定运费" value="fixed" />
            <el-option label="按体积" value="volume" />
          </el-select>
        </el-form-item>

        <!-- Pricing fields - hidden for fixed type -->
        <template v-if="showPricingFields">
          <el-form-item label="默认首件/首重" required>
            <el-input-number v-model="form.default_first_unit" :min="1" :max="999999" />
            <span style="margin-left: 10px">{{ chargeTypeUnit }}</span>
          </el-form-item>
          <el-form-item label="默认首件运费" required>
            <el-input-number v-model="form.default_first_cost" :min="0" :max="999999" />
            <span style="margin-left: 10px">分 ({{ formatCost(form.default_first_cost || 0) }})</span>
          </el-form-item>
          <el-form-item label="默认续件/续重" required>
            <el-input-number v-model="form.default_continue_unit" :min="1" :max="999999" />
            <span style="margin-left: 10px">{{ chargeTypeUnit }}</span>
          </el-form-item>
          <el-form-item label="默认续件运费" required>
            <el-input-number v-model="form.default_continue_cost" :min="0" :max="999999" />
            <span style="margin-left: 10px">分 ({{ formatCost(form.default_continue_cost || 0) }})</span>
          </el-form-item>
        </template>

        <!-- Fixed shipping cost - shown only for fixed type -->
        <el-form-item v-if="!showPricingFields" label="固定运费" required>
          <el-input-number v-model="form.default_first_cost" :min="0" :max="999999" />
          <span style="margin-left: 10px">分 ({{ formatCost(form.default_first_cost || 0) }})</span>
        </el-form-item>

        <el-form-item label="预计送达天数">
          <el-input-number
            v-model="form.estimate_days_min"
            :min="1"
            :max="99"
            placeholder="最少"
            style="width: 120px"
          />
          <span style="margin: 0 10px">-</span>
          <el-input-number
            v-model="form.estimate_days_max"
            :min="1"
            :max="99"
            placeholder="最多"
            style="width: 120px"
          />
          <span style="margin-left: 10px">天</span>
        </el-form-item>
      </el-form>
    </el-tab-pane>

    <!-- Excluded Regions Tab -->
    <el-tab-pane label="不配送区域" name="excluded" :disabled="dialogMode === 'create'">
      <div style="margin-bottom: 15px">
        <el-select
          v-model="excludedProvinces"
          multiple
          placeholder="选择不配送的省份"
          style="width: 100%"
          @change="handleExcludedProvinceChange"
        >
          <el-option
            v-for="province in PROVINCES"
            :key="province.code"
            :label="province.name"
            :value="province.code"
          />
        </el-select>
      </div>
      <div v-if="excludedProvinces.length > 0">
        <el-tag
          v-for="code in excludedProvinces"
          :key="code"
          closable
          style="margin: 5px"
          @close="removeExcludedProvince(code)"
        >
          {{ getProvinceName(code) }}
        </el-tag>
      </div>
      <el-empty v-else description="暂无不配送区域" :image-size="80" />
    </el-tab-pane>

    <!-- Free Shipping Rules Tab -->
    <el-tab-pane label="包邮规则" name="free-shipping" :disabled="dialogMode === 'create'">
      <el-form label-width="100px">
        <el-form-item label="包邮类型">
          <el-radio-group v-model="freeShippingType" @change="handleFreeShippingTypeChange">
            <el-radio value="none">不包邮</el-radio>
            <el-radio value="amount">满金额包邮</el-radio>
            <el-radio value="quantity">满件数包邮</el-radio>
            <el-radio value="seller">卖家承担运费</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item v-if="freeShippingType === 'amount'" label="满金额">
          <el-input-number v-model="form.free_threshold" :min="0" :max="99999999" />
          <span style="margin-left: 10px">分 ({{ form.free_threshold ? formatCost(form.free_threshold) : '¥0.00' }})</span>
        </el-form-item>

        <el-form-item v-if="freeShippingType === 'quantity'" label="满件数">
          <el-input-number v-model="form.free_quantity" :min="1" :max="9999" />
          <span style="margin-left: 10px">件</span>
        </el-form-item>
      </el-form>
    </el-tab-pane>

    <!-- Region Pricing Tab (existing, keep as is) -->
    <el-tab-pane label="区域定价" name="regions" :disabled="dialogMode === 'create'">
      <!-- Keep existing region pricing content -->
      ...
    </el-tab-pane>
  </el-tabs>

  <template #footer>
    <el-button @click="showDialog = false">取消</el-button>
    <el-button type="primary" :loading="submitLoading" @click="submit">确定</el-button>
  </template>
</el-dialog>
```

**Step 2: Add helper functions for excluded regions**

```typescript
function handleExcludedProvinceChange() {
  const selected = PROVINCES.filter(p => excludedProvinces.value.includes(p.code))
  form.value.excluded_regions = selected.map(p => ({ code: p.code, name: p.name }))
}

function removeExcludedProvince(code: string) {
  excludedProvinces.value = excludedProvinces.value.filter(c => c !== code)
  handleExcludedProvinceChange()
}

function getProvinceName(code: string): string {
  const province = PROVINCES.find(p => p.code === code)
  return province?.name || code
}

function handleFreeShippingTypeChange() {
  form.value.free_shipping_type = freeShippingType.value
  // Clear irrelevant fields
  if (freeShippingType.value !== 'amount') {
    form.value.free_threshold = null
  }
  if (freeShippingType.value !== 'quantity') {
    form.value.free_quantity = null
  }
}
```

**Step 3: Commit**

```bash
git add admin-web/src/views/ShippingTemplates.vue
git commit -m "feat(admin-web): add excluded regions and free shipping tabs"
```

---

## Task 8: Run Backend Tests

**Files:**
- Test: `backend/tests/services/test_shipping_template_service.py`

**Step 1: Run existing tests**

Run: `cd backend && pytest tests/services/test_shipping_template_service.py -v`
Expected: Some tests may fail due to schema changes

**Step 2: Fix failing tests**

Update test file to include new required fields in test data.

**Step 3: Add new tests for excluded regions**

```python
@pytest.mark.asyncio
async def test_calculate_shipping_excluded_region(db_session):
    """Test shipping calculation for excluded region"""
    service = ShippingTemplateService(db_session)

    # Create template with excluded region
    template = await service.create_template(ShippingTemplateCreate(
        name="Test Template",
        charge_type="fixed",
        default_first_cost=1000,
        excluded_regions=[{"code": "110000", "name": "北京市"}]
    ))

    # Calculate shipping for excluded region
    result = await service.calculate_shipping_cost(
        template_id=template.id,
        region_code="110000"
    )

    assert result["deliverable"] == False
    assert result["reason"] == "该地区不支持配送"
```

**Step 4: Add new tests for free shipping types**

```python
@pytest.mark.asyncio
async def test_free_shipping_by_quantity(db_session):
    """Test free shipping by quantity"""
    service = ShippingTemplateService(db_session)

    template = await service.create_template(ShippingTemplateCreate(
        name="Test Template",
        charge_type="quantity",
        default_first_unit=1,
        default_first_cost=1000,
        default_continue_unit=1,
        default_continue_cost=500,
        free_shipping_type="quantity",
        free_quantity=3
    ))

    # Below threshold
    result = await service.calculate_shipping_cost(
        template_id=template.id,
        quantity=2
    )
    assert result["free_shipping"] == False

    # At threshold
    result = await service.calculate_shipping_cost(
        template_id=template.id,
        quantity=3
    )
    assert result["free_shipping"] == True
    assert result["shipping_cost"] == 0


@pytest.mark.asyncio
async def test_seller_borne_shipping(db_session):
    """Test seller-borne shipping"""
    service = ShippingTemplateService(db_session)

    template = await service.create_template(ShippingTemplateCreate(
        name="Free Shipping Template",
        charge_type="fixed",
        default_first_cost=1000,
        free_shipping_type="seller"
    ))

    result = await service.calculate_shipping_cost(template_id=template.id)
    assert result["free_shipping"] == True
    assert result["shipping_cost"] == 0
```

**Step 5: Run all tests**

Run: `cd backend && pytest tests/services/test_shipping_template_service.py -v`
Expected: All tests pass

**Step 6: Commit**

```bash
git add backend/tests/services/test_shipping_template_service.py
git commit -m "test(shipping): add tests for new shipping template features"
```

---

## Task 9: Final Integration Test

**Step 1: Run backend server**

Run: `cd backend && uvicorn app.main:app --reload`

**Step 2: Run admin-web dev server**

Run: `cd admin-web && npm run dev`

**Step 3: Manual test checklist**

- [ ] Create new template with fixed shipping - verify only cost field shown
- [ ] Create template with volume charging
- [ ] Add excluded regions to template
- [ ] Set free shipping by quantity
- [ ] Set seller-borne shipping
- [ ] Edit existing template - verify data loads correctly
- [ ] Test API returns correct excluded_regions JSON

**Step 4: Final commit**

```bash
git add -A
git commit -m "feat(shipping): complete shipping template enhancement implementation"
```

---

## Summary

| Task | Description |
|------|-------------|
| 1 | Database migration |
| 2 | Update SQLAlchemy models |
| 3 | Update Pydantic schemas |
| 4 | Update service logic |
| 5 | Update frontend types |
| 6 | Update form logic |
| 7 | Update UI components |
| 8 | Backend tests |
| 9 | Integration testing |
