<template>
  <div>
    <h2 class="page-title" id="page-title">用户管理</h2>
    <SearchToolbar
      v-model:keyword="keyword"
      @search="onSearch"
    >
      <el-select v-model="statusFilter" placeholder="状态" clearable style="width: var(--input-width-md)">
        <el-option label="全部" value="" />
        <el-option label="正常" value="normal" />
        <el-option label="禁用" value="disabled" />
      </el-select>
    </SearchToolbar>

    <BaseDataTable
      v-model:current-page="page"
      v-model:page-size="pageSize"
      :items="items"
      :total="total"
      :loading="loading"
      table-label="用户列表"
      @page-change="fetch"
    >
      <el-table-column prop="anonymous_name" label="匿名昵称" width="140" />
      <el-table-column prop="openid" label="OpenID" min-width="200" show-overflow-tooltip />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <StatusTag :status="row.status" />
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="注册时间" width="180">
        <template #default="{ row }">
          {{ row.created_at ? formatDate(row.created_at) : '-' }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="100" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" link aria-label="查看用户详情" @click="goDetail(row.id)">详情</el-button>
        </template>
      </el-table-column>
    </BaseDataTable>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { getUsers, type AdminUserListItem } from '@/api/admin'
import BaseDataTable from '@/components/BaseDataTable.vue'
import SearchToolbar from '@/components/SearchToolbar.vue'
import StatusTag from '@/components/StatusTag.vue'
import { formatDate } from '@/utils/format'

const router = useRouter()
const loading = ref(false)
const items = ref<AdminUserListItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const keyword = ref('')
const statusFilter = ref('')

function onSearch() {
  page.value = 1
  fetch()
}

function goDetail(id: string) {
  router.push({ name: 'UserDetail', params: { id } })
}

async function fetch() {
  loading.value = true
  try {
    const params: { limit: number; offset: number; keyword?: string; status?: string } = {
      limit: pageSize.value,
      offset: (page.value - 1) * pageSize.value,
    }
    if (keyword.value) params.keyword = keyword.value
    if (statusFilter.value) params.status = statusFilter.value
    const { data } = await getUsers(params)
    items.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

onMounted(fetch)
watch([page, pageSize], fetch)
</script>

<style scoped>
.page-title { margin-bottom: 16px; font-size: 18px; }
</style>
