<script setup lang="ts">
import { ref, onMounted, computed, getCurrentInstance, nextTick } from 'vue'
import { onLoad, onShareAppMessage } from '@dcloudio/uni-app'
import { listPayday } from '@/api/payday'
import { getSalary, listSalary } from '@/api/salary'
import { getPostDetail } from '@/api/post'
import { formatDate } from '@/utils/format'
import { baseURL, request } from '@/utils/request'

// 获取当前组件实例，用于 Canvas 查询
const instance = getCurrentInstance()

const recordId = ref('')
const postId = ref('')
const record = ref(null)
const post = ref(null)
const paydayList = ref([])
const loading = ref(true)
const errMsg = ref('')
const saving = ref(false)
const posterUrl = ref('')
const posterType = ref('salary') // 'salary' for salary records, 'post' for posts

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
  console.log('[poster] loadData called, posterType:', posterType.value)
  loading.value = true
  errMsg.value = ''
  try {
    if (posterType.value === 'post') {
      // Load post data
      console.log('[poster] Loading post data, postId:', postId.value)
      await fetchPost()
      console.log('[poster] Post loaded:', post.value)
      if (post.value) {
        // 先关闭 loading，让 DOM 渲染
        loading.value = false
        // 等待 Vue nextTick 确保 DOM 更新
        await nextTick()
        // 再等待 canvas 元素渲染完成（type="2d" 需要更长时间）
        await new Promise(resolve => setTimeout(resolve, 1500))
        console.log('[poster] About to draw poster')
        await drawPoster()
      } else {
        console.log('[poster] No post data found')
        loading.value = false
      }
    } else {
      // Load salary record data
      console.log('[poster] Loading salary record data')
      const [paydayRes, recordData] = await Promise.all([listPayday(), fetchRecord()])
      console.log('[poster] Payday configs:', paydayRes, 'Record:', recordData)
      paydayList.value = paydayRes || []
      record.value = recordData
      if (record.value) {
        console.log('[poster] Record data loaded, about to draw poster')
        // 先关闭 loading，让 DOM 渲染
        loading.value = false
        // 等待 Vue nextTick 确保 DOM 更新
        await nextTick()
        // 再等待 canvas 元素渲染完成（type="2d" 需要更长时间）
        await new Promise(resolve => setTimeout(resolve, 1500))
        console.log('[poster] About to draw poster')
        await drawPoster()
        console.log('[poster] Draw poster completed')
      } else {
        console.log('[poster] No record data found')
        loading.value = false
      }
    }
  } catch (e: any) {
    console.error('[poster] Load failed:', e)
    console.error('[poster] Error stack:', e?.stack)
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
 * 使用后端新方案：参数映射系统
 * 1. 创建映射获取短码
 * 2. 使用短码生成小程序码
 */
async function generateQRCodeUrl(id: string, type: 'salary' | 'post' = 'salary'): Promise<string> {
  try {
    console.log('[poster] Generating QR code for id:', id, 'type:', type)
    // 使用一体化接口：创建映射 + 生成二维码
    // 开发环境使用 pages/index/index（因为 poster 页面未在微信发布）
    const response: any = await request({
      url: '/api/v1/qrcode/wxa/generate?width=200',
      method: 'POST',
      data: {
        page: 'pages/index/index',
        params:
          type === 'salary'
            ? { recordId: id, targetPage: 'pages/poster/index' }
            : { postId: id, targetPage: 'pages/poster/index' },
      },
      noAuth: true, // 二维码生成不需要认证
    })

    console.log('[poster] QR code API response:', response)

    // request 工具函数已经解析了响应数据，直接访问即可
    if (response && response.base64) {
      console.log('[poster] QR code generated successfully, type:', response.type)
      const base64Data = response.base64
      console.log('[poster] Base64 data length:', base64Data.length)
      console.log('[poster] Base64 data prefix:', base64Data.substring(0, 50))
      return base64Data
    } else {
      console.error('[poster] QR code generation failed - invalid response:', response)
      throw new Error('Failed to generate QR code')
    }
  } catch (e) {
    console.error('[poster] QR code generation error:', e)
    throw e
  }
}

/**
 * Draw salary record poster - using new Canvas 2D API
 */
function drawSalaryPoster(): Promise<void> {
  const r = record.value
  if (!r) return Promise.resolve()

  return new Promise((resolve, reject) => {
    // 先生成二维码
    generateQRCodeUrl(r.id, 'salary')
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
  record: SalaryRecord,
  qrDataUrl: string | null,
  resolve: (value: void | PromiseLike<void>) => void,
  reject: (reason?: any) => void
): void {
  try {
    console.log('[poster] Creating selector query')
    // 不使用 .in()，在整个页面范围内查询
    const query = uni.createSelectorQuery()
    query
      .select('#posterCanvas')
      .fields({ node: true, size: true })
      .exec(async res => {
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

        // 判断工资类型
        const isBonus = record.salary_type === 'bonus'
        const titleText = isBonus ? '年终奖' : '发薪日'
        const gradientStart = isBonus ? '#fdcb6e' : '#667eea'
        const gradientEnd = isBonus ? '#f39c12' : '#764ba2'

        console.log(
          '[poster] Starting canvas draw with Canvas 2D API, size:',
          w,
          'x',
          h,
          ', dpr:',
          dpr,
          ', type:',
          record.salary_type
        )

        // 清空画布
        ctx.clearRect(0, 0, w, h)

        // 背景 - 渐变色（奖金用金色，工资用紫色）
        const gradient = ctx.createLinearGradient(0, 0, 0, h)
        gradient.addColorStop(0, gradientStart)
        gradient.addColorStop(1, gradientEnd)
        ctx.fillStyle = gradient
        ctx.fillRect(0, 0, w, h)

        // 顶部装饰条
        ctx.fillStyle = 'rgba(255,255,255,0.2)'
        ctx.fillRect(0, 0, w, 6)

        // 标题
        ctx.fillStyle = '#fff'
        ctx.font = '16px sans-serif'
        ctx.textAlign = 'center'
        ctx.fillText(titleText, w / 2, 50)

        // 金额背景
        ctx.fillStyle = 'rgba(255,255,255,0.15)'
        drawRoundedRect2D(ctx, padding - 12, 80, w - padding * 2 + 24, 100, 16)
        ctx.fill()

        // 金额
        ctx.fillStyle = '#fff'
        ctx.font = '48px sans-serif'
        ctx.textAlign = 'center'
        ctx.fillText(`¥${record.amount}`, w / 2, 145)

        // 发薪日期
        ctx.fillStyle = 'rgba(255,255,255,0.9)'
        ctx.font = '14px sans-serif'
        ctx.textAlign = 'center'
        ctx.fillText(record.payday_date, w / 2, 185)

        // 工作名
        ctx.fillStyle = 'rgba(255,255,255,0.8)'
        ctx.font = '13px sans-serif'
        ctx.textAlign = 'center'
        ctx.fillText(jobName.value(record.config_id), w / 2, 210)

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
        ctx.fillText(moodText[record.mood] || record.mood, w / 2, 282)

        // 二维码
        if (qrDataUrl) {
          try {
            console.log('[poster] Drawing QR code, qrDataUrl length:', qrDataUrl.length)
            console.log('[poster] QR code data prefix:', qrDataUrl.substring(0, 50))
            const qrImage = canvas.createImage()
            await new Promise((imgResolve, imgReject) => {
              console.log('[poster] Setting QR image source...')
              qrImage.onload = () => {
                console.log('[poster] QR image loaded successfully')
                imgResolve()
              }
              qrImage.onerror = err => {
                console.error('[poster] QR image load error:', err)
                imgReject(err)
              }
              qrImage.src = qrDataUrl
            })
            console.log('[poster] Drawing QR image to canvas...')
            const qrSize = 80
            const qrX = w / 2 - qrSize / 2
            const qrY = 310
            ctx.drawImage(qrImage, qrX, qrY, qrSize, qrSize)
            console.log('[poster] QR code drawn successfully')

            // 二维码下方文字
            ctx.fillStyle = 'rgba(255,255,255,0.8)'
            ctx.font = '12px sans-serif'
            ctx.textAlign = 'center'
            ctx.fillText('扫码查看详情', w / 2, 405)
          } catch (e) {
            console.error('[poster] Failed to draw QR code:', e)
            console.error('[poster] QR code error stack:', e?.stack)
          }
        } else {
          console.log('[poster] No QR code data to draw')
        }

        // 底部文案（根据类型区分）
        ctx.fillStyle = 'rgba(255,255,255,0.6)'
        ctx.font = '12px sans-serif'
        ctx.textAlign = 'center'
        const footerText = isBonus ? '薪日 PayDay · 记录年终奖时刻' : '薪日 PayDay · 记录每一次到账'
        ctx.fillText(footerText, w / 2, h - 15)

        console.log('[poster] Canvas draw completed, converting to temp file')

        // 转换为临时文件
        uni.canvasToTempFilePath(
          {
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
              console.log('[poster] posterUrl.value set to:', posterUrl.value)
              console.log('[poster] posterUrl.value type:', typeof posterUrl.value)
              console.log('[poster] posterUrl.value length:', posterUrl.value?.length)
              resolve()
            },
            fail: (e: any) => {
              console.error('[poster] Canvas to temp file failed:', e)
              console.error('[poster] Error details:', JSON.stringify(e))
              posterUrl.value = ''
              // 显示错误给用户
              errMsg.value = '生成海报失败: ' + (e?.errMsg || '未知错误')
              reject(new Error('Canvas to temp file failed: ' + JSON.stringify(e)))
            },
          },
          instance
        )
      })
  } catch (e) {
    console.error('[poster] Draw error:', e)
    errMsg.value = '绘制海报失败: ' + (e?.message || '未知错误')
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
    generateQRCodeUrl(p.id, 'post')
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
  post: Post,
  qrDataUrl: string | null,
  resolve: (value: void | PromiseLike<void>) => void,
  reject: (reason?: any) => void
): void {
  try {
    console.log('[poster] Creating selector query for post')
    // 不使用 .in()，在整个页面范围内查询
    const query = uni.createSelectorQuery()
    query
      .select('#posterCanvas')
      .fields({ node: true, size: true })
      .exec(async res => {
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

        console.log(
          '[poster] Starting post canvas draw with Canvas 2D API, size:',
          w,
          'x',
          h,
          ', dpr:',
          dpr
        )

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
        ctx.fillText(
          `❤️ ${p.like_count}   💬 ${p.comment_count}   👁 ${p.view_count}`,
          w / 2,
          statsY
        )

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
        uni.canvasToTempFilePath(
          {
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
              console.log('[poster] posterUrl.value set to:', posterUrl.value)
              console.log('[poster] posterUrl.value type:', typeof posterUrl.value)
              console.log('[poster] posterUrl.value length:', posterUrl.value?.length)
              resolve()
            },
            fail: (e: any) => {
              console.error('[poster] Canvas to temp file failed:', e)
              console.error('[poster] Error details:', JSON.stringify(e))
              posterUrl.value = ''
              // 显示错误给用户
              errMsg.value = '生成海报失败: ' + (e?.errMsg || '未知错误')
              reject(new Error('Canvas to temp file failed: ' + JSON.stringify(e)))
            },
          },
          instance
        )
      })
  } catch (e) {
    console.error('[poster] Post draw error:', e)
    errMsg.value = '绘制海报失败: ' + (e?.message || '未知错误')
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
  console.log(
    '[poster] Component mounted, posterType:',
    posterType.value,
    'recordId:',
    recordId.value,
    'postId:',
    postId.value
  )
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
        mode="aspectFill"
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
  background: $gradient-brand;
  padding: $spacing-md;
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
  border: 4rpx solid var(--bg-glass-subtle);
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
  margin-top: $spacing-lg;
  font-size: $font-size-base;
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
  margin-bottom: $spacing-md;
}

.error-text {
  font-size: $font-size-base;
  color: #fff;
  margin-bottom: $spacing-2xl;
}

.retry-btn {
  padding: $spacing-md $spacing-2xl;
  background: var(--bg-glass-subtle);
  border-radius: 48rpx;
  color: #fff;
  font-size: $font-size-base;
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
  margin-bottom: $spacing-md;
}

.empty-text {
  font-size: $font-size-lg;
  color: #fff;
  font-weight: $font-weight-semibold;
  margin-bottom: $spacing-xs;
}

.empty-hint {
  font-size: $font-size-sm;
  color: var(--bg-glass-standard);
}

// Content
.content {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: $spacing-md 0 $spacing-2xl;
  overflow: visible;
}

.poster-canvas {
  position: absolute;
  left: -9999px;
  top: -9999px;
  width: 375px;
  height: 500px;
  opacity: 0;
  pointer-events: none;
  visibility: hidden;
}

.poster-image {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 600rpx;
  height: 800rpx; /* 固定高度，基于 375:500 比例 */
  border-radius: $radius-xl;
  box-shadow: $shadow-lg;
  margin-bottom: $spacing-2xl;
  background: #fff;
  display: block;
}

.actions {
  position: relative;
  z-index: 999;
  display: flex;
  flex-direction: row;
  gap: $spacing-md;
  width: 100%;
  max-width: 600rpx;
  justify-content: center;
  margin-bottom: $spacing-md;
}

.btn {
  flex: 1;
  padding: $spacing-lg;
  border-radius: 48rpx;
  font-size: $font-size-lg;
  font-weight: $font-weight-semibold;
  border: none;
  text-align: center;
  position: relative;
  z-index: 999;
}

.btn.primary {
  background: #fff;
  color: $brand-primary;
  box-shadow: $shadow-md;
}

.btn.secondary {
  background: var(--bg-glass-subtle);
  color: #fff;
}

.actions-wrapper {
  width: 100%;
  max-width: 600rpx;
  position: relative;
  z-index: 999;
  flex-shrink: 0;
  padding: $spacing-md 0;
}

.hint-wrapper {
  width: 100%;
  max-width: 600rpx;
  position: relative;
  z-index: 999;
  flex-shrink: 0;
  padding: $spacing-xs 0 $spacing-md;
}

.hint {
  position: relative;
  z-index: 999;
  font-size: $font-size-xs;
  color: var(--bg-glass-standard);
  text-align: center;
}
</style>
