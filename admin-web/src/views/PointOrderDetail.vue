<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getPointOrderDetail,
  processPointOrder,
  shipPointOrder,
  type PointOrder,
} from '@/api/pointShop'
import { listActiveCouriers, type CourierCompany } from '@/api/courier'
import { formatDateTime } from '@/utils/format'
import StatusTag from '@/components/StatusTag.vue'
import PaymentModeTag from '@/components/PaymentModeTag.vue'

const route = useRoute()
const router = useRouter()

const orderId = computed(() => route.params.id as string)

const order = ref<PointOrder | null>(null)
const loading = ref(false)

// 发货相关
const shipDialogVisible = ref(false)
const shipFormRef = ref()
const shipForm = ref({
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

// 判断订单是否需要发货
function needsShipping(): boolean {
  if (!order.value) return false
  if (order.value.status !== 'completed') return false
  if (order.value.shipment_id) return false
  if (order.value.product_type === 'virtual') return false
  if (order.value.shipping_method === 'no_shipping') return false
  return true
}

async function loadData() {
  if (!orderId.value) return
  loading.value = true
  try {
    const res = await getPointOrderDetail(orderId.value)
    order.value = res
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : '加载失败'
    ElMessage.error(errorMessage)
    router.push('/point-orders')
  } finally {
    loading.value = false
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

async function handleComplete() {
  if (!order.value) return
  try {
    await ElMessageBox.confirm(`确定完成订单"${order.value.order_number}"吗？`, '确认完成', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'success',
    })
    await processPointOrder(order.value.id, 'complete')
    ElMessage.success('订单已完成')
    await loadData()
  } catch (e: unknown) {
    if (e === 'cancel') return
    const errorMessage = e instanceof Error ? e.message : '操作失败'
    ElMessage.error(errorMessage)
  }
}

async function handleCancel() {
  if (!order.value) return
  try {
    const { value: notes } = await ElMessageBox.prompt(
      '请输入取消原因（可选）',
      `取消订单"${order.value.order_number}"`,
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
        inputPlaceholder: '请输入取消原因',
      }
    )
    await processPointOrder(order.value.id, 'cancel', notes || undefined)
    ElMessage.success('订单已取消')
    await loadData()
  } catch (e: unknown) {
    if (e === 'cancel') return
    const errorMessage = e instanceof Error ? e.message : '操作失败'
    ElMessage.error(errorMessage)
  }
}

// 打开发货对话框
function openShipDialog() {
  if (!order.value) return
  shipForm.value = {
    courier_code: '',
    tracking_number: '',
  }
  shipDialogVisible.value = true
}

// 发货
async function handleShip() {
  if (!order.value) return
  try {
    await shipFormRef.value.validate()
    await shipPointOrder(order.value.id, {
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

function goBack() {
  router.push('/point-orders')
}

onMounted(() => {
  loadData()
  loadCouriers()
})
</script>

<template>
  <div class="order-detail-container">
    <div v-loading="loading" class="page-content">
      <template v-if="order">
        <!-- 页面头部 -->
        <div class="page-header">
          <div class="header-left">
            <el-button link @click="goBack">
              <el-icon><ArrowLeft /></el-icon>
              返回列表
            </el-button>
            <h2>订单详情</h2>
          </div>
          <div class="header-right">
            <el-button
              v-if="order.status === 'pending'"
              type="success"
              @click="handleComplete"
            >
              完成订单
            </el-button>
            <el-button
              v-if="order.status === 'pending'"
              type="warning"
              @click="handleCancel"
            >
              取消订单
            </el-button>
            <el-button
              v-if="needsShipping()"
              type="primary"
              @click="openShipDialog"
            >
              发货
            </el-button>
          </div>
        </div>

        <!-- 订单基本信息 -->
        <el-card class="info-card">
          <template #header>
            <div class="card-header">
              <span class="title">订单信息</span>
              <StatusTag :status="order.status" />
            </div>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="订单号">{{ order.order_number }}</el-descriptions-item>
            <el-descriptions-item label="用户ID">{{ order.user_id }}</el-descriptions-item>
            <el-descriptions-item label="创建时间">
              {{ formatDateTime(order.created_at) }}
            </el-descriptions-item>
            <el-descriptions-item label="处理时间">
              {{ order.processed_at ? formatDateTime(order.processed_at) : '-' }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- 商品信息 -->
        <el-card class="info-card">
          <template #header>
            <div class="card-header">
              <span class="title">商品信息</span>
            </div>
          </template>
          <div class="product-info">
            <div class="product-image">
              <img v-if="order.product_image" :src="order.product_image" alt="商品图片" />
              <div v-else class="placeholder-image">商品</div>
            </div>
            <div class="product-detail">
              <div class="product-name">{{ order.product_name }}</div>
              <div class="product-meta">
                <span v-if="order.product_type === 'virtual'" class="meta-tag">虚拟商品</span>
                <span v-else-if="order.product_type === 'bundle'" class="meta-tag">套餐商品</span>
                <span v-else class="meta-tag">实物商品</span>
                <span v-if="order.shipping_method === 'self_pickup'" class="meta-tag">自提</span>
                <span v-else-if="order.shipping_method === 'no_shipping'" class="meta-tag">无需快递</span>
              </div>
            </div>
          </div>
          <el-descriptions :column="2" border style="margin-top: 16px">
            <el-descriptions-item label="支付方式">
              <PaymentModeTag :mode="order.payment_mode" />
            </el-descriptions-item>
            <el-descriptions-item label="积分">
              <span v-if="order.points_cost > 0">{{ order.points_cost }} 积分</span>
              <span v-else style="color: #999">-</span>
            </el-descriptions-item>
            <el-descriptions-item label="现金">
              <span v-if="order.cash_amount > 0" style="color: #f56c6c">
                ¥{{ (order.cash_amount / 100).toFixed(2) }}
              </span>
              <span v-else style="color: #67c23a">免支付</span>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- 收货地址 -->
        <el-card v-if="order.address" class="info-card">
          <template #header>
            <div class="card-header">
              <span class="title">收货信息</span>
            </div>
          </template>
          <div class="address-info">
            <div class="address-contact">
              <span class="contact-name">{{ order.address.contact_name }}</span>
              <span class="contact-phone">{{ order.address.contact_phone }}</span>
            </div>
            <div class="address-detail">
              {{ order.address.full_address }}
            </div>
          </div>
        </el-card>

        <!-- 发货信息 -->
        <el-card v-if="order.shipment" class="info-card">
          <template #header>
            <div class="card-header">
              <span class="title">发货信息</span>
              <el-tag type="success" size="small">已发货</el-tag>
            </div>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="物流公司">{{ order.shipment.courier_name }}</el-descriptions-item>
            <el-descriptions-item label="物流单号">{{ order.shipment.tracking_number }}</el-descriptions-item>
            <el-descriptions-item label="发货时间">
              {{ formatDateTime(order.shipment.shipped_at) }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- 退货信息 -->
        <el-card v-if="order.return_request" class="info-card">
          <template #header>
            <div class="card-header">
              <span class="title">退货信息</span>
              <el-tag :type="order.return_request.status === 'approved' ? 'success' : 'warning'" size="small">
                {{ order.return_request.status === 'approved' ? '已批准' : '待处理' }}
              </el-tag>
            </div>
          </template>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="退货原因">{{ order.return_request.reason }}</el-descriptions-item>
            <el-descriptions-item label="申请时间">
              {{ formatDateTime(order.return_request.created_at) }}
            </el-descriptions-item>
            <el-descriptions-item v-if="order.return_request.processed_at" label="处理时间">
              {{ formatDateTime(order.return_request.processed_at) }}
            </el-descriptions-item>
            <el-descriptions-item v-if="order.return_request.admin_notes" label="处理备注">
              {{ order.return_request.admin_notes }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- 备注信息 -->
        <el-card class="info-card">
          <template #header>
            <div class="card-header">
              <span class="title">备注信息</span>
            </div>
          </template>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="用户备注">
              {{ order.notes || '无' }}
            </el-descriptions-item>
            <el-descriptions-item label="管理员备注">
              {{ order.notes_admin || '无' }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </template>
    </div>

    <!-- 发货对话框 -->
    <el-dialog v-model="shipDialogVisible" title="订单发货" width="500px">
      <div v-if="order" class="ship-order-info">
        <p><strong>订单号：</strong>{{ order.order_number }}</p>
        <p><strong>商品名称：</strong>{{ order.product_name }}</p>
        <div v-if="order.address" class="ship-address-info">
          <p class="address-title"><strong>收货信息：</strong></p>
          <p class="address-contact">
            {{ order.address.contact_name }}
            {{ order.address.contact_phone }}
          </p>
          <p class="address-detail">{{ order.address.full_address }}</p>
        </div>
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
.order-detail-container {
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

.product-info {
  display: flex;
  gap: 16px;
}

.product-image {
  width: 100px;
  height: 100px;
  border-radius: 8px;
  overflow: hidden;
  flex-shrink: 0;
}

.product-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.placeholder-image {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
  color: #909399;
  font-size: 14px;
}

.product-detail {
  flex: 1;
}

.product-name {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 8px;
}

.product-meta {
  display: flex;
  gap: 8px;
}

.meta-tag {
  font-size: 12px;
  padding: 2px 8px;
  background: #f5f7fa;
  border-radius: 4px;
  color: #606266;
}

.address-info {
  padding: 8px 0;
}

.address-contact {
  margin-bottom: 8px;
}

.contact-name {
  font-weight: 500;
  margin-right: 16px;
}

.contact-phone {
  color: #606266;
}

.address-detail {
  color: #606266;
  line-height: 1.6;
}

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
}
</style>
