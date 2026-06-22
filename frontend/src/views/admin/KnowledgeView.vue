<template>
  <div class="page">
    <!-- 顶部统计卡片 -->
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-label">已上传文档</div>
        <div class="stat-value">{{ documents.length }}</div>
        <div class="stat-sub">份文件</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">已就绪</div>
        <div class="stat-value">{{ readyCount }}</div>
        <div class="stat-sub">可用于问答</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">处理中</div>
        <div class="stat-value">{{ processingCount }}</div>
        <div class="stat-sub">Dify 向量化中</div>
      </div>
    </div>

    <!-- 文档列表卡片 -->
    <div class="card">
      <div class="card-header">
        <span class="card-title">知识库文档</span>
        <el-upload
          :before-upload="handleUpload"
          :show-file-list="false"
          accept=".pdf,.txt,.docx"
        >
          <el-button type="primary" :loading="uploading">
            <el-icon><Upload /></el-icon> 上传文档
          </el-button>
        </el-upload>
      </div>

      <!-- 空状态 -->
      <div v-if="documents.length === 0" class="empty">
        <el-icon size="48" color="#9FE1CB"><Document /></el-icon>
        <p>还没有上传任何文档</p>
        <p class="empty-sub">上传 PDF、TXT 或 DOCX，AI 将基于这些内容回答患者问题</p>
      </div>

      <!-- 文档列表 -->
      <div v-else class="file-list">
        <div
          v-for="doc in documents"
          :key="doc.id"
          class="file-row"
        >
          <div class="file-icon">
            <el-icon><Document /></el-icon>
          </div>
          <div class="file-info">
            <span class="file-name">{{ doc.filename }}</span>
            <span class="file-time">{{ formatTime(doc.created_at) }}</span>
          </div>
          <el-tag
            :type="doc.status === 'ready' ? 'success' : doc.status === 'failed' ? 'danger' : 'warning'"
            size="small"
            round
          >
            {{ statusLabel(doc.status) }}
          </el-tag>
        </div>
      </div>
    </div>

    <!-- 上传提示 -->
    <div class="tip-card">
      <el-icon color="#1D9E75"><InfoFilled /></el-icon>
      <span>支持 PDF、TXT、DOCX 格式，单文件不超过 15MB。上传后 Dify 将自动解析并建立向量索引，处理完成后状态变为"已就绪"。</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/api/request'

interface DocItem {
  id: number
  filename: string
  status: string
  created_at: string
}

const documents = ref<DocItem[]>([])
const uploading = ref(false)

// 计算属性
const readyCount = computed(() => documents.value.filter(d => d.status === 'ready').length)
const processingCount = computed(() => documents.value.filter(d => d.status === 'processing').length)

// 状态标签
function statusLabel(status: string) {
  const map: Record<string, string> = {
    ready: '已就绪',
    processing: '处理中',
    failed: '失败',
  }
  return map[status] || status
}

// 格式化时间
function formatTime(t: string) {
  return new Date(t).toLocaleString('zh-CN', {
    month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit'
  })
}

// 上传文件
async function handleUpload(file: File) {
  uploading.value = true
  const formData = new FormData()
  formData.append('file', file)
  try {
    await request.post('/api/v1/knowledge/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    ElMessage.success('上传成功，Dify 处理中...')
    // 本地先插入一条，状态 processing
    documents.value.unshift({
      id: Date.now(),
      filename: file.name,
      status: 'processing',
      created_at: new Date().toISOString(),
    })
  } catch {
    // 错误已在拦截器处理
  } finally {
    uploading.value = false
  }
  return false  // 阻止 el-upload 默认上传行为
}

onMounted(() => {
  // 暂时用空数组，后续接口有列表再接
  documents.value = []
})
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
.stat-value { font-size: 28px; font-weight: 500; color: #1D9E75; }
.stat-sub { font-size: 11px; color: #9FE1CB; margin-top: 2px; }

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
.empty-sub { font-size: 12px; color: #bbb; margin-top: 4px !important; }

.file-list { display: flex; flex-direction: column; }

.file-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 0.5px solid #f1f5f9;
}

.file-row:last-child { border-bottom: none; }

.file-icon {
  width: 36px;
  height: 36px;
  background: #e1f5ee;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #1D9E75;
  font-size: 18px;
  flex-shrink: 0;
}

.file-info { flex: 1; display: flex; flex-direction: column; gap: 2px; }
.file-name { font-size: 13px; color: #1e293b; }
.file-time { font-size: 11px; color: #94a3b8; }

.tip-card {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  background: #e1f5ee;
  border: 0.5px solid #9FE1CB;
  border-radius: 8px;
  padding: 12px 16px;
  font-size: 12px;
  color: #0F6E56;
  line-height: 1.7;
}
</style>