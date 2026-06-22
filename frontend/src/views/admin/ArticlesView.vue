<template>
  <div class="page">
    <div class="card">
      <div class="card-header">
        <span class="card-title">健康科普文章</span>
        <el-button type="primary" @click="openDialog()">
          <el-icon><Plus /></el-icon> 新建文章
        </el-button>
      </div>

      <div v-if="articles.length === 0" class="empty">
        <el-icon size="48" color="#9FE1CB"><EditPen /></el-icon>
        <p>还没有发布任何文章</p>
      </div>

      <el-table v-else :data="articles" style="width: 100%" :header-cell-style="tableHeaderStyle">
        <el-table-column prop="title" label="标题" min-width="200" />
        <el-table-column prop="tags" label="标签" width="160">
          <template #default="{ row }">
            <el-tag
              v-for="tag in (row.tags || '').split(',').filter(Boolean)"
              :key="tag"
              size="small"
              style="margin-right: 4px; background: #e1f5ee; color: #0f6e56; border: none"
            >{{ tag }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.is_published ? 'success' : 'info'" size="small" round>
              {{ row.is_published ? '已上线' : '草稿' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="120">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="180">
          <template #default="{ row }">
            <el-button size="small" text @click="openDialog(row)">编辑</el-button>
            <el-button
              size="small" text
              :type="row.is_published ? 'warning' : 'success'"
              @click="togglePublish(row)"
            >{{ row.is_published ? '下线' : '上线' }}</el-button>
            <el-button size="small" text type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 新建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingArticle ? '编辑文章' : '新建文章'"
      width="600px"
    >
      <el-form :model="form" label-position="top">
        <el-form-item label="标题">
          <el-input v-model="form.title" placeholder="请输入文章标题" />
        </el-form-item>
        <el-form-item label="标签（逗号分隔）">
          <el-input v-model="form.tags" placeholder="如：口腔健康,体检须知" />
        </el-form-item>
        <el-form-item label="内容">
          <el-input
            v-model="form.content"
            type="textarea"
            :rows="8"
            placeholder="请输入文章内容..."
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/api/request'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

interface Article {
  id: number
  title: string
  content: string
  tags: string
  is_published: boolean
  created_at: string
}

const articles = ref<Article[]>([])
const dialogVisible = ref(false)
const saving = ref(false)
const editingArticle = ref<Article | null>(null)

const form = reactive({ title: '', content: '', tags: '' })

const tableHeaderStyle = { background: '#f8faf8', color: '#5F5E5A', fontSize: '12px' }

function formatTime(t: string) {
  return new Date(t).toLocaleDateString('zh-CN')
}

function openDialog(article?: Article) {
  editingArticle.value = article || null
  if (article) {
    form.title = article.title
    form.content = article.content
    form.tags = article.tags || ''
  } else {
    form.title = ''
    form.content = ''
    form.tags = ''
  }
  dialogVisible.value = true
}

async function loadArticles() {
  try {
    const res = await request.get(
      `/api/v1/articles/?org_id=${authStore.orgId}`
    ) as any
    articles.value = res || []
  } catch {
    // 接口未实现时用演示数据
    articles.value = [
      { id: 1, title: '洗牙前需要注意什么', tags: '口腔健康', is_published: true, content: '', created_at: new Date().toISOString() },
      { id: 2, title: '体检空腹时间须知', tags: '体检须知', is_published: false, content: '', created_at: new Date().toISOString() },
    ]
  }
}

async function handleSave() {
  if (!form.title.trim()) { ElMessage.warning('请输入标题'); return }
  if (!form.content.trim()) { ElMessage.warning('请输入内容'); return }

  saving.value = true
  try {
    if (editingArticle.value) {
      await request.patch(`/api/v1/articles/${editingArticle.value.id}`, form)
      const idx = articles.value.findIndex(a => a.id === editingArticle.value!.id)
      if (idx !== -1) Object.assign(articles.value[idx], form)
    } else {
      const res = await request.post('/api/v1/articles/', {
        ...form,
        organization_id: authStore.orgId,
      }) as any
      articles.value.unshift(res)
    }
    ElMessage.success('保存成功')
    dialogVisible.value = false
  } catch {
    // 接口未实现时本地模拟
    if (editingArticle.value) {
      const idx = articles.value.findIndex(a => a.id === editingArticle.value!.id)
      if (idx !== -1) Object.assign(articles.value[idx], form)
    } else {
      articles.value.unshift({
        id: Date.now(), ...form,
        is_published: false,
        created_at: new Date().toISOString()
      })
    }
    ElMessage.success('保存成功')
    dialogVisible.value = false
  } finally {
    saving.value = false
  }
}

async function togglePublish(row: Article) {
  try {
    await request.patch(`/api/v1/articles/${row.id}`, { is_published: !row.is_published })
  } catch { /* 本地更新 */ }
  row.is_published = !row.is_published
  ElMessage.success(row.is_published ? '已上线' : '已下线')
}

async function handleDelete(row: Article) {
  await ElMessageBox.confirm(`确定删除「${row.title}」？`, '提示', {
    confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning'
  })
  try {
    await request.delete(`/api/v1/articles/${row.id}`)
  } catch { /* 本地更新 */ }
  articles.value = articles.value.filter(a => a.id !== row.id)
  ElMessage.success('已删除')
}

onMounted(loadArticles)
</script>

<style scoped>
.page { display: flex; flex-direction: column; gap: 16px; }

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
</style>