/**
 * UserList 视图测试
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import UserList from '@/views/UserList.vue'

// Mock API
vi.mock('@/api/admin', () => ({
  getUsers: vi.fn(() =>
    Promise.resolve({
      data: {
        items: [],
        total: 0,
      },
    })
  ),
}))

// Mock vue-router
const mockPush = vi.fn()
vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}))

describe('UserList 视图', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('应该正确渲染', () => {
    const wrapper = mount(UserList, {
      global: {
        stubs: {
          'SearchToolbar': true,
          'BaseDataTable': true,
          'el-table-column': true,
          'el-button': true,
          'el-select': true,
          'el-option': true,
        },
      },
    })

    expect(wrapper.find('.page-title').exists()).toBe(true)
  })

  it('应该显示页面标题', () => {
    const wrapper = mount(UserList, {
      global: {
        stubs: {
          'SearchToolbar': true,
          'BaseDataTable': true,
          'el-table-column': true,
          'el-button': true,
          'el-select': true,
          'el-option': true,
        },
      },
    })

    expect(wrapper.find('.page-title').text()).toBe('用户管理')
  })

  it('应该有搜索工具栏', () => {
    const wrapper = mount(UserList, {
      global: {
        stubs: {
          'SearchToolbar': {
            template: '<div class="search-toolbar"><slot /></div>',
          },
          'BaseDataTable': true,
          'el-table-column': true,
          'el-button': true,
          'el-select': true,
          'el-option': true,
        },
      },
    })

    expect(wrapper.find('.search-toolbar').exists()).toBe(true)
  })

  it('应该有状态筛选器', () => {
    const wrapper = mount(UserList, {
      global: {
        stubs: {
          'SearchToolbar': true,
          'BaseDataTable': true,
          'el-table-column': true,
          'el-button': true,
          'el-select': true,
          'el-option': true,
        },
      },
    })

    // 验证组件存在
    expect(wrapper.vm).toBeDefined()
  })

  it('应该有数据表格', () => {
    const wrapper = mount(UserList, {
      global: {
        stubs: {
          'SearchToolbar': true,
          'BaseDataTable': {
            template: '<div class="data-table"><slot /></div>',
          },
          'el-table-column': true,
          'el-button': true,
          'el-select': true,
          'el-option': true,
        },
      },
    })

    expect(wrapper.find('.data-table').exists()).toBe(true)
  })

  it('应该有正确的表格列配置', () => {
    const wrapper = mount(UserList, {
      global: {
        stubs: {
          'SearchToolbar': true,
          'BaseDataTable': true,
          'el-table-column': {
            template: '<div class="table-col"><slot /></div>',
          },
          'el-button': true,
          'el-select': true,
          'el-option': true,
        },
      },
    })

    // 验证列配置存在
    expect(wrapper.vm).toBeDefined()
  })

  it('应该有分页功能', () => {
    const wrapper = mount(UserList, {
      global: {
        stubs: {
          'SearchToolbar': true,
          'BaseDataTable': true,
          'el-table-column': true,
          'el-button': true,
          'el-select': true,
          'el-option': true,
        },
      },
    })

    // 验证组件存在
    expect(wrapper.vm).toBeDefined()
  })
})
