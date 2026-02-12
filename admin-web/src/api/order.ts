/**
 * 会员订单管理 API
 */
import { request } from '@/utils/request'

const PREFIX = '/api/v1/admin/config/orders'

export interface OrderItem {
  id: string
  user_id: string
  membership_id: string
  membership_name: string
  amount: number
  status: 'pending' | 'paid' | 'cancelled' | 'refunded'
  payment_method: string | null
  start_date: string
  end_date: string | null
  created_at: string
}

export interface OrderStatusUpdate {
  status: 'pending' | 'paid' | 'cancelled' | 'refunded'
}

export interface OrderListResult {
  items: OrderItem[]
  total: number
}

/** 订单列表 */
export function listOrders(params?: {
  limit?: number
  offset?: number
}) {
  const { limit = 20, offset = 0 } = params ?? {}
  const q = new URLSearchParams()
  q.set('limit', String(limit))
  q.set('offset', String(offset))
  return request<OrderListResult>({
    url: `${PREFIX}?${q.toString()}`,
    method: 'GET',
  })
}

/** 更新订单状态 */
export function updateOrderStatus(orderId: string, data: OrderStatusUpdate) {
  return request<OrderItem>({
    url: `${PREFIX}/${orderId}`,
    method: 'PUT',
    data,
  })
}
