<template>
  <view class="point-redemptions-page">
    <view class="header">
      <text class="title">🎁 兑换中心</text>
      <view class="points-balance">
        <text>可用积分: {{ balance }}</text>
      </view>
    </view>

    <!-- Tab切换 -->
    <view class="tabs">
      <view class="tab" :class="{ active: activeTab === 'create' }" @tap="activeTab = 'create'">
        <text>兑换奖励</text>
      </view>
      <view class="tab" :class="{ active: activeTab === 'history' }" @tap="activeTab = 'history'">
        <text>兑换记录</text>
      </view>
    </view>

    <!-- 兑换表单 -->
    <view v-if="activeTab === 'create'" class="create-section">
      <view class="form">
        <view class="form-item">
          <text class="label">奖励类型</text>
          <picker :range="rewardTypes" @change="onRewardTypeChange">
            <view class="picker">
              <text>{{ form.rewardType || '选择类型' }}</text>
              <text class="arrow">▼</text>
            </view>
          </picker>
        </view>

        <view class="form-item">
          <text class="label">奖励名称 *</text>
          <input v-model="form.rewardName" class="input" placeholder="如：100元京东卡" />
        </view>

        <view class="form-item">
          <text class="label">消耗积分 *</text>
          <input v-model="form.pointsCost" class="input" type="digit" placeholder="输入所需积分" />
        </view>

        <view class="form-item">
          <text class="label">配送信息</text>
          <textarea
            v-model="form.deliveryInfo"
            class="textarea"
            placeholder="收货人、联系电话、地址等（JSON格式）"
          />
        </view>

        <view class="form-item">
          <text class="label">备注</text>
          <textarea v-model="form.notes" class="textarea" placeholder="其他备注信息（可选）" />
        </view>
      </view>

      <view class="footer">
        <button class="submit-btn" :disabled="!isFormValid" @tap="handleSubmit">提交兑换</button>
      </view>
    </view>

    <!-- 兑换记录 -->
    <view v-if="activeTab === 'history'" class="history-section">
      <view v-if="loading" class="loading">
        <text>加载中...</text>
      </view>

      <view v-else-if="redemptions.length === 0" class="empty">
        <text class="empty-icon">📦</text>
        <text class="empty-text">暂无兑换记录</text>
      </view>

      <view v-else class="redemption-list">
        <view v-for="item in redemptions" :key="item.id" class="redemption-card">
          <view class="redemption-header">
            <text class="reward-name">{{ item.rewardName }}</text>
            <view class="status-badge" :class="'status-' + item.status">
              <text>{{ getStatusText(item.status) }}</text>
            </view>
          </view>

          <view class="redemption-info">
            <view class="info-row">
              <text class="label">类型</text>
              <text class="value">{{ getRewardTypeText(item.rewardType) }}</text>
            </view>
            <view class="info-row">
              <text class="label">积分</text>
              <text class="value points">-{{ item.pointsCost }}</text>
            </view>
            <view class="info-row">
              <text class="label">时间</text>
              <text class="value">{{ formatDate(item.created_at) }}</text>
            </view>
          </view>

          <view v-if="item.rejectionReason" class="rejection-reason">
            <text>拒绝原因: {{ item.rejectionReason }}</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import type { PointRedemptionCreate } from '@/api/ability-points'
import { getMyPoints, getMyRedemptions, createRedemption } from '@/api/ability-points'

const balance = ref(0)
const activeTab = ref('create')
const loading = ref(false)
const redemptions = ref([])

const form = ref({
  rewardType: '',
  rewardName: '',
  pointsCost: '',
  deliveryInfo: '',
  notes: '',
})

const rewardTypes = ['优惠券', '实物礼品', '会员权益', '虚拟商品', '其他']

const isFormValid = computed(() => {
  return form.value.rewardName && form.value.pointsCost && parseInt(form.value.pointsCost) > 0
})

onMounted(() => {
  fetchBalance()
  fetchRedemptions()
})

async function fetchBalance() {
  try {
    const points = await getMyPoints()
    balance.value = points.availablePoints
  } catch (err) {
    console.error('Failed to fetch balance:', err)
    uni.showToast({
      title: '加载积分失败',
      icon: 'none',
    })
  }
}

async function fetchRedemptions() {
  try {
    loading.value = true
    const response = await getMyRedemptions()
    redemptions.value = response.redemptions || []
  } catch (err) {
    console.error('Failed to fetch redemptions:', err)
    uni.showToast({
      title: '加载失败',
      icon: 'none',
    })
  } finally {
    loading.value = false
  }
}

function onRewardTypeChange(e) {
  form.value.rewardType = rewardTypes[e.detail.value]
}

function getStatusText(status) {
  const map = {
    pending: '待审核',
    approved: '已通过',
    completed: '已完成',
    rejected: '已拒绝',
  }
  return map[status] || status
}

function getRewardTypeText(type) {
  return type || '其他'
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return `${date.getMonth() + 1}-${date.getDate()}`
}

async function handleSubmit() {
  if (!isFormValid.value) {
    uni.showToast({ title: '请填写必填项', icon: 'none' })
    return
  }

  const pointsCost = parseInt(form.value.pointsCost)
  if (pointsCost > balance.value) {
    uni.showToast({ title: '积分不足', icon: 'none' })
    return
  }

  try {
    uni.showLoading({ title: '提交中...' })

    const data= {
      rewardName: form.value.rewardName,
      rewardType: form.value.rewardType || '其他',
      pointsCost,
      deliveryInfo: form.value.deliveryInfo || undefined,
      notes: form.value.notes || undefined,
    }

    await createRedemption(data)
    uni.hideLoading()

    uni.showToast({ title: '提交成功', icon: 'success' })
    form.value = {
      rewardType: '',
      rewardName: '',
      pointsCost: '',
      deliveryInfo: '',
      notes: '',
    }
    activeTab.value = 'history'
    await Promise.all([fetchRedemptions(), fetchBalance()])
  } catch (err) {
    uni.hideLoading()
    console.error('Failed to create redemption:', err)
    uni.showToast({
      title: err.message || '提交失败',
      icon: 'none',
    })
  }
}
</script>

<style lang="scss" scoped>
.point-redemptions-page {
  min-height: 100vh;
  background: var(--bg-base);
  padding: $spacing-md;
}

.header {
  text-align: center;
  padding: $spacing-lg 0;

  .title {
    display: block;
    font-size: $font-size-xl;
    font-weight: $font-weight-bold;
    margin-bottom: $spacing-sm;
  }

  .points-balance {
    display: inline-block;
    padding: $spacing-xs $spacing-lg;
    background: $gradient-brand;
    border-radius: $radius-full;
    font-size: $font-size-sm;
    font-weight: $font-weight-bold;
  }
}

.tabs {
  display: flex;
  @include glass-card();
  padding: $spacing-xs;
  margin-bottom: $spacing-md;

  .tab {
    flex: 1;
    text-align: center;
    padding: $spacing-sm;
    border-radius: $radius-md;
    font-size: $font-size-base;

    &.active {
      background: $brand-primary;
      color: white;
      font-weight: $font-weight-bold;
    }
  }
}

.create-section {
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

      .input,
      .textarea,
      .picker {
        width: 100%;
        padding: $spacing-md;
        border: 1rpx solid var(--border-subtle);
        border-radius: $radius-sm;
        font-size: $font-size-base;
        background: var(--bg-glass-subtle);
      }

      .picker {
        display: flex;
        justify-content: space-between;
        align-items: center;

        .arrow {
          font-size: $font-size-xs;
          color: var(--text-tertiary);
        }
      }

      .textarea {
        min-height: 120rpx;
      }
    }
  }

  .footer {
    padding: $spacing-md 0;

    .submit-btn {
      width: 100%;
      background: $gradient-brand;
      color: white;
      border: none;
      border-radius: $radius-full;
      padding: $spacing-lg;
      font-size: $font-size-lg;

      &[disabled] {
        background: var(--text-tertiary);
      }
    }
  }
}

.history-section {
  .loading {
    text-align: center;
    padding: 100rpx 0;
    color: var(--text-tertiary);
  }

  .empty {
    text-align: center;
    padding: 100rpx 0;

    .empty-icon {
      display: block;
      font-size: 80rpx;
      margin-bottom: $spacing-md;
    }

    .empty-text {
      font-size: $font-size-base;
      color: var(--text-tertiary);
    }
  }

  .redemption-list {
    .redemption-card {
      @include glass-card();
      padding: $spacing-lg;
      margin-bottom: $spacing-sm;

      .redemption-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: $spacing-md;

        .reward-name {
          font-size: $font-size-lg;
          font-weight: $font-weight-bold;
        }

        .status-badge {
          padding: $spacing-2xs $spacing-sm;
          border-radius: $radius-full;
          font-size: $font-size-xs;

          &.status-pending {
            background: #fff7e6;
            color: $semantic-warning;
          }

          &.status-approved {
            background: #e6f7ff;
            color: $brand-primary;
          }

          &.status-completed {
            background: #f6ffed;
            color: $semantic-success;
          }

          &.status-rejected {
            background: #fff1f0;
            color: $semantic-error;
          }
        }
      }

      .redemption-info {
        .info-row {
          display: flex;
          justify-content: space-between;
          padding: $spacing-xs 0;
          font-size: $font-size-sm;

          .label {
            color: var(--text-tertiary);
          }

          .value {
            color: var(--text-primary);

            &.points {
              color: $semantic-error;
              font-weight: $font-weight-bold;
            }
          }
        }
      }

      .rejection-reason {
        margin-top: $spacing-sm;
        padding-top: $spacing-sm;
        border-top: 1rpx dashed var(--border-subtle);
        font-size: $font-size-sm;
        color: $semantic-error;
      }
    }
  }
}
</style>
