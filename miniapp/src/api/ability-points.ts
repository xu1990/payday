/**
 * 能力值积分系统 - Sprint 4.6
 * 与 backend /api/v1/ability-points 一致
 */
import request from '@/utils/request'

const PREFIX = '/api/v1/ability-points'

// ==================== 积分账户 ====================

/** 用户积分信息 */
export interface AbilityPointResponse {
  id: string
  userId: string
  totalPoints: number
  availablePoints: number
  level: number
  totalEarned: number
  totalSpent: number
  createdAt: string
  updatedAt: string
}

/** 获取我的积分信息 */
export function getMyPoints() {
  return request<AbilityPointResponse>({
    url: `${PREFIX}/my`,
    method: 'GET',
  }).then(data => {
    // 后端返回 snake_case 字段，映射到 camelCase
    if (data) {
      return {
        ...data,
        availablePoints: data.available_points ?? data.availablePoints,
        totalPoints: data.total_points ?? data.totalPoints,
        totalEarned: data.total_earned ?? data.totalEarned,
        totalSpent: data.total_spent ?? data.totalSpent,
        userId: data.user_id ?? data.userId,
        createdAt: data.created_at ?? data.createdAt,
        updatedAt: data.updated_at ?? data.updatedAt,
      } as AbilityPointResponse
    }
    return data
  })
}

// ==================== 积分流水 ====================

/** 积分流水记录 */
export interface PointTransactionResponse {
  id: string
  userId: string
  amount: number
  balanceAfter: number
  transactionType: string
  eventType?: string
  description?: string
  createdAt: string
}

/** 积分流水利表响应 */
export interface TransactionsListResponse {
  transactions: PointTransactionResponse[]
  total: number
}

/** 获取我的积分流水 */
export function getMyTransactions(limit = 50, offset = 0) {
  return request<TransactionsListResponse>({
    url: `${PREFIX}/my/transactions?limit=${limit}&offset=${offset}`,
    method: 'GET',
  }).then(res => {
    // 后端返回 snake_case 字段，映射到 camelCase
    if (res && res.transactions) {
      return {
        ...res,
        transactions: res.transactions.map((item: any) => ({
          ...item,
          transactionType: item.transaction_type ?? item.transactionType,
          eventType: item.event_type ?? item.eventType,
          createdAt: item.created_at ?? item.createdAt,
          balanceAfter: item.balance_after ?? item.balanceAfter,
          userId: item.user_id ?? item.userId,
        }))
      }
    }
    return res
  })
}

// ==================== 积分兑换 ====================

/** 兑换创建请求 */
export interface PointRedemptionCreate {
  rewardName: string
  rewardType: string
  pointsCost: number
  deliveryInfo?: string
  notes?: string
}

/** 兑换记录响应 */
export interface PointRedemptionResponse {
  id: string
  userId: string
  rewardName: string
  rewardType: string
  pointsCost: number
  status: 'pending' | 'approved' | 'completed' | 'rejected'
  deliveryInfo?: string
  notes?: string
  adminId?: string
  processedAt?: string
  rejectionReason?: string
  createdAt: string
  updatedAt: string
}

/** 兑换列表响应 */
export interface RedemptionsListResponse {
  redemptions: PointRedemptionResponse[]
  total: number
}

/** 创建积分兑换 */
export function createRedemption(data: PointRedemptionCreate) {
  return request<PointRedemptionResponse>({
    url: `${PREFIX}/redemptions`,
    method: 'POST',
    data,
  })
}

/** 获取我的兑换记录 */
export function getMyRedemptions(status?: string) {
  const url = status ? `${PREFIX}/redemptions?status=${status}` : `${PREFIX}/redemptions`
  return request<RedemptionsListResponse>({
    url,
    method: 'GET',
  })
}

// ==================== 积分事件 ====================

/** 积分事件项 */
export interface PointEvent {
  eventType: string
  points: number
}

/** 积分事件列表响应 */
export interface EventsListResponse {
  events: PointEvent[]
  total: number
}

/** 获取积分事件列表 */
export function getPointEvents() {
  return request<EventsListResponse>({
    url: `${PREFIX}/events`,
    method: 'GET',
  })
}
