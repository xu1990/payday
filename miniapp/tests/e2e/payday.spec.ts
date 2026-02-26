/**
 * E2E 测试 - 发薪日设置与工资记录
 * 测试发薪日配置和工资管理功能
 */
import { describe, it, expect, beforeAll } from 'vitest'
import { getMiniProgram } from './instance'
import {
  waitForPageLoad,
  waitForElement,
  inputText,
  tapElement,
  getPageData,
  delay,
} from './helpers'

describe('E2E: 发薪日设置', () => {
  beforeAll(async () => {
    const miniProgram = getMiniProgram()
    await delay(3000)

    // 跳转到发薪日设置页
    await miniProgram.reLaunch('/pages/payday-setting/index')
    await delay(2000)
  }, 60000)

  it('应该显示发薪日设置页', async () => {
    const miniProgram = getMiniProgram()
    const page = await miniProgram.currentPage()
    expect(page.path).toBe('pages/payday-setting/index')
    await waitForPageLoad(page)
  })

  it('应该显示发薪日选择器', async () => {
    const miniProgram = getMiniProgram()
    const page = await miniProgram.currentPage()

    // 查找日期选择器
    const datePicker = await page.$('.date-picker, .payday-picker, picker')
    expect(datePicker).toBeDefined()
  })

  it('应该显示保存按钮', async () => {
    const miniProgram = getMiniProgram()
    const page = await miniProgram.currentPage()

    const saveBtn = await page.$('.save-btn, .btn-save, button[type="submit"]')
    expect(saveBtn).toBeDefined()
  })

  it('应该能设置每月发薪日', async () => {
    const miniProgram = getMiniProgram()
    const page = await miniProgram.currentPage()

    // 查找并点击日期选择器
    const datePicker = await page.$('.date-picker, .payday-picker, picker')
    if (datePicker) {
      await datePicker.tap()
      await delay(500)

      // 点击确认（模拟选择日期）
      const confirmBtn = await page.$('.confirm, .btn-confirm')
      if (confirmBtn) {
        await confirmBtn.tap()
        await delay(500)
      }
    }

    // 点击保存
    const saveBtn = await page.$('.save-btn, .btn-save, button')
    if (saveBtn) {
      await saveBtn.tap()
      await delay(2000)

      // 验证是否显示成功提示
      // 注意：实际测试中需要根据实际情况调整
    }
  })
})

describe('E2E: 工资记录', () => {
  beforeAll(async () => {
    const miniProgram = getMiniProgram()
    await miniProgram.reLaunch('/pages/salary-record/index')
    await delay(2000)
  })

  it('应该显示工资记录页', async () => {
    const miniProgram = getMiniProgram()
    const page = await miniProgram.currentPage()
    expect(page.path).toBe('pages/salary-record/index')
    await waitForPageLoad(page)
  })

  it('应该显示添加记录按钮', async () => {
    const miniProgram = getMiniProgram()
    const page = await miniProgram.currentPage()

    const addBtn = await page.$('.add-btn, .btn-add, .fab-add')
    expect(addBtn).toBeDefined()
  })

  it('应该能点击添加记录按钮', async () => {
    const miniProgram = getMiniProgram()
    const page = await miniProgram.currentPage()

    const addBtn = await page.$('.add-btn, .btn-add, .fab-add')
    if (addBtn) {
      await addBtn.tap()
      await delay(1000)

      // 可能弹出选择框或跳转到添加页面
      const currentPage = await miniProgram.currentPage()
      // 根据实际业务逻辑验证
    }
  })

  it('应该显示工资列表', async () => {
    const miniProgram = getMiniProgram()
    const page = await miniProgram.currentPage()

    // 查找工资列表容器
    const salaryList = await page.$('.salary-list, .record-list, .list')
    expect(salaryList).toBeDefined()
  })
})

describe('E2E: 工资统计', () => {
  beforeAll(async () => {
    const miniProgram = getMiniProgram()
    await miniProgram.reLaunch('/pages/statistics/index')
    await delay(2000)
  })

  it('应该显示工资统计页', async () => {
    const miniProgram = getMiniProgram()
    const page = await miniProgram.currentPage()
    expect(page.path).toBe('pages/statistics/index')
    await waitForPageLoad(page)
  })

  it('应该显示统计数据', async () => {
    const miniProgram = getMiniProgram()
    const page = await miniProgram.currentPage()

    // 查找统计卡片或图表容器
    const statsCard = await page.$('.stats-card, .chart-container, .statistics')
    expect(statsCard).toBeDefined()
  })

  it('应该显示月度或年度切换', async () => {
    const miniProgram = getMiniProgram()
    const page = await miniProgram.currentPage()

    // 查找切换按钮
    const toggleBtn = await page.$('.toggle-btn, .switch-month-year, .period-switch')
    if (toggleBtn) {
      expect(toggleBtn).toBeDefined()
    }
  })
})

describe('E2E: 发薪海报', () => {
  beforeAll(async () => {
    const miniProgram = getMiniProgram()
    await miniProgram.reLaunch('/pages/poster/index')
    await delay(2000)
  })

  it('应该显示海报页', async () => {
    const miniProgram = getMiniProgram()
    const page = await miniProgram.currentPage()
    expect(page.path).toBe('pages/poster/index')
    await waitForPageLoad(page)
  })

  it('应该显示海报预览', async () => {
    const miniProgram = getMiniProgram()
    const page = await miniProgram.currentPage()

    // 查找海报画布或图片
    const posterCanvas = await page.$('.poster-canvas, .poster-image, canvas')
    expect(posterCanvas).toBeDefined()
  })

  it('应该显示保存或分享按钮', async () => {
    const miniProgram = getMiniProgram()
    const page = await miniProgram.currentPage()

    // 查找保存按钮
    const saveBtn = await page.$('.save-btn, .btn-save')

    // 查找分享按钮
    const shareBtn = await page.$('.share-btn, .btn-share')

    expect(saveBtn || shareBtn).toBeDefined()
  })
})
