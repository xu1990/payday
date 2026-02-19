<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { QuillEditor } from '@vueup/vue-quill'
import '@vueup/vue-quill/dist/vue-quill.snow.css'
import { ElMessage } from 'element-plus'
import { getAgreements, updateAgreement } from '@/api/miniprogram'

const activeTab = ref<'user' | 'privacy'>('user')
const userContent = ref('')
const privacyContent = ref('')
const loading = ref(false)
const saving = ref(false)

async function loadData() {
  loading.value = true
  try {
    const res = await getAgreements()
    userContent.value = res.data?.user_agreement || ''
    privacyContent.value = res.data?.privacy_agreement || ''
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : '加载失败'
    ElMessage.error(errorMessage)
  } finally {
    loading.value = false
  }
}

async function save() {
  saving.value = true
  try {
    const type = activeTab.value
    const content = type === 'user' ? userContent.value : privacyContent.value

    await updateAgreement({ type, content })
    ElMessage.success('保存成功')
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : '保存失败'
    ElMessage.error(errorMessage)
  } finally {
    saving.value = false
  }
}

function switchTab(tab: 'user' | 'privacy') {
  activeTab.value = tab
}

onMounted(loadData)
</script>

<template>
  <div class="agreement-page">
    <div class="header">
      <h2>协议管理</h2>
    </div>

    <el-tabs v-model="activeTab" @tab-change="switchTab">
      <el-tab-pane label="用户协议" name="user" />
      <el-tab-pane label="隐私协议" name="privacy" />
    </el-tabs>

    <div v-loading="loading" class="editor-container">
      <QuillEditor
        v-model:content="activeTab === 'user' ? userContent : privacyContent"
        contentType="html"
        theme="snow"
        :toolbar="[
          ['bold', 'italic', 'underline', 'strike'],
          ['blockquote', 'code-block'],
          [{ 'header': 1 }, { 'header': 2 }],
          [{ 'list': 'ordered'}, { 'list': 'bullet' }],
          [{ 'indent': '-1'}, { 'indent': '+1' }],
          ['link'],
          ['clean']
        ]"
        style="height: 400px; margin-bottom: 60px;"
      />

      <div class="actions">
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.agreement-page {
  padding: 24px;
}

.header {
  margin-bottom: 24px;
}

.header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.editor-container {
  background: #fff;
  padding: 24px;
  border-radius: 8px;
}

.actions {
  position: fixed;
  bottom: 24px;
  right: 24px;
  background: #fff;
  padding: 16px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
</style>
