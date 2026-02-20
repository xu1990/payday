<script setup lang="ts">
import { ref } from 'vue'
import { submitFeedback } from '@/api/user'
import { uploadImages } from '@/utils/upload'

const content = ref('')
const images = ref<string[]>([])
const contact = ref('')
const uploading = ref(false)

function chooseImage() {
  if (images.value.length >= 3) {
    uni.showToast({ title: '最多上传3张图片', icon: 'none' })
    return
  }

  uni.chooseImage({
    count: 3 - images.value.length,
    sizeType: ['compressed'],
    sourceType: ['album', 'camera'],
    success: (res) => {
      if (res.tempFilePaths) {
        images.value.push(...res.tempFilePaths)
      }
    }
  })
}

function removeImage(index: number) {
  images.value.splice(index, 1)
}

async function submit() {
  if (!content.value.trim()) {
    uni.showToast({ title: '请输入反馈内容', icon: 'none' })
    return
  }

  try {
    uni.showLoading({ title: '提交中...' })

    // Upload images to server if any
    let uploadedImages: string[] = []
    if (images.value.length > 0) {
      try {
        uploadedImages = await uploadImages(images.value)
      } catch (e) {
        // Image upload failed, but continue with text feedback
        console.warn('Image upload failed:', e)
        uni.hideLoading()
        uni.showModal({
          title: '图片上传失败',
          content: '图片上传失败，是否只提交文字反馈？',
          success: (res) => {
            if (res.confirm) {
              submitFeedbackWithImages([])
            }
          }
        })
        return
      }
    }

    await submitFeedbackWithImages(uploadedImages)
  } catch (e: any) {
    uni.hideLoading()
    uni.showToast({ title: e?.message || '提交失败', icon: 'none' })
  }
}

async function submitFeedbackWithImages(imgs: string[]) {
  try {
    await submitFeedback({
      content: content.value,
      images: imgs.length > 0 ? imgs : undefined,
      contact: contact.value || undefined
    })

    uni.hideLoading()
    uni.showToast({ title: '感谢您的反馈', icon: 'success' })

    setTimeout(() => {
      uni.navigateBack()
    }, 1500)
  } catch (e: any) {
    uni.hideLoading()
    uni.showToast({ title: e?.message || '提交失败', icon: 'none' })
  }
}
</script>

<template>
  <view class="feedback-page">
    <view class="section">
      <view class="section-title">反馈内容 *</view>
      <textarea
        class="textarea"
        v-model="content"
        placeholder="请详细描述您遇到的问题或建议..."
        maxlength="500"
      />
      <view class="char-count">{{ content.length }}/500</view>
    </view>

    <view class="section">
      <view class="section-title">添加图片（最多3张）</view>
      <view class="images">
        <view class="image-item" v-for="(img, idx) in images" :key="idx">
          <image :src="img" mode="aspectFill" />
          <view class="remove-btn" @click="removeImage(idx)">×</view>
        </view>
        <view class="add-image" v-if="images.length < 3" @click="chooseImage">
          <text class="plus">+</text>
          <text class="hint">添加图片</text>
        </view>
      </view>
    </view>

    <view class="section">
      <view class="section-title">联系方式（选填）</view>
      <input
        class="input"
        v-model="contact"
        placeholder="微信号、QQ或邮箱"
        maxlength="100"
      />
    </view>

    <button class="submit-btn" @click="submit">提交反馈</button>
  </view>
</template>

<style scoped lang="scss">
.feedback-page {
  padding: 24rpx;
  background: #f5f5f5;
  min-height: 100vh;
}

.section {
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
  margin-bottom: 24rpx;
}

.section-title {
  font-size: 28rpx;
  color: #333;
  margin-bottom: 16rpx;
  font-weight: 600;
}

.textarea {
  width: 100%;
  min-height: 200rpx;
  padding: 16rpx;
  border: 1rpx solid #e0e0e0;
  border-radius: 8rpx;
  font-size: 28rpx;
}

.char-count {
  text-align: right;
  font-size: 24rpx;
  color: #999;
  margin-top: 8rpx;
}

.images {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
}

.image-item {
  position: relative;
  width: 160rpx;
  height: 160rpx;
}

.image-item image {
  width: 100%;
  height: 100%;
  border-radius: 8rpx;
}

.remove-btn {
  position: absolute;
  top: -8rpx;
  right: -8rpx;
  width: 40rpx;
  height: 40rpx;
  background: rgba(0,0,0,0.6);
  color: #fff;
  border-radius: 20rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24rpx;
}

.add-image {
  width: 160rpx;
  height: 160rpx;
  border: 2rpx dashed #e0e0e0;
  border-radius: 8rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
}

.plus {
  font-size: 48rpx;
  color: #999;
}

.hint {
  font-size: 24rpx;
  color: #999;
}

.input {
  width: 100%;
  padding: 16rpx;
  border: 1rpx solid #e0e0e0;
  border-radius: 8rpx;
  font-size: 28rpx;
}

.submit-btn {
  width: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  border: none;
  border-radius: 12rpx;
  font-size: 32rpx;
  padding: 24rpx;
}
</style>
