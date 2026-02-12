/**
 * 会员与订单 - 与 backend /api/v1/membership 一致
 */
import request from '@/utils/request'

const PREFIX = '/api/v1/membership'

/** 会员套餐项 */
export interface MembershipItem {
  id: string
  name: string
  description: string | null
  price: number
  duration_days: number
  is_active: boolean
}

/** 会员列表响应 */
export interface MembershipListRes {
  items: MembershipItem[]
}

/** 创建会员订单请求 */
export interface MembershipOrderCreateReq {
  membership_id: string
  amount: number
  payment_method?: string
  transaction_id?: string
}

/** 会员订单项 */
export interface MembershipOrderItem {
  id: string
  membership_id: string
  amount: number
  status: string
  start_date: string
  end_date: string | null
  auto_renew: boolean
  created_at: string
}

/** 会员订单列表响应 */
export interface MembershipOrderListRes {
  items: MembershipOrderItem[]
}

/** 激活的会员信息 */
export interface ActiveMembership {
  id: string
  name: string
  description: string | null
  end_date: string
  days_remaining: number
}

/** 获取所有会员套餐 */
export function getMemberships() {
  return request<MembershipListRes>({
    url: PREFIX,
    method: 'GET',
  })
}

/** 创建会员订单 */
export function createMembershipOrder(data: MembershipOrderCreateReq) {
  return request<{ id: string; status: string; message: string }>({
    url: `${PREFIX}/order`,
    method: 'POST',
    data,
  })
}

/** 获取我的会员订单 */
export function getMyOrders() {
  return request<MembershipOrderListRes>({
    url: `${PREFIX}/my-orders`,
    method: 'GET',
  })
}

/** 获取当前激活的会员 */
export function getActiveMembership() {
  return request<ActiveMembership | {}>({
    url: `${PREFIX}/active`,
    method: 'GET',
  })
}

/** 取消会员订单 */
export function cancelOrder(orderId: string) {
  return request<{ success: boolean; message: string }>({
    url: `${PREFIX}/order/${orderId}/cancel`,
    method: 'POST',
  })
}
