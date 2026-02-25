<template>
  <el-tree-select
    :model-value="modelValue"
    :data="treeData"
    :props="treeProps"
    :placeholder="placeholder"
    :disabled="disabled || loading"
    :loading="loading"
    :clearable="clearable"
    :check-strictly="true"
    :render-after-expand="false"
    node-key="id"
    class="category-tree-select"
    @update:model-value="handleChange"
  />
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { getCategoryTree, type PointCategory } from '@/api/pointCategory'

/**
 * CategoryTreeSelect.vue - 分类树选择器组件
 *
 * 用于在表单中选择积分商品分类，支持层级结构展示
 *
 * @features
 * - 支持单选分类
 * - 自动加载分类树数据
 * - 支持禁用状态
 * - 支持清除选择
 * - 懒加载优化性能
 *
 * @example
 * ```vue
 * <CategoryTreeSelect
 *   v-model="formData.category_id"
 *   placeholder="请选择商品分类"
 *   :disabled="isEdit"
 * />
 * ```
 */

// ==================== Types ====================
interface TreeNode {
  id: string
  label: string
  value: string
  children?: TreeNode[]
  level: number
  is_active: boolean
}

interface Props {
  /** 当前选中的分类ID */
  modelValue?: string | null
  /** 占位文本 */
  placeholder?: string
  /** 是否禁用 */
  disabled?: boolean
  /** 是否可清除 */
  clearable?: boolean
  /** 是否只显示启用的分类 */
  activeOnly?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: null,
  placeholder: '请选择分类',
  disabled: false,
  clearable: true,
  activeOnly: true,
})

// ==================== Emits ====================
const emit = defineEmits<{
  'update:modelValue': [value: string | null]
}>()

// ==================== State ====================
const treeData = ref<TreeNode[]>([])
const loading = ref(false)

// Tree select props配置
const treeProps = {
  label: 'label',
  value: 'value',
  children: 'children',
  disabled: (data: TreeNode) => !data.is_active,
}

// ==================== Methods ====================
/**
 * 加载分类树数据
 */
async function loadCategories() {
  loading.value = true
  try {
    const categories = await getCategoryTree({ active_only: props.activeOnly })
    treeData.value = transformToTreeNodes(categories)
  } catch (error: any) {
    console.error('Failed to load categories:', error)
    ElMessage.error(error.message || '加载分类失败')
    treeData.value = []
  } finally {
    loading.value = false
  }
}

/**
 * 将API返回的分类数据转换为树节点格式
 */
function transformToTreeNodes(categories: PointCategory[]): TreeNode[] {
  return categories.map(cat => ({
    id: cat.id,
    label: cat.name,
    value: cat.id,
    level: cat.level,
    is_active: cat.is_active,
    children: cat.children ? transformToTreeNodes(cat.children) : undefined,
  }))
}

/**
 * 处理选择变化
 */
function handleChange(value: string | null) {
  emit('update:modelValue', value)
}

// ==================== Lifecycle ====================
onMounted(() => {
  loadCategories()
})

// 监听activeOnly变化，重新加载数据
watch(
  () => props.activeOnly,
  () => {
    loadCategories()
  }
)
</script>

<style scoped>
.category-tree-select {
  width: 100%;
}
</style>
