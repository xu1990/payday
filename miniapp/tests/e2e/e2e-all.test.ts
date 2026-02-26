/**
 * E2E 测试主入口
 * 按顺序运行所有测试套件
 */
import { describe, beforeAll, afterAll } from 'vitest'
import { initMiniProgram, closeMiniProgram } from './instance'

// 在所有测试开始前初始化一次
beforeAll(async () => {
  await initMiniProgram()
}, 180000)

// 在所有测试结束后清理
afterAll(async () => {
  await closeMiniProgram()
})

// 导入所有测试模块
import './splash.spec'
import './navigation.spec'
import './payday.spec'
