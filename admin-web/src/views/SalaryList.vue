<template>
  <div>
    <h2 class="page-title">工资记录</h2>
    <SearchToolbar
      v-model:keyword="filterUserId"
      placeholder="用户 ID 筛选"
      @search="fetch"
    />

    <BaseDataTable
      v-model:current-page="page"
      v-model:page-size="pageSize"
      :items="items"
      :total="total"
      :loading="loading"
      @page-change="fetch"
    >
      <el-table-column prop="user_id" label="用户ID" width="280" show-overflow-tooltip />
      <el-table-column prop="amount" label="金额" width="100" />
      <el-table-column prop="payday_date" label="发薪日" width="120" />
      <el-table-column prop="salary_type" label="类型" width="100" />
      <el-table-column prop="risk_status" label="风险" width="100">
        <template #default="{ row }">
          <StatusTag :status="row.risk_status" />
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">
          {{ row.created_at ? formatDate(row.created_at) : '-' }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="140" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" link @click="openAudit(row)">审核</el-button>
          <el-button type="danger" link @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </BaseDataTable>

    <el-dialog
      v-model="auditDialogVisible"
      title="人工审核"
      width="400px"
      :close-on-click-modal="false"
      @closed="auditRow = null"
    >
      <p v-if="auditRow">记录 ID：{{ auditRow.id }}，金额 {{ auditRow.amount }} 元。请选择审核结果：</p>
      <template #footer>
        <el-button @click="auditDialogVisible = false">取消</el-button>
        <el-button type="success" :loading="auditLoading" @click="submitAudit('approved')">通过</el-button>
        <el-button type="danger" :loading="auditLoading" @click="submitAudit('rejected')">拒绝</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getSalaryRecords, deleteSalaryRecord, updateSalaryRecordRisk, type AdminSalaryRecordItem } from '@/api/admin'
import BaseDataTable from '@/components/BaseDataTable.vue'
import SearchToolbar from '@/components/SearchToolbar.vue'
import StatusTag from '@/components/StatusTag.vue'
import { formatDate } from '@/utils/format'

const loading = ref(false)
const auditDialogVisible = ref(false)
const auditRow = ref<AdminSalaryRecordItem | null>(null)
const auditLoading = ref(false)
const items = ref<AdminSalaryRecordItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const filterUserId = ref('')

function openAudit(row: AdminSalaryRecordItem) {
  auditRow.value = row
  auditDialogVisible.value = true
}

async function submitAudit(riskStatus: 'approved' | 'rejected') {
  if (!auditRow.value) return
  auditLoading.value = true
  try {
    await updateSalaryRecordRisk(auditRow.value.id, { risk_status: riskStatus })
    ElMessage.success(riskStatus === 'approved' ? '已通过' : '已拒绝')
    auditDialogVisible.value = false
    await fetch()
  } catch (e: unknown) {
    const err = e as { response?: { status: number } }
    ElMessage.error(err.response?.status === 404 ? '记录不存在' : '操作失败')
  } finally {
    auditLoading.value = false
  }
}

async function onDelete(row: AdminSalaryRecordItem) {
  try {
    await ElMessageBox.confirm('确定删除该工资记录？', '提示', {
      type: 'warning',
    })
  } catch {
    return
  }
  try {
    await deleteSalaryRecord(row.id)
    ElMessage.success('已删除')
    await fetch()
  } catch (e: unknown) {
    const err = e as { response?: { status: number } }
    ElMessage.error(err.response?.status === 404 ? '记录不存在' : '删除失败')
  }
}

async function fetch() {
  loading.value = true
  try {
    const params: { limit: number; offset: number; user_id?: string } = {
      limit: pageSize.value,
      offset: (page.value - 1) * pageSize.value,
    }
    if (filterUserId.value) params.user_id = filterUserId.value
    const { items: salaries, total } = await getSalaryRecords(params)
    items.value = salaries
    total.value = total
  } finally {
    loading.value = false
  }
}

onMounted(fetch)
watch([page, pageSize], fetch)
</script>
