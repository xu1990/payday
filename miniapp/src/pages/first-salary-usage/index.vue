<template>
  <view class="salary-usage-page">
    <!-- 导航栏 -->
    <view class="navbar">
      <view class="nav-back" @tap="goBack">
        <text class="icon">←</text>
      </view>
      <view class="nav-title">第一笔工资用途</view>
      <view class="nav-placeholder"></view>
    </view>

    <!-- 工资信息 -->
    <view class="salary-info">
      <text class="label">你的第一笔工资（¥{{ salaryAmount }}）</text>
      <text class="question">是怎么用的？</text>
    </view>

    <!-- 用途列表 -->
    <view class="usage-list">
      <view
        v-for="(usage, index) in usages"
        :key="index"
        class="usage-item"
      >
        <!-- 分类选择器 -->
        <picker
          mode="selector"
          :range="categories"
          :value="getCategoryIndex(usage.usageCategory)"
          @change="(e) => onCategoryChange(e, index)"
        >
          <view class="category-picker">
            <text class="category-icon">{{ getCategoryIcon(usage.usageCategory) }}</text>
            <text class="category-text">{{ usage.usageCategory }}</text>
            <text class="arrow">›</text>
          </view>
        </picker>

        <!-- 金额输入 -->
        <input
          class="amount-input"
          type="digit"
          v-model="usage.amount"
          placeholder="金额"
          @input="calculateTotal"
        />

        <!-- 删除按钮 -->
        <view
          class="delete-btn"
          v-if="usages.length > 1"
          @tap="removeUsage(index)"
        >
          <text class="delete-icon">×</text>
        </view>
      </view>
    </view>

    <!-- 添加用途按钮 -->
    <view class="add-btn" @tap="addUsage">
      <text class="add-icon">+</text>
      <text class="add-text">添加用途</text>
    </view>

    <!-- 底部信息 -->
    <view class="footer">
      <view class="total">
        <text class="total-label">总计：</text>
        <text class="total-amount">¥{{ totalAmount }}</text>
      </view>
      <view class="tip" v-if="totalAmount > salaryAmount">
        <text class="warning">⚠️ 总金额超过了工资数额</text>
      </view>
      <button class="save-btn" @tap="handleSave" :disabled="isSaving">
        <text v-if="!isSaving">保存并生成分享卡</text>
        <text v-else>保存中...</text>
      </button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { showSuccess, showError } from '@/utils/toast'

interface Usage {
  usageCategory: string
  amount: string | number
  note?: string
}

const props = defineProps<{
  recordId?: string
  salaryAmount?: string | number
}>()

// 用途分类预设
const categories = [
  '💰 存起来',
  '🏠 交家里',
  '🛒 买东西',
  '🍖 吃顿好的',
  '🎉 娱乐玩乐',
  '🎁 送礼请客',
  '📚 学习提升',
  '💸 还债还贷',
  '📱 其他'
]

const usages = ref<Usage[]>([
  { usageCategory: categories[0], amount: '' }
])

const salaryAmount = ref(props.salaryAmount || 0)
const recordId = ref(props.recordId || '')
const isSaving = ref(false)

// 计算总金额
const totalAmount = computed(() => {
  return usages.value.reduce((sum, u) => {
    return sum + (Number(u.amount) || 0)
  }, 0).toFixed(2)
})

// 获取分类图标
function getCategoryIcon(category: string): string {
  const match = category.match(/^[^\s]+/)
  return match ? match[0] : '📝'
}

// 获取分类索引
function getCategoryIndex(category: string): number {
  return categories.findIndex(c => c === category)
}

// 分类改变
function onCategoryChange(e: any, index: number) {
  usages.value[index].usageCategory = categories[e.detail.value]
}

// 添加用途
function addUsage() {
  if (usages.value.length >= 10) {
    showError('最多只能添加10条用途')
    return
  }
  usages.value.push({
    usageCategory: categories[0],
    amount: ''
  })
}

// 删除用途
function removeUsage(index: number) {
  usages.value.splice(index, 1)
  calculateTotal()
}

// 计算总额
function calculateTotal() {
  // 触发 computed 重新计算
  // 实际计算由 computed 处理
}

// 返回
function goBack() {
  uni.navigateBack()
}

// 保存
async function handleSave() {
  // 验证
  if (totalAmount.value === '0.00' || totalAmount.value === '0') {
    showError('请至少输入一个用途金额')
    return
  }

  // 验证每条记录都有金额
  const hasEmptyAmount = usages.value.some(u => !u.amount || Number(u.amount) <= 0)
  if (hasEmptyAmount) {
    showError('请填写所有用途的金额')
    return
  }

  try {
    isSaving.value = true

    // 调用 API 保存
    // TODO: 实现真实的 API 调用
    // const { createFirstSalaryUsage } = await import('@/api/firstSalaryUsage')
    // await createFirstSalaryUsage(recordId.value, usages.value)

    // 模拟保存成功
    await new Promise(resolve => setTimeout(resolve, 1000))

    showSuccess('保存成功')

    // TODO: 生成分享卡
    setTimeout(() => {
      uni.navigateBack()
    }, 1500)
  } catch (error: any) {
    showError(error.message || '保存失败')
  } finally {
    isSaving.value = false
  }
}

onMounted(() => {
  // 从路由参数获取数据
  const pages = getCurrentPages()
  const currentPage = pages[pages.length - 1] as any
  const options = currentPage?.options || {}

  if (options.salaryAmount) {
    salaryAmount.value = Number(options.salaryAmount)
  }
  if (options.recordId) {
    recordId.value = options.recordId
  }
})
</script>

<style scoped>
.salary-usage-page {
  min-height: 100vh;
  background: #f5f5f5;
  padding-bottom: 200rpx;
}

.navbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 30rpx;
  background: #fff;
  position: sticky;
  top: 0;
  z-index: 100;
}

.nav-back {
  width: 60rpx;
  height: 60rpx;
  display: flex;
  align-items: center;
}

.nav-back .icon {
  font-size: 40rpx;
  color: #333;
}

.nav-title {
  font-size: 32rpx;
  font-weight: bold;
  color: #333;
}

.nav-placeholder {
  width: 60rpx;
}

.salary-info {
  text-align: center;
  padding: 60rpx 30rpx;
  background: #fff;
  margin: 20rpx;
  border-radius: 16rpx;
}

.label {
  display: block;
  font-size: 28rpx;
  color: #666;
  margin-bottom: 10rpx;
}

.question {
  display: block;
  font-size: 24rpx;
  color: #999;
}

.usage-list {
  padding: 0 20rpx;
}

.usage-item {
  display: flex;
  align-items: center;
  padding: 30rpx;
  background: #fff;
  border-radius: 12rpx;
  margin-bottom: 20rpx;
}

.category-picker {
  flex: 1;
  display: flex;
  align-items: center;
}

.category-icon {
  font-size: 40rpx;
  margin-right: 10rpx;
}

.category-text {
  font-size: 28rpx;
  color: #333;
}

.arrow {
  font-size: 32rpx;
  color: #999;
  margin-left: 10rpx;
}

.amount-input {
  width: 150rpx;
  text-align: right;
  font-size: 28rpx;
  border: 1rpx solid #e0e0e0;
  border-radius: 8rpx;
  padding: 10rpx;
}

.delete-btn {
  width: 50rpx;
  height: 50rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-left: 20rpx;
}

.delete-icon {
  font-size: 50rpx;
  color: #ff4d4f;
}

.add-btn {
  margin: 0 20rpx;
  padding: 30rpx;
  border: 2rpx dashed #999;
  border-radius: 12rpx;
  text-align: center;
  color: #666;
}

.add-icon {
  font-size: 40rpx;
}

.add-text {
  font-size: 28rpx;
  margin-left: 10rpx;
}

.footer {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 30rpx;
  background: #fff;
  box-shadow: 0 -2rpx 10rpx rgba(0,0,0,0.1);
}

.total {
  text-align: center;
  margin-bottom: 10rpx;
}

.total-label {
  font-size: 28rpx;
  color: #666;
}

.total-amount {
  font-size: 36rpx;
  font-weight: bold;
  color: #07c160;
}

.tip {
  text-align: center;
  margin-bottom: 20rpx;
}

.warning {
  font-size: 24rpx;
  color: #ff4d4f;
}

.save-btn {
  width: 100%;
  background: #07c160;
  color: white;
  border-radius: 12rpx;
  padding: 30rpx;
  font-size: 32rpx;
  border: none;
}

.save-btn[disabled] {
  opacity: 0.6;
}
</style>
