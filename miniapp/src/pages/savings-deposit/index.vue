<template>
  <view class="savings-deposit-page">
    <view class="header">
      <text class="title">💰 存入资金</text>
    </view>

    <view v-if="loading" class="loading">
      <text>加载中...</text>
    </view>

    <view v-else-if="goal" class="goal-info">
      <view class="goal-title">{{ goal.title }}</view>
      <view class="goal-progress">
        <view class="progress-label">
          <text>当前：¥{{ goal.currentAmount }}</text>
          <text>目标：¥{{ goal.targetAmount }}</text>
        </view>
        <view class="progress-bar">
          <view class="progress-fill" :style="{ width: goal.progressPercentage + '%' }"></view>
        </view>
        <text class="progress-percent">{{ goal.progressPercentage }}%</text>
      </view>
    </view>

    <view class="form">
      <view class="form-item">
        <text class="label">存款金额 (¥) *</text>
        <input
          v-model="amount"
          class="amount-input"
          type="digit"
          placeholder="输入存入金额"
          focus
        />
      </view>

      <view class="quick-amounts">
        <view v-for="val in quickValues" :key="val" class="quick-btn" @tap="setAmount(val)">
          <text>¥{{ val }}</text>
        </view>
      </view>

      <view class="form-item">
        <text class="label">备注</text>
        <textarea v-model="note" class="textarea" placeholder="记录这次存款（可选）" />
      </view>
    </view>

    <view v-if="amount && parseFloat(amount) > 0" class="preview">
      <text class="preview-label">存入后余额</text>
      <text class="preview-value">¥{{ projectedAmount }}</text>
      <text class="preview-percent">{{ projectedPercent }}%</text>
    </view>

    <view class="footer">
      <button
        class="submit-btn"
        :disabled="!amount || parseFloat(amount) <= 0"
        @tap="handleDeposit"
      >
        确认存入
      </button>
    </view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { getSavingsGoal, depositToGoal } from '@/api/savings'
import { transformSavingsGoal, safeNumber } from '@/utils/transform'

const goalId = ref('')
const goal = ref(null)
const amount = ref('')
const note = ref('')
const loading = ref(false)

const quickValues = [100, 500, 1000, 2000, 5000]

const projectedAmount = computed(() => {
  if (!goal.value || !amount.value) return '0.00'
  const current = safeNumber(goal.value.currentAmount, 0)
  const deposit = safeNumber(amount.value, 0)
  return (current + deposit).toFixed(2)
})

const projectedPercent = computed(() => {
  if (!goal.value) return 0
  const percent = (
    (parseFloat(projectedAmount.value) / safeNumber(goal.value.targetAmount, 1)) *
    100
  ).toFixed(1)
  return Math.min(percent, 100)
})

onLoad(options => {
  if (options.id) {
    goalId.value = options.id
    fetchGoal()
  }
})

async function fetchGoal() {
  try {
    loading.value = true
    const data = await getSavingsGoal(goalId.value)
    goal.value = transformSavingsGoal(data)
  } catch (error) {
    console.error('Failed to fetch savings goal:', error)
    uni.showToast({
      title: '加载失败，请重试',
      icon: 'none',
    })
  } finally {
    loading.value = false
  }
}

function setAmount(val) {
  amount.value = val.toString()
}

async function handleDeposit() {
  if (!amount.value || parseFloat(amount.value) <= 0) {
    uni.showToast({ title: '请输入有效金额', icon: 'none' })
    return
  }

  try {
    uni.showLoading({ title: '处理中...' })

    await depositToGoal(goalId.value, {
      amount: parseFloat(amount.value),
      note: note.value || undefined,
    })

    uni.hideLoading()
    uni.showToast({ title: '存款成功', icon: 'success' })
    setTimeout(() => {
      uni.navigateBack()
    }, 1500)
  } catch (error) {
    uni.hideLoading()
    console.error('Failed to deposit:', error)
    uni.showToast({
      title: error.message || '存款失败，请重试',
      icon: 'none',
    })
  }
}
</script>

<style lang="scss" scoped>
.savings-deposit-page {
  min-height: 100vh;
  background: #f5f5f5;
  padding: 20rpx;
}

.header {
  text-align: center;
  padding: 30rpx 0;

  .title {
    font-size: 36rpx;
    font-weight: bold;
  }
}

.loading {
  text-align: center;
  padding: 100rpx 0;
  color: #999;
}

.goal-info {
  background: white;
  border-radius: 20rpx;
  padding: 30rpx;
  margin-bottom: 20rpx;

  .goal-title {
    font-size: 32rpx;
    font-weight: bold;
    margin-bottom: 20rpx;
  }

  .goal-progress {
    .progress-label {
      display: flex;
      justify-content: space-between;
      margin-bottom: 10rpx;
      font-size: 24rpx;
      color: #666;
    }

    .progress-bar {
      height: 16rpx;
      background: #f0f0f0;
      border-radius: 8rpx;
      overflow: hidden;
      margin-bottom: 10rpx;

      .progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #1890ff 0%, #52c41a 100%);
        border-radius: 8rpx;
      }
    }

    .progress-percent {
      font-size: 24rpx;
      color: #1890ff;
      font-weight: bold;
    }
  }
}

.form {
  background: white;
  border-radius: 20rpx;
  padding: 30rpx;
  margin-bottom: 20rpx;

  .form-item {
    margin-bottom: 30rpx;

    &:last-child {
      margin-bottom: 0;
    }

    .label {
      display: block;
      font-size: 28rpx;
      color: #333;
      margin-bottom: 15rpx;
      font-weight: 500;
    }

    .amount-input {
      width: 100%;
      padding: 20rpx;
      border: 2rpx solid #1890ff;
      border-radius: 10rpx;
      font-size: 36rpx;
      font-weight: bold;
      text-align: center;
    }

    .textarea {
      width: 100%;
      padding: 20rpx;
      border: 1rpx solid #e0e0e0;
      border-radius: 10rpx;
      font-size: 28rpx;
      background: #fafafa;
      min-height: 120rpx;
    }
  }

  .quick-amounts {
    display: flex;
    flex-wrap: wrap;
    gap: 15rpx;
    margin-top: 15rpx;

    .quick-btn {
      padding: 15rpx 30rpx;
      background: #f0f0f0;
      border-radius: 50rpx;
      font-size: 24rpx;
    }
  }
}

.preview {
  background: linear-gradient(135deg, #ffeaa7 0%, #fdcb6e 100%);
  border-radius: 20rpx;
  padding: 30rpx;
  text-align: center;
  margin-bottom: 20rpx;

  .preview-label {
    display: block;
    font-size: 24rpx;
    opacity: 0.8;
    margin-bottom: 10rpx;
  }

  .preview-value {
    display: block;
    font-size: 48rpx;
    font-weight: bold;
    margin-bottom: 5rpx;
  }

  .preview-percent {
    font-size: 28rpx;
    font-weight: bold;
  }
}

.footer {
  padding: 20rpx 0;

  .submit-btn {
    width: 100%;
    background: linear-gradient(135deg, #52c41a 0%, #73d13d 100%);
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
