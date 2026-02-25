<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { StarFilled } from '@element-plus/icons-vue'
import {
  listAddresses,
  updateAddress,
  setDefaultAddress,
  type UserAddress,
  type UserAddressUpdate,
} from '@/api/userAddress'
import { formatDate } from '@/utils/format'

const list = ref<UserAddress[]>([])
const loading = ref(false)

// Search form
const searchUserId = ref('')
const searchPhone = ref('')

// Edit dialog
const showDialog = ref(false)
const editItem = ref<UserAddress | null>(null)
const editForm = ref<UserAddressUpdate>({})
const submitLoading = ref(false)

/**
 * Mask phone number for display
 * 13812345678 -> 138****5678
 */
function maskPhone(phone: string): string {
  if (!phone || phone.length < 7) return phone
  return phone.substring(0, 3) + '****' + phone.substring(7)
}

/**
 * Format full region name
 */
function formatRegion(item: UserAddress): string {
  return `${item.province_name} ${item.city_name} ${item.district_name}`
}

async function loadData() {
  if (!searchUserId.value && !searchPhone.value) {
    ElMessage.warning('请输入用户ID或手机号进行搜索')
    return
  }

  loading.value = true
  try {
    const params: { user_id?: string; phone?: string } = {}
    if (searchUserId.value) params.user_id = searchUserId.value
    if (searchPhone.value) params.phone = searchPhone.value

    const res = await listAddresses(params)
    list.value = res?.data || []
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : '加载失败'
    ElMessage.error(errorMessage)
    list.value = []
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  loadData()
}

function handleReset() {
  searchUserId.value = ''
  searchPhone.value = ''
  list.value = []
}

function openEdit(item: UserAddress) {
  editItem.value = item
  editForm.value = {
    province_code: item.province_code,
    province_name: item.province_name,
    city_code: item.city_code,
    city_name: item.city_name,
    district_code: item.district_code,
    district_name: item.district_name,
    detailed_address: item.detailed_address,
    postal_code: item.postal_code,
    contact_name: item.contact_name,
    contact_phone: item.contact_phone,
    is_active: item.is_active,
  }
  showDialog.value = true
}

async function handleSubmit() {
  if (!editItem.value) return

  if (!editForm.value.contact_name?.trim()) {
    ElMessage.warning('请输入联系人姓名')
    return
  }
  if (!editForm.value.contact_phone?.trim()) {
    ElMessage.warning('请输入联系电话')
    return
  }
  if (!editForm.value.detailed_address?.trim()) {
    ElMessage.warning('请输入详细地址')
    return
  }

  submitLoading.value = true
  try {
    await updateAddress(editItem.value.id, editForm.value)
    ElMessage.success('更新成功')
    showDialog.value = false
    await loadData()
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : '更新失败'
    ElMessage.error(errorMessage)
  } finally {
    submitLoading.value = false
  }
}

async function handleSetDefault(item: UserAddress) {
  try {
    await ElMessageBox.confirm(
      `确定要将此地址设置为${item.contact_name}的默认地址吗？`,
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    await setDefaultAddress(item.id)
    ElMessage.success('已设置为默认地址')
    await loadData()
  } catch (e: unknown) {
    if (e === 'cancel') return
    const errorMessage = e instanceof Error ? e.message : '操作失败'
    ElMessage.error(errorMessage)
  }
}

async function handleToggleActive(item: UserAddress) {
  const action = item.is_active ? '标记为无效' : '标记为有效'
  try {
    await ElMessageBox.confirm(`确定要${action}此地址吗？`, '确认操作', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await updateAddress(item.id, { is_active: !item.is_active })
    ElMessage.success(`${action}成功`)
    await loadData()
  } catch (e: unknown) {
    if (e === 'cancel') return
    const errorMessage = e instanceof Error ? e.message : '操作失败'
    ElMessage.error(errorMessage)
  }
}
</script>

<template>
  <div class="user-addresses-container">
    <div class="page-header">
      <h2>用户地址管理</h2>
    </div>

    <!-- Search Form -->
    <div class="search-form">
      <el-form :inline="true" @submit.prevent="handleSearch">
        <el-form-item label="用户ID">
          <el-input
            v-model="searchUserId"
            placeholder="请输入用户ID"
            clearable
            style="width: 200px"
          />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input
            v-model="searchPhone"
            placeholder="请输入手机号"
            clearable
            style="width: 200px"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- Address List Table -->
    <el-table v-loading="loading" :data="list" stripe>
      <el-table-column prop="user_id" label="用户ID" width="120" />
      <el-table-column prop="contact_name" label="联系人" width="120" />
      <el-table-column label="联系电话" width="130">
        <template #default="{ row }">
          {{ maskPhone(row.contact_phone) }}
        </template>
      </el-table-column>
      <el-table-column label="地区" width="280">
        <template #default="{ row }">
          {{ formatRegion(row) }}
        </template>
      </el-table-column>
      <el-table-column
        prop="detailed_address"
        label="详细地址"
        min-width="200"
        show-overflow-tooltip
      />
      <el-table-column label="默认" width="80" align="center">
        <template #default="{ row }">
          <el-icon v-if="row.is_default" color="#f5a623">
            <StarFilled />
          </el-icon>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column prop="is_active" label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
            {{ row.is_active ? '有效' : '无效' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="280" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click="openEdit(row)"> 编辑 </el-button>
          <el-button
            v-if="!row.is_default"
            link
            type="primary"
            size="small"
            @click="handleSetDefault(row)"
          >
            设为默认
          </el-button>
          <el-button
            link
            :type="row.is_active ? 'warning' : 'success'"
            size="small"
            @click="handleToggleActive(row)"
          >
            {{ row.is_active ? '标记无效' : '标记有效' }}
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- Edit Dialog -->
    <el-dialog v-model="showDialog" title="编辑地址" width="600px">
      <el-form v-if="editItem" :model="editForm" label-width="100px">
        <el-form-item label="用户ID">
          <el-input v-model="editItem.user_id" disabled />
        </el-form-item>
        <el-form-item label="联系人姓名" required>
          <el-input v-model="editForm.contact_name" placeholder="请输入联系人姓名" />
        </el-form-item>
        <el-form-item label="联系电话" required>
          <el-input v-model="editForm.contact_phone" placeholder="请输入联系电话" />
        </el-form-item>
        <el-form-item label="省份" required>
          <el-input v-model="editForm.province_name" placeholder="请输入省份名称" />
        </el-form-item>
        <el-form-item label="城市" required>
          <el-input v-model="editForm.city_name" placeholder="请输入城市名称" />
        </el-form-item>
        <el-form-item label="区县" required>
          <el-input v-model="editForm.district_name" placeholder="请输入区县名称" />
        </el-form-item>
        <el-form-item label="详细地址" required>
          <el-input
            v-model="editForm.detailed_address"
            type="textarea"
            :rows="2"
            placeholder="请输入详细地址"
          />
        </el-form-item>
        <el-form-item label="邮政编码">
          <el-input v-model="editForm.postal_code" placeholder="请输入邮政编码（可选）" />
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="editForm.is_active">
            <el-radio :label="true">有效</el-radio>
            <el-radio :label="false">无效</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit"> 保存 </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.user-addresses-container {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 500;
}

.search-form {
  margin-bottom: 20px;
  padding: 20px;
  background-color: #f5f7fa;
  border-radius: 4px;
}
</style>
