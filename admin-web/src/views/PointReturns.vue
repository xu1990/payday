<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  listReturns,
  approveReturn,
  rejectReturn,
  type PointReturn,
  type ReturnStatus,
} from '@/api/pointReturn'
import { formatDateTime } from '@/utils/format'

const router = useRouter()
const list = ref<PointReturn[]>([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = 20
const statusFilter = ref<ReturnStatus | ''>('')
const dateRange = ref<[Date, Date] | null>(null)

// 状态选项
const statusOptions = [
  { label: '全部', value: '' },
  { label: '待处理', value: 'requested' },
  { label: '已同意', value: 'approved' },
  { label: '已拒绝', value: 'rejected' },
]

// 详情对话框
const detailDialogVisible = ref(false)
const currentReturn = ref<PointReturn | null>(null)

async function loadData() {
  loading.value = true
  try {
    const [start_date, end_date] = dateRange.value?.map(d => d.toISOString().split('T')[0]) || []
    const res = await listReturns({
      status: statusFilter.value || undefined,
      start_date,
      end_date,
      limit: pageSize,
      offset: (currentPage.value - 1) * pageSize,
    })
    list.value = res?.data?.returns || []
    total.value = res?.data?.total || 0
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : '加载失败'
    ElMessage.error(errorMessage)
  } finally {
    loading.value = false
  }
}

function handleStatusChange() {
  currentPage.value = 1
  loadData()
}

function handleDateChange() {
  currentPage.value = 1
  loadData()
}

function handleViewDetail(item: PointReturn) {
  router.push({ name: 'PointReturnDetail', params: { id: item.id } })
}

async function handleApprove(item: PointReturn) {
  try {
    const { value: notes } = await ElMessageBox.prompt(
      '批准后将退还积分给用户，请输入备注信息',
      `批准退货申请 - ${item.order_number}`,
      {
        confirmButtonText: '确定批准',
        cancelButtonText: '取消',
        type: 'success',
        inputPlaceholder: '请输入备注信息（必填）',
        inputValidator: val => val && val.trim().length > 0,
        inputErrorMessage: '备注信息不能为空',
      }
    )
    await approveReturn(item.id, notes.trim())
    ElMessage.success('退货申请已批准，积分已退还')
    detailDialogVisible.value = false
    await loadData()
  } catch (e: unknown) {
    if (e === 'cancel') return
    const errorMessage = e instanceof Error ? e.message : '操作失败'
    ElMessage.error(errorMessage)
  }
}

async function handleReject(item: PointReturn) {
  try {
    const { value: notes } = await ElMessageBox.prompt(
      '请输入拒绝原因',
      `拒绝退货申请 - ${item.order_number}`,
      {
        confirmButtonText: '确定拒绝',
        cancelButtonText: '取消',
        type: 'warning',
        inputPlaceholder: '请输入拒绝原因（必填）',
        inputValidator: val => val && val.trim().length > 0,
        inputErrorMessage: '拒绝原因不能为空',
      }
    )
    await rejectReturn(item.id, notes.trim())
    ElMessage.success('退货申请已拒绝')
    detailDialogVisible.value = false
    await loadData()
  } catch (e: unknown) {
    if (e === 'cancel') return
    const errorMessage = e instanceof Error ? e.message : '操作失败'
    ElMessage.error(errorMessage)
  }
}

function getStatusType(status: ReturnStatus) {
  switch (status) {
    case 'requested':
      return 'warning'
    case 'approved':
      return 'success'
    case 'rejected':
      return 'danger'
    default:
      return ''
  }
}

function getStatusText(status: ReturnStatus) {
  switch (status) {
    case 'requested':
      return '待处理'
    case 'approved':
      return '已同意'
    case 'rejected':
      return '已拒绝'
    default:
      return status
  }
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="point-returns-container">
    <div class="page-header">
      <h2>退货管理</h2>
      <div class="filter-group">
        <el-select
          v-model="statusFilter"
          placeholder="筛选状态"
          style="width: 150px; margin-right: 12px"
          @change="handleStatusChange"
        >
          <el-option
            v-for="item in statusOptions"
            :key="item.value"
            :label="item.label"
            :value="item.value"
          />
        </el-select>
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
          style="width: 240px"
          @change="handleDateChange"
        />
      </div>
    </div>

    <el-table v-loading="loading" :data="list" stripe>
      <el-table-column prop="order_number" label="订单号" width="200" />
      <el-table-column prop="reason" label="退货原因" min-width="180" show-overflow-tooltip />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)" size="small">
            {{ getStatusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="申请时间" width="180">
        <template #default="{ row }">
          {{ formatDateTime(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column prop="processed_at" label="处理时间" width="180">
        <template #default="{ row }">
          {{ row.processed_at ? formatDateTime(row.processed_at) : '-' }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click="handleViewDetail(row)">
            查看
          </el-button>
          <el-button
            v-if="row.status === 'requested'"
            link
            type="success"
            size="small"
            @click="handleApprove(row)"
          >
            批准
          </el-button>
          <el-button
            v-if="row.status === 'requested'"
            link
            type="warning"
            size="small"
            @click="handleReject(row)"
          >
            拒绝
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-wrapper">
      <el-pagination
        v-model:current-page="currentPage"
        :page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        @current-change="loadData"
      />
    </div>

    <!-- 详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="退货申请详情"
      width="600px"
      :close-on-click-modal="false"
    >
      <div v-if="currentReturn" class="return-detail">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="订单号">
            {{ currentReturn.order_number }}
          </el-descriptions-item>
          <el-descriptions-item label="退货原因">
            {{ currentReturn.reason }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(currentReturn.status)" size="small">
              {{ getStatusText(currentReturn.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="申请时间">
            {{ formatDateTime(currentReturn.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="处理时间">
            {{ currentReturn.processed_at ? formatDateTime(currentReturn.processed_at) : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="管理员备注">
            {{ currentReturn.admin_notes || '-' }}
          </el-descriptions-item>
        </el-descriptions>

        <!-- 操作按钮（仅待处理状态显示） -->
        <div v-if="currentReturn.status === 'requested'" class="action-buttons">
          <el-button type="success" @click="handleApprove(currentReturn)"> 批准退货 </el-button>
          <el-button type="warning" @click="handleReject(currentReturn)"> 拒绝退货 </el-button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<style scoped>
.point-returns-container {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 500;
}

.filter-group {
  display: flex;
  align-items: center;
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.return-detail {
  padding: 10px 0;
}

.action-buttons {
  margin-top: 24px;
  text-align: center;
}

.action-buttons .el-button {
  margin: 0 10px;
  width: 120px;
}
</style>
