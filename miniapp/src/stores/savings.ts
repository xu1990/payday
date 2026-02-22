/**
 * 存款目标状态管理 - Sprint 4.4
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as savingsApi from '@/api/savings'
import type { SavingsGoalResponse } from '@/api/savings'

export const useSavingsStore = defineStore('savings', () => {
  // 状态
  const goals = ref<SavingsGoalResponse[]>([])
  const currentGoal = ref<SavingsGoalResponse | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // 计算属性
  const activeGoals = computed(() =>
    goals.value.filter(g => g.status === 'active')
  )

  const completedGoals = computed(() =>
    goals.value.filter(g => g.status === 'completed')
  )

  const totalSaved = computed(() =>
    goals.value.reduce((sum, g) => sum + g.currentAmount, 0)
  )

  const totalTarget = computed(() =>
    goals.value.reduce((sum, g) => sum + g.targetAmount, 0)
  )

  /**
   * 获取存款目标列表
   */
  async function fetchGoals(status?: string) {
    try {
      isLoading.value = true
      error.value = null
      const response = await savingsApi.getSavingsGoals(status)
      goals.value = response.goals
      return response.goals
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : '获取存款目标失败'
      return []
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 获取单个存款目标
   */
  async function fetchGoal(goalId: string) {
    try {
      isLoading.value = true
      error.value = null
      const goal = await savingsApi.getSavingsGoal(goalId)
      currentGoal.value = goal
      return goal
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : '获取存款目标失败'
      return null
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 创建存款目标
   */
  async function createGoal(data: savingsApi.SavingsGoalCreate) {
    try {
      isLoading.value = true
      error.value = null
      const goal = await savingsApi.createSavingsGoal(data)
      goals.value.unshift(goal)
      return goal
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : '创建存款目标失败'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 更新存款目标
   */
  async function updateGoal(goalId: string, data: savingsApi.SavingsGoalUpdate) {
    try {
      isLoading.value = true
      error.value = null
      const goal = await savingsApi.updateSavingsGoal(goalId, data)

      // 更新列表中的目标
      const index = goals.value.findIndex(g => g.id === goalId)
      if (index !== -1) {
        goals.value[index] = goal
      }

      // 更新当前目标
      if (currentGoal.value?.id === goalId) {
        currentGoal.value = goal
      }

      return goal
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : '更新存款目标失败'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 删除存款目标
   */
  async function deleteGoal(goalId: string) {
    try {
      isLoading.value = true
      error.value = null
      await savingsApi.deleteSavingsGoal(goalId)

      // 从列表中移除
      goals.value = goals.value.filter(g => g.id !== goalId)

      // 清除当前目标
      if (currentGoal.value?.id === goalId) {
        currentGoal.value = null
      }

      return true
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : '删除存款目标失败'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 向目标存入资金
   */
  async function depositToGoal(goalId: string, amount: number, note?: string) {
    try {
      isLoading.value = true
      error.value = null
      const goal = await savingsApi.depositToGoal(goalId, { amount, note })

      // 更新列表中的目标
      const index = goals.value.findIndex(g => g.id === goalId)
      if (index !== -1) {
        goals.value[index] = goal
      }

      // 更新当前目标
      if (currentGoal.value?.id === goalId) {
        currentGoal.value = goal
      }

      return goal
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : '存入资金失败'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 清空状态
   */
  function clearGoals() {
    goals.value = []
    currentGoal.value = null
    error.value = null
  }

  return {
    // 状态
    goals,
    currentGoal,
    isLoading,
    error,

    // 计算属性
    activeGoals,
    completedGoals,
    totalSaved,
    totalTarget,

    // 方法
    fetchGoals,
    fetchGoal,
    createGoal,
    updateGoal,
    deleteGoal,
    depositToGoal,
    clearGoals,
  }
})
