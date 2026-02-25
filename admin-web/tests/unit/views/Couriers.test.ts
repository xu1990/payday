/**
 * Couriers 视图测试
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import Couriers from '@/views/Couriers.vue'

// Mock API
vi.mock('@/api/courier', () => ({
  listCouriers: vi.fn(() =>
    Promise.resolve({
      data: {
        couriers: [],
        total: 0,
      },
    })
  ),
  createCourier: vi.fn(() =>
    Promise.resolve({
      data: { id: '1' },
    })
  ),
  updateCourier: vi.fn(() =>
    Promise.resolve({
      data: null,
    })
  ),
  deleteCourier: vi.fn(() =>
    Promise.resolve({
      data: null,
    })
  ),
}))

// Mock utils
vi.mock('@/utils/format', () => ({
  formatDate: vi.fn((date: string) => date),
}))

// Mock Element Plus
vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
  },
  ElMessageBox: {
    confirm: vi.fn(() => Promise.resolve('confirm')),
  },
}))

describe('Couriers 视图', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('应该正确渲染', () => {
    const wrapper = mount(Couriers, {
      global: {
        stubs: {
          'el-table': true,
          'el-table-column': true,
          'el-button': true,
          'el-pagination': true,
          'el-dialog': true,
          'el-form': true,
          'el-form-item': true,
          'el-input': true,
          'el-input-number': true,
          'el-checkbox': true,
          'el-tag': true,
        },
      },
    })

    expect(wrapper.find('.page-header').exists()).toBe(true)
    expect(wrapper.find('.page-header h2').text()).toBe('物流公司管理')
  })

  it('应该显示页面标题', () => {
    const wrapper = mount(Couriers, {
      global: {
        stubs: {
          'el-table': true,
          'el-table-column': true,
          'el-button': true,
          'el-pagination': true,
        },
      },
    })

    const title = wrapper.find('.page-header h2')
    expect(title.exists()).toBe(true)
    expect(title.text()).toBe('物流公司管理')
  })

  it('应该有新建按钮', () => {
    const wrapper = mount(Couriers, {
      global: {
        stubs: {
          'el-table': true,
          'el-table-column': true,
          'el-button': true,
          'el-pagination': true,
        },
      },
    })

    const button = wrapper.findAll('.page-header el-button-stub')
    expect(button.length).toBeGreaterThan(0)
  })
})
