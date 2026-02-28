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
          <el-menu-item index="/point-shop/create" aria-label="新增商品">新增商品</el-menu-item>
          <el-menu-item index="/point-categories" aria-label="分类管理">分类管理</el-menu-item>
          <el-menu-item index="/point-orders" aria-label="积分订单">积分订单</el-menu-item>
          <el-menu-item index="/point-shipments" aria-label="发货管理">发货管理</el-menu-item>
          <el-menu-item index="/point-returns" aria-label="退货管理">退货管理</el-menu-item>
          <el-menu-item index="/couriers" aria-label="物流公司">物流公司</el-menu-item>
          <el-menu-item index="/shipping-templates" aria-label="运费模板">运费模板</el-menu-item>
          <el-menu-item index="/specification-templates" aria-label="规格模板"
            >规格模板</el-menu-item
          >
          <el-menu-item index="/user-addresses" aria-label="用户地址">用户地址</el-menu-item>
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
        <div class="header-right">
          <el-dropdown trigger="click" @command="handleCommand">
            <span class="user-info">
              <el-icon><User /></el-icon>
              <span class="username">{{ profile?.username || '加载中...' }}</span>
              <el-tag size="small" :type="roleTagType" class="role-tag">{{ roleText }}</el-tag>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="changePassword">修改密码</el-dropdown-item>
                <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>

    <!-- 修改密码弹窗 -->
    <el-dialog v-model="passwordDialogVisible" title="修改密码" width="400px">
      <el-form
        ref="passwordFormRef"
        :model="passwordForm"
        :rules="passwordRules"
        label-width="80px"
      >
        <el-form-item label="旧密码" prop="old_password">
          <el-input
            v-model="passwordForm.old_password"
            type="password"
            placeholder="请输入旧密码"
            show-password
          />
        </el-form-item>
        <el-form-item label="新密码" prop="new_password">
          <el-input
            v-model="passwordForm.new_password"
            type="password"
            placeholder="请输入新密码（至少6位）"
            show-password
          />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirm_password">
          <el-input
            v-model="passwordForm.confirm_password"
            type="password"
            placeholder="请再次输入新密码"
            show-password
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="passwordDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="passwordLoading" @click="handleChangePassword">
          确定
        </el-button>
      </template>
    </el-dialog>
  </el-container>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  DataAnalysis,
  User,
  Document,
  ChatDotRound,
  UserFilled,
  Setting,
  ShoppingCart,
} from '@element-plus/icons-vue'
import { ElMessage, FormInstance, FormRules } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { getAdminProfile, changeAdminPassword, type AdminProfile } from '@/api/admin'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const profile = ref<AdminProfile | null>(null)
const passwordDialogVisible = ref(false)
const passwordLoading = ref(false)
const passwordFormRef = ref<FormInstance>()

const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: '',
})

const validateConfirmPassword = (
  _rule: unknown,
  value: string,
  callback: (error?: Error) => void
) => {
  if (value !== passwordForm.new_password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const passwordRules: FormRules = {
  old_password: [{ required: true, message: '请输入旧密码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' },
  ],
  confirm_password: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' },
  ],
}

const activeMenu = computed(() => {
  const p = route.path
  if (p.startsWith('/users') && p !== '/users') return '/users'
  return p
})

const roleText = computed(() => {
  switch (profile.value?.role) {
    case 'superadmin':
      return '超级管理员'
    case 'admin':
      return '管理员'
    case 'readonly':
      return '只读'
    default:
      return profile.value?.role || ''
  }
})

const roleTagType = computed(() => {
  switch (profile.value?.role) {
    case 'superadmin':
      return 'danger'
    case 'admin':
      return 'warning'
    default:
      return 'info'
  }
})

async function loadProfile() {
  try {
    profile.value = await getAdminProfile()
  } catch {
    // 忽略错误，可能未登录
  }
}

function handleCommand(command: string) {
  switch (command) {
    case 'changePassword':
      openPasswordDialog()
      break
    case 'logout':
      logout()
      break
  }
}

function openPasswordDialog() {
  passwordForm.old_password = ''
  passwordForm.new_password = ''
  passwordForm.confirm_password = ''
  passwordDialogVisible.value = true
}

async function handleChangePassword() {
  const valid = await passwordFormRef.value?.validate().catch(() => false)
  if (!valid) return

  passwordLoading.value = true
  try {
    await changeAdminPassword({
      old_password: passwordForm.old_password,
      new_password: passwordForm.new_password,
    })
    ElMessage.success('密码修改成功')
    passwordDialogVisible.value = false
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : '修改失败'
    ElMessage.error(errorMessage)
  } finally {
    passwordLoading.value = false
  }
}

function logout() {
  auth.logout()
  router.replace('/login')
}

onMounted(() => {
  loadProfile()
})
</script>

<style scoped>
.layout {
  height: 100vh;
}
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
.title {
  font-size: 16px;
}
.header-right {
  display: flex;
  align-items: center;
}
.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 4px;
  transition: background-color 0.2s;
}
.user-info:hover {
  background-color: #f5f7fa;
}
.username {
  font-size: 14px;
  color: #333;
}
.role-tag {
  margin-left: 4px;
}
.main {
  background: #f0f2f5;
  padding: 16px;
  overflow: auto;
}
</style>
