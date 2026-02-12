<template>
  <el-dialog
    v-model="visibleModel"
    :title="title"
    :width="width"
    :aria-label="title"
    v-bind="$attrs"
  >
    <el-form
      :model="form"
      :rules="rules"
      ref="formRef"
      label-width="100px"
      :aria-label="`${title}表单`"
    >
      <slot :form="form" :rules="rules"></slot>
    </el-form>
    <template #footer>
      <el-button aria-label="取消操作" @click="visibleModel = false">取消</el-button>
      <el-button type="primary" aria-label="确认提交" @click="handleSubmit">确定</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { FormInstance } from 'element-plus'

interface Props {
  title: string
  form: Record<string, any>
  rules?: Record<string, any>
  width?: string
}

withDefaults(defineProps<Props>(), {
  width: '600px',
})

const visibleModel = defineModel<boolean>('visible')
const formRef = ref<FormInstance>()

const emit = defineEmits(['submit'])

async function handleSubmit() {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    emit('submit')
  } catch {
    // 验证失败
  }
}

defineExpose({
  formRef,
})
</script>
