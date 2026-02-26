# 运费模板增强设计方案

## 概述

本文档描述运费模板功能的增强设计，解决以下问题：
1. 固定费用模式参数冗余
2. 不支持设置部分地区不配送
3. 包邮条件不够丰富
4. 缺少按体积计费方式

## 设计方案：渐进式增强

在现有架构上逐步增强，最小化改动，保证向后兼容。

## 数据模型变更

### ShippingTemplate 表新增字段

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `free_shipping_type` | VARCHAR(20) | 'none' | 包邮类型：none/amount/quantity/seller |
| `free_quantity` | INT | NULL | 满件数包邮阈值 |
| `excluded_regions` | JSON | NULL | 不配送区域 `[{code, name}]` |
| `volume_unit` | INT | NULL | 体积单位（cm³），计费方式为volume时使用 |

### ShippingTemplateRegion 表新增字段

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `free_quantity` | INT | NULL | 区域满件数包邮阈值 |
| `is_excluded` | TINYINT(1) | 0 | 标记为不配送区域 |

## 枚举值定义

### ChargeType (计费方式)

| 值 | 说明 | 单位 |
|----|------|------|
| `weight` | 按重量 | 克(g) |
| `quantity` | 按件数 | 件 |
| `fixed` | 固定运费 | - |
| `volume` | 按体积 | 立方厘米(cm³) |

### FreeShippingType (包邮类型)

| 值 | 说明 | 所需字段 |
|----|------|----------|
| `none` | 不包邮 | - |
| `amount` | 满金额包邮 | `free_threshold` |
| `quantity` | 满件数包邮 | `free_quantity` |
| `seller` | 卖家承担运费 | - |

## 前端UI设计

### 运费模板编辑弹窗Tab结构

```
┌─────────────────────────────────────────────────┐
│ [基本信息] [区域定价] [不配送区域] [包邮规则]    │
├─────────────────────────────────────────────────┤
│                                                 │
│  (各Tab内容)                                    │
│                                                 │
└─────────────────────────────────────────────────┘
```

### 基本信息 Tab

**计费方式选择**：
- 按重量（weight）
- 按件数（quantity）
- 固定运费（fixed）
- 按体积（volume）- 新增

**字段显示逻辑**：

| 计费方式 | 显示字段 |
|----------|----------|
| weight | 首重、首重运费、续重、续重运费 |
| quantity | 首件、首件运费、续件、续件运费 |
| fixed | 仅显示固定运费金额 |
| volume | 首体积、首体积运费、续体积、续体积运费 |

### 不配送区域 Tab（新增）

- 省份多选器
- 已选区域列表（可删除）
- 不配送原因输入（可选）

### 包邮规则 Tab（新增）

**包邮类型单选**：
- 不包邮（none）
- 满金额包邮（amount）→ 显示金额输入框
- 满件数包邮（quantity）→ 显示件数输入框
- 卖家承担运费（seller）→ 无需额外输入

### 区域定价 Tab（增强）

- 保持原有功能
- 新增「满件数包邮」字段
- 新增「设为不配送」开关

## API 变更

### Schema 变更

#### ShippingTemplateCreate

```python
class ShippingTemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    charge_type: Literal["weight", "quantity", "fixed", "volume"]

    # 计费参数（根据charge_type部分必填）
    default_first_unit: Optional[int] = None
    default_first_cost: Optional[int] = None
    default_continue_unit: Optional[int] = None
    default_continue_cost: Optional[int] = None

    # 包邮设置
    free_shipping_type: Literal["none", "amount", "quantity", "seller"] = "none"
    free_threshold: Optional[int] = None  # 满金额包邮
    free_quantity: Optional[int] = None   # 满件数包邮

    # 不配送区域
    excluded_regions: Optional[List[Dict[str, str]]] = None  # [{code, name}]

    # 预计送达
    estimate_days_min: Optional[int] = None
    estimate_days_max: Optional[int] = None
```

#### ShippingTemplateRegionCreate

```python
class ShippingTemplateRegionCreate(BaseModel):
    region_codes: str
    region_names: str

    # 计费参数
    first_unit: int
    first_cost: int
    continue_unit: int
    continue_cost: int

    # 包邮设置
    free_threshold: Optional[int] = None
    free_quantity: Optional[int] = None  # 新增

    # 不配送标记
    is_excluded: bool = False  # 新增
```

### 运费计算逻辑

```python
async def calculate_shipping_cost(
    self,
    template_id: str,
    region_code: Optional[str] = None,
    weight: Optional[int] = None,
    quantity: Optional[int] = None,
    volume: Optional[int] = None,  # 新增
    total_amount: Optional[int] = None
) -> dict:

    template = await self.get_template(template_id)

    # 1. 检查是否在不配送区域
    excluded_regions = template.excluded_regions or []
    excluded_codes = [r.get('code') for r in excluded_regions]
    if region_code in excluded_codes:
        return {
            "deliverable": False,
            "reason": "该地区不支持配送"
        }

    # 2. 检查区域级别的不配送标记
    region = await self._get_region_for_code(template_id, region_code)
    if region and region.is_excluded:
        return {
            "deliverable": False,
            "reason": "该地区不支持配送"
        }

    # 3. 检查卖家承担运费
    if template.free_shipping_type == "seller":
        return {
            "shipping_cost": 0,
            "free_shipping": True,
            "deliverable": True
        }

    # 4. 检查满件数包邮
    free_qty = region.free_quantity if region else template.free_quantity
    if template.free_shipping_type == "quantity" and quantity and free_qty:
        if quantity >= free_qty:
            return {
                "shipping_cost": 0,
                "free_shipping": True,
                "deliverable": True
            }

    # 5. 检查满金额包邮
    free_amt = region.free_threshold if region else template.free_threshold
    if template.free_shipping_type == "amount" and total_amount and free_amt:
        if total_amount >= free_amt:
            return {
                "shipping_cost": 0,
                "free_shipping": True,
                "deliverable": True
            }

    # 6. 固定运费
    if template.charge_type == "fixed":
        return {
            "shipping_cost": template.default_first_cost,
            "free_shipping": False,
            "deliverable": True
        }

    # 7. 按重量/件数/体积计费（原有逻辑）
    ...
```

## 数据库迁移

```sql
-- ShippingTemplate 新增字段
ALTER TABLE shipping_templates
ADD COLUMN free_shipping_type VARCHAR(20) DEFAULT 'none' COMMENT '包邮类型: none/amount/quantity/seller',
ADD COLUMN free_quantity INT DEFAULT NULL COMMENT '满件数包邮阈值',
ADD COLUMN excluded_regions JSON DEFAULT NULL COMMENT '不配送区域JSON',
ADD COLUMN volume_unit INT DEFAULT NULL COMMENT '体积单位(cm³)';

-- ShippingTemplateRegion 新增字段
ALTER TABLE shipping_template_regions
ADD COLUMN free_quantity INT DEFAULT NULL COMMENT '区域满件数包邮阈值',
ADD COLUMN is_excluded TINYINT(1) DEFAULT 0 COMMENT '是否不配送区域';
```

## 实施计划

### 阶段1：后端模型与API
1. 新增数据库字段（Alembic迁移）
2. 更新Pydantic Schema
3. 更新ShippingTemplateService
4. 更新API路由

### 阶段2：前端实现
1. 更新TypeScript类型定义
2. 更新ShippingTemplates.vue组件
3. 新增不配送区域Tab
4. 新增包邮规则Tab
5. 固定运费模式字段简化

### 阶段3：测试
1. 单元测试更新
2. 集成测试更新
3. E2E测试

## 兼容性说明

- 所有新增字段都有默认值，不影响现有数据
- 现有模板默认 `free_shipping_type = 'none'`，保持原有行为
- `excluded_regions` 默认为空，不影响配送范围
- 前端向后兼容，旧模板正常显示和编辑
