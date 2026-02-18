/**
 * Loading 组件单元测试
 * 测试加载提示组件
 */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import Loading from '@/components/Loading.vue'

describe('Loading 组件', () => {
  describe('基本渲染', () => {
    it('默认应该显示', () => {
      const wrapper = mount(Loading)

      expect(wrapper.vm.$props.show).toBe(true)
      expect(wrapper.find('.page-loading-container').exists()).toBe(true)
    })

    it('show 为 false 时应该隐藏', () => {
      const wrapper = mount(Loading, {
        props: {
          show: false,
        },
      })

      expect(wrapper.find('.page-loading-container').exists()).toBe(false)
    })

    it('应该有默认的 spinner 类型', () => {
      const wrapper = mount(Loading)

      expect(wrapper.vm.$props.type).toBe('spinner')
      expect(wrapper.find('.spinner').exists()).toBe(true)
    })
  })

  describe('加载类型', () => {
    it('应该显示 spinner 类型', () => {
      const wrapper = mount(Loading, {
        props: {
          type: 'spinner',
        },
      })

      expect(wrapper.find('.spinner').exists()).toBe(true)
      expect(wrapper.findAll('.spinner-dot')).toHaveLength(3)
    })

    it('应该显示 circle 类型', () => {
      const wrapper = mount(Loading, {
        props: {
          type: 'circle',
        },
      })

      expect(wrapper.find('.circle-loading').exists()).toBe(true)
      expect(wrapper.find('.circle-path').exists()).toBe(true)
    })
  })

  describe('文本提示', () => {
    it('应该显示加载文本', () => {
      const wrapper = mount(Loading, {
        props: {
          text: '加载中...',
        },
      })

      expect(wrapper.find('.loading-text').exists()).toBe(true)
      expect(wrapper.text()).toContain('加载中...')
    })

    it('没有文本时不应该显示文本元素', () => {
      const wrapper = mount(Loading, {
        props: {
          text: '',
        },
      })

      expect(wrapper.find('.loading-text').exists()).toBe(false)
    })
  })

  describe('全屏模式', () => {
    it('默认不是全屏模式', () => {
      const wrapper = mount(Loading)

      expect(wrapper.vm.$props.fullscreen).toBe(false)
      expect(wrapper.find('.fullscreen').exists()).toBe(false)
    })

    it('应该支持全屏模式', () => {
      const wrapper = mount(Loading, {
        props: {
          fullscreen: true,
        },
      })

      expect(wrapper.vm.$props.fullscreen).toBe(true)
      expect(wrapper.find('.fullscreen').exists()).toBe(true)
    })

    it('全屏模式应该有背景色', () => {
      const wrapper = mount(Loading, {
        props: {
          fullscreen: true,
          backgroundColor: 'rgba(0, 0, 0, 0.5)',
        },
      })

      expect(wrapper.vm.$props.backgroundColor).toBe('rgba(0, 0, 0, 0.5)')
    })
  })

  describe('样式类名', () => {
    it('应该有正确的容器类名', () => {
      const wrapper = mount(Loading)

      expect(wrapper.find('.page-loading-container').exists()).toBe(true)
    })

    it('应该有内容区域类名', () => {
      const wrapper = mount(Loading)

      expect(wrapper.find('.loading-content').exists()).toBe(true)
    })
  })

  describe('自定义配置', () => {
    it('应该支持自定义背景色', () => {
      const bgColor = 'rgba(255, 255, 255, 0.95)'
      const wrapper = mount(Loading, {
        props: {
          backgroundColor: bgColor,
        },
      })

      expect(wrapper.vm.$props.backgroundColor).toBe(bgColor)
    })
  })
})
