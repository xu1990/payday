<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  listMemberships,
  createMembership,
  updateMembership,
  deleteMembership,
  type MembershipItem,
  type MembershipCreate,
} from '@/api/membership'

const list = ref<MembershipItem[]>([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = 20

// 表单
const showDialog = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const editId = ref<string | null>(null)
const form = ref<MembershipCreate>({
  name: '',
  description: '',
  price: 0,
  duration_days: 30,
  sort_order: 0,
})

async function loadData() {
  loading.value = true
  try {
    const res = await listMemberships({
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

function openCreate() {
  dialogMode.value = 'create'
  editId.value = null
  form.value = {
    name: '',
    description: '',
    price: 0,
    duration_days: 30,
    sort_order: 0,
  }
  showDialog.value = true
}

function openEdit(item: MembershipItem) {
  dialogMode.value = 'edit'
  editId.value = item.id
  form.value = {
    name: item.name,
    description: item.description || '',
    price: Number(item.price) / 100, // 转换为元
    duration_days: item.duration_days,
    sort_order: item.sort_order,
  }
  showDialog.value = true
}

async function submit() {
  if (!form.value.name?.trim()) {
    ElMessage.warning('请输入套餐名称')
    return
  }
  if (form.value.price <= 0) {
    ElMessage.warning('请输入有效价格')
    return
  }
  if (form.value.duration_days <= 0) {
    ElMessage.warning('请输入有效天数')
    return
  }

  try {
    const payload = {
      ...form.value,
      price: form.value.price * 100, // 转换为分
    }

    if (dialogMode.value === 'create') {
      await createMembership(payload)
      ElMessage.success('创建成功')
    } else if (editId.value) {
      await updateMembership(editId.value, payload)
      ElMessage.success('更新成功')
    }
    showDialog.value = false
    await loadData()
  } catch (e: any) {
    ElMessage.error(e?.message || '操作失败')
  }
}

function doDelete(item: MembershipItem) {
  ElMessageBox.confirm(`确定要删除会员套餐「${item.name}」吗？`, '确认删除', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  })
    .then(async () => {
      try {
        await deleteMembership(item.id)
        ElMessage.success('删除成功')
        await loadData()
      } catch (e: any) {
        ElMessage.error(e?.message || '删除失败')
      }
    })
    .catch(() => {})
}

async function toggleActive(item: MembershipItem) {
  try {
    await updateMembership(item.id, {
      name: item.name,
      description: item.description,
      price: Number(item.price) / 100,
      duration_days: item.duration_days,
      sort_order: item.sort_order,
      is_active: !item.is_active,
    })
    ElMessage.success(item.is_active ? '已禁用' : '已启用')
    await loadData()
  } catch (e: any) {
    ElMessage.error(e?.message || '操作失败')
  }
}

function handlePageChange(page: number) {
  currentPage.value = page
  loadData()
}

function formatPrice(priceInCents: number): string {
  return (priceInCents / 100).toFixed(2)
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="memberships-page">
    <div class="header">
      <h2>会员套餐管理</h2>
      <el-button type="primary" @click="openCreate">创建套餐</el-button>
    </div>

    <el-table v-loading="loading" :data="list" stripe>
      <el-table-column prop="name" label="套餐名称" width="200" />
      <el-table-column prop="description" label="权益说明" show-overflow-tooltip />
      <el-table-column label="价格" width="120">
        <template #default="{ row }">
          <span class="price">¥{{ formatPrice(row.price) }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="duration_days" label="有效期（天）" width="120" align="center" />
      <el-table-column prop="sort_order" label="排序" width="80" align="center" />
      <el-table-column label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
            {{ row.is_active ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="创建时间" width="180">
        <template #default="{ row }">
          {{ new Date(row.created_at).toLocaleString() }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="280" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click="openEdit(row)">
            编辑
          </el-button>
          <el-button
            link
            :type="row.is_active ? 'warning' : 'success'"
            size="small"
            @click="toggleActive(row)"
          >
            {{ row.is_active ? '禁用' : '启用' }}
          </el-button>
          <el-button link type="danger" size="small" @click="doDelete(row)">
            删除
          </el-button>
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

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="showDialog"
      :title="dialogMode === 'create' ? '创建套餐' : '编辑套餐'"
      width="600px"
    >
      <el-form :model="form" label-width="100px">
        <el-form-item label="套餐名称" required>
          <el-input v-model="form.name" placeholder="请输入套餐名称" maxlength="50" show-word-limit />
        </el-form-item>
        <el-form-item label="权益说明">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入权益说明"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="价格（元）" required>
          <el-input-number v-model="form.price" :min="0" :precision="2" controls-position="right" />
        </el-form-item>
        <el-form-item label="有效期（天）" required>
          <el-input-number v-model="form.duration_days" :min="1" controls-position="right" />
        </el-form-item>
        <el-form-item label="排序权重">
          <el-input-number v-model="form.sort_order" :min="0" controls-position="right" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="submit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.memberships-page {
  padding: 24px;
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
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
