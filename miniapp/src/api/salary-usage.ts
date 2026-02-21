/**
 * 薪资使用记录 API
 * 与 backend /api/v1/salary-usage 一致
 */
import request from '@/utils/request'

const PREFIX = '/api/v1/salary-usage'

/** 消费类型 */
export type UsageType =
  | 'housing'
  | 'food'
  | 'transport'
  | 'shopping'
  | 'entertainment'
  | 'medical'
  | 'education'
  | 'other'

export interface SalaryUsageRecord {
  id: string
  user_id: string
  salary_record_id: string
  usage_type: UsageType
  amount: number
  usage_date: string
  description: string | null
  created_at: string
  updated_at: string
}

export interface SalaryUsageCreate {
  salary_record_id: string
  usage_type: UsageType
  amount: number
  usage_date: string
  description?: string | null
}

export interface SalaryUsageUpdate {
  usage_type?: UsageType
  amount?: number
  usage_date?: string
  description?: string | null
}

export interface SalaryUsageListParams {
  salary_record_id?: string
  usage_type?: UsageType
  from_date?: string
  to_date?: string
  limit?: number
  offset?: number
}

/** 列表 */
export function listSalaryUsage(params?: SalaryUsageListParams) {
  let url = PREFIX
  if (params && Object.keys(params).length) {
    const queryParts: string[] = []
    if (params.salary_record_id)
      queryParts.push(`salary_record_id=${encodeURIComponent(params.salary_record_id)}`)
    if (params.usage_type) queryParts.push(`usage_type=${encodeURIComponent(params.usage_type)}`)
    if (params.from_date) queryParts.push(`from_date=${encodeURIComponent(params.from_date)}`)
    if (params.to_date) queryParts.push(`to_date=${encodeURIComponent(params.to_date)}`)
    if (params.limit != null) queryParts.push(`limit=${encodeURIComponent(String(params.limit))}`)
    if (params.offset != null)
      queryParts.push(`offset=${encodeURIComponent(String(params.offset))}`)
    const qs = queryParts.join('&')
    if (qs) url += (url.includes('?') ? '&' : '?') + qs
  }
  return request<SalaryUsageRecord[]>({ url, method: 'GET' })
}

/** 新增 */
export function createSalaryUsage(data: SalaryUsageCreate) {
  return request<SalaryUsageRecord>({ url: PREFIX, method: 'POST', data })
}

/** 单条 */
export function getSalaryUsage(recordId: string) {
  return request<SalaryUsageRecord>({ url: `${PREFIX}/${recordId}`, method: 'GET' })
}

/** 更新 */
export function updateSalaryUsage(recordId: string, data: SalaryUsageUpdate) {
  return request<SalaryUsageRecord>({ url: `${PREFIX}/${recordId}`, method: 'PUT', data })
}

/** 删除 */
export function deleteSalaryUsage(recordId: string) {
  return request<void>({ url: `${PREFIX}/${recordId}`, method: 'DELETE' })
}
