<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  listShipments,
  createShipment,
  updateShipment,
  deleteShipment,
  getTracking,
  getPendingOrders,
  type PointShipment,
  type PointShipmentCreate,
  type PointShipmentUpdate,
  type PointOrderBasic,
  type TrackingEvent,
} from '@/api/pointShipment'
import { listActiveCouriers, type CourierCompany } from '@/api/courier'
import { formatDateTime } from '@/utils/format'

const router = useRouter()
const list = ref<PointShipment[]>([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = 20

// 筛选条件
const orderNumberFilter = ref<string>('')
const statusFilter = ref<string>('')
const courierFilter = ref<string>('')
const dateRangeFilter = ref<[Date, Date] | null>(null)

// 对话框相关
const createDialogVisible = ref(false)
const editDialogVisible = ref(false)
const trackingDialogVisible = ref(false)
const currentShipment = ref<PointShipment | null>(null)
const trackingEvents = ref<TrackingEvent[]>([])

// 创建表单
const createFormRef = ref()
const createForm = ref<PointShipmentCreate>({
  order_id: '',
  courier_code: '',
  tracking_number: '',
  notes: '',
})

// 编辑表单
const editFormRef = ref()
const editForm = ref<PointShipmentUpdate>({
  tracking_number: '',
  status: undefined,
  notes: '',
})

// 选项数据
const statusOptions = [
  { label: '全部', value: '' },
  { label: '待发货', value: 'pending' },
  { label: '已揽收', value: 'picked_up' },
  { label: '运输中', value: 'in_transit' },
  { label: '已送达', value: 'delivered' },
  { label: '失败', value: 'failed' },
]

const statusOptionsForEdit = [
  { label: '待发货', value: 'pending' },
  { label: '已揽收', value: 'picked_up' },
  { label: '运输中', value: 'in_transit' },
  { label: '已送达', value: 'delivered' },
  { label: '失败', value: 'failed' },
]

const pendingOrders = ref<PointOrderBasic[]>([])
const couriers = ref<CourierCompany[]>([])

// 创建表单校验规则
const createFormRules = {
  order_id: [{ required: true, message: '请选择订单', trigger: 'change' }],
  courier_code: [{ required: true, message: '请选择物流公司', trigger: 'change' }],
  tracking_number: [
    { required: true, message: '请输入物流单号', trigger: 'blur' },
    { min: 5, message: '物流单号长度不能少于5位', trigger: 'blur' },
  ],
}

// 编辑表单校验规则
const editFormRules = {
  tracking_number: [
    { required: true, message: '请输入物流单号', trigger: 'blur' },
    { min: 5, message: '物流单号长度不能少于5位', trigger: 'blur' },
  ],
}

async function loadData() {
  loading.value = true
  try {
    const params: Record<string, string | number> = {
      limit: pageSize,
      offset: (currentPage.value - 1) * pageSize,
    }
    if (orderNumberFilter.value) params.order_number = orderNumberFilter.value
    if (statusFilter.value) params.status = statusFilter.value
    if (courierFilter.value) params.courier_code = courierFilter.value
    if (dateRangeFilter.value) {
      params.date_from = dateRangeFilter.value[0].toISOString().split('T')[0]
      params.date_to = dateRangeFilter.value[1].toISOString().split('T')[0]
    }

    const res = await listShipments(params)
    list.value = res?.data?.shipments || []
    total.value = res?.data?.total || 0
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : '加载失败'
    ElMessage.error(errorMessage)
  } finally {
    loading.value = false
  }
}

async function loadPendingOrders() {
  try {
    const res = await getPendingOrders()
    pendingOrders.value = res?.data || []
  } catch (e: unknown) {
    console.error('加载待发货订单失败:', e)
  }
}

async function loadCouriers() {
  try {
    const res = await listActiveCouriers()
    couriers.value = res?.data || []
  } catch (e: unknown) {
    console.error('加载物流公司失败:', e)
  }
}

function handleFilter() {
  currentPage.value = 1
  loadData()
}

function handleReset() {
  orderNumberFilter.value = ''
  statusFilter.value = ''
  courierFilter.value = ''
  dateRangeFilter.value = null
  currentPage.value = 1
  loadData()
}

function handleViewDetail(shipment: PointShipment) {
  router.push({ name: 'PointShipmentDetail', params: { id: shipment.id } })
}

async function openCreateDialog() {
  await loadPendingOrders()
  if (pendingOrders.value.length === 0) {
    ElMessage.warning('没有待发货的订单')
    return
  }
  createForm.value = {
    order_id: '',
    courier_code: '',
    tracking_number: '',
    notes: '',
  }
  createDialogVisible.value = true
}

async function handleCreate() {
  try {
    await createFormRef.value.validate()
    await createShipment(createForm.value)
    ElMessage.success('发货记录已创建')
    createDialogVisible.value = false
    await loadData()
  } catch (e: unknown) {
    if (e === 'cancel') return
    const errorMessage = e instanceof Error ? e.message : '创建失败'
    ElMessage.error(errorMessage)
  }
}

function openEditDialog(shipment: PointShipment) {
  currentShipment.value = shipment
  editForm.value = {
    tracking_number: shipment.tracking_number,
    status: shipment.status,
    notes: shipment.notes || '',
  }
  editDialogVisible.value = true
}

async function handleEdit() {
  if (!currentShipment.value) return
  try {
    await editFormRef.value.validate()
    await updateShipment(currentShipment.value.id, editForm.value)
    ElMessage.success('发货记录已更新')
    editDialogVisible.value = false
    await loadData()
  } catch (e: unknown) {
    if (e === 'cancel') return
    const errorMessage = e instanceof Error ? e.message : '更新失败'
    ElMessage.error(errorMessage)
  }
}

async function openTrackingDialog(shipment: PointShipment) {
  currentShipment.value = shipment
  trackingEvents.value = []
  trackingDialogVisible.value = true

  try {
    const res = await getTracking(shipment.id)
    trackingEvents.value = res?.data?.tracking_info || []
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : '获取物流信息失败'
    ElMessage.error(errorMessage)
  }
}

async function handleDelete(shipment: PointShipment) {
  try {
    await ElMessageBox.confirm(`确定删除订单"${shipment.order_number}"的发货记录吗？`, '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await deleteShipment(shipment.id)
    ElMessage.success('发货记录已删除')
    await loadData()
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

onMounted(() => {
  loadData()
  loadCouriers()
})
</script>

<template>
  <div class="point-shipments-container">
    <div class="page-header">
      <h2>发货管理</h2>
      <el-button type="primary" @click="openCreateDialog">+ 创建发货</el-button>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <el-input
        v-model="orderNumberFilter"
        placeholder="订单号"
        clearable
        style="width: 180px"
        @keyup.enter="handleFilter"
      />
      <el-select v-model="statusFilter" placeholder="状态" clearable style="width: 150px">
        <el-option
          v-for="item in statusOptions"
          :key="item.value"
          :label="item.label"
          :value="item.value"
        />
      </el-select>
      <el-select v-model="courierFilter" placeholder="物流公司" clearable style="width: 150px">
        <el-option
          v-for="courier in couriers"
          :key="courier.code"
          :label="courier.name"
          :value="courier.code"
        />
      </el-select>
      <el-date-picker
        v-model="dateRangeFilter"
        type="daterange"
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        value-format="YYYY-MM-DD"
        style="width: 240px"
      />
      <el-button type="primary" @click="handleFilter">筛选</el-button>
      <el-button @click="handleReset">重置</el-button>
    </div>

    <!-- 发货列表表格 -->
    <el-table v-loading="loading" :data="list" stripe>
      <el-table-column prop="order_number" label="订单号" width="180" />
      <el-table-column prop="product_name" label="商品名称" width="180" />
      <el-table-column prop="courier_name" label="物流公司" width="120" />
      <el-table-column prop="tracking_number" label="物流单号" width="180" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)" size="small">
            {{ getStatusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="shipped_at" label="发货时间" width="180">
        <template #default="{ row }">
          {{ formatDateTime(row.shipped_at) }}
        </template>
      </el-table-column>
      <el-table-column prop="delivered_at" label="送达时间" width="180">
        <template #default="{ row }">
          {{ row.delivered_at ? formatDateTime(row.delivered_at) : '-' }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click="handleViewDetail(row)">
            详情
          </el-button>
          <el-button link type="primary" size="small" @click="openTrackingDialog(row)">
            跟踪
          </el-button>
          <el-button link type="primary" size="small" @click="openEditDialog(row)">
            编辑
          </el-button>
          <el-button link type="danger" size="small" @click="handleDelete(row)"> 删除 </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="pagination-wrapper">
      <el-pagination
        v-model:current-page="currentPage"
        :page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        @current-change="loadData"
      />
    </div>

    <!-- 创建发货对话框 -->
    <el-dialog v-model="createDialogVisible" title="创建发货" width="500px">
      <el-form ref="createFormRef" :model="createForm" :rules="createFormRules" label-width="100px">
        <el-form-item label="选择订单" prop="order_id">
          <el-select
            v-model="createForm.order_id"
            placeholder="请选择待发货订单"
            style="width: 100%"
            filterable
          >
            <el-option
              v-for="order in pendingOrders"
              :key="order.id"
              :label="`${order.order_number} - ${order.product_name}`"
              :value="order.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="物流公司" prop="courier_code">
          <el-select
            v-model="createForm.courier_code"
            placeholder="请选择物流公司"
            style="width: 100%"
          >
            <el-option
              v-for="courier in couriers"
              :key="courier.code"
              :label="courier.name"
              :value="courier.code"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="物流单号" prop="tracking_number">
          <el-input v-model="createForm.tracking_number" placeholder="请输入物流单号" clearable />
        </el-form-item>
        <el-form-item label="备注" prop="notes">
          <el-input
            v-model="createForm.notes"
            type="textarea"
            :rows="3"
            placeholder="请输入备注（可选）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreate">确定</el-button>
      </template>
    </el-dialog>

    <!-- 编辑发货对话框 -->
    <el-dialog v-model="editDialogVisible" title="编辑发货" width="500px">
      <el-form ref="editFormRef" :model="editForm" :rules="editFormRules" label-width="100px">
        <el-form-item label="物流单号" prop="tracking_number">
          <el-input v-model="editForm.tracking_number" placeholder="请输入物流单号" clearable />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-select v-model="editForm.status" placeholder="请选择状态" style="width: 100%">
            <el-option
              v-for="item in statusOptionsForEdit"
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

    <!-- 物流跟踪对话框 -->
    <el-dialog v-model="trackingDialogVisible" title="物流跟踪" width="600px">
      <div v-if="currentShipment" class="tracking-header">
        <p><strong>订单号：</strong>{{ currentShipment.order_number }}</p>
        <p><strong>物流公司：</strong>{{ currentShipment.courier_name }}</p>
        <p><strong>物流单号：</strong>{{ currentShipment.tracking_number }}</p>
      </div>
      <div class="tracking-timeline">
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
    </el-dialog>
  </div>
</template>

<style scoped>
.point-shipments-container {
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

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.tracking-header {
  padding: 12px;
  background-color: #f5f7fa;
  border-radius: 4px;
  margin-bottom: 20px;
}

.tracking-header p {
  margin: 4px 0;
  font-size: 14px;
}

.tracking-timeline {
  max-height: 400px;
  overflow-y: auto;
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
