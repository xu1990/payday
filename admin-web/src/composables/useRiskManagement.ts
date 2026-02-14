/**
 * 风险管理 - 可组合式函数
 *
 * 提供统一的风控操作（审核/拒绝）逻辑
 * 消除 PostList.vue, RiskPending.vue, CommentList.vue 中的重复代码
 */
import { ref } from 'vue'
import { ElMessageBox } from 'element-plus'
import { ElMessage } from 'element-plus'

/**
 * 风险管理可组合式函数
 *
 * @template T - 风险项类型（Post 或 Comment）
 * @returns 风险管理方法和状态
 */
export function useRiskManagement<T extends { id: string; risk_status?: string }>() {
  // 拒绝对话框可见性
  const rejectVisible = ref(false)
  const rejectReason = ref('')
  const rejectTarget = ref<T | null>(null)

  // 拒绝操作
  const reject = (item: T) => {
    rejectTarget.value = item
    rejectReason.value = ''
    rejectVisible.value = true
  }

  // 确认拒绝
  const confirmReject = async (
    updateFn: (id: string, data: { risk_status: string; risk_reason?: string }) => Promise<void>
  ) => {
    if (!rejectTarget.value) return

    if (!rejectReason.value?.trim()) {
      ElMessage.warning('请输入拒绝原因')
      return
    }

    try {
      await updateFn(rejectTarget.value.id, {
        risk_status: 'rejected',
        risk_reason: rejectReason.value
      })
      ElMessage.success('已拒绝')
      rejectVisible.value = false
      rejectTarget.value = null
      rejectReason.value = ''
    } catch (error: unknown) {
      // 使用类型守卫检查错误
      const isApiError = error && typeof error === 'object' && 'response' in error
      if (isApiError && (error as { response?: { status: number } }).response?.status === 404) {
        ElMessage.error('资源不存在')
      } else {
        ElMessage.error('操作失败，请重试')
      }
    }
  }

  // 通过操作
  const approve = async (
    updateFn: (id: string, data: { risk_status: string }) => Promise<void>
  ) => {
    try {
      await updateFn(item.id, {
        risk_status: 'approved'
      })
      ElMessage.success('已通过')
    } catch (error: unknown) {
      const isApiError = error && typeof error === 'object' && 'response' in error
      if (isApiError && (error as { response?: { status: number } }).response?.status === 404) {
        ElMessage.error('资源不存在')
      } else {
        ElMessage.error('操作失败，请重试')
      }
    }
  }

  return {
    rejectVisible,
    rejectReason,
    rejectTarget,
    reject,
    approve,
    confirmReject
  }
}
