<template>
  <view class="goal-create-page">
    <view class="header">
      <text class="title">创建存款目标</text>
    </view>

    <view class="form">
      <view class="form-item">
        <text class="label">目标名称 *</text>
        <input class="input" v-model="form.title" placeholder="如：买房基金、旅游基金" />
      </view>

      <view class="form-item">
        <text class="label">目标金额 (¥) *</text>
        <input class="input" type="digit" v-model="form.targetAmount" placeholder="输入目标金额" />
      </view>

      <view class="form-item">
        <text class="label">初始金额 (¥)</text>
        <input class="input" type="digit" v-model="form.currentAmount" placeholder="已有金额（可选）" />
      </view>

      <view class="form-item">
        <text class="label">目标类型</text>
        <picker :range="categories" @change="onCategoryChange">
          <view class="picker">
            <text>{{ form.category || '选择类型' }}</text>
            <text class="arrow">▼</text>
          </view>
        </picker>
      </view>

      <view class="form-item">
        <text class="label">开始日期</text>
        <uni-datetime-picker type="date" v-model="form.startDate">
          <view class="picker">
            <text>{{ form.startDate || '选择日期' }}</text>
          </view>
        </uni-datetime-picker>
      </view>

      <view class="form-item">
        <text class="label">目标截止日期</text>
        <uni-datetime-picker type="date" v-model="form.deadline">
          <view class="picker">
            <text>{{ form.deadline || '选择日期' }}</text>
          </view>
        </uni-datetime-picker>
      </view>

      <view class="form-item">
        <text class="label">备注</text>
        <textarea class="textarea" v-model="form.description" placeholder="描述你的目标（可选）" />
      </view>
    </view>

    <view class="footer">
      <button class="submit-btn" @tap="handleSubmit" :disabled="!isValid">创建目标</button>
    </view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { createSavingsGoal } from '@/api/savings'

const form = ref({
  title: '',
  targetAmount: '',
  currentAmount: '0',
  category: '',
  startDate: '',
  deadline: '',
  description: ''
})

const categories = ['买房', '买车', '旅游', '教育', '应急', '数码产品', '其他']

const isValid = computed(() => {
  return form.value.title && form.value.targetAmount && parseFloat(form.value.targetAmount) > 0
})

function onCategoryChange(e) {
  form.value.category = categories[e.detail.value]
}

async function handleSubmit() {
  if (!isValid.value) {
    uni.showToast({ title: '请填写必填项', icon: 'none' })
    return
  }

  try {
    uni.showLoading({ title: '创建中...' })

    const data = {
      title: form.value.title,
      targetAmount: parseFloat(form.value.targetAmount),
      currentAmount: parseFloat(form.value.currentAmount) || 0,
      category: form.value.category || undefined,
      startDate: form.value.startDate || undefined,
      deadline: form.value.deadline || undefined,
      description: form.value.description || undefined
    }

    await createSavingsGoal(data)

    uni.hideLoading()
    uni.showToast({ title: '创建成功', icon: 'success' })
    setTimeout(() => {
      uni.navigateBack()
    }, 1500)
  } catch (error) {
    uni.hideLoading()
    console.error('Failed to create savings goal:', error)
    uni.showToast({
      title: error.message || '创建失败，请重试',
      icon: 'none'
    })
  }
}
</script>

<style lang="scss" scoped>
.goal-create-page {
  min-height: 100vh;
  background: #f5f5f5;
  padding: 20rpx;
}

.header {
  text-align: center;
  padding: 40rpx 0;

  .title {
    font-size: 36rpx;
    font-weight: bold;
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

    .input, .textarea, .picker {
      width: 100%;
      padding: 20rpx;
      border: 1rpx solid #e0e0e0;
      border-radius: 10rpx;
      font-size: 28rpx;
      background: #fafafa;
    }

    .picker {
      display: flex;
      justify-content: space-between;
      align-items: center;

      .arrow {
        font-size: 20rpx;
        color: #999;
      }
    }

    .textarea {
      min-height: 150rpx;
    }
  }
}

.footer {
  padding: 20rpx 0;

  .submit-btn {
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
