/**
 * 能力值积分状态管理 - Sprint 4.6
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as pointsApi from '@/api/ability-points'
import type {
  AbilityPointResponse,
  PointTransactionResponse,
  PointRedemptionResponse,
} from '@/api/ability-points'

// 积分系统常量
const POINTS_PER_LEVEL = 1000 // 每升1级所需的积分

export const useAbilityPointsStore = defineStore('abilityPoints', () => {
  // 状态
  const points = ref<AbilityPointResponse | null>(null)
  const transactions = ref<PointTransactionResponse[]>([])
  const redemptions = ref<PointRedemptionResponse[]>([])
  const events = ref<pointsApi.PointEvent[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // 计算属性
  const availablePoints = computed(() => points.value?.availablePoints || 0)
  const level = computed(() => points.value?.level || 1)
  const totalPoints = computed(() => points.value?.totalPoints || 0)
  const levelProgress = computed(() => {
    if (!points.value) return 0
    return ((points.value.totalPoints % POINTS_PER_LEVEL) / 10).toFixed(1)
  })
  const nextLevelPoints = computed(() => {
    if (!points.value) return POINTS_PER_LEVEL
    return Math.ceil(points.value.totalPoints / POINTS_PER_LEVEL) * POINTS_PER_LEVEL
  })

  /**
   * 获取我的积分信息
   */
  async function fetchMyPoints() {
    try {
      isLoading.value = true
      error.value = null
      const data = await pointsApi.getMyPoints()
      points.value = data
      return data
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : '获取积分信息失败'
      return null
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 获取积分流水
   */
  async function fetchTransactions(limit = 50, offset = 0) {
    try {
      isLoading.value = true
      error.value = null
      const response = await pointsApi.getMyTransactions(limit, offset)
      transactions.value = response.transactions
      return response.transactions
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : '获取积分流水失败'
      return []
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 获取兑换记录
   */
  async function fetchRedemptions(status?: string) {
    try {
      isLoading.value = true
      error.value = null
      const response = await pointsApi.getMyRedemptions(status)
      redemptions.value = response.redemptions
      return response.redemptions
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : '获取兑换记录失败'
      return []
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 获取积分事件列表
   */
  async function fetchEvents() {
    try {
      isLoading.value = true
      error.value = null
      const response = await pointsApi.getPointEvents()
      events.value = response.events
      return response.events
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : '获取积分事件失败'
      return []
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 创建积分兑换
   */
  async function createRedemption(data: pointsApi.PointRedemptionCreate) {
    try {
      isLoading.value = true
      error.value = null

      // 检查积分是否足够
      if (points.value && data.pointsCost > points.value.availablePoints) {
        throw new Error('积分不足')
      }

      const redemption = await pointsApi.createRedemption(data)

      // 添加到兑换记录
      redemptions.value.unshift(redemption)

      // 刷新积分信息
      await fetchMyPoints()

      return redemption
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : '创建兑换失败'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 触发积分事件（hooks系统）
   */
  function triggerEvent(
    eventType: string,
    points: number,
    referenceId?: string,
    referenceType?: string,
    description?: string
  ) {
    // 本地乐观更新
    if (points.value) {
      points.value.availablePoints += points
      points.value.totalPoints += points
      points.value.totalEarned += points
      points.value.level = 1 + Math.floor(points.value.totalPoints / POINTS_PER_LEVEL)

      // 添加交易记录
      transactions.value.unshift({
        id: `local-${Date.now()}`,
        userId: points.value.userId,
        amount: points,
        balanceAfter: points.value.availablePoints,
        transactionType: 'earn',
        eventType,
        description: description || `${eventType}: +${points}积分`,
        createdAt: new Date().toISOString(),
      })
    }
  }

  /**
   * 清空状态
   */
  function clearState() {
    points.value = null
    transactions.value = []
    redemptions.value = []
    events.value = []
    error.value = null
  }

  return {
    // 状态
    points,
    transactions,
    redemptions,
    events,
    isLoading,
    error,

    // 计算属性
    availablePoints,
    level,
    totalPoints,
    levelProgress,
    nextLevelPoints,

    // 方法
    fetchMyPoints,
    fetchTransactions,
    fetchRedemptions,
    fetchEvents,
    createRedemption,
    triggerEvent,
    clearState,
  }
})
