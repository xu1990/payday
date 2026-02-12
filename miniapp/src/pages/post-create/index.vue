<script setup lang="ts">
import { ref } from 'vue'
import { createPost, type PostCreateParams, type PostType } from '@/api/post'
import { VALIDATION_PATTERNS, VALIDATION_LIMITS, VALIDATION_ERRORS } from '@/constants/validation'

const typeOptions: { value: PostType; label: string }[] = [
  { value: 'complaint', label: '吐槽' },
  { value: 'sharing', label: '分享' },
  { value: 'question', label: '提问' },
]

const type = ref<PostType>('complaint')
const content = ref('')
const salary_range = ref('')
const industry = ref('')
const city = ref('')
const submitting = ref(false)
// 用于取消之前的请求
const submitAbortKey = ref('post-create-submit')

async function submit() {
  // 防止重复提交（如果有正在进行的请求，会自动取消）
  if (submitting.value) {
    // 取消之前的请求，开始新的请求
  }

  const text = content.value.trim()

  // 验证内容
  if (!text) {
    uni.showToast({ title: VALIDATION_ERRORS.CONTENT_REQUIRED, icon: 'none' })
    return
  }

  if (text.length > VALIDATION_LIMITS.MAX_CONTENT_LENGTH) {
    uni.showToast({ title: VALIDATION_ERRORS.CONTENT_TOO_LONG, icon: 'none' })
    return
  }

  // 验证工资区间（如果填写）
  const salary = salary_range.value.trim()
  if (salary) {
    if (salary.length > VALIDATION_LIMITS.MAX_SALARY_LENGTH) {
      uni.showToast({ title: VALIDATION_ERRORS.SALARY_TOO_LONG, icon: 'none' })
      return
    }

    if (!VALIDATION_PATTERNS.SALARY_RANGE.test(salary)) {
      uni.showToast({ title: VALIDATION_ERRORS.SALARY_FORMAT_INVALID, icon: 'none' })
      return
    }
  }

  // 验证行业（如果填写）
  const ind = industry.value.trim()
  if (ind && ind.length > VALIDATION_LIMITS.MAX_INDUSTRY_LENGTH) {
    uni.showToast({ title: `行业不能超过${VALIDATION_LIMITS.MAX_INDUSTRY_LENGTH}字`, icon: 'none' })
    return
  }

  // 验证城市（如果填写）
  const cit = city.value.trim()
  if (cit && cit.length > VALIDATION_LIMITS.MAX_CITY_LENGTH) {
    uni.showToast({ title: `城市不能超过${VALIDATION_LIMITS.MAX_CITY_LENGTH}字`, icon: 'none' })
    return
  }

  submitting.value = true
  try {
    const data: PostCreateParams = {
      content: text,
      type: type.value,
    }
    if (salary) data.salary_range = salary
    if (ind) data.industry = ind
    if (cit) data.city = cit

    // 使用abortKey来自动取消之前的请求
    await createPost(data, { abortKey: submitAbortKey.value })
    uni.showToast({ title: '发布成功' })
    setTimeout(() => uni.navigateBack(), 800)
  } catch (e: any) {
    // 只在不是被取消的情况下显示错误
    if (e?.message !== 'Request cancelled') {
      uni.showToast({ title: e?.message || '发布失败', icon: 'none' })
    }
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <view class="page">
    <view class="form">
      <view class="row">
        <text class="label">类型</text>
        <picker
          :value="typeOptions.findIndex((o) => o.value === type)"
          :range="typeOptions"
          range-key="label"
          @change="(e: any) => (type = typeOptions[e.detail.value].value)"
        >
          <view class="picker">{{ typeOptions.find((o) => o.value === type)?.label }}</view>
        </picker>
      </view>
      <view class="row">
        <text class="label">内容</text>
        <textarea
          v-model="content"
          class="input area"
          placeholder="说说你的想法…"
          maxlength="5000"
          :show-confirm-bar="false"
        />
      </view>
      <view class="row">
        <text class="label">工资区间</text>
        <input v-model="salary_range" class="input" placeholder="选填" />
      </view>
      <view class="row">
        <text class="label">行业</text>
        <input v-model="industry" class="input" placeholder="选填" />
      </view>
      <view class="row">
        <text class="label">城市</text>
        <input v-model="city" class="input" placeholder="选填" />
      </view>
    </view>
    <button
      class="btn"
      :disabled="submitting"
      @click="submit"
    >
      {{ submitting ? '发布中…' : '发布' }}
    </button>
  </view>
</template>

<style scoped>
.page {
  min-height: 100vh;
  padding: 24rpx;
  background: #f5f5f5;
}
.form {
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
  margin-bottom: 32rpx;
}
.row {
  margin-bottom: 24rpx;
}
.row:last-child {
  margin-bottom: 0;
}
.label {
  display: block;
  font-size: 28rpx;
  color: #333;
  margin-bottom: 12rpx;
}
.input {
  width: 100%;
  padding: 20rpx;
  font-size: 28rpx;
  border: 1rpx solid #eee;
  border-radius: 8rpx;
  box-sizing: border-box;
}
.area {
  min-height: 200rpx;
}
.picker {
  padding: 20rpx;
  border: 1rpx solid #eee;
  border-radius: 8rpx;
  font-size: 28rpx;
}
.btn {
  width: 100%;
  height: 88rpx;
  line-height: 88rpx;
  background: #07c160;
  color: #fff;
  border-radius: 12rpx;
  font-size: 32rpx;
}
</style>
