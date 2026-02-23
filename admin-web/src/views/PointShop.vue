<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Close, Plus } from '@element-plus/icons-vue'
import type { UploadRequestOptions } from 'element-plus'
import {
  listPointProducts,
  createPointProduct,
  updatePointProduct,
  deletePointProduct,
  type PointProduct,
  type PointProductCreate,
} from '@/api/pointShop'
import { formatDate } from '@/utils/format'
import adminApi from '@/api/admin'

const list = ref<PointProduct[]>([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = 20

// 表单
const showDialog = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const editId = ref<string | null>(null)
const uploading = ref(false)
const form = ref<PointProductCreate>({
  name: '',
  description: '',
  image_urls: [],
  points_cost: 0,
  stock: 0,
  stock_unlimited: false,
  category: '',
  sort_order: 0,
})

// 图片上传处理
const handleImageUpload = async (options: UploadRequestOptions) => {
  const { file, onSuccess, onError } = options

  // 检查图片数量限制
  if (form.value.image_urls && form.value.image_urls.length >= 6) {
    ElMessage.error('最多只能上传6张图片')
    onError?.(new Error('超过图片数量限制'))
    return
  }

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
      if (!form.value.image_urls) {
        form.value.image_urls = []
      }
      form.value.image_urls.push(url)
      ElMessage.success('图片上传成功')
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

  // 检查图片数量限制
  if (form.value.image_urls && form.value.image_urls.length >= 6) {
    ElMessage.error('最多只能上传6张图片')
    return false
  }
  return true
}

const removeImage = (index: number) => {
  if (form.value.image_urls) {
    form.value.image_urls.splice(index, 1)
  }
}

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
  dialogMode.value = 'create'
  editId.value = null
  form.value = {
    name: '',
    description: '',
    image_urls: [],
    points_cost: 0,
    stock: 0,
    stock_unlimited: false,
    category: '',
    sort_order: 0,
  }
  showDialog.value = true
}

function openEdit(item: PointProduct) {
  dialogMode.value = 'edit'
  editId.value = item.id
  form.value = {
    name: item.name,
    description: item.description || '',
    image_urls: item.image_urls || [],
    points_cost: item.points_cost,
    stock: item.stock,
    stock_unlimited: item.stock_unlimited,
    category: item.category || '',
    sort_order: item.sort_order,
  }
  showDialog.value = true
}

async function submit() {
  if (!form.value.name?.trim()) {
    ElMessage.warning('请输入商品名称')
    return
  }
  if (form.value.points_cost <= 0) {
    ElMessage.warning('请输入有效的积分价格')
    return
  }
  if (!form.value.stock_unlimited && form.value.stock < 0) {
    ElMessage.warning('库存不能为负数')
    return
  }

  try {
    if (dialogMode.value === 'create') {
      await createPointProduct(form.value)
      ElMessage.success('创建成功')
    } else {
      if (!editId.value) return
      await updatePointProduct(editId.value, form.value)
      ElMessage.success('更新成功')
    }
    showDialog.value = false
    await loadData()
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : '操作失败'
    ElMessage.error(errorMessage)
  }
}

async function handleDelete(item: PointProduct) {
  try {
    await ElMessageBox.confirm(
      `确定要删除商品"${item.name}"吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
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
      <el-table-column prop="name" label="商品名称" width="180" />
      <el-table-column prop="category" label="分类" width="120">
        <template #default="{ row }">
          {{ row.category || '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="points_cost" label="积分价格" width="100">
        <template #default="{ row }">
          {{ row.points_cost }} 积分
        </template>
      </el-table-column>
      <el-table-column label="库存" width="100">
        <template #default="{ row }">
          {{ row.stock_unlimited ? '无限' : row.stock }}
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
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="240" fixed="right">
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

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="showDialog"
      :title="dialogMode === 'create' ? '新建商品' : '编辑商品'"
      width="600px"
    >
      <el-form :model="form" label-width="100px">
        <el-form-item label="商品名称" required>
          <el-input v-model="form.name" placeholder="请输入商品名称" />
        </el-form-item>
        <el-form-item label="商品分类">
          <el-input v-model="form.category" placeholder="请输入分类" />
        </el-form-item>
        <el-form-item label="商品描述">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入商品描述"
          />
        </el-form-item>
        <el-form-item label="商品图片">
          <div class="upload-tip">
            已上传 {{ form.image_urls?.length || 0 }} / 6 张
          </div>

          <!-- 图片上传列表 -->
          <div class="image-upload-list">
            <!-- 已上传的图片 -->
            <div
              v-for="(url, index) in form.image_urls"
              :key="index"
              class="upload-item"
            >
              <el-image
                :src="url"
                fit="cover"
                class="upload-image"
                :preview-src-list="form.image_urls"
                :initial-index="index"
              />
              <div class="upload-mask">
                <span class="mask-actions">
                  <el-icon @click="removeImage(index)" class="delete-icon">
                    <Close />
                  </el-icon>
                </span>
              </div>
            </div>

            <!-- 上传按钮（带+号） -->
            <el-upload
              v-if="(form.image_urls?.length || 0) < 6"
              :http-request="handleImageUpload"
              :before-upload="beforeImageUpload"
              :disabled="uploading"
              :show-file-list="false"
              accept="image/*"
              class="upload-btn-wrapper"
            >
              <div class="upload-placeholder" :class="{ 'is-uploading': uploading }">
                <el-icon class="upload-icon">
                  <Plus />
                </el-icon>
                <div class="upload-text">{{ uploading ? '上传中...' : '上传图片' }}</div>
              </div>
            </el-upload>
          </div>

          <div class="upload-hint">
            支持 jpg/png/gif 格式，单个文件不超过 5MB，最多上传 6 张图片
          </div>
        </el-form-item>
        <el-form-item label="积分价格" required>
          <el-input-number v-model="form.points_cost" :min="1" :max="999999" />
        </el-form-item>
        <el-form-item label="库存">
          <el-checkbox v-model="form.stock_unlimited">无限库存</el-checkbox>
          <el-input-number
            v-if="!form.stock_unlimited"
            v-model="form.stock"
            :min="0"
            :max="999999"
            style="margin-left: 10px"
          />
        </el-form-item>
        <el-form-item label="排序权重">
          <el-input-number v-model="form.sort_order" :min="0" :max="9999" />
          <span style="margin-left: 10px; color: #999; font-size: 12px"
            >数值越大越靠前</span
          >
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

.upload-tip {
  margin-bottom: 8px;
  font-size: 13px;
  color: #606266;
  font-weight: 500;
}

.image-upload-list {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.upload-item {
  position: relative;
  width: 104px;
  height: 104px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: hidden;
  cursor: pointer;
}

.upload-image {
  width: 100%;
  height: 100%;
}

.upload-item:hover .upload-mask {
  opacity: 1;
}

.upload-mask {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  opacity: 0;
  transition: opacity 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.mask-actions {
  display: flex;
  gap: 10px;
}

.delete-icon {
  font-size: 20px;
  color: #fff;
  cursor: pointer;
}

.delete-icon:hover {
  color: #f56c6c;
}

.upload-btn-wrapper {
  display: inline-block;
}

.upload-placeholder {
  width: 104px;
  height: 104px;
  border: 1px dashed #d9d9d9;
  border-radius: 4px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s;
  background-color: #fbfdff;
}

.upload-placeholder:hover {
  border-color: #409eff;
  background-color: #ecf5ff;
}

.upload-placeholder.is-uploading {
  cursor: not-allowed;
  opacity: 0.6;
}

.upload-icon {
  font-size: 24px;
  color: #8c939d;
  margin-bottom: 4px;
}

.upload-placeholder:hover .upload-icon {
  color: #409eff;
}

.upload-text {
  font-size: 12px;
  color: #8c939d;
}

.upload-placeholder:hover .upload-text {
  color: #409eff;
}

.upload-hint {
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
  line-height: 1.5;
}
</style>
