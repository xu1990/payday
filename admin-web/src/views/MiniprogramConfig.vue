<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  listConfigs,
  createConfig,
  updateConfig,
  deleteConfig,
  type MiniprogramConfigItem,
  type MiniprogramConfigCreate,
} from '@/api/miniprogram'

const list = ref<MiniprogramConfigItem[]>([])
const loading = ref(false)

// 表单
const showDialog = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const editId = ref<string | null>(null)
const form = ref<MiniprogramConfigCreate>({
  key: '',
  value: '',
  description: '',
  sort_order: 0,
})

async function loadData() {
  loading.value = true
  try {
    const res = await listConfigs()
    list.value = res?.data || []
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
    key: '',
    value: '',
    description: '',
    sort_order: 0,
  }
  showDialog.value = true
}

function openEdit(item: MiniprogramConfigItem) {
  dialogMode.value = 'edit'
  editId.value = item.id
  form.value = {
    key: item.key,
    value: item.value || '',
    description: item.description || '',
    sort_order: item.sort_order,
  }
  showDialog.value = true
}

async function submit() {
  if (!form.value.key?.trim()) {
    ElMessage.warning('请输入配置键')
    return
  }

  try {
    if (dialogMode.value === 'create') {
      const res = await createConfig(form.value)
      if (res.message && res.message.includes('已存在')) {
        ElMessage.warning(res.message)
        return
      }
      ElMessage.success('创建成功')
    } else if (editId.value) {
      await updateConfig(editId.value, {
        value: form.value.value,
        description: form.value.description,
        sort_order: form.value.sort_order,
      })
      ElMessage.success('更新成功')
    }
    showDialog.value = false
    await loadData()
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : '操作失败'
    ElMessage.error(errorMessage)
  }
}

function doDelete(item: MiniprogramConfigItem) {
  ElMessageBox.confirm(`确定要删除配置「${item.key}」吗？`, '确认删除', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  })
    .then(async () => {
      try {
        await deleteConfig(item.id)
        ElMessage.success('删除成功')
        await loadData()
      } catch (e: unknown) {
        const errorMessage = e instanceof Error ? e.message : '删除失败'
        ElMessage.error(errorMessage)
      }
    })
    .catch(() => {})
}

async function toggleActive(item: MiniprogramConfigItem) {
  try {
    await updateConfig(item.id, { is_active: !item.is_active })
    ElMessage.success(item.is_active ? '已禁用' : '已启用')
    await loadData()
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : '操作失败'
    ElMessage.error(errorMessage)
  }
}

function formatDate(isoString: string | null) {
  if (!isoString) return '-'
  return new Date(isoString).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="miniprogram-page">
    <div class="header">
      <h2>小程序配置管理</h2>
      <el-button type="primary" @click="openCreate">创建配置</el-button>
    </div>

    <el-table :data="list" v-loading="loading" stripe border style="width: 100%">
      <el-table-column prop="key" label="配置键" width="200" />
      <el-table-column prop="value" label="配置值" min-width="250" show-overflow-tooltip />
      <el-table-column prop="description" label="说明" width="200" show-overflow-tooltip />
      <el-table-column prop="sort_order" label="排序" width="80" align="center" />
      <el-table-column label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
            {{ row.is_active ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="更新时间" width="180">
        <template #default="{ row }">
          {{ formatDate(row.updated_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="260" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" :type="row.is_active ? 'warning' : 'success'" @click="toggleActive(row)">
            {{ row.is_active ? '禁用' : '启用' }}
          </el-button>
          <el-button size="small" type="danger" @click="doDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="showDialog"
      :title="dialogMode === 'create' ? '创建配置' : '编辑配置'"
      width="600px"
    >
      <el-form :model="form" label-width="100px">
        <el-form-item label="配置键" required>
          <el-input
            v-model="form.key"
            placeholder="例如：app_name, logo_url, privacy_policy"
            maxlength="50"
            show-word-limit
            :disabled="dialogMode === 'edit'"
          />
          <div class="form-tip">常用配置键：app_name（应用名称）、logo_url（Logo）、splash_image（开屏图）、privacy_policy（隐私协议）</div>
        </el-form-item>
        <el-form-item label="配置值">
          <el-input
            v-model="form.value"
            type="textarea"
            :rows="4"
            placeholder="请输入配置值（支持JSON或纯文本）"
            maxlength="1000"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="配置说明">
          <el-input
            v-model="form.description"
            placeholder="请输入配置说明"
            maxlength="200"
            show-word-limit
          />
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
.miniprogram-page {
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
.form-tip {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
  line-height: 1.5;
}
</style>
