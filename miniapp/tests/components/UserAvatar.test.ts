import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import UserAvatar from '@/components/UserAvatar.vue'

describe('UserAvatar', () => {
  it('renders avatar image when avatar prop is provided', () => {
    const wrapper = mount(UserAvatar, {
      props: {
        avatar: 'https://example.com/avatar.jpg',
        anonymousName: 'TestUser'
      }
    })

    const image = wrapper.find('image')
    expect(image.exists()).toBe(true)
    expect(image.attributes('src')).toBe('https://example.com/avatar.jpg')
  })

  it('renders placeholder when avatar is null', () => {
    const wrapper = mount(UserAvatar, {
      props: {
        avatar: null,
        anonymousName: 'TestUser'
      }
    })

    const placeholder = wrapper.find('.avatar-placeholder')
    expect(placeholder.exists()).toBe(true)
    expect(placeholder.text()).toBe('T')
  })

  it('renders question mark when anonymous_name is empty', () => {
    const wrapper = mount(UserAvatar, {
      props: {
        avatar: null,
        anonymousName: ''
      }
    })

    const placeholder = wrapper.find('.avatar-placeholder')
    expect(placeholder.text()).toBe('?')
  })

  it('applies correct size class', () => {
    const wrapper = mount(UserAvatar, {
      props: {
        avatar: null,
        anonymousName: 'Test',
        size: 'small'
      }
    })

    expect(wrapper.find('.small').exists()).toBe(true)
  })
})
