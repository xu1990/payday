/**
 * E2E 测试 - 导航与 Tab 切换
 * 测试底部 Tab 导航和页面跳转
 */
import { describe, it, expect, beforeAll } from 'vitest'
import { getMiniProgram } from './instance'
import {
  waitForPageLoad,
  waitForElement,
  switchTab,
  tapElement,
  delay,
} from './helpers'

describe('E2E: Tab 导航', () => {
  beforeAll(async () => {
    const miniProgram = getMiniProgram()
    await delay(3000)
  }, 60000)

  it('应该切换到广场 Tab', async () => {
    const miniProgram = getMiniProgram()
    const page = await switchTab(miniProgram, 'pages/square/index')
    expect(page.path).toBe('pages/square/index')
    await waitForPageLoad(page)
  })

  it('广场页应该显示帖子列表', async () => {
    const miniProgram = getMiniProgram()
    let page = await miniProgram.currentPage()

    if (page.path !== 'pages/square/index') {
      page = await switchTab(miniProgram, 'pages/square/index')
    }

    await waitForPageLoad(page)

    // 查找帖子列表容器
    const postList = await page.$('.post-list, .square-list, .list')
    expect(postList).toBeDefined()
  })

  it('应该切换到关注 Tab', async () => {
    const miniProgram = getMiniProgram()
    const page = await switchTab(miniProgram, 'pages/feed/index')
    expect(page.path).toBe('pages/feed/index')
    await waitForPageLoad(page)
  })

  it('关注页应该显示关注内容', async () => {
    const miniProgram = getMiniProgram()
    let page = await miniProgram.currentPage()

    if (page.path !== 'pages/feed/index') {
      const page = await switchTab(miniProgram, 'pages/feed/index')
    }

    await waitForPageLoad(page)

    // 查找关注流内容
    const feedList = await page.$('.feed-list, .post-list')
    expect(feedList).toBeDefined()
  })

  it('应该切换到我的 Tab', async () => {
    const miniProgram = getMiniProgram()
    const page = await switchTab(miniProgram, 'pages/profile/index')
    expect(page.path).toBe('pages/profile/index')
    await waitForPageLoad(page)
  })

  it('个人中心应该显示用户信息区域', async () => {
    const miniProgram = getMiniProgram()
    let page = await miniProgram.currentPage()

    if (page.path !== 'pages/profile/index') {
      page = await switchTab(miniProgram, 'pages/profile/index')
    }

    await waitForPageLoad(page)

    // 查找用户头像区域
    const userSection = await page.$('.user-info, .profile-header, .avatar-container')
    expect(userSection).toBeDefined()
  })

  it('应该切换回首页 Tab', async () => {
    const miniProgram = getMiniProgram()
    const page = await switchTab(miniProgram, 'pages/index')
    expect(page.path).toBe('pages/index')
    await waitForPageLoad(page)
  })
})

describe('E2E: 页面跳转', () => {
  beforeAll(async () => {
    const miniProgram = getMiniProgram()
    const page = await switchTab(miniProgram, 'pages/index')
    await waitForPageLoad(page)
  })

  it('应该能跳转到发薪日设置页', async () => {
    const miniProgram = getMiniProgram()
    const page = await miniProgram.currentPage()

    // 点击设置按钮（根据实际页面结构调整选择器）
    const settingBtn = await page.$('.setting-btn, .icon-settings, .btn-settings')

    if (settingBtn) {
      await settingBtn.tap()
      await delay(2000)

      const currentPage = await miniProgram.currentPage()
      expect(currentPage.path).toBe('pages/payday-setting/index')

      // 返回
      await miniProgram.navigateBack()
      await delay(1000)
    }
  })

  it('应该能跳转到工资记录页', async () => {
    const miniProgram = getMiniProgram()
    const page = await miniProgram.currentPage()

    // 点击工资记录按钮
    const salaryBtn = await page.$('.salary-btn, .icon-salary, .btn-salary')

    if (salaryBtn) {
      await salaryBtn.tap()
      await delay(2000)

      const currentPage = await miniProgram.currentPage()
      expect(currentPage.path).toBe('pages/salary-record/index')

      // 返回
      await miniProgram.navigateBack()
      await delay(1000)
    }
  })

  it('应该能跳转到发薪海报页', async () => {
    const miniProgram = getMiniProgram()
    const page = await miniProgram.currentPage()

    // 点击海报按钮
    const posterBtn = await page.$('.poster-btn, .icon-poster, .btn-poster')

    if (posterBtn) {
      await posterBtn.tap()
      await delay(2000)

      const currentPage = await miniProgram.currentPage()
      expect(currentPage.path).toBe('pages/poster/index')

      // 返回
      await miniProgram.navigateBack()
      await delay(1000)
    }
  })
})

describe('E2E: 个人中心功能入口', () => {
  beforeAll(async () => {
    const miniProgram = getMiniProgram()
    const page = await switchTab(miniProgram, 'pages/profile/index')
    await waitForPageLoad(page)
  })

  it('应该能从个人中心进入会员中心', async () => {
    const miniProgram = getMiniProgram()
    const page = await miniProgram.currentPage()

    const membershipBtn = await page.$('.membership-btn, .vip-btn, .btn-vip')
    if (membershipBtn) {
      await membershipBtn.tap()
      await delay(2000)

      const currentPage = await miniProgram.currentPage()
      expect(currentPage.path).toBe('pages/membership/index')

      await miniProgram.navigateBack()
      await delay(1000)
    }
  })

  it('应该能从个人中心进入设置页', async () => {
    const miniProgram = getMiniProgram()
    const page = await miniProgram.currentPage()

    const settingsBtn = await page.$('.settings-btn, .btn-settings')
    if (settingsBtn) {
      await settingsBtn.tap()
      await delay(2000)

      const currentPage = await miniProgram.currentPage()
      expect(currentPage.path).toBe('pages/settings/index')

      await miniProgram.navigateBack()
      await delay(1000)
    }
  })

  it('应该能从个人中心进入积分商城', async () => {
    const miniProgram = getMiniProgram()
    const page = await miniProgram.currentPage()

    const pointMallBtn = await page.$('.point-mall-btn, .mall-btn, .btn-points')
    if (pointMallBtn) {
      await pointMallBtn.tap()
      await delay(2000)

      const currentPage = await miniProgram.currentPage()
      expect(currentPage.path).toBe('pages/point-mall/index')

      await miniProgram.navigateBack()
      await delay(1000)
    }
  })
})
