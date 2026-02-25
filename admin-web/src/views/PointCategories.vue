<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Folder, FolderOpened, Close } from '@element-plus/icons-vue'
import type { UploadRequestOptions } from 'element-plus'
import {
  getCategoryTree,
  createPointCategory,
  updatePointCategory,
  deletePointCategory,
  type PointCategory,
  type PointCategoryCreate,
  type PointCategoryUpdate,
} from '@/api/pointCategory'
import adminApi from '@/api/admin'

// Tree data
const treeData = ref<PointCategory[]>([])
const treeLoading = ref(false)
const selectedNode = ref<PointCategory | null>(null)
const selectedNodeId = ref<string | null>(null)

// Form
const showForm = ref(false)
const formMode = ref<'create' | 'edit'>('create')
const editId = ref<string | null>(null)
const uploading = ref(false)
const form = ref<PointCategoryCreate>({
  name: '',
  level: 1,
  description: '',
  parent_id: null,
  icon_url: null,
  banner_url: null,
  sort_order: 0,
  is_active: true,
})

// Image upload handlers
const handleIconUpload = async (options: UploadRequestOptions) => {
  const { file, onSuccess, onError } = options
  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', file)

    const res = await adminApi.post('/admin/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })

    const url = res.data?.details?.url || res.data?.url
    if (url) {
      form.value.icon_url = url
      ElMessage.success('图标上传成功')
      onSuccess?.(res.data)
    } else {
      throw new Error('上传失败：未返回URL')
    }
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : '上传失败'
    ElMessage.error(errorMessage)
    onError?.(e as Error)
  } finally {
    uploading.value = false
  }
}

const handleBannerUpload = async (options: UploadRequestOptions) => {
  const { file, onSuccess, onError } = options
  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', file)

    const res = await adminApi.post('/admin/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })

    const url = res.data?.details?.url || res.data?.url
    if (url) {
      form.value.banner_url = url
      ElMessage.success('横幅上传成功')
      onSuccess?.(res.data)
    } else {
      throw new Error('上传失败：未返回URL')
    }
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : '上传失败'
    ElMessage.error(errorMessage)
    onError?.(e as Error)
  } finally {
    uploading.value = false
  }
}

const beforeImageUpload = (rawFile: File) => {
  if (!rawFile.type.startsWith('image/')) {
    ElMessage.error('只能上传图片文件')
    return false
  }
  if (rawFile.size / 1024 / 1024 > 5) {
    ElMessage.error('图片大小不能超过5MB')
    return false
  }
  return true
}

const removeIcon = () => {
  form.value.icon_url = null
}

const removeBanner = () => {
  form.value.banner_url = null
}

// Load tree data
async function loadTree() {
  treeLoading.value = true
  try {
    const res = await getCategoryTree({ active_only: false })
    treeData.value = res?.data || []
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : '加载失败'
    ElMessage.error(errorMessage)
  } finally {
    treeLoading.value = false
  }
}

// Tree node click
function handleNodeClick(data: PointCategory) {
  selectedNode.value = data
  selectedNodeId.value = data.id
}

// Open create form (root category)
function openCreateRoot() {
  formMode.value = 'create'
  editId.value = null
  form.value = {
    name: '',
    level: 1,
    description: '',
    parent_id: null,
    icon_url: null,
    banner_url: null,
    sort_order: 0,
    is_active: true,
  }
  showForm.value = true
}

// Open create form (subcategory)
function openCreateSubcategory() {
  if (!selectedNode.value) {
    ElMessage.warning('请先选择父分类')
    return
  }
  if (selectedNode.value.level >= 3) {
    ElMessage.warning('最多支持3级分类')
    return
  }

  formMode.value = 'create'
  editId.value = null
  form.value = {
    name: '',
    level: selectedNode.value.level + 1,
    description: '',
    parent_id: selectedNode.value.id,
    icon_url: null,
    banner_url: null,
    sort_order: 0,
    is_active: true,
  }
  showForm.value = true
}

// Open edit form
function openEdit() {
  if (!selectedNode.value) {
    ElMessage.warning('请先选择要编辑的分类')
    return
  }

  formMode.value = 'edit'
  editId.value = selectedNode.value.id
  form.value = {
    name: selectedNode.value.name,
    level: selectedNode.value.level,
    description: selectedNode.value.description || '',
    parent_id: selectedNode.value.parent_id,
    icon_url: selectedNode.value.icon_url,
    banner_url: selectedNode.value.banner_url,
    sort_order: selectedNode.value.sort_order,
    is_active: selectedNode.value.is_active,
  }
  showForm.value = true
}

// Submit form
async function submit() {
  if (!form.value.name?.trim()) {
    ElMessage.warning('请输入分类名称')
    return
  }

  try {
    if (formMode.value === 'create') {
      await createPointCategory(form.value)
      ElMessage.success('创建成功')
    } else {
      if (!editId.value) return
      const updateData: PointCategoryUpdate = {
        name: form.value.name,
        description: form.value.description,
        icon_url: form.value.icon_url,
        banner_url: form.value.banner_url,
        sort_order: form.value.sort_order,
        is_active: form.value.is_active,
      }
      await updatePointCategory(editId.value, updateData)
      ElMessage.success('更新成功')
    }
    showForm.value = false
    selectedNode.value = null
    selectedNodeId.value = null
    await loadTree()
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : '操作失败'
    ElMessage.error(errorMessage)
  }
}

// Delete category
async function handleDelete() {
  if (!selectedNode.value) {
    ElMessage.warning('请先选择要删除的分类')
    return
  }

  // Check if has children
  if (selectedNode.value.children && selectedNode.value.children.length > 0) {
    ElMessage.warning('该分类下有子分类，无法删除')
    return
  }

  try {
    await ElMessageBox.confirm(`确定要删除分类"${selectedNode.value.name}"吗？`, '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await deletePointCategory(selectedNode.value.id)
    ElMessage.success('删除成功')
    selectedNode.value = null
    selectedNodeId.value = null
    await loadTree()
  } catch (e: unknown) {
    if (e === 'cancel') return
    const errorMessage = e instanceof Error ? e.message : '删除失败'
    ElMessage.error(errorMessage)
  }
}

// Tree node rendering
const getNodeClass = (data: PointCategory) => {
  return {
    'tree-node-active': selectedNodeId.value === data.id,
    'tree-node-inactive': !data.is_active,
  }
}

const canAddSubcategory = computed(() => {
  return selectedNode.value && selectedNode.value.level < 3
})

onMounted(() => {
  loadTree()
})
</script>

<template>
  <div class="point-categories-container">
    <div class="page-header">
      <h2>积分商品分类管理</h2>
    </div>

    <div class="content-layout">
      <!-- Left: Tree View -->
      <div class="tree-panel">
        <div class="panel-header">
          <span>分类树</span>
          <el-button type="primary" size="small" @click="openCreateRoot">
            <el-icon><Plus /></el-icon>
            新建根分类
          </el-button>
        </div>

        <div v-loading="treeLoading" class="tree-wrapper">
          <el-tree
            v-if="treeData.length > 0"
            :data="treeData"
            :props="{ children: 'children', label: 'name' }"
            node-key="id"
            :expand-on-click-node="false"
            highlight-current
            :current-node-key="selectedNodeId"
            draggable
            :allow-drag="() => true"
            :allow-drop="() => false"
            @node-click="handleNodeClick"
          >
            <template #default="{ node, data }">
              <div class="custom-tree-node" :class="getNodeClass(data)">
                <el-icon class="node-icon">
                  <Folder v-if="!node.expanded" />
                  <FolderOpened v-else />
                </el-icon>
                <span class="node-label">{{ node.label }}</span>
                <el-tag v-if="!data.is_active" type="info" size="small" class="node-tag">
                  已禁用
                </el-tag>
              </div>
            </template>
          </el-tree>
          <el-empty v-else description="暂无分类" />
        </div>

        <div v-if="selectedNode" class="tree-actions">
          <el-button
            type="primary"
            size="small"
            :disabled="!canAddSubcategory"
            @click="openCreateSubcategory"
          >
            <el-icon><Plus /></el-icon>
            新建子分类
          </el-button>
          <el-button size="small" @click="openEdit"> 编辑 </el-button>
          <el-button type="danger" size="small" @click="handleDelete"> 删除 </el-button>
        </div>
      </div>

      <!-- Right: Edit Form -->
      <div class="form-panel">
        <div class="panel-header">
          <span>{{ formMode === 'create' ? '新建分类' : '编辑分类' }}</span>
        </div>

        <div class="form-wrapper">
          <el-form v-if="showForm" :model="form" label-width="100px">
            <el-form-item label="分类名称" required>
              <el-input v-model="form.name" placeholder="请输入分类名称" />
            </el-form-item>

            <el-form-item label="分类描述">
              <el-input
                v-model="form.description"
                type="textarea"
                :rows="3"
                placeholder="请输入分类描述"
              />
            </el-form-item>

            <el-form-item label="分类图标">
              <div v-if="form.icon_url" class="image-preview">
                <el-image
                  :src="form.icon_url"
                  fit="cover"
                  style="width: 100px; height: 100px; border-radius: 4px"
                  :preview-src-list="[form.icon_url]"
                />
                <el-button type="danger" size="small" class="remove-btn" @click="removeIcon">
                  <el-icon><Close /></el-icon>
                  删除
                </el-button>
              </div>
              <el-upload
                v-else
                :http-request="handleIconUpload"
                :before-upload="beforeImageUpload"
                :disabled="uploading"
                :show-file-list="false"
                accept="image/*"
              >
                <el-button type="primary" size="small" :loading="uploading">
                  <el-icon><Plus /></el-icon>
                  上传图标
                </el-button>
              </el-upload>
              <div class="upload-hint">建议尺寸：64x64px，支持 jpg/png/gif 格式</div>
            </el-form-item>

            <el-form-item label="分类横幅">
              <div v-if="form.banner_url" class="image-preview">
                <el-image
                  :src="form.banner_url"
                  fit="cover"
                  style="width: 200px; height: 100px; border-radius: 4px"
                  :preview-src-list="[form.banner_url]"
                />
                <el-button type="danger" size="small" class="remove-btn" @click="removeBanner">
                  <el-icon><Close /></el-icon>
                  删除
                </el-button>
              </div>
              <el-upload
                v-else
                :http-request="handleBannerUpload"
                :before-upload="beforeImageUpload"
                :disabled="uploading"
                :show-file-list="false"
                accept="image/*"
              >
                <el-button type="primary" size="small" :loading="uploading">
                  <el-icon><Plus /></el-icon>
                  上传横幅
                </el-button>
              </el-upload>
              <div class="upload-hint">建议尺寸：750x300px，支持 jpg/png/gif 格式</div>
            </el-form-item>

            <el-form-item label="排序权重">
              <el-input-number v-model="form.sort_order" :min="0" :max="9999" />
              <span style="margin-left: 10px; color: #999; font-size: 12px"> 数值越大越靠前 </span>
            </el-form-item>

            <el-form-item label="是否启用">
              <el-switch v-model="form.is_active" />
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="submit">确定</el-button>
              <el-button @click="showForm = false">取消</el-button>
            </el-form-item>
          </el-form>

          <el-empty v-else description="请选择要编辑的分类或新建分类" />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.point-categories-container {
  padding: 20px;
  height: calc(100vh - 120px);
  display: flex;
  flex-direction: column;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 500;
}

.content-layout {
  display: flex;
  gap: 20px;
  flex: 1;
  min-height: 0;
}

.tree-panel {
  flex: 0 0 350px;
  display: flex;
  flex-direction: column;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  background: #fff;
}

.form-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  background: #fff;
  min-width: 0;
}

.panel-header {
  padding: 12px 16px;
  border-bottom: 1px solid #ebeef5;
  font-weight: 500;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #f5f7fa;
}

.tree-wrapper {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.tree-actions {
  padding: 12px 16px;
  border-top: 1px solid #ebeef5;
  display: flex;
  gap: 8px;
  background: #f5f7fa;
}

.form-wrapper {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.custom-tree-node {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  padding: 4px 0;
}

.node-icon {
  color: #909399;
}

.node-label {
  flex: 1;
  font-size: 14px;
}

.node-tag {
  margin-left: auto;
}

.tree-node-active {
  color: #409eff;
  font-weight: 500;
}

.tree-node-inactive {
  color: #c0c4cc;
}

.image-preview {
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: flex-start;
}

.remove-btn {
  width: 100px;
}

.upload-hint {
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
  line-height: 1.5;
}

:deep(.el-tree-node__content) {
  height: 36px;
}

:deep(.el-tree-node__content:hover) {
  background-color: #f5f7fa;
}
</style>
