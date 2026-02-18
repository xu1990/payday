/**
 * EmptyState 组件单元测试
 * 测试空状态组件
 */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import EmptyState from '@/components/EmptyState.vue'

describe('EmptyState 组件', () => {
  describe('基本渲染', () => {
    it('应该渲染默认状态', () => {
      const wrapper = mount(EmptyState)

      expect(wrapper.find('.empty-state-container').exists()).toBe(true)
      expect(wrapper.find('.empty-icon').exists()).toBe(true)
    })

    it('应该显示默认图标', () => {
      const wrapper = mount(EmptyState)

      expect(wrapper.find('.icon-text').exists()).toBe(true)
      expect(wrapper.text()).toContain('📭')
    })
  })

  describe('自定义图标', () => {
    it('应该显示图片图标', () => {
      const wrapper = mount(EmptyState, {
        props: {
          icon: 'https://example.com/icon.png',
        },
      })

      expect(wrapper.find('.icon-image').exists()).toBe(true)
      expect(wrapper.find('.icon-image').attributes('src')).toBe('https://example.com/icon.png')
    })

    it('没有图片图标时显示文本图标', () => {
      const wrapper = mount(EmptyState, {
        props: {
          icon: '',
        },
      })

      expect(wrapper.find('.icon-text').exists()).toBe(true)
    })
  })

  describe('文本内容', () => {
    it('应该显示标题文本', () => {
      const wrapper = mount(EmptyState, {
        props: {
          text: '暂无数据',
        },
      })

      expect(wrapper.find('.empty-text').exists()).toBe(true)
      expect(wrapper.text()).toContain('暂无数据')
    })

    it('应该显示描述文本', () => {
      const wrapper = mount(EmptyState, {
        props: {
          description: '这里什么都没有',
        },
      })

      expect(wrapper.find('.empty-description').exists()).toBe(true)
      expect(wrapper.text()).toContain('这里什么都没有')
    })

    it('应该同时显示标题和描述', () => {
      const wrapper = mount(EmptyState, {
        props: {
          text: '暂无数据',
          description: '快去添加一些内容吧',
        },
      })

      expect(wrapper.text()).toContain('暂无数据')
      expect(wrapper.text()).toContain('快去添加一些内容吧')
    })
  })

  describe('操作按钮', () => {
    it('应该显示操作按钮', () => {
      const wrapper = mount(EmptyState, {
        props: {
          actionText: '去添加',
        },
      })

      expect(wrapper.find('.action-button').exists()).toBe(true)
      expect(wrapper.text()).toContain('去添加')
    })

    it('点击按钮应该触发事件', async () => {
      const wrapper = mount(EmptyState, {
        props: {
          actionText: '点击我',
        },
      })

      await wrapper.find('.action-button').trigger('click')

      expect(wrapper.emitted('action')).toBeTruthy()
      expect(wrapper.emitted('action').length).toBe(1)
    })

    it('没有操作文本时不应该显示按钮', () => {
      const wrapper = mount(EmptyState, {
        props: {
          actionText: '',
        },
      })

      expect(wrapper.find('.empty-action').exists()).toBe(false)
    })
  })

  describe('样式和布局', () => {
    it('应该有正确的容器类名', () => {
      const wrapper = mount(EmptyState)

      expect(wrapper.find('.empty-state-container').exists()).toBe(true)
    })

    it('应该是居中对齐', () => {
      const wrapper = mount(EmptyState)

      const container = wrapper.find('.empty-state-container')
      expect(container.exists()).toBe(true)
    })
  })

  describe('完整示例', () => {
    it('应该渲染完整的空状态', () => {
      const wrapper = mount(EmptyState, {
        props: {
          icon: 'https://example.com/empty.png',
          text: '还没有帖子',
          description: '快来发布第一条帖子吧',
          actionText: '发布帖子',
        },
      })

      expect(wrapper.find('.icon-image').exists()).toBe(true)
      expect(wrapper.text()).toContain('还没有帖子')
      expect(wrapper.text()).toContain('快来发布第一条帖子吧')
      expect(wrapper.text()).toContain('发布帖子')
      expect(wrapper.find('.action-button').exists()).toBe(true)
    })
  })
})
