/**
 * 简单的 XOR 加密工具（小程序兼容性）
 */

/**
 * 生成随机字符串
 */
function randomString(length: number): string {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
  let result = ''
  for (let i = 0; i < length; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length))
  }
  return result
}

/**
 * 获取或生成设备唯一密钥
 */
function getDeviceKey(): string {
  let key = uni.getStorageSync('device_key')
  if (!key) {
    key = randomString(32)
    uni.setStorageSync('device_key', key)
  }
  return key
}

/**
 * 简单 XOR 加密
 * 注意：生产环境建议使用更强大的加密方案
 */
export function encrypt(text: string): string {
  const key = getDeviceKey()
  let result = ''
  for (let i = 0; i < text.length; i++) {
    result += String.fromCharCode(text.charCodeAt(i) ^ key.charCodeAt(i % key.length))
  }
  // Base64 编码
  const base64 = uni.arrayBufferToBase64(new TextEncoder().encode(result).buffer)
  return base64
}

/**
 * 解密
 */
export function decrypt(encoded: string): string {
  try {
    const key = getDeviceKey()
    // Base64 解码
    const buffer = uni.base64ToArrayBuffer(encoded)
    const text = new TextDecoder().decode(new Uint8Array(buffer))
    let result = ''
    for (let i = 0; i < text.length; i++) {
      result += String.fromCharCode(text.charCodeAt(i) ^ key.charCodeAt(i % key.length))
    }
    return result
  } catch {
    return ''
  }
}
