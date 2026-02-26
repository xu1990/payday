<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete } from '@element-plus/icons-vue'
import {
  listSpecificationTemplates,
  createSpecificationTemplate,
  updateSpecificationTemplate,
  deleteSpecificationTemplate,
  type SpecificationTemplate,
} from '@/api/specificationTemplate'

// Data
const loading = ref(false)
const templates = ref<SpecificationTemplate[]>([])
const dialogVisible = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const editId = ref<string | null>(null)
const saving = ref(false)

// Form
const form = ref({
  name: '',
  description: '',
  values: [''],
  sort_order: 0,
  is_active: true,
})

// Preset templates for quick add
const presetTemplates = [
  { name: '颜色', values: ['红色', '蓝色', '黑色', '白色', '灰色', '绿色'] },
  { name: '尺寸', values: ['S', 'M', 'L', 'XL', 'XXL'] },
  { name: '尺码', values: ['36', '37', '38', '39', '40', '41', '42'] },
  { name: '容量', values: ['64GB', '128GB', '256GB', '512GB', '1TB'] },
  { name: '规格', values: ['大', '中', '小', '迷你'] },
  { name: '款式', values: ['标准款', '升级款', '豪华款'] },
  { name: '套餐', values: ['单件装', '两件装', '三件装', '礼盒装'] },
  { name: '材质', values: ['棉', '涤纶', '丝绸', '羊毛', '真皮'] },
]

// Load data
async function loadData() {
  loading.value = true
  try {
    const res = await listSpecificationTemplates()
    templates.value = res?.templates || []
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : '加载失败'
    ElMessage.error(errorMessage)
  } finally {
    loading.value = false
  }
}

// Open create dialog
function openCreate() {
  dialogMode.value = 'create'
  editId.value = null
  form.value = {
    name: '',
    description: '',
    values: [''],
    sort_order: 0,
    is_active: true,
  }
  dialogVisible.value = true
}

// Open edit dialog
function openEdit(template: SpecificationTemplate) {
  dialogMode.value = 'edit'
  editId.value = template.id
  form.value = {
    name: template.name,
    description: template.description || '',
    values: [...template.values, ''],
    sort_order: template.sort_order,
    is_active: template.is_active,
  }
  dialogVisible.value = true
}

// Add value input
function addValueInput() {
  form.value.values.push('')
}

// Remove value
function removeValue(index: number) {
  if (form.value.values.length > 1) {
    form.value.values.splice(index, 1)
  }
}

// Handle value input change
function handleValueInput(index: number, value: string) {
  form.value.values[index] = value
  // Auto add new input if last one has value
  if (index === form.value.values.length - 1 && value.trim()) {
    form.value.values.push('')
  }
}

// Get valid values (non-empty)
function getValidValues(): string[] {
  return form.value.values
    .map(v => v.trim())
    .filter(v => v.length > 0)
}

// Submit form
async function submit() {
  if (!form.value.name.trim()) {
    ElMessage.warning('请输入规格名称')
    return
  }

  const validValues = getValidValues()
  if (validValues.length === 0) {
    ElMessage.warning('请至少输入一个规格值')
    return
  }

  saving.value = true
  try {
    if (dialogMode.value === 'create') {
      await createSpecificationTemplate({
        name: form.value.name.trim(),
        description: form.value.description || null,
        values: validValues,
        sort_order: form.value.sort_order,
        is_active: form.value.is_active,
      })
      ElMessage.success('创建成功')
    } else if (editId.value) {
      await updateSpecificationTemplate(editId.value, {
        name: form.value.name.trim(),
        description: form.value.description || null,
        values: validValues,
        sort_order: form.value.sort_order,
        is_active: form.value.is_active,
      })
      ElMessage.success('更新成功')
    }
    dialogVisible.value = false
    await loadData()
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : '操作失败'
    ElMessage.error(errorMessage)
  } finally {
    saving.value = false
  }
}

// Delete template
async function handleDelete(template: SpecificationTemplate) {
  try {
    await ElMessageBox.confirm(
      `确定要删除规格模板"${template.name}"吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    await deleteSpecificationTemplate(template.id)
    ElMessage.success('删除成功')
    await loadData()
  } catch (e: unknown) {
    if (e === 'cancel') return
    const errorMessage = e instanceof Error ? e.message : '删除失败'
    ElMessage.error(errorMessage)
  }
}

// Quick add from preset
async function quickAdd(preset: { name: string; values: string[] }) {
  try {
    await createSpecificationTemplate({
      name: preset.name,
      values: preset.values,
      is_active: true,
    })
    ElMessage.success(`已添加"${preset.name}"规格模板`)
    await loadData()
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : '添加失败'
    ElMessage.error(errorMessage)
  }
}

// Toggle active status
async function toggleActive(template: SpecificationTemplate) {
  try {
    await updateSpecificationTemplate(template.id, {
      is_active: !template.is_active,
    })
    ElMessage.success(template.is_active ? '已禁用' : '已启用')
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
  <div class="spec-templates-container">
    <div class="page-header">
      <h2>规格模板管理</h2>
      <el-button type="primary" :icon="Plus" @click="openCreate">新增模板</el-button>
    </div>

    <!-- Quick add presets -->
    <el-card class="preset-card" header="快速添加预设模板">
      <div class="preset-grid">
        <div
          v-for="preset in presetTemplates"
          :key="preset.name"
          class="preset-item"
          @click="quickAdd(preset)"
        >
          <div class="preset-name">{{ preset.name }}</div>
          <div class="preset-values">
            <el-tag v-for="v in preset.values.slice(0, 4)" :key="v" size="small" style="margin: 2px">
              {{ v }}
            </el-tag>
            <el-tag v-if="preset.values.length > 4" size="small" type="info" style="margin: 2px">
              +{{ preset.values.length - 4 }}
            </el-tag>
          </div>
        </div>
      </div>
    </el-card>

    <!-- Templates list -->
    <el-card class="list-card">
      <el-table :data="templates" v-loading="loading" border>
        <el-table-column prop="name" label="规格名称" width="150" />
        <el-table-column prop="description" label="描述" min-width="150">
          <template #default="{ row }">
            {{ row.description || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="规格值" min-width="300">
          <template #default="{ row }">
            <el-tag
              v-for="value in row.values"
              :key="value"
              size="small"
              style="margin: 2px"
            >
              {{ value }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="sort_order" label="排序" width="80" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-switch
              :model-value="row.is_active"
              @change="toggleActive(row)"
              active-text="启用"
              inactive-text="禁用"
            />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" :icon="Edit" @click="openEdit(row)">编辑</el-button>
            <el-button link type="danger" :icon="Delete" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Create/Edit Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogMode === 'create' ? '新增规格模板' : '编辑规格模板'"
      width="500px"
    >
      <el-form label-width="100px">
        <el-form-item label="规格名称" required>
          <el-input v-model="form.name" placeholder="如：颜色、尺寸、容量等" maxlength="50" />
        </el-form-item>

        <el-form-item label="描述">
          <el-input v-model="form.description" placeholder="规格描述（可选）" maxlength="200" />
        </el-form-item>

        <el-form-item label="规格值" required>
          <div class="value-inputs">
            <div v-for="(_, index) in form.values" :key="index" class="value-input-row">
              <el-input
                :model-value="form.values[index]"
                placeholder="输入规格值"
                @input="handleValueInput(index, $event)"
                maxlength="50"
                style="width: 200px"
              />
              <el-button
                v-if="form.values.length > 1"
                link
                type="danger"
                @click="removeValue(index)"
              >
                删除
              </el-button>
            </div>
            <el-button link type="primary" @click="addValueInput">+ 添加规格值</el-button>
          </div>
        </el-form-item>

        <el-form-item label="排序权重">
          <el-input-number v-model="form.sort_order" :min="0" :max="9999" />
          <span style="margin-left: 10px; color: #999; font-size: 12px">数值越大越靠前</span>
        </el-form-item>

        <el-form-item label="状态">
          <el-switch v-model="form.is_active" active-text="启用" inactive-text="禁用" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.spec-templates-container {
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

.preset-card {
  margin-bottom: 20px;
}

.preset-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.preset-item {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 12px;
  cursor: pointer;
  transition: all 0.3s;
}

.preset-item:hover {
  border-color: #409eff;
  background-color: #ecf5ff;
}

.preset-name {
  font-weight: 500;
  margin-bottom: 8px;
}

.preset-values {
  display: flex;
  flex-wrap: wrap;
}

.list-card {
  margin-bottom: 20px;
}

.value-inputs {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.value-input-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
