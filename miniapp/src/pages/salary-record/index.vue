<script setup lang="ts">
import { ref, onMounted } from 'vue'
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

const formMode = ref<'add' | 'edit'>('add')
const editId = ref<string | null>(null)
const showForm = ref(false)
const form = ref<{
  config_id: string
  amount: string
  payday_date: string
  salary_type: SalaryType
  mood: MoodType
  note: string
}>({
  config_id: '',
  amount: '',
  payday_date: '',
  salary_type: 'normal',
  mood: 'happy',
  note: '',
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
    payday_date: today,
    salary_type: 'normal',
    mood: 'happy',
    note: '',
  }
  showForm.value = true
}

function openEdit(item: SalaryRecord) {
  formMode.value = 'edit'
  editId.value = item.id
  form.value = {
    config_id: item.config_id,
    amount: String(item.amount),
    payday_date: item.payday_date,
    salary_type: item.salary_type as SalaryType,
    mood: item.mood as MoodType,
    note: item.note || '',
  }
  showForm.value = true
}

function closeForm() {
  showForm.value = false
}

async function submitForm() {
  const amount = Number(form.value.amount)
  if (!form.value.config_id) {
    uni.showToast({ title: '请选择发薪日', icon: 'none' })
    return
  }
  if (!form.value.payday_date) {
    uni.showToast({ title: '请选择发薪日期', icon: 'none' })
    return
  }
  if (Number.isNaN(amount) || amount <= 0) {
    uni.showToast({ title: '请输入有效金额（元）', icon: 'none' })
    return
  }
  const payload: SalaryRecordCreate = {
    config_id: form.value.config_id,
    amount,
    payday_date: form.value.payday_date,
    salary_type: form.value.salary_type,
    mood: form.value.mood,
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
      <text class="tip">记录每次到账工资</text>
      <button class="btn-add" @click="openAdd">记一笔</button>
    </view>

    <view v-if="loading" class="loading">加载中...</view>
    <view v-else-if="errMsg" class="err">{{ errMsg }}</view>
    <view v-else-if="recordList.length === 0" class="empty">暂无记录，点击「记一笔」添加</view>
    <view v-else class="list">
      <view v-for="item in recordList" :key="item.id" class="card">
        <view class="card-main">
          <text class="amount">{{ item.amount }} 元</text>
          <text class="meta">{{ item.payday_date }} · {{ jobName(item.config_id) }} · {{ salaryTypeLabel(item.salary_type) }}</text>
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
          <text class="label">实发金额（元）</text>
          <input v-model="form.amount" type="digit" class="input" placeholder="必填" />
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
        <view class="form-item">
          <text class="label">备注（选填）</text>
          <input v-model="form.note" class="input" placeholder="选填" />
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
.tip { display: block; margin-top: 8rpx; color: #666; font-size: 26rpx; }
.btn-add { margin-top: 20rpx; background: #07c160; color: #fff; border: none; border-radius: 8rpx; }
.loading, .err, .empty { padding: 40rpx; text-align: center; color: #666; }
.list { display: flex; flex-direction: column; gap: 20rpx; }
.card { background: #f8f8f8; border-radius: 12rpx; padding: 24rpx; display: flex; justify-content: space-between; align-items: center; }
.card-main { flex: 1; }
.amount { font-weight: 600; font-size: 30rpx; display: block; }
.meta { display: block; margin-top: 8rpx; color: #666; font-size: 26rpx; }
.mood { display: block; margin-top: 4rpx; font-size: 26rpx; color: #07c160; }
.card-actions { display: flex; gap: 16rpx; }
.btn-sm { padding: 8rpx 20rpx; font-size: 24rpx; border: 1rpx solid #ccc; border-radius: 8rpx; background: #fff; }
.btn-sm.danger { border-color: #e0e0e0; color: #e64340; }
.mask { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: flex-end; z-index: 100; }
.form-panel { width: 100%; background: #fff; border-radius: 24rpx 24rpx 0 0; padding: 32rpx; max-height: 80vh; overflow: auto; }
.form-title { font-size: 32rpx; font-weight: 600; display: block; margin-bottom: 24rpx; }
.form-item { margin-bottom: 24rpx; }
.label { display: block; margin-bottom: 8rpx; color: #666; font-size: 26rpx; }
.input, .picker { border: 1rpx solid #e0e0e0; border-radius: 8rpx; padding: 20rpx; font-size: 28rpx; }
.picker { background: #fff; }
.form-actions { display: flex; gap: 20rpx; margin-top: 32rpx; }
.btn-cancel { flex: 1; border: 1rpx solid #ccc; border-radius: 8rpx; background: #fff; }
.btn-ok { flex: 1; background: #07c160; color: #fff; border: none; border-radius: 8rpx; }
</style>
