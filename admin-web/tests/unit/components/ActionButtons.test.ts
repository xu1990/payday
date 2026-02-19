/**
 * ActionButtons 组件单元测试
 * 测试操作按钮组组件
 */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ActionButtons from '@/components/ActionButtons.vue'

describe('ActionButtons 组件', () => {
  describe('按钮显示控制', () => {
    it('默认显示所有按钮', () => {
      const wrapper = mount(ActionButtons)

      expect(wrapper.find('[aria-label="编辑"]').exists()).toBe(true)
      expect(wrapper.text()).toContain('编辑')
      // 默认 isActive=true，所以显示"禁用"按钮
      expect(wrapper.text()).toContain('禁用')
      expect(wrapper.text()).toContain('删除')
    })

    it('showEdit 为 false 时隐藏编辑按钮', () => {
      const wrapper = mount(ActionButtons, {
        props: {
          showEdit: false,
        },
      })

      expect(wrapper.find('[aria-label="编辑"]').exists()).toBe(false)
      expect(wrapper.text()).not.toContain('编辑')
    })

    it('showToggle 为 false 时隐藏切换按钮', () => {
      const wrapper = mount(ActionButtons, {
        props: {
          showToggle: false,
        },
      })

      expect(wrapper.find('[aria-label="启用"]').exists()).toBe(false)
      expect(wrapper.find('[aria-label="禁用"]').exists()).toBe(false)
      expect(wrapper.text()).not.toContain('启用')
      expect(wrapper.text()).not.toContain('禁用')
    })

    it('showDelete 为 false 时隐藏删除按钮', () => {
      const wrapper = mount(ActionButtons, {
        props: {
          showDelete: false,
        },
      })

      expect(wrapper.find('[aria-label="删除"]').exists()).toBe(false)
      expect(wrapper.text()).not.toContain('删除')
    })
  })

  describe('切换按钮状态', () => {
    it('isActive 为 true 时显示禁用按钮', () => {
      const wrapper = mount(ActionButtons, {
        props: {
          isActive: true,
        },
      })

      expect(wrapper.text()).toContain('禁用')
      expect(wrapper.find('[aria-label="禁用"]').exists()).toBe(true)
    })

    it('isActive 为 false 时显示启用按钮', () => {
      const wrapper = mount(ActionButtons, {
        props: {
          isActive: false,
        },
      })

      expect(wrapper.text()).toContain('启用')
      expect(wrapper.find('[aria-label="启用"]').exists()).toBe(true)
    })
  })

  describe('事件触发', () => {
    it('点击编辑按钮触发 edit 事件', async () => {
      const wrapper = mount(ActionButtons)

      const editButton = wrapper.find('[aria-label="编辑"]')
      await editButton.trigger('click')

      expect(wrapper.emitted('edit')).toBeTruthy()
      expect(wrapper.emitted('edit')?.length).toBe(1)
    })

    it('点击切换按钮触发 toggle 事件', async () => {
      const wrapper = mount(ActionButtons)

      // 默认 isActive=true，所以找"禁用"按钮
      const toggleButton = wrapper.find('[aria-label="禁用"]')
      await toggleButton.trigger('click')

      expect(wrapper.emitted('toggle')).toBeTruthy()
      expect(wrapper.emitted('toggle')?.length).toBe(1)
    })

    it('点击删除按钮触发 delete 事件', async () => {
      const wrapper = mount(ActionButtons)

      const deleteButton = wrapper.find('[aria-label="删除"]')
      await deleteButton.trigger('click')

      expect(wrapper.emitted('delete')).toBeTruthy()
      expect(wrapper.emitted('delete')?.length).toBe(1)
    })
  })

  describe('插槽支持', () => {
    it('应该渲染默认插槽内容', () => {
      const wrapper = mount(ActionButtons, {
        slots: {
          default: '<button class="custom-button">自定义按钮</button>',
        },
      })

      expect(wrapper.find('.custom-button').exists()).toBe(true)
      expect(wrapper.text()).toContain('自定义按钮')
    })
  })

  describe('可访问性', () => {
    it('应该有正确的 ARIA 角色标签', () => {
      const wrapper = mount(ActionButtons)

      const container = wrapper.find('[role="group"]')
      expect(container.exists()).toBe(true)
    })

    it('应该有正确的 ARIA 标签', () => {
      const wrapper = mount(ActionButtons)

      expect(wrapper.find('[aria-label="编辑"]').exists()).toBe(true)
      // 默认 isActive=true，所以期待"禁用"标签
      expect(wrapper.find('[aria-label="禁用"]').exists()).toBe(true)
      expect(wrapper.find('[aria-label="删除"]').exists()).toBe(true)
    })
  })

  describe('样式和类名', () => {
    it('应该有 action-buttons 类名', () => {
      const wrapper = mount(ActionButtons)

      expect(wrapper.classes()).toContain('action-buttons')
    })
  })
})
