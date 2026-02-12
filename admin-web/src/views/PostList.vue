<template>
  <div>
    <h2 class="page-title">帖子管理</h2>
    <div class="toolbar" role="search" aria-label="帖子筛选工具栏">
      <el-select v-model="filterStatus" placeholder="状态" clearable style="width: 120px" aria-label="按状态筛选">
        <el-option label="正常" value="normal" />
        <el-option label="已隐藏" value="hidden" />
        <el-option label="已删除" value="deleted" />
      </el-select>
      <el-select v-model="filterRiskStatus" placeholder="风控状态" clearable style="width: 120px" aria-label="按风控状态筛选">
        <el-option label="待审" value="pending" />
        <el-option label="通过" value="approved" />
        <el-option label="拒绝" value="rejected" />
      </el-select>
      <el-button type="primary" aria-label="执行查询" @click="fetch">查询</el-button>
    </div>

    <BaseDataTable
      v-model:current-page="page"
      v-model:page-size="pageSize"
      :items="items"
      :total="total"
      :loading="loading"
      table-label="帖子列表"
      @page-change="fetch"
    >
      <el-table-column prop="id" label="ID" width="280" show-overflow-tooltip />
      <el-table-column prop="anonymous_name" label="匿名昵称" width="120" />
      <el-table-column prop="content" label="内容" min-width="200" show-overflow-tooltip />
      <el-table-column prop="type" label="类型" width="90" />
      <el-table-column prop="view_count" label="浏览" width="70" />
      <el-table-column prop="like_count" label="点赞" width="70" />
      <el-table-column prop="comment_count" label="评论" width="70" />
      <el-table-column prop="status" label="状态" width="80">
        <template #default="{ row }">
          <StatusTag :status="row.status" />
        </template>
      </el-table-column>
      <el-table-column prop="risk_status" label="风控" width="80">
        <template #default="{ row }">
          <StatusTag :status="row.risk_status" />
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="170">
        <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="260" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" link aria-label="查看帖子详情" @click="openDetail(row)">详情</el-button>
          <template v-if="row.risk_status === 'pending'">
            <el-button type="success" link aria-label="通过该帖子" @click="approve(row)">通过</el-button>
            <el-button type="warning" link aria-label="拒绝该帖子" @click="reject(row)">拒绝</el-button>
          </template>
          <el-button v-if="row.status === 'normal'" type="warning" link aria-label="隐藏该帖子" @click="hide(row)">隐藏</el-button>
          <el-button type="danger" link aria-label="删除该帖子" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </BaseDataTable>

    <el-dialog v-model="detailVisible" title="帖子详情" width="600px" aria-label="帖子详情对话框">
      <template v-if="currentPost">
        <p><strong>ID：</strong>{{ currentPost.id }}</p>
        <p><strong>匿名昵称：</strong>{{ currentPost.anonymous_name }}</p>
        <p><strong>类型：</strong>{{ currentPost.type }}</p>
        <p><strong>内容：</strong></p>
        <div class="content-block">{{ currentPost.content }}</div>
        <p v-if="currentPost.images?.length">图片：{{ currentPost.images.length }} 张</p>
        <p><strong>浏览/点赞/评论：</strong>{{ currentPost.view_count }} / {{ currentPost.like_count }} / {{ currentPost.comment_count }}</p>
        <p><strong>状态 / 风控：</strong>{{ currentPost.status }} / {{ currentPost.risk_status }}</p>
        <p v-if="currentPost.risk_reason"><strong>风控原因：</strong>{{ currentPost.risk_reason }}</p>
      </template>
    </el-dialog>

    <el-dialog v-model="rejectVisible" title="拒绝原因" width="400px" aria-label="拒绝原因对话框">
      <el-input v-model="rejectReason" type="textarea" placeholder="选填" :rows="3" aria-label="拒绝原因" />
      <template #footer>
        <el-button aria-label="取消拒绝" @click="rejectVisible = false">取消</el-button>
        <el-button type="primary" aria-label="确认拒绝" @click="confirmReject">确定拒绝</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getPosts,
  updatePostStatus,
  deletePost,
  type AdminPostListItem,
} from '@/api/admin'
import BaseDataTable from '@/components/BaseDataTable.vue'
import StatusTag from '@/components/StatusTag.vue'
import { getCommonApiErrorMessage } from '@/utils/error'

const loading = ref(false)
const items = ref<AdminPostListItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const filterStatus = ref<string>('')
const filterRiskStatus = ref<string>('')
const detailVisible = ref(false)
const currentPost = ref<AdminPostListItem | null>(null)
const rejectVisible = ref(false)
const rejectReason = ref('')
let rejectTarget: AdminPostListItem | null = null

function formatDate(s: string | null) {
  if (!s) return '-'
  try {
    return new Date(s).toLocaleString('zh-CN')
  } catch {
    return s
  }
}

function openDetail(row: AdminPostListItem) {
  currentPost.value = row
  detailVisible.value = true
}

async function approve(row: AdminPostListItem) {
  try {
    await updatePostStatus(row.id, { risk_status: 'approved' })
    ElMessage.success('已通过')
    await fetch()
  } catch (e: unknown) {
    ElMessage.error(getCommonApiErrorMessage(e))
  }
}

function reject(row: AdminPostListItem) {
  rejectTarget = row
  rejectReason.value = ''
  rejectVisible.value = true
}

async function confirmReject() {
  if (!rejectTarget) return
  try {
    await updatePostStatus(rejectTarget.id, {
      risk_status: 'rejected',
      risk_reason: rejectReason.value || undefined,
    })
    ElMessage.success('已拒绝')
    rejectVisible.value = false
    rejectTarget = null
    await fetch()
  } catch (e: unknown) {
    ElMessage.error(getCommonApiErrorMessage(e))
  }
}

async function hide(row: AdminPostListItem) {
  try {
    await ElMessageBox.confirm('确定隐藏该帖子？', '提示', { type: 'warning' })
  } catch {
    return
  }
  try {
    await updatePostStatus(row.id, { status: 'hidden' })
    ElMessage.success('已隐藏')
    await fetch()
  } catch (e: unknown) {
    ElMessage.error(getCommonApiErrorMessage(e))
  }
}

async function onDelete(row: AdminPostListItem) {
  try {
    await ElMessageBox.confirm('确定删除该帖子？', '提示', { type: 'warning' })
  } catch {
    return
  }
  try {
    await deletePost(row.id)
    ElMessage.success('已删除')
    await fetch()
  } catch (e: unknown) {
    ElMessage.error(getCommonApiErrorMessage(e))
  }
}

async function fetch() {
  loading.value = true
  try {
    const params: { limit: number; offset: number; status?: string; risk_status?: string } = {
      limit: pageSize.value,
      offset: (page.value - 1) * pageSize.value,
    }
    if (filterStatus.value) params.status = filterStatus.value
    if (filterRiskStatus.value) params.risk_status = filterRiskStatus.value
    const { data } = await getPosts(params)
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
.content-block { white-space: pre-wrap; background: var(--color-bg-base); padding: var(--spacing-md); border-radius: var(--radius-sm); margin: var(--spacing-sm) 0; }
</style>
