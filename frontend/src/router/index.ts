import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/chat',
    },
    {
      path: '/chat',
      name: 'Chat',
      component: () => import('@/views/Conversations.vue'),
      meta: { title: '对话', icon: 'chatbubbles' },
    },
    {
      path: '/dashboard',
      name: 'Dashboard',
      component: () => import('@/views/Dashboard.vue'),
      meta: { title: '仪表盘', icon: 'home' },
    },
    {
      path: '/characters',
      name: 'Characters',
      component: () => import('@/views/Characters.vue'),
      meta: { title: '角色管理', icon: 'people' },
    },
    {
      path: '/worldbooks',
      name: 'WorldBooks',
      component: () => import('@/views/WorldBooks.vue'),
      meta: { title: '世界书', icon: 'book' },
    },
    {
      path: '/presets',
      name: 'Presets',
      component: () => import('@/views/Presets.vue'),
      meta: { title: '预设管理', icon: 'settings' },
    },
    {
      path: '/models',
      name: 'Models',
      component: () => import('@/views/Models.vue'),
      meta: { title: '模型配置', icon: 'hardware-chip' },
    },
    {
      path: '/platforms',
      name: 'Platforms',
      component: () => import('@/views/Platforms.vue'),
      meta: { title: '平台连接', icon: 'cloud' },
    },
    {
      path: '/proactive',
      name: 'Proactive',
      component: () => import('@/views/Proactive.vue'),
      meta: { title: '主动交互', icon: 'notifications' },
    },
    {
      path: '/memories',
      name: 'Memories',
      component: () => import('@/views/Memories.vue'),
      meta: { title: '记忆管理', icon: 'brain' },
    },
    {
      path: '/settings',
      name: 'Settings',
      component: () => import('@/views/Settings.vue'),
      meta: { title: '系统设置', icon: 'cog' },
    },
  ],
})

export default router
