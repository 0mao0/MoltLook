import { createRouter, createWebHistory } from 'vue-router'
import { messages } from '@/locales'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/dashboard'
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: () => import('../views/DashboardView.vue'),
      meta: { title: messages.zh.menu.dashboard, titleEn: messages.en.menu.dashboard }
    },
    {
      path: '/feed',
      name: 'feed',
      component: () => import('../views/FeedView.vue'),
      meta: { title: messages.zh.menu.feed, titleEn: messages.en.menu.feed }
    },
    {
      path: '/network',
      name: 'network',
      component: () => import('../views/NetworkView.vue'),
      meta: { title: messages.zh.menu.network, titleEn: messages.en.menu.network }
    },
    {
      path: '/agents',
      name: 'agents',
      component: () => import('../views/AgentsView.vue'),
      meta: { title: messages.zh.menu.agents, titleEn: messages.en.menu.agents }
    },
  ],
})

// 导航守卫：根据语言更新页面标题
router.afterEach((to) => {
  const lang = localStorage.getItem('locale') || 'zh' as 'zh' | 'en'
  const title = lang === 'zh' ? to.meta.title : to.meta.titleEn
  const appName = messages[lang as 'zh' | 'en'].app.name
  if (title) {
    document.title = `${title} - ${appName}`
  }
})

export default router
