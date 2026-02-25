<template>
  <div class="region-pricing-form">
    <div class="form-header">
      <el-text type="info">
        {{
          chargeType === 'free'
            ? '包邮地区配置'
            : chargeType === 'flat'
              ? '统一运费'
              : '按地区计费配置'
        }}
      </el-text>
      <el-button
        v-if="chargeType === 'by_region'"
        type="primary"
        size="small"
        :disabled="disabled"
        @click="handleAddRegion"
      >
        添加地区
      </el-button>
    </div>

    <!-- 包邮或统一运费模式 -->
    <div v-if="chargeType === 'free' || chargeType === 'flat'" class="flat-charge-section">
      <el-form-item label="首件数量">
        <el-input-number
          v-model="localValue.first_piece"
          :min="1"
          :disabled="disabled"
          controls-position="right"
        />
      </el-form-item>

      <el-form-item v-if="chargeType === 'flat'" label="运费（元）">
        <el-input-number
          v-model="localValue.flat_fee"
          :min="0"
          :precision="2"
          :disabled="disabled"
          controls-position="right"
        />
      </el-form-item>
    </div>

    <!-- 按地区计费模式 -->
    <div v-else-if="chargeType === 'by_region'" class="by-region-section">
      <el-table :data="localValue.region_pricing" border style="width: 100%">
        <el-table-column label="配送地区" min-width="200">
          <template #default="{ row }">
            <el-select
              v-model="row.provinces"
              multiple
              collapse-tags
              collapse-tags-tooltip
              placeholder="选择省份"
              :disabled="disabled"
              style="width: 100%"
            >
              <el-option
                v-for="province in provinceOptions"
                :key="province.code"
                :label="province.name"
                :value="province.code"
              />
            </el-select>
          </template>
        </el-table-column>

        <el-table-column label="首件（件）" width="120">
          <template #default="{ row }">
            <el-input-number
              v-model="row.first_piece"
              :min="1"
              :disabled="disabled"
              controls-position="right"
              size="small"
            />
          </template>
        </el-table-column>

        <el-table-column label="首件运费（元）" width="130">
          <template #default="{ row }">
            <el-input-number
              v-model="row.first_piece_fee"
              :min="0"
              :precision="2"
              :disabled="disabled"
              controls-position="right"
              size="small"
            />
          </template>
        </el-table-column>

        <el-table-column label="续件（件）" width="120">
          <template #default="{ row }">
            <el-input-number
              v-model="row.additional_piece"
              :min="1"
              :disabled="disabled"
              controls-position="right"
              size="small"
            />
          </template>
        </el-table-column>

        <el-table-column label="续件运费（元）" width="130">
          <template #default="{ row }">
            <el-input-number
              v-model="row.additional_piece_fee"
              :min="0"
              :precision="2"
              :disabled="disabled"
              controls-position="right"
              size="small"
            />
          </template>
        </el-table-column>

        <el-table-column label="操作" width="80" fixed="right">
          <template #default="{ $index }">
            <el-button
              type="danger"
              link
              size="small"
              :disabled="disabled"
              @click="handleRemoveRegion($index)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty
        v-if="!localValue.region_pricing || localValue.region_pricing.length === 0"
        description="暂无地区配置，点击上方「添加地区」按钮添加"
        :image-size="80"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'

/**
 * RegionPricingForm.vue - 运费地区配置表单组件
 *
 * 用于配置运费模板的地区定价规则
 *
 * @features
 * - 支持三种计费模式：包邮、统一运费、按地区计费
 * - 按地区计费支持多省份选择
 * - 支持首件/续件计费
 * - 可添加/删除地区配置
 *
 * @example
 * ```vue
 * <RegionPricingForm
 *   v-model="shippingData.pricing_config"
 *   :charge-type="shippingData.charge_type"
 *   :disabled="isEdit"
 * />
 * ```
 */

// ==================== Types ====================
export interface RegionPricing {
  provinces: string[] // 省份代码数组
  first_piece: number // 首件数量
  first_piece_fee: number // 首件运费
  additional_piece: number // 续件数量
  additional_piece_fee: number // 续件运费
}

export interface PricingConfig {
  // 包邮或统一运费模式
  first_piece?: number
  flat_fee?: number

  // 按地区计费模式
  region_pricing?: RegionPricing[]
}

interface Province {
  code: string
  name: string
}

interface Props {
  modelValue: PricingConfig
  chargeType: 'free' | 'flat' | 'by_region'
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
})

// ==================== Emits ====================
const emit = defineEmits<{
  'update:modelValue': [value: PricingConfig]
}>()

// ==================== State ====================
// 本地数据副本
const localValue = ref<PricingConfig>({
  ...props.modelValue,
  first_piece: props.modelValue.first_piece || 1,
  flat_fee: props.modelValue.flat_fee || 0,
  region_pricing: props.modelValue.region_pricing || [],
})

// 省份选项（简化版，实际应从API或文件加载）
const provinceOptions: Province[] = [
  { code: '440000', name: '广东省' },
  { code: '110000', name: '北京市' },
  { code: '310000', name: '上海市' },
  { code: '330000', name: '浙江省' },
  { code: '320000', name: '江苏省' },
  { code: '370000', name: '山东省' },
  { code: '410000', name: '河南省' },
  { code: '420000', name: '湖北省' },
  { code: '430000', name: '湖南省' },
  { code: '510000', name: '四川省' },
]

// ==================== Methods ====================
/**
 * 添加地区配置
 */
function handleAddRegion() {
  if (!localValue.value.region_pricing) {
    localValue.value.region_pricing = []
  }

  localValue.value.region_pricing.push({
    provinces: [],
    first_piece: 1,
    first_piece_fee: 10,
    additional_piece: 1,
    additional_piece_fee: 5,
  })

  emitChange()
}

/**
 * 删除地区配置
 */
function handleRemoveRegion(index: number) {
  localValue.value.region_pricing?.splice(index, 1)
  emitChange()
}

/**
 * 触发更新事件
 */
function emitChange() {
  emit('update:modelValue', { ...localValue.value })
}

// ==================== Watch ====================
// 监听modelValue变化
watch(
  () => props.modelValue,
  newVal => {
    localValue.value = {
      ...newVal,
      first_piece: newVal.first_piece || 1,
      flat_fee: newVal.flat_fee || 0,
      region_pricing: newVal.region_pricing || [],
    }
  },
  { deep: true }
)

// 监听本地数据变化，自动触发更新
watch(
  localValue,
  () => {
    emitChange()
  },
  { deep: true }
)
</script>

<style scoped>
.region-pricing-form {
  width: 100%;
}

.form-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.flat-charge-section {
  display: flex;
  gap: 20px;
}

.by-region-section {
  margin-top: 10px;
}
</style>
