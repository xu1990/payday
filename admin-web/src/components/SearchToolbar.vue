<template>
  <div class="search-toolbar">
    <el-input
      v-model="keywordModel"
      placeholder="关键词"
      clearable
      style="width: 200px"
      @keyup.enter="handleSearch"
    />
    <slot></slot>
    <el-button type="primary" @click="handleSearch">搜索</el-button>
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
  gap: 8px;
  align-items: center;
  margin-bottom: 16px;
}
</style>
