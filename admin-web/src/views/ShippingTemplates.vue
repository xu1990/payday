<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  listShippingTemplates,
  getShippingTemplate,
  createShippingTemplate,
  updateShippingTemplate,
  deleteShippingTemplate,
  listTemplateRegions,
  createTemplateRegion,
  updateTemplateRegion,
  deleteTemplateRegion,
  type ShippingTemplate,
  type ShippingTemplateCreate,
  type ShippingTemplateUpdate,
  type ShippingTemplateRegion,
  type ShippingTemplateRegionCreate,
  type ShippingTemplateRegionUpdate,
  type ChargeType,
  type FreeShippingType,
  type ExcludedRegion,
  centsToYuan,
  yuanToCents,
  formatChargeType,
  formatFreeShippingType,
  getUnitLabel,
  parseRegionCodes,
  parseRegionNames,
  joinRegionCodes,
  joinRegionNames,
} from '@/api/shippingTemplate'
import { formatDate } from '@/utils/format'
import { PROVINCES, getProvinceNames, getProvinceCodes } from '@/constants/provinces'

// ==================== Template List ====================
const list = ref<ShippingTemplate[]>([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = 20

// ==================== Template Dialog ====================
const showDialog = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const editId = ref<string | null>(null)
const submitLoading = ref(false)
const activeTab = ref('basic')

// Basic form
const form = ref<ShippingTemplateCreate>({
  name: '',
  description: '',
  charge_type: 'weight',
  default_first_unit: 500,
  default_first_cost: 500, // 500 cents = ¥5.00
  default_continue_unit: 1000,
  default_continue_cost: 10, // 10 cents per 1000g
  free_shipping_type: 'none',
  free_threshold: null,
  free_quantity: null,
  excluded_regions: null,
  volume_unit: null,
  estimate_days_min: null,
  estimate_days_max: null,
})

// New refs for free shipping and excluded regions
const excludedProvinces = ref<string[]>([])
const freeShippingType = ref<FreeShippingType>('none')

// ==================== Region Management ====================
const regions = ref<ShippingTemplateRegion[]>([])
const regionsLoading = ref(false)

const showRegionDialog = ref(false)
const regionDialogMode = ref<'create' | 'edit'>('create')
const regionEditId = ref<string | null>(null)
const regionSubmitLoading = ref(false)

const regionForm = ref<ShippingTemplateRegionCreate>({
  region_codes: '',
  region_names: '',
  first_unit: 500,
  first_cost: 500,
  continue_unit: 1000,
  continue_cost: 10,
  free_threshold: null,
})

const selectedProvinces = ref<string[]>([])

// ==================== Computed ====================
const showPricingFields = computed(() => form.value.charge_type !== 'fixed')
const chargeTypeUnit = computed(() => getUnitLabel(form.value.charge_type))
const chargeTypeLabel = computed(() => formatChargeType(form.value.charge_type))

const regionChargeTypeUnit = computed(() => {
  if (!editId.value) return ''
  // Get the template's charge type
  const template = list.value.find(t => t.id === editId.value)
  if (!template) return ''
  return getUnitLabel(template.charge_type)
})

// ==================== Data Loading ====================
async function loadData() {
  loading.value = true
  try {
    const res = await listShippingTemplates({
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

async function loadRegions(templateId: string) {
  regionsLoading.value = true
  try {
    const res = await listTemplateRegions(templateId)
    regions.value = res?.data?.items || []
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : '加载区域失败'
    ElMessage.error(errorMessage)
    regions.value = []
  } finally {
    regionsLoading.value = false
  }
}

// ==================== Template CRUD ====================
function openCreate() {
  dialogMode.value = 'create'
  editId.value = null
  activeTab.value = 'basic'
  form.value = {
    name: '',
    description: '',
    charge_type: 'weight',
    default_first_unit: 500,
    default_first_cost: 500,
    default_continue_unit: 1000,
    default_continue_cost: 10,
    free_shipping_type: 'none',
    free_threshold: null,
    free_quantity: null,
    excluded_regions: null,
    volume_unit: null,
    estimate_days_min: null,
    estimate_days_max: null,
  }
  freeShippingType.value = 'none'
  excludedProvinces.value = []
  regions.value = []
  showDialog.value = true
}

async function openEdit(item: ShippingTemplate) {
  dialogMode.value = 'edit'
  editId.value = item.id
  activeTab.value = 'basic'

  // Load template details
  try {
    const res = await getShippingTemplate(item.id)
    const template = res.data

    form.value = {
      name: template.name,
      description: template.description || '',
      charge_type: template.charge_type,
      default_first_unit: template.default_first_unit,
      default_first_cost: template.default_first_cost,
      default_continue_unit: template.default_continue_unit,
      default_continue_cost: template.default_continue_cost,
      free_shipping_type: template.free_shipping_type || 'none',
      free_threshold: template.free_threshold,
      free_quantity: template.free_quantity,
      excluded_regions: template.excluded_regions,
      volume_unit: template.volume_unit,
      estimate_days_min: template.estimate_days_min,
      estimate_days_max: template.estimate_days_max,
    }

    // Load free shipping type
    freeShippingType.value = template.free_shipping_type || 'none'

    // Load excluded provinces
    if (template.excluded_regions && template.excluded_regions.length > 0) {
      excludedProvinces.value = template.excluded_regions.map(r => r.code)
    } else {
      excludedProvinces.value = []
    }

    // Load regions
    await loadRegions(item.id)
    showDialog.value = true
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : '加载模板失败'
    ElMessage.error(errorMessage)
  }
}

async function submit() {
  if (!form.value.name?.trim()) {
    ElMessage.warning('请输入模板名称')
    return
  }
  if (form.value.default_first_unit <= 0) {
    ElMessage.warning('首件/首重必须大于0')
    return
  }
  if (form.value.default_first_cost < 0) {
    ElMessage.warning('首件运费不能为负数')
    return
  }
  if (form.value.default_continue_unit <= 0) {
    ElMessage.warning('续件/续重必须大于0')
    return
  }
  if (form.value.default_continue_cost < 0) {
    ElMessage.warning('续件运费不能为负数')
    return
  }
  if (form.value.estimate_days_min && form.value.estimate_days_max) {
    if (form.value.estimate_days_max < form.value.estimate_days_min) {
      ElMessage.warning('最大天数不能小于最小天数')
      return
    }
  }

  // Sync free_shipping_type from ref to form
  form.value.free_shipping_type = freeShippingType.value

  // Build excluded_regions from selected provinces
  if (excludedProvinces.value.length > 0) {
    form.value.excluded_regions = excludedProvinces.value.map(code => {
      const province = PROVINCES.find(p => p.code === code)
      return {
        code,
        name: province?.name || code,
      }
    })
  } else {
    form.value.excluded_regions = null
  }

  submitLoading.value = true
  try {
    if (dialogMode.value === 'create') {
      await createShippingTemplate(form.value)
      ElMessage.success('创建成功')
    } else {
      if (!editId.value) return
      await updateShippingTemplate(editId.value, form.value)
      ElMessage.success('更新成功')
    }
    showDialog.value = false
    await loadData()
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : '操作失败'
    ElMessage.error(errorMessage)
  } finally {
    submitLoading.value = false
  }
}

async function handleDelete(item: ShippingTemplate) {
  try {
    await ElMessageBox.confirm(`确定要删除运费模板"${item.name}"吗？`, '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await deleteShippingTemplate(item.id)
    ElMessage.success('删除成功')
    await loadData()
  } catch (e: unknown) {
    if (e === 'cancel') return
    const errorMessage = e instanceof Error ? e.message : '删除失败'
    ElMessage.error(errorMessage)
  }
}

async function toggleActive(item: ShippingTemplate) {
  try {
    await updateShippingTemplate(item.id, { is_active: !item.is_active })
    ElMessage.success(item.is_active ? '已禁用' : '已启用')
    await loadData()
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : '操作失败'
    ElMessage.error(errorMessage)
  }
}

// ==================== Region CRUD ====================
function openCreateRegion() {
  regionDialogMode.value = 'create'
  regionEditId.value = null
  selectedProvinces.value = []
  regionForm.value = {
    region_codes: '',
    region_names: '',
    first_unit: form.value.default_first_unit,
    first_cost: form.value.default_first_cost,
    continue_unit: form.value.default_continue_unit,
    continue_cost: form.value.default_continue_cost,
    free_threshold: form.value.free_threshold,
  }
  showRegionDialog.value = true
}

function openEditRegion(region: ShippingTemplateRegion) {
  regionDialogMode.value = 'edit'
  regionEditId.value = region.id

  const codes = parseRegionCodes(region.region_codes)
  selectedProvinces.value = codes

  regionForm.value = {
    region_codes: region.region_codes,
    region_names: region.region_names,
    first_unit: region.first_unit,
    first_cost: region.first_cost,
    continue_unit: region.continue_unit,
    continue_cost: region.continue_cost,
    free_threshold: region.free_threshold,
  }
  showRegionDialog.value = true
}

async function handleProvinceChange() {
  // Update region codes and names based on selected provinces
  const selected = PROVINCES.filter(p => selectedProvinces.value.includes(p.code))
  regionForm.value.region_codes = joinRegionCodes(selected.map(p => p.code))
  regionForm.value.region_names = joinRegionNames(selected.map(p => p.name))
}

async function submitRegion() {
  if (!regionForm.value.region_codes) {
    ElMessage.warning('请选择地区')
    return
  }
  if (regionForm.value.first_unit <= 0) {
    ElMessage.warning('首件/首重必须大于0')
    return
  }
  if (regionForm.value.first_cost < 0) {
    ElMessage.warning('首件运费不能为负数')
    return
  }
  if (regionForm.value.continue_unit <= 0) {
    ElMessage.warning('续件/续重必须大于0')
    return
  }
  if (regionForm.value.continue_cost < 0) {
    ElMessage.warning('续件运费不能为负数')
    return
  }

  regionSubmitLoading.value = true
  try {
    if (regionDialogMode.value === 'create') {
      if (!editId.value) return
      await createTemplateRegion(editId.value, regionForm.value)
      ElMessage.success('添加成功')
    } else {
      if (!regionEditId.value) return
      await updateTemplateRegion(regionEditId.value, regionForm.value)
      ElMessage.success('更新成功')
    }
    showRegionDialog.value = false
    if (editId.value) {
      await loadRegions(editId.value)
    }
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : '操作失败'
    ElMessage.error(errorMessage)
  } finally {
    regionSubmitLoading.value = false
  }
}

async function handleDeleteRegion(region: ShippingTemplateRegion) {
  try {
    await ElMessageBox.confirm('确定要删除此区域配置吗？', '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await deleteTemplateRegion(region.id)
    ElMessage.success('删除成功')
    if (editId.value) {
      await loadRegions(editId.value)
    }
  } catch (e: unknown) {
    if (e === 'cancel') return
    const errorMessage = e instanceof Error ? e.message : '删除失败'
    ElMessage.error(errorMessage)
  }
}

async function handleToggleRegionActive(region: ShippingTemplateRegion) {
  try {
    await updateTemplateRegion(region.id, { is_active: !region.is_active })
    ElMessage.success(region.is_active ? '已禁用' : '已启用')
    if (editId.value) {
      await loadRegions(editId.value)
    }
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : '操作失败'
    ElMessage.error(errorMessage)
  }
}

// ==================== Formatters ====================
function formatCost(cents: number): string {
  return `¥${centsToYuan(cents).toFixed(2)}`
}

function formatRegionNames(region: ShippingTemplateRegion): string {
  return parseRegionNames(region.region_names).join('、')
}

function formatFirstUnit(region: ShippingTemplateRegion): string {
  const template = list.value.find(t => t.id === region.template_id)
  if (!template) return `${region.first_unit}`
  const unit = getUnitLabel(template.charge_type)
  return unit ? `${region.first_unit}${unit}` : `${region.first_unit}`
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="shipping-templates-container">
    <div class="page-header">
      <h2>运费模板管理</h2>
      <el-button type="primary" @click="openCreate">新建模板</el-button>
    </div>

    <!-- Template List Table -->
    <el-table v-loading="loading" :data="list" stripe>
      <el-table-column prop="name" label="模板名称" width="180" />
      <el-table-column prop="charge_type" label="计费方式" width="100">
        <template #default="{ row }">
          {{ formatChargeType(row.charge_type) }}
        </template>
      </el-table-column>
      <el-table-column label="默认运费" width="200">
        <template #default="{ row }">
          首{{ row.default_first_unit }}{{ getUnitLabel(row.charge_type) }}:
          {{ formatCost(row.default_first_cost) }}
          <br />
          续{{ row.default_continue_unit }}{{ getUnitLabel(row.charge_type) }}:
          {{ formatCost(row.default_continue_cost) }}
        </template>
      </el-table-column>
      <el-table-column label="包邮门槛" width="120">
        <template #default="{ row }">
          {{ row.free_threshold ? formatCost(row.free_threshold) : '-' }}
        </template>
      </el-table-column>
      <el-table-column label="预计送达" width="120">
        <template #default="{ row }">
          {{
            row.estimate_days_min && row.estimate_days_max
              ? `${row.estimate_days_min}-${row.estimate_days_max}天`
              : '-'
          }}
        </template>
      </el-table-column>
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
      <el-table-column label="操作" width="200" fixed="right">
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

    <!-- Create/Edit Dialog -->
    <el-dialog
      v-model="showDialog"
      :title="dialogMode === 'create' ? '新建运费模板' : '编辑运费模板'"
      width="800px"
      @close="activeTab = 'basic'"
    >
      <el-tabs v-model="activeTab">
        <!-- Basic Info Tab -->
        <el-tab-pane label="基本信息" name="basic">
          <el-form :model="form" label-width="120px">
            <el-form-item label="模板名称" required>
              <el-input v-model="form.name" placeholder="请输入模板名称" />
            </el-form-item>
            <el-form-item label="模板描述">
              <el-input
                v-model="form.description"
                type="textarea"
                :rows="2"
                placeholder="请输入模板描述"
              />
            </el-form-item>
            <el-form-item label="计费方式" required>
              <el-select v-model="form.charge_type" placeholder="请选择计费方式">
                <el-option label="按重量" value="weight" />
                <el-option label="按件数" value="quantity" />
                <el-option label="固定运费" value="fixed" />
              </el-select>
            </el-form-item>
            <el-form-item label="默认首件/首重" required>
              <el-input-number v-model="form.default_first_unit" :min="1" :max="999999" />
              <span style="margin-left: 10px">{{ chargeTypeUnit }}</span>
            </el-form-item>
            <el-form-item label="默认首件运费" required>
              <el-input-number v-model="form.default_first_cost" :min="0" :max="999999" />
              <span style="margin-left: 10px">分 ({{ formatCost(form.default_first_cost) }})</span>
            </el-form-item>
            <el-form-item label="默认续件/续重" required>
              <el-input-number v-model="form.default_continue_unit" :min="1" :max="999999" />
              <span style="margin-left: 10px">{{ chargeTypeUnit }}</span>
            </el-form-item>
            <el-form-item label="默认续件运费" required>
              <el-input-number v-model="form.default_continue_cost" :min="0" :max="999999" />
              <span style="margin-left: 10px"
                >分 ({{ formatCost(form.default_continue_cost) }})</span
              >
            </el-form-item>
            <el-form-item label="包邮门槛">
              <el-input-number v-model="form.free_threshold" :min="0" :max="999999" />
              <span style="margin-left: 10px">分</span>
              <span style="margin-left: 10px; color: #999; font-size: 12px"
                >订单金额满此金额包邮</span
              >
            </el-form-item>
            <el-form-item label="预计送达天数">
              <el-input-number
                v-model="form.estimate_days_min"
                :min="1"
                :max="99"
                placeholder="最少"
                style="width: 120px"
              />
              <span style="margin: 0 10px">-</span>
              <el-input-number
                v-model="form.estimate_days_max"
                :min="1"
                :max="99"
                placeholder="最多"
                style="width: 120px"
              />
              <span style="margin-left: 10px">天</span>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- Region Pricing Tab -->
        <el-tab-pane label="区域定价" name="regions" :disabled="dialogMode === 'create'">
          <div style="margin-bottom: 15px">
            <el-button type="primary" size="small" @click="openCreateRegion">
              + 添加区域
            </el-button>
            <span style="margin-left: 10px; color: #999; font-size: 12px">
              为特定地区设置不同的运费标准
            </span>
          </div>

          <el-table v-loading="regionsLoading" :data="regions" stripe size="small">
            <el-table-column label="地区" min-width="150">
              <template #default="{ row }">
                {{ formatRegionNames(row) }}
              </template>
            </el-table-column>
            <el-table-column label="首件/首重" width="120">
              <template #default="{ row }">
                {{ formatFirstUnit(row) }}
              </template>
            </el-table-column>
            <el-table-column label="首件运费" width="100">
              <template #default="{ row }">
                {{ formatCost(row.first_cost) }}
              </template>
            </el-table-column>
            <el-table-column label="续件/续重" width="120">
              <template #default="{ row }">
                {{ row.continue_unit }}{{ regionChargeTypeUnit }}
              </template>
            </el-table-column>
            <el-table-column label="续件运费" width="100">
              <template #default="{ row }">
                {{ formatCost(row.continue_cost) }}
              </template>
            </el-table-column>
            <el-table-column label="包邮门槛" width="100">
              <template #default="{ row }">
                {{ row.free_threshold ? formatCost(row.free_threshold) : '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="is_active" label="状态" width="70">
              <template #default="{ row }">
                <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
                  {{ row.is_active ? '启用' : '禁用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click="openEditRegion(row)">
                  编辑
                </el-button>
                <el-button link type="primary" size="small" @click="handleToggleRegionActive(row)">
                  {{ row.is_active ? '禁用' : '启用' }}
                </el-button>
                <el-button link type="danger" size="small" @click="handleDeleteRegion(row)">
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-empty
            v-if="!regionsLoading && regions.length === 0"
            description="暂无区域配置，点击上方按钮添加"
            :image-size="80"
          />
        </el-tab-pane>
      </el-tabs>

      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="submit">确定</el-button>
      </template>
    </el-dialog>

    <!-- Add/Edit Region Dialog -->
    <el-dialog
      v-model="showRegionDialog"
      :title="regionDialogMode === 'create' ? '添加区域' : '编辑区域'"
      width="600px"
    >
      <el-form :model="regionForm" label-width="120px">
        <el-form-item label="选择地区" required>
          <el-select
            v-model="selectedProvinces"
            multiple
            placeholder="请选择地区"
            style="width: 100%"
            @change="handleProvinceChange"
          >
            <el-option
              v-for="province in PROVINCES"
              :key="province.code"
              :label="province.name"
              :value="province.code"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="首件/首重" required>
          <el-input-number v-model="regionForm.first_unit" :min="1" :max="999999" />
          <span style="margin-left: 10px">{{ regionChargeTypeUnit || chargeTypeUnit }}</span>
        </el-form-item>
        <el-form-item label="首件运费" required>
          <el-input-number v-model="regionForm.first_cost" :min="0" :max="999999" />
          <span style="margin-left: 10px">分 ({{ formatCost(regionForm.first_cost) }})</span>
        </el-form-item>
        <el-form-item label="续件/续重" required>
          <el-input-number v-model="regionForm.continue_unit" :min="1" :max="999999" />
          <span style="margin-left: 10px">{{ regionChargeTypeUnit || chargeTypeUnit }}</span>
        </el-form-item>
        <el-form-item label="续件运费" required>
          <el-input-number v-model="regionForm.continue_cost" :min="0" :max="999999" />
          <span style="margin-left: 10px">分 ({{ formatCost(regionForm.continue_cost) }})</span>
        </el-form-item>
        <el-form-item label="包邮门槛">
          <el-input-number v-model="regionForm.free_threshold" :min="0" :max="999999" />
          <span style="margin-left: 10px">分</span>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showRegionDialog = false">取消</el-button>
        <el-button type="primary" :loading="regionSubmitLoading" @click="submitRegion">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.shipping-templates-container {
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
