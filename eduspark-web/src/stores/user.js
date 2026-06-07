import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api/request'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const refreshToken = ref(localStorage.getItem('refreshToken') || '')
  const username = ref('')

  const isLoggedIn = computed(() => !!token.value)

  async function login(usernameVal, password) {
    const res = await api.post('/api/auth/login', {
      username: usernameVal,
      password
    })
    token.value = res.data.access_token
    refreshToken.value = res.data.refresh_token
    username.value = usernameVal
    localStorage.setItem('token', token.value)
    localStorage.setItem('refreshToken', refreshToken.value)
  }

  async function register(usernameVal, password) {
    await api.post('/api/auth/register', {
      username: usernameVal,
      password
    })
  }

  function logout() {
    token.value = ''
    refreshToken.value = ''
    username.value = ''
    localStorage.removeItem('token')
    localStorage.removeItem('refreshToken')
  }

  return { token, refreshToken, username, isLoggedIn, login, register, logout }
})
