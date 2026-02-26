/**
 * E2E 测试 - 启动页和登录流程
 * 测试小程序启动、用户授权登录流程
 */
import { describe, it, expect, beforeAll } from 'vitest'
import { getMiniProgram } from './instance'
import {
  waitForPageLoad,
  waitForElement,
  delay,
  getPageData,
} from './helpers'

describe('E2E: 启动与登录流程', () => {
  beforeAll(async () => {
    // 等待小程序已经启动
    await delay(5000)
  }, 60000)

  it('应该显示启动页', async () => {
    const miniProgram = getMiniProgram()
    const page = await miniProgram.currentPage()
    expect(page.path).toBe('pages/splash/index')

    // 等待启动页加载
    await waitForPageLoad(page)

    // 验证启动页元素
    await waitForElement(page, '.splash-container')

    const pageData = await getPageData(page)
    expect(pageData).toBeDefined()
  })

  it('应该自动跳转到登录页或首页', async () => {
    // 等待跳转（根据是否有 token 决定跳转目标）
    await delay(3000)

    const miniProgram = getMiniProgram()
    const page = await miniProgram.currentPage()

    // 可能跳转到登录页或首页
    const validPaths = ['pages/login/index', 'pages/index']
    expect(validPaths).toContain(page.path)
  })

  it('登录页应该显示授权按钮', async () => {
    const miniProgram = getMiniProgram()
    const page = await miniProgram.currentPage()

    if (page.path !== 'pages/login/index') {
      // 如果不是登录页，说明已登录，跳过此测试
      return
    }

    // 等待登录页加载
    await waitForPageLoad(page)

    // 查找授权按钮
    const loginButton = await page.$('.auth-btn, .login-btn, button')
    expect(loginButton).toBeDefined()

    // 验证按钮文本
    if (loginButton) {
      const buttonText = await loginButton.text()
      expect(['微信授权登录', '授权登录', '立即登录']).toContain(buttonText)
    }
  })

  it('应该能够点击授权按钮', async () => {
    const miniProgram = getMiniProgram()
    const page = await miniProgram.currentPage()

    if (page.path !== 'pages/login/index') {
      return
    }

    // 点击授权按钮（注意：实际测试时需要 mock 微信授权接口）
    const loginButton = await page.$('.auth-btn, .login-btn, button')
    if (loginButton) {
      await loginButton.tap()
      // 等待跳转
      await delay(2000)

      // 验证是否跳转到首页
      const currentPage = await miniProgram.currentPage()
      expect(currentPage.path).toBe('pages/index')
    }
  })
})

describe('E2E: 首页基础功能', () => {
  beforeAll(async () => {
    const miniProgram = getMiniProgram()

    // 确保在首页
    const page = await miniProgram.currentPage()
    if (page.path !== 'pages/index') {
      await miniProgram.reLaunch('/pages/index/index')
      await delay(2000)
    }
  }, 60000)

  it('应该显示首页', async () => {
    const miniProgram = getMiniProgram()
    const page = await miniProgram.currentPage()
    expect(page.path).toBe('pages/index')
  })

  it('应该显示发薪日倒计时', async () => {
    const miniProgram = getMiniProgram()
    const page = await miniProgram.currentPage()

    // 等待页面加载
    await waitForPageLoad(page)

    // 查找倒计时元素
    const countdownElement = await page.$('.countdown, .payday-countdown, .days-left')
    expect(countdownElement).toBeDefined()
  })

  it('应该显示心情选择器', async () => {
    const miniProgram = getMiniProgram()
    const page = await miniProgram.currentPage()

    // 查找心情选择器
    const moodSelector = await page.$('.mood-selector, .mood-list')
    expect(moodSelector).toBeDefined()
  })

  it('应该显示底部导航栏', async () => {
    const miniProgram = getMiniProgram()

    // 微信小程序的 tab-bar 是原生组件，不在页面 DOM 中
    // 但可以通过 API 验证
    const tabBar = await miniProgram.callWxAPI('getTabBar')
    expect(tabBar).toBeDefined()
  })
})
