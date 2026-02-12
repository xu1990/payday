<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  listOrders,
  updateOrderStatus,
  type OrderItem,
} from '@/api/order'

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
  } catch (e: any) {
    ElMessage.error(e?.message || '加载失败')
  } finally {
    loading.value = false
  }
}

async function handleStatusChange(orderId: string, newStatus: string) {
  try {
    await updateOrderStatus(orderId, { status: newStatus as any })
    ElMessage.success('状态更新成功')
    await loadData()
  } catch (e: any) {
    ElMessage.error(e?.message || '操作失败')
  }
}

function getStatusType(status: string): 'success' | 'warning' | 'info' | 'danger' {
  switch (status) {
    case 'pending':
      return 'info'
    case 'paid':
      return 'success'
    case 'cancelled':
      return 'warning'
    case 'refunded':
      return 'danger'
    default:
      return 'info'
  }
}

function getStatusLabel(status: string): string {
  switch (status) {
    case 'pending':
      return '待支付'
    case 'paid':
      return '已支付'
    case 'cancelled':
      return '已取消'
    case 'refunded':
      return '已退款'
    default:
      return status
  }
}

function formatPrice(priceInCents: number): string {
  return (priceInCents / 100).toFixed(2)
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
    <div class="header">
      <h2>会员订单管理</h2>
    </div>

    <el-table v-loading="loading" :data="list" stripe>
      <el-table-column prop="id" label="订单ID" width="200" />
      <el-table-column prop="user_id" label="用户ID" width="150" />
      <el-table-column prop="membership_name" label="套餐名称" width="150" />
      <el-table-column prop="amount" label="实付金额（元）" width="130">
        <template #default="{ row }">
          <span class="price">¥{{ formatPrice(row.amount) }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="120" align="center">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)" size="small">
            {{ getStatusLabel(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="payment_method" label="支付方式" width="100" align="center">
        <template #default="{ row }">
          {{ row.payment_method || '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="start_date" label="开始时间" width="170">
        <template #default="{ row }">
          {{ row.start_date ? new Date(row.start_date).toLocaleString() : '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="end_date" label="到期时间" width="170">
        <template #default="{ row }">
          {{ row.end_date ? new Date(row.end_date).toLocaleString() : '-' }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-select
            v-model="row.status"
            @change="(val: any) => handleStatusChange(row.id, val)"
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
    </el-table>

    <div class="pagination">
      <el-pagination
        v-model:current-page="currentPage"
        :page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        @current-change="handlePageChange"
      />
    </div>
  </div>
</template>

<style scoped>
.orders-page {
  padding: 24px;
}
.header {
  margin-bottom: 24px;
}
.header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}
.price {
  font-weight: 600;
  color: #409eff;
}
.pagination {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}
</style>
