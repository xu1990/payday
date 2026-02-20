/**
 * 通知 - 与 backend /api/v1/notifications 一致
 */
import request from '@/utils/request'

const PREFIX = '/api/v1/notifications'

export interface NotificationItem {
  id: string
  user_id: string
  type: string
  title: string
  content: string | null
  related_id: string | null
  is_read: boolean
  created_at: string
}

export interface NotificationListResult {
  items: NotificationItem[]
  total: number
  unread_count: number
}

/** 通知列表（分页），含 total、unread_count */
export function getNotificationList(params?: {
  unread_only?: boolean
  type_filter?: string
  limit?: number
  offset?: number
}) {
  const { unread_only, type_filter, limit = 20, offset = 0 } = params ?? {}
  const queryParts: string[] = []
  if (unread_only !== undefined) queryParts.push(`unread_only=${encodeURIComponent(String(unread_only))}`)
  if (type_filter !== undefined) queryParts.push(`type_filter=${encodeURIComponent(type_filter)}`)
  queryParts.push(`limit=${encodeURIComponent(limit)}`)
  queryParts.push(`offset=${encodeURIComponent(offset)}`)
  const q = queryParts.join('&')
  return request<NotificationListResult>({
    url: `${PREFIX}?${q}`,
    method: 'GET',
  })
}

/** 未读数量 */
export function getUnreadCount() {
  return request<{ unread_count: number }>({
    url: `${PREFIX}/unread_count`,
    method: 'GET',
  })
}

/** 标记已读：传 notification_ids 为部分，传 all: true 为全部 */
export function markRead(body: { notification_ids?: string[]; all?: boolean }) {
  return request<{ updated: number }>({
    url: `${PREFIX}/read`,
    method: 'PUT',
    data: body,
  })
}

/** 单条标记已读 */
export function markOneRead(notificationId: string) {
  return request<{ updated: number }>({
    url: `${PREFIX}/${notificationId}/read`,
    method: 'PUT',
  })
}

/** 删除通知：可指定ID列表或全部删除 */
export function deleteNotifications(params?: {
  notification_ids?: string[]
  delete_all?: boolean
}) {
  const { notification_ids, delete_all = false } = params ?? {}
  const queryParts: string[] = []
  if (notification_ids?.length) {
    queryParts.push(`notification_ids=${encodeURIComponent(notification_ids.join(','))}`)
  }
  if (delete_all) {
    queryParts.push('delete_all=true')
  }
  const q = queryParts.join('&')
  return request<{ deleted: number }>({
    url: q ? `${PREFIX}?${q}` : PREFIX,
    method: 'DELETE',
  })
}
