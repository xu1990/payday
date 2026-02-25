<template>
  <div class="components-demo">
    <el-card class="demo-card">
      <template #header>
        <h2>Point Shop Components Demo</h2>
      </template>

      <!-- CategoryTreeSelect Demo -->
      <div class="demo-section">
        <h3>CategoryTreeSelect</h3>
        <CategoryTreeSelect v-model="categoryId" placeholder="请选择商品分类" :clearable="true" />
        <p class="demo-result">Selected Category ID: {{ categoryId || 'None' }}</p>
      </div>

      <el-divider />

      <!-- CourierSelect Demo -->
      <div class="demo-section">
        <h3>CourierSelect</h3>
        <CourierSelect
          v-model="courierCode"
          placeholder="请选择物流公司"
          :show-code="true"
          :active-only="true"
        />
        <p class="demo-result">Selected Courier: {{ courierCode || 'None' }}</p>
      </div>

      <el-divider />

      <!-- AddressForm Demo -->
      <div class="demo-section">
        <h3>AddressForm</h3>
        <AddressForm ref="addressFormRef" v-model="addressData" :show-default="true" />
        <div class="demo-actions">
          <el-button @click="handleValidateAddress">验证表单</el-button>
          <el-button @click="handleResetAddress">重置表单</el-button>
          <el-button type="primary" @click="handleSubmitAddress">提交</el-button>
        </div>
        <el-divider />
        <div class="demo-result">
          <h4>Address Data:</h4>
          <pre>{{ JSON.stringify(addressData, null, 2) }}</pre>
        </div>
      </div>

      <el-divider />

      <!-- RegionPricingForm Demo -->
      <div class="demo-section">
        <h3>RegionPricingForm</h3>
        <el-radio-group v-model="chargeType" class="charge-type-selector">
          <el-radio-button value="free">包邮</el-radio-button>
          <el-radio-button value="flat">统一运费</el-radio-button>
          <el-radio-button value="by_region">按地区计费</el-radio-button>
        </el-radio-group>
        <br /><br />
        <RegionPricingForm v-model="pricingConfig" :charge-type="chargeType" />
        <el-divider />
        <div class="demo-result">
          <h4>Pricing Config:</h4>
          <pre>{{ JSON.stringify(pricingConfig, null, 2) }}</pre>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  CategoryTreeSelect,
  CourierSelect,
  AddressForm,
  RegionPricingForm,
  type AddressFormData,
  type PricingConfig,
} from '.'

// CategoryTreeSelect
const categoryId = ref<string | null>(null)

// CourierSelect
const courierCode = ref<string | null>(null)

// AddressForm
const addressFormRef = ref()
const addressData = ref<AddressFormData>({
  contact_name: '',
  contact_phone: '',
  province_code: '',
  province_name: '',
  city_code: '',
  city_name: '',
  district_code: '',
  district_name: '',
  detailed_address: '',
  postal_code: '',
  is_default: false,
})

async function handleValidateAddress() {
  const isValid = await addressFormRef.value?.validate()
  if (isValid) {
    ElMessage.success('地址表单验证通过')
  } else {
    ElMessage.error('地址表单验证失败')
  }
}

function handleResetAddress() {
  addressFormRef.value?.resetFields()
  ElMessage.info('表单已重置')
}

function handleSubmitAddress() {
  console.log('Submit address:', addressData.value)
  ElMessage.success('地址已提交（查看控制台）')
}

// RegionPricingForm
const chargeType = ref<'free' | 'flat' | 'by_region'>('by_region')
const pricingConfig = ref<PricingConfig>({
  first_piece: 1,
  flat_fee: 0,
  region_pricing: [
    {
      provinces: ['440000'],
      first_piece: 1,
      first_piece_fee: 10,
      additional_piece: 1,
      additional_piece_fee: 5,
    },
  ],
})
</script>

<style scoped>
.components-demo {
  padding: 20px;
}

.demo-card {
  max-width: 900px;
  margin: 0 auto;
}

.demo-section {
  padding: 20px 0;
}

.demo-section h3 {
  margin-bottom: 15px;
  color: var(--el-text-color-primary);
}

.demo-section h4 {
  margin-bottom: 10px;
  color: var(--el-text-color-regular);
}

.demo-result {
  margin-top: 15px;
  padding: 10px;
  background-color: var(--el-fill-color-light);
  border-radius: 4px;
  font-size: 14px;
}

.demo-result pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.demo-actions {
  margin-top: 15px;
  display: flex;
  gap: 10px;
}

.charge-type-selector {
  margin-bottom: 10px;
}
</style>
