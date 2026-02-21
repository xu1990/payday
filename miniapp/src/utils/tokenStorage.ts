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
 *
 * 真机环境修复策略：
 * 完全依赖 uni.getStorageSync 和 uni.setStorageSync
 * - 模块级变量不跨页面共享（真机环境每个页面有新的模块实例）
 * - getApp() 可能返回 null 或不同实例
 * - 只有 uni.storage 是可靠跨页面共享的
 */

const TOKEN_KEY = 'payday_token'
const REFRESH_TOKEN_KEY = 'payday_refresh_token'
const USER_ID_KEY = 'payday_user_id'
const TIMESTAMP_KEY = 'payday_token_timestamp'

// 存储读写锁，防止并发操作导致数据损坏
let isWriting = false
let writeQueue: Array<() => void> = []
let readCount = 0
let readQueue: Array<() => void> = []

/**
 * 等待写入锁释放
 */
function waitForWriteLock(): Promise<void> {
  return new Promise(resolve => {
    if (!isWriting && readCount === 0) {
      resolve()
    } else {
      writeQueue.push(resolve)
    }
  })
}

/**
 * 获取读锁（允许多个并发读取，但写入独占）
 */
function acquireReadLock(): Promise<void> {
  return new Promise(resolve => {
    if (!isWriting) {
      readCount++
      resolve()
    } else {
      readQueue.push(resolve)
    }
  })
}

/**
 * 释放读锁
 */
function releaseReadLock() {
  readCount--
  if (readCount === 0 && writeQueue.length > 0) {
    // 没有读者了，唤醒一个写入者
    const next = writeQueue.shift()
    if (next) {
      isWriting = true
      next()
    }
  }
}

/**
 * 释放写入锁
 */
function releaseWriteLock() {
  isWriting = false
  // 优先唤醒等待的写入者
  if (writeQueue.length > 0) {
    const next = writeQueue.shift()
    isWriting = true
    next()
  } else {
    // 没有写入者，唤醒所有等待的读者
    while (readQueue.length > 0) {
      const next = readQueue.shift()
      readCount++
      next()
    }
  }
}

/**
 * Promise 封装的读取函数（带重试机制）
 *
 * 真机环境下，存储操作可能需要一点时间才能完成
 * 添加重试机制确保能读取到刚写入的数据
 * 修复：验证返回的数据非空，防止空字符串被当作有效数据
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
          // 验证数据非空
          if (data && typeof data === 'string' && data.length > 0) {
            console.log(`[tokenStorage] getStorage success for ${key}, attempt ${attempt}, length: ${data.length}`)
            resolve(data)
          } else {
            // 数据为空，当作失败处理
            console.warn(`[tokenStorage] getStorage returned empty data for ${key}, attempt ${attempt}`)
            if (attempt < maxRetries) {
              setTimeout(() => {
                tryGet().then(resolve).catch(reject)
              }, 100 * attempt)
            } else {
              console.warn(`[tokenStorage] getStorage returned empty data after ${maxRetries} attempts`)
              resolve('')
            }
          }
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
 * 真机环境修复策略：
 * 1. 使用写入锁防止并发写入
 * 2. 使用 uni.setStorageSync 同步存储（确保写入完成）
 * 3. 保存时间戳用于 grace period 检查
 * 4. 简单验证：立即读取确认存储成功
 */
export async function saveToken(
  token: string,
  refreshToken?: string,
  userId?: string
): Promise<void> {
  try {
    // 验证 token 参数
    if (!token || typeof token !== 'string') {
      throw new Error(`Invalid token parameter: expected non-empty string, got ${typeof token}`)
    }

    console.log('[tokenStorage] Saving token, userId:', userId, 'token length:', token.length)

    // 等待其他写入完成
    await waitForWriteLock()
    isWriting = true

    const timestamp = Date.now()

    try {
      // 使用 setStorageSync 确保同步写入
      uni.setStorageSync(TOKEN_KEY, token)
      console.log('[tokenStorage] Token saved via setStorageSync, length:', token.length)

      if (refreshToken) {
        uni.setStorageSync(REFRESH_TOKEN_KEY, refreshToken)
      }

      if (userId) {
        uni.setStorageSync(USER_ID_KEY, userId)
      }

      // 保存时间戳用于 grace period
      uni.setStorageSync(TIMESTAMP_KEY, timestamp.toString())

      // 真机环境下 setStorageSync 不是真正同步，需要等待存储真正持久化
      await new Promise(resolve => setTimeout(resolve, 200))

      // 验证：读取确认（带重试）
      let verified = false
      for (let attempt = 1; attempt <= 3; attempt++) {
        const savedToken = uni.getStorageSync(TOKEN_KEY) as string
        console.log(`[tokenStorage] Verification attempt ${attempt}:`,
          savedToken ? `GOT TOKEN (length: ${savedToken.length})` : 'NO TOKEN')

        if (savedToken && savedToken === token) {
          console.log('[tokenStorage] Token verified successfully on attempt', attempt)
          verified = true
          break
        }

        if (attempt < 3) {
          await new Promise(resolve => setTimeout(resolve, 100))
        }
      }

      if (!verified) {
        console.error('[tokenStorage] Token verification failed after 3 attempts')
        // 不抛出错误，因为数据可能已经写入，只是读取有延迟
      }

      console.log('[tokenStorage] All tokens saved, userId:', userId)

    } catch (e) {
      console.error('[tokenStorage] Storage operation failed:', e)
      throw e
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
  } finally {
    // 释放写入锁
    releaseWriteLock()
  }
}

/**
 * 获取本地存储的 Token
 *
 * 真机环境修复策略：
 * 1. 使用读锁，等待写入完成
 * 2. 直接从 uni.getStorageSync 读取（同步，可靠）
 * 3. 如果同步读取失败，尝试异步读取（带重试）
 * 4. 不使用任何全局变量或内存缓存
 */
export async function getToken(): Promise<string> {
  try {
    // 等待写入完成，获取读锁
    await acquireReadLock()

    try {
      // 1. 尝试同步读取存储（最可靠）
      try {
        const token = uni.getStorageSync(TOKEN_KEY) as string
        if (token && typeof token === 'string' && token.length > 0) {
          console.log('[tokenStorage] Token retrieved via getStorageSync, length:', token.length)
          return token
        }
      } catch (e) {
        console.warn('[tokenStorage] getStorageSync failed:', e)
      }

      // 2. 如果同步读取失败，尝试异步读取（带重试）
      const token = await getStoragePromise(TOKEN_KEY)
      if (token) {
        console.log('[tokenStorage] Token retrieved via async storage, length:', token.length)
        return token
      }

      console.warn('[tokenStorage] No token found in storage')
      return ''
    } finally {
      // 释放读锁
      releaseReadLock()
    }
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
      fail: err => reject(err),
    })
  })
}

/**
 * 清除本地存储的 Token
 */
export async function clearToken(): Promise<void> {
  try {
    // 清除存储
    await removeStoragePromise(TOKEN_KEY)
    await removeStoragePromise(REFRESH_TOKEN_KEY)
    await removeStoragePromise(USER_ID_KEY)
    await removeStoragePromise(TIMESTAMP_KEY)
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

/**
 * 获取最近一次保存 token 的时间戳
 * 用于 grace period 检查，防止登录后立即刷新 token
 */
export function getLastTokenSaveTime(): number {
  try {
    const timestamp = uni.getStorageSync(TIMESTAMP_KEY) as string
    return timestamp ? parseInt(timestamp, 10) : 0
  } catch (e) {
    console.warn('[tokenStorage] Failed to get timestamp:', e)
    return 0
  }
}

// 移除默认导出以避免小程序环境下的动态导入问题
// 所有导出都使用命名导出 (named exports)
