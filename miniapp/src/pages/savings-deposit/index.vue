<template>
  <view class="savings-deposit-page">
    <view class="header">
      <text class="title">存款存入资金</text>
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
  background: var(--bg-base);
  padding: $spacing-md;
}

.header {
  text-align: center;
  padding: $spacing-lg 0;

  .title {
    font-size: $font-size-2xl;
    font-weight: $font-weight-bold;
    color: var(--text-primary);
  }
}

.loading {
  text-align: center;
  padding: $spacing-3xl 0;
  color: var(--text-tertiary);
}

.goal-info {
  @include glass-card();
  padding: $spacing-lg;
  margin-bottom: $spacing-md;

  .goal-title {
    font-size: $font-size-lg;
    font-weight: $font-weight-bold;
    margin-bottom: $spacing-md;
    color: var(--text-primary);
  }

  .goal-progress {
    .progress-label {
      display: flex;
      justify-content: space-between;
      margin-bottom: $spacing-xs;
      font-size: $font-size-sm;
      color: var(--text-secondary);
    }

    .progress-bar {
      height: 16rpx;
      background: var(--bg-glass-subtle);
      border-radius: $radius-sm;
      overflow: hidden;
      margin-bottom: $spacing-xs;

      .progress-fill {
        height: 100%;
        background: $gradient-brand;
        border-radius: $radius-sm;
      }
    }

    .progress-percent {
      font-size: $font-size-sm;
      color: $brand-primary;
      font-weight: $font-weight-bold;
    }
  }
}

.form {
  @include glass-card();
  padding: $spacing-lg;
  margin-bottom: $spacing-md;

  .form-item {
    margin-bottom: $spacing-lg;

    &:last-child {
      margin-bottom: 0;
    }

    .label {
      display: block;
      font-size: $font-size-base;
      color: var(--text-primary);
      margin-bottom: $spacing-sm;
      font-weight: $font-weight-medium;
    }

    .amount-input {
      width: 100%;
      padding: $spacing-md;
      border: 2rpx solid $brand-primary;
      border-radius: $radius-md;
      font-size: $font-size-2xl;
      font-weight: $font-weight-bold;
      text-align: center;
      background: var(--bg-glass-subtle);
      color: var(--text-primary);
    }

    .textarea {
      @include glass-input();
      width: 100%;
      min-height: 120rpx;
    }
  }

  .quick-amounts {
    display: flex;
    flex-wrap: wrap;
    gap: $spacing-sm;
    margin-top: $spacing-sm;

    .quick-btn {
      padding: $spacing-sm $spacing-lg;
      background: var(--bg-glass-subtle);
      border-radius: $radius-xl;
      font-size: $font-size-sm;
      color: var(--text-primary);
      border: 1rpx solid var(--border-subtle);
    }
  }
}

.preview {
  background: $gradient-brand;
  border-radius: $radius-lg;
  padding: $spacing-lg;
  text-align: center;
  margin-bottom: $spacing-md;
  color: white;

  .preview-label {
    display: block;
    font-size: $font-size-sm;
    opacity: 0.8;
    margin-bottom: $spacing-xs;
  }

  .preview-value {
    display: block;
    font-size: $font-size-3xl;
    font-weight: $font-weight-bold;
    margin-bottom: 5rpx;
  }

  .preview-percent {
    font-size: $font-size-base;
    font-weight: $font-weight-bold;
  }
}

.footer {
  padding: $spacing-md 0;

  .submit-btn {
    width: 100%;
    background: linear-gradient(135deg, $semantic-success 0%, lighten($semantic-success, 10%) 100%);
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
