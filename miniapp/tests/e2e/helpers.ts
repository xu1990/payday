/**
 * E2E 测试辅助函数
 */

export interface E2ETestContext {
  miniProgram: any
  page?: any
}

/**
 * 等待页面加载完成
 */
export async function waitForPageLoad(page: Page, timeout = 5000): Promise<void> {
  await page.waitFor(async () => {
    const data = await page.data()
    // 假设页面有一个 loaded 标志
    return data.loaded !== false
  }, timeout)
}

/**
 * 等待元素出现
 */
export async function waitForElement(
  page: Page,
  selector: string,
  timeout = 5000
): Promise<void> {
  await page.waitFor(async () => {
    const elements = await page.$$(selector)
    return elements.length > 0
  }, timeout)
}

/**
 * 等待元素消失
 */
export async function waitForElementDisappear(
  page: Page,
  selector: string,
  timeout = 5000
): Promise<void> {
  await page.waitFor(async () => {
    const elements = await page.$$(selector)
    return elements.length === 0
  }, timeout)
}

/**
 * 点击元素
 */
export async function tapElement(page: Page, selector: string): Promise<void> {
  await waitForElement(page, selector)
  const element = await page.$(selector)
  if (!element) {
    throw new Error(`Element not found: ${selector}`)
  }
  await element.tap()
}

/**
 * 输入文本
 */
export async function inputText(
  page: Page,
  selector: string,
  text: string
): Promise<void> {
  await waitForElement(page, selector)
  const element = await page.$(selector)
  if (!element) {
    throw new Error(`Element not found: ${selector}`)
  }
  await element.trigger('input', { value: text })
}

/**
 * 获取页面数据
 */
export async function getPageData<T = any>(page: Page): Promise<T> {
  return (await page.data()) as T
}

/**
 * 滚动到页面底部
 */
export async function scrollToLower(page: Page): Promise<void> {
  await page.callMethod('onReachBottom')
}

/**
 * 下拉刷新
 */
export async function pullDownRefresh(page: Page): Promise<void> {
  await page.callMethod('onPullDownRefresh')
  // 等待刷新完成
  await page.waitFor(1000)
}

/**
 * 等待导航完成
 */
export async function waitForNavigation(
  miniProgram: any,
  targetPage: string,
  timeout = 5000
): Promise<any> {
  return await miniProgram.waitFor(`/${targetPage}`, timeout)
}

/**
 * 切换 Tab
 */
export async function switchTab(
  miniProgram: any,
  tabPage: string
): Promise<any> {
  if (!miniProgram) {
    throw new Error('MiniProgram instance is not available')
  }
  return await miniProgram.switchTab(`/${tabPage}`)
}

/**
 * 返回上一页
 */
export async function navigateBack(page: Page, delta = 1): Promise<void> {
  await page.callMethod('onUnload')
  // 使用 uni.navigateBack
  const pages = await page.$wx.page?.getPages?.() || []
  if (pages.length > delta) {
    await page.navigateBack()
  }
}

/**
 * 获取 Toast 消息
 */
export async function getToastMessage(miniProgram: MiniProgram): Promise<string> {
  const element = await miniProgram.$('.uni-toast__info')
  if (!element) {
    return ''
  }
  return await element.text()
}

/**
 * 等待 Toast 消失
 */
export async function waitForToastDisappear(
  miniProgram: MiniProgram,
  timeout = 3000
): Promise<void> {
  await miniProgram.waitFor(async () => {
    const element = await miniProgram.$('.uni-toast')
    return !element
  }, timeout)
}

/**
 * 断言元素存在
 */
export async function assertElementExists(
  page: Page,
  selector: string,
  message?: string
): Promise<void> {
  const elements = await page.$$(selector)
  if (elements.length === 0) {
    throw new Error(message || `Expected element "${selector}" to exist`)
  }
}

/**
 * 断言元素不存在
 */
export async function assertElementNotExists(
  page: Page,
  selector: string,
  message?: string
): Promise<void> {
  const elements = await page.$$(selector)
  if (elements.length > 0) {
    throw new Error(message || `Expected element "${selector}" to not exist`)
  }
}

/**
 * 断言元素文本
 */
export async function assertElementText(
  page: Page,
  selector: string,
  expectedText: string,
  message?: string
): Promise<void> {
  await waitForElement(page, selector)
  const element = await page.$(selector)
  if (!element) {
    throw new Error(`Element not found: ${selector}`)
  }
  const actualText = await element.text()
  if (actualText !== expectedText) {
    throw new Error(
      message || `Expected text "${expectedText}", got "${actualText}"`
    )
  }
}

/**
 * 断言元素包含文本
 */
export async function assertElementContainsText(
  page: Page,
  selector: string,
  expectedText: string,
  message?: string
): Promise<void> {
  await waitForElement(page, selector)
  const element = await page.$(selector)
  if (!element) {
    throw new Error(`Element not found: ${selector}`)
  }
  const actualText = await element.text()
  if (!actualText.includes(expectedText)) {
    throw new Error(
      message || `Expected text to contain "${expectedText}", got "${actualText}"`
    )
  }
}

/**
 * 截图（用于调试）
 */
export async function screenshot(
  page: Page,
  name: string
): Promise<Buffer> {
  return await page.screenshot({
    fullPage: true,
    type: 'png',
  })
}

/**
 * 延迟函数
 */
export function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}
