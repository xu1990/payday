/**
 * 字段名转换工具
 * 将后端的 snake_case 转换为前端的 camelCase
 */

/**
 * 转换单个存款目标对象的字段名
 */
export function transformSavingsGoal(goal: any): any {
  if (!goal) return null
  return {
    ...goal,
    targetAmount: goal.target_amount ?? 0,
    currentAmount: goal.current_amount ?? 0,
    startDate: goal.start_date,
    progressPercentage: goal.progress_percentage ?? 0,
    remainingAmount: goal.remaining_amount ?? 0,
    createdAt: goal.created_at,
    updatedAt: goal.updated_at,
    completedAt: goal.completed_at,
  }
}

/**
 * 转换存款目标数组
 */
export function transformSavingsGoals(goals: any[]): any[] {
  if (!goals) return []
  return goals.map(transformSavingsGoal)
}

/**
 * 安全获取数值，处理 NaN 和 null
 */
export function safeNumber(value: any, defaultValue = 0): number {
  if (value === null || value === undefined || isNaN(value)) {
    return defaultValue
  }
  return parseFloat(value) || defaultValue
}

/**
 * 格式化金额显示
 */
export function formatMoney(amount: any): string {
  const num = safeNumber(amount, 0)
  return num.toFixed(2)
}
