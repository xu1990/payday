/**
 * Token 存储管理
 *
 * 独立的 token 存储模块，避免循环依赖
 * 负责 token 的存储、读取、清除
 *
 * SECURITY: 小程序环境下直接存储 token
 * - 小程序提供存储隔离，其他小程序无法直接读取
 * - HTTPS 传输保护了数据安全
 * - JWT 签名由后端验证，不需要客户端加密
 */

const TOKEN_KEY = 'payday_token'
const REFRESH_TOKEN_KEY = 'payday_refresh_token'
const USER_ID_KEY = 'payday_user_id'

/**
 * 保存 Token 到本地存储
 */
export async function saveToken(
  token: string,
  refreshToken?: string,
  userId?: string
): Promise<void> {
  try {
    console.log('[tokenStorage] Saving token, userId:', userId)
    // 直接存储 token（小程序环境有存储隔离）
    uni.setStorageSync(TOKEN_KEY, token)
    console.log('[tokenStorage] Token saved successfully')

    if (refreshToken) {
      uni.setStorageSync(REFRESH_TOKEN_KEY, refreshToken)
    }

    if (userId) {
      uni.setStorageSync(USER_ID_KEY, userId)
    }
  } catch (e) {
    // 存储失败处理
    const errorMsg = e instanceof Error ? e.message : String(e)

    if (errorMsg.includes('quota') || errorMsg.includes('storage')) {
      uni.showModal({
        title: '存储失败',
        content: '存储空间不足，请清理缓存后重试',
        showCancel: false,
      })
    } else if (errorMsg.includes('access') || errorMsg.includes('permission')) {
      uni.showModal({
        title: '存储失败',
        content: '存储权限被禁用，请在设置中允许后重试',
        showCancel: false,
      })
    } else {
      uni.showModal({
        title: '存储失败',
        content: '无法保存登录信息，请检查设置',
        showCancel: false,
      })
    }

    console.error('[tokenStorage] Token save failed:', e)
    throw e
  }
}

/**
 * 获取本地存储的 Token
 */
export async function getToken(): Promise<string> {
  try {
    const token = uni.getStorageSync(TOKEN_KEY)
    if (!token) {
      console.warn('[tokenStorage] No token found in storage')
      return ''
    }
    console.log('[tokenStorage] Token retrieved successfully, length:', token.length)
    return token
  } catch (error) {
    console.error('[tokenStorage] Token retrieval failed:', error)
    return ''
  }
}

/**
 * 获取本地存储的 Refresh Token
 */
export async function getRefreshToken(): Promise<string> {
  try {
    const token = uni.getStorageSync(REFRESH_TOKEN_KEY)
    if (!token) {
      console.warn('[tokenStorage] No refresh token found in storage')
      return ''
    }
    return token
  } catch (error) {
    console.error('[tokenStorage] Refresh token retrieval failed:', error)
    return ''
  }
}

/**
 * 获取本地存储的 User ID
 */
export function getUserId(): string {
  try {
    return uni.getStorageSync(USER_ID_KEY) || ''
  } catch (error) {
    console.error('[tokenStorage] User ID retrieval failed:', error)
    return ''
  }
}

/**
 * 清除本地存储的 Token
 */
export function clearToken(): void {
  try {
    uni.removeStorageSync(TOKEN_KEY)
    uni.removeStorageSync(REFRESH_TOKEN_KEY)
    uni.removeStorageSync(USER_ID_KEY)
  } catch (e) {
    console.error('[tokenStorage] Token clear failed:', e)
  }
}

/**
 * 检查是否已登录
 */
export async function isLoggedIn(): Promise<boolean> {
  const token = await getToken()
  return !!token
}

export default {
  saveToken,
  getToken,
  getRefreshToken,
  getUserId,
  clearToken,
  isLoggedIn,
}
