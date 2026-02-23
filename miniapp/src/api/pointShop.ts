/**
 * 积分商城 API - Sprint 4.7
 */
import request from '@/utils/request'

const PREFIX = '/api/v1/point-shop'

// ==================== 商品 ====================

/** 商品项 */
export interface PointProduct {
  id: string
  name: string
  description: string | null
  image_url: string | null
  points_cost: number
  stock: number
  stock_unlimited: boolean
  category: string | null
}

/** 商品列表响应 */
export interface PointProductsResponse {
  products: PointProduct[]
  total: number
}

/** 获取商品列表 */
export function getPointProducts(category?: string) {
  const url = category ? `${PREFIX}/products?category=${category}` : `${PREFIX}/products`
  return request<PointProductsResponse>({
    url,
    method: 'GET',
  })
}

/** 获取商品详情 */
export function getPointProduct(productId: string) {
  return request<PointProduct>({
    url: `${PREFIX}/products/${productId}`,
    method: 'GET',
  })
}

// ==================== 订单 ====================

/** 订单创建请求 */
export interface PointOrderCreate {
  product_id: string
  delivery_info?: string
  notes?: string
}

/** 订单项 */
export interface PointOrder {
  id: string
  order_number: string
  product_name: string
  product_image: string | null
  points_cost: number
  status: 'pending' | 'completed' | 'cancelled' | 'refunded'
  created_at: string
}

/** 订单列表响应 */
export interface PointOrdersResponse {
  orders: PointOrder[]
  total: number
}

/** 创建订单（下单） */
export function createPointOrder(data: PointOrderCreate) {
  return request<PointOrder>({
    url: `${PREFIX}/orders`,
    method: 'POST',
    data,
  })
}

/** 获取我的订单列表 */
export function getMyPointOrders(status?: string, limit = 50, offset = 0) {
  let url = `${PREFIX}/orders?limit=${limit}&offset=${offset}`
  if (status) url += `&status=${status}`
  return request<PointOrdersResponse>({
    url,
    method: 'GET',
  })
}

/** 订单详情（包含更多信息） */
export interface PointOrderDetail extends PointOrder {
  delivery_info?: string
  notes?: string
}

/** 获取订单详情 */
export function getPointOrderDetail(orderId: string) {
  return request<PointOrderDetail>({
    url: `${PREFIX}/orders/${orderId}`,
    method: 'GET',
  })
}

/** 取消订单 */
export function cancelPointOrder(orderId: string) {
  return request({
    url: `${PREFIX}/orders/${orderId}/cancel`,
    method: 'POST',
  })
}
