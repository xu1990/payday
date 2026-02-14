<!--
  ActionButtons Component Stories
  操作按钮组组件
-->
<script setup lang="ts">
import type { Meta, StoryObj } from '@storybook/vue3'
import ActionButtons from './ActionButtons.vue'

interface Args {
  showEdit?: boolean
  showToggle?: boolean
  showDelete?: boolean
  isActive?: boolean
}

const meta: Meta<Args> = {
  title: 'Components/ActionButtons',
  component: ActionButtons,
  tags: ['autodocs'],
  argTypes: {
    showEdit: {
      description: '是否显示编辑按钮',
      control: 'boolean',
    },
    showToggle: {
      description: '是否显示切换按钮',
      control: 'boolean',
    },
    showDelete: {
      description: '是否显示删除按钮',
      control: 'boolean',
    },
    isActive: {
      description: '是否激活状态（影响切换按钮文本）',
      control: 'boolean',
    },
  },
}

export default meta

const Template: StoryObj<Args> = {
  render: (args) => ({
    setup() {
      return { args }
    },
    components: { ActionButtons },
    template: `
      <ActionButtons
        :showEdit="args.showEdit"
        :showToggle="args.showToggle"
        :showDelete="args.showDelete"
        :isActive="args.isActive"
        @edit="() => console.log('Edit clicked')"
        @toggle="() => console.log('Toggle clicked')"
        @delete="() => console.log('Delete clicked')"
      />
    `,
  }),
}

// 基础示例
export const Default = {
  ...Template,
  args: {
    showEdit: true,
    showToggle: true,
    showDelete: true,
    isActive: true,
  },
  parameters: {
    docs: {
      description: {
        story: '默认配置 - 显示所有按钮，激活状态',
      },
    },
  },
}

export const AllButtonsVisible = {
  ...Template,
  args: {
    showEdit: true,
    showToggle: true,
    showDelete: true,
    isActive: false,
  },
  parameters: {
    docs: {
      description: {
        story: '所有按钮可见，未激活状态',
      },
    },
  },
}

export const OnlyEditAndDelete = {
  ...Template,
  args: {
    showEdit: true,
    showToggle: false,
    showDelete: true,
  },
  parameters: {
    docs: {
      description: {
        story: '仅显示编辑和删除按钮',
      },
    },
  },
}

export const OnlyDelete = {
  ...Template,
  args: {
    showEdit: false,
    showToggle: false,
    showDelete: true,
  },
  parameters: {
    docs: {
      description: {
        story: '仅显示删除按钮（危险操作）',
      },
    },
  },
}

export const WithCustomSlot = {
  ...Template,
  args: {
    showEdit: false,
    showToggle: false,
    showDelete: false,
  },
  render: (args) => ({
    setup() {
      return { args }
    },
    components: { ActionButtons },
    template: `
      <ActionButtons
        :showEdit="args.showEdit"
        :showToggle="args.showToggle"
        :showDelete="args.showDelete"
      >
        <el-button link size="small" type="info">查看详情</el-button>
        <el-button link size="small" type="warning">导出</el-button>
      </ActionButtons>
    `,
  }),
  parameters: {
    docs: {
      description: {
        story: '使用自定义插槽添加额外按钮',
      },
    },
  },
}
</script>
