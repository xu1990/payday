<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  listOrders,
  updateOrderStatus,
  type OrderItem,
  type OrderStatusUpdate,
} from '@/api/order'
import BaseDataTable from '@/components/BaseDataTable.vue'
import StatusTag from '@/components/StatusTag.vue'
import { formatDate, formatAmount } from '@/utils/format'

const list = ref<OrderItem[]>([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = 20

async function loadData() {
  loading.value = true
  try {
    const res = await listOrders({
      limit: pageSize,
      offset: (currentPage.value - 1) * pageSize,
    })
    list.value = res?.items || []
    total.value = res?.total || 0
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : '加载失败'
    ElMessage.error(errorMessage)
  } finally {
    loading.value = false
  }
}

async function handleStatusChange(orderId: string, newStatus: OrderStatusUpdate['status']) {
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
      await loadData()
      return
    }
  }

  try {
    await updateOrderStatus(orderId, { status: newStatus })
    ElMessage.success('状态更新成功')
    await loadData()
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : '操作失败'
    ElMessage.error(errorMessage)
    await loadData() // 恢复原状
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
            v-model="row.status"
            @change="(val: OrderStatusUpdate['status']) => handleStatusChange(row.id, val)"
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
