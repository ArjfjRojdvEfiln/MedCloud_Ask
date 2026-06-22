import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  // 从 localStorage 恢复登录状态（刷新页面不丢失）
  const token = ref(localStorage.getItem('token') || '')
  const orgId = ref(Number(localStorage.getItem('orgId')) || 0)
  const orgName = ref(localStorage.getItem('orgName') || '')

  function setAuth(data: { access_token: string; org_id: number; org_name: string }) {
    token.value = data.access_token
    orgId.value = data.org_id
    orgName.value = data.org_name
    // 持久化到 localStorage
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('orgId', String(data.org_id))
    localStorage.setItem('orgName', data.org_name)
  }

  function logout() {
    token.value = ''
    orgId.value = 0
    orgName.value = ''
    localStorage.clear()
  }

  const isLoggedIn = () => !!token.value

  return { token, orgId, orgName, setAuth, logout, isLoggedIn }
})