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

const list = ref([])
const loading = ref(false)
const errMsg = ref('')

// 表单（新增/编辑）
const formMode = ref('add')
const editId = ref(null)
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

function openEdit(item) {
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
  const payload= {
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

function doDelete(item) {
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

<style scoped lang="scss">
.page {
  padding: $spacing-md;
  min-height: 100vh;
  background: var(--bg-base);
}
.head {
  margin-bottom: $spacing-md;
}
.title {
  font-size: $font-size-xl;
  font-weight: $font-weight-semibold;
  display: block;
  color: var(--text-primary);
}
.tip {
  display: block;
  margin-top: $spacing-xs;
  color: var(--text-secondary);
  font-size: $font-size-sm;
}
.btn-add {
  margin-top: $spacing-sm;
  background: $brand-primary;
  color: #fff;
  border: none;
  border-radius: $radius-sm;
}
.loading,
.err,
.empty {
  padding: $spacing-lg;
  text-align: center;
  color: var(--text-secondary);
}
.list {
  display: flex;
  flex-direction: column;
  gap: $spacing-sm;
}
.card {
  @include glass-card();
  padding: $spacing-md;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.card-main {
  flex: 1;
}
.job-name {
  font-weight: $font-weight-semibold;
  font-size: $font-size-lg;
  display: block;
  color: var(--text-primary);
}
.meta {
  display: block;
  margin-top: $spacing-xs;
  color: var(--text-secondary);
  font-size: $font-size-sm;
}
.salary {
  display: block;
  margin-top: 4rpx;
  color: $brand-primary;
  font-size: $font-size-sm;
}
.card-actions {
  display: flex;
  gap: $spacing-sm;
}
.btn-sm {
  padding: $spacing-xs $spacing-sm;
  font-size: $font-size-xs;
  border: 1rpx solid var(--border-subtle);
  border-radius: $radius-sm;
  background: var(--bg-glass-subtle);
  color: var(--text-primary);
}
.btn-sm.danger {
  border-color: var(--border-regular);
  color: $semantic-error;
}
.mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.25);
  display: flex;
  align-items: flex-end;
  z-index: 100;
}
.form-panel {
  width: 100%;
  background: #fff;
  border-radius: $radius-lg $radius-lg 0 0;
  padding: $spacing-lg;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 -16rpx 48rpx rgba(0, 0, 0, 0.15);
  border-top: 1rpx solid rgba(255, 255, 255, 0.8);
}
.form-title {
  font-size: $font-size-lg;
  font-weight: $font-weight-semibold;
  display: block;
  margin-bottom: $spacing-md;
  color: var(--text-primary);
}
.form-item {
  margin-bottom: $spacing-md;
}
.label {
  display: block;
  margin-bottom: $spacing-xs;
  color: var(--text-secondary);
  font-size: $font-size-sm;
}
.input,
.picker {
  @include glass-input();
  padding: $spacing-sm;
  font-size: $font-size-base;
  background: var(--bg-glass-standard);
}
.picker {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.form-actions {
  display: flex;
  gap: $spacing-sm;
  margin-top: $spacing-lg;
}
.btn-cancel {
  flex: 1;
  border: 1rpx solid var(--border-regular);
  border-radius: $radius-sm;
  background: var(--bg-glass-standard);
  color: var(--text-primary);
}
.btn-ok {
  flex: 1;
  background: $brand-primary;
  color: #fff;
  border: none;
  border-radius: $radius-sm;
}
</style>
