/**
 * 二维码相关 API
 */
import { request } from '@/utils/request'

/**
 * 查询二维码参数映射
 * 通过短码查询原始参数（用于扫描小程序码后的参数恢复）
 */
export function getQRCodeMapping(shortCode: string) {
  return request<{
    page: string
    params: Record<string, any>
    scan_count: number
    is_expired: boolean
  }>({
    url: `/api/v1/qrcode/wxa/mapping/${shortCode}`,
    method: 'GET',
    noAuth: true, // 二维码扫描时用户可能还未登录
  })
}
