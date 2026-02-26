<template>
  <view class="expense-tracking-page">
    <view class="header">
      <text class="title">支出明细</text>
      <text class="subtitle">工资: ¥{{ salaryAmount }}</text>
    </view>

    <!-- 已保存的支出列表 -->
    <view v-if="savedExpenses.length > 0" class="saved-expenses">
      <view class="section-title">已保存的支出</view>
      <view class="summary-card">
        <view class="summary-item">
          <text class="label">已支出</text>
          <text class="value highlight">¥{{ totalSavedAmount }}</text>
        </view>
        <view class="summary-item">
          <text class="label">剩余</text>
          <text class="value">¥{{ remainingAmount }}</text>
        </view>
      </view>

      <view class="expense-list-saved">
        <view v-for="item in savedExpenses" :key="item.id" class="saved-item">
          <view class="item-header">
            <text class="category">{{ item.category }}</text>
            <text class="amount">-¥{{ item.amount }}</text>
          </view>
          <view class="item-meta">
            <text class="date">{{ formatDate(item.expenseDate) }}</text>
            <text v-if="item.note" class="note">{{ item.note }}</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 新增支出表单 -->
    <view class="new-expense-section">
      <view class="section-title">新增支出</view>

      <view class="expense-list">
        <view v-for="(item, index) in expenses" :key="index" class="expense-item">
          <view class="item-header">
            <picker
              :range="categories"
              :value="item.categoryIndex"
              @change="onCategoryChange($event, index)"
            >
              <view class="category-picker">
                <text>{{ categories[item.categoryIndex] }}</text>
                <text class="arrow">▼</text>
              </view>
            </picker>
            <input
              v-model="item.amount"
              class="amount-input"
              type="digit"
              placeholder="金额"
              @input="calculateTotal"
            />
          </view>
          <input v-model="item.note" class="note-input" placeholder="备注（可选）" />
          <view class="date-picker">
            <uni-datetime-picker v-model="item.expenseDate" type="date" @change="calculateTotal">
              <view class="date-display">
                <text>{{ formatDate(item.expenseDate) }}</text>
              </view>
            </uni-datetime-picker>
          </view>
          <view v-if="expenses.length > 1" class="delete-btn" @tap="removeExpense(index)">
            <text>删除</text>
          </view>
        </view>
      </view>

      <!-- 添加按钮 -->
      <view class="add-btn" @tap="addExpense">
        <text>+ 添加支出</text>
      </view>

      <!-- 本次统计信息 -->
      <view class="summary">
        <view class="summary-item">
          <text class="label">本次总计</text>
          <text class="value">¥{{ totalAmount }}</text>
        </view>
        <view class="summary-item">
          <text class="label">笔数</text>
          <text class="value">{{ expenses.length }}笔</text>
        </view>
      </view>

      <!-- 保存按钮 -->
      <view class="footer">
        <button class="save-btn" :disabled="!isValid || expenses.length === 0" @tap="handleSave">
          保存记录
        </button>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import { createExpenses, getExpenses } from '@/api/expense'
import { getSalary } from '@/api/salary'

const salaryRecordId = ref('')
const salaryAmount = ref(0)
const loading = ref(false)
const savedExpenses = ref([])

const categories = ref([
  '🏠居住',
  '🍚饮食',
  '🚌交通',
  '🛍️购物',
  '🏥医疗',
  '🎮娱乐',
  '📚学习',
  '📱通讯',
  '🎁礼物',
  '💳还贷',
  '📦其他',
])

const expenses = ref([
  {
    categoryIndex: 0,
    amount: '',
    note: '',
    expenseDate: new Date().toISOString().split('T')[0],
  },
])

// 本次新增支出的总计
const totalAmount = computed(() => {
  return expenses.value
    .reduce((sum, item) => {
      return sum + (parseFloat(item.amount) || 0)
    }, 0)
    .toFixed(2)
})

// 已保存支出的总计
const totalSavedAmount = computed(() => {
  return savedExpenses.value
    .reduce((sum, item) => {
      return sum + parseFloat(item.amount || 0)
    }, 0)
    .toFixed(2)
})

// 剩余金额
const remainingAmount = computed(() => {
  const total = parseFloat(totalSavedAmount.value) || 0
  const remaining = salaryAmount.value - total
  return Math.max(0, remaining).toFixed(2)
})

const isValid = computed(() => {
  return expenses.value.every(item => item.amount && parseFloat(item.amount) > 0)
})

onLoad(async options => {
  console.log('[expense-tracking] onLoad options:', options)

  if (!options.recordId) {
    uni.showModal({
      title: '提示',
      content: '缺少工资记录ID，请重新操作',
      showCancel: false,
      success: () => {
        uni.navigateBack()
      },
    })
    return
  }

  salaryRecordId.value = options.recordId

  // 从后端API获取工资记录详情
  try {
    const record = await getSalary(options.recordId)
    salaryAmount.value = record.amount || 0
    console.log('[expense-tracking] salaryAmount:', salaryAmount.value)
  } catch (error) {
    console.error('[expense-tracking] Failed to load salary record:', error)
    uni.showToast({
      title: '获取工资记录失败',
      icon: 'none',
    })
  }

  console.log('[expense-tracking] recordId:', salaryRecordId.value)
})

// 每次显示页面时加载已保存的支出
onShow(() => {
  if (salaryRecordId.value) {
    fetchSavedExpenses()
  }
})

// 加载已保存的支出记录
async function fetchSavedExpenses() {
  if (!salaryRecordId.value) return

  try {
    loading.value = true
    const res = await getExpenses(salaryRecordId.value)
    if (res.records) {
      savedExpenses.value = res.records
    }
  } catch (error) {
    console.error('Failed to fetch expenses:', error)
  } finally {
    loading.value = false
  }
}

function addExpense() {
  expenses.value.push({
    categoryIndex: 0,
    amount: '',
    note: '',
    expenseDate: new Date().toISOString().split('T')[0],
  })
}

function removeExpense(index) {
  expenses.value.splice(index, 1)
  calculateTotal()
}

function onCategoryChange(e, index) {
  // 使用 Object.assign 触发响应式更新
  const updated = { ...expenses.value[index], categoryIndex: e.detail.value }
  expenses.value[index] = updated
}

function formatDate(dateStr) {
  if (!dateStr) return '选择日期'
  const date = new Date(dateStr)
  return `${date.getMonth() + 1}月${date.getDate()}日`
}

function calculateTotal() {
  // Trigger computed recalculation
}

async function handleSave() {
  if (!isValid.value) {
    uni.showToast({ title: '请填写所有金额', icon: 'none' })
    return
  }

  if (!salaryRecordId.value) {
    uni.showToast({ title: '缺少工资记录ID', icon: 'none' })
    return
  }

  const records = expenses.value.map(item => ({
    expenseDate: item.expenseDate,
    category: categories.value[item.categoryIndex],
    subcategory: undefined,
    amount: parseFloat(item.amount),
    note: item.note || undefined,
  }))

  console.log('[expense-tracking] Saving expenses for recordId:', salaryRecordId.value)
  console.log('[expense-tracking] Records:', records)

  try {
    uni.showLoading({ title: '保存中...' })

    await createExpenses(salaryRecordId.value, { expenses: records })

    uni.hideLoading()
    uni.showToast({ title: '保存成功', icon: 'success' })

    // 清空表单
    expenses.value = [
      {
        categoryIndex: 0,
        amount: '',
        note: '',
        expenseDate: new Date().toISOString().split('T')[0],
      },
    ]

    // 重新加载已保存的支出
    await fetchSavedExpenses()
  } catch (error) {
    uni.hideLoading()
    console.error('Failed to save expenses:', error)
    uni.showToast({
      title: error.message || '保存失败，请重试',
      icon: 'none',
    })
  }
}
</script>

<style lang="scss" scoped>
.expense-tracking-page {
  min-height: 100vh;
  background: var(--bg-base);
  padding: $spacing-md;
  padding-bottom: 150rpx;
}

.header {
  text-align: center;
  padding: $spacing-lg 0;
  margin-bottom: $spacing-md;

  .title {
    display: block;
    font-size: $font-size-2xl;
    font-weight: $font-weight-bold;
    margin-bottom: $spacing-xs;
    color: var(--text-primary);
  }

  .subtitle {
    font-size: $font-size-sm;
    color: var(--text-secondary);
  }
}

.section-title {
  font-size: $font-size-base;
  font-weight: $font-weight-bold;
  color: var(--text-primary);
  margin: $spacing-lg 0 $spacing-md;
  padding-left: $spacing-xs;
  border-left: 6rpx solid $brand-primary;
}

.saved-expenses {
  margin-bottom: $spacing-2xl;
}

.summary-card {
  background: $gradient-brand;
  border-radius: $radius-lg;
  padding: $spacing-lg;
  margin-bottom: $spacing-md;
  display: flex;
  justify-content: space-around;
  color: white;

  .summary-item {
    text-align: center;

    .label {
      display: block;
      font-size: $font-size-sm;
      color: rgba(255, 255, 255, 0.8);
      margin-bottom: $spacing-xs;
    }

    .value {
      display: block;
      font-size: $font-size-2xl;
      font-weight: $font-weight-bold;

      &.highlight {
        font-size: $font-size-3xl;
      }
    }
  }
}

.expense-list-saved {
  .saved-item {
    @include glass-card();
    padding: $spacing-lg;
    margin-bottom: $spacing-sm;

    .item-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: $spacing-xs;

      .category {
        font-size: $font-size-base;
        font-weight: $font-weight-bold;
        color: var(--text-primary);
      }

      .amount {
        font-size: $font-size-lg;
        font-weight: $font-weight-bold;
        color: $semantic-error;
      }
    }

    .item-meta {
      display: flex;
      gap: $spacing-md;
      font-size: $font-size-sm;
      color: var(--text-tertiary);

      .date {
        color: var(--text-secondary);
      }

      .note {
        flex: 1;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
    }
  }
}

.new-expense-section {
  @include glass-card();
  padding: $spacing-lg;
  margin-bottom: $spacing-md;
}

.expense-list {
  .expense-item {
    background: var(--bg-glass-subtle);
    border-radius: $radius-md;
    padding: $spacing-lg;
    margin-bottom: $spacing-md;

    .item-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: $spacing-sm;

      .category-picker {
        display: flex;
        align-items: center;
        gap: $spacing-xs;
        padding: $spacing-xs $spacing-md;
        background: var(--bg-glass-standard);
        border-radius: $radius-xl;
        font-size: $font-size-base;
        color: var(--text-primary);
        border: 1rpx solid var(--border-subtle);

        .arrow {
          font-size: $font-size-xs;
          color: var(--text-tertiary);
        }
      }

      .amount-input {
        flex: 1;
        text-align: right;
        font-size: $font-size-lg;
        font-weight: $font-weight-bold;
        color: $brand-primary;
      }
    }

    .note-input {
      width: 100%;
      padding: $spacing-sm;
      background: var(--bg-glass-standard);
      border-radius: $radius-md;
      font-size: $font-size-base;
      margin-bottom: $spacing-sm;
      color: var(--text-primary);
      border: 1rpx solid var(--border-subtle);
    }

    .date-picker {
      .date-display {
        padding: $spacing-xs;
        background: var(--bg-glass-standard);
        border-radius: $radius-md;
        text-align: center;
        font-size: $font-size-sm;
        color: var(--text-secondary);
        border: 1rpx solid var(--border-subtle);
      }
    }

    .delete-btn {
      text-align: center;
      padding: $spacing-sm;
      margin-top: $spacing-xs;
      font-size: $font-size-sm;
      color: $semantic-error;
    }
  }
}

.add-btn {
  text-align: center;
  padding: $spacing-lg;
  background: var(--bg-glass-standard);
  border-radius: $radius-md;
  margin: $spacing-md 0;
  font-size: $font-size-base;
  color: $brand-primary;
  border: 1rpx solid var(--border-subtle);
}

.summary {
  display: flex;
  justify-content: space-around;
  padding: $spacing-md 0;
  border-top: 1rpx solid var(--border-subtle);

  .summary-item {
    text-align: center;

    .label {
      display: block;
      font-size: $font-size-sm;
      color: var(--text-tertiary);
      margin-bottom: $spacing-xs;
    }

    .value {
      display: block;
      font-size: $font-size-lg;
      font-weight: $font-weight-bold;
      color: $brand-primary;
    }
  }
}

.footer {
  padding: $spacing-md 0;

  .save-btn {
    width: 100%;
    background: $gradient-brand;
    color: white;
    border: none;
    border-radius: $radius-xl;
    padding: $spacing-lg;
    font-size: $font-size-lg;

    &[disabled] {
      background: var(--text-disabled);
    }
  }
}
</style>
