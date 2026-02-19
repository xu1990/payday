/**
 * 小程序配置管理 API
 */
import { request } from '@/utils/request'

const PREFIX = '/admin/config/miniprogram'

export interface MiniprogramConfigItem {
  id: string
  key: string
  value: string | null
  description: string | null
  is_active: boolean
  sort_order: number
  created_at: string | null
  updated_at: string | null
}

export interface MiniprogramConfigCreate {
  key: string
  value?: string
  description?: string
  sort_order?: number
}

export interface MiniprogramConfigUpdate {
  value?: string
  description?: string
  is_active?: boolean
  sort_order?: number
}

/**
 * 获取小程序配置列表
 */
export function listConfigs(): Promise<{ data: MiniprogramConfigItem[]; message: string }> {
  return request({ url: PREFIX, method: 'GET' })
}

/**
 * 创建小程序配置
 */
export function createConfig(data: MiniprogramConfigCreate): Promise<{ data: MiniprogramConfigItem; message: string }> {
  return request({ url: PREFIX, method: 'POST', data })
}

/**
 * 更新小程序配置
 */
export function updateConfig(
  configId: string,
  data: MiniprogramConfigUpdate
): Promise<{ data: MiniprogramConfigItem; message: string }> {
  return request({ url: `${PREFIX}/${configId}`, method: 'PUT', data })
}

/**
 * 删除小程序配置
 */
export function deleteConfig(configId: string): Promise<{ data: { deleted: boolean }; message: string }> {
  return request({ url: `${PREFIX}/${configId}`, method: 'DELETE' })
}

export default {
  listConfigs,
  createConfig,
  updateConfig,
  deleteConfig,
}

/**
 * 获取协议内容
 */
export function getAgreements(): Promise<{
  data: {
    user_agreement: string
    privacy_agreement: string
  }
  message: string
}> {
  return request({ url: '/admin/config/agreements', method: 'GET' })
}

/**
 * 更新协议内容
 */
export function updateAgreement(data: {
  type: 'user' | 'privacy'
  content: string
}): Promise<{ message: string }> {
  return request({ url: '/admin/config/agreements', method: 'POST', data })
}

export interface SplashConfigData {
  image_url: string
  content: string
  countdown: number
  is_active: boolean
}

export interface SplashConfigResponse {
  data: SplashConfigData
  message: string
}

/**
 * 获取开屏配置
 */
export function getSplashConfig(): Promise<SplashConfigResponse> {
  return request({ url: '/admin/config/splash', method: 'GET' })
}

/**
 * 更新开屏配置
 */
export function updateSplashConfig(data: SplashConfigData): Promise<{ message: string }> {
  return request({ url: '/admin/config/splash', method: 'POST', data })
}
