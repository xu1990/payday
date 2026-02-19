<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import type { UploadProps } from 'element-plus'
import { getSplashConfig, updateSplashConfig, type SplashConfigData } from '@/api/miniprogram'

const form = ref<SplashConfigData>({
  image_url: '',
  content: '欢迎使用薪日 PayDay',
  countdown: 3,
  is_active: true,
})
const loading = ref(false)
const saving = ref(false)
const imageUrl = ref('')

async function loadData() {
  loading.value = true
  try {
    const res = await getSplashConfig()
    if (res.data) {
      form.value = res.data
      imageUrl.value = res.data.image_url || ''
    }
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
    await updateSplashConfig(form.value)
    ElMessage.success('保存成功')
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : '保存失败'
    ElMessage.error(errorMessage)
  } finally {
    saving.value = false
  }
}

const handleImageSuccess: UploadProps['onSuccess'] = (response) => {
  if (response.data?.url) {
    form.value.image_url = response.data.url
    imageUrl.value = response.data.url
    ElMessage.success('图片上传成功')
  }
}

const beforeImageUpload: UploadProps['beforeUpload'] = (rawFile) => {
  if (!rawFile.type.startsWith('image/')) {
    ElMessage.error('只能上传图片文件')
    return false
  }
  if (rawFile.size / 1024 / 1024 > 5) {
    ElMessage.error('图片大小不能超过5MB')
    return false
  }
  return true
}

onMounted(loadData)
</script>

<template>
  <div class="splash-page">
    <div class="header">
      <h2>开屏页面设置</h2>
    </div>

    <el-card v-loading="loading" class="form-card">
      <el-form :model="form" label-width="120px">
        <el-form-item label="开屏图片">
          <el-upload
            action="/api/v1/admin/upload"
            :show-file-list="false"
            :on-success="handleImageSuccess"
            :before-upload="beforeImageUpload"
            accept="image/*"
          >
            <el-button type="primary">选择图片</el-button>
          </el-upload>
          <div v-if="imageUrl" class="image-preview">
            <el-image :src="imageUrl" fit="contain" style="width: 200px; height: 300px;" />
          </div>
        </el-form-item>

        <el-form-item label="欢迎文字">
          <el-input v-model="form.content" placeholder="请输入欢迎文字" maxlength="50" show-word-limit />
        </el-form-item>

        <el-form-item label="倒计时时长">
          <el-input-number v-model="form.countdown" :min="1" :max="10" controls-position="right" />
          <span style="margin-left: 8px; color: #999;">秒</span>
        </el-form-item>

        <el-form-item label="启用状态">
          <el-switch v-model="form.is_active" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="saving" @click="save">保存配置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.splash-page {
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

.form-card {
  max-width: 600px;
}

.image-preview {
  margin-top: 16px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  overflow: hidden;
  display: inline-block;
}
</style>
