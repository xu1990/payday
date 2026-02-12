/**
 * 状态常量
 * 集中管理所有状态相关的常量
 */

/** 订单状态映射 */
export const ORDER_STATUS_MAP = {
  pending: { text: '待支付', type: 'info' as const },
  paid: { text: '已支付', type: 'success' as const },
  cancelled: { text: '已取消', type: 'info' as const },
  refunded: { text: '已退款', type: 'danger' as const },
} as const

/** 帖子状态映射 */
export const POST_STATUS_MAP = {
  normal: { text: '正常', type: 'success' as const },
  hidden: { text: '隐藏', type: 'info' as const },
  deleted: { text: '已删除', type: 'danger' as const },
} as const

/** 风控状态映射 */
export const RISK_STATUS_MAP = {
  pending: { text: '待审核', type: 'warning' as const },
  approved: { text: '已通过', type: 'success' as const },
  rejected: { text: '已拒绝', type: 'danger' as const },
} as const

/** 用户状态映射 */
export const USER_STATUS_MAP = {
  normal: { text: '正常', type: 'success' as const },
  disabled: { text: '已禁用', type: 'danger' as const },
  deleted: { text: '已删除', type: 'info' as const },
} as const
