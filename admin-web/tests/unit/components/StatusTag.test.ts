/**
 * StatusTag 组件单元测试
 * 测试状态标签组件
 */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import StatusTag from '@/components/StatusTag.vue'

describe('StatusTag 组件', () => {
  describe('默认状态映射', () => {
    it('active 状态应该显示为启用（绿色）', () => {
      const wrapper = mount(StatusTag, {
        props: {
          status: 'active',
        },
      })

      expect(wrapper.text()).toBe('启用')
      expect(wrapper.vm.tagType).toBe('success')
    })

    it('enabled 状态应该显示为启用（绿色）', () => {
      const wrapper = mount(StatusTag, {
        props: {
          status: 'enabled',
        },
      })

      expect(wrapper.text()).toBe('启用')
      expect(wrapper.vm.tagType).toBe('success')
    })

    it('disabled 状态应该显示为禁用（橙色）', () => {
      const wrapper = mount(StatusTag, {
        props: {
          status: 'disabled',
        },
      })

      expect(wrapper.text()).toBe('禁用')
      expect(wrapper.vm.tagType).toBe('warning')
    })

    it('pending 状态应该显示为待处理（蓝色）', () => {
      const wrapper = mount(StatusTag, {
        props: {
          status: 'pending',
        },
      })

      expect(wrapper.text()).toBe('待处理')
      expect(wrapper.vm.tagType).toBe('info')
    })

    it('rejected 状态应该显示为已拒绝（红色）', () => {
      const wrapper = mount(StatusTag, {
        props: {
          status: 'rejected',
        },
      })

      expect(wrapper.text()).toBe('已拒绝')
      expect(wrapper.vm.tagType).toBe('danger')
    })
  })

  describe('支付状态', () => {
    it('paid 状态应该显示为已支付（绿色）', () => {
      const wrapper = mount(StatusTag, {
        props: {
          status: 'paid',
        },
      })

      expect(wrapper.text()).toBe('已支付')
      expect(wrapper.vm.tagType).toBe('success')
    })

    it('cancelled 状态应该显示为已取消（蓝色）', () => {
      const wrapper = mount(StatusTag, {
        props: {
          status: 'cancelled',
        },
      })

      expect(wrapper.text()).toBe('已取消')
      expect(wrapper.vm.tagType).toBe('info')
    })
  })

  describe('审核状态', () => {
    it('approved 状态应该显示为已通过（绿色）', () => {
      const wrapper = mount(StatusTag, {
        props: {
          status: 'approved',
        },
      })

      expect(wrapper.text()).toBe('已通过')
      expect(wrapper.vm.tagType).toBe('success')
    })
  })

  describe('未知状态', () => {
    it('未知状态应该显示原始状态文本（蓝色）', () => {
      const wrapper = mount(StatusTag, {
        props: {
          status: 'unknown_status',
        },
      })

      expect(wrapper.text()).toBe('unknown_status')
      expect(wrapper.vm.tagType).toBe('info')
    })
  })

  describe('自定义状态映射', () => {
    it('应该支持自定义状态映射', () => {
      const customMap = {
        custom: { text: '自定义状态', type: 'success' as const },
        special: { text: '特殊状态', type: 'warning' as const },
      }

      const wrapper = mount(StatusTag, {
        props: {
          status: 'custom',
          statusMap: customMap,
        },
      })

      expect(wrapper.text()).toBe('自定义状态')
      expect(wrapper.vm.tagType).toBe('success')
    })

    it('自定义映射应该覆盖默认映射', () => {
      const customMap = {
        active: { text: '已激活', type: 'info' as const },
      }

      const wrapper = mount(StatusTag, {
        props: {
          status: 'active',
          statusMap: customMap,
        },
      })

      expect(wrapper.text()).toBe('已激活')
      expect(wrapper.vm.tagType).toBe('info')
    })
  })

  describe('HTML 过滤', () => {
    it('应该过滤状态文本中的 HTML 标签', () => {
      const customMap = {
        xss: { text: '<script>alert("xss")</script>', type: 'info' as const },
      }

      const wrapper = mount(StatusTag, {
        props: {
          status: 'xss',
          statusMap: customMap,
        },
      })

      expect(wrapper.text()).not.toContain('<script>')
      expect(wrapper.text()).not.toContain('alert')
    })
  })

  describe('可访问性', () => {
    it('应该有正确的 role 属性', () => {
      const wrapper = mount(StatusTag, {
        props: {
          status: 'active',
        },
      })

      expect(wrapper.find('[role="status"]').exists()).toBe(true)
    })

    it('应该有正确的 aria-label', () => {
      const wrapper = mount(StatusTag, {
        props: {
          status: 'active',
        },
      })

      expect(wrapper.attributes('aria-label')).toBe('状态：启用')
    })
  })
})
