<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  listPointProducts,
  deletePointProduct,
  updatePointProduct,
  type PointProduct,
} from '@/api/pointShop'
import { listSKUs, type SKUResponse } from '@/api/pointSku'
import { getCategoryTree } from '@/api/pointCategory'
import type { PointCategory } from '@/api/pointCategory'
import { formatDate } from '@/utils/format'

const router = useRouter()

const list = ref<PointProduct[]>([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = 20

// 筛选条件
const filters = reactive({
  product_type: '',
  category_id: '',
  is_active: undefined as boolean | undefined,
  keyword: '',
})
const categoryOptions = ref<PointCategory[]>([])

const productTypeOptions = [
  { label: '全部', value: '' },
  { label: '虚拟商品', value: 'virtual' },
  { label: '实物商品', value: 'physical' },
  { label: '套餐商品', value: 'bundle' },
]

const statusOptions = [
  { label: '全部', value: undefined },
  { label: '上架', value: true },
  { label: '下架', value: false },
]

const skuDialogVisible = ref(false)
const currentSkus = ref<SKUResponse[]>([])
const skuLoading = ref(false)

// 下架/删除原因相关
const reasonDialogVisible = ref(false)
const reasonDialogTitle = ref('')
const reasonForm = reactive({
  productId: '',
  actionType: '' as 'off-shelf' | 'delete',
  reason: '',
})

async function loadCategories() {
  try {
    const tree = await getCategoryTree(true)
    categoryOptions.value = flattenCategories(tree || [])
  } catch (e: unknown) {
    console.error('加载分类失败', e)
  }
}

function flattenCategories(categories: PointCategory[]): PointCategory[] {
  const result: PointCategory[] = []
  for (const cat of categories) {
    result.push(cat)
    if (cat.children?.length) {
      result.push(...flattenCategories(cat.children))
    }
  }
  return result
}

async function loadData() {
  loading.value = true
  try {
    const res = await listPointProducts({
      active_only: false,
      category_id: filters.category_id || undefined,
      is_active: filters.is_active,
      keyword: filters.keyword || undefined,
      product_type: filters.product_type || undefined,
    })
    list.value = res?.products || []
    total.value = res?.total || 0
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : '加载失败'
    ElMessage.error(errorMessage)
  } finally {
    loading.value = false
  }
}

function handleFilter() {
  currentPage.value = 1
  loadData()
}

function openCreate() {
  router.push('/point-shop/create')
}

function openEdit(item: PointProduct) {
  router.push(`/point-shop/${item.id}/edit`)
}

async function openSkuList(row: PointProduct) {
  skuDialogVisible.value = true
  skuLoading.value = true
  currentSkus.value = []
  try {
    const res = await listSKUs(row.id, false)
    currentSkus.value = res?.skus || []
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : '加载SKU失败'
    ElMessage.error(errorMessage)
  } finally {
    skuLoading.value = false
  }
}

// 下架操作
function handleOffShelf(item: PointProduct) {
  reasonDialogTitle.value = '下架商品'
  reasonForm.productId = item.id
  reasonForm.actionType = 'off-shelf'
  reasonForm.reason = ''
  reasonDialogVisible.value = true
}

// 删除操作
function handleDelete(item: PointProduct) {
  reasonDialogTitle.value = '删除商品'
  reasonForm.productId = item.id
  reasonForm.actionType = 'delete'
  reasonForm.reason = ''
  reasonDialogVisible.value = true
}

// 确认操作
async function confirmAction() {
  if (!reasonForm.reason.trim()) {
    ElMessage.warning('请填写原因')
    return
  }

  try {
    if (reasonForm.actionType === 'off-shelf') {
      await updatePointProduct(reasonForm.productId, {
        is_active: false,
        off_shelf_reason: reasonForm.reason,
      })
      ElMessage.success('已下架')
    } else {
      await deletePointProduct(reasonForm.productId, reasonForm.reason)
      ElMessage.success('删除成功')
    }
    reasonDialogVisible.value = false
    await loadData()
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : '操作失败'
    ElMessage.error(errorMessage)
  }
}

// 上架操作
async function handleOnShelf(item: PointProduct) {
  try {
    await updatePointProduct(item.id, { is_active: true })
    ElMessage.success('已上架')
    await loadData()
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : '操作失败'
    ElMessage.error(errorMessage)
  }
}

onMounted(() => {
  loadCategories()
  loadData()
})
</script>

<template>
  <div class="point-shop-container">
    <div class="page-header">
      <h2>积分商品管理</h2>
      <el-button type="primary" @click="openCreate">新建商品</el-button>
    </div>

    <!-- 筛选条件 -->
    <div class="filter-section">
      <el-select
        v-model="filters.product_type"
        placeholder="商品类型"
        clearable
        style="width: 120px"
        @change="handleFilter"
      >
        <el-option
          v-for="item in productTypeOptions"
          :key="item.value"
          :label="item.label"
          :value="item.value"
        />
      </el-select>
      <el-select
        v-model="filters.category_id"
        placeholder="商品分类"
        clearable
        style="width: 150px"
        @change="handleFilter"
      >
        <el-option
          v-for="cat in categoryOptions"
          :key="cat.id"
          :label="cat.name"
          :value="cat.id"
        />
      </el-select>
      <el-select
        v-model="filters.is_active"
        placeholder="上架状态"
        clearable
        style="width: 100px"
        @change="handleFilter"
      >
        <el-option
          v-for="item in statusOptions"
          :key="String(item.value)"
          :label="item.label"
          :value="item.value"
        />
      </el-select>
      <el-input
        v-model="filters.keyword"
        placeholder="搜索商品名称"
        clearable
        style="width: 200px"
        @keyup.enter="handleFilter"
        @clear="handleFilter"
      />
      <el-button type="primary" @click="handleFilter">搜索</el-button>
    </div>

    <el-table :data="list" v-loading="loading" stripe>
      <el-table-column prop="name" label="商品名称" width="180" />
      <el-table-column prop="category" label="分类" width="100">
        <template #default="{ row }">
          {{ row.category || '-' }}
        </template>
      </el-table-column>
      <el-table-column label="类型" width="80">
        <template #default="{ row }">
          <el-tag v-if="row.product_type === 'virtual'" type="info" size="small">虚拟</el-tag>
          <el-tag v-else-if="row.product_type === 'bundle'" type="warning" size="small">套餐</el-tag>
          <el-tag v-else type="success" size="small">实物</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="主图" width="80">
        <template #default="{ row }">
          <el-image
            v-if="row.image_urls && row.image_urls.length > 0"
            :src="row.image_urls[0]"
            fit="cover"
            style="width: 50px; height: 50px; border-radius: 4px"
            :preview-src-list="row.image_urls"
          />
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column prop="points_cost" label="积分" width="80">
        <template #default="{ row }">
          {{ row.points_cost }}
        </template>
      </el-table-column>
      <el-table-column label="库存" width="80">
        <template #default="{ row }">
          <template v-if="row.has_sku">
            <span v-if="row.stock_unlimited" class="stock-unlimited">无限</span>
            <span v-else>{{ row.stock }}</span>
            <el-tag type="warning" size="small" style="margin-left: 4px">多规格</el-tag>
          </template>
          <template v-else>
            {{ row.stock_unlimited ? '无限' : row.stock }}
          </template>
        </template>
      </el-table-column>
      <el-table-column label="销量" width="70">
        <template #default="{ row }">
          {{ row.total_sold || row.sold || 0 }}
        </template>
      </el-table-column>
      <el-table-column label="SKU" width="70">
        <template #default="{ row }">
          <el-button v-if="row.has_sku" link type="primary" size="small" @click="openSkuList(row)">
            查看
          </el-button>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column prop="is_active" label="状态" width="70">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
            {{ row.is_active ? '上架' : '下架' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="sort_order" label="排序" width="60" />
      <el-table-column prop="created_at" label="创建时间" width="150">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click="openEdit(row)">编辑</el-button>
          <template v-if="row.is_active">
            <el-button link type="warning" size="small" @click="handleOffShelf(row)">下架</el-button>
          </template>
          <template v-else>
            <el-button link type="success" size="small" @click="handleOnShelf(row)">上架</el-button>
          </template>
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

  <!-- SKU Dialog -->
  <el-dialog v-model="skuDialogVisible" title="SKU列表" width="800">
    <el-table :data="currentSkus" v-loading="skuLoading" stripe>
      <el-table-column prop="sku_code" label="SKU编码" width="120" />
      <el-table-column label="规格" width="150">
        <template #default="{ row }">
          <div v-for="(value, key) in row.specs" :key="key">
            {{ key }}: {{ value }}
          </div>
        </template>
      </el-table-column>
      <el-table-column label="库存" width="80">
        <template #default="{ row }">
          {{ row.stock_unlimited ? '无限' : row.stock }}
        </template>
      </el-table-column>
      <el-table-column label="销量" width="80">
        <template #default="{ row }">
          {{ row.sold || 0 }}
        </template>
      </el-table-column>
      <el-table-column prop="points_cost" label="积分" width="80">
        <template #default="{ row }">
          {{ row.points_cost }}
        </template>
      </el-table-column>
      <el-table-column label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
            {{ row.is_active ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
    </el-table>
  </el-dialog>

  <!-- 下架/删除原因弹窗 -->
  <el-dialog v-model="reasonDialogVisible" :title="reasonDialogTitle" width="400px">
    <el-form label-width="80px">
      <el-form-item label="原因" required>
        <el-input
          v-model="reasonForm.reason"
          type="textarea"
          :rows="3"
          placeholder="请填写下架/删除原因"
          style="width: 100%"
          resize="none"
        />
      </el-form-item>
    </el-form>
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="reasonDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmAction" :disabled="!reasonForm.reason.trim()">
          确定
        </el-button>
      </span>
    </template>
  </el-dialog>
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

.filter-section {
  display: flex;
  gap: 10px;
  margin-bottom: 15px;
  flex-wrap: wrap;
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.stock-unlimited {
  color: #67c23a;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>
