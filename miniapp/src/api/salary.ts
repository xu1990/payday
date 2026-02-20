/**
 * 工资记录 - 与 backend /api/v1/salary 一致；金额 API 为元
 */
import request from '@/utils/request'

const PREFIX = '/api/v1/salary'

/** 工资类型 */
export type SalaryType = 'normal' | 'bonus' | 'allowance' | 'other'
/** 心情 */
export type MoodType = 'happy' | 'relief' | 'sad' | 'angry' | 'expect'

export interface SalaryRecord {
  id: string
  user_id: string
  config_id: string
  amount: number
  before_tax: number | null
  tax_amount: number | null
  payday_date: string
  salary_type: SalaryType
  salary_source: string | null
  delay_days: number | null
  delay_reason: string | null
  images: string[] | null
  note: string | null
  mood: MoodType
  risk_status: string
  created_at: string
  updated_at: string
}

export interface SalaryRecordCreate {
  config_id: string
  amount: number
  before_tax?: number | null
  tax_amount?: number | null
  payday_date: string
  salary_type?: SalaryType
  salary_source?: string | null
  delay_days?: number | null
  delay_reason?: string | null
  images?: string[] | null
  note?: string | null
  mood: MoodType
}

export interface SalaryRecordUpdate {
  amount?: number
  before_tax?: number | null
  tax_amount?: number | null
  payday_date?: string
  salary_type?: SalaryType
  salary_source?: string | null
  delay_days?: number | null
  delay_reason?: string | null
  images?: string[] | null
  note?: string | null
  mood?: MoodType
}

export interface SalaryListParams {
  config_id?: string
  from_date?: string
  to_date?: string
  limit?: number
  offset?: number
}

/** 列表 */
export function listSalary(params?: SalaryListParams) {
  let url = PREFIX
  if (params && Object.keys(params).length) {
    const queryParts: string[] = []
    if (params.config_id) queryParts.push(`config_id=${encodeURIComponent(params.config_id)}`)
    if (params.from_date) queryParts.push(`from_date=${encodeURIComponent(params.from_date)}`)
    if (params.to_date) queryParts.push(`to_date=${encodeURIComponent(params.to_date)}`)
    if (params.limit != null) queryParts.push(`limit=${encodeURIComponent(String(params.limit))}`)
    if (params.offset != null)
      queryParts.push(`offset=${encodeURIComponent(String(params.offset))}`)
    const qs = queryParts.join('&')
    if (qs) url += (url.includes('?') ? '&' : '?') + qs
  }
  return request<SalaryRecord[]>({ url, method: 'GET' })
}

/** 新增 */
export function createSalary(data: SalaryRecordCreate) {
  return request<SalaryRecord>({ url: PREFIX, method: 'POST', data })
}

/** 单条 */
export function getSalary(recordId: string) {
  return request<SalaryRecord>({ url: `${PREFIX}/${recordId}`, method: 'GET' })
}

/** 更新 */
export function updateSalary(recordId: string, data: SalaryRecordUpdate) {
  return request<SalaryRecord>({ url: `${PREFIX}/${recordId}`, method: 'PUT', data })
}

/** 删除 */
export function deleteSalary(recordId: string) {
  return request<void>({ url: `${PREFIX}/${recordId}`, method: 'DELETE' })
}
