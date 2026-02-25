<template>
  <el-form
    ref="formRef"
    :model="formData"
    :rules="formRules"
    label-width="100px"
    class="address-form"
    @validate="handleValidate"
  >
    <!-- 联系人姓名 -->
    <el-form-item label="联系人" prop="contact_name">
      <el-input
        v-model="formData.contact_name"
        placeholder="请输入联系人姓名"
        clearable
        :disabled="disabled"
      />
    </el-form-item>

    <!-- 联系电话 -->
    <el-form-item label="联系电话" prop="contact_phone">
      <el-input
        v-model="formData.contact_phone"
        placeholder="请输入联系电话"
        clearable
        :disabled="disabled"
        maxlength="11"
      />
    </el-form-item>

    <!-- 省市区选择 -->
    <el-form-item label="所在地区" prop="region">
      <el-cascader
        :model-value="regionValue"
        :options="regionOptions"
        :props="cascaderProps"
        placeholder="请选择省/市/区"
        clearable
        filterable
        :disabled="disabled"
        class="region-cascader"
        @update:model-value="handleRegionChange"
      />
    </el-form-item>

    <!-- 详细地址 -->
    <el-form-item label="详细地址" prop="detailed_address">
      <el-input
        v-model="formData.detailed_address"
        type="textarea"
        :rows="3"
        placeholder="请输入详细地址，如街道、楼栋号、门牌号等"
        :disabled="disabled"
        maxlength="200"
        show-word-limit
      />
    </el-form-item>

    <!-- 邮政编码 -->
    <el-form-item label="邮政编码" prop="postal_code">
      <el-input
        v-model="formData.postal_code"
        placeholder="请输入邮政编码（可选）"
        clearable
        :disabled="disabled"
        maxlength="6"
      />
    </el-form-item>

    <!-- 是否默认地址 -->
    <el-form-item v-if="showDefault" label="设为默认" prop="is_default">
      <el-switch
        v-model="formData.is_default"
        :active-text="formData.is_default ? '是' : '否'"
        :disabled="disabled"
      />
    </el-form-item>
  </el-form>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import type { UserAddress } from '@/api/userAddress'

/**
 * AddressForm.vue - 地址表单组件
 *
 * 用于输入和编辑用户收货地址信息
 *
 * @features
 * - 完整的地址字段（联系人、电话、省市区、详细地址、邮编）
 * - 表单验证（手机号格式、必填项）
 * - 支持省市区级联选择
 * - 支持设为默认地址
 * - 支持禁用状态
 *
 * @example
 * ```vue
 * <AddressForm
 *   ref="addressFormRef"
 *   v-model="addressData"
 *   :show-default="true"
 *   @validate="handleValidate"
 * />
 * ```
 */

// ==================== Types ====================
export interface AddressFormData {
  contact_name: string
  contact_phone: string
  province_code: string
  province_name: string
  city_code: string
  city_name: string
  district_code: string
  district_name: string
  detailed_address: string
  postal_code?: string
  is_default?: boolean
}

interface RegionData {
  value: string
  label: string
  code: string
  children?: RegionData[]
}

interface Props {
  /** 地址数据 */
  modelValue: AddressFormData | UserAddress
  /** 是否显示"设为默认"开关 */
  showDefault?: boolean
  /** 是否禁用表单 */
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showDefault: false,
  disabled: false,
})

// ==================== Emits ====================
const emit = defineEmits<{
  'update:modelValue': [value: AddressFormData]
  validate: [isValid: boolean]
}>()

// ==================== State ====================
const formRef = ref<FormInstance>()

// 表单数据（本地副本）
const formData = computed<AddressFormData>(() => {
  const value = props.modelValue
  // 如果是UserAddress类型，转换为AddressFormData
  if ('id' in value) {
    const addr = value as UserAddress
    return {
      contact_name: addr.contact_name,
      contact_phone: addr.contact_phone,
      province_code: addr.province_code,
      province_name: addr.province_name,
      city_code: addr.city_code,
      city_name: addr.city_name,
      district_code: addr.district_code,
      district_name: addr.district_name,
      detailed_address: addr.detailed_address,
      postal_code: addr.postal_code || '',
      is_default: addr.is_default,
    }
  }
  return value as AddressFormData
})

// 省市区级联值
const regionValue = computed(() => {
  return [
    formData.value.province_code,
    formData.value.city_code,
    formData.value.district_code,
  ].filter(Boolean)
})

// 表单验证规则
const formRules: FormRules = {
  contact_name: [
    { required: true, message: '请输入联系人姓名', trigger: 'blur' },
    { min: 2, max: 20, message: '联系人姓名长度在2-20个字符', trigger: 'blur' },
  ],
  contact_phone: [
    { required: true, message: '请输入联系电话', trigger: 'blur' },
    {
      pattern: /^1[3-9]\d{9}$/,
      message: '请输入正确的手机号码',
      trigger: 'blur',
    },
  ],
  detailed_address: [
    { required: true, message: '请输入详细地址', trigger: 'blur' },
    { min: 5, max: 200, message: '详细地址长度在5-200个字符', trigger: 'blur' },
  ],
  postal_code: [
    {
      pattern: /^\d{6}$/,
      message: '邮政编码格式不正确',
      trigger: 'blur',
    },
  ],
}

// Cascader配置
const cascaderProps = {
  value: 'code',
  label: 'label',
  children: 'children',
  expandTrigger: 'hover' as const,
}

// 简化的省市区数据（实际项目中应该从API或文件加载完整数据）
const regionOptions: RegionData[] = [
  {
    value: '广东省',
    label: '广东省',
    code: '440000',
    children: [
      {
        value: '广州市',
        label: '广州市',
        code: '440100',
        children: [
          { value: '天河区', label: '天河区', code: '440106' },
          { value: '越秀区', label: '越秀区', code: '440104' },
          { value: '海珠区', label: '海珠区', code: '440105' },
          { value: '荔湾区', label: '荔湾区', code: '440103' },
        ],
      },
      {
        value: '深圳市',
        label: '深圳市',
        code: '440300',
        children: [
          { value: '南山区', label: '南山区', code: '440305' },
          { value: '福田区', label: '福田区', code: '440304' },
          { value: '罗湖区', label: '罗湖区', code: '440303' },
        ],
      },
    ],
  },
  {
    value: '北京市',
    label: '北京市',
    code: '110000',
    children: [
      {
        value: '北京市',
        label: '北京市',
        code: '110100',
        children: [
          { value: '东城区', label: '东城区', code: '110101' },
          { value: '西城区', label: '西城区', code: '110102' },
          { value: '朝阳区', label: '朝阳区', code: '110105' },
          { value: '海淀区', label: '海淀区', code: '110108' },
        ],
      },
    ],
  },
  {
    value: '上海市',
    label: '上海市',
    code: '310000',
    children: [
      {
        value: '上海市',
        label: '上海市',
        code: '310100',
        children: [
          { value: '黄浦区', label: '黄浦区', code: '310101' },
          { value: '徐汇区', label: '徐汇区', code: '310104' },
          { value: '长宁区', label: '长宁区', code: '310105' },
          { value: '静安区', label: '静安区', code: '310106' },
          { value: '普陀区', label: '普陀区', code: '310107' },
        ],
      },
    ],
  },
]

// ==================== Methods ====================
/**
 * 处理省市区选择变化
 */
function handleRegionChange(value: string[]) {
  if (value && value.length === 3) {
    // 查找对应的省市区名称
    const province = regionOptions.find(p => p.code === value[0])
    const city = province?.children?.find(c => c.code === value[1])
    const district = city?.children?.find(d => d.code === value[2])

    emit('update:modelValue', {
      ...formData.value,
      province_code: value[0],
      province_name: province?.label || '',
      city_code: value[1],
      city_name: city?.label || '',
      district_code: value[2],
      district_name: district?.label || '',
    })
  }
}

/**
 * 处理表单验证事件
 */
function handleValidate(prop: string, isValid: boolean) {
  // 可以在这里处理单个字段验证结果
}

/**
 * 验证整个表单
 */
async function validate(): Promise<boolean> {
  if (!formRef.value) return false
  try {
    await formRef.value.validate()
    return true
  } catch {
    return false
  }
}

/**
 * 重置表单
 */
function resetFields() {
  formRef.value?.resetFields()
}

/**
 * 清除验证
 */
function clearValidate() {
  formRef.value?.clearValidate()
}

// ==================== Expose ====================
defineExpose({
  formRef,
  validate,
  resetFields,
  clearValidate,
})
</script>

<style scoped>
.address-form {
  width: 100%;
}

.region-cascader {
  width: 100%;
}
</style>
