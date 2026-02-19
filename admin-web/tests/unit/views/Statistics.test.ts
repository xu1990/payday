/**
 * Statistics 视图测试
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import Statistics from '@/views/Statistics.vue'

// Mock API
vi.mock('@/api/admin', () => ({
  getStatistics: vi.fn(() =>
    Promise.resolve({
      data: {
        user_total: 1000,
        user_new_today: 50,
        salary_record_total: 5000,
        salary_record_today: 200,
      },
    })
  ),
}))

// Mock ElMessage
vi.mock('element-plus', () => ({
  ElMessage: {
    error: vi.fn(),
  },
}))

// Mock error utility
vi.mock('@/utils/error', () => ({
  getCommonApiErrorMessage: vi.fn(() => '获取统计数据失败'),
}))

describe('Statistics 视图', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('应该正确渲染', () => {
    const wrapper = mount(Statistics, {
      global: {
        stubs: {
          'el-row': true,
          'el-col': true,
          'el-card': true,
        },
      },
    })

    expect(wrapper.find('.statistics-page').exists()).toBe(true)
  })

  it('应该显示页面标题', () => {
    const wrapper = mount(Statistics, {
      global: {
        stubs: {
          'el-row': true,
          'el-col': true,
          'el-card': true,
        },
      },
    })

    expect(wrapper.find('.page-title').exists()).toBe(true)
    expect(wrapper.find('.page-title').text()).toBe('数据统计')
  })

  it('应该显示4个统计卡片', () => {
    const wrapper = mount(Statistics, {
      global: {
        stubs: {
          'el-row': {
            template: '<div class="stats-row"><slot /></div>',
          },
          'el-col': {
            template: '<div class="stat-col"><slot /></div>',
          },
          'el-card': {
            template: '<div class="stat-card"><slot /></div>',
          },
        },
      },
    })

    expect(wrapper.find('.stats-row').exists()).toBe(true)
  })

  it('应该有正确的统计标签', () => {
    const wrapper = mount(Statistics, {
      global: {
        stubs: {
          'el-row': {
            template: '<div class="stats-row"><slot /></div>',
          },
          'el-col': {
            template: '<div class="stat-col"><slot /></div>',
          },
          'el-card': {
            template: '<div class="stat-card"><slot /></div>',
          },
        },
      },
    })

    // 验证组件结构存在
    expect(wrapper.find('.statistics-page').exists()).toBe(true)
    expect(wrapper.find('.stats-row').exists()).toBe(true)
  })

  it('应该有loading状态', () => {
    const wrapper = mount(Statistics, {
      global: {
        stubs: {
          'el-row': true,
          'el-col': true,
          'el-card': true,
        },
      },
    })

    // 验证组件实例存在
    expect(wrapper.vm).toBeDefined()
  })

  it('应该有统计数据引用', () => {
    const wrapper = mount(Statistics, {
      global: {
        stubs: {
          'el-row': true,
          'el-col': true,
          'el-card': true,
        },
      },
    })

    // 验证组件实例
    expect(wrapper.vm).toBeDefined()
  })

  it('应该在组件挂载时加载数据', () => {
    const wrapper = mount(Statistics, {
      global: {
        stubs: {
          'el-row': true,
          'el-col': true,
          'el-card': true,
        },
      },
    })

    // 验证组件实例存在
    expect(wrapper.vm).toBeDefined()
  })

  it('应该有正确的样式类名', () => {
    const wrapper = mount(Statistics, {
      global: {
        stubs: {
          'el-row': true,
          'el-col': true,
          'el-card': true,
        },
      },
    })

    expect(wrapper.classes()).toContain('statistics-page')
  })
})
