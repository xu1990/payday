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
const tempFilePath = ref('')

const moodText: Record<MoodType, string> = {
  happy: '开心',
  relief: '续命',
  sad: '崩溃',
  angry: '暴躁',
  expect: '期待',
}

const jobName = computed(() => (configId: string) => paydayList.value.find((c) => c.id === configId)?.job_name || '工资')

onLoad((query: any) => {
  recordId.value = query?.recordId || ''
})

onShareAppMessage(() => ({
  title: '发薪海报',
  path: recordId.value ? `/pages/poster/index?recordId=${recordId.value}` : '/pages/poster/index',
}))

async function loadData() {
  loading.value = true
  errMsg.value = ''
  try {
    const [paydayRes, recordData] = await Promise.all([listPayday(), fetchRecord()])
    paydayList.value = paydayRes || []
    record.value = recordData
    if (record.value) await drawPoster()
  } catch (e: any) {
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

function drawPoster(): Promise<void> {
  const r = record.value
  if (!r) return Promise.resolve()

  return new Promise((resolve, reject) => {
    const ctx = uni.createCanvasContext('posterCanvas')
    const w = 375
    const h = 500
    const padding = 24
    const lineH = 28

    // 背景
    ctx.setFillStyle('#1a1a2e')
    ctx.fillRect(0, 0, w, h)

    // 顶部装饰条
    ctx.setFillStyle('#07c160')
    ctx.fillRect(0, 0, w, 6)

    // 标题
    ctx.setFillStyle('#fff')
    ctx.setFontSize(16)
    ctx.fillText('发薪日', padding, 50)

    // 金额
    ctx.setFillStyle('#07c160')
    ctx.setFontSize(42)
    ctx.setFontWeight('bold')
    ctx.fillText(`¥ ${r.amount}`, padding, 130)
    ctx.setFontWeight('normal')

    // 发薪日期、工作名
    ctx.setFillStyle('rgba(255,255,255,0.85)')
    ctx.setFontSize(14)
    ctx.fillText(`${r.payday_date} · ${jobName.value(r.config_id)}`, padding, 180)

    // 心情
    ctx.setFillStyle('rgba(255,255,255,0.7)')
    ctx.setFontSize(13)
    ctx.fillText(moodText[r.mood] || r.mood, padding, 180 + lineH)

    // 底部文案
    ctx.setFillStyle('rgba(255,255,255,0.5)')
    ctx.setFontSize(12)
    ctx.fillText('薪日 PayDay · 记录每一次到账', padding, h - 30)

    ctx.draw(false, () => {
      setTimeout(() => {
        uni.canvasToTempFilePath({
          canvasId: 'posterCanvas',
          width: w,
          height: h,
          destWidth: w * 2,
          destHeight: h * 2,
          success: (res) => {
            tempFilePath.value = res.tempFilePath
            resolve()
          },
          fail: (e) => reject(e),
        })
      }, 350)
    })
  })
}

async function saveToAlbum() {
  if (!tempFilePath.value) {
    uni.showToast({ title: '请先生成海报', icon: 'none' })
    return
  }
  saving.value = true
  try {
    await uni.authorize({ scope: 'scope.writePhotosAlbum' }).catch(() => ({}))
    await uni.saveImageToPhotosAlbum({ filePath: tempFilePath.value })
    uni.showToast({ title: '已保存到相册' })
  } catch (e: any) {
    if (e?.errMsg?.includes('auth deny')) {
      uni.showModal({
        title: '提示',
        content: '需要相册权限才能保存，请在设置中开启',
        confirmText: '去设置',
        success: (res) => res.confirm && uni.openSetting(),
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

onMounted(() => {
  loadData()
})
</script>

<template>
  <view class="page">
    <view v-if="loading" class="loading">加载中...</view>
    <view v-else-if="errMsg" class="err">{{ errMsg }}</view>
    <view v-else-if="!record" class="empty">暂无工资记录，先去记一笔吧</view>
    <view v-else class="content">
      <canvas
        canvas-id="posterCanvas"
        class="canvas"
        :style="{ width: '375px', height: '500px' }"
      />
      <view class="actions">
        <button class="btn primary" :loading="saving" @click="saveToAlbum">保存到相册</button>
        <button class="btn" open-type="share">分享给好友</button>
      </view>
    </view>
  </view>
</template>

<style scoped>
.page { min-height: 100vh; background: #111; padding: 24rpx; box-sizing: border-box; }
.loading, .err, .empty { padding: 80rpx 0; text-align: center; color: #999; }
.content { display: flex; flex-direction: column; align-items: center; }
.canvas { background: #1a1a2e; border-radius: 16rpx; margin-bottom: 32rpx; }
.actions { display: flex; flex-direction: column; gap: 20rpx; width: 100%; max-width: 400rpx; }
.btn { padding: 24rpx; border-radius: 12rpx; font-size: 30rpx; }
.btn.primary { background: #07c160; color: #fff; border: none; }
.btn:not(.primary) { background: #333; color: #fff; border: none; }
</style>
