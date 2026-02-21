<script lang="ts">
import { defineComponent } from 'vue'
import { useAuthStore } from '@/stores/auth'

export default defineComponent({
  globalData: {
    tokenBackup: null as {
      token: string
      refreshToken?: string
      userId?: string
      timestamp?: number
    } | null,
  },
  onLaunch() {
    // 初始化认证状态 - 从本地存储恢复 token
    const authStore = useAuthStore()
    authStore.init().then(() => {
      console.log('[App] Auth store initialized, isLoggedIn:', authStore.isLoggedIn)
    })
  },
})
</script>

<style></style>
