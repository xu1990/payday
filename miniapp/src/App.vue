<script setup lang="ts">
import { onLaunch } from '@dcloudio/uni-app'
import { useAuthStore } from '@/stores/auth'

onLaunch(async () => {
  // 初始化认证状态 - 从本地存储恢复 token
  const authStore = useAuthStore()
  await authStore.init()
  console.log('[App] Auth store initialized, isLoggedIn:', authStore.isLoggedIn)
})
</script>

<style></style>
