<!--
  BaseDataTable Component Stories
  带分页的数据表格组件
-->
<script setup lang="ts">
import type { Meta, StoryObj } from '@storybook/vue3'
import { ref } from 'vue'
import BaseDataTable from './BaseDataTable.vue'

interface Args {
  loading?: boolean
  empty?: boolean
  data?: any[]
  columns?: any[]
}

const meta: Meta<Args> = {
  title: 'Components/BaseDataTable',
  component: BaseDataTable,
  tags: ['autodocs'],
  argTypes: {
    loading: {
      description: '是否加载中',
      control: 'boolean',
    },
    empty: {
      description: '是否为空数据',
      control: 'boolean',
    },
  },
}

export default meta

const mockData = [
  { id: 1, name: '张三', status: 'active', email: 'zhangsan@example.com' },
  { id: 2, name: '李四', status: 'disabled', email: 'lisi@example.com' },
  { id: 3, name: '王五', status: 'pending', email: 'wangwu@example.com' },
]

const mockColumns = [
  { key: 'id', label: 'ID', width: 80 },
  { key: 'name', label: '姓名', width: 120 },
  { key: 'email', label: '邮箱', width: 200 },
  {
    key: 'status',
    label: '状态',
    width: 100,
    formatter: (row: any) => row.status,
  },
]

const Template: StoryObj<Args> = {
  render: (args) => ({
    setup() {
      const data = ref(args.data || mockData)
      const columns = ref(args.columns || mockColumns)
      return { args, data, columns }
    },
    components: { BaseDataTable },
    template: `
      <BaseDataTable
        :data="data"
        :columns="columns"
        :loading="args.loading"
        :empty="args.empty"
      />
    `,
  }),
}

export const Default = {
  ...Template,
  args: {
    loading: false,
    empty: false,
  },
  parameters: {
    docs: {
      description: {
        story: '默认状态 - 显示数据表格',
      },
    },
  },
}

export const Loading = {
  ...Template,
  args: {
    loading: true,
    empty: false,
  },
  parameters: {
    docs: {
      description: {
        story: '加载状态 - 显示加载指示器',
      },
    },
  },
}

export const Empty = {
  ...Template,
  args: {
    loading: false,
    empty: true,
    data: [],
  },
  parameters: {
    docs: {
      description: {
        story: '空状态 - 显示空数据提示',
      },
    },
  },
}

export const WithPagination = {
  ...Template,
  render: () => ({
    setup() {
      const data = ref(mockData)
      const columns = ref(mockColumns)
      const total = ref(100)
      const page = ref(1)
      const pageSize = ref(20)

      const handlePageChange = (newPage: number) => {
        page.value = newPage
        console.log('Page changed to:', newPage)
      }

      return { data, columns, total, page, pageSize, handlePageChange }
    },
    components: { BaseDataTable },
    template: `
      <BaseDataTable
        :data="data"
        :columns="columns"
        :total="total"
        :page="page"
        :pageSize="pageSize"
        @page-change="handlePageChange"
      />
    `,
  }),
  parameters: {
    docs: {
      description: {
        story: '带分页的表格 - 显示总数和页码切换',
      },
    },
  },
}
</script>
