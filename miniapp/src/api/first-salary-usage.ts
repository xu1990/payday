/**
 * 第一笔工资用途 API
 * 与 backend /api/v1/first-salary-usage 一致
 */
import request from '@/utils/request'

const PREFIX = '/api/v1/first-salary-usage'

/** 用途分类类型 */
export type UsageCategory =
  | '存起来'
  | '交家里'
  | '买东西'
  | '请客吃饭'
  | '旅游'
  | '学习'
  | '其他'

/** 子分类（预设选项） */
export type UsageSubcategory =
  | '银行存款'
  | '理财'
  | '给父母'
  | '还房贷'
  | '数码产品'
  | '衣服鞋包'
  | '美妆护肤'
  | '食品饮料'
  | '旅游出行'
  | '教育培训'
  | '娱乐休闲'
  | '医疗健康'
  | '其他'

export interface FirstSalaryUsageRecord {
  id: string
  user_id: string
  salary_record_id: string
  usage_category: UsageCategory
  usage_subcategory: UsageSubcategory | null
  amount: number
  note: string | null
  created_at: string
  updated_at: string
}

export interface FirstSalaryUsageCreate {
  salary_record_id: string
  usage_category: UsageCategory
  usage_subcategory?: UsageSubcategory | null
  amount: number
  note?: string | null
}

export interface FirstSalaryUsageUpdate {
  usage_category?: UsageCategory
  usage_subcategory?: UsageSubcategory | null
  amount?: number
  note?: string | null
}

export interface FirstSalaryUsageListParams {
  salary_record_id?: string
  usage_category?: UsageCategory
  skip?: number
  limit?: number
}

export interface FirstSalaryUsageListResponse {
  total: number
  items: FirstSalaryUsageRecord[]
}

export interface CategoryStatistics {
  statistics: Record<UsageCategory, number>
}

/** 列表 */
export function listFirstSalaryUsage(params?: FirstSalaryUsageListParams) {
  let url = PREFIX
  if (params && Object.keys(params).length) {
    const queryParts: string[] = []
    if (params.salary_record_id)
      queryParts.push(`salary_record_id=${encodeURIComponent(params.salary_record_id)}`)
    if (params.usage_category)
      queryParts.push(`usage_category=${encodeURIComponent(params.usage_category)}`)
    if (params.skip != null)
      queryParts.push(`skip=${encodeURIComponent(String(params.skip))}`)
    if (params.limit != null)
      queryParts.push(`limit=${encodeURIComponent(String(params.limit))}`)
    const qs = queryParts.join('&')
    if (qs) url += `?${qs}`
  }
  return request<FirstSalaryUsageListResponse>({ url, method: 'GET' })
}

/** 新增 */
export function createFirstSalaryUsage(data: FirstSalaryUsageCreate) {
  return request<FirstSalaryUsageRecord>({ url: PREFIX, method: 'POST', data })
}

/** 单条 */
export function getFirstSalaryUsage(recordId: string) {
  return request<FirstSalaryUsageRecord>({ url: `${PREFIX}/${recordId}`, method: 'GET' })
}

/** 更新 */
export function updateFirstSalaryUsage(recordId: string, data: FirstSalaryUsageUpdate) {
  return request<FirstSalaryUsageRecord>({ url: `${PREFIX}/${recordId}`, method: 'PUT', data })
}

/** 删除 */
export function deleteFirstSalaryUsage(recordId: string) {
  return request<void>({ url: `${PREFIX}/${recordId}`, method: 'DELETE' })
}

/** 按分类统计 */
export function getCategoryStatistics(params?: { salary_record_id?: string }) {
  let url = `${PREFIX}/statistics/by-category`
  if (params && params.salary_record_id) {
    url += `?salary_record_id=${encodeURIComponent(params.salary_record_id)}`
  }
  return request<CategoryStatistics>({ url, method: 'GET' })
}
