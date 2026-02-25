<template>
  <el-select
    :model-value="modelValue"
    :placeholder="placeholder"
    :disabled="disabled || loading"
    :loading="loading"
    :clearable="clearable"
    :filterable="filterable"
    class="courier-select"
    @update:model-value="handleChange"
  >
    <el-option
      v-for="courier in couriers"
      :key="courier.id"
      :label="courier.name"
      :value="courier.code"
      :disabled="!courier.is_active"
    >
      <div class="courier-option">
        <span class="courier-name">{{ courier.name }}</span>
        <span v-if="showCode" class="courier-code">({{ courier.code }})</span>
        <el-tag v-if="courier.supports_cod" size="small" type="success" class="courier-tag">
          货到付款
        </el-tag>
        <el-tag v-if="courier.supports_cold_chain" size="small" type="info" class="courier-tag">
          冷链
        </el-tag>
      </div>
    </el-option>
  </el-select>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { listCouriers, listActiveCouriers, type CourierCompany } from '@/api/courier'

/**
 * CourierSelect.vue - 物流公司选择器组件
 *
 * 用于在表单中选择物流公司，显示物流公司特性标签
 *
 * @features
 * - 支持搜索/过滤
 * - 显示物流公司特性（货到付款、冷链等）
 * - 支持只显示启用的物流公司
 * - 支持显示物流公司代码
 * - 自动加载物流公司列表
 *
 * @example
 * ```vue
 * <CourierSelect
 *   v-model="formData.courier_code"
 *   placeholder="请选择物流公司"
 *   :active-only="true"
 *   :show-code="true"
 * />
 * ```
 */

// ==================== Types ====================
interface Props {
  /** 当前选中的物流公司代码 */
  modelValue?: string | null
  /** 占位文本 */
  placeholder?: string
  /** 是否禁用 */
  disabled?: boolean
  /** 是否可清除 */
  clearable?: boolean
  /** 是否可搜索/过滤 */
  filterable?: boolean
  /** 是否只显示启用的物流公司 */
  activeOnly?: boolean
  /** 是否显示物流公司代码 */
  showCode?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: null,
  placeholder: '请选择物流公司',
  disabled: false,
  clearable: true,
  filterable: true,
  activeOnly: true,
  showCode: false,
})

// ==================== Emits ====================
const emit = defineEmits<{
  'update:modelValue': [value: string | null]
}>()

// ==================== State ====================
const couriers = ref<CourierCompany[]>([])
const loading = ref(false)

// ==================== Methods ====================
/**
 * 加载物流公司列表
 */
async function loadCouriers() {
  loading.value = true
  try {
    // 如果只需要启用的物流公司，使用专用接口
    if (props.activeOnly) {
      couriers.value = await listActiveCouriers()
    } else {
      // 否则获取所有物流公司（不限制数量）
      const result = await listCouriers({
        active_only: false,
        limit: 1000, // 获取较多数据用于选择
        offset: 0,
      })
      couriers.value = result.couriers
    }
  } catch (error: any) {
    console.error('Failed to load couriers:', error)
    ElMessage.error(error.message || '加载物流公司失败')
    couriers.value = []
  } finally {
    loading.value = false
  }
}

/**
 * 处理选择变化
 */
function handleChange(value: string | null) {
  emit('update:modelValue', value)
}

// ==================== Lifecycle ====================
onMounted(() => {
  loadCouriers()
})

// 监听activeOnly变化，重新加载数据
watch(
  () => props.activeOnly,
  () => {
    loadCouriers()
  }
)
</script>

<style scoped>
.courier-select {
  width: 100%;
}

.courier-option {
  display: flex;
  align-items: center;
  gap: 8px;
}

.courier-name {
  flex: 1;
}

.courier-code {
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.courier-tag {
  flex-shrink: 0;
}
</style>
