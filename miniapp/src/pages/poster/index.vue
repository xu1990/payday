<script setup lang="ts">
import { ref, onMounted, computed, getCurrentInstance, nextTick } from 'vue'
import { onLoad, onShareAppMessage } from '@dcloudio/uni-app'
import { listPayday, type PaydayConfig } from '@/api/payday'
import { getSalary, listSalary, type SalaryRecord, type MoodType } from '@/api/salary'
import { getPostDetail, type PostItem } from '@/api/post'
import { formatDate } from '@/utils/format'
import QRCode from 'qrcode'

// 获取当前组件实例，用于 Canvas 查询
const instance = getCurrentInstance()

const recordId = ref<string>('')
const postId = ref<string>('')
const record = ref<SalaryRecord | null>(null)
const post = ref<PostItem | null>(null)
const paydayList = ref<PaydayConfig[]>([])
const loading = ref(true)
const errMsg = ref('')
const saving = ref(false)
const posterUrl = ref('')
const posterType = ref<'salary' | 'post'>('salary') // 'salary' for salary records, 'post' for posts

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
  postId.value = query?.postId || ''
  posterType.value = postId.value ? 'post' : 'salary'
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
    if (posterType.value === 'post') {
      // Load post data
      await fetchPost()
      if (post.value) {
        // 先关闭 loading，让 DOM 渲染
        loading.value = false
        // 等待 Vue nextTick 确保 DOM 更新
        await nextTick()
        // 再等待 canvas 元素渲染完成（type="2d" 需要更长时间）
        await new Promise(resolve => setTimeout(resolve, 1500))
        await drawPoster()
      }
    } else {
      // Load salary record data
      const [paydayRes, recordData] = await Promise.all([listPayday(), fetchRecord()])
      paydayList.value = paydayRes || []
      record.value = recordData
      if (record.value) {
        // 先关闭 loading，让 DOM 渲染
        loading.value = false
        // 等待 Vue nextTick 确保 DOM 更新
        await nextTick()
        // 再等待 canvas 元素渲染完成（type="2d" 需要更长时间）
        await new Promise(resolve => setTimeout(resolve, 1500))
        await drawPoster()
      }
    }
  } catch (e: any) {
    console.error('[poster] Load failed:', e)
    errMsg.value = e?.message || '加载失败'
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

async function fetchPost(): Promise<void> {
  if (!postId.value) {
    throw new Error('帖子ID不存在')
  }
  post.value = await getPostDetail(postId.value)
}

/**
 * Draw rounded rectangle (Canvas 2D version)
 */
function drawRoundedRect2D(
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
  if (posterType.value === 'post') {
    return drawPostPoster()
  } else {
    return drawSalaryPoster()
  }
}

/**
 * Generate QR code data URL for sharing
 */
function generateQRCodeUrl(recordId: string): Promise<string> {
  // TODO: 替换为实际的 H5 落地页 URL
  // 临时使用页面路径，等后端提供 H5 落地页后替换
  const shareUrl = `https://your-domain.com/poster/share?recordId=${recordId}`
  return QRCode.toDataURL(shareUrl, {
    width: 200,
    margin: 1,
    color: {
      dark: '#333333',
      light: '#FFFFFF'
    }
  })
}

/**
 * Draw salary record poster - using new Canvas 2D API
 */
function drawSalaryPoster(): Promise<void> {
  const r = record.value
  if (!r) return Promise.resolve()

  return new Promise((resolve, reject) => {
    // 先生成二维码
    generateQRCodeUrl(r.id)
      .then(qrDataUrl => {
        console.log('[poster] QR code generated')
        drawSalaryPosterWithQR(r, qrDataUrl, resolve, reject)
      })
      .catch(err => {
        console.error('[poster] Failed to generate QR code:', err)
        // 即使二维码生成失败，仍然绘制海报（不带二维码）
        drawSalaryPosterWithQR(r, null, resolve, reject)
      })
  })
}

/**
 * Draw salary record poster with QR code
 */
function drawSalaryPosterWithQR(
  r: SalaryRecord,
  qrDataUrl: string | null,
  resolve: (value: void | PromiseLike<void>) => void,
  reject: (reason?: any) => void
): void {
  try {
    console.log('[poster] Creating selector query')
    // 不使用 .in()，在整个页面范围内查询
    const query = uni.createSelectorQuery()
    query.select('#posterCanvas')
      .fields({ node: true, size: true })
      .exec(async (res) => {
        console.log('[poster] SelectorQuery result:', JSON.stringify(res))
        if (!res || !res[0]) {
          console.error('[poster] Query returned empty result')
          reject(new Error('Query returned empty result'))
          return
        }
        if (!res[0].node) {
          console.error('[poster] Canvas node not found, result:', res[0])
          reject(new Error('Canvas node not found'))
          return
        }

        const canvas = res[0].node
        const ctx = canvas.getContext('2d')

        const dpr = uni.getSystemInfoSync().pixelRatio
        const w = 375
        const h = 500

        // 设置 canvas 实际尺寸
        canvas.width = w * dpr
        canvas.height = h * dpr
        ctx.scale(dpr, dpr)

        const padding = 24

        console.log('[poster] Starting canvas draw with Canvas 2D API, size:', w, 'x', h, ', dpr:', dpr)

        // 清空画布
        ctx.clearRect(0, 0, w, h)

        // 背景 - 渐变色
        const gradient = ctx.createLinearGradient(0, 0, 0, h)
        gradient.addColorStop(0, '#667eea')
        gradient.addColorStop(1, '#764ba2')
        ctx.fillStyle = gradient
        ctx.fillRect(0, 0, w, h)

        // 顶部装饰条
        ctx.fillStyle = 'rgba(255,255,255,0.2)'
        ctx.fillRect(0, 0, w, 6)

        // 标题
        ctx.fillStyle = '#fff'
        ctx.font = '16px sans-serif'
        ctx.textAlign = 'center'
        ctx.fillText('发薪日', w / 2, 50)

        // 金额背景
        ctx.fillStyle = 'rgba(255,255,255,0.15)'
        drawRoundedRect2D(ctx, padding - 12, 80, w - padding * 2 + 24, 100, 16)
        ctx.fill()

        // 金额
        ctx.fillStyle = '#fff'
        ctx.font = '48px sans-serif'
        ctx.textAlign = 'center'
        ctx.fillText(`¥${r.amount}`, w / 2, 145)

        // 发薪日期
        ctx.fillStyle = 'rgba(255,255,255,0.9)'
        ctx.font = '14px sans-serif'
        ctx.textAlign = 'center'
        ctx.fillText(r.payday_date, w / 2, 185)

        // 工作名
        ctx.fillStyle = 'rgba(255,255,255,0.8)'
        ctx.font = '13px sans-serif'
        ctx.textAlign = 'center'
        ctx.fillText(jobName.value(r.config_id), w / 2, 210)

        // 分隔线
        ctx.strokeStyle = 'rgba(255,255,255,0.2)'
        ctx.lineWidth = 1
        ctx.beginPath()
        ctx.moveTo(padding, 240)
        ctx.lineTo(w - padding, 240)
        ctx.stroke()

        // 心情标签
        ctx.fillStyle = 'rgba(255,255,255,0.2)'
        drawRoundedRect2D(ctx, w / 2 - 40, 260, 80, 32, 16)
        ctx.fill()

        ctx.fillStyle = '#fff'
        ctx.font = '14px sans-serif'
        ctx.textAlign = 'center'
        ctx.fillText(moodText[r.mood] || r.mood, w / 2, 282)

        // 二维码
        if (qrDataUrl) {
          try {
            const qrImage = canvas.createImage()
            await new Promise((imgResolve, imgReject) => {
              qrImage.onload = imgResolve
              qrImage.onerror = imgReject
              qrImage.src = qrDataUrl
            })
            const qrSize = 80
            const qrX = w / 2 - qrSize / 2
            const qrY = 310
            ctx.drawImage(qrImage, qrX, qrY, qrSize, qrSize)

            // 二维码下方文字
            ctx.fillStyle = 'rgba(255,255,255,0.8)'
            ctx.font = '12px sans-serif'
            ctx.textAlign = 'center'
            ctx.fillText('扫码查看详情', w / 2, 405)
          } catch (e) {
            console.error('[poster] Failed to draw QR code:', e)
          }
        }

        // 底部文案
        ctx.fillStyle = 'rgba(255,255,255,0.6)'
        ctx.font = '12px sans-serif'
        ctx.textAlign = 'center'
        ctx.fillText('薪日 PayDay · 记录每一次到账', w / 2, h - 15)

        console.log('[poster] Canvas draw completed, converting to temp file')

        // 转换为临时文件
        uni.canvasToTempFilePath({
          canvas: canvas,
          x: 0,
          y: 0,
          width: w,
          height: h,
          destWidth: w * 2,
          destHeight: h * 2,
          fileType: 'png',
          success: (res2: any) => {
            console.log('[poster] Canvas to temp file success:', res2.tempFilePath)
            posterUrl.value = res2.tempFilePath
            resolve()
          },
          fail: (e: any) => {
            console.error('[poster] Canvas to temp file failed:', e)
            console.error('[poster] Error details:', JSON.stringify(e))
            posterUrl.value = ''
            reject(new Error('Canvas to temp file failed: ' + JSON.stringify(e)))
          },
        })
      })
  } catch (e) {
    console.error('[poster] Draw error:', e)
    reject(e)
  }
}

/**
 * Draw post poster - using new Canvas 2D API
 */
function drawPostPoster(): Promise<void> {
  const p = post.value
  if (!p) return Promise.resolve()

  return new Promise((resolve, reject) => {
    // 先生成二维码
    generateQRCodeUrl(p.id)
      .then(qrDataUrl => {
        console.log('[poster] QR code generated for post')
        drawPostPosterWithQR(p, qrDataUrl, resolve, reject)
      })
      .catch(err => {
        console.error('[poster] Failed to generate QR code:', err)
        // 即使二维码生成失败，仍然绘制海报（不带二维码）
        drawPostPosterWithQR(p, null, resolve, reject)
      })
  })
}

/**
 * Draw post poster with QR code
 */
function drawPostPosterWithQR(
  p: PostItem,
  qrDataUrl: string | null,
  resolve: (value: void | PromiseLike<void>) => void,
  reject: (reason?: any) => void
): void {
  try {
    console.log('[poster] Creating selector query for post')
    // 不使用 .in()，在整个页面范围内查询
    const query = uni.createSelectorQuery()
    query.select('#posterCanvas')
      .fields({ node: true, size: true })
      .exec(async (res) => {
        console.log('[poster] SelectorQuery result:', JSON.stringify(res))
        if (!res || !res[0]) {
          console.error('[poster] Query returned empty result')
          reject(new Error('Query returned empty result'))
          return
        }
        if (!res[0].node) {
          console.error('[poster] Canvas node not found, result:', res[0])
          reject(new Error('Canvas node not found'))
          return
        }

        const canvas = res[0].node
        const ctx = canvas.getContext('2d')

        const dpr = uni.getSystemInfoSync().pixelRatio
        const w = 375
        const h = 500

        // 设置 canvas 实际尺寸
        canvas.width = w * dpr
        canvas.height = h * dpr
        ctx.scale(dpr, dpr)

        const padding = 24

        console.log('[poster] Starting post canvas draw with Canvas 2D API, size:', w, 'x', h, ', dpr:', dpr)

        // 清空画布
        ctx.clearRect(0, 0, w, h)

        // 背景 - 渐变色
        const gradient = ctx.createLinearGradient(0, 0, 0, h)
        gradient.addColorStop(0, '#667eea')
        gradient.addColorStop(1, '#764ba2')
        ctx.fillStyle = gradient
        ctx.fillRect(0, 0, w, h)

        // 顶部装饰条
        ctx.fillStyle = 'rgba(255,255,255,0.2)'
        ctx.fillRect(0, 0, w, 6)

        // 标题
        ctx.fillStyle = '#fff'
        ctx.font = '16px sans-serif'
        ctx.textAlign = 'center'
        ctx.fillText('薪日社区', w / 2, 50)

        // 用户昵称
        ctx.fillStyle = 'rgba(255,255,255,0.9)'
        ctx.font = '14px sans-serif'
        ctx.textAlign = 'left'
        ctx.fillText(p.anonymous_name, padding, 90)

        // 时间
        ctx.fillStyle = 'rgba(255,255,255,0.6)'
        ctx.font = '12px sans-serif'
        ctx.textAlign = 'right'
        const timeStr = formatDate(p.created_at)
        ctx.fillText(timeStr, w - padding, 90)

        // 内容背景 - 调整高度以适应二维码
        ctx.fillStyle = 'rgba(255,255,255,0.15)'
        drawRoundedRect2D(ctx, padding - 8, 110, w - padding * 2 + 16, 180, 12)
        ctx.fill()

        // 内容 - 简单的文字换行处理
        ctx.fillStyle = '#fff'
        ctx.font = '15px sans-serif'
        ctx.textAlign = 'left'
        const content = p.content
        const maxWidth = w - padding * 2
        const lineHeight = 24
        let y = 135

        // 简单的文字换行
        const lines = wrapText(ctx, content, maxWidth)
        const maxLines = 7 // 减少到7行以适应二维码
        for (let i = 0; i < Math.min(lines.length, maxLines); i++) {
          ctx.fillText(lines[i], padding, y)
          y += lineHeight
        }

        if (lines.length > maxLines) {
          ctx.fillText('...', padding, y)
          y += lineHeight
        }

        // 底部统计信息
        const statsY = y + 20
        ctx.fillStyle = 'rgba(255,255,255,0.8)'
        ctx.font = '13px sans-serif'
        ctx.textAlign = 'center'
        ctx.fillText(`❤️ ${p.like_count}   💬 ${p.comment_count}   👁 ${p.view_count}`, w / 2, statsY)

        // 二维码
        if (qrDataUrl) {
          try {
            const qrImage = canvas.createImage()
            await new Promise((imgResolve, imgReject) => {
              qrImage.onload = imgResolve
              qrImage.onerror = imgReject
              qrImage.src = qrDataUrl
            })
            const qrSize = 80
            const qrX = w / 2 - qrSize / 2
            const qrY = 360
            ctx.drawImage(qrImage, qrX, qrY, qrSize, qrSize)

            // 二维码下方文字
            ctx.fillStyle = 'rgba(255,255,255,0.8)'
            ctx.font = '12px sans-serif'
            ctx.textAlign = 'center'
            ctx.fillText('扫码查看详情', w / 2, 455)
          } catch (e) {
            console.error('[poster] Failed to draw QR code:', e)
          }
        }

        // 底部文案
        ctx.fillStyle = 'rgba(255,255,255,0.6)'
        ctx.font = '12px sans-serif'
        ctx.textAlign = 'center'
        ctx.fillText('薪日 PayDay · 记录每一次到账', w / 2, h - 15)

        console.log('[poster] Post canvas draw completed, converting to temp file')

        // 转换为临时文件
        uni.canvasToTempFilePath({
          canvas: canvas,
          x: 0,
          y: 0,
          width: w,
          height: h,
          destWidth: w * 2,
          destHeight: h * 2,
          fileType: 'png',
          success: (res2: any) => {
            console.log('[poster] Canvas to temp file success:', res2.tempFilePath)
            posterUrl.value = res2.tempFilePath
            resolve()
          },
          fail: (e: any) => {
            console.error('[poster] Canvas to temp file failed:', e)
            console.error('[poster] Error details:', JSON.stringify(e))
            posterUrl.value = ''
            reject(new Error('Canvas to temp file failed: ' + JSON.stringify(e)))
          },
        })
      })
  } catch (e) {
    console.error('[poster] Post draw error:', e)
    reject(e)
  }
}

/**
 * Helper function to wrap text into multiple lines
 */
function wrapText(ctx: any, text: string, maxWidth: number): string[] {
  const lines: string[] = []
  let currentLine = ''

  for (let i = 0; i < text.length; i++) {
    const testLine = currentLine + text[i]
    const metrics = ctx.measureText(testLine)
    const testWidth = metrics.width

    if (testWidth > maxWidth && i > 0) {
      lines.push(currentLine)
      currentLine = text[i]
    } else {
      currentLine = testLine
    }
  }
  lines.push(currentLine)
  return lines
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
        id="posterCanvas"
        type="2d"
        class="poster-canvas"
        :style="{ width: '375px', height: '500px' }"
      />

      <!-- Generated Poster Image -->
      <image
        v-if="posterUrl"
        class="poster-image"
        :src="posterUrl"
        @click="previewImage"
      />

      <!-- Actions -->
      <view class="actions-wrapper">
        <view class="actions">
          <button class="btn primary" :loading="saving" @click="saveToAlbum">保存到相册</button>
          <button class="btn secondary" open-type="share">分享给好友</button>
        </view>
      </view>

      <!-- Hint -->
      <view class="hint-wrapper">
        <view class="hint">点击海报可预览大图</view>
      </view>
    </view>
  </view>
</template>

<style scoped lang="scss">
.page {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 24rpx;
  box-sizing: border-box;
  overflow-y: auto;
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
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20rpx 0 40rpx;
}

.poster-canvas {
  position: fixed;
  left: 0;
  top: 0;
  width: 375px;
  height: 500px;
  opacity: 0;
  pointer-events: none;
  z-index: -999;
}

.poster-image {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 600rpx;
  height: 400rpx;
  border-radius: 24rpx;
  box-shadow: 0 16rpx 48rpx rgba(0, 0, 0, 0.2);
  margin-bottom: 32rpx;
  background: #fff;
  display: block;
  object-fit: contain;
}

.actions {
  position: relative;
  z-index: 10;
  display: flex;
  flex-direction: row;
  gap: 20rpx;
  width: 100%;
  max-width: 600rpx;
  justify-content: center;
  margin-bottom: 16rpx;
}

.btn {
  flex: 1;
  padding: 28rpx;
  border-radius: 48rpx;
  font-size: 30rpx;
  font-weight: 600;
  border: none;
  text-align: center;
  position: relative;
  z-index: 10;
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

.actions-wrapper {
  width: 100%;
  max-width: 600rpx;
}

.hint-wrapper {
  width: 100%;
  max-width: 600rpx;
}

.hint {
  position: relative;
  z-index: 10;
  margin-top: 16rpx;
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.6);
  text-align: center;
}
</style>
