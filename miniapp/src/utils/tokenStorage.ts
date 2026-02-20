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
 * Promise 封装的存储函数
 * 解决真机环境下 setStorageSync 不是真正同步的问题
 */
function setStoragePromise(key: string, data: string): Promise<void> {
  return new Promise((resolve, reject) => {
    uni.setStorage({
      key,
      data,
      success: () => resolve(),
      fail: (err) => reject(err),
    })
  })
}

/**
 * Promise 封装的读取函数（带重试机制）
 *
 * 真机环境下，存储操作可能需要一点时间才能完成
 * 添加重试机制确保能读取到刚写入的数据
 */
function getStoragePromise(key: string, maxRetries: number = 3): Promise<string> {
  let attempt = 0

  async function tryGet(): Promise<string> {
    attempt++
    return new Promise((resolve, reject) => {
      uni.getStorage({
        key,
        success: (res) => {
          const data = res.data as string
          console.log(`[tokenStorage] getStorage success for ${key}, attempt ${attempt}`)
          resolve(data)
        },
        fail: (err) => {
          // 如果是未找到数据的错误
          if (err.errMsg && err.errMsg.includes('data not found')) {
            // 如果还有重试次数，延迟后重试
            if (attempt < maxRetries) {
              console.warn(`[tokenStorage] getStorage not found for ${key}, retrying (${attempt}/${maxRetries})`)
              setTimeout(() => {
                tryGet().then(resolve).catch(reject)
              }, 100 * attempt) // 递增延迟：100ms, 200ms, 300ms
            } else {
              console.warn(`[tokenStorage] getStorage not found for ${key} after ${maxRetries} attempts`)
              resolve('')
            }
          } else {
            reject(err)
          }
        },
      })
    })
  }

  return tryGet()
}

/**
 * 保存 Token 到本地存储
 *
 * 修复：使用 Promise 封装的异步存储，确保存储完成后才返回
 * 解决真机调试时 token 未及时写入导致后续请求 401 的问题
 */
export async function saveToken(
  token: string,
  refreshToken?: string,
  userId?: string
): Promise<void> {
  try {
    console.log('[tokenStorage] Saving token, userId:', userId)

    // 使用异步存储并等待完成
    await setStoragePromise(TOKEN_KEY, token)
    console.log('[tokenStorage] Token saved successfully')

    if (refreshToken) {
      await setStoragePromise(REFRESH_TOKEN_KEY, refreshToken)
    }

    if (userId) {
      await setStoragePromise(USER_ID_KEY, userId)
    }

    console.log('[tokenStorage] All tokens saved, userId:', userId)
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
 *
 * 修复：使用 Promise 封装的异步读取，解决真机环境下读取不到刚写入的 token 的问题
 */
export async function getToken(): Promise<string> {
  try {
    const token = await getStoragePromise(TOKEN_KEY)
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
    const token = await getStoragePromise(REFRESH_TOKEN_KEY)
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
export async function getUserId(): Promise<string> {
  try {
    const userId = await getStoragePromise(USER_ID_KEY)
    return userId || ''
  } catch (error) {
    console.error('[tokenStorage] User ID retrieval failed:', error)
    return ''
  }
}

/**
 * Promise 封装的移除函数
 */
function removeStoragePromise(key: string): Promise<void> {
  return new Promise((resolve, reject) => {
    uni.removeStorage({
      key,
      success: () => resolve(),
      fail: (err) => reject(err),
    })
  })
}

/**
 * 清除本地存储的 Token
 */
export async function clearToken(): Promise<void> {
  try {
    await removeStoragePromise(TOKEN_KEY)
    await removeStoragePromise(REFRESH_TOKEN_KEY)
    await removeStoragePromise(USER_ID_KEY)
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
