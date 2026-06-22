<template>
  <div class="page">
    <!-- 统计卡片 -->
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-label">待确认</div>
        <div class="stat-value">{{ pendingList.length }}</div>
        <div class="stat-sub">条预约</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">已确认</div>
        <div class="stat-value" style="color: #1D9E75">{{ confirmedList.length }}</div>
        <div class="stat-sub">条预约</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">已取消</div>
        <div class="stat-value" style="color: #888">{{ cancelledList.length }}</div>
        <div class="stat-sub">条预约</div>
      </div>
    </div>

    <!-- 预约列表 -->
    <div class="card">
      <div class="card-header">
        <span class="card-title">预约记录</span>
        <el-radio-group v-model="filterStatus" size="small">
          <el-radio-button value="all">全部</el-radio-button>
          <el-radio-button value="pending">待确认</el-radio-button>
          <el-radio-button value="confirmed">已确认</el-radio-button>
          <el-radio-button value="cancelled">已取消</el-radio-button>
        </el-radio-group>
      </div>

      <div v-if="loading" class="loading">
        <el-icon class="is-loading"><Loading /></el-icon> 加载中...
      </div>

      <div v-else-if="filteredList.length === 0" class="empty">
        <el-icon size="48" color="#9FE1CB"><Calendar /></el-icon>
        <p>暂无预约记录</p>
      </div>

      <el-table v-else :data="filteredList" style="width: 100%" :header-cell-style="tableHeaderStyle">
        <el-table-column prop="patient_name" label="患者姓名" width="100" />
        <el-table-column prop="patient_phone" label="手机号" width="130" />
        <el-table-column prop="department_name" label="科室" width="120" />
        <el-table-column prop="slot_date" label="预约日期" width="110" />
        <el-table-column prop="slot_time" label="时间段" width="120" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag
              :type="statusType(row.status)"
              size="small"
              round
            >
              {{ statusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="150">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'pending'"
              type="success"
              size="small"
              text
              @click="handleConfirm(row)"
            >确认</el-button>
            <el-button
              v-if="row.status === 'pending'"
              type="danger"
              size="small"
              text
              @click="handleCancel(row)"
            >取消</el-button>
            <span v-if="row.status !== 'pending'" style="color: #ccc; font-size: 12px">—</span>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/api/request'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

interface Appointment {
  id: number
  patient_name: string
  patient_phone: string
  department_name: string
  slot_date: string
  slot_time: string
  status: string
}

const appointments = ref<Appointment[]>([])
const filterStatus = ref('all')
const loading = ref(false)

const pendingList = computed(() => appointments.value.filter(a => a.status === 'pending'))
const confirmedList = computed(() => appointments.value.filter(a => a.status === 'confirmed'))
const cancelledList = computed(() => appointments.value.filter(a => a.status === 'cancelled'))

const filteredList = computed(() => {
  if (filterStatus.value === 'all') return appointments.value
  return appointments.value.filter(a => a.status === filterStatus.value)
})

const tableHeaderStyle = { background: '#f8faf8', color: '#5F5E5A', fontSize: '12px' }

function statusLabel(status: string) {
  const map: Record<string, string> = {
    pending: '待确认', confirmed: '已确认', cancelled: '已取消'
  }
  return map[status] || status
}

function statusType(status: string) {
  const map: Record<string, string> = {
    pending: 'warning', confirmed: 'success', cancelled: 'info'
  }
  return map[status] || ''
}

async function loadAppointments() {
  loading.value = true
  try {
    const res = await request.get(
      `/api/v1/appointments/?org_id=${authStore.orgId}`
    ) as any
    appointments.value = res || []
  } catch {
    // 接口还没实现时显示演示数据
    appointments.value = [
      { id: 1, patient_name: '张三', patient_phone: '138****0001', department_name: '口腔科', slot_date: '2026-06-23', slot_time: '09:00-09:30', status: 'pending' },
      { id: 2, patient_name: '李四', patient_phone: '139****0002', department_name: '体检科', slot_date: '2026-06-23', slot_time: '10:00-10:30', status: 'confirmed' },
      { id: 3, patient_name: '王五', patient_phone: '137****0003', department_name: '口腔科', slot_date: '2026-06-22', slot_time: '14:00-14:30', status: 'cancelled' },
    ]
  } finally {
    loading.value = false
  }
}

async function handleConfirm(row: Appointment) {
  await ElMessageBox.confirm(`确认 ${row.patient_name} 的预约？`, '提示', {
    confirmButtonText: '确认',
    cancelButtonText: '取消',
    type: 'warning',
  })
  try {
    await request.patch(`/api/v1/appointments/${row.id}`, { status: 'confirmed' })
    row.status = 'confirmed'
    ElMessage.success('已确认')
  } catch {
    row.status = 'confirmed'  // 接口未实现时本地更新
    ElMessage.success('已确认')
  }
}

async function handleCancel(row: Appointment) {
  await ElMessageBox.confirm(`取消 ${row.patient_name} 的预约？`, '提示', {
    confirmButtonText: '确认取消',
    cancelButtonText: '返回',
    type: 'warning',
  })
  try {
    await request.patch(`/api/v1/appointments/${row.id}`, { status: 'cancelled' })
    row.status = 'cancelled'
    ElMessage.success('已取消')
  } catch {
    row.status = 'cancelled'
    ElMessage.success('已取消')
  }
}

onMounted(loadAppointments)
</script>

<style scoped>
.page { display: flex; flex-direction: column; gap: 16px; }

.stats-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.stat-card {
  background: #fff;
  border: 0.5px solid #e2e8f0;
  border-radius: 10px;
  padding: 16px 20px;
}

.stat-label { font-size: 12px; color: #888; margin-bottom: 6px; }
.stat-value { font-size: 28px; font-weight: 500; color: #e8a020; }
.stat-sub { font-size: 11px; color: #bbb; margin-top: 2px; }

.card {
  background: #fff;
  border: 0.5px solid #e2e8f0;
  border-radius: 12px;
  padding: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.card-title { font-size: 14px; font-weight: 500; color: #1e293b; }

.empty {
  text-align: center;
  padding: 40px 0;
  color: #888;
}

.empty p { margin-top: 8px; font-size: 14px; }

.loading {
  text-align: center;
  padding: 40px 0;
  color: #888;
  font-size: 14px;
}
</style>