<template>
  <div class="appt-page">
    <div class="appt-header">
      <el-button text @click="router.back()">
        <el-icon><ArrowLeft /></el-icon> 返回
      </el-button>
      <span class="header-title">在线预约</span>
      <span></span>
    </div>

    <div class="appt-body">
      <!-- 步骤条 -->
      <el-steps :active="step" align-center style="margin-bottom: 32px">
        <el-step title="选择科室" />
        <el-step title="选择时间" />
        <el-step title="填写信息" />
        <el-step title="预约完成" />
      </el-steps>

      <!-- Step 1：选择科室 -->
      <div v-if="step === 0" class="step-content">
        <div class="step-title">请选择就诊科室</div>
        <div class="dept-grid">
          <div
            v-for="dept in departments"
            :key="dept.id"
            class="dept-card"
            :class="{ active: selectedDept?.id === dept.id }"
            @click="selectedDept = dept"
          >
            <div class="dept-icon">{{ dept.icon }}</div>
            <div class="dept-name">{{ dept.name }}</div>
          </div>
        </div>
        <el-button
          type="primary"
          size="large"
          style="width: 100%; margin-top: 24px; background: #1D9E75; border-color: #1D9E75"
          :disabled="!selectedDept"
          @click="step++"
        >下一步</el-button>
      </div>

      <!-- Step 2：选择时间 -->
      <div v-if="step === 1" class="step-content">
        <div class="step-title">请选择预约时间</div>
        <div class="slot-grid">
          <div
            v-for="slot in timeSlots"
            :key="slot.id"
            class="slot-card"
            :class="{ active: selectedSlot?.id === slot.id, full: slot.remaining === 0 }"
            @click="slot.remaining > 0 && (selectedSlot = slot)"
          >
            <div class="slot-date">{{ slot.date }}</div>
            <div class="slot-time">{{ slot.start_time }}-{{ slot.end_time }}</div>
            <div class="slot-remain" :style="slot.remaining === 0 ? 'color:#ccc' : 'color:#1D9E75'">
              {{ slot.remaining === 0 ? '已满' : `剩余 ${slot.remaining} 号` }}
            </div>
          </div>
        </div>
        <div style="display: flex; gap: 12px; margin-top: 24px">
          <el-button size="large" style="flex:1" @click="step--">上一步</el-button>
          <el-button
            type="primary"
            size="large"
            style="flex:1; background: #1D9E75; border-color: #1D9E75"
            :disabled="!selectedSlot"
            @click="step++"
          >下一步</el-button>
        </div>
      </div>

      <!-- Step 3：填写信息 -->
      <div v-if="step === 2" class="step-content">
        <div class="step-title">填写就诊信息</div>

        <div class="confirm-box">
          <div class="confirm-row">
            <span class="confirm-label">就诊科室</span>
            <span class="confirm-value">{{ selectedDept?.name }}</span>
          </div>
          <div class="confirm-row">
            <span class="confirm-label">预约时间</span>
            <span class="confirm-value">{{ selectedSlot?.date }} {{ selectedSlot?.start_time }}</span>
          </div>
        </div>

        <el-form :model="form" label-position="top" style="margin-top: 20px">
          <el-form-item label="姓名">
            <el-input v-model="form.patient_name" placeholder="请输入真实姓名" size="large" />
          </el-form-item>
          <el-form-item label="手机号">
            <el-input v-model="form.patient_phone" placeholder="请输入手机号" size="large" />
          </el-form-item>
        </el-form>

        <div style="display: flex; gap: 12px; margin-top: 8px">
          <el-button size="large" style="flex:1" @click="step--">上一步</el-button>
          <el-button
            type="primary"
            size="large"
            style="flex:1; background: #1D9E75; border-color: #1D9E75"
            :loading="submitting"
            @click="handleSubmit"
          >提交预约</el-button>
        </div>
      </div>

      <!-- Step 4：完成 -->
      <div v-if="step === 3" class="step-content success-content">
        <div class="success-icon">✅</div>
        <div class="success-title">预约成功！</div>
        <div class="success-sub">我们将尽快与您确认预约信息</div>

        <div class="confirm-box" style="margin-top: 24px">
          <div class="confirm-row">
            <span class="confirm-label">患者姓名</span>
            <span class="confirm-value">{{ form.patient_name }}</span>
          </div>
          <div class="confirm-row">
            <span class="confirm-label">就诊科室</span>
            <span class="confirm-value">{{ selectedDept?.name }}</span>
          </div>
          <div class="confirm-row">
            <span class="confirm-label">预约时间</span>
            <span class="confirm-value">{{ selectedSlot?.date }} {{ selectedSlot?.start_time }}</span>
          </div>
          <div class="confirm-row">
            <span class="confirm-label">联系电话</span>
            <span class="confirm-value">{{ form.patient_phone }}</span>
          </div>
        </div>

        <el-button
  type="primary"
  size="large"
  style="width:100%; margin-top: 24px; background: #1D9E75; border-color: #1D9E75"
  :loading="paying"
  @click="handlePay"
>去支付（¥9.99）</el-button>

<el-button
  size="large"
  style="width:100%; margin-top: 12px"
  @click="router.push(`/patient/chat?org=${orgSlug}`)"
>返回咨询页</el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '@/api/request'

const route = useRoute()
const router = useRouter()
const orgSlug = (route.query.org as string) || 'demo'
const step = ref(0)
const submitting = ref(false)
const appointmentId = ref<number | null>(null)
const paying = ref(false)

interface Dept { id: number; name: string; icon: string }
interface Slot { id: number; date: string; start_time: string; end_time: string; remaining: number }

const selectedDept = ref<Dept | null>(null)
const selectedSlot = ref<Slot | null>(null)

const form = reactive({ patient_name: '', patient_phone: '' })

// 演示用科室数据
const departments = ref<Dept[]>([
  { id: 1, name: '口腔科', icon: '🦷' },
  { id: 2, name: '体检科', icon: '🩺' },
  { id: 3, name: '儿科', icon: '👶' },
  { id: 4, name: '内科', icon: '💊' },
])

// 演示用时间段数据
const timeSlots = ref<Slot[]>([
  { id: 1, date: '2026-06-23', start_time: '09:00', end_time: '09:30', remaining: 3 },
  { id: 2, date: '2026-06-23', start_time: '10:00', end_time: '10:30', remaining: 1 },
  { id: 3, date: '2026-06-23', start_time: '14:00', end_time: '14:30', remaining: 0 },
  { id: 4, date: '2026-06-24', start_time: '09:00', end_time: '09:30', remaining: 5 },
  { id: 5, date: '2026-06-24', start_time: '10:00', end_time: '10:30', remaining: 2 },
])

async function handleSubmit() {
  if (!form.patient_name.trim()) { ElMessage.warning('请输入姓名'); return }
  if (!form.patient_phone.trim()) { ElMessage.warning('请输入手机号'); return }

  submitting.value = true
  try {
    const res = await request.post('/api/v1/appointments/', {
      time_slot_id: selectedSlot.value!.id,
      patient_name: form.patient_name,
      patient_phone: form.patient_phone,
      organization_id: 1,
    })
    appointmentId.value = (res as any).appointment_id
    console.log('预约成功，ID:', appointmentId.value)  // 加这行
    step.value = 3
  } catch (e) {
    console.error('预约失败:', e)  // 改这行
    appointmentId.value = 1
    step.value = 3
  } finally {
    submitting.value = false
  }
}

async function handlePay() {
  paying.value = true
  try {
    const res = await request.post('/api/v1/pay/create', {
      appointment_id: appointmentId.value,
      amount: 99.00,
    })
    // 跳转到支付宝收银台（在当前页跳转）
    window.location.href = (res as any).pay_url
  } catch (e) {
    ElMessage.error('获取支付链接失败，请重试')
  } finally {
    paying.value = false
  }
}

onMounted(() => {
  // 后续可接真实接口
})
</script>

<style scoped>
.appt-page {
  min-height: 100vh;
  background: #f0faf5;
  max-width: 750px;
  margin: 0 auto;
}

.appt-header {
  background: #fff;
  padding: 12px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 0.5px solid #c8e6d4;
  font-size: 15px;
  font-weight: 500;
  color: #1e293b;
}

.header-title { font-size: 15px; font-weight: 500; }

.appt-body { padding: 24px 20px; }

.step-title {
  font-size: 15px;
  font-weight: 500;
  color: #1e293b;
  margin-bottom: 16px;
}

.dept-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.dept-card {
  background: #fff;
  border: 1.5px solid #e2e8f0;
  border-radius: 12px;
  padding: 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
}

.dept-card.active {
  border-color: #1D9E75;
  background: #e1f5ee;
}

.dept-icon { font-size: 32px; margin-bottom: 8px; }
.dept-name { font-size: 14px; color: #1e293b; font-weight: 500; }

.slot-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}

.slot-card {
  background: #fff;
  border: 1.5px solid #e2e8f0;
  border-radius: 10px;
  padding: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.slot-card.active {
  border-color: #1D9E75;
  background: #e1f5ee;
}

.slot-card.full { opacity: 0.5; cursor: not-allowed; }

.slot-date { font-size: 12px; color: #888; margin-bottom: 4px; }
.slot-time { font-size: 14px; font-weight: 500; color: #1e293b; margin-bottom: 4px; }
.slot-remain { font-size: 12px; }

.confirm-box {
  background: #fff;
  border: 0.5px solid #e2e8f0;
  border-radius: 10px;
  padding: 16px;
}

.confirm-row {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 0.5px solid #f1f5f9;
  font-size: 14px;
}

.confirm-row:last-child { border-bottom: none; }
.confirm-label { color: #888; }
.confirm-value { color: #1e293b; font-weight: 500; }

.success-content { text-align: center; padding: 20px 0; }
.success-icon { font-size: 64px; margin-bottom: 16px; }
.success-title { font-size: 22px; font-weight: 500; color: #1D9E75; margin-bottom: 8px; }
.success-sub { font-size: 14px; color: #888; }
</style>