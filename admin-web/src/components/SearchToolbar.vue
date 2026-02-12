<template>
  <div class="search-toolbar" role="search" aria-label="搜索工具栏">
    <el-input
      v-model="keywordModel"
      placeholder="关键词"
      clearable
      style="width: 200px"
      aria-label="搜索关键词"
      @keyup.enter="handleSearch"
    />
    <slot></slot>
    <el-button type="primary" aria-label="执行搜索" @click="handleSearch">搜索</el-button>
  </div>
</template>

<script setup lang="ts">
const keywordModel = defineModel<string>('keyword')

const emit = defineEmits(['search'])

function handleSearch() {
  emit('search')
}
</script>

<style scoped>
.search-toolbar {
  display: flex;
  gap: var(--spacing-sm);
  align-items: center;
  margin-bottom: var(--spacing-md);
}
</style>
