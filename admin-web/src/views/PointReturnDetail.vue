<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getReturnDetail,
  approveReturn,
  rejectReturn,
  type PointReturn,
  type ReturnStatus,
} from '@/api/pointReturn'
import { getPointOrderDetail, type PointOrder } from '@/api/pointShop'
import { formatDateTime } from '@/utils/format'

const route = useRoute()
const router = useRouter()

const returnId = computed(() => route.params.id as string)
const returnData = ref<PointReturn | null>(null)
const order = ref<PointOrder | null>(null)
const loading = ref(false)

async function loadData() {
  loading.value = true
  try {
    const data = await getReturnDetail(returnId.value)
    returnData.value = data

    // 加载关联订单信息
    if (data.order_id) {
      try {
        order.value = await getPointOrderDetail(data.order_id)
      } catch {
        // 忽略订单加载错误
      }
    }
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : '加载失败'
    ElMessage.error(errorMessage)
    router.push({ name: 'PointReturns' })
  } finally {
    loading.value = false
  }
}

async function handleApprove() {
  if (!returnData.value) return
  try {
    const { value: notes } = await ElMessageBox.prompt(
      '批准后将退还积分给用户，请输入备注信息',
      `批准退货申请 - ${returnData.value.order_number}`,
      {
        confirmButtonText: '确定批准',
        cancelButtonText: '取消',
        type: 'success',
        inputPlaceholder: '请输入备注信息（必填）',
        inputValidator: val => val && val.trim().length > 0,
        inputErrorMessage: '备注信息不能为空',
      }
    )
    await approveReturn(returnData.value.id, notes.trim())
    ElMessage.success('退货申请已批准，积分已退还')
    await loadData()
  } catch (e: unknown) {
    if (e === 'cancel') return
    const errorMessage = e instanceof Error ? e.message : '操作失败'
    ElMessage.error(errorMessage)
  }
}

async function handleReject() {
  if (!returnData.value) return
  try {
    const { value: notes } = await ElMessageBox.prompt(
      '请输入拒绝原因',
      `拒绝退货申请 - ${returnData.value.order_number}`,
      {
        confirmButtonText: '确定拒绝',
        cancelButtonText: '取消',
        type: 'warning',
        inputPlaceholder: '请输入拒绝原因（必填）',
        inputValidator: val => val && val.trim().length > 0,
        inputErrorMessage: '拒绝原因不能为空',
      }
    )
    await rejectReturn(returnData.value.id, notes.trim())
    ElMessage.success('退货申请已拒绝')
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

function goBack() {
  router.push({ name: 'PointReturns' })
}

function goToOrder() {
  if (order.value) {
    router.push({ name: 'PointOrderDetail', params: { id: order.value.id } })
  }
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="return-detail-container">
    <div class="page-content">
      <div class="page-header">
        <div class="header-left">
          <el-button link @click="goBack">
            <el-icon><ArrowLeft /></el-icon>
            返回
          </el-button>
          <h2>退货详情</h2>
        </div>
        <div v-if="returnData?.status === 'requested'" class="header-actions">
          <el-button type="success" @click="handleApprove">批准退货</el-button>
          <el-button type="warning" @click="handleReject">拒绝退货</el-button>
        </div>
      </div>

      <div v-loading="loading" class="info-section">
        <!-- 退货信息 -->
        <el-card class="info-card">
          <template #header>
            <div class="card-header">
              <span class="title">退货信息</span>
              <el-tag v-if="returnData" :type="getStatusType(returnData.status)" size="small">
                {{ getStatusText(returnData.status) }}
              </el-tag>
            </div>
          </template>
          <el-descriptions v-if="returnData" :column="2" border>
            <el-descriptions-item label="退货ID">{{ returnData.id }}</el-descriptions-item>
            <el-descriptions-item label="订单号">
              <el-link type="primary" @click="goToOrder">{{ returnData.order_number }}</el-link>
            </el-descriptions-item>
            <el-descriptions-item label="退货原因" :span="2">
              {{ returnData.reason }}
            </el-descriptions-item>
            <el-descriptions-item label="申请时间">
              {{ formatDateTime(returnData.created_at) }}
            </el-descriptions-item>
            <el-descriptions-item label="处理时间">
              {{ returnData.processed_at ? formatDateTime(returnData.processed_at) : '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="管理员备注" :span="2">
              {{ returnData.admin_notes || '-' }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- 关联订单信息 -->
        <el-card v-if="order" class="info-card">
          <template #header>
            <div class="card-header">
              <span class="title">关联订单</span>
              <el-link type="primary" @click="goToOrder">查看订单详情</el-link>
            </div>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="商品名称">{{ order.product_name }}</el-descriptions-item>
            <el-descriptions-item label="订单状态">
              <el-tag :type="order.status === 'completed' ? 'success' : 'warning'" size="small">
                {{ order.status === 'completed' ? '已完成' : order.status }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="积分">{{ order.points_cost }} 积分</el-descriptions-item>
            <el-descriptions-item label="现金">
              {{ order.cash_amount ? `¥${(order.cash_amount / 100).toFixed(2)}` : '免支付' }}
            </el-descriptions-item>
            <el-descriptions-item label="用户ID">{{ order.user_id }}</el-descriptions-item>
            <el-descriptions-item label="创建时间">{{ formatDateTime(order.created_at) }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </div>
    </div>
  </div>
</template>

<style scoped>
.return-detail-container {
  padding: 20px;
}

.page-content {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-left h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 500;
}

.info-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header .title {
  font-size: 16px;
  font-weight: 500;
}
</style>
