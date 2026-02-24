# 积分商城管理后台模块设计文档

**Date:** 2025-02-24
**Status:** Approved
**Author:** Claude (Brainstorming Session)

---

## Overview

本文档描述了积分商城管理后台缺失功能的完整设计方案。该项目需要在现有基础上新增 7 个管理页面，覆盖分类、规格、物流、地址、运费、发货、退货等功能。

### Current State

**Existing Backend Models:**
- `PointProduct` - 商品基本信息
- `PointOrder` - 积分订单
- `UserAddress` - 用户收货地址
- `AdminRegion` - 行政区域
- `CourierCompany` - 物流公司
- `OrderShipment` - 订单发货
- `OrderReturn` - 订单退货
- `ShippingTemplate` - 运费模板

**Existing Admin Pages:**
- `PointShop.vue` - 商品 CRUD（基础版）
- `PointOrders.vue` - 订单列表与处理

### Missing Pages

1. **分类管理** - 商品分类树形结构管理
2. **商品规格管理** - SKU 多规格系统
3. **物流公司管理** - 快递公司基础 CRUD
4. **用户地址管理** - 查看和管理用户收货地址
5. **运费模板** - 区域化运费配置
6. **发货管理** - 订单发货与物流跟踪
7. **退货管理** - 退货审批流程

---

## Architecture Decision

### Selected Approach: Standalone Pages with Shared API

**Rationale:**
- Matches existing admin-web architecture patterns
- Easy to implement incrementally
- Clear separation of concerns
- Simpler debugging and maintenance
- Can reuse shared components

---

## Section 1: Database Models

### 1.1 New Models

#### PointCategory (商品分类表)

```python
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

#### PointSpecification (商品规格表)

```python
class PointSpecification(Base):
    """商品规格定义表（如：颜色、尺寸）"""
    __tablename__ = "point_specifications"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    product_id = Column(String(36), ForeignKey("point_products.id"),
                       nullable=False, index=True, comment="商品ID")
    name = Column(String(50), nullable=False, comment="规格名称")
    sort_order = Column(Integer, default=0, nullable=False, comment="排序权重")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
```

#### PointSpecificationValue (规格值表)

```python
class PointSpecificationValue(Base):
    """规格值表（如：红色、蓝色、L、XL）"""
    __tablename__ = "point_specification_values"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    specification_id = Column(String(36), ForeignKey("point_specifications.id"),
                             nullable=False, index=True, comment="规格ID")
    value = Column(String(50), nullable=False, comment="规格值")
    sort_order = Column(Integer, default=0, nullable=False, comment="排序权重")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
```

#### PointProductSKU (商品SKU表)

```python
class PointProductSKU(Base):
    """商品SKU表 - 多规格库存管理"""
    __tablename__ = "point_product_skus"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    product_id = Column(String(36), ForeignKey("point_products.id"),
                       nullable=False, index=True, comment="商品ID")
    sku_code = Column(String(50), unique=True, nullable=False,
                     index=True, comment="SKU编码")
    specs = Column(Text, nullable=False, comment="规格组合JSON")
    # Example: {"颜色": "红色", "尺寸": "L"}

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

#### PointReturn (积分订单退货表)

```python
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

### 1.2 Updated Models

#### PointProduct (Update)

```python
# Add these fields:
category_id = Column(String(36), ForeignKey("point_categories.id"),
                    nullable=True, index=True, comment="分类ID")
has_sku = Column(Boolean, default=False,
                 nullable=False, comment="是否启用SKU管理")

# Keep 'category' string for backward compatibility during transition
```

#### PointOrder (Update)

```python
# Add these fields:
sku_id = Column(String(36), ForeignKey("point_product_skus.id"),
               nullable=True, comment="SKU ID")
address_id = Column(String(36), ForeignKey("user_addresses.id"),
                   nullable=True, comment="收货地址ID")
shipment_id = Column(String(36), ForeignKey("order_shipments.id"),
                    nullable=True, comment="发货ID")
```

---

## Section 2: API Routes

### 2.1 Category Management

```
GET    /api/v1/admin/point-categories
POST   /api/v1/admin/point-categories
GET    /api/v1/admin/point-categories/{id}
PUT    /api/v1/admin/point-categories/{id}
DELETE /api/v1/admin/point-categories/{id}
GET    /api/v1/admin/point-categories/tree
PUT    /api/v1/admin/point-categories/{id}/move
```

### 2.2 SKU/Specification Management

```
# Specifications
GET    /api/v1/admin/point-products/{product_id}/specifications
POST   /api/v1/admin/point-products/{product_id}/specifications
PUT    /api/v1/admin/specifications/{id}
DELETE /api/v1/admin/specifications/{id}

# Specification Values
GET    /api/v1/admin/specifications/{spec_id}/values
POST   /api/v1/admin/specifications/{spec_id}/values
DELETE /api/v1/admin/specification-values/{id}

# SKUs
GET    /api/v1/admin/point-products/{product_id}/skus
POST   /api/v1/admin/point-products/{product_id}/skus
PUT    /api/v1/admin/skus/{id}
DELETE /api/v1/admin/skus/{id}
POST   /api/v1/admin/skus/batch-update
```

### 2.3 Courier Management

```
GET    /api/v1/admin/couriers
POST   /api/v1/admin/couriers
GET    /api/v1/admin/couriers/{id}
PUT    /api/v1/admin/couriers/{id}
DELETE /api/v1/admin/couriers/{id}
GET    /api/v1/admin/couriers/active
```

### 2.4 User Address Management

```
GET    /api/v1/admin/user-addresses
GET    /api/v1/admin/user-addresses/{id}
PUT    /api/v1/admin/user-addresses/{id}
POST   /api/v1/admin/user-addresses/{id}/set-default
GET    /api/v1/admin/users/{user_id}/addresses
```

### 2.5 Shipping Templates

```
GET    /api/v1/admin/shipping-templates
POST   /api/v1/admin/shipping-templates
GET    /api/v1/admin/shipping-templates/{id}
PUT    /api/v1/admin/shipping-templates/{id}
DELETE /api/v1/admin/shipping-templates/{id}

# Region Pricing
GET    /api/v1/admin/shipping-templates/{id}/regions
POST   /api/v1/admin/shipping-templates/{id}/regions
PUT    /api/v1/admin/shipping-template-regions/{region_id}
DELETE /api/v1/admin/shipping-template-regions/{region_id}
```

### 2.6 Shipment Tracking

```
GET    /api/v1/admin/point-shipments
POST   /api/v1/admin/point-orders/{order_id}/ship
PUT    /api/v1/admin/point-shipments/{id}
GET    /api/v1/admin/point-shipments/{id}/tracking
```

### 2.7 Returns Management

```
GET    /api/v1/admin/point-returns
POST   /api/v1/admin/point-orders/{order_id}/return
POST   /api/v1/admin/point-returns/{id}/approve
POST   /api/v1/admin/point-returns/{id}/reject
```

### 2.8 User-Facing Updates

```
GET    /api/v1/point-shop/products
       Response: Add sku_enabled flag

GET    /api/v1/point-shop/products/{id}
       Response: Add specifications, sku_list

POST   /api/v1/point-shop/orders
       Request: Add sku_id field (when has_sku=true)
```

---

## Section 3: Admin Pages

### 3.1 PointCategories.vue - 分类管理

**Features:**
- Tree view (el-tree) with drag-drop reordering
- Add root category / Add subcategory
- Edit: name, description, icon, banner, sort_order
- Delete: check if has products/children
- Category icons and banner images upload

**Layout:**
```
┌─────────────────────────────────────────────────────────┐
│  [分类树 (拖拽排序)]        │  [分类编辑表单]              │
│  📁 实物奖励                 │  Name: [_____]             │
│    📁 数码产品               │  Description: [_____]      │
│      📄 手机                │  Icon: [Upload]            │
│      📄 电脑                │  Banner: [Upload]          │
│    📁 生活用品               │  Sort: [10]                │
│  📁 虚拟奖励                 │  Active: [✓]               │
│    📄 优惠券                 │  [Save] [Cancel]           │
│  [+ 新建分类]                │                            │
└─────────────────────────────────────────────────────────┘
```

### 3.2 PointShop.vue (Enhanced) - 商品 + SKU

**Enhanced Features:**
- "Enable SKU" switch
- Category dropdown (tree select)
- SKU management section

**SKU Section:**
```
[规格配置]
+ Add Spec
├── Color: [Red] [Blue] [Green] [Delete]
└── Size:  [S]   [M]    [L]     [Delete]
[Generate SKUs] Button

[SKU Table]
┌─────────┬───────┬──────┬─────────┬───────┬────────────┐
│ Color   │ Size  │ Stock│ Price   │ Image │ Actions    │
├─────────┼───────┼──────┼─────────┼───────┼────────────┤
│ Red     │ S     │ [10] │ [100]   │ [Upload]│ Edit/Delete│
│ Red     │ M     │ [20] │ [100]   │ [Upload]│ Edit/Delete│
└─────────┴───────┴──────┴─────────┴───────┴────────────┘
```

### 3.3 Couriers.vue - 物流公司

**Simple CRUD Table:**
```
┌──────┬────────┬──────────┬─────────────┬────────┬─────────┐
│ Name │ Code   │ Website  │ Tracking URL│ Active │ Actions │
├──────┼────────┼──────────┼─────────────┼────────┼─────────┤
│ 顺丰  │ SF     │ sf-ex... │ sf.com/... │   ✓    │Edit/Del │
│ 中通  │ ZTO    │ zto.com  │ zto.com/.. │   ✓    │Edit/Del │
└──────┴────────┴──────────┴─────────────┴────────┴─────────┘
[+ Add Courier]
```

### 3.4 UserAddresses.vue - 用户地址

**Search & Table:**
```
Search: [User ID] [Phone] [Province/City Filter]

┌──────┬────────┬─────────┬───────┬────────┬─────────┐
│ User │ Contact│ Phone   │ Region│ Address│ Default │
├──────┼────────┼─────────┼───────┼────────┼─────────┤
│ 123  │ 张三   │138****  │ 北京朝阳│ xx路1号│   ★    │View/Edit│
│ 456  │ 李四   │139****  │ 上海浦东│ yy路2号│        │View/Edit│
└──────┴────────┴─────────┴───────┴────────┴─────────┘
```

**Edit Dialog:**
- All address fields editable
- Set as default button
- Mark as invalid button
- Audit log display

### 3.5 ShippingTemplates.vue - 运费模板

**Template List + Edit Dialog:**
```
[Template List Table]

[Edit Dialog]
Basic Info:
- Template Name: [____]
- Charge Type: [Weight ▼]
- Free Threshold: [____]
- Estimate Days: [3] - [7]

Default Pricing:
- First Unit: [500] (cost)
- Continue Unit: [10] (cost/kg)

Region Pricing:
┌────────────┬──────────┬──────────┬───────────┬────────┐
│ Regions    │ First    │ Continue │ Free      │Active  │
├────────────┼──────────┼──────────┼───────────┼────────┤
│ 北京,上海  │ 500      │ 10/kg    │ 5000      │   ✓    │Edit/Del│
│ 广东,广西  │ 400      │ 8/kg     │ 3000      │   ✓    │Edit/Del│
└────────────┴──────────┴──────────┴───────────┴────────┘
[+ Add Region]
```

### 3.6 PointShipments.vue - 发货管理

**Table with Actions:**
```
Filter: [Order #] [Status] [Courier] [Date Range]

┌────────────┬─────────┬────────┬────────┬────────┬──────────┐
│ Order #    │ Product │ Courier│ Track #│ Status │ Actions  │
├────────────┼─────────┼────────┼────────┼────────┼──────────┤
│ PO20250101 │ 商品A   │ 顺丰   │ SF123  │ Shipped│Track/Del │
│ PO20250102 │ 商品B   │ 中通   │ ZTO456 │ Pending│Edit      │
└────────────┴─────────┴────────┴────────┴────────┴──────────┘
[+ Create Shipment]
```

**Create Shipment:**
- Select pending order
- Select courier (dropdown)
- Enter tracking number
- Save

### 3.7 PointReturns.vue - 退货管理

**Table + Actions:**
```
┌────────────┬────────┬────────┬────────┬────────┐
│ Order #    │ Reason │ Status │ Date   │ Actions│
├────────────┼────────┼────────┼────────┼────────┤
│ PO20250101 │ 质量问题│ Pending│ 01-20  │Approve │
│ PO20250102 │ 不想要了│ Rejected│ 01-19  │View    │
└────────────┴────────┴────────┴────────┴────────┘
```

**Actions:**
- Approve: Add notes → confirm
- Reject: Require reason → confirm
- View: Show full details

**Status Flow:**
```
requested → approved (process refund)
          → rejected (no action)
```

---

## Section 4: Shared Components

### 4.1 Component List

| Component | Purpose | Props |
|-----------|---------|-------|
| `CategoryTreeSelect.vue` | Category tree picker | `modelValue`, `placeholder`, `disabled` |
| `AddressForm.vue` | Address input form | `modelValue`, `showDefault` |
| `CourierSelect.vue` | Courier dropdown | `modelValue`, `activeOnly` |
| `RegionPricingForm.vue` | Shipping region config | `modelValue`, `chargeType` |
| `SpecEditor.vue` | Specifications editor | `modelValue`, `productId` |
| `SKUTable.vue` | SKU data table | `modelValue`, `specifications` |

### 4.2 API Client Modules

New files in `admin-web/src/api/`:
- `pointCategory.ts`
- `courier.ts`
- `userAddress.ts`
- `shippingTemplate.ts`
- `pointShipment.ts`
- `pointReturn.ts`
- Update `pointShop.ts` for SKU endpoints

---

## Section 5: Router Configuration

Add to `admin-web/src/router/index.ts`:

```typescript
{
  path: '/admin/point-categories',
  name: 'PointCategories',
  component: () => import('@/views/PointCategories.vue'),
  meta: { title: '积分商品分类', requiresAdmin: true }
},
{
  path: '/admin/couriers',
  name: 'Couriers',
  component: () => import('@/views/Couriers.vue'),
  meta: { title: '物流公司管理', requiresAdmin: true }
},
{
  path: '/admin/user-addresses',
  name: 'UserAddresses',
  component: () => import('@/views/UserAddresses.vue'),
  meta: { title: '用户地址管理', requiresAdmin: true }
},
{
  path: '/admin/shipping-templates',
  name: 'ShippingTemplates',
  component: () => import('@/views/ShippingTemplates.vue'),
  meta: { title: '运费模板', requiresAdmin: true }
},
{
  path: '/admin/point-shipments',
  name: 'PointShipments',
  component: () => import('@/views/PointShipments.vue'),
  meta: { title: '积分订单发货', requiresAdmin: true }
},
{
  path: '/admin/point-returns',
  name: 'PointReturns',
  component: () => import('@/views/PointReturns.vue'),
  meta: { title: '退货管理', requiresAdmin: true }
}
```

---

## Section 6: Backend Services

New service files in `backend/app/services/`:
- `point_category_service.py`
- `point_sku_service.py`
- `courier_service.py`
- `user_address_service.py`
- `shipping_template_service.py`
- `point_shipment_service.py`
- `point_return_service.py`

---

## Section 7: Implementation Notes

### 7.1 Database Migrations

Create Alembic migrations for:
1. New tables: `point_categories`, `point_specifications`, `point_specification_values`, `point_product_skus`, `point_returns`
2. Update `point_products` table (add `category_id`, `has_sku`)
3. Update `point_orders` table (add `sku_id`, `address_id`, `shipment_id`)

### 7.2 Data Migration

- Migrate existing `category` strings to new `PointCategory` records
- Create default SKU for existing products (if `has_sku=false`)

### 7.3 Testing

- Unit tests for all service layer functions
- Integration tests for API endpoints
- Frontend component tests (Vitest)

---

## Summary

This design completes the points shop admin module with 7 management pages, 6 new database models, and comprehensive API coverage. The implementation follows existing patterns and maintains consistency with the current codebase architecture.

**Next Steps:** Create detailed implementation plan using the `writing-plans` skill.
