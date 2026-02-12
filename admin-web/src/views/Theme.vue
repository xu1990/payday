<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  listThemes,
  createTheme,
  updateTheme,
  deleteTheme,
  type ThemeItem,
  type ThemeCreate,
} from '@/api/theme'

const list = ref<ThemeItem[]>([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = 20

// 表单
const showDialog = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const editId = ref<string | null>(null)
const form = ref<ThemeCreate>({
  name: '',
  code: '',
  preview_image: '',
  config: '',
  sort_order: 0,
})

async function loadData() {
  loading.value = true
  try {
    const res = await listThemes({
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
    code: '',
    preview_image: '',
    config: '',
    is_premium: false,
    sort_order: 0,
  }
  showDialog.value = true
}

function openEdit(item: ThemeItem) {
  dialogMode.value = 'edit'
  editId.value = item.id
  form.value = {
    name: item.name,
    code: item.code,
    preview_image: item.preview_image || '',
    config: item.config || '',
    is_premium: item.is_premium,
    sort_order: item.sort_order,
  }
  showDialog.value = true
}

async function submit() {
  if (!form.value.name?.trim()) {
    ElMessage.warning('请输入主题名称')
    return
  }
  if (!form.value.code?.trim()) {
    ElMessage.warning('请输入主题代码')
    return
  }

  try {
    if (dialogMode.value === 'create') {
      await createTheme(form.value)
      ElMessage.success('创建成功')
    } else if (editId.value) {
      await updateTheme(editId.value, form.value)
      ElMessage.success('更新成功')
    }
    showDialog.value = false
    await loadData()
  } catch (e: any) {
    ElMessage.error(e?.message || '操作失败')
  }
}

function doDelete(item: ThemeItem) {
  ElMessageBox.confirm(`确定要删除主题「${item.name}」吗？`, '确认删除', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  })
    .then(async () => {
      try {
        await deleteTheme(item.id)
        ElMessage.success('删除成功')
        await loadData()
      } catch (e: any) {
        ElMessage.error(e?.message || '删除失败')
      }
    })
    .catch(() => {})
}

async function toggleActive(item: ThemeItem) {
  try {
    await updateTheme(item.id, {
      name: item.name,
      code: item.code,
      preview_image: item.preview_image,
      config: item.config,
      is_premium: item.is_premium,
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

onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="themes-page">
    <div class="header">
      <h2>主题配置管理</h2>
      <el-button type="primary" @click="openCreate">创建主题</el-button>
    </div>

    <el-table v-loading="loading" :data="list" stripe>
      <el-table-column prop="name" label="主题名称" width="200" />
      <el-table-column prop="code" label="主题代码" width="150" />
      <el-table-column label="预览图" width="120">
        <template #default="{ row }">
          <el-image
            v-if="row.preview_image"
            :src="row.preview_image"
            fit="cover"
            style="width: 60px; height: 40px; border-radius: 4px"
          />
          <span v-else class="text-muted">-</span>
        </template>
      </el-table-column>
      <el-table-column prop="is_premium" label="类型" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="row.is_premium ? 'warning' : ''" size="small">
            {{ row.is_premium ? '会员专属' : '免费' }}
          </el-tag>
        </template>
      </el-table-column>
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
      :title="dialogMode === 'create' ? '创建主题' : '编辑主题'"
      width="700px"
    >
      <el-form :model="form" label-width="120px">
        <el-form-item label="主题名称" required>
          <el-input v-model="form.name" placeholder="请输入主题名称" maxlength="50" show-word-limit />
        </el-form-item>
        <el-form-item label="主题代码" required>
          <el-input v-model="form.code" placeholder="请输入主题代码（唯一标识）" maxlength="50" show-word-limit />
        </el-form-item>
        <el-form-item label="预览图">
          <el-input v-model="form.preview_image" placeholder="请输入图片URL" maxlength="500" />
        </el-form-item>
        <el-form-item label="主题配置（JSON）">
          <el-input
            v-model="form.config"
            type="textarea"
            :rows="5"
            placeholder='{"primaryColor": "#07c160", "fontScale": 1.0}'
            maxlength="1000"
          />
        </el-form-item>
        <el-form-item label="排序权重">
          <el-input-number v-model="form.sort_order" :min="0" controls-position="right" />
        </el-form-item>
        <el-form-item label="会员专属">
          <el-switch v-model="form.is_premium" />
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
.themes-page {
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
.pagination {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}
.text-muted {
  color: #999;
}
</style>
