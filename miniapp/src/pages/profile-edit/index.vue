<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { updateCurrentUser, type UserInfo } from '@/api/user'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()

const nickname = ref('')
const avatarUrl = ref('')

onMounted(() => {
  if (userStore.userInfo) {
    nickname.value = userStore.userInfo.nickname || ''
    avatarUrl.value = userStore.userInfo.avatar || ''
  }
})

// 选择头像
async function chooseAvatar() {
  try {
    const res: any = await uni.chooseImage({
      count: 1,
      sizeType: ['compressed'],
      sourceType: ['album', 'camera'],
    })

    if (res.tempFilePaths && res.tempFilePaths.length > 0) {
      const tempPath = res.tempFilePaths[0]
      await uploadAvatar(tempPath)
    }
  } catch (e) {
    // 用户取消选择
  }
}

// 上传头像
async function uploadAvatar(filePath: string) {
  try {
    uni.showLoading({ title: '上传中...' })

    const token = uni.getStorageSync('token')
    const uploadRes: any = await uni.uploadFile({
      url: 'http://127.0.0.1:8000/api/v1/user/me/upload-avatar',
      filePath,
      name: 'file',
      header: {
        Authorization: `Bearer ${token}`,
      },
    })

    const data = JSON.parse(uploadRes.data)
    if (data.code === 0) {
      avatarUrl.value = data.data.url

      // 更新 userStore
      await userStore.fetchCurrentUser()

      uni.hideLoading()
      uni.showToast({ title: '头像上传成功', icon: 'success' })
    } else {
      throw new Error(data.message || '上传失败')
    }
  } catch (e: any) {
    uni.hideLoading()
    uni.showToast({ title: e?.message || '上传失败', icon: 'none' })
  }
}

// 修改昵称
async function editNickname() {
  try {
    const res: any = await uni.showModal({
      title: '修改昵称',
      editable: true,
      placeholderText: nickname.value || '请输入昵称',
      maxLength: 20,
    })

    if (res.confirm && res.content) {
      const newNickname = res.content.trim()
      if (newNickname && newNickname !== nickname.value) {
        await saveNickname(newNickname)
      }
    }
  } catch (e) {
    // 用户取消
  }
}

// 保存昵称
async function saveNickname(newNickname: string) {
  try {
    uni.showLoading({ title: '保存中...' })
    await updateCurrentUser({ nickname: newNickname })

    nickname.value = newNickname

    // 更新 userStore
    await userStore.fetchCurrentUser()

    uni.hideLoading()
    uni.showToast({ title: '保存成功', icon: 'success' })
  } catch (e: any) {
    uni.hideLoading()
    uni.showToast({ title: e?.message || '保存失败', icon: 'none' })
  }
}
</script>

<template>
  <view class="page">
    <!-- 头像 -->
    <view class="section">
      <view class="section-title">头像</view>
      <view class="avatar-container" @click="chooseAvatar">
        <image
          class="avatar-image"
          :src="avatarUrl || '/static/default-avatar.png'"
          mode="aspectFill"
        />
        <text class="change-hint">点击更换</text>
      </view>
    </view>

    <!-- 昵称 -->
    <view class="section">
      <view class="section-title">昵称</view>
      <view class="nickname-container" @click="editNickname">
        <text class="nickname-text">{{ nickname || '未设置' }}</text>
        <text class="arrow">›</text>
      </view>
    </view>

    <!-- 提示信息 -->
    <view class="tips">
      <text class="tips-text">点击头像可从相册或相机选择图片上传</text>
    </view>
  </view>
</template>

<style scoped lang="scss">
.page {
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
  color: #999;
  margin-bottom: 16rpx;
}

.avatar-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20rpx 0;
}

.avatar-image {
  width: 160rpx;
  height: 160rpx;
  border-radius: 80rpx;
  background: #f0f0f0;
  margin-bottom: 16rpx;
}

.change-hint {
  font-size: 24rpx;
  color: #667eea;
}

.nickname-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16rpx 0;
}

.nickname-text {
  font-size: 30rpx;
  color: #333;
}

.arrow {
  font-size: 48rpx;
  color: #999;
  font-weight: 300;
}

.tips {
  padding: 24rpx;
}

.tips-text {
  font-size: 24rpx;
  color: #999;
  text-align: center;
}
</style>
