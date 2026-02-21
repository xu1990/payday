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

// 全局变量备份，解决真机环境下存储异步导致的问题
let globalTokenBackup: { token: string; refreshToken?: string; userId?: string } | null = null

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
      fail: err => reject(err),
    })
  })
}

/**
 * 同步存储函数（使用 setStorageSync 确保真正同步）
 * 用于关键场景如登录后立即跳转
 */
function setStorageSyncSync(key: string, data: string): boolean {
  try {
    uni.setStorageSync(key, data)
    return true
  } catch (e) {
    console.error(`[tokenStorage] setStorageSync failed for ${key}:`, e)
    return false
  }
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
        success: res => {
          const data = res.data as string
          console.log(`[tokenStorage] getStorage success for ${key}, attempt ${attempt}`)
          resolve(data)
        },
        fail: err => {
          // 如果是未找到数据的错误
          if (err.errMsg && err.errMsg.includes('data not found')) {
            // 如果还有重试次数，延迟后重试
            if (attempt < maxRetries) {
              console.warn(
                `[tokenStorage] getStorage not found for ${key}, retrying (${attempt}/${maxRetries})`
              )
              setTimeout(() => {
                tryGet().then(resolve).catch(reject)
              }, 100 * attempt) // 递增延迟：100ms, 200ms, 300ms
            } else {
              console.warn(
                `[tokenStorage] getStorage not found for ${key} after ${maxRetries} attempts`
              )
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
 * 修复策略（真机环境）：
 * 1. 使用 setStorageSync 确保真正同步写入
 * 2. 同时保存到全局变量作为备份
 * 3. 验证存储成功（多次尝试）
 */
export async function saveToken(
  token: string,
  refreshToken?: string,
  userId?: string
): Promise<void> {
  try {
    console.log('[tokenStorage] Saving token, userId:', userId)

    // 1. 先保存到全局变量（内存备份，始终可靠）
    globalTokenBackup = { token, refreshToken, userId }
    console.log('[tokenStorage] Token saved to global backup')

    // 2. 使用同步存储确保写入
    const tokenSaved = setStorageSyncSync(TOKEN_KEY, token)
    if (!tokenSaved) {
      throw new Error('Token sync storage failed')
    }
    console.log('[tokenStorage] Token saved via setStorageSync')

    if (refreshToken) {
      setStorageSyncSync(REFRESH_TOKEN_KEY, refreshToken)
    }

    if (userId) {
      setStorageSyncSync(USER_ID_KEY, userId)
    }

    // 3. 验证存储成功（使用 getStorageSync 读取）
    let verified = false
    for (let i = 0; i < 5; i++) {
      try {
        const stored = uni.getStorageSync(TOKEN_KEY) as string
        if (stored && stored === token) {
          console.log(`[tokenStorage] Token verified via getStorageSync (attempt ${i + 1}/5)`)
          verified = true
          break
        }
        console.warn(`[tokenStorage] Token verification failed, retrying... (${i + 1}/5)`)
        await new Promise(resolve => setTimeout(resolve, 50))
      } catch (e) {
        console.warn(`[tokenStorage] Token verification error:`, e)
      }
    }

    if (!verified) {
      console.error('[tokenStorage] Token verification failed after 5 attempts')
      throw new Error('Token存储验证失败')
    }

    console.log('[tokenStorage] All tokens saved and verified, userId:', userId)
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
 * 修复策略：
 * 1. 优先从 uni.getStorageSync 读取（同步，快速）
 * 2. 如果失败，尝试从全局变量备份读取
 * 3. 如果都失败，返回空字符串
 */
export async function getToken(): Promise<string> {
  try {
    // 1. 先尝试同步读取
    try {
      const token = uni.getStorageSync(TOKEN_KEY) as string
      if (token && typeof token === 'string' && token.length > 0) {
        console.log('[tokenStorage] Token retrieved via getStorageSync, length:', token.length)
        return token
      }
    } catch (e) {
      console.warn('[tokenStorage] getStorageSync failed:', e)
    }

    // 2. 尝试从全局变量备份读取
    if (globalTokenBackup && globalTokenBackup.token) {
      console.log('[tokenStorage] Token retrieved from global backup')
      // 同时尝试重新写入存储
      try {
        setStorageSyncSync(TOKEN_KEY, globalTokenBackup.token)
        if (globalTokenBackup.refreshToken) {
          setStorageSyncSync(REFRESH_TOKEN_KEY, globalTokenBackup.refreshToken)
        }
        if (globalTokenBackup.userId) {
          setStorageSyncSync(USER_ID_KEY, globalTokenBackup.userId)
        }
        console.log('[tokenStorage] Token restored to storage from backup')
      } catch (restoreError) {
        console.warn('[tokenStorage] Failed to restore token to storage:', restoreError)
      }
      return globalTokenBackup.token
    }

    // 3. 如果都失败，尝试异步读取（最后的机会）
    const token = await getStoragePromise(TOKEN_KEY)
    if (token) {
      console.log('[tokenStorage] Token retrieved via async storage, length:', token.length)
      return token
    }

    console.warn('[tokenStorage] No token found in storage or backup')
    return ''
  } catch (error) {
    console.error('[tokenStorage] Token retrieval failed:', error)

    // 最后的最后，尝试从全局备份读取
    if (globalTokenBackup && globalTokenBackup.token) {
      console.log('[tokenStorage] Token retrieved from global backup as last resort')
      return globalTokenBackup.token
    }

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
      fail: err => reject(err),
    })
  })
}

/**
 * 清除本地存储的 Token
 */
export async function clearToken(): Promise<void> {
  try {
    // 清除全局备份
    globalTokenBackup = null
    console.log('[tokenStorage] Global backup cleared')

    // 清除存储
    await removeStoragePromise(TOKEN_KEY)
    await removeStoragePromise(REFRESH_TOKEN_KEY)
    await removeStoragePromise(USER_ID_KEY)
    console.log('[tokenStorage] Storage cleared')
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
