/**
 * StatusTag 组件单元测试
 * 测试状态标签的渲染和样式
 */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import StatusTag from '@/components/StatusTag.vue'

describe('StatusTag 组件', () => {
  describe('基础渲染', () => {
    it('应该正确渲染激活状态', () => {
      const wrapper = mount(StatusTag, {
        props: {
          status: 'active',
        },
      })

      expect(wrapper.text()).toContain('启用')
      expect(wrapper.find('[role="status"]').exists()).toBe(true)
    })

    it('应该正确渲染禁用状态', () => {
      const wrapper = mount(StatusTag, {
        props: {
          status: 'disabled',
        },
      })

      expect(wrapper.text()).toContain('禁用')
    })

    it('应该正确渲染待处理状态', () => {
      const wrapper = mount(StatusTag, {
        props: {
          status: 'pending',
        },
      })

      expect(wrapper.text()).toContain('待处理')
    })

    it('应该正确渲染已拒绝状态', () => {
      const wrapper = mount(StatusTag, {
        props: {
          status: 'rejected',
        },
      })

      expect(wrapper.text()).toContain('已拒绝')
    })
  })

  describe('标签类型', () => {
    it('应该为成功状态设置 success 类型', () => {
      const wrapper = mount(StatusTag, {
        props: {
          status: 'active',
        },
      })

      const tag = wrapper.find('.el-tag')
      expect(tag.classes()).toContain('el-tag--success')
    })

    it('应该为警告状态设置 warning 类型', () => {
      const wrapper = mount(StatusTag, {
        props: {
          status: 'disabled',
        },
      })

      const tag = wrapper.find('.el-tag')
      expect(tag.classes()).toContain('el-tag--warning')
    })

    it('应该为危险状态设置 danger 类型', () => {
      const wrapper = mount(StatusTag, {
        props: {
          status: 'rejected',
        },
      })

      const tag = wrapper.find('.el-tag')
      expect(tag.classes()).toContain('el-tag--danger')
    })

    it('应该为信息状态设置 info 类型', () => {
      const wrapper = mount(StatusTag, {
        props: {
          status: 'pending',
        },
      })

      const tag = wrapper.find('.el-tag')
      expect(tag.classes()).toContain('el-tag--info')
    })
  })

  describe('未知状态处理', () => {
    it('应该显示原始状态文本当状态不在映射表中', () => {
      const unknownStatus = 'unknown_status'
      const wrapper = mount(StatusTag, {
        props: {
          status: unknownStatus,
        },
      })

      expect(wrapper.text()).toContain(unknownStatus)
    })

    it('应该为未知状态使用 info 类型', () => {
      const wrapper = mount(StatusTag, {
        props: {
          status: 'unknown_status',
        },
      })

      const tag = wrapper.find('.el-tag')
      expect(tag.classes()).toContain('el-tag--info')
    })
  })

  describe('HTML 注入防护', () => {
    it('应该移除状态文本中的 HTML 标签', () => {
      const wrapper = mount(StatusTag, {
        props: {
          status: '<script>alert("xss")</script>',
        },
      })

      const text = wrapper.text()
      expect(text).not.toContain('<script>')
      expect(text).not.toContain('alert')
    })

    it('应该处理包含 HTML 标签的状态', () => {
      const wrapper = mount(StatusTag, {
        props: {
          status: '<b>bold</b>',
        },
      })

      const text = wrapper.text()
      expect(text).not.toContain('<b>')
      expect(text).not.toContain('</b>')
    })
  })

  describe('可访问性', () => {
    it('应该有正确的 ARIA 标签', () => {
      const wrapper = mount(StatusTag, {
        props: {
          status: 'active',
        },
      })

      const tag = wrapper.find('[role="status"]')
      expect(tag.exists()).toBe(true)

      const ariaLabel = tag.attributes()['aria-label']
      expect(ariaLabel).toContain('状态')
      expect(ariaLabel).toContain('启用')
    })
  })
})
