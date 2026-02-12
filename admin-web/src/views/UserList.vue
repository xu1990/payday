<template>
  <div>
    <h2 class="page-title">用户管理</h2>
    <div class="toolbar">
      <el-input
        v-model="keyword"
        placeholder="匿名昵称关键词"
        clearable
        style="width: 200px"
        @keyup.enter="onSearch"
      />
      <el-select v-model="statusFilter" placeholder="状态" clearable style="width: 120px">
        <el-option label="全部" value="" />
        <el-option label="正常" value="normal" />
        <el-option label="禁用" value="disabled" />
      </el-select>
      <el-button type="primary" @click="onSearch">搜索</el-button>
    </div>
    <el-table v-loading="loading" :data="items" stripe>
      <el-table-column prop="anonymous_name" label="匿名昵称" width="140" />
      <el-table-column prop="openid" label="OpenID" min-width="200" show-overflow-tooltip />
      <el-table-column prop="status" label="状态" width="100" />
      <el-table-column prop="created_at" label="注册时间" width="180">
        <template #default="{ row }">
          {{ row.created_at ? formatDate(row.created_at) : '-' }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="100" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" link @click="goDetail(row.id)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination
      v-model:current-page="page"
      v-model:page-size="pageSize"
      :total="total"
      :page-sizes="[10, 20, 50]"
      layout="total, sizes, prev, pager, next"
      class="pagination"
      @current-change="fetch"
      @size-change="fetch"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { getUsers, type AdminUserListItem } from '@/api/admin'

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

function formatDate(s: string) {
  try {
    return new Date(s).toLocaleString('zh-CN')
  } catch {
    return s
  }
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
.toolbar { margin-bottom: 16px; display: flex; gap: 8px; align-items: center; }
.pagination { margin-top: 16px; justify-content: flex-end; }
</style>
