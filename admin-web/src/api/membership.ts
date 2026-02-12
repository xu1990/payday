/**
 * 会员套餐管理 API
 */
import { request } from '@/utils/request'

const PREFIX = '/api/v1/admin/config/memberships'

export interface MembershipItem {
  id: string
  name: string
  description: string | null
  price: number
  duration_days: number
  is_active: boolean
  sort_order: number
  created_at: string
}

export interface MembershipCreate {
  name: string
  description?: string | null
  price: number
  duration_days: number
  sort_order?: number
}

export interface MembershipUpdate {
  name?: string
  description?: string | null
  price?: number
  duration_days?: number
  is_active?: boolean
  sort_order?: number
}

export interface MembershipListResult {
  items: MembershipItem[]
  total: number
}

/** 会员套餐列表 */
export function listMemberships(params?: {
  active_only?: boolean
  limit?: number
  offset?: number
}) {
  const { active_only = false, limit = 20, offset = 0 } = params ?? {}
  const q = new URLSearchParams()
  q.set('active_only', String(active_only))
  q.set('limit', String(limit))
  q.set('offset', String(offset))
  return request<MembershipListResult>({
    url: `${PREFIX}?${q.toString()}`,
    method: 'GET',
  })
}

/** 创建套餐 */
export function createMembership(data: MembershipCreate) {
  return request<MembershipItem>({
    url: PREFIX,
    method: 'POST',
    data,
  })
}

/** 获取单个套餐 */
export function getMembership(membershipId: string) {
  return request<MembershipItem>({
    url: `${PREFIX}/${membershipId}`,
    method: 'GET',
  })
}

/** 更新套餐 */
export function updateMembership(membershipId: string, data: MembershipUpdate) {
  return request<MembershipItem>({
    url: `${PREFIX}/${membershipId}`,
    method: 'PUT',
    data,
  })
}

/** 删除套餐 */
export function deleteMembership(membershipId: string) {
  return request<{ deleted: boolean }>({
    url: `${PREFIX}/${membershipId}`,
    method: 'DELETE',
  })
}
