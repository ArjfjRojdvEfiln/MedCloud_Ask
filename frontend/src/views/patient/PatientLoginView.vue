<template>
  <div class="login-container">
    <el-card class="login-card">
      <!-- 标题 -->
      <div class="login-header">
        <h2>患者登录</h2>
        <p>登录后可管理预约记录</p>
      </div>

      <!-- Tab 切换 -->
      <el-tabs v-model="activeTab" class="login-tabs">
        <!-- ========== Tab 1：验证码登录 ========== -->
        <el-tab-pane label="验证码登录" name="sms">
          <el-form :model="smsForm" :rules="smsRules" ref="smsFormRef" label-position="top">
            <el-form-item label="手机号" prop="phone">
              <el-input
                v-model="smsForm.phone"
                placeholder="请输入手机号"
                size="large"
                maxlength="11"
              />
            </el-form-item>

            <el-form-item label="验证码" prop="code">
              <div class="code-row">
                <el-input
                  v-model="smsForm.code"
                  placeholder="请输入验证码"
                  size="large"
                  maxlength="6"
                  style="flex: 1"
                />
                <el-button
                  size="large"
                  :disabled="countdown > 0 || !smsForm.phone"
                  @click="handleSendCode"
                  class="code-btn"
                >
                  {{ countdown > 0 ? `${countdown}s 后重发` : '获取验证码' }}
                </el-button>
              </div>
            </el-form-item>

            <el-button
              type="primary"
              size="large"
              style="width: 100%; margin-top: 8px"
              :loading="smsLoading"
              @click="handleSmsLogin"
            >
              登录
            </el-button>
          </el-form>
        </el-tab-pane>

        <!-- ========== Tab 2：微信登录 ========== -->
        <el-tab-pane label="微信登录" name="wechat">
          <div class="wechat-section">
            <!-- 微信扫码提示区 -->
            <div class="wechat-qr-hint">
              <div class="qr-placeholder">🟢</div>
              <p class="qr-text">点击下方按钮，使用微信扫码登录</p>
            </div>

            <el-button
              type="success"
              size="large"
              style="width: 100%; margin-top: 12px"
              :loading="wechatLoading"
              @click="handleWechatLogin"
            >
              微信扫码登录
            </el-button>

            <!-- 开发模式：模拟微信登录 -->
            <div v-if="showMockWechat" class="mock-section">
              <el-divider content-position="center">
                <span style="color: #909399; font-size: 12px">开发模式 — 模拟微信登录</span>
              </el-divider>
              <el-input
                v-model="mockOpenid"
                placeholder="输入模拟 openid（任意字符）"
                size="default"
                style="margin-bottom: 8px"
              />
              <el-button
                size="default"
                style="width: 100%"
                :loading="mockLoading"
                @click="handleMockWechatLogin"
              >
                模拟登录
              </el-button>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance } from 'element-plus'
import request from '@/api/request'
import { usePatientAuthStore } from '@/stores/patientAuth'

const route = useRoute()
const router = useRouter()
const patientAuth = usePatientAuthStore()

// ── 从 URL 获取上下文 ────────────────────────────────
const orgSlug = (route.query.org as string) || 'demo'
const redirect = (route.query.redirect as string) || `/patient/chat?org=${orgSlug}`

// ── Tab 状态 ────────────────────────────────────────
const activeTab = ref('sms')

// ── 验证码登录 ──────────────────────────────────────
const smsForm = reactive({ phone: '', code: '' })
const smsFormRef = ref<FormInstance>()
const smsLoading = ref(false)
const countdown = ref(0)
let countdownTimer: ReturnType<typeof setInterval> | null = null

const smsRules = {
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '手机号格式不正确', trigger: 'blur' },
  ],
  code: [{ required: true, message: '请输入验证码', trigger: 'blur' }],
}

async function handleSendCode() {
  if (!smsForm.phone || !/^1[3-9]\d{9}$/.test(smsForm.phone)) {
    ElMessage.warning('请先输入正确的手机号')
    return
  }
  try {
    await request.post('/api/v1/patient/send-code', {
      phone: smsForm.phone,
      institution_id: 1, // TODO: 后续从 orgSlug 解析 institution_id
    })
    ElMessage.success('验证码已发送（演示阶段：123456）')
    // 60 秒倒计时
    countdown.value = 60
    countdownTimer = setInterval(() => {
      countdown.value--
      if (countdown.value <= 0 && countdownTimer) {
        clearInterval(countdownTimer)
        countdownTimer = null
      }
    }, 1000)
  } catch {
    // request.ts 拦截器已弹错误提示
  }
}

async function handleSmsLogin() {
  await smsFormRef.value?.validate()
  smsLoading.value = true
  try {
    const res = (await request.post('/api/v1/patient/login', {
      phone: smsForm.phone,
      institution_id: 1, // TODO: 后续从 orgSlug 解析
      code: smsForm.code,
    })) as any
    patientAuth.setAuth(res)
    ElMessage.success('登录成功')
    router.push(redirect)
  } catch {
    // request.ts 拦截器已弹错误提示
  } finally {
    smsLoading.value = false
  }
}

// ── 微信登录 ────────────────────────────────────────
const wechatLoading = ref(false)
const showMockWechat = ref(false)
const mockOpenid = ref('')
const mockLoading = ref(false)

async function handleWechatLogin() {
  wechatLoading.value = true
  try {
    const fullRedirect = window.location.origin + redirect
    const redirectParams = encodeURIComponent(fullRedirect)
    const res = (await request.get(
      `/api/v1/patient/wechat/auth-url?redirect_uri=${redirectParams}`
    )) as any
    // 跳转到微信授权页
    window.location.href = res.auth_url
  } catch {
    wechatLoading.value = false
  }
}

async function handleMockWechatLogin() {
  if (!mockOpenid.value.trim()) {
    ElMessage.warning('请输入模拟 openid')
    return
  }
  mockLoading.value = true
  try {
    const res = (await request.post('/api/v1/patient/wechat/mock-login', {
      openid: mockOpenid.value.trim(),
      institution_id: 1,
    })) as any
    patientAuth.setAuth(res)
    ElMessage.success('模拟登录成功')
    router.push(redirect)
  } catch {
    // request.ts 拦截器已弹错误提示
  } finally {
    mockLoading.value = false
  }
}

// ── 检查是否为开发模式 ──────────────────────────────
onMounted(async () => {
  // 通过调一次 auth-url 来判断：dev 返回的是本地回调地址，不是微信域名
  try {
    const res = (await request.get('/api/v1/patient/wechat/auth-url')) as any
    if (res.auth_url && !res.auth_url.includes('open.weixin.qq.com')) {
      showMockWechat.value = true
    }
  } catch {
    // 接口不可用时不展示模拟区
  }
})
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
  margin-bottom: 16px;
}

.login-header h2 {
  font-size: 24px;
  color: #303133;
  margin-bottom: 6px;
}

.login-header p {
  color: #909399;
  font-size: 13px;
}

.login-tabs :deep(.el-tabs__header) {
  margin-bottom: 8px;
}

.login-tabs :deep(.el-tabs__active-bar) {
  background-color: #1D9E75;
}

.login-tabs :deep(.el-tabs__item.is-active) {
  color: #1D9E75;
}

.login-tabs :deep(.el-tabs__item:hover) {
  color: #1D9E75;
}

/* 验证码行 */
.code-row {
  display: flex;
  gap: 10px;
}

.code-btn {
  min-width: 130px;
  border-color: #1D9E75;
  color: #1D9E75;
  white-space: nowrap;
}

.code-btn:hover {
  background: #e1f5ee;
  border-color: #0f6e56;
  color: #0f6e56;
}

/* 微信扫码区 */
.wechat-section {
  text-align: center;
  padding: 8px 0;
}

.wechat-qr-hint {
  padding: 32px 0;
}

.qr-placeholder {
  font-size: 80px;
  margin-bottom: 12px;
}

.qr-text {
  color: #909399;
  font-size: 14px;
}

/* 开发模式模拟区 */
.mock-section {
  margin-top: 16px;
}

/* 全局按钮色 */
:deep(.el-button--primary) {
  background-color: #1D9E75;
  border-color: #1D9E75;
}

:deep(.el-button--primary:hover) {
  background-color: #0f6e56;
  border-color: #0f6e56;
}

:deep(.el-button--success) {
  background-color: #07C160;
  border-color: #07C160;
}

:deep(.el-button--success:hover) {
  background-color: #06AD56;
  border-color: #06AD56;
}
</style>
