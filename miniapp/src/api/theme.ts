/**
 * 主题与设置 - 与 backend /api/v1/themes 一致
 */
import request from '@/utils/request'

const PREFIX = '/api/v1/themes'

/** 主题项 */
export interface ThemeItem {
  id: string
  name: string
  display_name: string
  preview_color: string
  primary_color: string
  is_dark: boolean
}

/** 主题列表响应 */
export interface ThemeListRes {
  items: ThemeItem[]
}

/** 用户设置 */
export interface UserSettings {
  theme_id: string | null
  privacy_profile: number
  allow_stranger_notice: number
  allow_comment: number
}

/** 用户设置更新请求 */
export interface UserSettingsUpdateReq {
  theme_id?: string | null
  privacy_profile?: number
  allow_stranger_notice?: number
  allow_comment?: number
}

/** 获取所有主题 */
export function getThemes() {
  return request<ThemeListRes>({
    url: PREFIX,
    method: 'GET',
  })
}

/** 获取用户设置 */
export function getUserSettings() {
  return request<UserSettings>({
    url: `${PREFIX}/my-settings`,
    method: 'GET',
  })
}

/** 更新用户设置 */
export function updateUserSettings(data: UserSettingsUpdateReq) {
  return request<UserSettings>({
    url: `${PREFIX}/my-settings`,
    method: 'PUT',
    data,
  })
}
