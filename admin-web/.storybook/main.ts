/**
 * Storybook 主配置文件
 * 配置 Storybook 用于 Vue 3 + TypeScript + Element Plus
 */
import type { StorybookConfig } from '@storybook/vue3-vite'
import { viteResolve } from '@storybook/api-vite'

const config: StorybookConfig = {
  stories: [
    // 自动发现所有 stories
    '../src/**/*.mdx',
    '../src/**/*.stories.@(js|jsx|ts|tsx|vue)',
  ],
  addons: [
    '@storybook/addon-links',
    '@storybook/addon-essentials',
    '@storybook/addon-interactions',
    '@storybook/addon-themes',
    '@storybook/addon-docs',
  ],
  framework: {
    name: '@storybook/vue3-vite',
    options: {},
  },
  docs: {
    autodocs: 'tag',
  },
  typescript: {
    reactDocgen: 'react-docgen-typescript',
    reactDocgenTypescriptOptions: {
      shouldExtractLiteralValuesFromEnum: true,
      propFilter: (prop) => (prop.parent ? !prop.parent.name.startsWith('HTML') : true),
    },
  },
  async viteFinal(viteConfig) {
    // 配置路径别名
    viteConfig.resolve = viteConfig.resolve || {}
    viteConfig.resolve.alias = {
      ...viteConfig.resolve.alias,
      '@': '/src',
    }

    return viteConfig
  },
}

export default config
