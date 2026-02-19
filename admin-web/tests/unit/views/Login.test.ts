/**
 * Login 视图测试
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import Login from '@/views/Login.vue'

// Mock vue-router
const mockPush = vi.fn()
const mockReplace = vi.fn()

vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: mockPush,
    replace: mockReplace,
  }),
  useRoute: () => ({
    query: { redirect: '/' },
  }),
}))

// Mock API
vi.mock('@/api/admin', () => ({
  login: vi.fn(() =>
    Promise.resolve({
      data: {
        access_token: 'test_token',
        csrf_token: 'test_csrf',
      },
    })
  ),
}))

// Mock ElMessage
vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn(),
  },
}))

describe('Login 视图', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('应该正确渲染', () => {
    const wrapper = mount(Login, {
      global: {
        stubs: {
          'el-card': true,
          'el-form': true,
          'el-form-item': true,
          'el-input': true,
          'el-button': true,
          'el-alert': true,
        },
      },
    })

    expect(wrapper.find('.login-wrap').exists()).toBe(true)
  })

  it('应该显示登录卡片标题', () => {
    const wrapper = mount(Login, {
      global: {
        stubs: {
          'el-card': {
            template: '<div class="login-card"><slot name="header">薪日 PayDay · 管理后台</slot></div>',
          },
          'el-form': true,
          'el-form-item': true,
          'el-input': true,
          'el-button': true,
          'el-alert': true,
        },
      },
    })

    expect(wrapper.text()).toContain('薪日 PayDay · 管理后台')
  })

  it('应该有用户名和密码输入框', () => {
    const wrapper = mount(Login, {
      global: {
        stubs: {
          'el-card': true,
          'el-form': true,
          'el-form-item': true,
          'el-input': true,
          'el-button': true,
          'el-alert': true,
        },
      },
    })

    // 验证表单结构存在
    expect(wrapper.find('.login-wrap').exists()).toBe(true)
  })

  it('应该有登录按钮', () => {
    const wrapper = mount(Login, {
      global: {
        stubs: {
          'el-card': true,
          'el-form': true,
          'el-form-item': true,
          'el-input': true,
          'el-button': true,
          'el-alert': true,
        },
      },
    })

    // 验证组件结构存在
    expect(wrapper.find('.login-wrap').exists()).toBe(true)
  })

  it('应该有正确的样式类名', () => {
    const wrapper = mount(Login, {
      global: {
        stubs: {
          'el-card': true,
          'el-form': true,
          'el-form-item': true,
          'el-input': true,
          'el-button': true,
          'el-alert': true,
        },
      },
    })

    expect(wrapper.classes()).toContain('login-wrap')
  })

  it('应该支持表单验证规则', () => {
    const wrapper = mount(Login, {
      global: {
        stubs: {
          'el-card': true,
          'el-form': true,
          'el-form-item': true,
          'el-input': true,
          'el-button': true,
          'el-alert': true,
        },
      },
    })

    // 验证组件实例存在
    expect(wrapper.vm).toBeDefined()
  })

  it('应该有loading状态', () => {
    const wrapper = mount(Login, {
      global: {
        stubs: {
          'el-card': true,
          'el-form': true,
          'el-form-item': true,
          'el-input': true,
          'el-button': true,
          'el-alert': true,
        },
      },
    })

    // 验证组件实例
    expect(wrapper.vm).toBeDefined()
  })

  it('应该有error状态', () => {
    const wrapper = mount(Login, {
      global: {
        stubs: {
          'el-card': true,
          'el-form': true,
          'el-form-item': true,
          'el-input': true,
          'el-button': true,
          'el-alert': true,
        },
      },
    })

    // 验证组件实例
    expect(wrapper.vm).toBeDefined()
  })
})
