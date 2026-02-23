/**
 * 邀请系统 API - Sprint 4.7
 */
import request from '@/utils/request'

const PREFIX = '/api/v1/invitation'

// ==================== 邀请码 ====================

/** 获取我的邀请码 */
export function getMyInviteCode() {
  return request<{ invite_code: string }>({
    url: `${PREFIX}/my-code`,
    method: 'GET',
  })
}

/** 邀请统计信息 */
export interface InvitationStats {
  invite_code: string
  total_invited: number
  total_points_earned: number
}

/** 获取邀请统计 */
export function getInvitationStats() {
  return request<InvitationStats>({
    url: `${PREFIX}/stats`,
    method: 'GET',
  })
}

// ==================== 邀请列表 ====================

/** 邀请记录项 */
export interface InvitationItem {
  invitee_id: string
  invitee_name: string
  created_at: string
  points_rewarded: number
}

/** 邀请列表响应 */
export interface InvitationsListResponse {
  invitations: InvitationItem[]
  total: number
}

/** 获取我邀请的用户列表 */
export function getMyInvitations(limit = 50, offset = 0) {
  return request<InvitationsListResponse>({
    url: `${PREFIX}/my-invitations?limit=${limit}&offset=${offset}`,
    method: 'GET',
  })
}

// ==================== 应用邀请码 ====================

/** 应用邀请码响应 */
export interface ApplyInviteCodeResponse {
  success: boolean
  inviter_id: string
  points_earned: number
}

/** 应用邀请码（注册时或个人中心调用） */
export function applyInviteCode(inviteCode: string) {
  return request<ApplyInviteCodeResponse>({
    url: `${PREFIX}/apply`,
    method: 'POST',
    data: { invite_code: inviteCode },
  })
}
