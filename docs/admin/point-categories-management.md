# 积分商品分类管理

## 功能概述

积分商品分类管理页面允许管理员创建和管理多级分类体系，最多支持3级分类。

## 访问路径

- 菜单位置：积分商城 -> 分类管理
- 路由：`/point-categories`

## 功能说明

### 分类树（左侧面板）

1. **查看分类结构**
   - 树形显示所有分类
   - 支持展开/折叠子分类
   - 显示分类状态（启用/禁用）

2. **选择分类**
   - 点击分类节点选中
   - 选中后可进行编辑、删除、添加子分类操作

3. **拖拽排序**
   - 支持拖拽节点调整顺序（前端视觉）
   - 实际排序通过 `sort_order` 字段控制

### 分类编辑（右侧面板）

#### 新建根分类

1. 点击"新建根分类"按钮
2. 填写分类信息：
   - **分类名称**（必填）：最多50字符
   - **分类描述**（可选）：分类说明
   - **分类图标**（可选）：建议尺寸 64x64px
   - **分类横幅**（可选）：建议尺寸 750x300px
   - **排序权重**：数值越大越靠前
   - **是否启用**：控制分类在前端显示

#### 新建子分类

1. 先选择父分类
2. 点击"新建子分类"按钮
3. 自动设置父分类和层级

#### 编辑分类

1. 选择要编辑的分类
2. 点击"编辑"按钮
3. 修改分类信息
4. 点击"确定"保存

#### 删除分类

1. 选择要删除的分类
2. 点击"删除"按钮
3. 确认删除

**限制**：
- 有子分类的分类无法删除
- 有商品的分类无法删除（后端检查）

## API 接口

### 前端 API 客户端

位置：`admin-web/src/api/pointCategory.ts`

```typescript
// 获取分类列表（平铺）
listPointCategories({ active_only: false })

// 获取分类树（层级结构）
getCategoryTree({ active_only: false })

// 创建分类
createPointCategory({
  name: '数码产品',
  level: 1,
  description: '数码产品分类',
  parent_id: null,
  icon_url: 'https://...',
  banner_url: 'https://...',
  sort_order: 100,
  is_active: true
})

// 更新分类
updatePointCategory(categoryId, {
  name: '新名称',
  is_active: false
})

// 删除分类
deletePointCategory(categoryId)
```

### 后端 API 端点

位置：`backend/app/api/v1/point_categories.py`

- `GET /api/v1/admin/point-categories` - 获取分类列表
- `GET /api/v1/admin/point-categories/tree` - 获取分类树
- `GET /api/v1/admin/point-categories/{id}` - 获取单个分类
- `POST /api/v1/admin/point-categories` - 创建分类
- `PUT /api/v1/admin/point-categories/{id}` - 更新分类
- `DELETE /api/v1/admin/point-categories/{id}` - 删除分类

## 数据模型

### PointCategory

```typescript
interface PointCategory {
  id: string                  // UUID
  name: string                // 分类名称
  description: string | null  // 分类描述
  parent_id: string | null    // 父分类ID
  icon_url: string | null     // 图标URL
  banner_url: string | null   // 横幅URL
  level: number               // 层级（1/2/3）
  sort_order: number          // 排序权重
  is_active: boolean          // 是否启用
  created_at: string          // 创建时间
  updated_at: string          // 更新时间
  children?: PointCategory[]  // 子分类（仅tree接口）
}
```

## 使用场景

### 示例分类结构

```
📁 实物奖励
  📁 数码产品
    📄 手机
    📄 电脑
  📁 生活用品
    📄 家居
    📄 个护
📁 虚拟奖励
  📁 优惠券
  📁 会员卡
```

### 最佳实践

1. **层级深度**
   - 建议不超过3级
   - 过深的层级影响用户体验

2. **命名规范**
   - 简洁明了，便于用户理解
   - 避免使用特殊字符

3. **排序建议**
   - 重要分类使用较高数值
   - 同级分类按 100、90、80 递减
   - 便于后续插入新分类

4. **图标和横幅**
   - 图标：使用 PNG/JPG，透明背景更佳
   - 横幅：展示分类特色商品

5. **启用/禁用**
   - 临时下架使用禁用，而非删除
   - 禁用分类下所有商品不可见

## 注意事项

1. **分类删除限制**
   - 有子分类无法删除
   - 有商品关联无法删除（需先处理商品）

2. **图片上传**
   - 支持格式：jpg/png/gif
   - 单文件大小限制：5MB
   - 使用腾讯云 COS 存储

3. **权限控制**
   - 需要管理员权限
   - 所有接口需要 JWT 认证

## 相关文件

- 前端页面：`admin-web/src/views/PointCategories.vue`
- 前端 API：`admin-web/src/api/pointCategory.ts`
- 后端路由：`backend/app/api/v1/point_categories.py`
- 后端服务：`backend/app/services/point_category_service.py`
- 数据模型：`backend/app/models/point_category.py`
