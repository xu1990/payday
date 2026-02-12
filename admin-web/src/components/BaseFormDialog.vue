<template>
  <el-dialog
    v-model="visibleModel"
    :title="title"
    :width="width"
    v-bind="$attrs"
  >
    <el-form
      :model="form"
      :rules="rules"
      ref="formRef"
      label-width="100px"
    >
      <slot :form="form" :rules="rules"></slot>
    </el-form>
    <template #footer>
      <el-button @click="visibleModel = false">取消</el-button>
      <el-button type="primary" @click="handleSubmit">确定</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import type { FormInstance } from 'element-plus'

interface Props {
  title: string
  form: Record<string, any>
  rules?: Record<string, any>
  width?: string
}

const props = withDefaults(defineProps<Props>(), {
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
