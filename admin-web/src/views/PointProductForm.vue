<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Close, Plus } from '@element-plus/icons-vue'
import type { UploadRequestOptions } from 'element-plus'
import {
  getPointProduct,
  createPointProduct,
  updatePointProduct,
  type PointProduct,
  type PointProductCreate,
  type ProductType,
  type ShippingMethod,
} from '@/api/pointShop'
import {
  listSpecifications,
  createSpecification,
  deleteSpecification,
  listSpecificationValues,
  createSpecificationValue,
  deleteSpecificationValue,
  listSKUs,
  createSKU,
  batchUpdateSKUs,
  type PointSpecification,
  type PointSpecificationValue,
  type PointProductSKU,
} from '@/api/pointSku'
import { getCategoryTree } from '@/api/pointCategory'
import { listShippingTemplates, type ShippingTemplate } from '@/api/shippingTemplate'
import {
  listSpecificationTemplates,
  type SpecificationTemplate,
} from '@/api/specificationTemplate'
import adminApi from '@/api/admin'

const route = useRoute()
const router = useRouter()
const productId = route.params.id as string | undefined
const isEdit = !!productId

const loading = ref(false)
const saving = ref(false)
const uploading = ref(false)

// 表单数据
const form = ref<PointProductCreate>({
  name: '',
  description: '',
  image_urls: [],
  points_cost: 0,
  stock: 0,
  stock_unlimited: false,
  category: '',
  category_id: undefined,
  has_sku: false,
  product_type: 'physical',
  shipping_method: 'express',
  shipping_template_id: undefined,
  sort_order: 0,
  is_active: true,
})

// SKU管理状态
const specifications = ref<(PointSpecification & { values?: PointSpecificationValue[] })[]>([])
const skus = ref<PointProductSKU[]>([])
const newSpecName = ref('')
const newSpecValues = ref<Record<string, string[]>>({})
const skuLoading = ref(false)

// 分类树
const categoryTree = ref<any[]>([])
const loadingCategories = ref(false)

// 运费模板
const shippingTemplates = ref<ShippingTemplate[]>([])
const loadingTemplates = ref(false)

// 规格模板（从API加载）
const specTemplates = ref<SpecificationTemplate[]>([])
const loadingSpecTemplates = ref(false)
const showPresetDialog = ref(false)

// 商品类型选项
const productTypeOptions = [
  { label: '实物商品', value: 'physical' as ProductType },
  { label: '虚拟商品', value: 'virtual' as ProductType },
  { label: '套餐商品', value: 'bundle' as ProductType },
]

// 物流方式选项
const shippingMethodOptions = [
  { label: '快递发货', value: 'express' as ShippingMethod },
  { label: '用户自提', value: 'self_pickup' as ShippingMethod },
  { label: '无需快递', value: 'no_shipping' as ShippingMethod },
]

// 根据商品类型过滤物流方式
const availableShippingMethods = computed(() => {
  // 虚拟商品只能使用"无需快递"
  if (form.value.product_type === 'virtual') {
    return shippingMethodOptions.filter(m => m.value === 'no_shipping')
  }
  return shippingMethodOptions
})

// 是否显示运费模板选择（仅快递发货时显示）
const showShippingTemplate = computed(() => {
  return form.value.shipping_method === 'express'
})

// 监听商品类型变化，自动调整物流方式
const handleProductTypeChange = () => {
  if (form.value.product_type === 'virtual') {
    form.value.shipping_method = 'no_shipping'
    form.value.shipping_template_id = undefined
  } else if (form.value.product_type === 'physical') {
    if (form.value.shipping_method === 'no_shipping') {
      form.value.shipping_method = 'express'
    }
  }
}

// 监听物流方式变化
const handleShippingMethodChange = () => {
  if (form.value.shipping_method !== 'express') {
    form.value.shipping_template_id = undefined
  }
}

// 加载运费模板
async function loadShippingTemplates() {
  loadingTemplates.value = true
  try {
    const res = await listShippingTemplates({ active_only: true, limit: 100 })
    shippingTemplates.value = res.items || []
  } catch (e) {
    ElMessage.error('加载运费模板失败')
  } finally {
    loadingTemplates.value = false
  }
}

// 加载规格模板
async function loadSpecTemplates() {
  loadingSpecTemplates.value = true
  try {
    const res = await listSpecificationTemplates({ active_only: true })
    specTemplates.value = res?.templates || []
  } catch (e) {
    ElMessage.error('加载规格模板失败')
  } finally {
    loadingSpecTemplates.value = false
  }
}

// 图片上传处理
const handleImageUpload = async (options: UploadRequestOptions) => {
  const { file, onSuccess, onError } = options

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
      headers: { 'Content-Type': 'multipart/form-data' },
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

// 加载分类树
async function loadCategories() {
  loadingCategories.value = true
  try {
    const res = await getCategoryTree()
    // getCategoryTree 直接返回数组（已被 axios 拦截器解包）
    categoryTree.value = Array.isArray(res) ? res : []
  } catch (e) {
    ElMessage.error('加载分类失败')
  } finally {
    loadingCategories.value = false
  }
}

// 加载商品数据（编辑模式）
async function loadProduct() {
  if (!productId) return

  loading.value = true
  try {
    const product = await getPointProduct(productId)

    form.value = {
      name: product.name,
      description: product.description || '',
      image_urls: product.image_urls || [],
      points_cost: product.points_cost,
      stock: product.stock,
      stock_unlimited: product.stock_unlimited,
      category: product.category || '',
      category_id: product.category_id,
      has_sku: product.has_sku || false,
      product_type: product.product_type ?? 'physical',
      shipping_method: product.shipping_method ?? 'express',
      shipping_template_id: product.shipping_template_id ?? undefined,
      sort_order: product.sort_order,
      is_active: product.is_active,
    }

    // 如果是SKU商品，加载规格和SKU数据
    if (product.has_sku) {
      await loadSpecifications()
      await loadSKUs()
    }
  } catch (e) {
    ElMessage.error('加载商品失败')
  } finally {
    loading.value = false
  }
}

// 加载规格
async function loadSpecifications() {
  if (!productId) return

  try {
    const res = await listSpecifications(productId)
    const specs = res.specifications || []

    // 加载每个规格的值
    for (const spec of specs) {
      const valuesRes = await listSpecificationValues(spec.id)
      spec.values = valuesRes.values || []
    }

    specifications.value = specs
  } catch (e) {
    ElMessage.error('加载规格失败')
  }
}

// 加载SKU
async function loadSKUs() {
  if (!productId) return

  skuLoading.value = true
  try {
    const res = await listSKUs(productId)
    skus.value = res.skus || []
  } catch (e) {
    ElMessage.error('加载SKU失败')
  } finally {
    skuLoading.value = false
  }
}

// 选择规格模板
function selectSpecTemplate(template: SpecificationTemplate) {
  // 检查是否已存在同名规格
  if (specifications.value.some(s => s.name === template.name)) {
    ElMessage.warning(`规格"${template.name}"已存在`)
    return
  }

  if (productId) {
    // 编辑模式：调用API创建
    addSpecificationWithValues(template.name, template.values)
  } else {
    // 新建模式：本地添加
    specifications.value.push({
      id: `temp_${Date.now()}`,
      product_id: '',
      name: template.name,
      sort_order: specifications.value.length,
      created_at: new Date().toISOString(),
      values: template.values.map((v, i) => ({
        id: `temp_val_${Date.now()}_${i}`,
        specification_id: '',
        value: v,
        sort_order: i,
      })),
    })
    newSpecValues.value[template.name] = [...template.values, '']
  }
  showPresetDialog.value = false
  ElMessage.success(`已添加规格"${template.name}"`)
}

// 编辑模式下添加规格和值
async function addSpecificationWithValues(name: string, values: string[]) {
  try {
    const specRes = await createSpecification(productId!, { name, sort_order: specifications.value.length })
    const specId = specRes.id

    // 添加规格值
    for (const value of values) {
      await createSpecificationValue(specId, { value, sort_order: 0 })
    }

    await loadSpecifications()
    ElMessage.success('添加规格成功')
  } catch (e) {
    ElMessage.error('添加规格失败')
  }
}

// 添加规格
async function addSpecification() {
  if (!newSpecName.value.trim()) {
    ElMessage.warning('请输入规格名称')
    return
  }

  if (specifications.value.length >= 6) {
    ElMessage.warning('最多支持6个规格')
    return
  }

  if (productId) {
    // 编辑模式：调用API创建
    try {
      await createSpecification(productId, { name: newSpecName.value, sort_order: specifications.value.length })
      await loadSpecifications()
      newSpecName.value = ''
      ElMessage.success('添加规格成功')
    } catch (e) {
      ElMessage.error('添加规格失败')
    }
  } else {
    // 新建模式：本地添加
    specifications.value.push({
      id: `temp_${Date.now()}`,
      product_id: '',
      name: newSpecName.value,
      sort_order: specifications.value.length,
      created_at: new Date().toISOString(),
      values: [],
    })
    newSpecValues.value[newSpecName.value] = []
    newSpecName.value = ''
  }
}

// 添加规格值
async function addSpecValue(specName: string) {
  const values = newSpecValues.value[specName]
  if (!values || !values[values.length - 1]?.trim()) {
    ElMessage.warning('请先输入规格值')
    return
  }

  if (values.length >= 10) {
    ElMessage.warning('每个规格最多支持10个值')
    return
  }

  // 空值会在输入时自动添加
}

// 删除规格
async function removeSpecification(spec: PointSpecification, index: number) {
  if (!productId) {
    // 新建模式：直接删除
    specifications.value.splice(index, 1)
    delete newSpecValues.value[spec.name]
    return
  }

  // 编辑模式：调用API删除
  try {
    await deleteSpecification(spec.id)
    await loadSpecifications()
    ElMessage.success('删除规格成功')
  } catch (e) {
    ElMessage.error('删除规格失败')
  }
}

// 删除规格值
async function removeSpecValue(spec: PointSpecification, value: string) {
  if (!productId) {
    // 新建模式：直接删除
    const values = newSpecValues.value[spec.name]
    const index = values.indexOf(value)
    if (index > -1) {
      values.splice(index, 1)
    }
    return
  }

  // 编辑模式：调用API删除
  try {
    const specValue = spec.values?.find(v => v.value === value)
    if (specValue) {
      await deleteSpecificationValue(specValue.id)
      await loadSpecifications()
      ElMessage.success('删除规格值成功')
    }
  } catch (e) {
    ElMessage.error('删除规格值失败')
  }
}

// 生成SKU组合
function generateSKUCombinations() {
  if (specifications.value.length === 0) {
    ElMessage.warning('请先添加规格')
    return
  }

  const validSpecs = specifications.value.filter(spec => {
    const values = productId ? (spec.values || []).map(v => v.value) : (newSpecValues.value[spec.name] || [])
    return values.length > 0
  })

  if (validSpecs.length === 0) {
    ElMessage.warning('请为每个规格添加至少一个值')
    return
  }

  // 生成笛卡尔积
  function cartesian(arr: any[][]): any[] {
    if (arr.length === 0) return [[]]
    const [first, ...rest] = arr
    const restCombinations = cartesian(rest)
    const result: any[] = []
    for (const item of first) {
      for (const combination of restCombinations) {
        result.push([item, ...combination])
      }
    }
    return result
  }

  const allValues = validSpecs.map(spec => {
    const values = productId ? (spec.values || []).map(v => v.value) : (newSpecValues.value[spec.name] || [])
    return values.map(v => ({ name: spec.name, value: v }))
  })

  const combinations = cartesian(allValues)

  skus.value = combinations.map((combo, index) => {
    const specs: Record<string, string> = {}
    combo.forEach(c => {
      specs[c.name] = c.value
    })

    return {
      id: `temp_sku_${Date.now()}_${index}`,
      product_id: productId || '',
      sku_code: '',
      specs: JSON.stringify(specs),
      stock: form.value.stock_unlimited ? 0 : form.value.stock,
      stock_unlimited: form.value.stock_unlimited,
      points_cost: form.value.points_cost,
      image_url: '',
      is_active: true,
      sort_order: index,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
  })

  ElMessage.success(`已生成 ${skus.value.length} 个SKU`)
}

// 保存
async function save() {
  // 基础验证
  if (!form.value.name?.trim()) {
    ElMessage.warning('请输入商品名称')
    return
  }

  if (form.value.points_cost <= 0) {
    ElMessage.warning('请输入有效的积分价格')
    return
  }

  if (!form.value.has_sku && !form.value.stock_unlimited && form.value.stock < 0) {
    ElMessage.warning('库存不能为负数')
    return
  }

  // SKU模式验证
  if (form.value.has_sku) {
    if (specifications.value.length === 0) {
      ElMessage.warning('请至少添加一个规格')
      return
    }

    const hasValues = specifications.value.some(spec => {
      const values = productId ? (spec.values || []) : (newSpecValues.value[spec.name] || [])
      return values.length > 0
    })

    if (!hasValues) {
      ElMessage.warning('请为规格添加值')
      return
    }

    if (skus.value.length === 0) {
      ElMessage.warning('请生成SKU')
      return
    }

    // 验证SKU数据
    for (const sku of skus.value) {
      if (!sku.stock_unlimited && sku.stock < 0) {
        ElMessage.warning('SKU库存不能为负数')
        return
      }
      if (sku.points_cost <= 0) {
        ElMessage.warning('SKU积分价格必须大于0')
        return
      }
    }
  }

  saving.value = true
  try {
    // 准备提交数据 - 一次性提交规格和SKU信息
    const submitData: PointProductCreate = {
      ...form.value,
      // 如果是SKU商品，添加规格和SKU信息
      specifications: form.value.has_sku
        ? specifications.value.map(spec => ({
            name: spec.name,
            values: productId
              ? (spec.values || []).map((v: any) => v.value).filter(v => v.trim())
              : (newSpecValues.value[spec.name] || []).filter(v => v.trim()),
          }))
        : [],
      skus: form.value.has_sku
        ? skus.value.map((sku, index) => ({
          ...sku,
          sku_code: sku.sku_code || `SKU-${index + 1}`,
          specs: typeof sku.specs === 'string' ? JSON.parse(sku.specs) : sku.specs,
          stock: sku.stock,
          stock_unlimited: sku.stock_unlimited,
          points_cost: sku.points_cost,
          image_url: sku.image_url || '',
          sort_order: index,
          is_active: sku.is_active ?? true,
        }))
        : [],
    }

    if (productId) {
      // 编辑模式 - 一次性提交所有数据（后端会处理更新逻辑）
      await updatePointProduct(productId, submitData)
    } else {
      // 新建模式 - 一次性提交所有数据
      const res = await createPointProduct(submitData)
    }

    ElMessage.success(productId ? '更新成功' : '创建成功')
    router.push('/point-shop')
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : '保存失败'
    ElMessage.error(errorMessage)
  } finally {
    saving.value = false
  }
}

function goBack() {
  router.back()
}

// 格式化规格显示
function formatSpecs(sku: PointProductSKU) {
  try {
    const specs = typeof sku.specs === 'string' ? JSON.parse(sku.specs) : sku.specs
    return Object.entries(specs).map(([k, v]) => `${k}: ${v}`).join(' / ')
  } catch {
    return sku.specs
  }
}

// 监听规格值输入变化
function handleSpecValueInput(specName: string, index: number, value: string) {
  if (!newSpecValues.value[specName]) {
    newSpecValues.value[specName] = []
  }
  newSpecValues.value[specName][index] = value

  // 如果是最后一个值且有内容，添加新的空值
  if (index === newSpecValues.value[specName].length - 1 && value.trim()) {
    newSpecValues.value[specName].push('')
  }
}

onMounted(async () => {
  await Promise.all([loadCategories(), loadShippingTemplates(), loadSpecTemplates()])
  if (isEdit) {
    await loadProduct()
  }
})
</script>

<template>
  <div class="product-form-container">
    <div class="page-header">
      <div class="header-left">
        <el-button :icon="ArrowLeft" @click="goBack">返回</el-button>
        <h2>{{ isEdit ? '编辑商品' : '新增商品' }}</h2>
      </div>
      <div class="header-right">
        <el-button @click="goBack">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </div>
    </div>

    <el-form v-loading="loading" label-width="120px" class="product-form">
      <!-- 基本信息 -->
      <el-card class="form-section" header="基本信息">
        <el-form-item label="商品名称" required>
          <el-input v-model="form.name" placeholder="请输入商品名称" maxlength="100" show-word-limit />
        </el-form-item>

        <el-form-item label="商品类型">
          <el-select
            v-model="form.product_type"
            placeholder="请选择商品类型"
            @change="handleProductTypeChange"
            style="width: 200px"
          >
            <el-option
              v-for="option in productTypeOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
          <span style="margin-left: 10px; color: #999; font-size: 12px">
            实物商品需要物流配送，虚拟商品自动发货，套餐商品包含多个商品
          </span>
        </el-form-item>

        <el-form-item label="物流方式">
          <el-select
            v-model="form.shipping_method"
            placeholder="请选择物流方式"
            :disabled="form.product_type === 'virtual'"
            @change="handleShippingMethodChange"
            style="width: 200px"
          >
            <el-option
              v-for="option in availableShippingMethods"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
          <span style="margin-left: 10px; color: #999; font-size: 12px">
            <template v-if="form.product_type === 'virtual'">
              虚拟商品无需物流
            </template>
            <template v-else-if="form.shipping_method === 'express'">
              需要选择运费模板
            </template>
            <template v-else-if="form.shipping_method === 'self_pickup'">
              用户到店自提
            </template>
            <template v-else>
              无需物流配送
            </template>
          </span>
        </el-form-item>

        <el-form-item v-if="showShippingTemplate" label="运费模板">
          <el-select
            v-model="form.shipping_template_id"
            placeholder="请选择运费模板"
            :loading="loadingTemplates"
            clearable
            filterable
            style="width: 300px"
          >
            <el-option
              v-for="template in shippingTemplates"
              :key="template.id"
              :label="template.name"
              :value="template.id"
            >
              <span>{{ template.name }}</span>
              <span style="float: right; color: #999; font-size: 12px">
                {{ template.description || '无描述' }}
              </span>
            </el-option>
          </el-select>
          <span style="margin-left: 10px; color: #999; font-size: 12px">
            未选择则使用默认运费
          </span>
        </el-form-item>

        <el-form-item label="商品分类">
          <el-cascader
            v-model="form.category_id"
            :options="categoryTree"
            :props="{
              value: 'id',
              label: 'name',
              children: 'children',
              emitPath: false,
              checkStrictly: true,
            }"
            :loading="loadingCategories"
            placeholder="请选择商品分类"
            clearable
            filterable
            style="width: 300px"
          />
        </el-form-item>

        <el-form-item label="商品描述">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="4"
            placeholder="请输入商品描述"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="商品图片">
          <div class="upload-tip">已上传 {{ form.image_urls?.length || 0 }} / 6 张</div>
          <div class="image-upload-list">
            <div v-for="(url, index) in form.image_urls" :key="index" class="upload-item">
              <el-image :src="url" fit="cover" class="upload-image" :preview-src-list="form.image_urls" :initial-index="index" />
              <div class="upload-mask">
                <span class="mask-actions">
                  <el-icon @click="removeImage(index)" class="delete-icon"><Close /></el-icon>
                </span>
              </div>
            </div>
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
                <el-icon class="upload-icon"><Plus /></el-icon>
                <div class="upload-text">{{ uploading ? '上传中...' : '上传图片' }}</div>
              </div>
            </el-upload>
          </div>
          <div class="upload-hint">支持 jpg/png/gif 格式，单个文件不超过 5MB，最多上传 6 张图片</div>
        </el-form-item>

        <el-form-item label="SKU管理">
          <el-switch v-model="form.has_sku" active-text="启用" inactive-text="不启用" />
          <span style="margin-left: 10px; color: #999; font-size: 12px">启用后可为商品设置多规格（如颜色、尺寸等）</span>
        </el-form-item>

        <!-- 非SKU模式：价格和库存 -->
        <template v-if="!form.has_sku">
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
        </template>

        <el-form-item label="排序权重">
          <el-input-number v-model="form.sort_order" :min="0" :max="9999" />
          <span style="margin-left: 10px; color: #999; font-size: 12px">数值越大越靠前</span>
        </el-form-item>

        <el-form-item label="上架状态">
          <el-switch v-model="form.is_active" active-text="上架" inactive-text="下架" />
        </el-form-item>
      </el-card>

      <!-- SKU管理 -->
      <el-card v-if="form.has_sku" class="form-section" header="规格管理">
        <!-- 规格模板选择 -->
        <div style="margin-bottom: 15px">
          <el-button type="success" @click="showPresetDialog = true">选择规格模板</el-button>
          <span style="margin-left: 10px; color: #999; font-size: 12px">从已保存的规格模板中快速添加</span>
        </div>

        <div class="spec-editor">
          <div v-for="(spec, index) in specifications" :key="spec.id" class="spec-item">
            <div class="spec-header">
              <span class="spec-name">{{ spec.name }}</span>
              <el-button link type="danger" size="small" @click="removeSpecification(spec, index)">删除</el-button>
            </div>
            <div class="spec-values">
              <template v-if="productId">
                <!-- 编辑模式：显示已保存的规格值 -->
                <el-tag
                  v-for="value in spec.values"
                  :key="value.id"
                  closable
                  @close="removeSpecValue(spec, value.value)"
                >
                  {{ value.value }}
                </el-tag>
              </template>
              <template v-else>
                <!-- 新建模式：显示输入的规格值 -->
                <el-tag
                  v-for="(value, vIndex) in newSpecValues[spec.name] || []"
                  :key="vIndex"
                  closable
                  @close="removeSpecValue(spec, value)"
                >
                  {{ value }}
                </el-tag>
              </template>
            </div>
          </div>

          <div class="add-spec">
            <el-input
              v-model="newSpecName"
              placeholder="规格名称，如：颜色、尺寸"
              style="width: 200px; margin-right: 10px"
              @keyup.enter="addSpecification"
            />
            <el-button type="primary" @click="addSpecification">添加规格</el-button>
            <span style="margin-left: 10px; color: #999; font-size: 12px">最多支持6个规格</span>
          </div>

          <div v-if="specifications.length > 0" class="spec-values-input">
            <div v-for="spec in specifications" :key="spec.id" class="spec-value-input-item">
              <div class="spec-label">{{ spec.name }}：</div>
              <div v-if="!productId" class="spec-value-inputs">
                <div v-for="(value, index) in newSpecValues[spec.name] || []" :key="index" class="spec-value-input-row">
                  <el-input
                    :model-value="value"
                    placeholder="输入规格值，按Enter添加"
                    @input="handleSpecValueInput(spec.name, index, $event)"
                    @keyup.enter="(e) => e.target.blur()"
                    style="width: 150px; margin-right: 5px"
                  />
                  <el-button link type="danger" size="small" @click="removeSpecValue(spec, value)">删除</el-button>
                </div>
                <el-button
                  v-if="!newSpecValues[spec.name] || newSpecValues[spec.name].length === 0"
                  link
                  type="primary"
                  size="small"
                  @click="handleSpecValueInput(spec.name, 0, '')"
                >
                  + 添加规格值
                </el-button>
              </div>
              <div v-else class="spec-hint">
                <span style="color: #999; font-size: 12px">编辑模式下，请保存后重新生成SKU</span>
              </div>
            </div>
          </div>

          <el-button
            v-if="specifications.length > 0 && !productId"
            type="success"
            @click="generateSKUCombinations"
            style="margin-top: 15px"
          >
            生成SKU组合
          </el-button>
        </div>
      </el-card>

      <!-- SKU列表 -->
      <el-card v-if="form.has_sku && skus.length > 0" class="form-section" header="SKU列表">
        <el-table :data="skus" border>
          <el-table-column label="规格" width="250">
            <template #default="{ row }">{{ formatSpecs(row) }}</template>
          </el-table-column>
          <el-table-column label="SKU编码" width="150">
            <template #default="{ row }">
              <el-input v-model="row.sku_code" placeholder="自动生成或手动输入" />
            </template>
          </el-table-column>
          <el-table-column label="库存" width="150">
            <template #default="{ row }">
              <el-checkbox v-model="row.stock_unlimited" size="small" />
              <el-input-number
                v-if="!row.stock_unlimited"
                v-model="row.stock"
                :min="0"
                :max="999999"
                size="small"
                style="margin-left: 5px"
              />
            </template>
          </el-table-column>
          <el-table-column label="积分价格" width="150">
            <template #default="{ row }">
              <el-input-number v-model="row.points_cost" :min="1" :max="999999" size="small" />
            </template>
          </el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-switch v-model="row.is_active" size="small" />
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </el-form>

    <!-- 规格模板选择对话框 -->
    <el-dialog v-model="showPresetDialog" title="选择规格模板" width="600px">
      <div v-loading="loadingSpecTemplates">
        <div v-if="specTemplates.length === 0" class="empty-templates">
          <el-empty description="暂无规格模板，请先在「规格模板管理」中创建模板">
            <el-button type="primary" @click="router.push('/specification-templates')">
              前往创建
            </el-button>
          </el-empty>
        </div>
        <div v-else class="preset-specs-grid">
          <div
            v-for="template in specTemplates"
            :key="template.id"
            class="preset-spec-card"
            @click="selectSpecTemplate(template)"
          >
            <div class="preset-spec-name">{{ template.name }}</div>
            <div v-if="template.description" class="preset-spec-desc">{{ template.description }}</div>
            <div class="preset-spec-values">
              <el-tag v-for="v in template.values.slice(0, 5)" :key="v" size="small" style="margin: 2px">{{ v }}</el-tag>
              <el-tag v-if="template.values.length > 5" size="small" type="info" style="margin: 2px">+{{ template.values.length - 5 }}</el-tag>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="showPresetDialog = false">取消</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.product-form-container {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-left h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 500;
}

.header-right {
  display: flex;
  gap: 10px;
}

.form-section {
  margin-bottom: 20px;
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

.spec-editor {
  padding: 10px 0;
}

.spec-item {
  margin-bottom: 20px;
  padding: 15px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
}

.spec-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.spec-name {
  font-weight: 500;
  color: #303133;
}

.spec-values {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.spec-values .el-tag {
  margin: 0;
}

.add-spec {
  display: flex;
  align-items: center;
  padding: 15px;
  border: 1px dashed #dcdfe6;
  border-radius: 4px;
}

.spec-values-input {
  margin-top: 20px;
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.spec-value-input-item {
  margin-bottom: 15px;
}

.spec-label {
  font-weight: 500;
  margin-bottom: 10px;
}

.spec-value-inputs {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.spec-value-input-row {
  display: flex;
  align-items: center;
}

.spec-hint {
  color: #999;
  font-size: 12px;
}

/* 预设规格选择 */
.preset-specs-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.empty-templates {
  padding: 40px 0;
  text-align: center;
}

.preset-spec-card {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.3s;
}

.preset-spec-card:hover {
  border-color: #409eff;
  background-color: #ecf5ff;
}

.preset-spec-desc {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
}

.preset-spec-name {
  font-weight: 500;
  font-size: 16px;
  margin-bottom: 8px;
  color: #303133;
}

.preset-spec-values {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
</style>
