<template>
  <el-container class="layout">
    <el-aside width="220px" class="aside" aria-label="主导航菜单">
      <div class="logo" role="banner">PayDay 管理</div>
      <el-menu
        :default-active="activeMenu"
        router
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
        role="navigation"
        aria-label="管理后台导航"
      >
        <!-- 数据中心 -->
        <el-menu-item index="/statistics" aria-label="数据统计页面">
          <el-icon><DataAnalysis /></el-icon>
          <span>数据统计</span>
        </el-menu-item>

        <!-- 用户管理 -->
        <el-sub-menu index="user-management" aria-label="用户管理">
          <template #title>
            <el-icon><User /></el-icon>
            <span>用户管理</span>
          </template>
          <el-menu-item index="/users" aria-label="用户列表">用户列表</el-menu-item>
          <el-menu-item index="/salary-records" aria-label="工资记录">工资记录</el-menu-item>
        </el-sub-menu>

        <!-- 内容管理 -->
        <el-sub-menu index="content-management" aria-label="内容管理">
          <template #title>
            <el-icon><Document /></el-icon>
            <span>内容管理</span>
          </template>
          <el-menu-item index="/posts" aria-label="帖子管理">帖子管理</el-menu-item>
          <el-menu-item index="/comments" aria-label="评论管理">评论管理</el-menu-item>
          <el-menu-item index="/topics" aria-label="话题管理">话题管理</el-menu-item>
          <el-menu-item index="/risk-pending" aria-label="风控待审">风控待审</el-menu-item>
        </el-sub-menu>

        <!-- 会员系统 -->
        <el-sub-menu index="membership-system" aria-label="会员系统">
          <template #title>
            <el-icon><UserFilled /></el-icon>
            <span>会员系统</span>
          </template>
          <el-menu-item index="/memberships" aria-label="会员管理">会员管理</el-menu-item>
          <el-menu-item index="/orders" aria-label="订单管理">订单管理</el-menu-item>
        </el-sub-menu>

        <!-- 积分商城 -->
        <el-sub-menu index="point-shop" aria-label="积分商城">
          <template #title>
            <el-icon><ShoppingCart /></el-icon>
            <span>积分商城</span>
          </template>
          <el-menu-item index="/point-shop" aria-label="积分商品">积分商品</el-menu-item>
          <el-menu-item index="/point-orders" aria-label="积分订单">积分订单</el-menu-item>
        </el-sub-menu>

        <!-- 系统配置 -->
        <el-sub-menu index="system-config" aria-label="系统配置">
          <template #title>
            <el-icon><Setting /></el-icon>
            <span>系统配置</span>
          </template>
          <el-menu-item index="/themes" aria-label="主题配置">主题配置</el-menu-item>
          <el-menu-item index="/miniprogram" aria-label="小程序配置">小程序配置</el-menu-item>
          <el-menu-item index="/agreements" aria-label="协议管理">协议管理</el-menu-item>
          <el-menu-item index="/splash" aria-label="开屏设置">开屏设置</el-menu-item>
        </el-sub-menu>

        <!-- 用户反馈 -->
        <el-menu-item index="/feedback" aria-label="用户反馈页面">
          <el-icon><ChatDotRound /></el-icon>
          <span>用户反馈</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="header">
        <span class="title">薪日管理后台</span>
        <el-button type="danger" link @click="logout">退出</el-button>
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
import { DataAnalysis, User, Document, ChatDotRound, UserFilled, Setting, ShoppingCart } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const activeMenu = computed(() => {
  const p = route.path
  if (p.startsWith('/users') && p !== '/users') return '/users'
  return p
})

function logout() {
  auth.logout()
  router.replace('/login')
}
</script>

<style scoped>
.layout { height: 100vh; }
.aside {
  background: #304156;
  overflow-x: hidden;
}
.logo {
  height: 50px;
  line-height: 50px;
  text-align: center;
  color: #fff;
  font-weight: 600;
  background: #263445;
}
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  padding: 0 16px;
}
.title { font-size: 16px; }
.main {
  background: #f0f2f5;
  padding: 16px;
  overflow: auto;
}
</style>
