<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listPointOrders, processPointOrder, type PointOrder } from '@/api/pointShop'
import { formatDate } from '@/utils/format'

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
      <el-table-column prop="points_cost" label="积分" width="100">
        <template #default="{ row }"> {{ row.points_cost }} 积分 </template>
      </el-table-column>
      <el-table-column prop="user_id" label="用户ID" width="180" />
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
          <span v-if="row.status !== 'pending'" style="color: #999; font-size: 12px"> 已处理 </span>
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
</style>
