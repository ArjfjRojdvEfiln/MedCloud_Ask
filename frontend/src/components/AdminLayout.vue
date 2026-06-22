<template>
  <el-container class="admin-container">
    <!-- 侧边栏 -->
    <el-aside width="220px" class="aside">
      <div class="logo">
        <span>🏥 医云问</span>
        <p>{{ authStore.orgName }}</p>
      </div>

      <el-menu
        :default-active="route.path"
        router
        background-color="#f0faf5"
        text-color="#5F5E5A"
        active-text-color="#0f6e56"
      >
        <el-menu-item index="/admin/knowledge">
          <el-icon><Document /></el-icon>
          <span>知识库管理</span>
        </el-menu-item>
        <el-menu-item index="/admin/appointments">
          <el-icon><Calendar /></el-icon>
          <span>预约管理</span>
        </el-menu-item>
        <el-menu-item index="/admin/articles">
          <el-icon><EditPen /></el-icon>
          <span>文章管理</span>
        </el-menu-item>
      </el-menu>

      <div class="logout-btn">
        <el-button text style="color: #94a3b8" @click="handleLogout">
          <el-icon><SwitchButton /></el-icon> 退出登录
        </el-button>
      </div>
    </el-aside>

    <!-- 右侧内容区 -->
    <el-container>
      <el-header class="header">
        <span class="page-title">{{ pageTitle }}</span>
      </el-header>
      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

// 根据路由自动显示页面标题
const pageTitle = computed(() => {
  const map: Record<string, string> = {
    '/admin/knowledge': '知识库管理',
    '/admin/appointments': '预约管理',
    '/admin/articles': '文章管理',
  }
  return map[route.path] || '管理后台'
})

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.admin-container {
  height: 100vh;
}

.aside {
  background-color: #f0faf5;
  display: flex;
  flex-direction: column;
}

.logo {
  padding: 24px 20px;
  border-bottom: 1px solid #c8e6d4;
}

.logo span {
  font-size: 18px;
  font-weight: 600;
  color: #0f6e56;
}

.logo p {
  font-size: 12px;
  color: #5DCAA5;
  margin-top: 4px;
}

.logout-btn {
  margin-top: auto;
  padding: 16px;
  border-top: 1px solid #c8e6d4;
}

.header {
  background: #ffffff;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  align-items: center;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

.page-title {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
}

.main {
  background: #f8fafc;
}
</style>