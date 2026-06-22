<template>
  <div class="login-container">
    <el-card class="login-card">
      <div class="login-header">
        <h2>医云问</h2>
        <p>中小医疗机构 AI 智能客服平台</p>
      </div>

      <el-form :model="form" :rules="rules" ref="formRef" label-position="top">
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="form.username"
            placeholder="请输入用户名"
            prefix-icon="User"
            size="large"
          />
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            prefix-icon="Lock"
            size="large"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <el-button
          type="primary"
          size="large"
          style="width: 100%; margin-top: 8px"
          :loading="loading"
          @click="handleLogin"
        >
          登录
        </el-button>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance } from 'element-plus'
import request from '@/api/request'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

// 表单数据
const form = reactive({
  username: '',
  password: '',
})

// 表单校验规则
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

const formRef = ref<FormInstance>()
const loading = ref(false)

async function handleLogin() {
  // 先触发前端校验
  await formRef.value?.validate()

  loading.value = true
  try {
    const res = await request.post('/api/v1/auth/login', form) as any
    // 存 token 和机构信息
    authStore.setAuth(res)
    ElMessage.success('登录成功')
    router.push('/admin/knowledge')
  } catch {
    // 错误已在 request.ts 拦截器里统一弹出，这里不重复处理
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0faf5;
}

.login-card {
  width: 420px;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-header h2 {
  font-size: 28px;
  color: #303133;
  margin-bottom: 8px;
}

.login-header p {
  color: #909399;
  font-size: 14px;
}

:deep(.el-button--primary) {
  background-color: #1D9E75;
  border-color: #1D9E75;
}

:deep(.el-button--primary:hover) {
  background-color: #0f6e56;
  border-color: #0f6e56;
}
</style>