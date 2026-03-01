<template>
  <div class="notification-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>消息列表</span>
          <el-button type="primary" @click="$router.push('/system-messages')">
            发送系统消息
          </el-button>
        </div>
      </template>

      <!-- 筛选条件 -->
      <el-form :inline="true" :model="filters" class="filter-form">
        <el-form-item label="消息类型">
          <el-select v-model="filters.type" placeholder="全部类型" clearable style="width: 120px">
            <el-option label="评论" value="comment" />
            <el-option label="回复" value="reply" />
            <el-option label="点赞" value="like" />
            <el-option label="关注" value="follow" />
            <el-option label="系统" value="system" />
          </el-select>
        </el-form-item>
        <el-form-item label="阅读状态">
          <el-select v-model="filters.isRead" placeholder="全部" clearable style="width: 100px">
            <el-option label="已读" :value="true" />
            <el-option label="未读" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item label="用户ID">
          <el-input v-model="filters.user_id" placeholder="输入用户ID" clearable style="width: 200px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 消息表格 -->
      <el-table :data="notifications" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="280" />
        <el-table-column prop="user_id" label="接收用户" width="280" />
        <el-table-column prop="type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getTypeTagType(row.type)" size="small">
              {{ getTypeLabel(row.type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="标题" min-width="150" />
        <el-table-column prop="content" label="内容" min-width="200">
          <template #default="{ row }">
            <span class="content-text">{{ row.content || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="is_read" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_read ? 'success' : 'warning'" size="small">
              {{ row.is_read ? '已读' : '未读' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { getNotifications, type AdminNotificationItem } from '@/api/admin'

const loading = ref(false)
const notifications = ref<AdminNotificationItem[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

const filters = reactive({
  type: '',
  isRead: undefined as boolean | undefined,
  user_id: ''
})

const typeLabels: Record<string, string> = {
  comment: '评论',
  reply: '回复',
  like: '点赞',
  follow: '关注',
  system: '系统'
}

const typeTagTypes: Record<string, string> = {
  comment: 'primary',
  reply: 'primary',
  like: 'danger',
  follow: 'success',
  system: 'info'
}

function getTypeLabel(type: string): string {
  return typeLabels[type] || type
}

function getTypeTagType(type: string): string {
  return typeTagTypes[type] || ''
}

function formatTime(time: string): string {
  if (!time) return ''
  return new Date(time).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

async function loadData() {
  loading.value = true
  try {
    const params: Record<string, any> = {
      limit: pageSize.value,
      offset: (currentPage.value - 1) * pageSize.value
    }

    if (filters.type) params.type = filters.type
    if (filters.isRead !== undefined) params.is_read = filters.isRead
    if (filters.user_id) params.user_id = filters.user_id

    const result = await getNotifications(params)
    notifications.value = result.items
    total.value = result.total
  } catch (error) {
    console.error('加载消息列表失败:', error)
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  currentPage.value = 1
  loadData()
}

function handleReset() {
  filters.type = ''
  filters.isRead = undefined
  filters.user_id = ''
  currentPage.value = 1
  loadData()
}

function handleSizeChange(size: number) {
  pageSize.value = size
  currentPage.value = 1
  loadData()
}

function handlePageChange(page: number) {
  currentPage.value = page
  loadData()
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.notification-list {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-form {
  margin-bottom: 20px;
}

.content-text {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
