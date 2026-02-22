<template>
  <view class="expense-tracking-page">
    <view class="header">
      <text class="title">每月支出记录</text>
      <text class="subtitle">记录你的每一笔花销</text>
    </view>

    <!-- 支出列表 -->
    <view class="expense-list">
      <view class="expense-item" v-for="(item, index) in expenses" :key="index">
        <view class="item-header">
          <picker :range="categories" :value="item.categoryIndex" @change="onCategoryChange($event, index)">
            <view class="category-picker">
              <text>{{ categories[item.categoryIndex] }}</text>
              <text class="arrow">▼</text>
            </view>
          </picker>
          <input
            class="amount-input"
            type="digit"
            v-model="item.amount"
            placeholder="金额"
            @input="calculateTotal"
          />
        </view>
        <input
          class="note-input"
          v-model="item.note"
          placeholder="备注（可选）"
        />
        <view class="date-picker">
          <uni-datetime-picker type="date" v-model="item.expenseDate" @change="calculateTotal">
            <view class="date-display">
              <text>{{ formatDate(item.expenseDate) }}</text>
            </view>
          </uni-datetime-picker>
        </view>
        <view class="delete-btn" v-if="expenses.length > 1" @tap="removeExpense(index)">
          <text>删除</text>
        </view>
      </view>
    </view>

    <!-- 添加按钮 -->
    <view class="add-btn" @tap="addExpense">
      <text>+ 添加支出</text>
    </view>

    <!-- 统计信息 -->
    <view class="summary">
      <view class="summary-item">
        <text class="label">总计</text>
        <text class="value">¥{{ totalAmount }}</text>
      </view>
      <view class="summary-item">
        <text class="label">笔数</text>
        <text class="value">{{ expenses.length }}笔</text>
      </view>
    </view>

    <!-- 保存按钮 -->
    <view class="footer">
      <button class="save-btn" @tap="handleSave" :disabled="!isValid">保存记录</button>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { onLoad } from '@dcloudio/uni-app'

const salaryRecordId = ref('')
const salaryAmount = ref(0)

const categories = ref([
  '🏠居住', '🍚饮食', '🚌交通', '🛍️购物', '🏥医疗',
  '🎮娱乐', '📚学习', '📱通讯', '🎁礼物', '💳还贷', '📦其他'
])

const expenses = ref([
  {
    categoryIndex: 0,
    amount: '',
    note: '',
    expenseDate: new Date().toISOString().split('T')[0]
  }
])

const totalAmount = computed(() => {
  return expenses.value.reduce((sum, item) => {
    return sum + (parseFloat(item.amount) || 0)
  }, 0).toFixed(2)
})

const isValid = computed(() => {
  return expenses.value.every(item => item.amount && parseFloat(item.amount) > 0)
})

onLoad((options) => {
  if (options.recordId) {
    salaryRecordId.value = options.recordId
  }
  if (options.amount) {
    salaryAmount.value = parseFloat(options.amount)
  }
})

function addExpense() {
  expenses.value.push({
    categoryIndex: 0,
    amount: '',
    note: '',
    expenseDate: new Date().toISOString().split('T')[0]
  })
}

function removeExpense(index) {
  expenses.value.splice(index, 1)
  calculateTotal()
}

function onCategoryChange(e, index) {
  expenses.value[index].categoryIndex = e.detail.value
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

  const records = expenses.value.map(item => ({
    expenseDate: item.expenseDate,
    category: categories.value[item.categoryIndex],
    subcategory: null,
    amount: parseFloat(item.amount),
    note: item.note || null
  }))

  try {
    uni.showLoading({ title: '保存中...' })

    const token = uni.getStorageSync('token')
    const res = await uni.request({
      url: 'https://api.example.com/api/v1/salary/' + salaryRecordId.value + '/expenses',
      method: 'POST',
      header: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      data: { expenses: records }
    })

    uni.hideLoading()

    if (res.data.code === 0) {
      uni.showToast({ title: '保存成功', icon: 'success' })
      setTimeout(() => {
        uni.navigateBack()
      }, 1500)
    } else {
      uni.showToast({ title: res.data.message || '保存失败', icon: 'none' })
    }
  } catch (error) {
    uni.hideLoading()
    uni.showToast({ title: '网络错误', icon: 'none' })
    console.error(error)
  }
}
</script>

<style lang="scss" scoped>
.expense-tracking-page {
  min-height: 100vh;
  background: #f5f5f5;
  padding: 20rpx;
}

.header {
  text-align: center;
  padding: 40rpx 0;
  background: white;
  border-radius: 20rpx;
  margin-bottom: 20rpx;

  .title {
    display: block;
    font-size: 36rpx;
    font-weight: bold;
    margin-bottom: 10rpx;
  }

  .subtitle {
    font-size: 24rpx;
    color: #999;
  }
}

.expense-list {
  .expense-item {
    background: white;
    border-radius: 20rpx;
    padding: 20rpx;
    margin-bottom: 20rpx;

    .item-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 15rpx;

      .category-picker {
        display: flex;
        align-items: center;
        padding: 10rpx 20rpx;
        background: #f0f0f0;
        border-radius: 10rpx;

        .arrow {
          margin-left: 10rpx;
          font-size: 20rpx;
          color: #666;
        }
      }

      .amount-input {
        width: 200rpx;
        text-align: right;
        font-size: 32rpx;
        font-weight: bold;
      }
    }

    .note-input {
      width: 100%;
      padding: 10rpx;
      border: 1rpx solid #e0e0e0;
      border-radius: 10rpx;
      margin-bottom: 15rpx;
    }

    .date-picker {
      .date-display {
        padding: 10rpx;
        background: #f0f0f0;
        border-radius: 10rpx;
        text-align: center;
      }
    }

    .delete-btn {
      margin-top: 15rpx;
      text-align: center;
      padding: 10rpx;
      color: #ff4d4f;
      border: 1rpx solid #ff4d4f;
      border-radius: 10rpx;
    }
  }
}

.add-btn {
  background: white;
  border-radius: 20rpx;
  padding: 30rpx;
  text-align: center;
  margin-bottom: 20rpx;
  color: #1890ff;
  font-weight: bold;
}

.summary {
  display: flex;
  background: white;
  border-radius: 20rpx;
  padding: 30rpx;
  margin-bottom: 20rpx;

  .summary-item {
    flex: 1;
    text-align: center;

    .label {
      display: block;
      font-size: 24rpx;
      color: #999;
      margin-bottom: 10rpx;
    }

    .value {
      font-size: 32rpx;
      font-weight: bold;
      color: #1890ff;
    }
  }
}

.footer {
  padding: 20rpx 0;

  .save-btn {
    width: 100%;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 50rpx;
    padding: 30rpx;
    font-size: 32rpx;

    &[disabled] {
      background: #ccc;
    }
  }
}
</style>
