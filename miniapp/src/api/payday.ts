/**
 * 发薪日配置 - 与 backend app.api.v1.payday 一致
 */
import request from '@/utils/request'

const PREFIX = '/api/v1/payday'

/** 发薪日配置（与 PaydayConfigResponse 一致） */
export interface PaydayConfig {
  id: string
  user_id: string
  job_name: string
  payday: number
  calendar_type: 'solar' | 'lunar'
  estimated_salary: number | null
  is_active: number
  created_at: string
  updated_at: string
}

/** 新增参数 */
export interface PaydayConfigCreate {
  job_name: string
  payday: number
  calendar_type?: 'solar' | 'lunar'
  estimated_salary?: number | null
  is_active?: number
}

/** 更新参数（全部可选） */
export interface PaydayConfigUpdate {
  job_name?: string
  payday?: number
  calendar_type?: 'solar' | 'lunar'
  estimated_salary?: number | null
  is_active?: number
}

/** 列表 */
export function listPayday() {
  return request<PaydayConfig[]>({ url: PREFIX, method: 'GET' })
}

/** 新增 */
export function createPayday(data: PaydayConfigCreate) {
  return request<PaydayConfig>({ url: PREFIX, method: 'POST', data })
}

/** 单条 */
export function getPayday(configId: string) {
  return request<PaydayConfig>({ url: `${PREFIX}/${configId}`, method: 'GET' })
}

/** 更新 */
export function updatePayday(configId: string, data: PaydayConfigUpdate) {
  return request<PaydayConfig>({ url: `${PREFIX}/${configId}`, method: 'PUT', data })
}

/** 删除（204 无 body） */
export function deletePayday(configId: string) {
  return request<void>({ url: `${PREFIX}/${configId}`, method: 'DELETE' })
}
