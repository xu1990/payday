<template>
  <view class="first-salary-usage-page">
    <!-- Header -->
    <view class="header">
      <text class="title">第一笔工资用途</text>
      <text class="subtitle">记录你的第一笔工资怎么花的</text>
    </view>

    <!-- Usage Category Selection -->
    <view class="form-section">
      <view class="section-title">
        <text class="title-text">用途分类</text>
        <text class="required">*</text>
      </view>
      <view class="category-grid">
        <view
          v-for="category in usageCategories"
          :key="category.value"
          :class="['category-item', { active: formData.usage_category === category.value }]"
          @tap="selectCategory(category.value)"
        >
          <text class="category-icon">{{ category.icon }}</text>
          <text class="category-label">{{ category.label }}</text>
        </view>
      </view>
    </view>

    <!-- Subcategory Selection (Optional) -->
    <view v-if="formData.usage_category" class="form-section">
      <view class="section-title">
        <text class="title-text">子分类</text>
        <text class="optional">（可选）</text>
      </view>
      <view class="subcategory-grid">
        <view
          v-for="subcategory in currentSubcategories"
          :key="subcategory.value"
          :class="[
            'subcategory-item',
            { active: formData.usage_subcategory === subcategory.value },
          ]"
          @tap="selectSubcategory(subcategory.value)"
        >
          <text class="subcategory-label">{{ subcategory.label }}</text>
        </view>
        <view
          :class="['subcategory-item', { active: formData.usage_subcategory === null }]"
          @tap="selectSubcategory(null)"
        >
          <text class="subcategory-label">不填</text>
        </view>
      </view>
    </view>

    <!-- Amount Input -->
    <view class="form-section">
      <view class="section-title">
        <text class="title-text">金额</text>
        <text class="required">*</text>
      </view>
      <view class="amount-input-wrapper">
        <text class="currency-symbol">¥</text>
        <input
          v-model="formData.amount"
          class="amount-input"
          type="digit"
          placeholder="0.00"
          placeholder-class="placeholder"
          @input="onAmountInput"
        />
      </view>
      <text v-if="amountError" class="error-text">{{ amountError }}</text>
    </view>

    <!-- Salary Record Selection -->
    <view class="form-section">
      <view class="section-title">
        <text class="title-text">关联薪资记录</text>
        <text class="required">*</text>
      </view>
      <picker
        :range="salaryRecords"
        range-key="label"
        :value="selectedSalaryIndex"
        @change="onSalaryChange"
      >
        <view class="picker">
          <text :class="['picker-text', { placeholder: !selectedSalaryLabel }]">
            {{ selectedSalaryLabel || '请选择薪资记录' }}
          </text>
          <text class="picker-arrow">›</text>
        </view>
      </picker>
    </view>

    <!-- Note Input (Optional) -->
    <view class="form-section">
      <view class="section-title">
        <text class="title-text">备注</text>
        <text class="optional">（可选）</text>
      </view>
      <textarea
        v-model="formData.note"
        class="note-input"
        placeholder="写下你的想法或故事..."
        placeholder-class="placeholder"
        maxlength="500"
        :show-confirm-bar="false"
      />
      <view class="char-count">{{ formData.note.length }}/500</view>
    </view>

    <!-- Total Amount Display -->
    <view v-if="formData.amount" class="total-section">
      <text class="total-label">已填写金额：</text>
      <text class="total-amount">¥{{ formatAmount(formData.amount) }}</text>
    </view>

    <!-- Submit Button -->
    <view class="submit-section">
      <button
        class="submit-btn"
        :disabled="!isFormValid || submitting"
        :loading="submitting"
        @tap="handleSubmit"
      >
        {{ submitting ? '保存中...' : '保存记录' }}
      </button>
    </view>

    <!-- My Records List -->
    <view v-if="myRecords.length > 0" class="records-section">
      <view class="section-header">
        <text class="section-title-text">我的记录</text>
        <text class="record-count">{{ myRecords.length }}条</text>
      </view>
      <view class="records-list">
        <view
          v-for="record in myRecords"
          :key="record.id"
          class="record-item"
          @tap="viewRecordDetail(record)"
        >
          <view class="record-header">
            <text class="record-category">{{ record.usage_category }}</text>
            <text class="record-amount">¥{{ formatAmount(record.amount) }}</text>
          </view>
          <view v-if="record.usage_subcategory" class="record-subcategory">
            <text>{{ record.usage_subcategory }}</text>
          </view>
          <view v-if="record.note" class="record-note">
            <text>{{ record.note }}</text>
          </view>
          <view class="record-footer">
            <text class="record-date">{{ formatDate(record.created_at) }}</text>
            <text class="record-delete" @tap.stop="deleteRecord(record.id)">删除</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { listSalary, type SalaryRecord } from '@/api/salary'
import {
  createFirstSalaryUsage,
  deleteFirstSalaryUsage,
  type UsageCategory,
  type UsageSubcategory,
} from '@/api/first-salary-usage'
import { useFirstSalaryUsageStore } from '@/stores/first-salary-usage'
import { showSuccess, showError, showConfirm } from '@/utils/toast'

interface FormData {
  usage_category: UsageCategory | ''
  usage_subcategory: UsageSubcategory | null
  amount: string
  salary_record_id: string
  note: string
}

const formData = ref<FormData>({
  usage_category: '',
  usage_subcategory: null,
  amount: '',
  salary_record_id: '',
  note: '',
})

const amountError = ref('')
const submitting = ref(false)
const salaryRecords = ref<Array<{ id: string; label: string }>>([])

const store = useFirstSalaryUsageStore()
const myRecords = computed(() => store.records)

// 用途分类选项
const usageCategories: Array<{ value: UsageCategory; label: string; icon: string }> = [
  { value: '存起来', label: '存起来', icon: '💰' },
  { value: '交家里', label: '交家里', icon: '🏠' },
  { value: '买东西', label: '买东西', icon: '🛍️' },
  { value: '请客吃饭', label: '请客吃饭', icon: '🍽️' },
  { value: '旅游', label: '旅游', icon: '✈️' },
  { value: '学习', label: '学习', icon: '📚' },
  { value: '其他', label: '其他', icon: '📝' },
]

// 子分类映射
const subcategoryMap: Record<UsageCategory, Array<{ value: UsageSubcategory; label: string }>> = {
  存起来: [
    { value: '银行存款', label: '银行存款' },
    { value: '理财', label: '理财' },
    { value: '其他', label: '其他' },
  ],
  交家里: [
    { value: '给父母', label: '给父母' },
    { value: '还房贷', label: '还房贷' },
    { value: '其他', label: '其他' },
  ],
  买东西: [
    { value: '数码产品', label: '数码产品' },
    { value: '衣服鞋包', label: '衣服鞋包' },
    { value: '美妆护肤', label: '美妆护肤' },
    { value: '食品饮料', label: '食品饮料' },
    { value: '其他', label: '其他' },
  ],
  请客吃饭: [
    { value: '餐饮', label: '餐饮' },
    { value: '娱乐休闲', label: '娱乐休闲' },
    { value: '其他', label: '其他' },
  ],
  旅游: [
    { value: '旅游出行', label: '旅游出行' },
    { value: '其他', label: '其他' },
  ],
  学习: [
    { value: '教育培训', label: '教育培训' },
    { value: '其他', label: '其他' },
  ],
  其他: [{ value: '其他', label: '其他' }],
}

const currentSubcategories = computed(() => {
  if (!formData.value.usage_category) return []
  return subcategoryMap[formData.value.usage_category] || []
})

const selectedSalaryIndex = computed(() => {
  const index = salaryRecords.value.findIndex(r => r.id === formData.value.salary_record_id)
  return index >= 0 ? index : -1
})

const selectedSalaryLabel = computed(() => {
  if (!formData.value.salary_record_id) return ''
  const record = salaryRecords.value.find(r => r.id === formData.value.salary_record_id)
  return record?.label || ''
})

const isFormValid = computed(() => {
  return (
    formData.value.usage_category &&
    formData.value.amount &&
    parseFloat(formData.value.amount) > 0 &&
    formData.value.salary_record_id
  )
})

onMounted(() => {
  loadSalaryRecords()
  loadMyRecords()
})

const loadSalaryRecords = async () => {
  try {
    const records = await listSalary({ limit: 100 })
    salaryRecords.value = records
      .filter(r => r.amount > 0) // 只显示有金额的记录
      .map(record => ({
        id: record.id,
        label: `${record.payday_date} ¥${record.amount}`,
      }))
  } catch (error) {
    console.error('加载薪资记录失败:', error)
  }
}

const loadMyRecords = async () => {
  try {
    await store.fetchRecords({ limit: 50 })
  } catch (error) {
    console.error('加载记录失败:', error)
  }
}

const selectCategory = (category: UsageCategory) => {
  formData.value.usage_category = category
  formData.value.usage_subcategory = null // 重置子分类
}

const selectSubcategory = (subcategory: UsageSubcategory | null) => {
  formData.value.usage_subcategory = subcategory
}

const onAmountInput = () => {
  amountError.value = ''
  const amount = parseFloat(formData.value.amount)
  if (formData.value.amount && (isNaN(amount) || amount <= 0)) {
    amountError.value = '请输入有效的金额'
  }
}

const onSalaryChange = (e: any) => {
  const index = e.detail.value
  if (index >= 0 && index < salaryRecords.value.length) {
    formData.value.salary_record_id = salaryRecords.value[index].id
  }
}

const formatAmount = (amount: string | number) => {
  const num = typeof amount === 'string' ? parseFloat(amount) : amount
  return isNaN(num) ? '0.00' : num.toFixed(2)
}

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

const handleSubmit = async () => {
  if (!isFormValid.value) {
    showError('请填写所有必填项')
    return
  }

  const amount = parseFloat(formData.value.amount)
  if (isNaN(amount) || amount <= 0) {
    amountError.value = '请输入有效的金额'
    showError('请输入有效的金额')
    return
  }

  submitting.value = true
  try {
    await createFirstSalaryUsage({
      salary_record_id: formData.value.salary_record_id,
      usage_category: formData.value.usage_category as UsageCategory,
      usage_subcategory: formData.value.usage_subcategory,
      amount: amount,
      note: formData.value.note || null,
    })

    showSuccess('保存成功！')

    // 重置表单
    formData.value = {
      usage_category: '',
      usage_subcategory: null,
      amount: '',
      salary_record_id: '',
      note: '',
    }

    // 重新加载记录列表
    await loadMyRecords()
  } catch (error: any) {
    console.error('保存失败:', error)
    showError(error.message || '保存失败，请重试')
  } finally {
    submitting.value = false
  }
}

const viewRecordDetail = (record: any) => {
  // 可以跳转到详情页或弹出详情
  console.log('查看详情:', record)
}

const deleteRecord = async (recordId: string) => {
  showConfirm('确定要删除这条记录吗？', async () => {
    try {
      await deleteFirstSalaryUsage(recordId)
      showSuccess('删除成功')
      await loadMyRecords()
    } catch (error: any) {
      showError(error.message || '删除失败')
    }
  })
}
</script>

<style lang="scss" scoped>
.first-salary-usage-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 40rpx 30rpx;
  padding-bottom: 200rpx;
}

.header {
  text-align: center;
  margin-bottom: 60rpx;
  padding-top: 40rpx;
}

.title {
  display: block;
  font-size: 48rpx;
  font-weight: bold;
  color: #ffffff;
  margin-bottom: 16rpx;
}

.subtitle {
  display: block;
  font-size: 28rpx;
  color: rgba(255, 255, 255, 0.8);
}

.form-section {
  background: #ffffff;
  border-radius: 24rpx;
  padding: 32rpx;
  margin-bottom: 24rpx;
}

.section-title {
  display: flex;
  align-items: center;
  margin-bottom: 24rpx;
}

.title-text {
  font-size: 32rpx;
  font-weight: 600;
  color: #1a1a1a;
  margin-right: 8rpx;
}

.required {
  color: #ff4d4f;
  font-size: 28rpx;
}

.optional {
  font-size: 24rpx;
  color: #999999;
}

// 分类网格
.category-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16rpx;
}

.category-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24rpx 16rpx;
  border: 2rpx solid #e8e8e8;
  border-radius: 16rpx;
  transition: all 0.3s;
}

.category-item.active {
  border-color: #667eea;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
}

.category-icon {
  font-size: 48rpx;
  margin-bottom: 8rpx;
}

.category-label {
  font-size: 24rpx;
  color: #333333;
}

// 子分类网格
.subcategory-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
}

.subcategory-item {
  padding: 16rpx 24rpx;
  border: 2rpx solid #e8e8e8;
  border-radius: 40rpx;
  font-size: 26rpx;
  color: #666666;
  transition: all 0.3s;
}

.subcategory-item.active {
  border-color: #667eea;
  background: #667eea;
  color: #ffffff;
}

// 金额输入
.amount-input-wrapper {
  display: flex;
  align-items: center;
  padding: 24rpx;
  background: #f5f5f5;
  border-radius: 16rpx;
}

.currency-symbol {
  font-size: 36rpx;
  font-weight: bold;
  color: #333333;
  margin-right: 16rpx;
}

.amount-input {
  flex: 1;
  font-size: 36rpx;
  font-weight: bold;
  color: #333333;
}

.placeholder {
  color: #999999;
}

.error-text {
  display: block;
  margin-top: 16rpx;
  font-size: 24rpx;
  color: #ff4d4f;
}

// Picker
.picker {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24rpx;
  background: #f5f5f5;
  border-radius: 16rpx;
}

.picker-text {
  font-size: 30rpx;
  color: #333333;
}

.picker-text.placeholder {
  color: #999999;
}

.picker-arrow {
  font-size: 40rpx;
  color: #999999;
}

// 备注输入
.note-input {
  width: 100%;
  min-height: 160rpx;
  padding: 24rpx;
  background: #f5f5f5;
  border-radius: 16rpx;
  font-size: 28rpx;
  line-height: 1.6;
}

.char-count {
  text-align: right;
  margin-top: 12rpx;
  font-size: 24rpx;
  color: #999999;
}

// 总金额显示
.total-section {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32rpx;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 24rpx;
  margin-bottom: 24rpx;
}

.total-label {
  font-size: 28rpx;
  color: #666666;
  margin-right: 16rpx;
}

.total-amount {
  font-size: 40rpx;
  font-weight: bold;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

// 提交按钮
.submit-section {
  margin-bottom: 40rpx;
}

.submit-btn {
  width: 100%;
  height: 96rpx;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 48rpx;
  font-size: 32rpx;
  font-weight: 600;
  color: #ffffff;
  border: none;
}

.submit-btn[disabled] {
  opacity: 0.5;
}

// 记录列表
.records-section {
  background: #ffffff;
  border-radius: 24rpx;
  padding: 32rpx;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24rpx;
}

.section-title-text {
  font-size: 32rpx;
  font-weight: 600;
  color: #1a1a1a;
}

.record-count {
  font-size: 24rpx;
  color: #999999;
}

.records-list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.record-item {
  padding: 24rpx;
  background: #f8f8f8;
  border-radius: 16rpx;
}

.record-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12rpx;
}

.record-category {
  font-size: 28rpx;
  font-weight: 600;
  color: #333333;
}

.record-amount {
  font-size: 32rpx;
  font-weight: bold;
  color: #667eea;
}

.record-subcategory {
  margin-bottom: 8rpx;
  font-size: 24rpx;
  color: #666666;
}

.record-note {
  margin-bottom: 12rpx;
  font-size: 26rpx;
  color: #999999;
  line-height: 1.5;
}

.record-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 16rpx;
  border-top: 1rpx solid #e8e8e8;
}

.record-date {
  font-size: 22rpx;
  color: #999999;
}

.record-delete {
  font-size: 24rpx;
  color: #ff4d4f;
}
</style>
