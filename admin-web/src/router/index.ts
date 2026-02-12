import { createRouter, createWebHashHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/login', name: 'Login', component: () => import('@/views/Login.vue'), meta: { public: true } },
    {
      path: '/',
      component: () => import('@/views/Layout.vue'),
      meta: { requiresAuth: true },
      children: [
        { path: '', redirect: '/statistics' },
        { path: 'statistics', name: 'Statistics', component: () => import('@/views/Statistics.vue') },
        { path: 'users', name: 'Users', component: () => import('@/views/UserList.vue') },
        { path: 'users/:id', name: 'UserDetail', component: () => import('@/views/UserDetail.vue') },
        { path: 'salary-records', name: 'SalaryRecords', component: () => import('@/views/SalaryList.vue') },
        { path: 'posts', name: 'Posts', component: () => import('@/views/PostList.vue') },
        { path: 'comments', name: 'Comments', component: () => import('@/views/CommentList.vue') },
        { path: 'risk-pending', name: 'RiskPending', component: () => import('@/views/RiskPending.vue') },
      ],
    },
  ],
})

router.beforeEach((to, _from, next) => {
  const auth = useAuthStore()
  if (to.meta.public) {
    if (auth.isLoggedIn && to.name === 'Login') return next({ path: '/' })
    return next()
  }
  if (to.meta.requiresAuth && !auth.isLoggedIn) return next({ path: '/login', query: { redirect: to.fullPath } })
  next()
})

export default router
