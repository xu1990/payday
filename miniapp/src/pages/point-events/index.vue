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
      <view
        class="event-card"
        v-for="event in events"
        :key="event.event_type"
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
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const loading = ref(true)
const events = ref([])

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
  savings_goal_complete: '完成存款目标'
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
  savings_goal_complete: '达成存款目标'
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
  savings_goal_complete: '🎊'
}

onMounted(() => {
  fetchEvents()
})

async function fetchEvents() {
  try {
    loading.value = true
    const token = uni.getStorageSync('token')

    const res = await uni.request({
      url: 'https://api.example.com/api/v1/ability-points/events',
      method: 'GET',
      header: {
        'Authorization': `Bearer ${token}`
      }
    })

    if (res.data.code === 0) {
      events.value = res.data.data.events || []
    }
  } catch (error) {
    console.error(error)
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
  }
}
</style>
