<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { listPayday, type PaydayConfig } from '@/api/payday'
import {
  listSalary,
  createSalary,
  updateSalary,
  deleteSalary,
  type SalaryRecord,
  type SalaryRecordCreate,
  type SalaryType,
  type MoodType,
} from '@/api/salary'

const paydayList = ref<PaydayConfig[]>([])
const recordList = ref<SalaryRecord[]>([])
const loading = ref(false)
const errMsg = ref('')

const salaryTypeOptions: { value: SalaryType; label: string }[] = [
  { value: 'normal', label: '工资' },
  { value: 'bonus', label: '奖金' },
  { value: 'allowance', label: '补贴' },
  { value: 'other', label: '其他' },
]
const moodOptions: { value: MoodType; label: string }[] = [
  { value: 'happy', label: '开心' },
  { value: 'relief', label: '续命' },
  { value: 'sad', label: '崩溃' },
  { value: 'expect', label: '期待' },
  { value: 'angry', label: '暴躁' },
]
const sourceOptions = ['公司', '工厂', '兼职', '其他']

const formMode = ref<'add' | 'edit'>('add')
const editId = ref<string | null>(null)
const showForm = ref(false)
const showAdvanced = ref(false)
const form = ref<{
  config_id: string
  amount: string
  before_tax: string
  tax_amount: string
  payday_date: string
  salary_type: SalaryType
  mood: MoodType
  salary_source: string
  delay_days: string
  delay_reason: string
  note: string
}>({
  config_id: '',
  amount: '',
  before_tax: '',
  tax_amount: '',
  payday_date: '',
  salary_type: 'normal',
  mood: 'happy',
  salary_source: '',
  delay_days: '',
  delay_reason: '',
  note: '',
})

// 计算实际金额是否与税前扣税匹配
const amountMatchWarning = computed(() => {
  const pre = Number(form.value.before_tax) || 0
  const tax = Number(form.value.tax_amount) || 0
  const actual = Number(form.value.amount) || 0
  if (pre > 0 && tax > 0) {
    const expected = pre - tax
    if (Math.abs(expected - actual) > 0.01) {
      return `税前¥${pre} - 扣税¥${tax} = ¥${expected}，与实发¥${actual}不一致`
    }
  }
  return ''
})

async function loadPaydayList() {
  try {
    const res = await listPayday()
    paydayList.value = res || []
    if (paydayList.value.length && !form.value.config_id) form.value.config_id = paydayList.value[0].id
  } catch {
    paydayList.value = []
  }
}

async function loadRecordList() {
  loading.value = true
  errMsg.value = ''
  try {
    const res = await listSalary()
    recordList.value = Array.isArray(res) ? res : []
  } catch (e: any) {
    errMsg.value = e?.message || '加载失败'
    recordList.value = []
  } finally {
    loading.value = false
  }
}

function openAdd() {
  formMode.value = 'add'
  editId.value = null
  const today = new Date().toISOString().slice(0, 10)
  form.value = {
    config_id: paydayList.value[0]?.id || '',
    amount: '',
    before_tax: '',
    tax_amount: '',
    payday_date: today,
    salary_type: 'normal',
    mood: 'happy',
    salary_source: '',
    delay_days: '',
    delay_reason: '',
    note: '',
  }
  showAdvanced.value = false
  showForm.value = true
}

function openEdit(item: SalaryRecord) {
  formMode.value = 'edit'
  editId.value = item.id
  form.value = {
    config_id: item.config_id,
    amount: String(item.amount),
    before_tax: item.before_tax ? String(item.before_tax) : '',
    tax_amount: item.tax_amount ? String(item.tax_amount) : '',
    payday_date: item.payday_date,
    salary_type: item.salary_type as SalaryType,
    mood: item.mood as MoodType,
    salary_source: item.salary_source || '',
    delay_days: item.delay_days ? String(item.delay_days) : '',
    delay_reason: item.delay_reason || '',
    note: item.note || '',
  }
  showAdvanced.value = !!(item.before_tax || item.tax_amount || item.salary_source || item.delay_days)
  showForm.value = true
}

function closeForm() {
  showForm.value = false
}

async function submitForm() {
  const amount = Number(form.value.amount)
  const before_tax = form.value.before_tax ? Number(form.value.before_tax) : null
  const tax_amount = form.value.tax_amount ? Number(form.value.tax_amount) : null
  const delay_days = form.value.delay_days ? Number(form.value.delay_days) : null

  if (!form.value.config_id) {
    uni.showToast({ title: '请选择发薪日', icon: 'none' })
    return
  }
  if (!form.value.payday_date) {
    uni.showToast({ title: '请选择发薪日期', icon: 'none' })
    return
  }
  if (Number.isNaN(amount) || amount <= 0) {
    uni.showToast({ title: '请输入有效实发金额（元）', icon: 'none' })
    return
  }
  if (before_tax !== null && before_tax <= 0) {
    uni.showToast({ title: '税前金额必须大于0', icon: 'none' })
    return
  }
  if (tax_amount !== null && tax_amount < 0) {
    uni.showToast({ title: '扣税金额不能为负数', icon: 'none' })
    return
  }
  if (delay_days !== null && delay_days < 0) {
    uni.showToast({ title: '延迟天数不能为负数', icon: 'none' })
    return
  }
  if (delay_days !== null && delay_days > 0 && !form.value.delay_reason?.trim()) {
    uni.showToast({ title: '延迟到账请填写原因', icon: 'none' })
    return
  }

  const payload: SalaryRecordCreate = {
    config_id: form.value.config_id,
    amount,
    before_tax,
    tax_amount,
    payday_date: form.value.payday_date,
    salary_type: form.value.salary_type,
    mood: form.value.mood,
    salary_source: form.value.salary_source || null,
    delay_days,
    delay_reason: form.value.delay_reason || null,
    note: form.value.note.trim() || undefined,
  }
  try {
    if (formMode.value === 'add') {
      await createSalary(payload)
      uni.showToast({ title: '记录成功' })
    } else if (editId.value) {
      await updateSalary(editId.value, payload)
      uni.showToast({ title: '保存成功' })
    }
    closeForm()
    await loadRecordList()
  } catch (e: any) {
    uni.showToast({ title: e?.message || '操作失败', icon: 'none' })
  }
}

function goPoster(id: string) {
  uni.navigateTo({ url: `/pages/poster/index?recordId=${id}` })
}

function doDelete(item: SalaryRecord) {
  uni.showModal({
    title: '确认删除',
    content: `删除这条工资记录？`,
    success: async (res) => {
      if (!res.confirm) return
      try {
        await deleteSalary(item.id)
        uni.showToast({ title: '已删除' })
        await loadRecordList()
      } catch (e: any) {
        uni.showToast({ title: e?.message || '删除失败', icon: 'none' })
      }
    },
  })
}

function salaryTypeLabel(v: string) {
  return salaryTypeOptions.find((o) => o.value === v)?.label ?? v
}
function moodLabel(v: string) {
  return moodOptions.find((o) => o.value === v)?.label ?? v
}
function jobName(configId: string) {
  return paydayList.value.find((c) => c.id === configId)?.job_name ?? configId
}

onMounted(async () => {
  await loadPaydayList()
  await loadRecordList()
})
</script>

<template>
  <view class="page">
    <view class="head">
      <text class="title">工资记录</text>
      <text class="tip">记录每次到账工资，支持税前扣税统计</text>
      <button class="btn-add" @click="openAdd">记一笔</button>
    </view>

    <view v-if="loading" class="loading">加载中...</view>
    <view v-else-if="errMsg" class="err">{{ errMsg }}</view>
    <view v-else-if="recordList.length === 0" class="empty">暂无记录，点击「记一笔」添加</view>
    <view v-else class="list">
      <view v-for="item in recordList" :key="item.id" class="card">
        <view class="card-main">
          <view class="amount-row">
            <text class="amount">{{ item.amount }} 元</text>
            <text v-if="item.delay_days" class="delay-badge">延迟{{ item.delay_days }}天</text>
          </view>
          <text class="meta">{{ item.payday_date }} · {{ jobName(item.config_id) }} · {{ salaryTypeLabel(item.salary_type) }}</text>
          <view v-if="item.before_tax || item.salary_source" class="detail-row">
            <text v-if="item.before_tax" class="detail-item">税前: ¥{{ item.before_tax }}</text>
            <text v-if="item.tax_amount" class="detail-item">扣税: ¥{{ item.tax_amount }}</text>
            <text v-if="item.salary_source" class="detail-item source">{{ item.salary_source }}</text>
          </view>
          <text class="mood">{{ moodLabel(item.mood) }}</text>
        </view>
        <view class="card-actions">
          <button class="btn-sm" @click="openEdit(item)">编辑</button>
          <button class="btn-sm" @click="goPoster(item.id)">海报</button>
          <button class="btn-sm danger" @click="doDelete(item)">删除</button>
        </view>
      </view>
    </view>

    <view v-if="showForm" class="mask" @click="closeForm">
      <view class="form-panel" @click.stop>
        <text class="form-title">{{ formMode === 'add' ? '记一笔' : '编辑记录' }}</text>

        <!-- 基础信息 -->
        <view class="form-section">
          <text class="section-title">基础信息</text>
          <view class="form-item">
            <text class="label">关联发薪日</text>
            <picker
              :value="paydayList.findIndex((c) => c.id === form.config_id)"
              :range="paydayList"
              range-key="job_name"
              @change="(e: any) => (form.config_id = paydayList[e.detail.value]?.id || '')"
            >
              <view class="picker">{{ jobName(form.config_id) || '请选择' }}</view>
            </picker>
          </view>
          <view class="form-item">
            <text class="label required">实发金额（元）</text>
            <input v-model="form.amount" type="digit" class="input" placeholder="必填，实际到账金额" />
          </view>
          <view class="form-item">
            <text class="label">发薪日期</text>
            <picker mode="date" :value="form.payday_date" @change="(e: any) => (form.payday_date = e.detail.value)">
              <view class="picker">{{ form.payday_date || '请选择' }}</view>
            </picker>
          </view>
          <view class="form-item">
            <text class="label">类型</text>
            <picker
              :value="salaryTypeOptions.findIndex((o) => o.value === form.salary_type)"
              :range="salaryTypeOptions"
              range-key="label"
              @change="(e: any) => (form.salary_type = salaryTypeOptions[e.detail.value]?.value ?? 'normal')"
            >
              <view class="picker">{{ salaryTypeLabel(form.salary_type) }}</view>
            </picker>
          </view>
          <view class="form-item">
            <text class="label">心情</text>
            <picker
              :value="moodOptions.findIndex((o) => o.value === form.mood)"
              :range="moodOptions"
              range-key="label"
              @change="(e: any) => (form.mood = moodOptions[e.detail.value]?.value ?? 'happy')"
            >
              <view class="picker">{{ moodLabel(form.mood) }}</view>
            </picker>
          </view>
        </view>

        <!-- 高级选项 -->
        <view class="form-section">
          <view class="section-header" @click="showAdvanced = !showAdvanced">
            <text class="section-title">高级选项</text>
            <text class="expand-icon">{{ showAdvanced ? '▼' : '▶' }}</text>
          </view>
          <view v-if="showAdvanced" class="advanced-content">
            <view class="form-item">
              <text class="label">税前金额（元）</text>
              <input v-model="form.before_tax" type="digit" class="input" placeholder="选填" />
            </view>
            <view class="form-item">
              <text class="label">扣税金额（元）</text>
              <input v-model="form.tax_amount" type="digit" class="input" placeholder="选填" />
            </view>
            <view v-if="amountMatchWarning" class="warning">
              <text class="warning-icon">⚠️</text>
              <text class="warning-text">{{ amountMatchWarning }}</text>
            </view>
            <view class="form-item">
              <text class="label">工资来源</text>
              <picker
                :value="sourceOptions.indexOf(form.salary_source)"
                :range="sourceOptions"
                @change="(e: any) => (form.salary_source = sourceOptions[e.detail.value] ?? '')"
              >
                <view class="picker">{{ form.salary_source || '请选择' }}</view>
              </picker>
            </view>
            <view class="form-item">
              <text class="label">延迟天数</text>
              <input v-model="form.delay_days" type="number" class="input" placeholder="选填，如延迟到账" />
            </view>
            <view v-if="form.delay_days && Number(form.delay_days) > 0" class="form-item">
              <text class="label required">延迟原因</text>
              <input v-model="form.delay_reason" class="input" placeholder="延迟到账必填" />
            </view>
          </view>
        </view>

        <!-- 备注 -->
        <view class="form-section">
          <text class="section-title">备注</text>
          <view class="form-item">
            <textarea v-model="form.note" class="textarea" placeholder="选填，记录心情或其他信息" maxlength="200" />
            <text class="char-count">{{ form.note.length }}/200</text>
          </view>
        </view>

        <view class="form-actions">
          <button class="btn-cancel" @click="closeForm">取消</button>
          <button class="btn-ok" @click="submitForm">保存</button>
        </view>
      </view>
    </view>
  </view>
</template>

<style scoped>
.page { padding: 24rpx; min-height: 100vh; }
.head { margin-bottom: 24rpx; }
.title { font-size: 36rpx; font-weight: 600; display: block; }
.tip { display: block; margin-top: 8rpx; color: #666; font-size: 26rpx; line-height: 1.5; }
.btn-add { margin-top: 20rpx; background: #07c160; color: #fff; border: none; border-radius: 8rpx; }
.loading, .err, .empty { padding: 40rpx; text-align: center; color: #666; }
.list { display: flex; flex-direction: column; gap: 20rpx; }
.card { background: #f8f8f8; border-radius: 12rpx; padding: 24rpx; display: flex; justify-content: space-between; align-items: center; }
.card-main { flex: 1; }
.amount-row { display: flex; align-items: center; gap: 16rpx; }
.amount { font-weight: 600; font-size: 30rpx; display: block; }
.delay-badge { background: #ff6b6b; color: #fff; font-size: 20rpx; padding: 4rpx 12rpx; border-radius: 8rpx; }
.meta { display: block; margin-top: 8rpx; color: #666; font-size: 26rpx; }
.detail-row { display: flex; flex-wrap: wrap; gap: 16rpx; margin-top: 8rpx; }
.detail-item { font-size: 24rpx; color: #999; background: #fff; padding: 4rpx 12rpx; border-radius: 6rpx; }
.detail-item.source { color: #07c160; }
.mood { display: block; margin-top: 4rpx; font-size: 26rpx; color: #07c160; }
.card-actions { display: flex; gap: 16rpx; }
.btn-sm { padding: 8rpx 20rpx; font-size: 24rpx; border: 1rpx solid #ccc; border-radius: 8rpx; background: #fff; }
.btn-sm.danger { border-color: #e0e0e0; color: #e64340; }
.mask { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: flex-end; z-index: 100; }
.form-panel { width: 100%; background: #fff; border-radius: 24rpx 24rpx 0 0; padding: 32rpx; max-height: 80vh; overflow: auto; }
.form-title { font-size: 32rpx; font-weight: 600; display: block; margin-bottom: 24rpx; }
.form-section { margin-bottom: 24rpx; }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16rpx; }
.section-title { font-size: 28rpx; font-weight: 500; color: #333; }
.expand-icon { font-size: 24rpx; color: #999; }
.advanced-content { animation: slideDown 0.3s ease; }
@keyframes slideDown {
  from { opacity: 0; transform: translateY(-10rpx); }
  to { opacity: 1; transform: translateY(0); }
}
.form-item { margin-bottom: 20rpx; position: relative; }
.label { display: block; margin-bottom: 8rpx; color: #666; font-size: 26rpx; }
.label.required::after { content: '*'; color: #e64340; margin-left: 4rpx; }
.input, .picker, .textarea { border: 1rpx solid #e0e0e0; border-radius: 8rpx; padding: 20rpx; font-size: 28rpx; }
.picker { background: #fff; display: flex; align-items: center; justify-content: space-between; }
.textarea { min-height: 120rpx; resize: none; }
.char-count { text-align: right; font-size: 22rpx; color: #999; margin-top: 8rpx; display: block; }
.warning { display: flex; align-items: center; gap: 12rpx; padding: 16rpx; background: #fff3cd; border-radius: 8rpx; margin-top: 16rpx; }
.warning-icon { font-size: 28rpx; }
.warning-text { font-size: 24rpx; color: #856404; flex: 1; }
.form-actions { display: flex; gap: 20rpx; margin-top: 32rpx; }
.btn-cancel { flex: 1; border: 1rpx solid #ccc; border-radius: 8rpx; background: #fff; }
.btn-ok { flex: 1; background: #07c160; color: #fff; border: none; border-radius: 8rpx; }
</style>
