<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  listPointProducts,
  deletePointProduct,
  updatePointProduct,
  type PointProduct,
} from '@/api/pointShop'
import { formatDate } from '@/utils/format'

const router = useRouter()

const list = ref<PointProduct[]>([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = 20

async function loadData() {
  loading.value = true
  try {
    const res = await listPointProducts({
      limit: pageSize,
      offset: (currentPage.value - 1) * pageSize,
    })
    list.value = res?.data?.products || []
    total.value = res?.data?.total || 0
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : '加载失败'
    ElMessage.error(errorMessage)
  } finally {
    loading.value = false
  }
}

function openCreate() {
  router.push('/point-shop/create')
}

function openEdit(item: PointProduct) {
  router.push(`/point-shop/${item.id}/edit`)
}

async function handleDelete(item: PointProduct) {
  try {
    await ElMessageBox.confirm(`确定要删除商品"${item.name}"吗？`, '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await deletePointProduct(item.id)
    ElMessage.success('删除成功')
    await loadData()
  } catch (e: unknown) {
    if (e === 'cancel') return
    const errorMessage = e instanceof Error ? e.message : '删除失败'
    ElMessage.error(errorMessage)
  }
}

async function toggleActive(item: PointProduct) {
  try {
    await updatePointProduct(item.id, { is_active: !item.is_active })
    ElMessage.success(item.is_active ? '已下架' : '已上架')
    await loadData()
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : '操作失败'
    ElMessage.error(errorMessage)
  }
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="point-shop-container">
    <div class="page-header">
      <h2>积分商品管理</h2>
      <el-button type="primary" @click="openCreate">新建商品</el-button>
    </div>

    <el-table :data="list" v-loading="loading" stripe>
      <el-table-column prop="name" label="商品名称" width="200" />
      <el-table-column prop="category" label="分类" width="150">
        <template #default="{ row }">
          {{ row.category || '-' }}
        </template>
      </el-table-column>
      <el-table-column label="类型" width="100">
        <template #default="{ row }">
          <el-tag v-if="row.product_type === 'virtual'" type="info" size="small">虚拟</el-tag>
          <el-tag v-else-if="row.product_type === 'bundle'" type="warning" size="small">套餐</el-tag>
          <el-tag v-else type="success" size="small">实物</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="物流" width="100">
        <template #default="{ row }">
          <span v-if="row.shipping_method === 'express'">快递</span>
          <span v-else-if="row.shipping_method === 'self_pickup'">自提</span>
          <span v-else style="color: #999">无需快递</span>
        </template>
      </el-table-column>
      <el-table-column label="主图" width="100">
        <template #default="{ row }">
          <el-image
            v-if="row.image_urls && row.image_urls.length > 0"
            :src="row.image_urls[0]"
            fit="cover"
            style="width: 60px; height: 60px; border-radius: 4px"
            :preview-src-list="row.image_urls"
          />
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column prop="points_cost" label="积分价格" width="100">
        <template #default="{ row }">
          {{ row.points_cost }} 积分
        </template>
      </el-table-column>
      <el-table-column label="库存" width="100">
        <template #default="{ row }">
          {{ row.has_sku ? '多规格' : (row.stock_unlimited ? '无限' : row.stock) }}
        </template>
      </el-table-column>
      <el-table-column prop="sort_order" label="排序" width="80" />
      <el-table-column prop="is_active" label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
            {{ row.is_active ? '上架' : '下架' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="SKU" width="80">
        <template #default="{ row }">
          <el-tag v-if="row.has_sku" type="warning" size="small">SKU</el-tag>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click="openEdit(row)">编辑</el-button>
          <el-button link type="primary" size="small" @click="toggleActive(row)">
            {{ row.is_active ? '下架' : '上架' }}
          </el-button>
          <el-button link type="danger" size="small" @click="handleDelete(row)">删除</el-button>
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
.point-shop-container {
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
