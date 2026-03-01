<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getShipmentDetail,
  updateShipment,
  deleteShipment,
  getTracking,
  type PointShipment,
  type TrackingEvent,
  type PointShipmentUpdate,
} from '@/api/pointShipment'
import { formatDateTime } from '@/utils/format'
import { getPointOrderDetail, type PointOrder } from '@/api/pointShop'

const route = useRoute()
const router = useRouter()

const shipmentId = computed(() => route.params.id as string)
const shipment = ref<PointShipment | null>(null)
const order = ref<PointOrder | null>(null)
const loading = ref(false)
const trackingLoading = ref(false)
const trackingEvents = ref<TrackingEvent[]>([])

// 编辑相关
const editDialogVisible = ref(false)
const editFormRef = ref()
const editForm = ref<PointShipmentUpdate>({
  tracking_number: '',
  status: undefined,
  notes: '',
})

const statusOptions = [
  { label: '待发货', value: 'pending' },
  { label: '已揽收', value: 'picked_up' },
  { label: '运输中', value: 'in_transit' },
  { label: '已送达', value: 'delivered' },
  { label: '失败', value: 'failed' },
]

async function loadData() {
  loading.value = true
  try {
    const data = await getShipmentDetail(shipmentId.value)
    shipment.value = data

    // 加载关联订单信息
    if (data.order_id) {
      try {
        order.value = await getPointOrderDetail(data.order_id)
      } catch {
        // 忽略订单加载错误
      }
    }

    // 加载物流跟踪信息
    await loadTracking()
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : '加载失败'
    ElMessage.error(errorMessage)
  } finally {
    loading.value = false
  }
}

async function loadTracking() {
  if (!shipment.value) return
  trackingLoading.value = true
  try {
    const res = await getTracking(shipment.value.id)
    trackingEvents.value = res?.tracking_info || []
  } catch {
    trackingEvents.value = []
  } finally {
    trackingLoading.value = false
  }
}

function openEditDialog() {
  if (!shipment.value) return
  editForm.value = {
    tracking_number: shipment.value.tracking_number,
    status: shipment.value.status,
    notes: shipment.value.notes || '',
  }
  editDialogVisible.value = true
}

async function handleEdit() {
  if (!shipment.value) return
  try {
    await editFormRef.value.validate()
    await updateShipment(shipment.value.id, editForm.value)
    ElMessage.success('发货记录已更新')
    editDialogVisible.value = false
    await loadData()
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : '更新失败'
    ElMessage.error(errorMessage)
  }
}

async function handleDelete() {
  if (!shipment.value) return
  try {
    await ElMessageBox.confirm(
      `确定删除订单"${shipment.value.order_number}"的发货记录吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    await deleteShipment(shipment.value.id)
    ElMessage.success('发货记录已删除')
    router.push({ name: 'PointShipments' })
  } catch (e: unknown) {
    if (e === 'cancel') return
    const errorMessage = e instanceof Error ? e.message : '删除失败'
    ElMessage.error(errorMessage)
  }
}

function getStatusType(status: string) {
  switch (status) {
    case 'pending':
      return 'info'
    case 'picked_up':
      return 'warning'
    case 'in_transit':
      return 'primary'
    case 'delivered':
      return 'success'
    case 'failed':
      return 'danger'
    default:
      return ''
  }
}

function getStatusText(status: string) {
  switch (status) {
    case 'pending':
      return '待发货'
    case 'picked_up':
      return '已揽收'
    case 'in_transit':
      return '运输中'
    case 'delivered':
      return '已送达'
    case 'failed':
      return '失败'
    default:
      return status
  }
}

function goBack() {
  router.push({ name: 'PointShipments' })
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
  <div class="shipment-detail-container">
    <div class="page-content">
      <div class="page-header">
        <div class="header-left">
          <el-button link @click="goBack">
            <el-icon><ArrowLeft /></el-icon>
            返回
          </el-button>
          <h2>发货详情</h2>
        </div>
        <div class="header-actions">
          <el-button type="primary" @click="openEditDialog">编辑</el-button>
          <el-button type="danger" @click="handleDelete">删除</el-button>
        </div>
      </div>

      <div v-loading="loading" class="info-section">
        <!-- 基本信息 -->
        <el-card class="info-card">
          <template #header>
            <div class="card-header">
              <span class="title">基本信息</span>
            </div>
          </template>
          <el-descriptions v-if="shipment" :column="2" border>
            <el-descriptions-item label="发货ID">{{ shipment.id }}</el-descriptions-item>
            <el-descriptions-item label="订单号">
              <el-link type="primary" @click="goToOrder">{{ shipment.order_number }}</el-link>
            </el-descriptions-item>
            <el-descriptions-item label="商品名称">{{ shipment.product_name }}</el-descriptions-item>
            <el-descriptions-item label="物流公司">{{ shipment.courier_name }}</el-descriptions-item>
            <el-descriptions-item label="物流单号">{{ shipment.tracking_number }}</el-descriptions-item>
            <el-descriptions-item label="发货状态">
              <el-tag :type="getStatusType(shipment.status)" size="small">
                {{ getStatusText(shipment.status) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="发货时间">{{ formatDateTime(shipment.shipped_at) }}</el-descriptions-item>
            <el-descriptions-item label="送达时间">
              {{ shipment.delivered_at ? formatDateTime(shipment.delivered_at) : '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="备注">{{ shipment.notes || '-' }}</el-descriptions-item>
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
            <el-descriptions-item label="订单状态">
              <el-tag :type="order.status === 'completed' ? 'success' : 'warning'" size="small">
                {{ order.status === 'completed' ? '已完成' : order.status }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="用户ID">{{ order.user_id }}</el-descriptions-item>
            <el-descriptions-item label="收货人" v-if="order.address">
              {{ order.address.contact_name }} {{ order.address.contact_phone }}
            </el-descriptions-item>
            <el-descriptions-item label="收货地址" v-if="order.address">
              {{ order.address.full_address }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- 物流跟踪 -->
        <el-card class="info-card">
          <template #header>
            <div class="card-header">
              <span class="title">物流跟踪</span>
              <el-button link type="primary" @click="loadTracking" :loading="trackingLoading">
                刷新
              </el-button>
            </div>
          </template>
          <div v-loading="trackingLoading" class="tracking-section">
            <el-timeline v-if="trackingEvents.length > 0">
              <el-timeline-item
                v-for="(event, index) in trackingEvents"
                :key="index"
                :timestamp="formatDateTime(event.time)"
                placement="top"
              >
                <div class="timeline-content">
                  <div class="timeline-status">{{ event.status }}</div>
                  <div class="timeline-desc">{{ event.description }}</div>
                  <div v-if="event.location" class="timeline-location">{{ event.location }}</div>
                </div>
              </el-timeline-item>
            </el-timeline>
            <el-empty v-else description="暂无物流跟踪信息" />
          </div>
        </el-card>
      </div>
    </div>

    <!-- 编辑对话框 -->
    <el-dialog v-model="editDialogVisible" title="编辑发货记录" width="500px">
      <el-form ref="editFormRef" :model="editForm" label-width="100px">
        <el-form-item label="物流单号" prop="tracking_number">
          <el-input v-model="editForm.tracking_number" placeholder="请输入物流单号" clearable />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-select v-model="editForm.status" placeholder="请选择状态" style="width: 100%">
            <el-option
              v-for="item in statusOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="备注" prop="notes">
          <el-input
            v-model="editForm.notes"
            type="textarea"
            :rows="3"
            placeholder="请输入备注（可选）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleEdit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.shipment-detail-container {
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

.tracking-section {
  min-height: 200px;
}

.timeline-content {
  padding: 8px 0;
}

.timeline-status {
  font-weight: 500;
  font-size: 15px;
  margin-bottom: 4px;
}

.timeline-desc {
  color: #606266;
  font-size: 14px;
  margin-bottom: 4px;
}

.timeline-location {
  color: #909399;
  font-size: 12px;
}
</style>
