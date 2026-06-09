// Shared reactive state: notify LearningPath to refresh when path is generated in chat
import { ref } from 'vue'

const refreshCounter = ref(0)

export function usePathRefresh() {
  function notifyPathGenerated() {
    refreshCounter.value++
  }

  return {
    refreshCounter,
    notifyPathGenerated,
  }
}
