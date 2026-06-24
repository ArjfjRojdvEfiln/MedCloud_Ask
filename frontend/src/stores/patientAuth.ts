import { defineStore } from 'pinia'
import { ref } from 'vue'

export const usePatientAuthStore = defineStore('patientAuth', () => {
  // 从 localStorage 恢复登录状态（刷新页面不丢失）
  const token = ref(localStorage.getItem('patient_token') || '')
  const patientId = ref(Number(localStorage.getItem('patient_id')) || 0)
  const phone = ref(localStorage.getItem('patient_phone') || '')
  const name = ref(localStorage.getItem('patient_name') || '')

  function setAuth(data: {
    access_token: string
    patient_id: number
    phone: string
    name: string
  }) {
    token.value = data.access_token
    patientId.value = data.patient_id
    phone.value = data.phone
    name.value = data.name
    // 持久化到 localStorage
    localStorage.setItem('patient_token', data.access_token)
    localStorage.setItem('patient_id', String(data.patient_id))
    localStorage.setItem('patient_phone', data.phone)
    localStorage.setItem('patient_name', data.name)
  }

  function logout() {
    token.value = ''
    patientId.value = 0
    phone.value = ''
    name.value = ''
    localStorage.removeItem('patient_token')
    localStorage.removeItem('patient_id')
    localStorage.removeItem('patient_phone')
    localStorage.removeItem('patient_name')
  }

  const isLoggedIn = () => !!token.value

  /** 登录后跳回原页面，token 从 URL 参数解析 */
  function handleCallback() {
    const params = new URLSearchParams(window.location.search)
    const urlToken = params.get('token')
    if (urlToken) {
      setAuth({
        access_token: urlToken,
        patient_id: Number(params.get('patient_id')) || 0,
        phone: params.get('phone') || '',
        name: params.get('name') || '',
      })
      // 清理 URL 中的 token，不暴露在地址栏
      const url = new URL(window.location.href)
      url.searchParams.delete('token')
      url.searchParams.delete('patient_id')
      url.searchParams.delete('phone')
      url.searchParams.delete('name')
      window.history.replaceState({}, '', url.toString())
      return true
    }
    return false
  }

  return { token, patientId, phone, name, setAuth, logout, isLoggedIn, handleCallback }
})
