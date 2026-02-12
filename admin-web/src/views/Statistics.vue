<template>
  <div class="statistics-page">
    <h2 class="page-title">数据统计</h2>
    <el-row :gutter="16" class="stats-row">
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-label">用户总数</div>
          <div class="stat-value">{{ stats?.user_total ?? '-' }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-label">今日新增用户</div>
          <div class="stat-value">{{ stats?.user_new_today ?? '-' }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-label">工资记录总数</div>
          <div class="stat-value">{{ stats?.salary_record_total ?? '-' }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-label">今日新增记录</div>
          <div class="stat-value">{{ stats?.salary_record_today ?? '-' }}</div>
        </el-card>
      </el-col>
    </el-row>
    <el-card v-if="loading" v-loading="loading" style="min-height: 120px" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getStatistics, type AdminStatistics } from '@/api/admin'

const loading = ref(true)
const stats = ref<AdminStatistics | null>(null)

onMounted(async () => {
  try {
    const { data } = await getStatistics()
    stats.value = data
  } catch {
    stats.value = null
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.statistics-page {
  padding: var(--spacing-lg);
}
.page-title {
  margin-bottom: var(--spacing-md);
  font-size: var(--font-size-lg);
}
.stats-row {
  margin-bottom: var(--spacing-md);
}
.stat-label {
  color: var(--color-text-secondary);
  font-size: var(--font-size-base);
  margin-bottom: var(--spacing-sm);
}
.stat-value {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--color-primary);
}
</style>
