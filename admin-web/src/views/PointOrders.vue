<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  listPointOrders,
  processPointOrder,
  shipPointOrder,
  type PointOrder,
} from '@/api/pointShop'
import { listActiveCouriers, type CourierCompany } from '@/api/courier'
import { formatDate } from '@/utils/format'

const router = useRouter()
const list = ref<PointOrder[]>([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = 20
const statusFilter = ref<string>('')

// 状态选项
const statusOptions = [
  { label: '全部', value: '' },
  { label: '待处理', value: 'pending' },
  { label: '已完成', value: 'completed' },
  { label: '已取消', value: 'cancelled' },
  { label: '已退款', value: 'refunded' },
]

// 发货相关
const shipDialogVisible = ref(false)
const shipFormRef = ref()
const shipForm = ref({
  order_id: '',
  courier_code: '',
  tracking_number: '',
})
const shipFormRules = {
  courier_code: [{ required: true, message: '请选择物流公司', trigger: 'change' }],
  tracking_number: [
    { required: true, message: '请输入物流单号', trigger: 'blur' },
    { min: 5, message: '物流单号长度不能少于5位', trigger: 'blur' },
  ],
}
const couriers = ref<CourierCompany[]>([])
const currentShipOrder = ref<PointOrder | null>(null)

async function loadData() {
  loading.value = true
  try {
    const res = await listPointOrders({
      status: statusFilter.value || undefined,
      limit: pageSize,
      offset: (currentPage.value - 1) * pageSize,
    })
    list.value = res?.orders || []
    total.value = res?.total || 0
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

function handleViewDetail(order: PointOrder) {
  router.push({ name: 'PointOrderDetail', params: { id: order.id } })
}

async function handleComplete(order: PointOrder) {
  try {
    await ElMessageBox.confirm(`确定完成订单"${order.order_number}"吗？`, '确认完成', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'success',
    })
    await processPointOrder(order.id, 'complete')
    ElMessage.success('订单已完成')
    await loadData()
  } catch (e: unknown) {
    if (e === 'cancel') return
    const errorMessage = e instanceof Error ? e.message : '操作失败'
    ElMessage.error(errorMessage)
  }
}

async function handleCancel(order: PointOrder) {
  try {
    const { value: notes } = await ElMessageBox.prompt(
      '请输入取消原因（可选）',
      `取消订单"${order.order_number}"`,
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
        inputPlaceholder: '请输入取消原因',
      }
    )
    await processPointOrder(order.id, 'cancel', notes || undefined)
    ElMessage.success('订单已取消')
    await loadData()
  } catch (e: unknown) {
    if (e === 'cancel') return
    const errorMessage = e instanceof Error ? e.message : '操作失败'
    ElMessage.error(errorMessage)
  }
}

// 加载物流公司列表
async function loadCouriers() {
  try {
    const res = await listActiveCouriers()
    couriers.value = res?.data || []
  } catch (e: unknown) {
    console.error('加载物流公司失败:', e)
  }
}

// 判断订单是否需要发货
function needsShipping(order: PointOrder): boolean {
  // 只有已完成的订单且没有发货记录的实物商品需要发货
  if (order.status !== 'completed') return false
  if (order.shipment_id) return false
  // 虚拟商品和无需快递的商品不需要发货
  if (order.product_type === 'virtual') return false
  if (order.shipping_method === 'no_shipping') return false
  return true
}

// 打开发货对话框
function openShipDialog(order: PointOrder) {
  currentShipOrder.value = order
  shipForm.value = {
    order_id: order.id,
    courier_code: '',
    tracking_number: '',
  }
  shipDialogVisible.value = true
}

// 发货
async function handleShip() {
  if (!currentShipOrder.value) return
  try {
    await shipFormRef.value.validate()
    await shipPointOrder(currentShipOrder.value.id, {
      courier_code: shipForm.value.courier_code,
      tracking_number: shipForm.value.tracking_number,
    })
    ElMessage.success('发货成功')
    shipDialogVisible.value = false
    await loadData()
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : '发货失败'
    ElMessage.error(errorMessage)
  }
}

function getStatusType(status: string) {
  switch (status) {
    case 'pending':
      return 'warning'
    case 'completed':
      return 'success'
    case 'cancelled':
      return 'info'
    case 'refunded':
      return 'danger'
    default:
      return ''
  }
}

function getStatusText(status: string) {
  switch (status) {
    case 'pending':
      return '待处理'
    case 'completed':
      return '已完成'
    case 'cancelled':
      return '已取消'
    case 'refunded':
      return '已退款'
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
  <div class="point-orders-container">
    <div class="page-header">
      <h2>积分订单管理</h2>
      <el-select
        v-model="statusFilter"
        placeholder="筛选状态"
        style="width: 150px"
        @change="handleStatusChange"
      >
        <el-option
          v-for="item in statusOptions"
          :key="item.value"
          :label="item.label"
          :value="item.value"
        />
      </el-select>
    </div>

    <el-table v-loading="loading" :data="list" stripe>
      <el-table-column prop="order_number" label="订单号" width="200" />
      <el-table-column prop="product_name" label="商品名称" width="180" />
      <el-table-column label="支付方式" width="120">
        <template #default="{ row }">
          <el-tag v-if="row.payment_mode === 'points_only'" type="success" size="small">纯积分</el-tag>
          <el-tag v-else-if="row.payment_mode === 'cash_only'" type="warning" size="small">纯现金</el-tag>
          <el-tag v-else-if="row.payment_mode === 'mixed'" type="primary" size="small">积分+现金</el-tag>
          <el-tag v-else type="info" size="small">纯积分</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="points_cost" label="积分" width="100">
        <template #default="{ row }">
          <span v-if="row.points_cost > 0">{{ row.points_cost }} 积分</span>
          <span v-else style="color: #999">-</span>
        </template>
      </el-table-column>
      <el-table-column prop="cash_amount" label="现金" width="100">
        <template #default="{ row }">
          <span v-if="row.cash_amount && row.cash_amount > 0" style="color: #f56c6c">
            ¥{{ (row.cash_amount / 100).toFixed(2) }}
          </span>
          <span v-else style="color: #67c23a">免支付</span>
        </template>
      </el-table-column>
      <el-table-column prop="user_id" label="用户ID" width="180" />
      <el-table-column label="收货信息" width="220">
        <template #default="{ row }">
          <div v-if="row.address" class="address-cell">
            <div class="address-contact">
              {{ row.address.contact_name }} {{ row.address.contact_phone }}
            </div>
            <div class="address-detail" :title="row.address.full_address">
              {{ row.address.full_address }}
            </div>
          </div>
          <span v-else-if="row.product_type === 'virtual'" style="color: #999; font-size: 12px">
            虚拟商品
          </span>
          <span v-else style="color: #999; font-size: 12px">-</span>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)" size="small">
            {{ getStatusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column prop="processed_at" label="处理时间" width="180">
        <template #default="{ row }">
          {{ row.processed_at ? formatDate(row.processed_at) : '-' }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button
            link
            type="primary"
            size="small"
            @click="handleViewDetail(row)"
          >
            详情
          </el-button>
          <el-button
            v-if="row.status === 'pending'"
            link
            type="success"
            size="small"
            @click="handleComplete(row)"
          >
            完成
          </el-button>
          <el-button
            v-if="row.status === 'pending'"
            link
            type="warning"
            size="small"
            @click="handleCancel(row)"
          >
            取消
          </el-button>
          <el-button
            v-if="needsShipping(row)"
            link
            type="primary"
            size="small"
            @click="openShipDialog(row)"
          >
            发货
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

    <!-- 发货对话框 -->
    <el-dialog v-model="shipDialogVisible" title="订单发货" width="500px">
      <div v-if="currentShipOrder" class="ship-order-info">
        <p><strong>订单号：</strong>{{ currentShipOrder.order_number }}</p>
        <p><strong>商品名称：</strong>{{ currentShipOrder.product_name }}</p>
        <!-- 收货信息 -->
        <div v-if="currentShipOrder.address" class="ship-address-info">
          <p class="address-title"><strong>收货信息：</strong></p>
          <p class="address-contact">
            {{ currentShipOrder.address.contact_name }}
            {{ currentShipOrder.address.contact_phone }}
          </p>
          <p class="address-detail">{{ currentShipOrder.address.full_address }}</p>
        </div>
        <p v-if="currentShipOrder.notes"><strong>备注：</strong>{{ currentShipOrder.notes }}</p>
      </div>
      <el-form ref="shipFormRef" :model="shipForm" :rules="shipFormRules" label-width="100px">
        <el-form-item label="物流公司" prop="courier_code">
          <el-select
            v-model="shipForm.courier_code"
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
          <el-input v-model="shipForm.tracking_number" placeholder="请输入物流单号" clearable />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="shipDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleShip">确认发货</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.point-orders-container {
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

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

/* 订单列表收货信息样式 */
.address-cell {
  font-size: 12px;
  line-height: 1.4;
}

.address-contact {
  font-weight: 500;
  color: #303133;
}

.address-detail {
  color: #606266;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 200px;
}

/* 发货弹窗收货信息样式 */
.ship-order-info {
  padding: 12px;
  background-color: #f5f7fa;
  border-radius: 4px;
  margin-bottom: 20px;
}

.ship-order-info p {
  margin: 4px 0;
  font-size: 14px;
}

.ship-address-info {
  margin-top: 8px;
  padding: 8px;
  background-color: #fff;
  border-radius: 4px;
  border: 1px solid #e4e7ed;
}

.ship-address-info .address-title {
  margin-bottom: 4px;
}

.ship-address-info .address-contact {
  color: #409eff;
  font-size: 14px;
}

.ship-address-info .address-detail {
  color: #606266;
  font-size: 13px;
  white-space: normal;
  word-break: break-all;
  max-width: 100%;
}
</style>
