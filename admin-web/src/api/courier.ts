/**
 * 物流公司管理 API
 */
import { request } from '@/utils/request'

const PREFIX = '/admin/couriers'

// ==================== 类型定义 ====================
export interface CourierCompany {
  id: string
  code: string // e.g., "SF", "ZTO"
  name: string // e.g., "顺丰速运", "中通快递"
  website: string | null
  tracking_url: string | null
  supports_cod: boolean
  supports_cold_chain: boolean
  sort_order: number
  is_active: boolean
  created_at: string
}

export interface CourierCreate {
  code: string
  name: string
  website?: string | null
  tracking_url?: string | null
  supports_cod?: boolean
  supports_cold_chain?: boolean
  sort_order?: number
  is_active?: boolean
}

export interface CourierUpdate {
  code?: string
  name?: string
  website?: string | null
  tracking_url?: string | null
  supports_cod?: boolean
  supports_cold_chain?: boolean
  sort_order?: number
  is_active?: boolean
}

export interface CourierListResult {
  couriers: CourierCompany[]
  total: number
}

// ==================== API 函数 ====================

/** 获取物流公司列表 */
export function listCouriers(params?: { active_only?: boolean; limit?: number; offset?: number }) {
  const { active_only = false, limit = 20, offset = 0 } = params ?? {}
  const q = new URLSearchParams()
  q.set('active_only', String(active_only))
  q.set('limit', String(limit))
  q.set('offset', String(offset))
  return request<CourierListResult>({
    url: `${PREFIX}?${q.toString()}`,
    method: 'GET',
  })
}

/** 创建物流公司 */
export function createCourier(data: CourierCreate) {
  return request<{ id: string }>({
    url: PREFIX,
    method: 'POST',
    data,
  })
}

/** 获取物流公司详情 */
export function getCourier(courierId: string) {
  return request<CourierCompany>({
    url: `${PREFIX}/${courierId}`,
    method: 'GET',
  })
}

/** 更新物流公司 */
export function updateCourier(courierId: string, data: CourierUpdate) {
  return request({
    url: `${PREFIX}/${courierId}`,
    method: 'PUT',
    data,
  })
}

/** 删除物流公司 */
export function deleteCourier(courierId: string) {
  return request({
    url: `${PREFIX}/${courierId}`,
    method: 'DELETE',
  })
}

/** 获取启用的物流公司列表（用于下拉选择） */
export function listActiveCouriers() {
  return request<CourierCompany[]>({
    url: `${PREFIX}/active`,
    method: 'GET',
  })
}
