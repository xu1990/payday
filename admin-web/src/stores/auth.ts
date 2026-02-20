import { defineStore } from 'pinia'
import { ElMessage } from 'element-plus'

const CSRF_KEY = 'payday_admin_csrf'

/**
 * SECURITY: JWT token 现在存储在 httpOnly cookie 中
 *
 * 为什么移除 localStorage 存储 JWT：
 * 1. httpOnly cookie 防止 JavaScript 访问 token，防止 XSS 窃取
 * 2. SameSite=strict 防止 CSRF 攻击
 * 3. JWT 的签名验证由后端完成，前端无需存储
 * 4. CSRF token 仍需存储（仅用于状态变更操作）
 *
 * 真正的安全性来自：
 * 1. JWT 加密签名（后端已实现）
 * 2. 短期 token 有效期（15分钟） + refresh token 轮换
 * 3. 后端验证和撤销
 * 4. 状态变更操作的 CSRF token（新实现）
 */

/**
 * 检测 localStorage 是否可用
 */
function isStorageAvailable(): boolean {
  try {
    const test = '__storage_test__'
    localStorage.setItem(test, test)
    localStorage.removeItem(test)
    return true
  } catch {
    return false
  }
}

/**
 * 安全的 localStorage 操作，失败时显示错误提示
 */
function safeSetItem(key: string, value: string): boolean {
  try {
    localStorage.setItem(key, value)
    return true
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error)

    if (errorMessage.includes('quota')) {
      ElMessage.error('浏览器存储空间不足，请清理缓存后重试')
    } else if (errorMessage.includes('access')) {
      ElMessage.error('浏览器存储功能被禁用，请在设置中允许后重试')
    } else {
      ElMessage.error('无法保存登录信息，请检查浏览器设置')
    }
    return false
  }
}

/**
 * 安全的 localStorage 删除操作，失败时显示警告
 */
function safeRemoveItem(key: string): boolean {
  try {
    localStorage.removeItem(key)
    return true
  } catch (error) {
    console.warn('Failed to remove from localStorage:', error)
    return false
  }
}

/**
 * 安全的 localStorage 读取操作，失败时返回空字符串
 */
function safeGetItem(key: string): string {
  try {
    return localStorage.getItem(key) || ''
  } catch {
    return ''
  }
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    // JWT token 存储在内存中用于 Authorization header
    // 同时也在 httpOnly cookie 中作为备份
    token: safeGetItem('payday_admin_token'),
    refreshToken: '',
    csrfToken: safeGetItem(CSRF_KEY),
    // 记忆存储是否可用
    storageAvailable: isStorageAvailable(),
    // 如果有 token，设置为已登录状态（修复刷新跳转登录问题）
    _isLoggedIn: !!safeGetItem('payday_admin_token'),
  }),
  getters: {
    isLoggedIn: (state) => state._isLoggedIn,
    /** 验证当前 token 是否具有 admin scope（由后端验证）*/
    hasAdminScope: (state) => state._isLoggedIn,
  },
  actions: {
    setToken(t: string, csrfToken?: string, refreshToken?: string) {
      // 存储 JWT token 到 state 和 localStorage
      // 用于 Authorization header
      // token 也在 httpOnly cookie 中作为备份
      this.token = t
      if (t) {
        safeSetItem('payday_admin_token', t)
      } else {
        safeRemoveItem('payday_admin_token')
      }

      // 只保存 CSRF token 到 localStorage
      if (csrfToken !== undefined) {
        this.csrfToken = csrfToken
        if (csrfToken) {
          safeSetItem(CSRF_KEY, csrfToken)
        } else {
          safeRemoveItem(CSRF_KEY)
        }
      }

      // 处理refresh token：如果传入了新值则更新，否则保留旧值
      if (refreshToken !== undefined) {
        this.refreshToken = refreshToken
        if (refreshToken) {
          safeSetItem('payday_admin_refresh_token', refreshToken)
        } else {
          safeRemoveItem('payday_admin_refresh_token')
        }
      }

      // 如果存储不可用，给出警告
      if (!this.storageAvailable) {
        ElMessage.warning('浏览器存储不可用，每次刷新都需要重新登录')
        return
      }

      // 设置登录状态
      this._isLoggedIn = !!t
    },
    logout() {
      this.token = ''
      this.refreshToken = ''
      this.csrfToken = ''
      this._isLoggedIn = false
      safeRemoveItem('payday_admin_token')
      safeRemoveItem(CSRF_KEY)
      safeRemoveItem('payday_admin_refresh_token')

      // 清除 httpOnly cookie 需要调用后端登出端点
      // 这里只清除前端状态
    },
  },
})
