/**
 * 存款目标 - Sprint 4.4
 * 与 backend /api/v1/savings-goals 一致
 */
import request from '@/utils/request'

const PREFIX = '/api/v1/savings-goals'

/** 存款目标创建 */
export interface SavingsGoalCreate {
  title: string
  description?: string
  targetAmount: number
  currentAmount?: number
  deadline?: string
  startDate?: string
  category?: string
  icon?: string
}

/** 存款目标响应 */
export interface SavingsGoalResponse {
  id: string
  userId: string
  title: string
  description?: string
  targetAmount: number
  currentAmount: number
  deadline?: string
  startDate?: string
  status: 'active' | 'completed' | 'cancelled' | 'paused'
  category?: string
  icon?: string
  progressPercentage: number
  remainingAmount: number
  createdAt: string
  updatedAt: string
  completedAt?: string
}

/** 目标列表响应 */
export interface SavingsGoalsListResponse {
  goals: SavingsGoalResponse[]
  total: number
}

/** 创建存款目标 */
export function createSavingsGoal(data: SavingsGoalCreate) {
  // Transform camelCase to snake_case for backend
  const snakeCaseData = {
    title: data.title,
    description: data.description,
    target_amount: data.targetAmount,
    current_amount: data.currentAmount ?? 0,
    deadline: data.deadline,
    start_date: data.startDate,
    category: data.category,
    icon: data.icon,
  }
  console.log('[savings.ts] Transformed data:', snakeCaseData)
  return request<SavingsGoalResponse>({
    url: `${PREFIX}`,
    method: 'POST',
    data: snakeCaseData,
  })
}

/** 获取存款目标列表 */
export function getSavingsGoals(status?: string) {
  const url = status ? `${PREFIX}?status=${status}` : `${PREFIX}`
  return request<SavingsGoalsListResponse>({
    url,
    method: 'GET',
  })
}

/** 获取单个存款目标 */
export function getSavingsGoal(goalId: string) {
  return request<SavingsGoalResponse>({
    url: `${PREFIX}/${goalId}`,
    method: 'GET',
  })
}

/** 更新存款目标 */
export interface SavingsGoalUpdate {
  title?: string
  description?: string
  targetAmount?: number
  currentAmount?: number
  deadline?: string
  startDate?: string
  status?: string
  category?: string
  icon?: string
}

export function updateSavingsGoal(goalId: string, data: SavingsGoalUpdate) {
  // Transform camelCase to snake_case for backend
  const snakeCaseData: Record<string, unknown> = {}
  if (data.title !== undefined) snakeCaseData.title = data.title
  if (data.description !== undefined) snakeCaseData.description = data.description
  if (data.targetAmount !== undefined) snakeCaseData.target_amount = data.targetAmount
  if (data.currentAmount !== undefined) snakeCaseData.current_amount = data.currentAmount
  if (data.deadline !== undefined) snakeCaseData.deadline = data.deadline
  if (data.startDate !== undefined) snakeCaseData.start_date = data.startDate
  if (data.status !== undefined) snakeCaseData.status = data.status
  if (data.category !== undefined) snakeCaseData.category = data.category
  if (data.icon !== undefined) snakeCaseData.icon = data.icon

  return request<SavingsGoalResponse>({
    url: `${PREFIX}/${goalId}`,
    method: 'PUT',
    data: snakeCaseData,
  })
}

/** 删除存款目标（软删除） */
export function deleteSavingsGoal(goalId: string) {
  return request<{ deleted: boolean }>({
    url: `${PREFIX}/${goalId}`,
    method: 'DELETE',
  })
}

/** 存款请求 */
export interface SavingsDepositRequest {
  amount: number
  note?: string
}

/** 向目标存入金额 */
export function depositToGoal(goalId: string, data: SavingsDepositRequest) {
  return request<SavingsGoalResponse>({
    url: `${PREFIX}/${goalId}/deposit`,
    method: 'POST',
    data,
  })
}
