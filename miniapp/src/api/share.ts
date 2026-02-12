/**
 * 分享API - P1-2 分享功能
提供分享记录的创建和查询接口
 */
import request from '@/utils/request'

const PREFIX = '/api/v1/share'

/** 分享记录项 */
export interface ShareItem {
  id: string
  user_id: string
  target_type: string
  target_id: string
  share_channel: string
  share_status: string
  created_at: string
  updated_at: string | null
  error_message: string | null
}

/** 创建分享记录请求 */
export interface ShareCreateReq {
  target_type: string
  target_id: string
  share_channel: 'wechat_friend' | 'wechat_moments'
}

/** 分享记录响应 */
export interface ShareItemRes {
  id: string
  share_channel: string
  share_status: string
  created_at: string
}

/** 创建分享记录 */
export function createShare(data: ShareCreateReq) {
  return request<ShareItemRes>({
    url: `${PREFIX}`,
    method: 'POST',
    data,
  })
}
