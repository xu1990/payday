/**
 * E2E 测试共享实例模块
 * 提供 miniProgram 全局单例
 * 使用文件系统锁确保只初始化一次
 */
import { Automator } from '@dcloudio/uni-automator'
import { writeFileSync, readFileSync, existsSync, unlinkSync } from 'fs'
import { join } from 'path'

const LOCK_FILE = join(process.cwd(), '.tmp', 'e2e-lock.json')
const LOCK_TIMEOUT = 120000 // 2 minutes

interface LockData {
  pid: number
  port: number
  timestamp: number
}

let globalMiniProgram: any = null
let isInitializing = false

// 确保锁目录存在
function ensureLockDir() {
  const dir = join(process.cwd(), '.tmp')
  if (!existsSync(dir)) {
    const fs = require('fs')
    fs.mkdirSync(dir, { recursive: true })
  }
}

// 检查锁文件
function checkLock(): LockData | null {
  try {
    if (existsSync(LOCK_FILE)) {
      const data = JSON.parse(readFileSync(LOCK_FILE, 'utf-8')) as LockData
      // 检查锁是否过期
      if (Date.now() - data.timestamp < LOCK_TIMEOUT) {
        return data
      }
      // 锁过期，清理
      try { unlinkSync(LOCK_FILE) } catch {}
    }
  } catch {}
  return null
}

// 创建锁
function createLock(port: number): void {
  ensureLockDir()
  const data: LockData = {
    pid: process.pid,
    port,
    timestamp: Date.now()
  }
  writeFileSync(LOCK_FILE, JSON.stringify(data))
}

// 释放锁
function releaseLock(): void {
  try {
    if (existsSync(LOCK_FILE)) {
      const data = JSON.parse(readFileSync(LOCK_FILE, 'utf-8')) as LockData
      // 只有锁的创建者才能释放
      if (data.pid === process.pid) {
        unlinkSync(LOCK_FILE)
      }
    }
  } catch {}
}

export async function initMiniProgram(): Promise<any> {
  // 检查是否已有进程在运行
  const lock = checkLock()
  if (lock && lock.pid !== process.pid) {
    console.log(`检测到其他测试进程 (PID: ${lock.pid}) 已在运行，等待...`)
    // 等待一段时间让其他进程完成
    await new Promise(resolve => setTimeout(resolve, 3000))
    // 递归重试
    return initMiniProgram()
  }

  // 如果已经初始化，直接返回
  if (globalMiniProgram) {
    console.log('使用已存在的微信开发者工具实例')
    return globalMiniProgram
  }

  // 如果正在初始化，等待完成
  if (isInitializing) {
    console.log('等待微信开发者工具初始化...')
    await new Promise(resolve => setTimeout(resolve, 1000))
    return initMiniProgram()
  }

  isInitializing = true

  try {
    console.log('正在启动微信开发者工具...')

    const executablePath =
      process.env.WECHAT_DEVTOOLS_PATH || '/Applications/wechatwebdevtools.app/Contents/MacOS/cli'

    const automator = new Automator()
    const instance = await automator.launch({
      executablePath,
      projectPath: './dist/build/mp-weixin',
      port: 9420,
      platform: 'mp-weixin',
      close: false,
    })

    globalMiniProgram = instance
    createLock(9420)
    console.log('微信开发者工具已启动')
    return instance
  } finally {
    isInitializing = false
  }
}

export async function closeMiniProgram(): Promise<void> {
  if (globalMiniProgram) {
    console.log('正在关闭微信开发者工具...')
    try {
      await globalMiniProgram.close()
    } catch (e) {
      // 忽略关闭时的错误
    }
    globalMiniProgram = null
    console.log('微信开发者工具已关闭')
  }
  releaseLock()
}

export function getMiniProgram() {
  if (!globalMiniProgram) {
    throw new Error('MiniProgram instance not initialized. Call initMiniProgram() first.')
  }
  return globalMiniProgram
}
