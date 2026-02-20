<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getFeedbackList, type FeedbackItem } from '@/api/feedback'

const list = ref<FeedbackItem[]>([])
const loading = ref(false)

async function loadData() {
  loading.value = true
  try {
    const res = await getFeedbackList()
    list.value = res.data || []
  } catch (e: any) {
    ElMessage.error(e?.message || '加载失败')
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

<template>
  <div class="feedback-page">
    <div class="header">
      <h2>用户反馈</h2>
    </div>

    <el-table :data="list" v-loading="loading" stripe border>
      <el-table-column prop="created_at" label="时间" width="180" />
      <el-table-column prop="content" label="反馈内容" min-width="200" show-overflow-tooltip />
      <el-table-column label="图片" width="150">
        <template #default="{ row }">
          <el-image
            v-for="(img, idx) in row.images"
            :key="idx"
            :src="img"
            style="width: 60px; height: 60px; margin-right: 8px;"
            :preview-src-list="row.images"
          />
        </template>
      </el-table-column>
      <el-table-column prop="contact" label="联系方式" width="150" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag v-if="row.status === 'pending'" type="warning">待处理</el-tag>
          <el-tag v-else-if="row.status === 'processing'" type="primary">处理中</el-tag>
          <el-tag v-else-if="row.status === 'resolved'" type="success">已解决</el-tag>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<style scoped>
.feedback-page { padding: 24px; }
.header { margin-bottom: 24px; }
.header h2 { margin: 0; }
</style>
