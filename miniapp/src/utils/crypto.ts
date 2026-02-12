/**
 * 加密和签名工具（小程序兼容性）
 * 使用 AES-GCM 加密算法提供更强的安全性
 */

/**
 * 生成加密安全的随机字符串
 * SECURITY: 使用 crypto.getRandomValues() 而非 Math.random()
 */
function randomString(length: number): string {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
  const randomValues = new Uint8Array(length)
  crypto.getRandomValues(randomValues)

  let result = ''
  for (let i = 0; i < length; i++) {
    result += chars.charAt(randomValues[i] % chars.length)
  }
  return result
}

/**
 * 获取或生成设备唯一密钥（256位）
 */
async function getDeviceKey(): Promise<CryptoKey> {
  let keyString = uni.getStorageSync('device_key')
  if (!keyString) {
    // 生成新的随机密钥
    keyString = randomString(32)
    uni.setStorageSync('device_key', keyString)
  }

  // 将字符串密钥转换为 CryptoKey
  const encoder = new TextEncoder()
  const keyBuffer = encoder.encode(keyString.padEnd(32, '0').slice(0, 32))

  return await crypto.subtle.importKey(
    'raw',
    keyBuffer,
    { name: 'AES-GCM' },
    false,
    ['encrypt', 'decrypt']
  )
}

/**
 * AES-GCM 加密
 * 用于保护存储在本地的敏感数据（如 token）
 */
export async function encrypt(text: string): Promise<string> {
  try {
    const key = await getDeviceKey()
    const encoder = new TextEncoder()
    const data = encoder.encode(text)

    // 生成随机初始化向量 (IV)
    const iv = crypto.getRandomValues(new Uint8Array(12))

    // 使用 AES-GCM 加密
    const encrypted = await crypto.subtle.encrypt(
      { name: 'AES-GCM', iv },
      key,
      data
    )

    // 合并 IV 和加密数据
    const combined = new Uint8Array(iv.length + encrypted.byteLength)
    combined.set(iv)
    combined.set(new Uint8Array(encrypted), iv.length)

    // Base64 编码
    return uni.arrayBufferToBase64(combined.buffer)
  } catch (error) {
    throw new Error('加密失败')
  }
}

/**
 * AES-GCM 解密
 */
export async function decrypt(encoded: string): Promise<string> {
  try {
    const key = await getDeviceKey()

    // Base64 解码
    const combined = new Uint8Array(uni.base64ToArrayBuffer(encoded))

    // 提取 IV (前12字节) 和加密数据
    const iv = combined.slice(0, 12)
    const encrypted = combined.slice(12)

    // 使用 AES-GCM 解密
    const decrypted = await crypto.subtle.decrypt(
      { name: 'AES-GCM', iv },
      key,
      encrypted
    )

    const decoder = new TextDecoder()
    return decoder.decode(decrypted)
  } catch (error) {
    return ''
  }
}

/**
 * HMAC-SHA256 签名（用于 API 请求签名）
 * @param data 待签名的数据
 * @param secret 密钥
 * @returns 十六进制签名字符串
 */
export async function hmacSha256(data: string, secret: string): Promise<string> {
  // 将字符串转换为 ArrayBuffer
  const encoder = new TextEncoder()
  const dataBuffer = encoder.encode(data)
  const secretBuffer = encoder.encode(secret)

  // 导入密钥
  const key = await crypto.subtle.importKey(
    'raw',
    secretBuffer,
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign']
  )

  // 生成签名
  const signature = await crypto.subtle.sign(
    'HMAC',
    key,
    dataBuffer
  )

  // 转换为十六进制字符串
  const hashArray = Array.from(new Uint8Array(signature))
  const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('')

  return hashHex
}

