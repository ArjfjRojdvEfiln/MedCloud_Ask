import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
      {
      path: '/patient/appointment',
      component: () => import('@/views/patient/AppointmentView.vue'),
},
    {
      path: '/',
      redirect: '/login',
    },
    {
      path: '/login',
      component: () => import('@/views/LoginView.vue'),
    },
    {
      path: '/admin',
      component: () => import('@/components/AdminLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: 'knowledge',
          component: () => import('@/views/admin/KnowledgeView.vue'),
        },
        {
          path: 'appointments',
          component: () => import('@/views/admin/AppointmentsView.vue'),
        },
        {
          path: 'articles',
          component: () => import('@/views/admin/ArticlesView.vue'),
        },
      ],
    },
    {
      path: '/patient/chat',
      component: () => import('@/views/patient/ChatView.vue'),
    },
  ],
})

router.beforeEach((to) => {
  const authStore = useAuthStore()
  if (to.meta.requiresAuth && !authStore.isLoggedIn()) {
    return '/login'
  }
})

export default router