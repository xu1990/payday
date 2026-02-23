<template>
  <view class="invite-code-page">
    <!-- 邀请码卡片 -->
    <view class="invite-card">
      <view class="card-header">
        <text class="title">我的邀请码</text>
        <text class="subtitle">邀请好友注册获得积分奖励</text>
      </view>

      <view class="code-section">
        <view class="code-box" @tap="copyInviteCode">
          <text class="code">{{ inviteCode || '加载中...' }}</text>
          <view class="copy-btn">
            <text>点击复制</text>
          </view>
        </view>
        <view class="reward-tip">
          <text>🎁 邀请奖励：你获得30积分，好友获得10积分</text>
        </view>
      </view>
    </view>

    <!-- 统计信息 -->
    <view class="stats-section">
      <view class="stat-item">
        <text class="stat-value">{{ stats.total_invited || 0 }}</text>
        <text class="stat-label">已邀请人数</text>
      </view>
      <view class="stat-divider"></view>
      <view class="stat-item">
        <text class="stat-value">{{ stats.total_points_earned || 0 }}</text>
        <text class="stat-label">获得积分</text>
      </view>
    </view>

    <!-- 邀请记录列表 -->
    <view class="invitations-section">
      <view class="section-title">
        <text>邀请记录</text>
      </view>

      <view v-if="loading" class="loading">
        <text>加载中...</text>
      </view>

      <view v-else-if="invitations.length === 0" class="empty">
        <text>暂无邀请记录</text>
        <text class="empty-tip">快去邀请好友吧~</text>
      </view>

      <view v-else class="invitations-list">
        <view class="invitation-item" v-for="item in invitations" :key="item.invitee_id">
          <view class="avatar">
            <text>{{ item.invitee_name.substring(0, 2) }}</text>
          </view>
          <view class="info">
            <text class="name">{{ item.invitee_name }}</text>
            <text class="time">{{ formatTime(item.created_at) }}</text>
          </view>
          <view class="reward">
            <text class="points">+{{ item.points_rewarded }}</text>
            <text class="label">积分</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 二维码邀请区域 -->
    <view class="qrcode-section" v-if="showQRCode">
      <view class="section-title">
        <text>二维码邀请</text>
        <text class="subtitle">好友扫码即可注册</text>
      </view>

      <view class="qrcode-container">
        <view v-if="generatingQRCode" class="qrcode-loading">
          <text>生成中...</text>
        </view>
        <image
          v-else-if="qrcodeDataUrl"
          class="qrcode-image"
          :src="qrcodeDataUrl"
          mode="widthFix"
        />
        <view v-else class="qrcode-placeholder">
          <text>二维码生成中...</text>
        </view>
        <view class="qrcode-tip">
          <text>好友扫描二维码填写邀请码注册</text>
        </view>
      </view>

      <view class="qrcode-actions">
        <button class="action-btn" @tap="saveQRCode" :disabled="!qrcodeDataUrl || generatingQRCode">
          <text>{{ generatingQRCode ? '生成中...' : '💾 保存二维码' }}</text>
        </button>
      </view>
    </view>

    <!-- 分享按钮 -->
    <view class="share-section">
      <button class="share-btn" @tap="shareInvite">
        <text>📤 分享邀请码给好友</text>
      </button>
    </view>
  </view>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { getMyInviteCode, getInvitationStats, getMyInvitations } from '@/api/invitation'
import { request } from '@/utils/request'

const inviteCode = ref('')
const stats = ref({ total_invited: 0, total_points_earned: 0 })
const invitations = ref([])
const loading = ref(false)
const qrcodeDataUrl = ref('')
const showQRCode = ref(false)
const generatingQRCode = ref(false)

onMounted(() => {
  loadData()
})

// 监听邀请码变化，显示二维码区域
watch(inviteCode, (newCode) => {
  if (newCode) {
    showQRCode.value = true
    // 生成二维码
    generateQRCode(newCode)
  }
})

// 生成二维码（使用后端 API）
async function generateQRCode(code) {
  try {
    generatingQRCode.value = true

    // 调用后端 API 生成小程序码
    const response = await request({
      url: '/api/v1/qrcode/wxa/generate',
      method: 'POST',
      data: {
        page: 'pages/login/index',
        params: {
          inviteCode: code
        },
        expires_days: 365  // 二维码有效期1年
      }
    })

    if (response && response.base64) {
      qrcodeDataUrl.value = response.base64
    }
  } catch (err) {
    console.error('Failed to generate QR code:', err)
    uni.showToast({
      title: '二维码生成失败',
      icon: 'none'
    })
  } finally {
    generatingQRCode.value = false
  }
}

// 保存二维码
async function saveQRCode() {
  if (!qrcodeDataUrl.value) {
    uni.showToast({
      title: '二维码未生成',
      icon: 'none'
    })
    return
  }

  try {
    uni.showLoading({
      title: '保存中...'
    })

    // 将 base64 转换为临时文件
    const base64Data = qrcodeDataUrl.value.replace(/^data:image\/\w+;base64,/, '')
    const fileName = `qrcode_${Date.now()}.png`

    // 使用 uni.env 获取临时目录路径（跨平台兼容）
    const tempFilePath = `${uni.env?.USER_DATA_PATH || wx.env.USER_DATA_PATH}/${fileName}`

    // 将 base64 转换为 ArrayBuffer
    const binaryString = uni.base64ToArrayBuffer(base64Data)

    // 写入临时文件
    const fs = uni.getFileSystemManager()
    fs.writeFileSync(tempFilePath, binaryString)

    // 保存图片到相册
    await uni.saveImageToPhotosAlbum({
      filePath: tempFilePath
    })

    uni.hideLoading()
    uni.showToast({
      title: '已保存到相册',
      icon: 'success'
    })

    // 清理临时文件
    setTimeout(() => {
      try {
        fs.unlinkSync(tempFilePath)
      } catch (e) {
        console.warn('Failed to cleanup temp file:', e)
      }
    }, 1000)
  } catch (err) {
    uni.hideLoading()
    console.error('Save failed:', err)

    // 如果用户拒绝授权
    if (err.errMsg && err.errMsg.includes('auth')) {
      uni.showModal({
        title: '提示',
        content: '需要您授权保存相册权限',
        success: (modalRes) => {
          if (modalRes.confirm) {
            uni.openSetting()
          }
        }
      })
    } else {
      uni.showToast({
        title: '保存失败',
        icon: 'none'
      })
    }
  }
}

async function loadData() {
  try {
    // 获取邀请码
    const codeRes = await getMyInviteCode()
    inviteCode.value = codeRes.invite_code || ''

    // 获取统计
    const statsRes = await getInvitationStats()
    stats.value = statsRes || { total_invited: 0, total_points_earned: 0 }

    // 获取邀请列表
    loading.value = true
    const listRes = await getMyInvitations()
    invitations.value = listRes.invitations || []
  } catch (err) {
    console.error('Failed to load data:', err)
    uni.showToast({
      title: '加载失败',
      icon: 'none'
    })
  } finally {
    loading.value = false
  }
}

function copyInviteCode() {
  if (!inviteCode.value) return

  uni.setClipboardData({
    data: inviteCode.value,
    success: () => {
      uni.showToast({
        title: '邀请码已复制',
        icon: 'success'
      })
    }
  })
}

function shareInvite() {
  // 这里可以调用小程序的分享功能
  uni.showShareMenu({
    withShareTicket: true
  })
  uni.showToast({
    title: '点击右上角分享给好友',
    icon: 'none'
  })
}

function formatTime(timeStr) {
  const date = new Date(timeStr)
  const now = new Date()
  const diff = Math.floor((now - date) / 1000)

  if (diff < 60) return '刚刚'
  if (diff < 3600) return `${Math.floor(diff / 60)}分钟前`
  if (diff < 86400) return `${Math.floor(diff / 3600)}小时前`
  if (diff < 2592000) return `${Math.floor(diff / 86400)}天前`

  const month = date.getMonth() + 1
  const day = date.getDate()
  return `${month}月${day}日`
}
</script>

<style lang="scss" scoped>
.invite-code-page {
  min-height: 100vh;
  background: #f5f5f5;
  padding-bottom: 150rpx;
}

.invite-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  margin: 20rpx;
  border-radius: 30rpx;
  padding: 40rpx;
  color: white;

  .card-header {
    text-align: center;
    margin-bottom: 40rpx;

    .title {
      display: block;
      font-size: 36rpx;
      font-weight: bold;
      margin-bottom: 10rpx;
    }

    .subtitle {
      font-size: 24rpx;
      opacity: 0.9;
    }
  }

  .code-section {
    .code-box {
      background: rgba(255, 255, 255, 0.2);
      border: 2rpx solid rgba(255, 255, 255, 0.5);
      border-radius: 20rpx;
      padding: 30rpx;
      text-align: center;
      margin-bottom: 20rpx;

      .code {
        display: block;
        font-size: 48rpx;
        font-weight: bold;
        letter-spacing: 5rpx;
        margin-bottom: 10rpx;
        font-family: 'Courier New', monospace;
      }

      .copy-btn {
        font-size: 24rpx;
        opacity: 0.9;
      }
    }

    .reward-tip {
      text-align: center;
      font-size: 24rpx;
      opacity: 0.9;
    }
  }
}

.stats-section {
  display: flex;
  background: white;
  margin: 20rpx;
  border-radius: 20rpx;
  padding: 40rpx;
  align-items: center;
  justify-content: space-around;

  .stat-item {
    flex: 1;
    text-align: center;

    .stat-value {
      display: block;
      font-size: 48rpx;
      font-weight: bold;
      color: #667eea;
      margin-bottom: 10rpx;
    }

    .stat-label {
      font-size: 24rpx;
      color: #999;
    }
  }

  .stat-divider {
    width: 2rpx;
    height: 80rpx;
    background: #e5e5e5;
  }
}

.invitations-section {
  margin: 20rpx;

  .section-title {
    font-size: 28rpx;
    font-weight: bold;
    margin-bottom: 20rpx;
    padding-left: 10rpx;
  }

  .loading,
  .empty {
    text-align: center;
    padding: 80rpx 0;
    color: #999;
    font-size: 26rpx;

    .empty-tip {
      display: block;
      font-size: 24rpx;
      margin-top: 10rpx;
    }
  }

  .invitations-list {
    .invitation-item {
      display: flex;
      align-items: center;
      background: white;
      border-radius: 20rpx;
      padding: 25rpx;
      margin-bottom: 15rpx;

      .avatar {
        width: 80rpx;
        height: 80rpx;
        border-radius: 50%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 28rpx;
        font-weight: bold;
        margin-right: 20rpx;
      }

      .info {
        flex: 1;

        .name {
          display: block;
          font-size: 28rpx;
          font-weight: bold;
          margin-bottom: 5rpx;
        }

        .time {
          font-size: 24rpx;
          color: #999;
        }
      }

      .reward {
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
}

.qrcode-section {
  margin: 20rpx;
  background: white;
  border-radius: 20rpx;
  padding: 30rpx;

  .section-title {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 28rpx;
    font-weight: bold;
    margin-bottom: 20rpx;
    padding-left: 0;

    .subtitle {
      font-size: 24rpx;
      color: #999;
      font-weight: normal;
    }
  }

  .qrcode-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 30rpx 0;
    background: #f8f8f8;
    border-radius: 15rpx;
    margin-bottom: 20rpx;

    .qrcode-loading,
    .qrcode-placeholder {
      width: 400rpx;
      height: 400rpx;
      display: flex;
      align-items: center;
      justify-content: center;
      background: white;
      border-radius: 10rpx;
      color: #999;
      font-size: 26rpx;
    }

    .qrcode-image {
      width: 400rpx;
      height: 400rpx;
      border-radius: 10rpx;
      background: white;
      box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.1);
    }

    .qrcode-tip {
      margin-top: 20rpx;
      font-size: 24rpx;
      color: #666;
      text-align: center;
    }
  }

  .qrcode-actions {
    display: flex;
    gap: 15rpx;

    .action-btn {
      flex: 1;
      background: white;
      color: #667eea;
      border: 1rpx solid #667eea;
      border-radius: 12rpx;
      padding: 20rpx;
      font-size: 26rpx;
      font-weight: 500;

      &::after {
        border: none;
      }
    }
  }
}

.share-section {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 20rpx;
  background: white;
  box-shadow: 0 -2rpx 10rpx rgba(0, 0, 0, 0.1);

  .share-btn {
    width: 100%;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 50rpx;
    padding: 25rpx;
    font-size: 28rpx;
    font-weight: bold;

    &::after {
      border: none;
    }
  }
}
</style>
