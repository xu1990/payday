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
        { path: 'topics', name: 'Topics', component: () => import('@/views/topics/index.vue') },
        { path: 'memberships', name: 'Memberships', component: () => import('@/views/Membership.vue') },
        { path: 'themes', name: 'Themes', component: () => import('@/views/Theme.vue') },
        { path: 'orders', name: 'Orders', component: () => import('@/views/Order.vue') },
        { path: 'miniprogram', name: 'Miniprogram', component: () => import('@/views/MiniprogramConfig.vue') },
        { path: 'agreements', name: 'Agreements', component: () => import('@/views/AgreementManagement.vue') },
        { path: 'splash', name: 'Splash', component: () => import('@/views/SplashSettings.vue') },
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
  // 验证用户已登录且具有 admin scope
  if (to.meta.requiresAuth) {
    if (!auth.isLoggedIn) {
      return next({ path: '/login', query: { redirect: to.fullPath } })
    }
    if (!auth.hasAdminScope) {
      // token 缺少 admin scope，强制登出
      auth.logout()
      return next({ path: '/login', query: { redirect: to.fullPath } })
    }
  }
  next()
})

export default router
