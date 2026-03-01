<template>
  <div class="system-messages">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>发送系统消息</span>
        </div>
      </template>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
        v-loading="loading"
      >
        <el-form-item label="消息标题" prop="title">
          <el-input
            v-model="form.title"
            placeholder="请输入消息标题"
            maxlength="100"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="消息内容" prop="content">
          <el-input
            v-model="form.content"
            type="textarea"
            placeholder="请输入消息内容（可选）"
            :rows="4"
            maxlength="1000"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="发送对象" prop="sendType">
          <el-radio-group v-model="form.sendType">
            <el-radio value="all">所有用户</el-radio>
            <el-radio value="selected">指定用户</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item
          v-if="form.sendType === 'selected'"
          label="选择用户"
          prop="user_ids"
        >
          <el-select
            v-model="form.user_ids"
            multiple
            filterable
            remote
            reserve-keyword
            placeholder="请输入用户昵称搜索"
            :remote-method="searchUsers"
            :loading="searchLoading"
            style="width: 100%"
          >
            <el-option
              v-for="user in userOptions"
              :key="user.id"
              :label="user.anonymous_name"
              :value="user.id"
            />
          </el-select>
          <div class="form-tip">
            已选择 {{ form.user_ids?.length || 0 }} 个用户
          </div>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSubmit" :loading="submitting">
            发送消息
          </el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 发送结果 -->
    <el-card v-if="sendResult" class="result-card">
      <template #header>
        <div class="card-header">
          <span>发送结果</span>
        </div>
      </template>
      <el-result
        :icon="sendResult.failed_count === 0 ? 'success' : 'warning'"
        :title="sendResult.failed_count === 0 ? '发送成功' : '部分发送成功'"
      >
        <template #sub-title>
          <div class="result-stats">
            <p>成功发送: <span class="success">{{ sendResult.success_count }}</span> 条</p>
            <p v-if="sendResult.failed_count > 0">
              发送失败: <span class="failed">{{ sendResult.failed_count }}</span> 条
            </p>
          </div>
        </template>
        <template #extra>
          <el-button type="primary" @click="sendResult = null">继续发送</el-button>
        </template>
      </el-result>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { sendSystemMessage, getUsers, type SystemMessageSendResponse, type AdminUserListItem } from '@/api/admin'

const formRef = ref<FormInstance>()
const loading = ref(false)
const submitting = ref(false)
const searchLoading = ref(false)
const sendResult = ref<SystemMessageSendResponse | null>(null)
const userOptions = ref<AdminUserListItem[]>([])

const form = reactive({
  title: '',
  content: '',
  sendType: 'all' as 'all' | 'selected',
  user_ids: [] as string[]
})

const rules: FormRules = {
  title: [
    { required: true, message: '请输入消息标题', trigger: 'blur' },
    { min: 1, max: 100, message: '标题长度为1-100个字符', trigger: 'blur' }
  ],
  sendType: [
    { required: true, message: '请选择发送对象', trigger: 'change' }
  ]
}

async function searchUsers(keyword: string) {
  if (!keyword) {
    userOptions.value = []
    return
  }

  searchLoading.value = true
  try {
    const result = await getUsers({ keyword, page_size: 20 })
    userOptions.value = result.items
  } catch (error) {
    console.error('搜索用户失败:', error)
  } finally {
    searchLoading.value = false
  }
}

async function handleSubmit() {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    // 验证是否选择了用户
    if (form.sendType === 'selected' && (!form.user_ids || form.user_ids.length === 0)) {
      ElMessage.warning('请选择要发送的用户')
      return
    }

    submitting.value = true
    try {
      const result = await sendSystemMessage({
        title: form.title,
        content: form.content || undefined,
        send_to_all: form.sendType === 'all',
        user_ids: form.sendType === 'selected' ? form.user_ids : undefined
      })

      sendResult.value = result
      ElMessage.success('系统消息发送完成')

      // 重置表单
      formRef.value?.resetFields()
      form.user_ids = []
    } catch (error: any) {
      ElMessage.error(error.response?.data?.message || '发送失败')
    } finally {
      submitting.value = false
    }
  })
}

function handleReset() {
  formRef.value?.resetFields()
  form.user_ids = []
  sendResult.value = null
}
</script>

<style scoped>
.system-messages {
  padding: 20px;
}

.system-messages .card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.system-messages .form-tip {
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
}

.system-messages .result-card {
  margin-top: 20px;
}

.system-messages .result-stats {
  font-size: 14px;
}

.system-messages .result-stats .success {
  color: #67c23a;
  font-weight: bold;
}

.system-messages .result-stats .failed {
  color: #f56c6c;
  font-weight: bold;
}
</style>
