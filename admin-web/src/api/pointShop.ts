/**
 * 积分商城管理 API
 */
import { request } from '@/utils/request'

const PREFIX = '/api/v1/point-shop/admin'

// ==================== 商品管理 ====================
export interface PointProduct {
  id: string
  name: string
  description: string | null
  image_url: string | null
  points_cost: number
  stock: number
  stock_unlimited: boolean
  category: string | null
  is_active: boolean
  sort_order: number
  created_at: string
}

export interface PointProductCreate {
  name: string
  description?: string | null
  image_url?: string | null
  points_cost: number
  stock: number
  stock_unlimited?: boolean
  category?: string | null
  sort_order?: number
}

export interface PointProductUpdate {
  name?: string
  description?: string | null
  image_url?: string | null
  points_cost?: number
  stock?: number
  stock_unlimited?: boolean
  category?: string | null
  is_active?: boolean
  sort_order?: number
}

export interface PointProductListResult {
  products: PointProduct[]
  total: number
}

/** 商品列表 */
export function listPointProducts(params?: {
  active_only?: boolean
  limit?: number
  offset?: number
}) {
  const { active_only = false, limit = 20, offset = 0 } = params ?? {}
  const q = new URLSearchParams()
  q.set('active_only', String(active_only))
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
export function deletePointProduct(productId: string) {
  return request({
    url: `${PREFIX}/products/${productId}`,
    method: 'DELETE',
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
}

export interface PointOrderListResult {
  orders: PointOrder[]
  total: number
}

/** 订单列表 */
export function listPointOrders(params?: {
  status?: string
  limit?: number
  offset?: number
}) {
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
export function processPointOrder(
  orderId: string,
  action: 'complete' | 'cancel',
  notes?: string
) {
  return request({
    url: `${PREFIX}/orders/${orderId}/process`,
    method: 'POST',
    data: { action, notes },
  })
}
