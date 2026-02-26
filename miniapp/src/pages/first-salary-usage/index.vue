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
import { listSalary } from '@/api/salary'
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

const formData = ref({
  usage_category: '',
  usage_subcategory: null,
  amount: '',
  salary_record_id: '',
  note: '',
})

const amountError = ref('')
const submitting = ref(false)
const salaryRecords = ref<any[]>([])

const store = useFirstSalaryUsageStore()
const myRecords = computed(() => store.records)

// 用途分类选项
const usageCategories: Array<{ value; label: string; icon: string }> = [
  { value: '存起来', label: '存起来', icon: '💰' },
  { value: '交家里', label: '交家里', icon: '🏠' },
  { value: '买东西', label: '买东西', icon: '🛍️' },
  { value: '请客吃饭', label: '请客吃饭', icon: '🍽️' },
  { value: '旅游', label: '旅游', icon: '✈️' },
  { value: '学习', label: '学习', icon: '📚' },
  { value: '其他', label: '其他', icon: '📝' },
]

// 子分类映射
const subcategoryMap: Record<UsageCategory, Array<{ value; label: string }>> = {
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

const selectCategory = (category) => {
  formData.value.usage_category = category
  formData.value.usage_subcategory = null // 重置子分类
}

const selectSubcategory = (subcategory = null) => {
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
  background: $gradient-brand;
  padding: $spacing-lg $spacing-md;
  padding-bottom: 200rpx;
}

.header {
  text-align: center;
  margin-bottom: $spacing-xl;
  padding-top: $spacing-lg;
}

.title {
  display: block;
  font-size: $font-size-2xl;
  font-weight: $font-weight-bold;
  color: #ffffff;
  margin-bottom: $spacing-sm;
}

.subtitle {
  display: block;
  font-size: $font-size-sm;
  color: rgba(255, 255, 255, 0.8);
}

.form-section {
  @include glass-card();
  padding: $spacing-lg;
  margin-bottom: $spacing-md;
}

.section-title {
  display: flex;
  align-items: center;
  margin-bottom: $spacing-md;
}

.title-text {
  font-size: $font-size-lg;
  font-weight: $font-weight-semibold;
  color: var(--text-primary);
  margin-right: $spacing-xs;
}

.required {
  color: $semantic-error;
  font-size: $font-size-base;
}

.optional {
  font-size: $font-size-xs;
  color: var(--text-tertiary);
}

// 分类网格
.category-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: $spacing-sm;
}

.category-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: $spacing-md $spacing-sm;
  border: 2rpx solid var(--border-subtle);
  border-radius: $radius-md;
  transition: all 0.3s;
}

.category-item.active {
  border-color: $brand-primary;
  background: var(--bg-glass-subtle);
}

.category-icon {
  font-size: $font-size-2xl;
  margin-bottom: $spacing-xs;
}

.category-label {
  font-size: $font-size-xs;
  color: var(--text-primary);
}

// 子分类网格
.subcategory-grid {
  display: flex;
  flex-wrap: wrap;
  gap: $spacing-sm;
}

.subcategory-item {
  padding: $spacing-sm $spacing-md;
  border: 2rpx solid var(--border-subtle);
  border-radius: $radius-xl;
  font-size: $font-size-sm;
  color: var(--text-secondary);
  transition: all 0.3s;
}

.subcategory-item.active {
  border-color: $brand-primary;
  background: $brand-primary;
  color: #ffffff;
}

// 金额输入
.amount-input-wrapper {
  display: flex;
  align-items: center;
  padding: $spacing-md;
  background: var(--bg-glass-subtle);
  border-radius: $radius-md;
}

.currency-symbol {
  font-size: $font-size-lg;
  font-weight: $font-weight-bold;
  color: var(--text-primary);
  margin-right: $spacing-sm;
}

.amount-input {
  flex: 1;
  font-size: $font-size-lg;
  font-weight: $font-weight-bold;
  color: var(--text-primary);
}

.placeholder {
  color: var(--text-tertiary);
}

.error-text {
  display: block;
  margin-top: $spacing-sm;
  font-size: $font-size-xs;
  color: $semantic-error;
}

// Picker
.picker {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: $spacing-md;
  background: var(--bg-glass-subtle);
  border-radius: $radius-md;
}

.picker-text {
  font-size: $font-size-base;
  color: var(--text-primary);
}

.picker-text.placeholder {
  color: var(--text-tertiary);
}

.picker-arrow {
  font-size: $font-size-xl;
  color: var(--text-tertiary);
}

// 备注输入
.note-input {
  width: 100%;
  min-height: 160rpx;
  padding: $spacing-md;
  background: var(--bg-glass-subtle);
  border-radius: $radius-md;
  font-size: $font-size-base;
  line-height: 1.6;
  color: var(--text-primary);
}

.char-count {
  text-align: right;
  margin-top: $spacing-xs;
  font-size: $font-size-xs;
  color: var(--text-tertiary);
}

// 总金额显示
.total-section {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: $spacing-lg;
  background: var(--bg-glass-standard);
  border-radius: $radius-lg;
  margin-bottom: $spacing-md;
}

.total-label {
  font-size: $font-size-base;
  color: var(--text-secondary);
  margin-right: $spacing-sm;
}

.total-amount {
  font-size: $font-size-xl;
  font-weight: $font-weight-bold;
  background: $gradient-brand;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

// 提交按钮
.submit-section {
  margin-bottom: $spacing-lg;
}

.submit-btn {
  width: 100%;
  height: 96rpx;
  background: $gradient-brand;
  border-radius: $radius-xl;
  font-size: $font-size-lg;
  font-weight: $font-weight-semibold;
  color: #ffffff;
  border: none;
}

.submit-btn[disabled] {
  opacity: 0.5;
}

// 记录列表
.records-section {
  @include glass-card();
  padding: $spacing-lg;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: $spacing-md;
}

.section-title-text {
  font-size: $font-size-lg;
  font-weight: $font-weight-semibold;
  color: var(--text-primary);
}

.record-count {
  font-size: $font-size-xs;
  color: var(--text-tertiary);
}

.records-list {
  display: flex;
  flex-direction: column;
  gap: $spacing-sm;
}

.record-item {
  padding: $spacing-md;
  background: var(--bg-glass-subtle);
  border-radius: $radius-md;
}

.record-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: $spacing-xs;
}

.record-category {
  font-size: $font-size-base;
  font-weight: $font-weight-semibold;
  color: var(--text-primary);
}

.record-amount {
  font-size: $font-size-lg;
  font-weight: $font-weight-bold;
  color: $brand-primary;
}

.record-subcategory {
  margin-bottom: $spacing-xs;
  font-size: $font-size-xs;
  color: var(--text-secondary);
}

.record-note {
  margin-bottom: $spacing-xs;
  font-size: $font-size-sm;
  color: var(--text-tertiary);
  line-height: 1.5;
}

.record-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: $spacing-sm;
  border-top: 1rpx solid var(--border-subtle);
}

.record-date {
  font-size: $font-size-xs;
  color: var(--text-tertiary);
}

.record-delete {
  font-size: $font-size-xs;
  color: $semantic-error;
}
</style>
