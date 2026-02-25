<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  listCouriers,
  createCourier,
  updateCourier,
  deleteCourier,
  type CourierCompany,
  type CourierCreate,
} from '@/api/courier'
import { formatDate } from '@/utils/format'

const list = ref<CourierCompany[]>([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = 20

// 表单
const showDialog = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const editId = ref<string | null>(null)
const form = ref<CourierCreate>({
  code: '',
  name: '',
  website: null,
  tracking_url: null,
  supports_cod: false,
  supports_cold_chain: false,
  sort_order: 0,
  is_active: true,
})

// 自动大写代码
const handleCodeInput = (value: string) => {
  form.value.code = value.toUpperCase()
}

async function loadData() {
  loading.value = true
  try {
    const res = await listCouriers({
      limit: pageSize,
      offset: (currentPage.value - 1) * pageSize,
    })
    list.value = res?.data?.couriers || []
    total.value = res?.data?.total || 0
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : '加载失败'
    ElMessage.error(errorMessage)
  } finally {
    loading.value = false
  }
}

function openCreate() {
  dialogMode.value = 'create'
  editId.value = null
  form.value = {
    code: '',
    name: '',
    website: null,
    tracking_url: null,
    supports_cod: false,
    supports_cold_chain: false,
    sort_order: 0,
    is_active: true,
  }
  showDialog.value = true
}

function openEdit(item: CourierCompany) {
  dialogMode.value = 'edit'
  editId.value = item.id
  form.value = {
    code: item.code,
    name: item.name,
    website: item.website,
    tracking_url: item.tracking_url,
    supports_cod: item.supports_cod,
    supports_cold_chain: item.supports_cold_chain,
    sort_order: item.sort_order,
    is_active: item.is_active,
  }
  showDialog.value = true
}

async function submit() {
  if (!form.value.code?.trim()) {
    ElMessage.warning('请输入物流公司代码')
    return
  }
  if (!form.value.name?.trim()) {
    ElMessage.warning('请输入物流公司名称')
    return
  }

  try {
    if (dialogMode.value === 'create') {
      await createCourier(form.value)
      ElMessage.success('创建成功')
    } else {
      if (!editId.value) return
      await updateCourier(editId.value, form.value)
      ElMessage.success('更新成功')
    }
    showDialog.value = false
    await loadData()
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : '操作失败'
    ElMessage.error(errorMessage)
  }
}

async function handleDelete(item: CourierCompany) {
  try {
    await ElMessageBox.confirm(`确定要删除物流公司"${item.name}"吗？`, '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await deleteCourier(item.id)
    ElMessage.success('删除成功')
    await loadData()
  } catch (e: unknown) {
    if (e === 'cancel') return
    const errorMessage = e instanceof Error ? e.message : '删除失败'
    ElMessage.error(errorMessage)
  }
}

async function toggleActive(item: CourierCompany) {
  try {
    await updateCourier(item.id, { is_active: !item.is_active })
    ElMessage.success(item.is_active ? '已禁用' : '已启用')
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
  <div class="couriers-container">
    <div class="page-header">
      <h2>物流公司管理</h2>
      <el-button type="primary" @click="openCreate">新建物流公司</el-button>
    </div>

    <el-table v-loading="loading" :data="list" stripe>
      <el-table-column prop="code" label="代码" width="100" />
      <el-table-column prop="name" label="名称" width="150" />
      <el-table-column prop="website" label="网站" width="180">
        <template #default="{ row }">
          <a
            v-if="row.website"
            :href="row.website"
            target="_blank"
            rel="noopener"
            class="link-text"
          >
            {{ row.website }}
          </a>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column prop="tracking_url" label="查询网址" width="200">
        <template #default="{ row }">
          <a
            v-if="row.tracking_url"
            :href="row.tracking_url"
            target="_blank"
            rel="noopener"
            class="link-text"
          >
            {{ row.tracking_url }}
          </a>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column label="支持服务" width="150">
        <template #default="{ row }">
          <el-tag v-if="row.supports_cod" type="success" size="small" style="margin-right: 4px"
            >货到付款</el-tag
          >
          <el-tag v-if="row.supports_cold_chain" type="info" size="small">冷链</el-tag>
          <span v-if="!row.supports_cod && !row.supports_cold_chain">-</span>
        </template>
      </el-table-column>
      <el-table-column prop="sort_order" label="排序" width="80" />
      <el-table-column prop="is_active" label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
            {{ row.is_active ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="240" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click="openEdit(row)">编辑</el-button>
          <el-button link type="primary" size="small" @click="toggleActive(row)">
            {{ row.is_active ? '禁用' : '启用' }}
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

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="showDialog"
      :title="dialogMode === 'create' ? '新建物流公司' : '编辑物流公司'"
      width="600px"
    >
      <el-form :model="form" label-width="120px">
        <el-form-item label="物流公司代码" required>
          <el-input
            v-model="form.code"
            placeholder="如: SF, ZTO, YTO"
            maxlength="10"
            @input="handleCodeInput"
          />
          <div class="form-hint">英文大写字母，如 SF（顺丰）、ZTO（中通）</div>
        </el-form-item>

        <el-form-item label="物流公司名称" required>
          <el-input v-model="form.name" placeholder="如: 顺丰速运" />
        </el-form-item>

        <el-form-item label="官网">
          <el-input v-model="form.website" placeholder="https://www.sf-express.com" />
        </el-form-item>

        <el-form-item label="物流查询网址">
          <el-input v-model="form.tracking_url" placeholder="https://www.sf-express.com/track" />
          <div class="form-hint">用户可通过此网址查询物流信息</div>
        </el-form-item>

        <el-form-item label="支持服务">
          <el-checkbox v-model="form.supports_cod">货到付款</el-checkbox>
          <el-checkbox v-model="form.supports_cold_chain">冷链运输</el-checkbox>
        </el-form-item>

        <el-form-item label="排序权重">
          <el-input-number v-model="form.sort_order" :min="0" :max="9999" />
          <span style="margin-left: 10px; color: #999; font-size: 12px">数值越大越靠前</span>
        </el-form-item>

        <el-form-item label="状态">
          <el-checkbox v-model="form.is_active">启用</el-checkbox>
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
.couriers-container {
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

.link-text {
  color: #409eff;
  text-decoration: none;
  word-break: break-all;
}

.link-text:hover {
  text-decoration: underline;
}

.form-hint {
  margin-top: 4px;
  font-size: 12px;
  color: #909399;
  line-height: 1.5;
}
</style>
