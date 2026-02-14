<!--
  StatusTag Component Stories
  展示不同状态的标签组件
-->
<script setup lang="ts">
import type { Meta, StoryObj } from '@storybook/vue3'
import StatusTag from './StatusTag.vue'

// 定义参数类型
interface Args {
  status: string
}

const meta: Meta<Args> = {
  title: 'Components/StatusTag',
  component: StatusTag,
  tags: ['autodocs'],
  argTypes: {
    status: {
      description: '状态值',
      control: 'select',
      options: [
        'active',
        'enabled',
        'normal',
        'paid',
        'approved',
        'disabled',
        'inactive',
        'pending',
        'rejected',
        'deleted',
        'cancelled',
      ],
      },
    },
  },
}

export default meta

const Template: StoryObj<Args> = {
  render: (args) => ({
    setup() {
      return { args }
    },
    components: { StatusTag },
    template: '<StatusTag :status="args.status" />',
  }),
}

// 基础示例
export const Active = {
  ...Template,
  args: {
    status: 'active',
  },
  parameters: {
    docs: {
      description: {
        story: '激活状态 - 显示为绿色成功标签',
      },
    },
  },
}

export const Enabled = {
  ...Template,
  args: {
    status: 'enabled',
  },
}

export const Pending = {
  ...Template,
  args: {
    status: 'pending',
  },
  parameters: {
    docs: {
      description: {
        story: '待处理状态 - 显示为蓝色信息标签',
      },
    },
  },
}

export const Disabled = {
  ...Template,
  args: {
    status: 'disabled',
  },
  parameters: {
    docs: {
      description: {
        story: '禁用状态 - 显示为黄色警告标签',
      },
    },
  },
}

export const Rejected = {
  ...Template,
  args: {
    status: 'rejected',
  },
  parameters: {
    docs: {
      description: {
        story: '已拒绝状态 - 显示为红色危险标签',
      },
    },
  },
}

export const Unknown = {
  ...Template,
  args: {
    status: 'custom_status',
  },
  parameters: {
    docs: {
      description: {
        story: '未知状态 - 显示原始状态文本和默认 info 类型',
      },
    },
  },
}

// 所有状态组合
export const AllStatuses = {
  render: () => ({
    components: { StatusTag },
    template: `
      <div style="display: flex; flex-direction: column; gap: 8px;">
        <StatusTag status="active" />
        <StatusTag status="enabled" />
        <StatusTag status="normal" />
        <StatusTag status="paid" />
        <StatusTag status="approved" />
        <StatusTag status="disabled" />
        <StatusTag status="inactive" />
        <StatusTag status="pending" />
        <StatusTag status="rejected" />
        <StatusTag status="deleted" />
        <StatusTag status="cancelled" />
        <StatusTag status="custom_status" />
      </div>
    `,
  }),
  parameters: {
    docs: {
      description: {
        story: '展示所有预定义状态标签',
      },
    },
  },
}
</script>
