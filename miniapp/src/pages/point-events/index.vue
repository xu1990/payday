<template>
  <view class="point-events-page">
    <view class="header">
      <text class="title">📋 赚积分</text>
      <text class="subtitle">完成以下任务获得积分</text>
    </view>

    <view v-if="loading" class="loading">
      <text>加载中...</text>
    </view>

    <view v-else class="events-list">
      <!-- 邀请好友特殊入口 -->
      <view class="event-card special-card" @tap="goToInvite">
        <view class="event-icon">✨</view>
        <view class="event-info">
          <view class="event-name">邀请好友</view>
          <view class="event-desc">邀请好友注册，双方各得积分</view>
        </view>
        <view class="event-points">
          <text class="points">+30</text>
          <text class="label">积分/人</text>
        </view>
        <view class="arrow">›</view>
      </view>

      <view
        v-for="event in events"
        :key="event.event_type"
        class="event-card"
        @tap="goToEvent(event.event_type)"
      >
        <view class="event-icon">{{ getEventIcon(event.event_type) }}</view>
        <view class="event-info">
          <view class="event-name">{{ getEventName(event.event_type) }}</view>
          <view class="event-desc">{{ getEventDesc(event.event_type) }}</view>
        </view>
        <view class="event-points">
          <text class="points">+{{ event.points }}</text>
          <text class="label">积分</text>
        </view>
        <view class="arrow">›</view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getPointEvents } from '@/api/ability-points'

const loading = ref(true)
const events = ref([])
const error = ref(null)

const eventNames = {
  checkin_daily: '每日打卡',
  checkin_weekly: '每周打卡',
  checkin_milestone: '里程碑打卡',
  checkin_special: '特殊打卡',
  post_create: '发布帖子',
  post_liked: '帖子被赞',
  comment_create: '发表评论',
  follow_someone: '关注他人',
  salary_record: '记录工资',
  first_salary: '第一笔工资',
  savings_goal_create: '创建存款目标',
  savings_goal_complete: '完成存款目标',
}

const eventDescs = {
  checkin_daily: '每天签到打卡获得积分',
  checkin_weekly: '连续打卡一周获得奖励',
  checkin_milestone: '达成打卡里程碑',
  checkin_special: '参与特殊打卡活动',
  post_create: '在社区分享你的故事',
  post_liked: '你的帖子被他人点赞',
  comment_create: '参与社区互动评论',
  follow_someone: '关注感兴趣的用户',
  salary_record: '记录每月工资收入',
  first_salary: '记录第一笔工资',
  savings_goal_create: '设定存款目标',
  savings_goal_complete: '达成存款目标',
}

const eventIcons = {
  checkin_daily: '📅',
  checkin_weekly: '📆',
  checkin_milestone: '🏆',
  checkin_special: '⭐',
  post_create: '✍️',
  post_liked: '👍',
  comment_create: '💬',
  follow_someone: '👥',
  salary_record: '💰',
  first_salary: '🎉',
  savings_goal_create: '🎯',
  savings_goal_complete: '🎊',
}

onMounted(() => {
  fetchEvents()
})

async function fetchEvents() {
  try {
    loading.value = true
    error.value = null
    const response = await getPointEvents()
    events.value = response.events || []
  } catch (err) {
    console.error('Failed to fetch events:', err)
    error.value = err.message || '加载失败'
    uni.showToast({
      title: error.value,
      icon: 'none',
    })
  } finally {
    loading.value = false
  }
}

function getEventName(type) {
  return eventNames[type] || type
}

function getEventDesc(type) {
  return eventDescs[type] || '完成此任务获得积分'
}

function getEventIcon(type) {
  return eventIcons[type] || '🎁'
}

function goToInvite() {
  uni.navigateTo({
    url: '/pages/invite-code/index',
  })
}

function goToEvent(eventType) {
  const routes = {
    checkin_daily: '/pages/checkin/index',
    checkin_weekly: '/pages/checkin/index',
    checkin_milestone: '/pages/checkin/index',
    checkin_special: '/pages/checkin/index',
    post_create: '/pages/post-create/index',
    follow_someone: '/pages/user-list/index',
    salary_record: '/pages/salary-record/index',
    first_salary: '/pages/salary-record/index',
    savings_goal_create: '/pages/savings-goals/index',
    savings_goal_complete: '/pages/savings-goals/index',
  }

  const route = routes[eventType]
  if (route) {
    uni.navigateTo({
      url: route,
    })
  }
}
</script>

<style lang="scss" scoped>
.point-events-page {
  min-height: 100vh;
  background: #f5f5f5;
  padding: 20rpx;
}

.header {
  text-align: center;
  padding: 40rpx 0;

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

.loading {
  text-align: center;
  padding: 100rpx 0;
  color: #999;
}

.events-list {
  .event-card {
    display: flex;
    align-items: center;
    background: white;
    border-radius: 20rpx;
    padding: 25rpx;
    margin-bottom: 15rpx;
    position: relative;

    &.special-card {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

      .event-icon {
        filter: drop-shadow(0 2rpx 4rpx rgba(0, 0, 0, 0.1));
      }

      .event-name {
        color: white;
      }

      .event-desc {
        color: rgba(255, 255, 255, 0.8);
      }

      .event-points {
        .points {
          color: #fff;
        }

        .label {
          color: rgba(255, 255, 255, 0.8);
        }
      }

      .arrow {
        font-size: 40rpx;
        color: white;
        font-weight: 300;
        margin-left: 10rpx;
      }
    }

    .event-icon {
      font-size: 50rpx;
      margin-right: 20rpx;
    }

    .event-info {
      flex: 1;

      .event-name {
        font-size: 28rpx;
        font-weight: bold;
        margin-bottom: 5rpx;
      }

      .event-desc {
        font-size: 24rpx;
        color: #999;
      }
    }

    .event-points {
      text-align: right;

      .points {
        display: block;
        font-size: 32rpx;
        font-weight: bold;
        color: #1890ff;
      }

      .label {
        font-size: 22rpx;
        color: #999;
      }
    }

    .arrow {
      font-size: 40rpx;
      color: #ccc;
      font-weight: 300;
      margin-left: 10rpx;
    }
  }
}
</style>
