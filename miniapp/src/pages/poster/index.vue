<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { onLoad, onShareAppMessage } from '@dcloudio/uni-app'
import { listPayday, type PaydayConfig } from '@/api/payday'
import { getSalary, listSalary, type SalaryRecord, type MoodType } from '@/api/salary'

const recordId = ref<string>('')
const record = ref<SalaryRecord | null>(null)
const paydayList = ref<PaydayConfig[]>([])
const loading = ref(true)
const errMsg = ref('')
const saving = ref(false)
const posterUrl = ref('')

const moodText: Record<MoodType, string> = {
  happy: '开心',
  relief: '续命',
  sad: '崩溃',
  angry: '暴躁',
  expect: '期待',
}

const jobName = computed(
  () => (configId: string) => paydayList.value.find(c => c.id === configId)?.job_name || '工资'
)

onLoad((query: any) => {
  recordId.value = query?.recordId || ''
})

onShareAppMessage(() => ({
  title: '发薪海报',
  path: recordId.value ? `/pages/poster/index?recordId=${recordId.value}` : '/pages/poster/index',
  imageUrl: posterUrl.value || '',
}))

async function loadData() {
  loading.value = true
  errMsg.value = ''
  try {
    const [paydayRes, recordData] = await Promise.all([listPayday(), fetchRecord()])
    paydayList.value = paydayRes || []
    record.value = recordData
    if (record.value) {
      await drawPoster()
    }
  } catch (e: any) {
    console.error('[poster] Load failed:', e)
    errMsg.value = e?.message || '加载失败'
  } finally {
    loading.value = false
  }
}

async function fetchRecord(): Promise<SalaryRecord | null> {
  if (recordId.value) {
    const res = await getSalary(recordId.value)
    return res
  }
  const list = await listSalary({ limit: 1 })
  const first = Array.isArray(list) && list.length ? list[0] : null
  if (first) recordId.value = first.id
  return first
}

/**
 * Draw rounded rectangle (WeChat mini-program compatible)
 * Replaces ctx.roundRect which is not available in mini-program environment
 */
function drawRoundedRect(
  ctx: any,
  x: number,
  y: number,
  width: number,
  height: number,
  radius: number
): void {
  ctx.beginPath()
  ctx.moveTo(x + radius, y)
  ctx.lineTo(x + width - radius, y)
  ctx.arcTo(x + width, y, x + width, y + radius, radius)
  ctx.lineTo(x + width, y + height - radius)
  ctx.arcTo(x + width, y + height, x + width - radius, y + height, radius)
  ctx.lineTo(x + radius, y + height)
  ctx.arcTo(x, y + height, x, y + height - radius, radius)
  ctx.lineTo(x, y + radius)
  ctx.arcTo(x, y, x + radius, y, radius)
  ctx.closePath()
}

function drawPoster(): Promise<void> {
  const r = record.value
  if (!r) return Promise.resolve()

  return new Promise((resolve, reject) => {
    const ctx = uni.createCanvasContext('posterCanvas')
    const w = 375
    const h = 500
    const padding = 24
    const lineH = 28

    // 背景 - 渐变色
    const gradient = ctx.createLinearGradient(0, 0, 0, h)
    gradient.addColorStop(0, '#667eea')
    gradient.addColorStop(1, '#764ba2')
    ctx.setFillStyle(gradient)
    ctx.fillRect(0, 0, w, h)

    // 顶部装饰条
    ctx.setFillStyle('rgba(255,255,255,0.2)')
    ctx.fillRect(0, 0, w, 6)

    // 标题
    ctx.setFillStyle('#fff')
    ctx.setFontSize(16)
    ctx.setTextAlign('center')
    ctx.fillText('发薪日', w / 2, 50)

    // 金额背景
    ctx.setFillStyle('rgba(255,255,255,0.15)')
    drawRoundedRect(ctx, padding - 12, 80, w - padding * 2 + 24, 100, 16)
    ctx.fill()

    // 金额
    ctx.setFillStyle('#fff')
    ctx.setFontSize(48)
    ctx.setFontWeight('bold')
    ctx.setTextAlign('center')
    ctx.fillText(`¥${r.amount}`, w / 2, 145)
    ctx.setFontWeight('normal')

    // 发薪日期
    ctx.setFillStyle('rgba(255,255,255,0.9)')
    ctx.setFontSize(14)
    ctx.setTextAlign('center')
    ctx.fillText(r.payday_date, w / 2, 185)

    // 工作名
    ctx.setFillStyle('rgba(255,255,255,0.8)')
    ctx.setFontSize(13)
    ctx.fillText(jobName.value(r.config_id), w / 2, 210)

    // 分隔线
    ctx.setStrokeStyle('rgba(255,255,255,0.2)')
    ctx.setLineWidth(1)
    ctx.beginPath()
    ctx.moveTo(padding, 240)
    ctx.lineTo(w - padding, 240)
    ctx.stroke()

    // 心情标签
    const moodBg = 'rgba(255,255,255,0.2)'
    ctx.setFillStyle(moodBg)
    drawRoundedRect(ctx, w / 2 - 40, 260, 80, 32, 16)
    ctx.fill()

    ctx.setFillStyle('#fff')
    ctx.setFontSize(14)
    ctx.setTextAlign('center')
    ctx.fillText(moodText[r.mood] || r.mood, w / 2, 282)

    // 底部文案
    ctx.setFillStyle('rgba(255,255,255,0.6)')
    ctx.setFontSize(12)
    ctx.setTextAlign('center')
    ctx.fillText('薪日 PayDay · 记录每一次到账', w / 2, h - 30)

    ctx.draw(false, () => {
      setTimeout(() => {
        uni.canvasToTempFilePath({
          canvasId: 'posterCanvas',
          width: w,
          height: h,
          destWidth: w * 2,
          destHeight: h * 2,
          fileType: 'png',
          success: res => {
            console.log('[poster] Canvas to temp file success:', res.tempFilePath)
            posterUrl.value = res.tempFilePath
            resolve()
          },
          fail: e => {
            console.error('[poster] Canvas to temp file failed:', e)
            reject(e)
          },
        })
      }, 500)
    })
  })
}

async function saveToAlbum() {
  if (!posterUrl.value) {
    uni.showToast({ title: '请先生成海报', icon: 'none' })
    return
  }
  saving.value = true
  try {
    // 先检查权限
    const authRes = await uni.getSetting()
    if (!authRes.authSetting['scope.writePhotosAlbum']) {
      // 没有权限，请求权限
      await uni.authorize({ scope: 'scope.writePhotosAlbum' })
    }
    await uni.saveImageToPhotosAlbum({ filePath: posterUrl.value })
    uni.showToast({ title: '已保存到相册', icon: 'success' })
  } catch (e: any) {
    console.error('[poster] Save failed:', e)
    if (e?.errMsg?.includes('auth deny')) {
      uni.showModal({
        title: '提示',
        content: '需要相册权限才能保存，请在设置中开启',
        confirmText: '去设置',
        success: res => res.confirm && uni.openSetting(),
      })
    } else {
      uni.showToast({ title: e?.message || '保存失败', icon: 'none' })
    }
  } finally {
    saving.value = false
  }
}

function onShare() {
  uni.showToast({ title: '请点击右上角分享', icon: 'none' })
}

function previewImage() {
  if (!posterUrl.value) return
  uni.previewImage({
    urls: [posterUrl.value],
    current: posterUrl.value,
  })
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <view class="page">
    <!-- Loading -->
    <view v-if="loading" class="loading-wrapper">
      <view class="loading-icon"></view>
      <text class="loading-text">生成海报中...</text>
    </view>

    <!-- Error -->
    <view v-else-if="errMsg" class="error-wrapper">
      <text class="error-icon">⚠️</text>
      <text class="error-text">{{ errMsg }}</text>
      <button class="retry-btn" @click="loadData">重试</button>
    </view>

    <!-- Empty -->
    <view v-else-if="!record" class="empty-wrapper">
      <text class="empty-icon">💰</text>
      <text class="empty-text">暂无工资记录</text>
      <text class="empty-hint">先去记一笔吧</text>
    </view>

    <!-- Content -->
    <view v-else class="content">
      <!-- Canvas (hidden, used for rendering) -->
      <canvas
        canvas-id="posterCanvas"
        class="canvas"
        :style="{ width: '375px', height: '500px' }"
      />

      <!-- Generated Poster Image -->
      <image
        v-if="posterUrl"
        class="poster-image"
        :src="posterUrl"
        mode="widthFix"
        @click="previewImage"
      />

      <!-- Actions -->
      <view class="actions">
        <button class="btn primary" :loading="saving" @click="saveToAlbum">保存到相册</button>
        <button class="btn secondary" open-type="share">分享给好友</button>
      </view>

      <!-- Hint -->
      <view class="hint">点击海报可预览大图</view>
    </view>
  </view>
</template>

<style scoped lang="scss">
.page {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 24rpx;
  box-sizing: border-box;
}

// Loading
.loading-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 120rpx 0;
}

.loading-icon {
  width: 60rpx;
  height: 60rpx;
  border: 4rpx solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.loading-text {
  margin-top: 32rpx;
  font-size: 28rpx;
  color: #fff;
}

// Error
.error-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 120rpx 0;
}

.error-icon {
  font-size: 80rpx;
  margin-bottom: 24rpx;
}

.error-text {
  font-size: 28rpx;
  color: #fff;
  margin-bottom: 40rpx;
}

.retry-btn {
  padding: 20rpx 48rpx;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 48rpx;
  color: #fff;
  font-size: 28rpx;
}

// Empty
.empty-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 120rpx 0;
}

.empty-icon {
  font-size: 100rpx;
  margin-bottom: 24rpx;
}

.empty-text {
  font-size: 32rpx;
  color: #fff;
  font-weight: 600;
  margin-bottom: 12rpx;
}

.empty-hint {
  font-size: 26rpx;
  color: rgba(255, 255, 255, 0.7);
}

// Content
.content {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.canvas {
  position: fixed;
  left: -9999rpx;
  top: -9999rpx;
}

.poster-image {
  width: 100%;
  max-width: 600rpx;
  border-radius: 24rpx;
  box-shadow: 0 16rpx 48rpx rgba(0, 0, 0, 0.2);
  margin-bottom: 40rpx;
  background: #fff;
}

.actions {
  display: flex;
  flex-direction: column;
  gap: 24rpx;
  width: 100%;
  max-width: 500rpx;
}

.btn {
  padding: 28rpx;
  border-radius: 48rpx;
  font-size: 32rpx;
  font-weight: 600;
  border: none;
}

.btn.primary {
  background: #fff;
  color: #667eea;
  box-shadow: 0 8rpx 24rpx rgba(255, 255, 255, 0.3);
}

.btn.secondary {
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
}

.hint {
  margin-top: 32rpx;
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.6);
  text-align: center;
}
</style>
