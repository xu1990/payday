/**
 * 支出记录 - Sprint 4.2
 * 与 backend /api/v1/salary/{recordId}/expenses 一致
 */
import request from '@/utils/request'

const PREFIX = '/api/v1/salary'

/** 支出记录创建项 */
export interface ExpenseRecordCreate {
  expenseDate: string
  category: string
  subcategory?: string
  amount: number
  note?: string
}

/** 支出记录响应 */
export interface ExpenseRecordResponse {
  id: string
  salaryRecordId: string
  expenseDate: string
  category: string
  subcategory?: string
  amount: number
  note?: string
  createdAt: string
}

/** 批量创建请求 */
export interface ExpenseListCreate {
  expenses: ExpenseRecordCreate[]
}

/** 创建支出记录响应 */
export interface ExpenseListResponse {
  records: ExpenseRecordResponse[]
  total: number
}

/** 创建支出记录 */
export function createExpenses(recordId: string, data: ExpenseListCreate) {
  return request<ExpenseListResponse>({
    url: `${PREFIX}/${recordId}/expenses`,
    method: 'POST',
    data,
  })
}

/** 获取支出记录 */
export function getExpenses(recordId: string) {
  return request<ExpenseListResponse>({
    url: `${PREFIX}/${recordId}/expenses`,
    method: 'GET',
  })
}
