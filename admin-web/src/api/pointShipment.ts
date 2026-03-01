/**
 * 积分订单发货管理 API
 */
import { request } from '@/utils/request'

const PREFIX = '/admin/point-shipments'

// ==================== 类型定义 ====================

export interface TrackingEvent {
  time: string
  status: string
  location?: string
  description: string
}

export interface PointShipment {
  id: string
  order_id: string
  order_number: string // e.g., "PO20250101"
  product_name: string
  courier_code: string
  courier_name: string
  tracking_number: string
  status: 'pending' | 'picked_up' | 'in_transit' | 'delivered' | 'failed'
  shipped_at: string
  delivered_at?: string
  tracking_info?: TrackingEvent[]
  notes?: string | null
}

export interface PointOrderBasic {
  id: string
  order_number: string
  product_name: string
  status: string
  user_id: string
}

export interface PointShipmentListResult {
  shipments: PointShipment[]
  total: number
}

export interface PointShipmentCreate {
  order_id: string
  courier_code: string
  tracking_number: string
  notes?: string
}

export interface PointShipmentUpdate {
  tracking_number?: string
  status?: 'pending' | 'picked_up' | 'in_transit' | 'delivered' | 'failed'
  notes?: string
}

export interface PointShipmentListParams {
  order_number?: string
  status?: string
  courier_code?: string
  date_from?: string
  date_to?: string
  limit?: number
  offset?: number
}

// ==================== API 函数 ====================

/** 获取发货列表 */
export function listShipments(params?: PointShipmentListParams) {
  const {
    order_number,
    status,
    courier_code,
    date_from,
    date_to,
    limit = 20,
    offset = 0,
  } = params ?? {}
  const q = new URLSearchParams()
  q.set('skip', String(offset)) // 后端使用 skip 而不是 offset
  q.set('limit', String(limit))
  if (order_number) q.set('order_number', order_number)
  if (status) q.set('status', status)
  if (courier_code) q.set('courier_code', courier_code)
  if (date_from) q.set('date_from', date_from)
  if (date_to) q.set('date_to', date_to)

  return request<PointShipmentListResult>({
    url: `${PREFIX}?${q.toString()}`,
    method: 'GET',
  })
}

/** 获取待发货订单列表（没有发货记录的订单） */
export function getPendingOrders() {
  return request<PointOrderBasic[]>({
    url: `${PREFIX}/pending-orders`,
    method: 'GET',
  })
}

/** 创建发货记录 */
export function createShipment(data: PointShipmentCreate) {
  return request<{ id: string }>({
    url: PREFIX,
    method: 'POST',
    data,
  })
}

/** 更新发货记录 */
export function updateShipment(shipmentId: string, data: PointShipmentUpdate) {
  return request({
    url: `${PREFIX}/${shipmentId}`,
    method: 'PUT',
    data,
  })
}

/** 获取物流跟踪信息 */
export function getTracking(shipmentId: string) {
  return request<{ tracking_info: TrackingEvent[] }>({
    url: `${PREFIX}/${shipmentId}/tracking`,
    method: 'GET',
  })
}

/** 删除发货记录 */
export function deleteShipment(shipmentId: string) {
  return request({
    url: `${PREFIX}/${shipmentId}`,
    method: 'DELETE',
  })
}

/** 获取发货详情 */
export function getShipmentDetail(shipmentId: string) {
  return request<PointShipment>({
    url: `${PREFIX}/${shipmentId}`,
    method: 'GET',
  })
}
