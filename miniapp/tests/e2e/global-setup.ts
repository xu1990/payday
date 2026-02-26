/**
 * E2E 测试全局设置
 * 使用 beforeAll/afterAll 在每个测试套件前运行
 * 但通过 globalThis 单例确保只初始化一次
 */
import { beforeAll, afterAll } from 'vitest'
import { initMiniProgram, closeMiniProgram } from './instance'

beforeAll(async () => {
  // initMiniProgram 内部使用 globalThis 单例，多次调用会复用实例
  await initMiniProgram()
}, 180000)

afterAll(async () => {
  // 只在最后一个测试套件结束时清理
  await closeMiniProgram()
})
