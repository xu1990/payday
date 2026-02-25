# 牛马日志 & Enhanced E-commerce Modules - Design Document

**Document Version:** 1.0
**Date:** 2025-02-24
**Status:** Approved
**Author:** AI Design Assistant

---

# Table of Contents

1. [Module 1: 牛马日志 (Work Diary)](#module-1-牛马日志-work-diary)
   - [Architecture Overview](#11-architecture-overview)
   - [Database Schema](#12-database-schema)
   - [API Design](#13-api-design)
   - [Data Flow](#14-data-flow)
   - [Caching Strategy](#15-caching-strategy)

2. [Module 2: Enhanced E-commerce System](#module-2-enhanced-ecommerce-system)
   - [Architecture Overview](#21-architecture-overview)
   - [Database Schema](#22-database-schema)
   - [API Design](#23-api-design)
   - [Distributed Locking](#24-distributed-locking-for-stock)
   - [Shipping & Return Workflow](#25-shipping--return-workflow)
   - [Virtual Products & Bundles](#26-virtual-products--bundles)
   - [Caching Strategy](#27-caching-strategy)

3. [Implementation Priorities](#3-implementation-priorities)

---

# Module 1: 牛马日志 (Work Diary)

## 1.1 Architecture Overview

### System Design

```
┌─────────────────────────────────────────────────────────────┐
│                     牛马日志 Module                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐         ┌──────────────┐                 │
│  │  WorkRecord  │────────▶│    Post      │                 │
│  │  (工作记录)   │  1:1    │  (社交帖子)   │                 │
│  │              │         │              │                 │
│  │ - clock_in   │         │ - comments  │                 │
│  │ - clock_out  │         │ - likes     │                 │
│  │ - overtime   │         │ - shares    │                 │
│  │ - work_type  │         │ - risk_ctl  │                 │
│  └──────────────┘         └──────────────┘                 │
│         │                                                   │
│         │ Reuses existing systems                          │
│         ▼                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Comment    │  │     Like     │  │ Notification │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

1. **WorkRecord-Post 1:1 Relationship**: Each work record creates exactly one social post
2. **Automatic Post Creation**: When user creates a WorkRecord, a corresponding Post is auto-generated
3. **Post Type = "work"**: New post type in the existing Post enum
4. **Reuses All Social Features**: Comments, likes, notifications, risk control work out-of-the-box

---

## 1.2 Database Schema

### New Tables

```sql
-- 工作记录表
CREATE TABLE work_records (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    post_id VARCHAR(36) UNIQUE NOT NULL,  -- Link to Post

    -- Clock In/Out
    clock_in_time DATETIME NOT NULL,
    clock_out_time DATETIME NULL,
    work_duration_minutes INT NULL,

    -- Work Details
    work_type VARCHAR(20) NOT NULL,  -- regular/overtime/weekend/holiday
    overtime_hours DECIMAL(4,2) DEFAULT 0,

    -- Location & Context
    location VARCHAR(200) NULL,
    company_name VARCHAR(100) NULL,

    -- Mood & Tags
    mood VARCHAR(20) NULL,  -- tired/stressed/motivated/neutral
    tags JSON NULL,  -- ["加班", "赶项目", "无休"]

    -- Content (shared with Post)
    content TEXT NOT NULL,
    images JSON NULL,

    -- Timestamps
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_user_date (user_id, clock_in_time),
    INDEX idx_work_type (work_type),
    INDEX idx_overtime (overtime_hours),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
);

-- Modify Post table to add 'work' type
ALTER TABLE posts MODIFY COLUMN type
    ENUM('complaint', 'sharing', 'question', 'work')
    DEFAULT 'sharing';
```

### Work Type Enum

| Type | Description | Overtime Calculation |
|------|-------------|---------------------|
| `regular` | Normal working hours | 0 |
| `overtime` | Weekday overtime | Based on clock_out - clock_in |
| `weekend` | Weekend work | Entire duration |
| `holiday` | Holiday work | Entire duration |

---

## 1.3 API Design

### Endpoints

```python
# app/api/v1/work_log.py

@router.post("/work-logs")
async def create_work_log(
    clock_in_time: datetime,
    content: str,
    work_type: WorkType,
    clock_out_time: datetime = None,
    images: List[str] = [],
    mood: str = None,
    tags: List[str] = [],
    location: str = None
):
    """
    Create work record + auto-generate social post

    Flow:
    1. Create WorkRecord
    2. Auto-create Post with type='work'
    3. Link WorkRecord.post_id = Post.id
    4. Trigger risk check (async)
    5. Return combined data
    """

@router.get("/work-logs")
async def list_work_logs(
    date_from: date,
    date_to: date,
    work_type: WorkType = None,
    page: int = 1
):
    """List user's work records with pagination"""

@router.get("/work-logs/{id}")
async def get_work_log(id: str):
    """Get work record with associated post, comments, likes"""

@router.put("/work-logs/{id}/clock-out")
async def clock_out(id: str, clock_out_time: datetime):
    """Record clock-out time and calculate duration"""

@router.get("/work-logs/feed")
async def get_work_feed(
    feed_type: str = "hot",  # hot/latest/following
    page: int = 1
):
    """
    Get social feed of work posts
    Reuses Post logic with filter: type='work'
    """
```

---

## 1.4 Data Flow

### Create Work Record Flow

```
User Request
     │
     ▼
┌─────────────────┐
│ Validate Input  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Create WorkRecord│
│ (work_records)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Create Post     │
│ type='work'     │
│ content/content │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Link:           │
│ work.post_id =  │
│   post.id       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Async Risk Check│ (Celery task)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Return Response │
│ with post_id    │
└─────────────────┘
```

---

## 1.5 Caching Strategy

```python
# Redis Keys

# User's work stats (TTL: 1h)
work:stats:{user_id}:{month} = {
    "total_overtime_hours": 45.5,
    "work_days": 22,
    "recent_mood": "tired"
}

# Hot work posts (TTL: 24h)
work:hot:{date} = ZSET(post_id, hot_score)

# Work record detail (TTL: 30min)
work:record:{id} = JSON(WorkRecord + Post summary)
```

---

# Module 2: Enhanced E-commerce System

## 2.1 Architecture Overview

```
┌────────────────────────────────────────────────────────────────────┐
│                   Enhanced E-commerce System                       │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │                    Product Catalog                        │      │
│  │  ┌──────────┐  ┌──────────┐  ┌────────────────┐         │      │
│  │  │ Category │─▶│ Product  │─▶│ ProductSKU     │         │      │
│  │  └──────────┘  └──────────┘  │ (variants)     │         │      │
│  │                               └────────────────┘         │      │
│  │  ┌────────────────┐  ┌──────────────────────┐           │      │
│  │  │ProductBundle   │  │ ProductPrice         │           │      │
│  │  │(pre/custom)    │  │ (multi-pricing)      │           │      │
│  │  └────────────────┘  └──────────────────────┘           │      │
│  └──────────────────────────────────────────────────────────┘      │
│                              │                                    │
│                              ▼                                    │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │                    Order System                           │      │
│  │  ┌──────────┐  ┌──────────┐  ┌────────────────┐         │      │
│  │  │   Order  │─▶│OrderItem │─▶│ OrderAddress   │         │      │
│  │  └──────────┘  └──────────┘  └────────────────┘         │      │
│  │  ┌──────────────────┐  ┌────────────────────┐            │      │
│  │  │OrderShipment     │  │ OrderReturn        │            │      │
│  │  │(shipping tracking│  │ (refund/replacement)│            │      │
│  │  └──────────────────┘  └────────────────────┘            │      │
│  └──────────────────────────────────────────────────────────┘      │
│                              │                                    │
│                              ▼                                    │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │                 Support Systems                            │      │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │      │
│  │  │UserAddress   │  │ShippingTemplate│ │Distributed   │   │      │
│  │  │              │  │              │  │Lock(Redis)  │   │      │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │      │
│  └──────────────────────────────────────────────────────────┘      │
│                                                                     │
└────────────────────────────────────────────────────────────────────┘
```

---

## 2.2 Database Schema

### 2.2.1 Product Tables

```sql
-- Product category table
CREATE TABLE product_categories (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    parent_id VARCHAR(36) NULL,  -- For subcategories
    icon VARCHAR(200) NULL,
    sort_order INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_parent (parent_id),
    INDEX idx_code (code),
    FOREIGN KEY (parent_id) REFERENCES product_categories(id)
);

-- Unified product table (replaces PointProduct)
CREATE TABLE products (
    id VARCHAR(36) PRIMARY KEY,

    -- Basic info
    name VARCHAR(100) NOT NULL,
    description TEXT NULL,
    images JSON NULL,  -- ["url1", "url2"]

    -- Classification
    category_id VARCHAR(36) NULL,
    product_type ENUM('point', 'cash', 'hybrid') DEFAULT 'point',
    item_type ENUM('physical', 'virtual', 'bundle') NOT NULL,
    bundle_type ENUM('pre_configured', 'custom_builder', NULL) NULL,

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_virtual BOOLEAN DEFAULT FALSE,
    sort_order INT DEFAULT 0,

    -- SEO
    seo_keywords VARCHAR(200) NULL,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_category (category_id),
    INDEX idx_type (product_type, item_type),
    INDEX idx_active (is_active, sort_order),
    FOREIGN KEY (category_id) REFERENCES product_categories(id)
);

-- Product SKU (for variants)
CREATE TABLE product_skus (
    id VARCHAR(36) PRIMARY KEY,
    product_id VARCHAR(36) NOT NULL,

    -- SKU identification
    sku_code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,  -- e.g., "Red - Size L"

    -- Variant attributes
    attributes JSON NOT NULL,  -- {"color": "red", "size": "L"}

    -- Inventory
    stock INT DEFAULT 0,
    stock_unlimited BOOLEAN DEFAULT FALSE,

    -- Images (specific to this SKU)
    images JSON NULL,

    -- Weight for shipping
    weight_grams INT NULL,

    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_product (product_id),
    INDEX idx_sku (sku_code),
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- Multi-pricing table
CREATE TABLE product_prices (
    id VARCHAR(36) PRIMARY KEY,
    sku_id VARCHAR(36) NOT NULL,

    -- Price type
    price_type ENUM('base', 'member', 'bulk', 'promotion') NOT NULL,

    -- Price (can be points or cash)
    price_amount DECIMAL(10, 2) NOT NULL,
    currency ENUM('CNY', 'POINTS') NOT NULL,

    -- Conditions
    min_quantity INT DEFAULT 1,  -- For bulk pricing
    membership_level INT NULL,   -- For member pricing
    valid_from DATETIME NULL,
    valid_until DATETIME NULL,

    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_sku (sku_id),
    INDEX idx_type (price_type),
    INDEX idx_currency (currency),
    UNIQUE KEY unique_price (sku_id, price_type, currency, min_quantity),
    FOREIGN KEY (sku_id) REFERENCES product_skus(id) ON DELETE CASCADE
);

-- Product bundles (for bundle_type='pre_configured')
CREATE TABLE product_bundles (
    id VARCHAR(36) PRIMARY KEY,
    bundle_product_id VARCHAR(36) NOT NULL,  -- The bundle product
    component_product_id VARCHAR(36) NOT NULL,  -- Component product
    component_sku_id VARCHAR(36) NULL,  -- Specific SKU if required
    quantity INT NOT NULL DEFAULT 1,

    is_required BOOLEAN DEFAULT TRUE,  -- For custom bundles

    INDEX idx_bundle (bundle_product_id),
    INDEX idx_component (component_product_id),
    FOREIGN KEY (bundle_product_id) REFERENCES products(id) ON DELETE CASCADE,
    FOREIGN KEY (component_product_id) REFERENCES products(id)
);
```

### 2.2.2 Address & Shipping Tables

```sql
-- 行政区域表（省市区数据）
CREATE TABLE admin_regions (
    id VARCHAR(36) PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,  -- 行政区划代码
    name VARCHAR(50) NOT NULL,
    level ENUM('province', 'city', 'district') NOT NULL,
    parent_code VARCHAR(20) NULL,  -- 父级区域代码

    sort_order INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,

    INDEX idx_parent (parent_code),
    INDEX idx_level (level),
    INDEX idx_code (code)
);

-- User addresses
CREATE TABLE user_addresses (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,

    -- Contact info
    receiver_name VARCHAR(50) NOT NULL,
    phone VARCHAR(20) NOT NULL,

    -- Address
    province_code VARCHAR(20) NOT NULL,
    city_code VARCHAR(20) NOT NULL,
    district_code VARCHAR(20) NOT NULL,
    detail_address VARCHAR(200) NOT NULL,
    postal_code VARCHAR(10) NULL,

    -- Metadata
    is_default BOOLEAN DEFAULT FALSE,
    address_tag VARCHAR(20) NULL,  -- 'home', 'office', 'school'

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_user (user_id),
    INDEX idx_default (user_id, is_default),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 运费模板表
CREATE TABLE shipping_templates (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    description VARCHAR(200) NULL,

    -- 默认运费（当区域未单独设置时使用）
    default_shipping_type ENUM('free', 'flat', 'quantity_based', 'weight_based') NOT NULL,
    default_cost DECIMAL(10, 2) DEFAULT 0,

    -- 计费规则
    billing_rules JSON NULL,
    /* Example for weight_based:
    {
        "base_cost": 10,        // 首重费用
        "base_weight": 1000,    // 首重(克)
        "additional_cost": 5,   // 续重费用
        "additional_weight": 1000 // 续重单位(克)
    }
    */

    -- 免邮条件
    free_shipping_min_amount DECIMAL(10, 2) NULL,  -- 订单满额免邮
    free_shipping_min_quantity INT NULL,           -- 满件数免邮

    -- 时效
    estimated_days_min INT NULL,  -- 最少送达天数
    estimated_days_max INT NULL,  -- 最多送达天数

    -- 支持的快递公司
    supported_couriers JSON NULL,  -- ["SF", "YTO", "STO"]

    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_active (is_active)
);

-- 运费模板-区域关联表
CREATE TABLE shipping_template_regions (
    id VARCHAR(36) PRIMARY KEY,
    template_id VARCHAR(36) NOT NULL,
    region_code VARCHAR(20) NOT NULL,  -- 关联到 admin_regions.code

    -- 区域类型
    region_type ENUM('free', 'shipping', 'no_shipping') NOT NULL,
    /*
    - free: 免邮区域（不计算运费）
    - shipping: 计费区域（按规则计算运费）
    - no_shipping: 不配送区域（用户无法选择）
    */

    -- 计费规则（仅 region_type='shipping' 时有效）
    shipping_type ENUM('flat', 'quantity_based', 'weight_based') NOT NULL,
    cost DECIMAL(10, 2) NOT NULL,  -- 固定运费或首费

    -- 计费规则（可覆盖模板默认）
    billing_rules JSON NULL,  -- 同 shipping_templates.billing_rules

    -- 免邮条件（可覆盖模板默认）
    free_shipping_min_amount DECIMAL(10, 2) NULL,
    free_shipping_min_quantity INT NULL,

    -- 时效（可覆盖模板默认）
    estimated_days_min INT NULL,
    estimated_days_max INT NULL,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_template (template_id),
    INDEX idx_region (region_code),
    INDEX idx_type (region_type),
    UNIQUE KEY unique_template_region (template_id, region_code),
    FOREIGN KEY (template_id) REFERENCES shipping_templates(id) ON DELETE CASCADE,
    FOREIGN KEY (region_code) REFERENCES admin_regions(code) ON DELETE CASCADE
);

-- 快递公司配置表
CREATE TABLE courier_companies (
    id VARCHAR(36) PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,  -- SF, YTO, STO, ZTO, EMS
    name VARCHAR(50) NOT NULL,
    name_en VARCHAR(50) NULL,

    -- API配置
    api_provider VARCHAR(50) NULL,  -- kuaidi100, kdniao, etc.
    api_key VARCHAR(100) NULL,
    api_secret VARCHAR(100) NULL,

    -- 配送范围
    service_regions JSON NULL,  -- 支持的区域代码列表

    -- 配送时效（天数）
    default_days_min INT NULL,
    default_days_max INT NULL,

    is_active BOOLEAN DEFAULT TRUE,
    sort_order INT DEFAULT 0,

    INDEX idx_active (is_active),
    INDEX idx_code (code)
);
```

### 2.2.3 Order Tables

```sql
-- Unified order table
CREATE TABLE orders (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    order_number VARCHAR(32) UNIQUE NOT NULL,

    -- Order info
    total_amount DECIMAL(10, 2) NOT NULL,  -- In cents/fen
    points_used INT DEFAULT 0,
    discount_amount DECIMAL(10, 2) DEFAULT 0,
    shipping_cost DECIMAL(10, 2) DEFAULT 0,
    final_amount DECIMAL(10, 2) NOT NULL,

    -- Payment
    payment_method ENUM('wechat', 'alipay', 'points', 'hybrid') NOT NULL,
    payment_status ENUM('pending', 'paid', 'failed', 'refunded') DEFAULT 'pending',
    transaction_id VARCHAR(100) NULL,
    paid_at DATETIME NULL,

    -- Status
    status ENUM(
        'pending',        -- Awaiting payment
        'paid',           -- Paid, awaiting shipment
        'processing',     -- Being prepared
        'shipped',        -- Shipped
        'delivered',      -- Delivered
        'completed',      -- Completed
        'cancelled',      -- Cancelled
        'refunding',      -- Refunding
        'refunded'        -- Refunded
    ) DEFAULT 'pending',

    -- Shipping
    shipping_address_id VARCHAR(36) NULL,
    shipping_template_id VARCHAR(36) NULL,

    -- Timestamps
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_user (user_id),
    INDEX idx_number (order_number),
    INDEX idx_status (status),
    INDEX idx_payment (payment_status),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (shipping_address_id) REFERENCES user_addresses(id)
);

-- Order items
CREATE TABLE order_items (
    id VARCHAR(36) PRIMARY KEY,
    order_id VARCHAR(36) NOT NULL,
    product_id VARCHAR(36) NOT NULL,
    sku_id VARCHAR(36) NULL,

    -- Item snapshot (at time of order)
    product_name VARCHAR(100) NOT NULL,
    sku_name VARCHAR(100) NULL,
    product_image VARCHAR(500) NULL,
    attributes JSON NULL,  -- Snapshot of SKU attributes

    -- Pricing snapshot
    unit_price DECIMAL(10, 2) NOT NULL,
    quantity INT NOT NULL,
    subtotal DECIMAL(10, 2) NOT NULL,

    -- For bundles
    bundle_components JSON NULL,  -- Array of component items

    INDEX idx_order (order_id),
    INDEX idx_product (product_id),
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
);

-- Order shipments
CREATE TABLE order_shipments (
    id VARCHAR(36) PRIMARY KEY,
    order_id VARCHAR(36) NOT NULL,

    -- Shipping info
    courier_code VARCHAR(20) NOT NULL,  -- SF, YTO, STO, etc.
    courier_name VARCHAR(50) NOT NULL,
    tracking_number VARCHAR(50) NOT NULL,

    -- Status
    status ENUM(
        'pending',      -- Awaiting pickup
        'picked_up',    -- Picked up
        'in_transit',   -- In transit
        'delivered',    -- Delivered
        'failed'        -- Delivery failed
    ) DEFAULT 'pending',

    -- Tracking
    shipped_at DATETIME NOT NULL,
    delivered_at DATETIME NULL,
    tracking_info JSON NULL,  -- Cached tracking data

    INDEX idx_order (order_id),
    INDEX idx_tracking (courier_code, tracking_number),
    FOREIGN KEY (order_id) REFERENCES orders(id)
);

-- Order returns
CREATE TABLE order_returns (
    id VARCHAR(36) PRIMARY KEY,
    order_id VARCHAR(36) NOT NULL,
    order_item_id VARCHAR(36) NOT NULL,

    -- Return reason
    return_reason VARCHAR(20) NOT NULL,  -- quality/wrong/forgot/other
    return_description TEXT NULL,
    images JSON NULL,

    -- Return type
    return_type ENUM('refund_only', 'replace', 'return_and_refund') NOT NULL,

    -- Status
    status ENUM(
        'requested',     -- User requested
        'approved',      -- Admin approved
        'rejected',      -- Admin rejected
        'shipped_back',  -- User shipped back
        'received',      -- Seller received
        'processing',    -- Processing refund/replacement
        'completed'      -- Completed
    ) DEFAULT 'requested',

    -- Resolution
    refund_amount DECIMAL(10, 2) NULL,
    refund_transaction_id VARCHAR(100) NULL,

    -- Timeline
    requested_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    approved_at DATETIME NULL,
    completed_at DATETIME NULL,

    -- Admin
    admin_id VARCHAR(36) NULL,
    admin_notes TEXT NULL,

    INDEX idx_order (order_id),
    INDEX idx_status (status),
    FOREIGN KEY (order_id) REFERENCES orders(id)
);
```

---

## 2.3 API Design

### Product APIs

```python
# app/api/v1/products.py

@router.get("/products")
async def list_products(
    category_id: str = None,
    product_type: str = None,  # point/cash/hybrid
    item_type: str = None,     # physical/virtual/bundle
    page: int = 1,
    page_size: int = 20,
    sort_by: str = "default"   # default/price_asc/price_desc/sales
):
    """List products with filters"""

@router.get("/products/{id}")
async def get_product(id: str):
    """Get product detail with all SKUs and prices"""

@router.get("/products/{id}/skus")
async def get_product_skus(id: str):
    """Get all SKUs for a product with prices"""

@router.post("/products/{id}/calculate-price")
async def calculate_price(
    id: str,
    sku_id: str,
    quantity: int = 1,
    user_membership_level: int = None
):
    """
    Calculate final price based on:
    - Base price
    - Bulk pricing
    - Member discount
    - Active promotions
    """
```

### Shopping Cart APIs

```python
# app/api/v1/cart.py

@router.get("/cart")
async def get_cart():
    """Get user's shopping cart"""

@router.post("/cart/items")
async def add_cart_item(
    sku_id: str,
    quantity: int = 1
):
    """Add item to cart with distributed lock"""

@router.put("/cart/items/{id}")
async def update_cart_item(
    id: str,
    quantity: int
):
    """Update cart item quantity with stock lock"""

@router.delete("/cart/items/{id}")
async def remove_cart_item(id: str):
    """Remove item from cart"""
```

### Order APIs

```python
# app/api/v1/orders.py

@router.post("/orders")
async def create_order(
    items: List[OrderItem],
    shipping_address_id: str,
    payment_method: str,
    points_to_use: int = 0
):
    """
    Create order with distributed locking:
    1. Lock stock for each SKU
    2. Calculate prices
    3. Create order
    4. Deduct stock
    5. Release locks
    """

@router.get("/orders/{id}")
async def get_order(id: str):
    """Get order details with items and shipment"""

@router.put("/orders/{id}/cancel")
async def cancel_order(id: str, reason: str):
    """Cancel order and restore stock"""

@router.post("/orders/{id}/pay")
async def pay_order(id: str):
    """Initiate payment (WeChat Pay / Points)"""
```

### Address APIs

```python
# app/api/v1/addresses.py

@router.get("/addresses")
async def list_addresses():
    """Get user's addresses"""

@router.post("/addresses")
async def create_address(data: AddressCreate):
    """Add new address"""

@router.put("/addresses/{id}")
async def update_address(id: str, data: AddressUpdate):
    """Update address"""

@router.delete("/addresses/{id}")
async def delete_address(id: str):
    """Delete address"""

@router.put("/addresses/{id}/default")
async def set_default_address(id: str):
    """Set as default address"""
```

### Shipping APIs

```python
# app/api/v1/shipping.py

@router.post("/shipping/calculate")
async def calculate_shipping(
    template_id: str,
    destination_code: str,  # 省市区代码
    items: List[CartItem],  # 购物车商品
    use_address_id: str = None  -- 或者使用地址ID
):
    """
    计算运费

    Request:
    {
        "template_id": "xxx",
        "destination_code": "310100"  // 上海市
        "items": [
            {"sku_id": "xxx", "quantity": 2}
        ]
    }

    Response:
    {
        "shipping_cost": 15.00,
        "is_free_shipping": False,
        "estimated_days_min": 2,
        "estimated_days_max": 4,
        "region_type": "shipping",
        "region_name": "上海市",
        "free_shipping_threshold": {
            "min_amount": 99.00,
            "min_quantity": null,
            "short_amount": 15.00  // 距免邮还差15元
        }
    }
    """
```

### Admin Shipping Template APIs

```python
# app/api/v1/admin/shipping.py

@router.get("/shipping/templates")
async def list_shipping_templates():
    """获取运费模板列表"""

@router.post("/shipping/templates")
async def create_shipping_template(data: ShippingTemplateCreate):
    """
    创建运费模板
    {
        "name": "江浙沪包邮",
        "default_shipping_type": "weight_based",
        "default_cost": 10,
        "billing_rules": {
            "base_cost": 10,
            "base_weight": 1000,
            "additional_cost": 5,
            "additional_weight": 1000
        },
        "free_shipping_min_amount": 99,
        "regions": [
            {
                "region_code": "310000",  // 上海
                "region_type": "free"
            },
            {
                "region_code": "320000",  // 江苏
                "region_type": "shipping",
                "shipping_type": "flat",
                "cost": 5
            },
            {
                "region_code": "810000",  // 香港
                "region_type": "no_shipping"
            }
        ]
    }
    """

@router.put("/shipping/templates/{id}")
async def update_shipping_template(
    id: str,
    data: ShippingTemplateUpdate
):
    """更新运费模板"""

@router.post("/shipping/templates/{id}/regions")
async def add_template_region(
    id: str,
    region_code: str,
    region_type: str,
    cost: Decimal = None,
    billing_rules: dict = None
):
    """添加区域配置到模板"""

@router.delete("/shipping/templates/{id}/regions/{region_id}")
async def remove_template_region(
    id: str,
    region_id: str
):
    """从模板移除区域"""

@router.get("/regions")
async def list_admin_regions(
    level: str = None,  # province/city/district
    parent_code: str = None
):
    """获取行政区域列表（级联选择）"""
```

---

## 2.4 Distributed Locking for Stock

### Redis-based Stock Lock

```python
# app/services/stock_lock.py

class StockLockService:
    """Distributed stock locking using Redis"""

    LOCK_TTL = 300  # 5 minutes

    async def acquire_stock_lock(
        self,
        sku_id: str,
        quantity: int
    ) -> bool:
        """
        Acquire lock on SKU stock

        Uses Redis INCR for atomic operation:
        1. Increment locked quantity
        2. Check if exceeds available stock
        3. If exceeds, rollback and return False

        Returns True if lock acquired, False if insufficient stock
        """
        lock_key = f"stock:lock:{sku_id}"
        stock_key = f"sku:stock:{sku_id}"

        pipe = redis.pipeline()

        # Get current stock and locked quantity
        pipe.get(stock_key)
        pipe.get(lock_key)
        stock, locked = await pipe.execute()

        available = int(stock) if stock else 0
        locked_qty = int(locked) if locked else 0

        # Check if enough stock
        if locked_qty + quantity > available:
            return False

        # Acquire lock
        await redis.incrby(lock_key, quantity)
        await redis.expire(lock_key, self.LOCK_TTL)

        return True

    async def confirm_stock(
        self,
        sku_id: str,
        quantity: int
    ):
        """
        Confirm stock deduction after order payment
        Removes from lock and deducts from actual stock
        """
        lock_key = f"stock:lock:{sku_id}"
        stock_key = f"sku:stock:{sku_id}"

        pipe = redis.pipeline()
        pipe.decrby(lock_key, quantity)
        pipe.decrby(stock_key, quantity)
        await pipe.execute()

    async def release_stock_lock(
        self,
        sku_id: str,
        quantity: int
    ):
        """
        Release stock lock (order cancelled/timeout)
        """
        lock_key = f"stock:lock:{sku_id}"
        await redis.decrby(lock_key, quantity)
```

### Order Creation Flow with Locks

```python
async def create_order_with_lock(
    user_id: str,
    items: List[OrderItemDTO],
    shipping_address_id: str
) -> Order:
    """
    Create order with distributed stock locking

    Flow:
    1. Validate shipping address
    2. Acquire stock locks for all items
    3. If any lock fails, release all and raise error
    4. Calculate prices
    5. Create order (status='pending')
    6. Initiate payment
    7. On payment success: confirm stock deduction
    8. On payment failure: release locks
    """

    # Step 1: Validate address
    address = await get_user_address(shipping_address_id)
    if not address or address.user_id != user_id:
        raise ValidationException("Invalid address")

    # Step 2: Acquire locks
    acquired_locks = []
    try:
        for item in items:
            locked = await stock_lock_service.acquire_stock_lock(
                item.sku_id,
                item.quantity
            )
            if not locked:
                raise BusinessException(
                    f"Insufficient stock for SKU {item.sku_id}"
                )
            acquired_locks.append(item)

        # Step 3-5: Create order
        order = await _create_order_in_db(
            user_id, items, address
        )

        # Step 6: Initiate payment
        payment_result = await initiate_payment(order)

        if payment_result.success:
            # Step 7: Confirm stock
            for item in items:
                await stock_lock_service.confirm_stock(
                    item.sku_id,
                    item.quantity
                )
            order.status = "paid"
        else:
            # Step 8: Release locks on payment failure
            for item in items:
                await stock_lock_service.release_stock_lock(
                    item.sku_id,
                    item.quantity
                )

        await db.commit()
        return order

    except Exception as e:
        # Release all acquired locks on error
        for item in acquired_locks:
            await stock_lock_service.release_stock_lock(
                item.sku_id,
                item.quantity
            )
        raise e
```

---

## 2.5 Shipping & Return Workflow

### Shipping Flow

```
Order Paid
    │
    ▼
┌─────────────────┐
│ Admin Process   │
│ (Pick & Pack)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Create Shipment │
│ - courier_code  │
│ - tracking_no   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Update Order    │
│ status='shipped'│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Notify User     │ (WeChat template msg)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Track Delivery  │ (Poll courier API)
│ - Update status │
│ - Auto-complete │
└─────────────────┘
```

### Return Flow

```
User Request Return
    │
    ▼
┌─────────────────┐
│ Create Return   │
│ status='req..'  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Admin Review    │
│ (approve/reject)│
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
[Approve] [Reject]
    │         │
    ▼         ▼
┌────────┐ ┌────────────┐
│User Ship│ │Notify User │
│Back     │ └────────────┘
└────┬────┘
     │
     ▼
┌─────────────────┐
│Seller Receives  │
└────────┬────────┘
     │
     ▼
┌─────────────────┐
│Process Resolution│
│- Refund         │
│- Replacement    │
└────────┬────────┘
     │
     ▼
┌─────────────────┐
│Complete Return  │
└─────────────────┘
```

---

## 2.6 Virtual Products & Bundles

### Virtual Product Delivery

```python
async def fulfill_virtual_order(order: Order):
    """
    Auto-fulfill virtual products

    Instant delivery products:
    - Membership extension
    - Theme unlock

    Manual processing products:
    - Gift cards
    - Coupon codes
    """
    for item in order.items:
        product = await get_product(item.product_id)

        if product.item_type == "virtual":
            # Check delivery type
            if product.delivery_type == "instant":
                # Instant delivery
                if product.virtual_type == "membership":
                    await extend_user_membership(
                        order.user_id,
                        item.product_id
                    )
                elif product.virtual_type == "theme":
                    await unlock_user_theme(
                        order.user_id,
                        item.product_id
                    )

                # Mark as completed
                order.status = "completed"

            elif product.delivery_type == "manual":
                # Requires admin processing
                order.status = "processing"
                await notify_admin_for_manual_processing(order.id)
```

### Bundle Products

```python
# Pre-configured bundle
async def fulfill_pre_configured_bundle(order_item: OrderItem):
    """
    Bundle is a single product with pre-defined components
    User just selects the bundle
    """
    bundle = await get_product_bundle(order_item.product_id)

    # Bundle already defined, just deliver
    # Physical: ship as single package
    # Virtual: deliver all components
    pass

# Custom bundle builder
async def fulfill_custom_bundle(order_item: OrderItem):
    """
    User builds their own bundle
    - Select X items from category
    - Dynamic pricing based on selection
    """
    # Bundle components stored in order_item.bundle_components
    # Each component fulfilled individually
    pass
```

---

## 2.7 Caching Strategy

```python
# Product catalog cache
product:detail:{id} = JSON(Product + SKUs + Prices)  # TTL: 1h
product:list:{category}:{page} = JSON(product_list)   # TTL: 10min

# Stock cache (critical for distributed lock)
sku:stock:{sku_id} = INT(stock_count)  # TTL: 5min

# User cart cache
cart:user:{user_id} = JSON(cart_items)  # TTL: 30min

# Order cache
order:detail:{id} = JSON(order + items)  # TTL: 24h

# Hot products (for ranking)
product:hot:{category} = ZSET(product_id, sales_score)  # TTL: 1h
```

---

# 3. Implementation Priorities

## Phase 1: 牛马日志 Module (Week 1-2)

**Priority: HIGH**
- Create `work_records` table
- Modify `posts` table to add 'work' type
- Implement WorkRecord CRUD APIs
- Implement auto-create Post logic
- Implement clock-in/clock-out functionality
- Add work feed (reuse Post feed with type filter)
- Add statistics (overtime hours by month)

**Deliverables:**
- Users can clock in/out for work
- Work records auto-create social posts
- Work posts appear in community feed
- Comments, likes, notifications work out-of-the-box

---

## Phase 2: E-commerce Core - Product Catalog (Week 3-4)

**Priority: HIGH**
- Create product schema tables (categories, products, SKUs, prices)
- Create address & shipping tables (admin_regions, user_addresses, shipping_templates)
- Migrate existing PointProduct data to new schema
- Implement product CRUD APIs
- Implement SKU & pricing management
- Implement address management APIs
- Implement shipping template management (admin)

**Deliverables:**
- Admin can create products with multi-SKU
- Admin can set multi-pricing (base, member, bulk)
- Users can manage delivery addresses
- Admin can configure shipping templates with regions

---

## Phase 3: E-commerce Core - Order System (Week 5-6)

**Priority: HIGH**
- Create order tables (orders, order_items, order_shipments, order_returns)
- Implement shopping cart APIs
- Implement distributed stock locking service
- Implement order creation flow with locks
- Implement payment integration (WeChat Pay + Points)
- Implement order status management

**Deliverables:**
- Users can add products to cart
- Users can create orders (points or cash)
- Stock is locked during order creation
- Orders can be paid with WeChat Pay or Points

---

## Phase 4: Shipping & Returns (Week 7-8)

**Priority: MEDIUM**
- Implement shipping cost calculator
- Implement shipment creation & tracking
- Implement courier API integration
- Implement return request flow
- Implement refund/replacement processing

**Deliverables:**
- System calculates shipping costs based on regions
- Admin can ship orders with tracking numbers
- Users can track shipment status
- Users can request returns
- Admin can process returns and refunds

---

## Phase 5: Advanced Features (Week 9-10)

**Priority: LOW**
- Implement virtual product auto-delivery
- Implement bundle products (pre-configured)
- Implement custom bundle builder
- Implement real-time tracking updates
- Implement order analytics & reports

**Deliverables:**
- Virtual products (membership, themes) auto-deliver
- Pre-configured bundles work correctly
- Advanced users can build custom bundles
- Tracking status updates automatically
- Admin has comprehensive order analytics

---

# Summary

## Module 1: 牛马日志 (Work Diary)

**Key Features:**
- WorkRecord table with clock-in/out, overtime tracking
- Auto-linked to Post for social features
- Work types: regular, overtime, weekend, holiday
- Mood, tags, location support
- Reuses Comment, Like, Notification, Risk Control

**Database Tables:**
- `work_records` (NEW)
- `posts` (MODIFY: add 'work' type)

---

## Module 2: Enhanced E-commerce

**Key Features:**
- Unified product schema (point + cash)
- Multi-SKU with variant attributes
- Multi-pricing (base, member, bulk, promotion)
- Product categories and bundles
- User addresses and shipping templates with regional support
- Distributed stock locking with Redis
- Complete shipping & return workflow
- Virtual product auto-delivery

**Database Tables:**
- `product_categories` (NEW)
- `products` (NEW - replaces `point_products`)
- `product_skus` (NEW)
- `product_prices` (NEW)
- `product_bundles` (NEW)
- `admin_regions` (NEW)
- `user_addresses` (NEW)
- `shipping_templates` (NEW)
- `shipping_template_regions` (NEW)
- `courier_companies` (NEW)
- `orders` (NEW - replaces `point_orders`)
- `order_items` (NEW)
- `order_shipments` (NEW)
- `order_returns` (NEW)

---

**Document Version:** 1.0
**Last Updated:** 2025-02-24
**Status:** Approved - Ready for Implementation Planning
