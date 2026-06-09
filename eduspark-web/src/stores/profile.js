import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api/request'

export const useProfileStore = defineStore('profile', () => {
  const profile = ref(null)
  const loading = ref(false)

  async function fetchProfile() {
    loading.value = true
    try {
      const res = await api.get('/api/profile')
      profile.value = res.data
    } finally {
      loading.value = false
    }
  }

  // 雷达图数据格式
  function getRadarData() {
    if (!profile.value) return null
    return {
      dimensions: ['知识基础', '认知风格', '学习能力', '易错点', '学习目标', '学习偏好'],
      values: [
        Number.isFinite(profile.value.knowledge_base?.score) ? profile.value.knowledge_base.score : 0,
        Number.isFinite(profile.value.cognitive_style?.score) ? profile.value.cognitive_style.score : 0,
        Number.isFinite(profile.value.learning_ability?.score) ? profile.value.learning_ability.score : 0,
        Number.isFinite(profile.value.error_patterns?.score) ? profile.value.error_patterns.score : 0,
        Number.isFinite(profile.value.learning_goals?.score) ? profile.value.learning_goals.score : 0,
        Number.isFinite(profile.value.learning_preferences?.score) ? profile.value.learning_preferences.score : 0
      ]
    }
  }

  return { profile, loading, fetchProfile, getRadarData }
})
