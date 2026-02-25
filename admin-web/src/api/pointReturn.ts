/**
 * 积分订单退货管理 API
 */
import { request } from '@/utils/request'

const PREFIX = '/point-returns'

// ==================== 退货管理 ====================

/**
 * 退货申请状态
 */
export type ReturnStatus = 'requested' | 'approved' | 'rejected'

/**
 * 退货申请
 */
export interface PointReturn {
  id: string
  order_id: string
  order_number: string
  reason: string
  status: ReturnStatus
  admin_notes: string | null
  admin_id: string | null
  created_at: string
  processed_at: string | null
}

/**
 * 创建退货申请
 */
export interface PointReturnCreate {
  order_id: string
  reason: string
}

/**
 * 退货列表结果
 */
export interface PointReturnListResult {
  returns: PointReturn[]
  total: number
}

/**
 * 退货列表查询参数
 */
export interface PointReturnListParams {
  status?: ReturnStatus | ''
  start_date?: string
  end_date?: string
  limit?: number
  offset?: number
}

/**
 * 获取退货列表
 */
export function listReturns(params?: PointReturnListParams) {
  const { limit = 20, offset = 0, status, start_date, end_date } = params ?? {}
  const q = new URLSearchParams()
  q.set('limit', String(limit))
  q.set('offset', String(offset))
  if (status) q.set('status', status)
  if (start_date) q.set('start_date', start_date)
  if (end_date) q.set('end_date', end_date)

  return request<PointReturnListResult>({
    url: `${PREFIX}?${q.toString()}`,
    method: 'GET',
  })
}

/**
 * 创建退货申请
 */
export function createReturn(data: PointReturnCreate) {
  return request<{ id: string }>({
    url: `${PREFIX}/returns`,
    method: 'POST',
    data,
  })
}

/**
 * 为订单创建退货申请
 */
export function createOrderReturn(orderId: string, reason: string) {
  return request<{ id: string }>({
    url: `${PREFIX}/orders/${orderId}/return`,
    method: 'POST',
    data: { reason },
  })
}

/**
 * 批准退货申请
 */
export function approveReturn(returnId: string, adminNotes: string) {
  return request({
    url: `${PREFIX}/${returnId}/approve`,
    method: 'POST',
    data: { admin_notes: adminNotes },
  })
}

/**
 * 拒绝退货申请
 */
export function rejectReturn(returnId: string, adminNotes: string) {
  return request({
    url: `${PREFIX}/${returnId}/reject`,
    method: 'POST',
    data: { admin_notes: adminNotes },
  })
}
