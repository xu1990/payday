/**
 * 积分商城管理 API
 */
import { request } from '@/utils/request'

const PREFIX = '/point-shop/admin'

// ==================== 商品类型和物流方式 ====================
export type ProductType = 'virtual' | 'physical' | 'bundle'
export type ShippingMethod = 'express' | 'self_pickup' | 'no_shipping'

// ==================== 商品管理 ====================
export interface PointProduct {
  id: string
  name: string
  description: string | null
  image_urls: string[]
  image_url: string | null // 兼容旧版，第一张图片
  points_cost: number
  stock: number
  stock_unlimited: boolean
  sold: number
  fake_sold: number // 注水销量
  total_sold: number // 总销量（实际+注水）
  category: string | null
  category_id: string | null
  has_sku: boolean
  product_type: ProductType
  shipping_method: ShippingMethod
  shipping_template_id: string | null
  is_active: boolean
  off_shelf_reason: string | null // 下架/删除原因
  sort_order: number
  created_at: string
}

export interface SpecificationInput {
  name: string
  values: string[]
}

export interface SKUInput {
  sku_code?: string
  specs: Record<string, string>
  stock: number
  stock_unlimited?: boolean
  points_cost: number
  image_url?: string
  sort_order?: number
  is_active?: boolean
}

export interface PointProductCreate {
  name: string
  description?: string | null
  image_urls?: string[]
  points_cost: number
  stock: number
  stock_unlimited?: boolean
  fake_sold?: number // 注水销量
  category?: string | null
  category_id?: string | null
  has_sku?: boolean
  product_type?: ProductType
  shipping_method?: ShippingMethod
  shipping_template_id?: string | null
  sort_order?: number
  is_active?: boolean
  // SKU相关数据，创建时一起提交
  specifications?: SpecificationInput[]
  skus?: SKUInput[]
}

export interface PointProductUpdate {
  name?: string
  description?: string | null
  image_urls?: string[]
  points_cost?: number
  stock?: number
  stock_unlimited?: boolean
  fake_sold?: number // 注水销量
  category?: string | null
  category_id?: string | null
  has_sku?: boolean
  is_active?: boolean
  product_type?: ProductType
  shipping_method?: ShippingMethod
  shipping_template_id?: string | null
  sort_order?: number
  off_shelf_reason?: string // 下架/删除原因
  // SKU相关数据， 更新时一起提交
  specifications?: SpecificationInput[]
  skus?: SKUInput[]
}

export interface PointProductListResult {
  products: PointProduct[]
  total: number
}

/** 商品列表 */
export function listPointProducts(params?: {
  active_only?: boolean
  category_id?: string
  is_active?: boolean
  keyword?: string
  product_type?: string
  limit?: number
  offset?: number
}) {
  const {
    active_only,
    category_id,
    is_active,
    keyword,
    product_type,
    limit = 20,
    offset = 0,
  } = params ?? {}
  const q = new URLSearchParams()
  if (active_only !== undefined) q.set('active_only', String(active_only))
  if (category_id) q.set('category_id', category_id)
  if (is_active !== undefined) q.set('is_active', String(is_active))
  if (keyword) q.set('keyword', keyword)
  if (product_type) q.set('product_type', product_type)
  q.set('limit', String(limit))
  q.set('offset', String(offset))
  return request<PointProductListResult>({
    url: `${PREFIX}/products?${q.toString()}`,
    method: 'GET',
  })
}

/** 创建商品 */
export function createPointProduct(data: PointProductCreate) {
  return request<{ id: string }>({
    url: `${PREFIX}/products`,
    method: 'POST',
    data,
  })
}

/** 获取商品详情 */
export function getPointProduct(productId: string) {
  return request<PointProduct>({
    url: `${PREFIX}/products/${productId}`,
    method: 'GET',
  })
}

/** 更新商品 */
export function updatePointProduct(productId: string, data: PointProductUpdate) {
  return request({
    url: `${PREFIX}/products/${productId}`,
    method: 'PUT',
    data,
  })
}

/** 删除商品（软删除） */
export function deletePointProduct(productId: string, reason?: string) {
  return request({
    url: `${PREFIX}/products/${productId}`,
    method: 'DELETE',
    data: reason ? { reason } : undefined,
  })
}

/** 下架商品 */
export function offShelfProduct(productId: string, reason: string) {
  return request({
    url: `${PREFIX}/products/${productId}`,
    method: 'PUT',
    data: { is_active: false, off_shelf_reason: reason },
  })
}

// ==================== 订单管理 ====================
export interface PointOrder {
  id: string
  order_number: string
  user_id: string
  product_name: string
  product_image: string | null
  points_cost: number
  status: 'pending' | 'completed' | 'cancelled' | 'refunded'
  created_at: string
  processed_at: string | null
  notes_admin: string | null
  // 发货相关字段
  product_type?: ProductType
  shipping_method?: ShippingMethod
  shipment_id?: string | null
}

export interface PointOrderListResult {
  orders: PointOrder[]
  total: number
}

/** 订单列表 */
export function listPointOrders(params?: { status?: string; limit?: number; offset?: number }) {
  const { limit = 20, offset = 0, status } = params ?? {}
  const q = new URLSearchParams()
  q.set('limit', String(limit))
  q.set('offset', String(offset))
  if (status) q.set('status', status)
  return request<PointOrderListResult>({
    url: `${PREFIX}/orders?${q.toString()}`,
    method: 'GET',
  })
}

/** 处理订单（完成或取消） */
export function processPointOrder(orderId: string, action: 'complete' | 'cancel', notes?: string) {
  return request({
    url: `${PREFIX}/orders/${orderId}/process`,
    method: 'POST',
    data: { action, notes },
  })
}

/** 订单发货 */
export function shipPointOrder(
  orderId: string,
  data: { courier_code: string; tracking_number: string }
) {
  return request<{ id: string }>({
    url: `/admin/point-shipments/point-orders/${orderId}/ship`,
    method: 'POST',
    data,
  })
}
