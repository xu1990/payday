/**
 * 小程序码扫码处理工具
 *
 * 小程序扫码后会进入指定页面，并携带 scene 参数（短码）
 * 页面需要调用接口查询原始参数
 */

import { request } from '@/utils/request'

export interface QRCodeMappingResult {
  page: string
  params: Record<string, any>
  scan_count: number
  is_expired: boolean
}

/**
 * 通过短码查询二维码参数映射
 *
 * @param shortCode - 小程序码的 scene 参数（短码）
 * @returns 映射结果，包含页面路径和自定义参数
 */
export async function getQRCodeMapping(shortCode: string): Promise<QRCodeMappingResult> {
  return request<QRCodeMappingResult>({
    url: `/api/v1/qrcode/wxa/mapping/${shortCode}`,
    method: 'GET',
    showLoading: true,
    loadingText: '加载中...'
  })
}

/**
 * 从小程序码 scene 参数中解析并获取原始参数
 *
 * 使用场景：
 * 1. 在 App.vue 的 onLaunch 中检查 scene 参数
 * 2. 在具体页面的 onLoad 中处理跳转逻辑
 *
 * @param scene - 小程序启动参数中的 scene
 * @param options - 额外配置
 * @returns 解析后的参数对象
 */
export async function parseQRCodeScene(
  scene: string,
  options: {
    redirectTo?: boolean  // 是否自动跳转到目标页面
  } = {}
): Promise<QRCodeMappingResult | null> {
  try {
    const result = await getQRCodeMapping(scene)

    // 如果映射已过期
    if (result.is_expired) {
      uni.showToast({
        title: '二维码已过期',
        icon: 'none'
      })
      return null
    }

    // 自动跳转到目标页面（可选）
    if (options.redirectTo && result.page) {
      // 检查是否有目标页面参数（用于绕过微信小程序码限制）
      const targetPage = result.params.targetPage || result.page
      const otherParams = { ...result.params }
      delete otherParams.targetPage  // 移除 targetPage，不需要传递

      // 构建页面参数
      const query = new URLSearchParams(otherParams as any).toString()
      const url = query ? `/${targetPage}?${query}` : `/${targetPage}`

      uni.navigateTo({
        url,
        fail: () => {
          // 如果 navigateTo 失败，尝试 switchTab
          uni.switchTab({
            url: `/${targetPage}`,
            fail: () => {
              console.error('[QRCode] Failed to navigate to:', targetPage)
            }
          })
        }
      })
    }

    return result
  } catch (e) {
    console.error('[QRCode] Failed to parse scene:', e)
    uni.showToast({
      title: '二维码无效',
      icon: 'none'
    })
    return null
  }
}

/**
 * 小程序启动时处理二维码扫码
 *
 * 在 App.vue 的 onLaunch 中调用：
 * ```ts
 * import { handleQRCodeLaunch } from '@/utils/qrcode'
 *
 * onLaunch((options: any) => {
 *   if (options.scene) {
 *     handleQRCodeLaunch(options.scene)
 *   }
 * })
 * ```
 */
export async function handleQRCodeLaunch(scene: string): Promise<void> {
  const result = await parseQRCodeScene(scene, { redirectTo: true })

  if (result) {
    console.log('[QRCode] Successfully navigated to:', result.page, result.params)
  }
}
