/**
 * 主题配置管理 API
 */
import { request } from '@/utils/request'

const PREFIX = '/api/v1/admin/config/themes'

export interface ThemeItem {
  id: string
  name: string
  code: string
  preview_image: string | null
  config: string | null
  is_premium: boolean
  is_active: boolean
  sort_order: number
  created_at: string
}

export interface ThemeCreate {
  name: string
  code: string
  preview_image?: string | null
  config?: string | null
  is_premium?: boolean
  sort_order?: number
}

export interface ThemeUpdate {
  name?: string
  preview_image?: string | null
  config?: string | null
  is_premium?: boolean
  sort_order?: number
  is_active?: boolean
}

export interface ThemeListResult {
  items: ThemeItem[]
  total: number
}

/** 主题列表 */
export function listThemes(params?: {
  active_only?: boolean
  limit?: number
  offset?: number
}) {
  const { active_only = false, limit = 20, offset = 0 } = params ?? {}
  const q = new URLSearchParams()
  q.set('active_only', String(active_only))
  q.set('limit', String(limit))
  q.set('offset', String(offset))
  return request<ThemeListResult>({
    url: `${PREFIX}?${q.toString()}`,
    method: 'GET',
  })
}

/** 创建主题 */
export function createTheme(data: ThemeCreate) {
  return request<ThemeItem>({
    url: PREFIX,
    method: 'POST',
    data,
  })
}

/** 获取单个主题 */
export function getTheme(themeId: string) {
  return request<ThemeItem>({
    url: `${PREFIX}/${themeId}`,
    method: 'GET',
  })
}

/** 更新主题 */
export function updateTheme(themeId: string, data: ThemeUpdate) {
  return request<ThemeItem>({
    url: `${PREFIX}/${themeId}`,
    method: 'PUT',
    data,
  })
}

/** 删除主题 */
export function deleteTheme(themeId: string) {
  return request<{ deleted: boolean }>({
    url: `${PREFIX}/${themeId}`,
    method: 'DELETE',
  })
}
