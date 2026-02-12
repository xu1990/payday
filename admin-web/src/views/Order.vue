<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  listOrders,
  updateOrderStatus,
  type OrderItem,
  type OrderStatusUpdate,
} from '@/api/order'
import BaseDataTable from '@/components/BaseDataTable.vue'
import StatusTag from '@/components/StatusTag.vue'
import { formatDate, formatAmount } from '@/utils/format'
import { ORDER_STATUS_MAP } from '@/constants/status'
import { useErrorHandler } from '@/composables/useErrorHandler'

const { handleError } = useErrorHandler()

const list = ref<OrderItem[]>([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = 20

// 状态更新时的loading状态，防止并发操作
const updatingOrderId = ref<string | null>(null)

async function loadData() {
  loading.value = true
  try {
    const res = await listOrders({
      limit: pageSize,
      offset: (currentPage.value - 1) * pageSize,
    })
    list.value = res?.data?.items || []
    total.value = res?.data?.total || 0
  } catch (e: unknown) {
    handleError(e, '加载失败')
  } finally {
    loading.value = false
  }
}

async function handleStatusChange(orderId: string, newStatus: OrderStatusUpdate['status']) {
  // 防止对同一个订单的并发操作
  if (updatingOrderId.value === orderId) {
    return
  }

  // 对关键状态变更添加确认
  if (newStatus === 'refunded' || newStatus === 'cancelled') {
    const statusText = newStatus === 'refunded' ? '退款' : '取消'
    try {
      await ElMessageBox.confirm(
        `确定要将订单状态更改为「${statusText}」吗？此操作不可撤销。`,
        '确认状态变更',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning',
        }
      )
    } catch {
      // 用户取消操作
      return
    }
  }

  // 设置loading状态
  updatingOrderId.value = orderId

  try {
    await updateOrderStatus(orderId, { status: newStatus })
    ElMessage.success('状态更新成功')
    await loadData()
  } catch (e: unknown) {
    handleError(e, '操作失败')
    await loadData() // 恢复原状态
  } finally {
    updatingOrderId.value = null
  }
}

function handlePageChange(page: number) {
  currentPage.value = page
  loadData()
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="orders-page">
    <h2 class="page-title">会员订单管理</h2>

    <BaseDataTable
      v-model:current-page="currentPage"
      :items="list"
      :total="total"
      :loading="loading"
      @page-change="handlePageChange"
    >
      <el-table-column prop="id" label="订单ID" width="200" />
      <el-table-column prop="user_id" label="用户ID" width="150" />
      <el-table-column prop="membership_name" label="套餐名称" width="150" />
      <el-table-column prop="amount" label="实付金额（元）" width="130">
        <template #default="{ row }">
          <div v-memo="[row.id, row.amount]">
            <span class="price">{{ formatAmount(row.amount) }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="120" align="center">
        <template #default="{ row }">
          <StatusTag
            :status="row.status"
            :status-map="{
              pending: { text: '待支付', type: 'info' },
              paid: { text: '已支付', type: 'success' },
              cancelled: { text: '已取消', type: 'info' },
              refunded: { text: '已退款', type: 'danger' }
            }"
          />
        </template>
      </el-table-column>
      <el-table-column prop="payment_method" label="支付方式" width="100" align="center">
        <template #default="{ row }">
          {{ row.payment_method || '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="start_date" label="开始时间" width="170">
        <template #default="{ row }">
          <div v-memo="[row.id, row.start_date]">
            {{ row.start_date ? formatDate(row.start_date) : '-' }}
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="end_date" label="到期时间" width="170">
        <template #default="{ row }">
          <div v-memo="[row.id, row.end_date]">
            {{ row.end_date ? formatDate(row.end_date) : '-' }}
          </div>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-select
            :model-value="row.status"
            @change="(val: OrderStatusUpdate['status']) => handleStatusChange(row.id, val)"
            :disabled="updatingOrderId === row.id"
            size="small"
            style="width: 120px"
          >
            <el-option label="待支付" value="pending" />
            <el-option label="已支付" value="paid" />
            <el-option label="已取消" value="cancelled" />
            <el-option label="已退款" value="refunded" />
          </el-select>
        </template>
      </el-table-column>
    </BaseDataTable>
  </div>
</template>

<style scoped>
.price {
  font-weight: 600;
  color: var(--color-primary);
}
</style>
