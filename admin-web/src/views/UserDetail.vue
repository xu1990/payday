<template>
  <div class="user-detail-page">
    <el-page-header title="返回" @back="router.push({ name: 'Users' })">
      <template #content>用户详情</template>
    </el-page-header>
    <el-card v-loading="loading" class="detail-card">
      <template v-if="user">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="ID">{{ user.id }}</el-descriptions-item>
          <el-descriptions-item label="匿名昵称">{{ user.anonymous_name }}</el-descriptions-item>
          <el-descriptions-item label="OpenID">{{ user.openid }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <StatusTag :status="user.status" />
          </el-descriptions-item>
          <el-descriptions-item label="关注数">{{ user.follower_count }}</el-descriptions-item>
          <el-descriptions-item label="粉丝数">{{ user.following_count }}</el-descriptions-item>
          <el-descriptions-item label="帖子数">{{ user.post_count }}</el-descriptions-item>
          <el-descriptions-item label="注册时间">{{ formatDate(user.created_at) }}</el-descriptions-item>
        </el-descriptions>
      </template>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getUser, type AdminUserDetail } from '@/api/admin'
import StatusTag from '@/components/StatusTag.vue'
import { formatDate } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const user = ref<AdminUserDetail | null>(null)

const id = computed(() => route.params.id as string)

onMounted(async () => {
  if (!id.value) return
  try {
    const { data } = await getUser(id.value)
    user.value = data
  } catch {
    user.value = null
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.user-detail-page {
  padding: var(--spacing-lg);
}
.detail-card {
  margin-top: var(--spacing-md);
}
</style>
