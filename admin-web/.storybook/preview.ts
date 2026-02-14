/**
 * Storybook Preview 配置
 * 全局配置和装饰器
 */
import type { Preview } from '@storybook/vue3-vite'
import { withThemeByDataAttribute } from '@storybook/addon-themes'
import { themes } from '@storybook/theming'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import '../src/styles/design-tokens.css'

// 自定义主题
const lightTheme = {
  ...themes.light,
  base: 'light',
  default: true,
  appBg: '#f5f5f5',
  appContentBg: '#ffffff',
  appBorderColor: '#e0e0e0',
  textColor: '#1a1a1a',
  textInverseColor: '#ffffff',
  barTextColor: '#1a1a1a',
  barSelectedColor: '#409EFF',
  barBg: '#ffffff',
  inputBg: '#ffffff',
  inputBorder: '#dcdfe6',
}

const darkTheme = {
  ...themes.dark,
  base: 'dark',
  appBg: '#1a1a1a',
  appContentBg: '#242424',
  appBorderColor: '#333333',
  textColor: '#e0e0e0',
  textInverseColor: '#1a1a1a',
  barTextColor: '#e0e0e0',
  barSelectedColor: '#409EFF',
  barBg: '#1a1a1a',
  inputBg: '#2a2a2a',
  inputBorder: '#444444',
}

const preview: Preview = {
  parameters: {
    actions: { argTypesRegex: '^on[A-Z].*' },
    controls: {
      matchers: {
        color: /(background|textColor)$/i,
        date: /Date$/,
      },
    },
    backgrounds: {
      default: 'light',
      values: [
        { name: 'light', value: '#ffffff' },
        { name: 'dark', value: '#1a1a1a' },
      ],
    },
  },
  globalTypes: [
    // 全局类型定义
    { name: 'Router', type: { name: 'Router', value: {} } },
    { name: 'Pinia', type: { name: 'Pinia', value: {} } },
  ],
  decorators: [
    // 模拟 Vue Router
    (story, context) => {
      // 创建 mock router
      const mockRouter = {
        push: () => {},
        replace: () => {},
        go: () => {},
        back: () => {},
        forward: () => {},
        currentRoute: {
          value: { path: '/', params: {}, query: {} },
        },
      }

      // 提供给所有 stories
      ;(context as any).router = mockRouter

      return story()
    },
    // 模拟 Pinia store
    (story, context) => {
      // 创建 mock store
      const mockStore = {
        user: null,
        accessToken: '',
        refreshToken: '',
        csrfToken: '',
        isAuthenticated: false,
      }

      ;(context as any).store = mockStore

      return story()
    },
    withThemeByDataAttribute({
      themes: {
        light: lightTheme,
        dark: darkTheme,
      },
      defaultTheme: 'light',
    }),
  ],
}

export default preview
