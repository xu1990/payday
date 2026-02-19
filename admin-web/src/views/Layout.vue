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
        <el-menu-item index="/statistics" aria-label="数据统计页面">
          <el-icon><DataAnalysis /></el-icon>
          <span>数据统计</span>
        </el-menu-item>
        <el-menu-item index="/users" aria-label="用户管理页面">
          <el-icon><User /></el-icon>
          <span>用户管理</span>
        </el-menu-item>
        <el-menu-item index="/salary-records" aria-label="工资记录页面">
          <el-icon><List /></el-icon>
          <span>工资记录</span>
        </el-menu-item>
        <el-menu-item index="/posts" aria-label="帖子管理页面">
          <el-icon><Document /></el-icon>
          <span>帖子管理</span>
        </el-menu-item>
        <el-menu-item index="/comments" aria-label="评论管理页面">
          <el-icon><ChatDotRound /></el-icon>
          <span>评论管理</span>
        </el-menu-item>
        <el-menu-item index="/risk-pending" aria-label="风控待审页面">
          <el-icon><DocumentChecked /></el-icon>
          <span>风控待审</span>
        </el-menu-item>
        <el-menu-item index="/topics" aria-label="话题管理页面">
          <el-icon><PriceTag /></el-icon>
          <span>话题管理</span>
        </el-menu-item>
        <el-menu-item index="/memberships" aria-label="会员管理页面">
          <el-icon><UserFilled /></el-icon>
          <span>会员管理</span>
        </el-menu-item>
        <el-menu-item index="/themes" aria-label="主题配置页面">
          <el-icon><Brush /></el-icon>
          <span>主题配置</span>
        </el-menu-item>
        <el-menu-item index="/orders" aria-label="订单管理页面">
          <el-icon><Tickets /></el-icon>
          <span>订单管理</span>
        </el-menu-item>
        <el-menu-item index="/miniprogram" aria-label="小程序配置页面">
          <el-icon><Setting /></el-icon>
          <span>小程序配置</span>
        </el-menu-item>
        <el-menu-item index="/agreements" aria-label="协议管理页面">
          <el-icon><Document /></el-icon>
          <span>协议管理</span>
        </el-menu-item>
        <el-menu-item index="/splash" aria-label="开屏设置页面">
          <el-icon><Document /></el-icon>
          <span>开屏设置</span>
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
import { DataAnalysis, User, List, Document, ChatDotRound, DocumentChecked, PriceTag, UserFilled, Brush, Tickets, Setting } from '@element-plus/icons-vue'
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
