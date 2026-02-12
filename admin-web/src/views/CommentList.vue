<template>
  <div>
    <h2 class="page-title">评论管理</h2>
    <div class="toolbar" role="search" aria-label="评论筛选工具栏">
      <el-input v-model="filterPostId" placeholder="帖子 ID" clearable style="width: 280px" aria-label="按帖子ID筛选" />
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
      table-label="评论列表"
      @page-change="fetch"
    >
      <el-table-column prop="id" label="ID" width="280" show-overflow-tooltip />
      <el-table-column prop="post_id" label="帖子ID" width="280" show-overflow-tooltip />
      <el-table-column prop="anonymous_name" label="匿名昵称" width="120" />
      <el-table-column prop="content" label="内容" min-width="200" show-overflow-tooltip />
      <el-table-column prop="like_count" label="点赞" width="70" />
      <el-table-column prop="risk_status" label="风控" width="80">
        <template #default="{ row }">
          <StatusTag :status="row.risk_status" />
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="170">
        <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <template v-if="row.risk_status === 'pending'">
            <el-button type="success" link aria-label="通过该评论" @click="approve(row)">通过</el-button>
            <el-button type="warning" link aria-label="拒绝该评论" @click="reject(row)">拒绝</el-button>
          </template>
        </template>
      </el-table-column>
    </BaseDataTable>

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
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  getComments,
  updateCommentRisk,
  type AdminCommentListItem,
} from '@/api/admin'
import BaseDataTable from '@/components/BaseDataTable.vue'
import StatusTag from '@/components/StatusTag.vue'

const loading = ref(false)
const items = ref<AdminCommentListItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const filterPostId = ref('')
const filterRiskStatus = ref<string>('')
const rejectVisible = ref(false)
const rejectReason = ref('')
let rejectTarget: AdminCommentListItem | null = null

// 本地格式化函数（修复：移除导入冲突）
function formatDate(s: string | null) {
  if (!s) return '-'
  try {
    return new Date(s).toLocaleString('zh-CN')
  } catch {
    return s
  }
}

async function approve(row: AdminCommentListItem) {
  try {
    await updateCommentRisk(row.id, { risk_status: 'approved' })
    ElMessage.success('已通过')
    await fetch()
  } catch (e: unknown) {
    const err = e as { response?: { status: number } }
    ElMessage.error(err.response?.status === 404 ? '评论不存在' : '操作失败')
  }
}

function reject(row: AdminCommentListItem) {
  rejectTarget = row
  rejectReason.value = ''
  rejectVisible.value = true
}

async function confirmReject() {
  if (!rejectTarget) return
  try {
    await updateCommentRisk(rejectTarget.id, {
      risk_status: 'rejected',
      risk_reason: rejectReason.value || undefined,
    })
    ElMessage.success('已拒绝')
    rejectVisible.value = false
    rejectTarget = null
    await fetch()
  } catch (e: unknown) {
    const err = e as { response?: { status: number } }
    ElMessage.error(err.response?.status === 404 ? '评论不存在' : '操作失败')
  }
}

async function fetch() {
  loading.value = true
  try {
    const params: { limit: number; offset: number; post_id?: string; risk_status?: string } = {
      limit: pageSize.value,
      offset: (page.value - 1) * pageSize.value,
    }
    if (filterPostId.value) params.post_id = filterPostId.value
    if (filterRiskStatus.value) params.risk_status = filterRiskStatus.value
    const { data } = await getComments(params)
    items.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

onMounted(fetch)
</script>
