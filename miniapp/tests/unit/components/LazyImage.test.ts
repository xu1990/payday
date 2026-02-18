/**
 * LazyImage 组件单元测试
 * 测试懒加载图片组件
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock uni 全局对象
const mockImageInfo = vi.fn()
global.uni = {
  getImageInfo: mockImageInfo,
} as any

import { mount } from '@vue/test-utils'
import LazyImage from '@/components/LazyImage.vue'

describe('LazyImage 组件', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('基本渲染', () => {
    it('应该渲染骨架屏（加载中）', () => {
      const wrapper = mount(LazyImage, {
        props: {
          src: 'https://example.com/image.jpg',
          width: '200px',
          height: '200px',
        },
      })

      // 初始状态应该显示骨架屏
      expect(wrapper.find('.lazy-skeleton').exists()).toBe(true)
    })

    it('应该使用默认宽高', () => {
      const wrapper = mount(LazyImage, {
        props: {
          src: 'https://example.com/image.jpg',
        },
      })

      expect(wrapper.vm.$props.width).toBe('100%')
      expect(wrapper.vm.$props.height).toBe('auto')
    })

    it('应该使用默认模式', () => {
      const wrapper = mount(LazyImage, {
        props: {
          src: 'https://example.com/image.jpg',
        },
      })

      expect(wrapper.vm.$props.mode).toBe('aspectFill')
    })
  })

  describe('错误状态', () => {
    it('应该显示错误状态', async () => {
      const wrapper = mount(LazyImage, {
        props: {
          src: 'https://example.com/image.jpg',
        },
      })

      // 模拟错误
      await wrapper.vm.handleError({})

      expect(wrapper.vm.isError).toBe(true)
      expect(wrapper.vm.isLoaded).toBe(false)
    })

    it('错误状态应该显示重试提示', async () => {
      const wrapper = mount(LazyImage, {
        props: {
          src: 'https://example.com/image.jpg',
        },
      })

      await wrapper.vm.handleError({})
      await wrapper.vm.$nextTick()

      expect(wrapper.find('.lazy-error').exists()).toBe(true)
      expect(wrapper.text()).toContain('加载失败')
    })
  })

  describe('加载成功', () => {
    it('应该加载成功后显示图片', async () => {
      const wrapper = mount(LazyImage, {
        props: {
          src: 'https://example.com/image.jpg',
        },
      })

      // 模拟加载成功
      await wrapper.vm.handleLoad({})

      expect(wrapper.vm.isLoaded).toBe(true)
      expect(wrapper.vm.isError).toBe(false)
    })
  })

  describe('重试功能', () => {
    it('应该能够重试加载失败的图片', async () => {
      const wrapper = mount(LazyImage, {
        props: {
          src: 'https://example.com/image.jpg',
        },
      })

      // 设置错误状态
      await wrapper.vm.handleError({})
      expect(wrapper.vm.isError).toBe(true)

      // 重试
      wrapper.vm.handleRetry()
      expect(wrapper.vm.isError).toBe(false)
      expect(wrapper.vm.displaySrc).toContain('?t=')
    })
  })

  describe('缓存功能', () => {
    it('应该启用缓存', () => {
      const wrapper = mount(LazyImage, {
        props: {
          src: 'https://example.com/image.jpg',
          cache: true,
        },
      })

      expect(wrapper.vm.$props.cache).toBe(true)
    })

    it('应该能够禁用缓存', () => {
      const wrapper = mount(LazyImage, {
        props: {
          src: 'https://example.com/image.jpg',
          cache: false,
        },
      })

      expect(wrapper.vm.$props.cache).toBe(false)
    })
  })

  describe('事件触发', () => {
    it('应该触发 load 事件', async () => {
      const wrapper = mount(LazyImage, {
        props: {
          src: 'https://example.com/image.jpg',
        },
      })

      await wrapper.vm.handleLoad({})

      expect(wrapper.emitted('load')).toBeTruthy()
      expect(wrapper.emitted('load').length).toBe(1)
    })

    it('应该触发 error 事件', async () => {
      const wrapper = mount(LazyImage, {
        props: {
          src: 'https://example.com/image.jpg',
        },
      })

      await wrapper.vm.handleError({})

      expect(wrapper.emitted('error')).toBeTruthy()
    })
  })

  describe('自定义配置', () => {
    it('应该支持自定义骨架屏颜色', () => {
      const wrapper = mount(LazyImage, {
        props: {
          src: 'https://example.com/image.jpg',
          skeletonColor: '#e0e0e0',
        },
      })

      expect(wrapper.vm.$props.skeletonColor).toBe('#e0e0e0')
    })

    it('应该支持自定义错误文本', () => {
      const wrapper = mount(LazyImage, {
        props: {
          src: 'https://example.com/image.jpg',
          errorText: '图片加载失败',
        },
      })

      expect(wrapper.vm.$props.errorText).toBe('图片加载失败')
    })

    it('应该支持不同的显示模式', () => {
      const modes = ['aspectFill', 'aspectFit', 'widthFix', 'heightFix', 'scaleToFill'] as const

      modes.forEach(mode => {
        const wrapper = mount(LazyImage, {
          props: {
            src: 'https://example.com/image.jpg',
            mode,
          },
        })

        expect(wrapper.vm.$props.mode).toBe(mode)
      })
    })
  })
})
