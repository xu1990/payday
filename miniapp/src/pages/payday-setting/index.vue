<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  listPayday,
  createPayday,
  updatePayday,
  deletePayday,
  type PaydayConfig,
  type PaydayConfigCreate,
} from '@/api/payday'

const list = ref<PaydayConfig[]>([])
const loading = ref(false)
const errMsg = ref('')

// 表单（新增/编辑）
const formMode = ref<'add' | 'edit'>('add')
const editId = ref<string | null>(null)
const showForm = ref(false)
/** 表单里预估工资用「元」展示和输入，提交时转为分 */
const form = ref<{
  job_name: string
  payday: number
  calendar_type: 'solar' | 'lunar'
  estimated_salaryYuan: number | ''
  is_active: number
}>({
  job_name: '',
  payday: 15,
  calendar_type: 'solar',
  estimated_salaryYuan: '',
  is_active: 1,
})

const calendarOptions = [
  { value: 'solar', label: '公历' },
  { value: 'lunar', label: '农历' },
]
const paydayOptions = Array.from({ length: 31 }, (_, i) => ({ value: i + 1, label: `${i + 1} 日` }))

async function loadList() {
  loading.value = true
  errMsg.value = ''
  try {
    const res = await listPayday()
    list.value = res || []
  } catch (e: any) {
    errMsg.value = e?.message || '加载失败'
    list.value = []
  } finally {
    loading.value = false
  }
}

function openAdd() {
  formMode.value = 'add'
  editId.value = null
  form.value = {
    job_name: '',
    payday: 15,
    calendar_type: 'solar',
    estimated_salaryYuan: '',
    is_active: 1,
  }
  showForm.value = true
}

function openEdit(item: PaydayConfig) {
  formMode.value = 'edit'
  editId.value = item.id
  form.value = {
    job_name: item.job_name,
    payday: item.payday,
    calendar_type: item.calendar_type as 'solar' | 'lunar',
    estimated_salaryYuan: item.estimated_salary != null ? item.estimated_salary / 100 : '',
    is_active: item.is_active,
  }
  showForm.value = true
}

function closeForm() {
  showForm.value = false
}

async function submitForm() {
  if (!form.value.job_name.trim()) {
    uni.showToast({ title: '请填写工作名称', icon: 'none' })
    return
  }
  const yuan = form.value.estimated_salaryYuan
  const payload: PaydayConfigCreate = {
    job_name: form.value.job_name.trim(),
    payday: form.value.payday,
    calendar_type: form.value.calendar_type,
    estimated_salary: yuan !== '' && yuan != null ? Math.round(Number(yuan) * 100) : undefined,
    is_active: form.value.is_active,
  }
  try {
    if (formMode.value === 'add') {
      await createPayday(payload)
      uni.showToast({ title: '添加成功' })
    } else if (editId.value) {
      await updatePayday(editId.value, payload)
      uni.showToast({ title: '保存成功' })
    }
    closeForm()
    await loadList()
  } catch (e: any) {
    uni.showToast({ title: e?.message || '操作失败', icon: 'none' })
  }
}

function doDelete(item: PaydayConfig) {
  uni.showModal({
    title: '确认删除',
    content: `删除「${item.job_name}」的发薪日配置？`,
    success: async res => {
      if (!res.confirm) return
      try {
        await deletePayday(item.id)
        uni.showToast({ title: '已删除' })
        await loadList()
      } catch (e: any) {
        uni.showToast({ title: e?.message || '删除失败', icon: 'none' })
      }
    },
  })
}

function calendarLabel(v: string) {
  return calendarOptions.find(o => o.value === v)?.label ?? v
}

onMounted(() => {
  loadList()
})
</script>

<template>
  <view class="page">
    <view class="head">
      <text class="title">发薪日设置</text>
      <text class="tip">配置每月发薪日，支持多份工作</text>
      <button class="btn-add" @click="openAdd">添加发薪日</button>
    </view>

    <view v-if="loading" class="loading">加载中...</view>
    <view v-else-if="errMsg" class="err">{{ errMsg }}</view>
    <view v-else-if="list.length === 0" class="empty">暂无配置，点击上方添加</view>
    <view v-else class="list">
      <view v-for="item in list" :key="item.id" class="card">
        <view class="card-main">
          <text class="job-name">{{ item.job_name }}</text>
          <text class="meta"
            >每月 {{ item.payday }} 日（{{ calendarLabel(item.calendar_type) }}）</text
          >
          <text v-if="item.estimated_salary != null" class="salary"
            >预估 {{ (item.estimated_salary / 100).toFixed(0) }} 元</text
          >
        </view>
        <view class="card-actions">
          <button class="btn-sm" @click="openEdit(item)">编辑</button>
          <button class="btn-sm danger" @click="doDelete(item)">删除</button>
        </view>
      </view>
    </view>

    <!-- 新增/编辑表单弹层 -->
    <view v-if="showForm" class="mask" @click="closeForm">
      <view class="form-panel" @click.stop>
        <text class="form-title">{{ formMode === 'add' ? '添加发薪日' : '编辑发薪日' }}</text>
        <view class="form-item">
          <text class="label">工作名称</text>
          <input v-model="form.job_name" class="input" placeholder="如：主职" />
        </view>
        <view class="form-item">
          <text class="label">发薪日（每月几日）</text>
          <picker
            :value="form.payday - 1"
            :range="paydayOptions"
            range-key="label"
            @change="(e: any) => (form.payday = paydayOptions[e.detail.value].value)"
          >
            <view class="picker">{{ form.payday }} 日</view>
          </picker>
        </view>
        <view class="form-item">
          <text class="label">历法</text>
          <picker
            :value="form.calendar_type === 'lunar' ? 1 : 0"
            :range="calendarOptions"
            range-key="label"
            @change="
              (e: any) =>
                (form.calendar_type = calendarOptions[e.detail.value].value as 'solar' | 'lunar')
            "
          >
            <view class="picker">{{ calendarLabel(form.calendar_type) }}</view>
          </picker>
        </view>
        <view class="form-item">
          <text class="label">预估工资（元，选填）</text>
          <input
            v-model.number="form.estimated_salaryYuan"
            type="digit"
            class="input"
            placeholder="不填则不显示"
          />
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
.page {
  padding: 24rpx;
  min-height: 100vh;
}
.head {
  margin-bottom: 24rpx;
}
.title {
  font-size: 36rpx;
  font-weight: 600;
  display: block;
}
.tip {
  display: block;
  margin-top: 8rpx;
  color: #666;
  font-size: 26rpx;
}
.btn-add {
  margin-top: 20rpx;
  background: #07c160;
  color: #fff;
  border: none;
  border-radius: 8rpx;
}
.loading,
.err,
.empty {
  padding: 40rpx;
  text-align: center;
  color: #666;
}
.list {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}
.card {
  background: #f8f8f8;
  border-radius: 12rpx;
  padding: 24rpx;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.card-main {
  flex: 1;
}
.job-name {
  font-weight: 600;
  font-size: 30rpx;
  display: block;
}
.meta {
  display: block;
  margin-top: 8rpx;
  color: #666;
  font-size: 26rpx;
}
.salary {
  display: block;
  margin-top: 4rpx;
  color: #07c160;
  font-size: 26rpx;
}
.card-actions {
  display: flex;
  gap: 16rpx;
}
.btn-sm {
  padding: 8rpx 20rpx;
  font-size: 24rpx;
  border: 1rpx solid #ccc;
  border-radius: 8rpx;
  background: #fff;
}
.btn-sm.danger {
  border-color: #e0e0e0;
  color: #e64340;
}
.mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: flex-end;
  z-index: 100;
}
.form-panel {
  width: 100%;
  background: #fff;
  border-radius: 24rpx 24rpx 0 0;
  padding: 32rpx;
  max-height: 80vh;
  overflow: auto;
}
.form-title {
  font-size: 32rpx;
  font-weight: 600;
  display: block;
  margin-bottom: 24rpx;
}
.form-item {
  margin-bottom: 24rpx;
}
.label {
  display: block;
  margin-bottom: 8rpx;
  color: #666;
  font-size: 26rpx;
}
.input,
.picker {
  border: 1rpx solid #e0e0e0;
  border-radius: 8rpx;
  padding: 20rpx;
  font-size: 28rpx;
}
.picker {
  background: #fff;
}
.form-actions {
  display: flex;
  gap: 20rpx;
  margin-top: 32rpx;
}
.btn-cancel {
  flex: 1;
  border: 1rpx solid #ccc;
  border-radius: 8rpx;
  background: #fff;
}
.btn-ok {
  flex: 1;
  background: #07c160;
  color: #fff;
  border: none;
  border-radius: 8rpx;
}
</style>
