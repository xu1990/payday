import { ref, onUnmounted } from 'vue'
import { getUnreadCount } from '@/api/notification'

const POLL_INTERVAL = 30000 // 30 seconds

export function useNotificationUnread() {
  const unreadCount = ref(0)
  let intervalId: number | null = null

  async function fetch() {
    try {
      const res = await getUnreadCount()
      unreadCount.value = res?.unread_count ?? 0
    } catch (e) {
      console.error('[useNotificationUnread] Failed to fetch unread count:', e)
    }
  }

  function startPolling() {
    fetch() // Initial fetch
    intervalId = setInterval(fetch, POLL_INTERVAL) as unknown as number
  }

  function stopPolling() {
    if (intervalId !== null) {
      clearInterval(intervalId)
      intervalId = null
    }
  }

  function refresh() {
    fetch()
  }

  // Auto cleanup on unmount
  onUnmounted(() => {
    stopPolling()
  })

  return {
    unreadCount,
    startPolling,
    stopPolling,
    refresh,
  }
}
