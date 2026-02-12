<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  listTopics,
  createTopic,
  updateTopic,
  deleteTopic,
  type TopicItem,
  type TopicCreate,
} from '@/api/topics'
import BaseDataTable from '@/components/BaseDataTable.vue'
import StatusTag from '@/components/StatusTag.vue'
import ActionButtons from '@/components/ActionButtons.vue'
import { formatDate } from '@/utils/format'

const list = ref<TopicItem[]>([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = 20

// 表单
const showDialog = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const editId = ref<string | null>(null)
const form = ref<TopicCreate>({
  name: '',
  description: '',
  cover_image: '',
  sort_order: 0,
})

async function loadData() {
  loading.value = true
  try {
    const res = await listTopics({
      limit: pageSize,
      offset: (currentPage.value - 1) * pageSize,
    })
    list.value = res?.data?.items || []
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
    name: '',
    description: '',
    cover_image: '',
    sort_order: 0,
  }
  showDialog.value = true
}

function openEdit(item: TopicItem) {
  dialogMode.value = 'edit'
  editId.value = item.id
  form.value = {
    name: item.name,
    description: item.description || '',
    cover_image: item.cover_image || '',
    sort_order: item.sort_order,
  }
  showDialog.value = true
}

async function submit() {
  if (!form.value.name?.trim()) {
    ElMessage.warning('请输入话题名称')
    return
  }

  try {
    if (dialogMode.value === 'create') {
      await createTopic(form.value)
      ElMessage.success('创建成功')
    } else if (editId.value) {
      await updateTopic(editId.value, {
        name: form.value.name,
        description: form.value.description,
        cover_image: form.value.cover_image,
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

function doDelete(item: TopicItem) {
  ElMessageBox.confirm(`确定要删除话题「${item.name}」吗？`, '确认删除', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  })
    .then(async () => {
      try {
        await deleteTopic(item.id)
        ElMessage.success('删除成功')
        await loadData()
      } catch (e: unknown) {
        const errorMessage = e instanceof Error ? e.message : '删除失败'
        ElMessage.error(errorMessage)
      }
    })
    .catch(() => {})
}

async function toggleActive(item: TopicItem) {
  try {
    await updateTopic(item.id, {
      name: item.name,
      description: item.description,
      cover_image: item.cover_image,
      is_active: !item.is_active,
      sort_order: item.sort_order,
    })
    ElMessage.success(item.is_active ? '已禁用' : '已启用')
    await loadData()
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : '操作失败'
    ElMessage.error(errorMessage)
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
  <div class="topics-page">
    <div class="header">
      <h2>话题管理</h2>
      <el-button type="primary" @click="openCreate">创建话题</el-button>
    </div>

    <BaseDataTable
      v-model:current-page="currentPage"
      :items="list"
      :total="total"
      :loading="loading"
      @page-change="handlePageChange"
    >
      <el-table-column prop="name" label="话题名称" width="200" />
      <el-table-column prop="description" label="描述" show-overflow-tooltip />
      <el-table-column label="封面" width="120">
        <template #default="{ row }">
          <el-image
            v-if="row.cover_image"
            :src="row.cover_image"
            fit="cover"
            style="width: 60px; height: 40px; border-radius: var(--radius-sm)"
          />
          <span v-else class="text-muted">-</span>
        </template>
      </el-table-column>
      <el-table-column prop="post_count" label="帖子数" width="100" align="center" />
      <el-table-column prop="sort_order" label="排序" width="80" align="center" />
      <el-table-column label="状态" width="100" align="center">
        <template #default="{ row }">
          <StatusTag :status="row.is_active ? 'active' : 'inactive'" />
        </template>
      </el-table-column>
      <el-table-column label="创建时间" width="180">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <ActionButtons
            :is-active="row.is_active"
            @edit="openEdit(row)"
            @toggle="toggleActive(row)"
            @delete="doDelete(row)"
          />
        </template>
      </el-table-column>
    </BaseDataTable>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="showDialog"
      :title="dialogMode === 'create' ? '创建话题' : '编辑话题'"
      width="600px"
    >
      <el-form :model="form" label-width="100px">
        <el-form-item label="话题名称" required>
          <el-input v-model="form.name" placeholder="请输入话题名称" maxlength="50" show-word-limit />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入话题描述"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="封面图片">
          <el-input v-model="form.cover_image" placeholder="请输入图片URL" />
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
.topics-page {
  padding: var(--spacing-xl);
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-xl);
}
.header h2 {
  margin: 0;
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
}
.text-muted {
  color: var(--color-text-secondary);
}
</style>
