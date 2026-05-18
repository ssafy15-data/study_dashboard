import { createRouter, createWebHistory } from 'vue-router'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'dashboard', component: () => import('@/views/DashboardView.vue') },
    { path: '/member/:id', name: 'member', component: () => import('@/views/MemberView.vue') },
    { path: '/stats', name: 'stats', component: () => import('@/views/StatsView.vue') },
  ],
})

