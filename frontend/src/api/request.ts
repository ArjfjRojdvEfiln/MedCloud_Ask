import axios from 'axios'
import { ElMessage } from 'element-plus'

const request = axios.create({
  baseURL: 'http://localhost:8000',  // 后端地址
  timeout: 30000,
})

// 请求拦截器：每个请求自动带上 token
request.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器：统一处理错误
request.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const msg = error.response?.data?.detail || '请求失败'
    // 404 和 405 是接口未实现，静默处理不弹红色提示
    if (error.response?.status !== 404 && error.response?.status !== 405) {
      ElMessage.error(msg)
    }
    // token 过期，跳回登录页
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default request