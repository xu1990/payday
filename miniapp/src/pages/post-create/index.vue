<script setup lang="ts">
import { ref } from 'vue'
import { createPost, type PostCreateParams, type PostType } from '@/api/post'

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

async function submit() {
  const text = content.value.trim()
  if (!text) {
    uni.showToast({ title: '请输入内容', icon: 'none' })
    return
  }
  submitting.value = true
  try {
    const data: PostCreateParams = {
      content: text,
      type: type.value,
    }
    if (salary_range.value.trim()) data.salary_range = salary_range.value.trim()
    if (industry.value.trim()) data.industry = industry.value.trim()
    if (city.value.trim()) data.city = city.value.trim()
    await createPost(data)
    uni.showToast({ title: '发布成功' })
    setTimeout(() => uni.navigateBack(), 800)
  } catch (e: any) {
    uni.showToast({ title: e?.message || '发布失败', icon: 'none' })
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
