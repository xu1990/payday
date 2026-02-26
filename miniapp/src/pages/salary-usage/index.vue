<template>
  <view class="salary-usage-page">
    <!-- Header -->
    <view class="header">
      <text class="title">记一笔</text>
    </view>

    <!-- Form -->
    <view class="form">
      <!-- Usage Type Selection -->
      <view class="form-item">
        <text class="label">消费类型</text>
        <view class="type-grid">
          <view
            v-for="type in usageTypes"
            :key="type.value"
            :class="['type-item', { active: formData.usage_type === type.value }]"
            @tap="selectType(type.value)"
          >
            <text class="type-icon">{{ type.icon }}</text>
            <text class="type-label">{{ type.label }}</text>
          </view>
        </view>
      </view>

      <!-- Amount Input -->
      <view class="form-item">
        <text class="label">金额</text>
        <input
          v-model="formData.amount"
          class="amount-input"
          type="digit"
          placeholder="请输入金额"
          placeholder-class="placeholder"
        />
      </view>

      <!-- Date Selection -->
      <view class="form-item">
        <text class="label">日期</text>
        <picker mode="date" :value="formData.usage_date" @change="onDateChange">
          <view class="picker">
            {{ formData.usage_date || '选择日期' }}
          </view>
        </picker>
      </view>

      <!-- Salary Record Selection -->
      <view class="form-item">
        <text class="label">关联薪资</text>
        <picker :range="salaryRecords" range-key="label" @change="onSalaryChange">
          <view class="picker">
            {{ selectedSalaryLabel || '选择薪资记录' }}
          </view>
        </picker>
      </view>

      <!-- Description Input -->
      <view class="form-item">
        <text class="label">备注</text>
        <textarea
          v-model="formData.description"
          class="desc-input"
          placeholder="添加备注（可选）"
          placeholder-class="placeholder"
          maxlength="500"
        />
      </view>

      <!-- Submit Button -->
      <button class="submit-btn" :disabled="loading" @tap="handleSubmit">
        {{ loading ? '保存中...' : '保存' }}
      </button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { listSalary } from '@/api/salary'
import { createSalaryUsage } from '@/api/salary-usage'
import { showSuccess, showError } from '@/utils/toast'

interface FormData {
  usage_type: UsageType | ''
  amount: string
  usage_date: string
  salary_record_id: string
  description: string
}

const formData = ref({
  usage_type: '',
  amount: '',
  usage_date: '',
  salary_record_id: '',
  description: '',
})

const loading = ref(false)
const salaryRecords = ref>([])

const usageTypes = [
  { value: 'housing' as UsageType, label: '住房', icon: '🏠' },
  { value: 'food' as UsageType, label: '餐饮', icon: '🍔' },
  { value: 'transport' as UsageType, label: '交通', icon: '🚗' },
  { value: 'shopping' as UsageType, label: '购物', icon: '🛍️' },
  { value: 'entertainment' as UsageType, label: '娱乐', icon: '🎮' },
  { value: 'medical' as UsageType, label: '医疗', icon: '💊' },
  { value: 'education' as UsageType, label: '教育', icon: '📚' },
  { value: 'other' as UsageType, label: '其他', icon: '📝' },
]

const selectedSalaryLabel = computed(() => {
  if (!formData.value.salary_record_id) return ''
  const record = salaryRecords.value.find(r => r.id === formData.value.salary_record_id)
  return record?.label || ''
})

onMounted(() => {
  // Set default date to today
  const today = new Date().toISOString().split('T')[0]
  formData.value.usage_date = today

  // Load salary records
  loadSalaryRecords()
})

const selectType = (type) => {
  formData.value.usage_type = type
}

const onDateChange = (e: any) => {
  formData.value.usage_date = e.detail.value
}

const onSalaryChange = (e: any) => {
  const index = e.detail.value
  if (index >= 0 && index < salaryRecords.value.length) {
    formData.value.salary_record_id = salaryRecords.value[index].id
  }
}

const loadSalaryRecords = async () => {
  try {
    const records = await listSalary({ limit: 100 })

    // Format records for picker display
    salaryRecords.value = records.map(record => ({
      id: record.id,
      label: `${record.payday_date} - ¥${record.amount}`,
    }))
  } catch (error) {
    console.error('[salary-usage] Failed to load salary records:', error)
    showError('加载薪资记录失败')
  }
}

const handleSubmit = async () => {
  // Validate form
  if (!formData.value.usage_type) {
    showError('请选择消费类型')
    return
  }

  if (!formData.value.amount) {
    showError('请输入金额')
    return
  }

  const amountNum = parseFloat(formData.value.amount)
  if (isNaN(amountNum) || amountNum <= 0) {
    showError('请输入有效的金额')
    return
  }

  if (!formData.value.salary_record_id) {
    showError('请选择薪资记录')
    return
  }

  loading.value = true
  try {
    await createSalaryUsage({
      salary_record_id: formData.value.salary_record_id,
      usage_type: formData.value.usage_type as UsageType,
      amount: amountNum,
      usage_date: formData.value.usage_date,
      description: formData.value.description || undefined,
    })

    showSuccess('保存成功')

    // Navigate back after delay
    setTimeout(() => {
      uni.navigateBack()
    }, 1000)
  } catch (error) {
    console.error('[salary-usage] Failed to create usage record:', error)
    showError('保存失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
.salary-usage-page {
  padding: 20rpx;
  background: #f5f5f5;
  min-height: 100vh;
}

.header {
  padding: 20rpx 0;
  text-align: center;

  .title {
    font-size: 36rpx;
    font-weight: bold;
    color: #333;
  }
}

.form {
  background: white;
  border-radius: 16rpx;
  padding: 20rpx;
}

.form-item {
  margin-bottom: 30rpx;

  .label {
    display: block;
    font-size: 28rpx;
    color: #333;
    margin-bottom: 16rpx;
    font-weight: 500;
  }
}

.type-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16rpx;

  .type-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 20rpx;
    border: 2rpx solid #e5e5e5;
    border-radius: 12rpx;
    transition: all 0.3s;

    &.active {
      border-color: #9b59b6;
      background: #f4e5f9;
    }

    .type-icon {
      font-size: 40rpx;
      margin-bottom: 8rpx;
    }

    .type-label {
      font-size: 24rpx;
      color: #666;
    }
  }
}

.amount-input,
.picker,
.desc-input {
  width: 100%;
  padding: 20rpx;
  border: 2rpx solid #e5e5e5;
  border-radius: 8rpx;
  font-size: 28rpx;
  background: #fff;
  color: #333;
}

.placeholder {
  color: #999;
}

.desc-input {
  height: 150rpx;
}

.submit-btn {
  width: 100%;
  padding: 28rpx;
  background: linear-gradient(135deg, #9b59b6, #8e44ad);
  color: white;
  border: none;
  border-radius: 12rpx;
  font-size: 32rpx;
  font-weight: bold;
  margin-top: 20rpx;

  &[disabled] {
    opacity: 0.6;
  }
}
</style>
