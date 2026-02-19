<script setup lang="ts">
import { ref, computed } from 'vue'
import { createPost, type PostCreateParams, type PostType } from '@/api/post'
import { VALIDATION_PATTERNS, VALIDATION_LIMITS, VALIDATION_ERRORS } from '@/constants/validation'
import {
  VISIBILITY_OPTIONS,
  type PostVisibility,
  INDUSTRY_OPTIONS,
  CITY_OPTIONS,
  SALARY_RANGE_OPTIONS
} from '@/constants/post'

const typeOptions: { value: PostType; label: string }[] = [
  { value: 'complaint', label: '吐槽' },
  { value: 'sharing', label: '分享' },
  { value: 'question', label: '提问' },
]

const type = ref<PostType>('complaint')
const content = ref('')
const images = ref<string[]>([])
const salary_range = ref('')
const industry = ref('')
const city = ref('')
const visibility = ref<PostVisibility>('public')
const submitting = ref(false)

// Picker 索引
const salaryIndex = ref(-1)
const industryIndex = ref(-1)
const cityIndex = ref(-1)
const visibilityIndex = ref(0)

// 计算当前选择的标签
const salaryLabel = computed(() => salaryIndex.value >= 0 ? SALARY_RANGE_OPTIONS[salaryIndex.value] : '选填')
const industryLabel = computed(() => industryIndex.value >= 0 ? INDUSTRY_OPTIONS[industryIndex.value] : '选填')
const cityLabel = computed(() => cityIndex.value >= 0 ? CITY_OPTIONS[cityIndex.value] : '选填')
const visibilityLabel = computed(() => VISIBILITY_OPTIONS[visibilityIndex.value].label)

// 选择图片
async function chooseImage() {
  if (images.value.length >= 9) {
    uni.showToast({ title: '最多上传9张图片', icon: 'none' })
    return
  }

  try {
    const res: any = await uni.chooseImage({
      count: 9 - images.value.length,
      sizeType: ['compressed'],
      sourceType: ['album', 'camera'],
    })

    if (res.tempFilePaths && res.tempFilePaths.length > 0) {
      // TODO: 这里需要上传图片到服务器
      // 暂时直接使用本地路径，实际需要调用上传接口
      images.value.push(...res.tempFilePaths)
    }
  } catch (e) {
    // 用户取消选择
  }
}

// 删除图片
function removeImage(index: number) {
  images.value.splice(index, 1)
}

// 预览图片
function previewImage(index: number) {
  uni.previewImage({
    urls: images.value,
    current: index
  })
}

// 选择薪资范围
function onSalaryChange(e: any) {
  salaryIndex.value = e.detail.value
  salary_range.value = SALARY_RANGE_OPTIONS[salaryIndex.value]
}

// 选择行业
function onIndustryChange(e: any) {
  industryIndex.value = e.detail.value
  industry.value = INDUSTRY_OPTIONS[industryIndex.value]
}

// 选择城市
function onCityChange(e: any) {
  cityIndex.value = e.detail.value
  city.value = CITY_OPTIONS[cityIndex.value]
}

// 选择可见性
function onVisibilityChange(e: any) {
  visibilityIndex.value = e.detail.value
  visibility.value = VISIBILITY_OPTIONS[visibilityIndex.value].value
}

async function submit() {
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

  submitting.value = true
  try {
    const data: PostCreateParams = {
      content: text,
      type: type.value,
      images: images.value.length > 0 ? images.value : undefined,
    }
    if (salary_range.value) data.salary_range = salary_range.value
    if (industry.value) data.industry = industry.value
    if (city.value) data.city = city.value

    // TODO: 添加 visibility 字段到后端 API
    // if (visibility.value !== 'public') data.visibility = visibility.value

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
      <!-- 类型选择 -->
      <view class="row type-row">
        <text class="label">类型</text>
        <view class="type-options">
          <view
            v-for="opt in typeOptions"
            :key="opt.value"
            class="type-option"
            :class="{ active: type === opt.value }"
            @click="type = opt.value"
          >
            {{ opt.label }}
          </view>
        </view>
      </view>

      <!-- 内容输入 -->
      <view class="row content-row">
        <text class="label">内容</text>
        <textarea
          v-model="content"
          class="input area"
          placeholder="说说你的想法…"
          maxlength="5000"
          :show-confirm-bar="false"
        />
        <view class="char-count">{{ content.length }}/5000</view>
      </view>

      <!-- 图片上传 -->
      <view class="row image-row">
        <text class="label">图片 ({{ images.length }}/9)</text>
        <view class="image-list">
          <view
            v-for="(img, i) in images"
            :key="i"
            class="image-item"
          >
            <image
              :src="img"
              mode="aspectFill"
              @click="previewImage(i)"
            />
            <view class="delete-btn" @click="removeImage(i)">×</view>
          </view>
          <view
            v-if="images.length < 9"
            class="add-image"
            @click="chooseImage"
          >
            <text class="add-icon">+</text>
            <text class="add-text">添加图片</text>
          </view>
        </view>
      </view>

      <!-- 薪资范围 -->
      <view class="row picker-row">
        <text class="label">薪资范围</text>
        <picker
          :value="salaryIndex"
          :range="SALARY_RANGE_OPTIONS"
          @change="onSalaryChange"
        >
          <view class="picker">
            {{ salaryLabel }}
            <text class="arrow">›</text>
          </view>
        </picker>
      </view>

      <!-- 行业 -->
      <view class="row picker-row">
        <text class="label">行业</text>
        <picker
          :value="industryIndex"
          :range="INDUSTRY_OPTIONS"
          @change="onIndustryChange"
        >
          <view class="picker">
            {{ industryLabel }}
            <text class="arrow">›</text>
          </view>
        </picker>
      </view>

      <!-- 城市 -->
      <view class="row picker-row">
        <text class="label">城市</text>
        <picker
          :value="cityIndex"
          :range="CITY_OPTIONS"
          @change="onCityChange"
        >
          <view class="picker">
            {{ cityLabel }}
            <text class="arrow">›</text>
          </view>
        </picker>
      </view>

      <!-- 可见性 -->
      <view class="row picker-row">
        <text class="label">可见范围</text>
        <picker
          :value="visibilityIndex"
          :range="VISIBILITY_OPTIONS"
          range-key="label"
          @change="onVisibilityChange"
        >
          <view class="picker">
            {{ visibilityLabel }}
            <text class="arrow">›</text>
          </view>
        </picker>
      </view>
      <view v-if="visibility !== 'public'" class="visibility-hint">
        {{ VISIBILITY_OPTIONS[visibilityIndex].description }}
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

<style scoped lang="scss">
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
  margin-bottom: 32rpx;

  &:last-child {
    margin-bottom: 0;
  }
}

.label {
  display: block;
  font-size: 28rpx;
  color: #333;
  font-weight: 500;
  margin-bottom: 16rpx;
}

// 类型选择
.type-row {
  .type-options {
    display: flex;
    gap: 16rpx;
  }

  .type-option {
    flex: 1;
    padding: 16rpx 24rpx;
    text-align: center;
    border: 2rpx solid #e0e0e0;
    border-radius: 8rpx;
    font-size: 28rpx;
    color: #666;
    transition: all 0.3s;

    &.active {
      border-color: #667eea;
      background: rgba(102, 126, 234, 0.1);
      color: #667eea;
      font-weight: 600;
    }
  }
}

// 内容输入
.content-row {
  position: relative;

  .area {
    min-height: 200rpx;
    padding-bottom: 60rpx;
  }

  .char-count {
    position: absolute;
    bottom: 16rpx;
    right: 16rpx;
    font-size: 24rpx;
    color: #999;
  }
}

// 图片上传
.image-row {
  .image-list {
    display: flex;
    flex-wrap: wrap;
    gap: 16rpx;
  }

  .image-item {
    position: relative;
    width: 160rpx;
    height: 160rpx;

    image {
      width: 100%;
      height: 100%;
      border-radius: 8rpx;
    }

    .delete-btn {
      position: absolute;
      top: -8rpx;
      right: -8rpx;
      width: 40rpx;
      height: 40rpx;
      background: rgba(0, 0, 0, 0.6);
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #fff;
      font-size: 28rpx;
      line-height: 1;
    }
  }

  .add-image {
    width: 160rpx;
    height: 160rpx;
    border: 2rpx dashed #ddd;
    border-radius: 8rpx;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: #fafafa;

    .add-icon {
      font-size: 48rpx;
      color: #999;
      line-height: 1;
    }

    .add-text {
      font-size: 24rpx;
      color: #999;
      margin-top: 8rpx;
    }
  }
}

// Picker 选择
.picker-row {
  .picker {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 20rpx 24rpx;
    border: 1rpx solid #e0e0e0;
    border-radius: 8rpx;
    font-size: 28rpx;
    color: #333;
    background: #fafafa;

    .arrow {
      color: #999;
      font-size: 32rpx;
      font-weight: 300;
    }
  }
}

.visibility-hint {
  margin-top: -24rpx;
  margin-bottom: 24rpx;
  padding-left: 24rpx;
  font-size: 24rpx;
  color: #999;
}

// 按钮
.btn {
  width: 100%;
  height: 88rpx;
  line-height: 88rpx;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  border-radius: 12rpx;
  font-size: 32rpx;
  font-weight: 600;
  border: none;

  &[disabled] {
    opacity: 0.6;
  }
}
</style>
