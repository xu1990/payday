# 用户协议、开屏页面、个人资料编辑 - 实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标：** 实现管理后台的富文本协议编辑、开屏页面配置、小程序个人资料编辑页面，以及设置页面的退出登录和账号注销功能。

**架构：** 在现有一体化用户服务基础上扩展，复用 MiniprogramConfig 表存储协议和开屏配置，User 表添加软删除字段支持账号注销恢复。

**技术栈：**
- 后端：FastAPI + SQLAlchemy + MySQL + Tencent COS
- 管理后台：Vue3 + Element Plus + Quill.js（富文本编辑器）
- 小程序：uni-app + Vue3

---

## 阶段 1: 数据库变更

### 任务 1.1: 创建数据库迁移文件

**文件：**
- 创建: `backend/alembic/versions/YYYYMMDD_add_deactivated_at_to_users.py`

**步骤 1: 生成迁移文件**

```bash
cd backend
alembic revision -m "add deactivated_at to users table"
```

**步骤 2: 编辑迁移文件**

打开生成的迁移文件，写入以下内容：

```python
"""add deactivated_at to users table

Revision ID: <generated_revision_id>
Revises: <previous_revision_id>
Create Date: 2026-02-19

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '<generated_revision_id>'
down_revision = '<previous_revision_id>'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('deactivated_at', sa.DateTime(), nullable=True, comment='注销时间（软删除）'))
    op.create_index('idx_users_deactivated_at', 'users', ['deactivated_at'])


def downgrade():
    op.drop_index('idx_users_deactivated_at', table_name='users')
    op.drop_column('users', 'deactivated_at')
```

**步骤 3: 运行迁移**

```bash
cd backend
alembic upgrade head
```

预期输出: `Running upgrade -> <revision_id>, add deactivated_at to users table`

**步骤 4: 验证迁移**

```bash
mysql -u root -p payday_db -e "DESCRIBE users;" | grep deactivated_at
```

预期输出: `deactivated_at datetime YES`

**步骤 5: 提交**

```bash
git add backend/alembic/versions/
git commit -m "feat: add deactivated_at column to users table for soft delete"
```

---

## 阶段 2: 后端 API - 用户注销和头像上传

### 任务 2.1: 更新 User 模型

**文件：**
- 修改: `backend/app/models/user.py:39` (在 User 类末尾添加字段)

**步骤 1: 添加 deactivated_at 字段**

在 `User` 类中，`updated_at` 字段之后添加：

```python
    deactivated_at = Column(DateTime, nullable=True, comment="注销时间（软删除）")
```

**步骤 2: 提交**

```bash
git add backend/app/models/user.py
git commit -m "feat: add deactivated_at field to User model"
```

---

### 任务 2.2: 更新 User schema

**文件：**
- 修改: `backend/app/schemas/user.py:19` (在 UserResponse 类中添加字段)

**步骤 1: 在 UserResponse 类中添加字段**

在 `updated_at` 字段之后添加：

```python
    deactivated_at: Optional[str] = None
```

**步骤 2: 在 UserUpdate 类中添加字段**

在文件末尾的 `UserUpdate` 类之后添加新类：

```python
class UserDeactivate(BaseModel):
    """用户注销请求"""
    pass  # 空请求体，仅确认操作
```

**步骤 3: 提交**

```bash
git add backend/app/schemas/user.py
git commit -m "feat: add deactivated_at to UserResponse schema"
```

---

### 任务 2.3: 创建用户服务函数

**文件：**
- 修改: `backend/app/services/user_service.py`

**步骤 1: 在文件末尾添加新函数**

```python
async def deactivate_user(db: AsyncSession, user_id: str) -> User:
    """注销用户（软删除）"""
    from datetime import datetime, timedelta
    from sqlalchemy import update, select

    # 计算恢复截止时间（30天后）
    recovery_until = datetime.utcnow() + timedelta(days=30)

    result = await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(deactivated_at=datetime.utcnow())
        .returning(User)
    )
    await db.commit()

    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one()
    return user


async def reactivate_user(db: AsyncSession, user_id: str) -> User:
    """恢复已注销的用户"""
    from sqlalchemy import update, select

    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(deactivated_at=None)
    )
    await db.commit()

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one()
    return user


async def upload_user_avatar(db: AsyncSession, user_id: str, avatar_url: str) -> User:
    """更新用户头像"""
    return await update_user(db, user_id, UserUpdate(avatar=avatar_url))
```

**步骤 2: 提交**

```bash
git add backend/app/services/user_service.py
git commit -m "feat: add deactivate, reactivate, and upload_avatar functions"
```

---

### 任务 2.4: 添加用户注销和恢复 API

**文件：**
- 修改: `backend/app/api/v1/user.py`

**步骤 1: 在文件顶部导入区域添加**

在现有导入后添加：

```python
from datetime import datetime, timedelta
from app.services.user_service import deactivate_user, reactivate_user, upload_user_avatar
```

**步骤 2: 在文件末尾（第62行后）添加新端点**

```python
@router.post("/me/deactivate")
async def deactivate_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """注销当前用户账号（软删除，30天可恢复）"""
    user = await deactivate_user(db, current_user.id)
    recovery_until = (datetime.utcnow() + timedelta(days=30)).isoformat()

    return success_response(
        data={"recovery_until": recovery_until},
        message="注销成功，30天内可通过登录恢复"
    )


@router.post("/me/reactivate")
async def reactivate_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """恢复已注销的账号"""
    user = await reactivate_user(db, current_user.id)
    return success_response(data=_user_to_response(user), message="账号已恢复")


@router.post("/me/upload-avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """上传用户头像到腾讯云 COS"""
    from fastapi import File, UploadFile
    from app.utils.storage import storage_service

    # 验证文件类型
    if not file.content_type or not file.content_type.startswith('image/'):
        from app.core.exceptions import ValidationException
        raise ValidationException("只支持图片文件")

    # 读取文件内容
    content = await file.read()

    # 验证文件大小（5MB）
    if len(content) > 5 * 1024 * 1024:
        from app.core.exceptions import ValidationException
        raise ValidationException("图片大小不能超过5MB")

    # 上传到 COS
    import uuid
    ext = file.filename.split('.')[-1] if file.filename else 'jpg'
    key = f"avatars/{current_user.id}/{uuid.uuid4()}.{ext}"
    url = storage_service.cos_client.upload_file(content, key)

    # 更新用户头像
    user = await upload_user_avatar(db, current_user.id, url)

    return success_response(data={"url": url}, message="头像上传成功")
```

**步骤 3: 在文件开头导入 File 和 UploadFile**

在导入区域添加：

```python
from fastapi import File, UploadFile
```

**步骤 4: 提交**

```bash
git add backend/app/api/v1/user.py
git commit -m "feat: add deactivate, reactivate, and upload-avatar endpoints"
```

---

### 任务 2.5: 更新登录服务以支持自动恢复

**文件：**
- 修改: `backend/app/services/auth_service.py`

**步骤 1: 找到 login_with_code 函数，在返回用户信息前检查 deactivation 状态**

在函数中，获取用户对象后添加检查：

```python
    # 检查用户是否已注销
    if user.deactivated_at:
        # 自动恢复账号
        from datetime import datetime, timedelta
        recovery_deadline = user.deactivated_at + timedelta(days=30)

        if datetime.utcnow() > recovery_deadline:
            # 超过30天，无法恢复
            raise BusinessException("账号已注销且超过恢复期限", code="ACCOUNT_PERMANENTLY_DELETED")

        # 在恢复期限内，自动恢复账号
        from sqlalchemy import update
        await db.execute(
            update(User).where(User.id == user.id).values(deactivated_at=None)
        )
        await db.commit()
```

**步骤 2: 提交**

```bash
git add backend/app/services/auth_service.py
git commit -m "feat: auto-reactivate deactivated users on login within 30 days"
```

---

### 任务 2.6: 添加协议和开屏配置的公共查询 API

**文件：**
- 创建: `backend/app/api/v1/config.py`

**步骤 1: 创建新文件**

创建完整的新文件：

```python
"""
公共配置 API - 小程序获取协议、开屏配置等
"""
from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import success_response
from app.models.miniprogram_config import MiniprogramConfig
from typing import Optional

router = APIRouter(prefix="/config", tags=["public-config"])


class AgreementResponse(BaseModel):
    user_agreement: Optional[str] = None
    privacy_agreement: Optional[str] = None


class SplashConfigResponse(BaseModel):
    image_url: Optional[str] = None
    content: Optional[str] = None
    countdown: int = 3
    is_active: bool = False


@router.get("/public/agreements")
async def get_public_agreements(
    db: AsyncSession = Depends(get_db),
):
    """获取用户协议和隐私协议（公开接口）"""
    from sqlalchemy import select

    # 获取用户协议
    user_result = await db.execute(
        select(MiniprogramConfig).where(MiniprogramConfig.key == 'user_agreement')
    )
    user_config = user_result.scalar_one_or_none()
    user_agreement = user_config.value if user_config else None

    # 获取隐私协议
    privacy_result = await db.execute(
        select(MiniprogramConfig).where(MiniprogramConfig.key == 'privacy_agreement')
    )
    privacy_config = privacy_result.scalar_one_or_none()
    privacy_agreement = privacy_config.value if privacy_config else None

    return success_response(
        data=AgreementResponse(
            user_agreement=user_agreement,
            privacy_agreement=privacy_agreement
        ).model_dump(),
        message="获取协议成功"
    )


@router.get("/public/splash")
async def get_public_splash_config(
    db: AsyncSession = Depends(get_db),
):
    """获取开屏页面配置（公开接口）"""
    from sqlalchemy import select
    import json

    result = await db.execute(
        select(MiniprogramConfig).where(MiniprogramConfig.key == 'splash_config')
    )
    config = result.scalar_one_or_none()

    if not config or not config.value or not config.is_active:
        return success_response(
            data=SplashConfigResponse(is_active=False).model_dump(),
            message="开屏配置未启用"
        )

    try:
        splash_data = json.loads(config.value)
        return success_response(
            data=SplashConfigResponse(
                image_url=splash_data.get('image_url'),
                content=splash_data.get('content'),
                countdown=splash_data.get('countdown', 3),
                is_active=True
            ).model_dump(),
            message="获取开屏配置成功"
        )
    except (json.JSONDecodeError, TypeError):
        return success_response(
            data=SplashConfigResponse(is_active=False).model_dump(),
            message="开屏配置格式错误"
        )
```

**步骤 2: 注册路由**

修改 `backend/app/api/v1/__init__.py`:

在导入区域添加：
```python
from .config import router as config_router
```

在 `api_router.include_router` 列表末尾添加：
```python
api_router.include_router(config_router)
```

**步骤 3: 提交**

```bash
git add backend/app/api/v1/config.py backend/app/api/v1/__init__.py
git commit -m "feat: add public config API for agreements and splash"
```

---

## 阶段 3: 管理后台 - 协议管理页面

### 任务 3.1: 安装 Quill.js 富文本编辑器

**文件：**
- 修改: `admin-web/package.json`

**步骤 1: 安装依赖**

```bash
cd admin-web
npm install @vueup/vue-quill quill
```

**步骤 2: 提交 package-lock.json**

```bash
git add admin-web/package.json admin-web/package-lock.json
git commit -m "chore: install @vueup/vue-quill for rich text editing"
```

---

### 任务 3.2: 创建协议管理 API 客户端

**文件：**
- 修改: `admin-web/src/api/miniprogram.ts`

**步骤 1: 在文件末尾添加函数**

```typescript
/**
 * 获取协议内容
 */
export function getAgreements(): Promise<{
  data: {
    user_agreement: string
    privacy_agreement: string
  }
  message: string
}> {
  return request({ url: '/admin/config/agreements', method: 'GET' })
}

/**
 * 更新协议内容
 */
export function updateAgreement(data: {
  type: 'user' | 'privacy'
  content: string
}): Promise<{ message: string }> {
  return request({ url: '/admin/config/agreements', method: 'POST', data })
}
```

**步骤 2: 提交**

```bash
git add admin-web/src/api/miniprogram.ts
git commit -m "feat: add agreement management API functions"
```

---

### 任务 3.3: 创建协议管理页面

**文件：**
- 创建: `admin-web/src/views/AgreementManagement.vue`

**步骤 1: 创建完整文件**

```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { QuillEditor } from '@vueup/vue-quill'
import '@vueup/vue-quill/dist/vue-quill.snow.css'
import { ElMessage } from 'element-plus'
import { getAgreements, updateAgreement } from '@/api/miniprogram'

const activeTab = ref<'user' | 'privacy'>('user')
const userContent = ref('')
const privacyContent = ref('')
const loading = ref(false)
const saving = ref(false)

async function loadData() {
  loading.value = true
  try {
    const res = await getAgreements()
    userContent.value = res.data?.user_agreement || ''
    privacyContent.value = res.data?.privacy_agreement || ''
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : '加载失败'
    ElMessage.error(errorMessage)
  } finally {
    loading.value = false
  }
}

async function save() {
  saving.value = true
  try {
    const type = activeTab.value
    const content = type === 'user' ? userContent.value : privacyContent.value

    await updateAgreement({ type, content })
    ElMessage.success('保存成功')
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : '保存失败'
    ElMessage.error(errorMessage)
  } finally {
    saving.value = false
  }
}

function switchTab(tab: 'user' | 'privacy') {
  activeTab.value = tab
}

onMounted(loadData)
</script>

<template>
  <div class="agreement-page">
    <div class="header">
      <h2>协议管理</h2>
    </div>

    <el-tabs v-model="activeTab" @tab-change="switchTab">
      <el-tab-pane label="用户协议" name="user" />
      <el-tab-pane label="隐私协议" name="privacy" />
    </el-tabs>

    <div v-loading="loading" class="editor-container">
      <QuillEditor
        v-model:content="activeTab === 'user' ? userContent : privacyContent"
        contentType="html"
        theme="snow"
        :toolbar="[
          ['bold', 'italic', 'underline', 'strike'],
          ['blockquote', 'code-block'],
          [{ 'header': 1 }, { 'header': 2 }],
          [{ 'list': 'ordered'}, { 'list': 'bullet' }],
          [{ 'indent': '-1'}, { 'indent': '+1' }],
          ['link'],
          ['clean']
        ]"
        style="height: 400px; margin-bottom: 60px;"
      />

      <div class="actions">
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.agreement-page {
  padding: 24px;
}

.header {
  margin-bottom: 24px;
}

.header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.editor-container {
  background: #fff;
  padding: 24px;
  border-radius: 8px;
}

.actions {
  position: fixed;
  bottom: 24px;
  right: 24px;
  background: #fff;
  padding: 16px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
</style>
```

**步骤 2: 注册路由**

修改 `admin-web/src/router/index.ts`:

在 Layout children 数组中添加（在 miniprogram 路由之后）：
```typescript
{ path: 'agreements', name: 'Agreements', component: () => import('@/views/AgreementManagement.vue') },
```

**步骤 3: 在 Layout 中添加菜单项**

修改 `admin-web/src/views/Layout.vue`:

在导航菜单中找到合适位置添加（在 "小程序配置" 菜单项之后）：
```vue
<el-menu-item index="/agreements">协议管理</el-menu-item>
```

**步骤 4: 提交**

```bash
git add admin-web/src/views/AgreementManagement.vue admin-web/src/router/index.ts admin-web/src/views/Layout.vue
git commit -m "feat: add agreement management page with rich text editor"
```

---

## 阶段 4: 管理后台 - 开屏页面设置

### 任务 4.1: 创建开屏配置 API 客户端

**文件：**
- 修改: `admin-web/src/api/miniprogram.ts`

**步骤 1: 在文件末尾添加函数**

```typescript
export interface SplashConfigData {
  image_url: string
  content: string
  countdown: number
  is_active: boolean
}

export interface SplashConfigResponse {
  data: SplashConfigData
  message: string
}

/**
 * 获取开屏配置
 */
export function getSplashConfig(): Promise<SplashConfigResponse> {
  return request({ url: '/admin/config/splash', method: 'GET' })
}

/**
 * 更新开屏配置
 */
export function updateSplashConfig(data: SplashConfigData): Promise<{ message: string }> {
  return request({ url: '/admin/config/splash', method: 'POST', data })
}
```

**步骤 2: 提交**

```bash
git add admin-web/src/api/miniprogram.ts
git commit -m "feat: add splash config API functions"
```

---

### 任务 4.2: 创建开屏设置页面

**文件：**
- 创建: `admin-web/src/views/SplashSettings.vue`

**步骤 1: 创建完整文件**

```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import type { UploadProps } from 'element-plus'
import { getSplashConfig, updateSplashConfig, type SplashConfigData } from '@/api/miniprogram'

const form = ref<SplashConfigData>({
  image_url: '',
  content: '欢迎使用薪日 PayDay',
  countdown: 3,
  is_active: true,
})
const loading = ref(false)
const saving = ref(false)
const imageUrl = ref('')

async function loadData() {
  loading.value = true
  try {
    const res = await getSplashConfig()
    if (res.data) {
      form.value = res.data
      imageUrl.value = res.data.image_url || ''
    }
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : '加载失败'
    ElMessage.error(errorMessage)
  } finally {
    loading.value = false
  }
}

async function save() {
  saving.value = true
  try {
    await updateSplashConfig(form.value)
    ElMessage.success('保存成功')
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : '保存失败'
    ElMessage.error(errorMessage)
  } finally {
    saving.value = false
  }
}

const handleImageSuccess: UploadProps['onSuccess'] = (response) => {
  if (response.data?.url) {
    form.value.image_url = response.data.url
    imageUrl.value = response.data.url
    ElMessage.success('图片上传成功')
  }
}

const beforeImageUpload: UploadProps['beforeUpload'] = (rawFile) => {
  if (!rawFile.type.startsWith('image/')) {
    ElMessage.error('只能上传图片文件')
    return false
  }
  if (rawFile.size / 1024 / 1024 > 5) {
    ElMessage.error('图片大小不能超过5MB')
    return false
  }
  return true
}

onMounted(loadData)
</script>

<template>
  <div class="splash-page">
    <div class="header">
      <h2>开屏页面设置</h2>
    </div>

    <el-card v-loading="loading" class="form-card">
      <el-form :model="form" label-width="120px">
        <el-form-item label="开屏图片">
          <el-upload
            action="/api/v1/admin/upload"
            :show-file-list="false"
            :on-success="handleImageSuccess"
            :before-upload="beforeImageUpload"
            accept="image/*"
          >
            <el-button type="primary">选择图片</el-button>
          </el-upload>
          <div v-if="imageUrl" class="image-preview">
            <el-image :src="imageUrl" fit="contain" style="width: 200px; height: 300px;" />
          </div>
        </el-form-item>

        <el-form-item label="欢迎文字">
          <el-input v-model="form.content" placeholder="请输入欢迎文字" maxlength="50" show-word-limit />
        </el-form-item>

        <el-form-item label="倒计时时长">
          <el-input-number v-model="form.countdown" :min="1" :max="10" controls-position="right" />
          <span style="margin-left: 8px; color: #999;">秒</span>
        </el-form-item>

        <el-form-item label="启用状态">
          <el-switch v-model="form.is_active" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="saving" @click="save">保存配置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.splash-page {
  padding: 24px;
}

.header {
  margin-bottom: 24px;
}

.header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.form-card {
  max-width: 600px;
}

.image-preview {
  margin-top: 16px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  overflow: hidden;
  display: inline-block;
}
</style>
```

**步骤 2: 注册路由**

修改 `admin-web/src/router/index.ts`:

在 Layout children 数组中添加：
```typescript
{ path: 'splash', name: 'Splash', component: () => import('@/views/SplashSettings.vue') },
```

**步骤 3: 在 Layout 中添加菜单项**

修改 `admin-web/src/views/Layout.vue`:

在导航菜单中添加（在 "协议管理" 之后）：
```vue
<el-menu-item index="/splash">开屏设置</el-menu-item>
```

**步骤 4: 提交**

```bash
git add admin-web/src/views/SplashSettings.vue admin-web/src/router/index.ts admin-web/src/views/Layout.vue
git commit -m "feat: add splash settings page with image upload"
```

---

## 阶段 5: 后端 API - 管理后台接口实现

### 任务 5.1: 创建后端协议管理 API

**文件：**
- 修改: `backend/app/api/v1/admin_config.py` (在文件末尾添加)

**步骤 1: 在文件末尾添加协议管理端点**

```python
# ==================== 协议管理 ====================

class AgreementUpdate(BaseModel):
    type: str = Field(..., description="协议类型: user 或 privacy")
    content: str = Field(..., description="协议内容（HTML）")


@router.get("/agreements")
async def get_agreements(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取用户协议和隐私协议"""
    from sqlalchemy import select

    # 获取用户协议
    user_result = await db.execute(
        select(MiniprogramConfig).where(MiniprogramConfig.key == 'user_agreement')
    )
    user_config = user_result.scalar_one_or_none()

    # 获取隐私协议
    privacy_result = await db.execute(
        select(MiniprogramConfig).where(MiniprogramConfig.key == 'privacy_agreement')
    )
    privacy_config = privacy_result.scalar_one_or_none()

    return success_response(
        data={
            "user_agreement": user_config.value if user_config else "",
            "privacy_agreement": privacy_config.value if privacy_config else "",
            "updated_at": (
                max(user_config.updated_at, privacy_config.updated_at).isoformat()
                if user_config and privacy_config
                else None
            )
        },
        message="获取协议成功"
    )


@router.post("/agreements")
async def update_agreement(
    data: AgreementUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """更新协议内容"""
    from sqlalchemy import select, update

    key = f"{data.type}_agreement"

    # 查找现有配置
    result = await db.execute(
        select(MiniprogramConfig).where(MiniprogramConfig.key == key)
    )
    config = result.scalar_one_or_none()

    if config:
        # 更新现有配置
        await db.execute(
            update(MiniprogramConfig)
            .where(MiniprogramConfig.key == key)
            .values(value=data.content)
        )
    else:
        # 创建新配置
        new_config = MiniprogramConfig(
            key=key,
            value=data.content,
            description=f"{data.type} agreement",
            is_active=True,
            sort_order=0
        )
        db.add(new_config)

    await db.commit()

    return success_response(message="保存成功")
```

**步骤 2: 提交**

```bash
git add backend/app/api/v1/admin_config.py
git commit -m "feat: add agreement management endpoints for admin"
```

---

### 任务 5.2: 创建后端开屏配置 API

**文件：**
- 修改: `backend/app/api/v1/admin_config.py` (在任务 5.1 添加的代码之后)

**步骤 1: 添加开屏配置端点**

在任务 5.1 添加的代码之后继续添加：

```python
# ==================== 开屏配置管理 ====================

class SplashConfigUpdate(BaseModel):
    image_url: str = Field(..., description="开屏图片 URL")
    content: str = Field(..., description="欢迎文字")
    countdown: int = Field(3, ge=1, le=10, description="倒计时时长（秒）")
    is_active: bool = Field(True, description="是否启用")


@router.get("/splash")
async def get_splash_config(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取开屏配置"""
    from sqlalchemy import select
    import json

    result = await db.execute(
        select(MiniprogramConfig).where(MiniprogramConfig.key == 'splash_config')
    )
    config = result.scalar_one_or_none()

    if not config or not config.value:
        return success_response(
            data={
                "image_url": "",
                "content": "",
                "countdown": 3,
                "is_active": False
            },
            message="获取开屏配置成功"
        )

    try:
        splash_data = json.loads(config.value)
        return success_response(
            data={
                "image_url": splash_data.get("image_url", ""),
                "content": splash_data.get("content", ""),
                "countdown": splash_data.get("countdown", 3),
                "is_active": config.is_active
            },
            message="获取开屏配置成功"
        )
    except (json.JSONDecodeError, TypeError):
        return success_response(
            data={
                "image_url": "",
                "content": "",
                "countdown": 3,
                "is_active": False
            },
            message="开屏配置格式错误"
        )


@router.post("/splash")
async def update_splash_config(
    data: SplashConfigUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """更新开屏配置"""
    from sqlalchemy import select, update
    import json

    # 查找现有配置
    result = await db.execute(
        select(MiniprogramConfig).where(MiniprogramConfig.key == 'splash_config')
    )
    config = result.scalar_one_or_none()

    value_json = json.dumps({
        "image_url": data.image_url,
        "content": data.content,
        "countdown": data.countdown,
    })

    if config:
        # 更新现有配置
        await db.execute(
            update(MiniprogramConfig)
            .where(MiniprogramConfig.key == 'splash_config')
            .values(value=value_json, is_active=data.is_active)
        )
    else:
        # 创建新配置
        new_config = MiniprogramConfig(
            key='splash_config',
            value=value_json,
            description='Splash screen configuration',
            is_active=data.is_active,
            sort_order=0
        )
        db.add(new_config)

    await db.commit()

    return success_response(message="保存成功")
```

**步骤 2: 提交**

```bash
git add backend/app/api/v1/admin_config.py
git commit -m "feat: add splash config endpoints for admin"
```

---

## 阶段 6: 小程序 - 个人资料编辑页面

### 任务 6.1: 添加个人资料编辑页面路由

**文件：**
- 修改: `miniapp/src/pages.json`

**步骤 1: 在 pages 数组中添加新页面**

在 `"pages/profile/index"` 之后添加：

```json
{
  "path": "pages/profile-edit/index",
  "style": {
    "navigationBarTitleText": "编辑资料",
    "navigationStyle": "default"
  }
},
```

**步骤 2: 提交**

```bash
git add miniapp/src/pages.json
git commit -m "feat: add profile-edit page route"
```

---

### 任务 6.2: 创建个人资料编辑页面

**文件：**
- 创建: `miniapp/src/pages/profile-edit/index.vue`

**步骤 1: 创建完整文件**

```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { updateCurrentUser, type UserInfo } from '@/api/user'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()

const nickname = ref('')
const avatarUrl = ref('')
const saving = ref(false)

onMounted(() => {
  if (userStore.userInfo) {
    nickname.value = userStore.userInfo.nickname || ''
    avatarUrl.value = userStore.userInfo.avatar || ''
  }
})

// 选择头像
async function chooseAvatar() {
  try {
    const res: any = await uni.chooseImage({
      count: 1,
      sizeType: ['compressed'],
      sourceType: ['album', 'camera'],
    })

    if (res.tempFilePaths && res.tempFilePaths.length > 0) {
      const tempPath = res.tempFilePaths[0]

      // 上传到服务器
      await uploadAvatar(tempPath)
    }
  } catch (e) {
    // 用户取消选择
  }
}

// 上传头像
async function uploadAvatar(filePath: string) {
  try {
    uni.showLoading({ title: '上传中...' })

    const token = uni.getStorageSync('token')
    const uploadRes: any = await uni.uploadFile({
      url: `${getApp().globalData.apiUrl}/api/v1/user/me/upload-avatar`,
      filePath,
      name: 'file',
      header: {
        'Authorization': `Bearer ${token}`
      }
    })

    const data = JSON.parse(uploadRes.data)
    if (data.code === 0) {
      avatarUrl.value = data.data.url

      // 更新 userStore
      await userStore.fetchCurrentUser()

      uni.hideLoading()
      uni.showToast({ title: '头像上传成功', icon: 'success' })
    } else {
      throw new Error(data.message || '上传失败')
    }
  } catch (e: any) {
    uni.hideLoading()
    uni.showToast({ title: e?.message || '上传失败', icon: 'none' })
  }
}

// 修改昵称
async function editNickname() {
  try {
    const res: any = await uni.showModal({
      title: '修改昵称',
      editable: true,
      placeholderText: nickname.value || '请输入昵称',
      maxLength: 20
    })

    if (res.confirm && res.content) {
      const newNickname = res.content.trim()
      if (newNickname && newNickname !== nickname.value) {
        await saveNickname(newNickname)
      }
    }
  } catch (e) {
    // 用户取消
  }
}

// 保存昵称
async function saveNickname(newNickname: string) {
  try {
    uni.showLoading({ title: '保存中...' })
    await updateCurrentUser({ nickname: newNickname })

    nickname.value = newNickname

    // 更新 userStore
    await userStore.fetchCurrentUser()

    uni.hideLoading()
    uni.showToast({ title: '保存成功', icon: 'success' })
  } catch (e: any) {
    uni.hideLoading()
    uni.showToast({ title: e?.message || '保存失败', icon: 'none' })
  }
}

function goBack() {
  uni.navigateBack()
}
</script>

<template>
  <view class="page">
    <view class="header">
      <text class="title">编辑个人资料</text>
    </view>

    <!-- 头像 -->
    <view class="section">
      <view class="section-title">头像</view>
      <view class="avatar-container" @click="chooseAvatar">
        <image
          class="avatar-image"
          :src="avatarUrl || '/static/default-avatar.png'"
          mode="aspectFill"
        />
        <text class="change-hint">点击更换</text>
      </view>
    </view>

    <!-- 昵称 -->
    <view class="section">
      <view class="section-title">昵称</view>
      <view class="nickname-container" @click="editNickname">
        <text class="nickname-text">{{ nickname || '未设置' }}</text>
        <text class="arrow">›</text>
      </view>
    </view>

    <!-- 提示信息 -->
    <view class="tips">
      <text class="tips-text">点击头像可从相册或相机选择图片上传</text>
    </view>
  </view>
</template>

<style scoped lang="scss">
.page {
  padding: 24rpx;
  background: #f5f5f5;
  min-height: 100vh;
}

.header {
  margin-bottom: 30rpx;
}

.title {
  font-size: 48rpx;
  font-weight: bold;
}

.section {
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
  margin-bottom: 24rpx;
}

.section-title {
  font-size: 28rpx;
  color: #999;
  margin-bottom: 16rpx;
}

.avatar-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20rpx 0;
}

.avatar-image {
  width: 160rpx;
  height: 160rpx;
  border-radius: 80rpx;
  background: #f0f0f0;
  margin-bottom: 16rpx;
}

.change-hint {
  font-size: 24rpx;
  color: #667eea;
}

.nickname-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16rpx 0;
}

.nickname-text {
  font-size: 30rpx;
  color: #333;
}

.arrow {
  font-size: 48rpx;
  color: #999;
  font-weight: 300;
}

.tips {
  padding: 24rpx;
}

.tips-text {
  font-size: 24rpx;
  color: #999;
  text-align: center;
}
</style>
```

**步骤 2: 提交**

```bash
git add miniapp/src/pages/profile-edit/index.vue
git commit -m "feat: add profile edit page with avatar upload and nickname edit"
```

---

### 任务 6.3: 修改个人中心页面，添加点击头像跳转

**文件：**
- 修改: `miniapp/src/pages/profile/index.vue`

**步骤 1: 给头像区域添加点击事件**

修改头像部分的代码（第96-99行）：

```vue
<!-- 用户头部 -->
<view class="user-header" @click="goProfileEdit">
  <image class="user-avatar" :src="avatarUrl" mode="aspectFill" />
  <text class="user-name">{{ displayName }}</text>
</view>
```

**步骤 2: 在 script 中添加跳转函数**

在函数定义区域（第86行附近）添加：

```javascript
function goProfileEdit() {
  uni.navigateTo({ url: '/pages/profile-edit/index' })
}
```

**步骤 3: 提交**

```bash
git add miniapp/src/pages/profile/index.vue
git commit -m "feat: add click handler to avatar for profile edit navigation"
```

---

## 阶段 7: 小程序 - 设置页面添加退出和注销

### 任务 7.1: 添加退出登录和注销 API

**文件：**
- 修改: `miniapp/src/api/user.ts`

**步骤 1: 在文件末尾添加函数**

```typescript
/**
 * 注销账号
 */
export function deactivateAccount(): Promise<{
  data: { recovery_until: string }
  message: string
}> {
  return request({
    url: `${PREFIX}/me/deactivate`,
    method: 'POST'
  })
}

/**
 * 退出登录
 */
export function logout(): Promise<{ message: string }> {
  return request({
    url: '/api/v1/auth/logout',
    method: 'POST'
  })
}
```

**步骤 2: 提交**

```bash
git add miniapp/src/api/user.ts
git commit -m "feat: add deactivate and logout API functions"
```

---

### 任务 7.2: 修改设置页面，添加退出和注销功能

**文件：**
- 修改: `miniapp/src/pages/settings/index.vue`

**步骤 1: 在模板末尾（第93行之后）添加退出和注销按钮**

```vue
<!-- 退出登录 -->
<view class="section">
  <view class="section-title">退出登录</view>
  <button class="btn-logout" @click="handleLogout">退出登录</button>
</view>

<!-- 注销账号 -->
<view class="section danger-section">
  <view class="section-title">账号操作</view>
  <button class="btn-deactivate" @click="handleDeactivate">注销账号</button>
  <text class="warning-text">⚠️ 注销后30天内可通过登录恢复</text>
</view>
```

**步骤 2: 在 script 中添加处理函数**

在函数定义区域（第243行之后）添加：

```javascript
// 退出登录
async function handleLogout() {
  try {
    const res = await logout()

    // 清除本地存储
    uni.removeStorageSync('token')
    uni.removeStorageSync('refreshToken')
    uni.removeStorageSync('userInfo')

    // 清除 userStore
    userStore.$reset()

    uni.showToast({ title: '已退出登录', icon: 'success' })

    // 跳转到首页
    setTimeout(() => {
      uni.reLaunch({ url: '/pages/index' })
    }, 1000)
  } catch (e: any) {
    uni.showToast({ title: e?.message || '退出失败', icon: 'none' })
  }
}

// 注销账号
async function handleDeactivate() {
  try {
    // 二次确认
    const confirmRes: any = await uni.showModal({
      title: '确认注销账号？',
      content: '注销后您的数据将被保留，30天内可通过登录恢复账号。超过30天将无法恢复。',
      confirmText: '确认注销',
      confirmColor: '#ff4d4f',
    })

    if (!confirmRes.confirm) {
      return
    }

    const res = await deactivateAccount()

    // 清除本地存储
    uni.removeStorageSync('token')
    uni.removeStorageSync('refreshToken')
    uni.removeStorageSync('userInfo')

    // 清除 userStore
    userStore.$reset()

    uni.showModal({
      title: '注销成功',
      content: `账号已注销，${new Date(res.data.recovery_until).toLocaleDateString()} 前可通过登录恢复`,
      showCancel: false,
      success: () => {
        uni.reLaunch({ url: '/pages/index' })
      }
    })
  } catch (e: any) {
    uni.showToast({ title: e?.message || '注销失败', icon: 'none' })
  }
}
```

**步骤 3: 在 script 顶部导入区域添加**

```typescript
import { deactivateAccount, logout } from '@/api/user'
```

**步骤 4: 在 style 中添加样式**

```scss
.btn-logout {
  width: 100%;
  background: #fff;
  color: #333;
  border: 1rpx solid #e0e0e0;
  border-radius: 12rpx;
  font-size: 30rpx;
  margin-top: 16rpx;
}

.danger-section {
  margin-top: 40rpx;
}

.btn-deactivate {
  width: 100%;
  background: #ff4d4f;
  color: #fff;
  border: none;
  border-radius: 12rpx;
  font-size: 30rpx;
  margin-top: 16rpx;
}

.warning-text {
  display: block;
  font-size: 24rpx;
  color: #ff4d4f;
  text-align: center;
  margin-top: 16rpx;
}
```

**步骤 5: 提交**

```bash
git add miniapp/src/pages/settings/index.vue
git commit -m "feat: add logout and account deactivate functionality to settings"
```

---

## 阶段 8: 测试

### 任务 8.1: 后端集成测试

**文件：**
- 修改: `backend/tests/integration/test_user_flow.py` (在文件末尾添加)

**步骤 1: 添加测试函数**

```python
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_user_deactivate_and_reactivate(async_client: AsyncClient, test_user_token: str):
    """测试用户注销和恢复"""

    # 注销账号
    response = await async_client.post(
        "/api/v1/user/me/deactivate",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert "recovery_until" in data["data"]

    # 恢复账号
    response = await async_client.post(
        "/api/v1/user/me/reactivate",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
```

**步骤 2: 运行测试**

```bash
cd backend
pytest tests/integration/test_user_flow.py::test_user_deactivate_and_reactivate -v
```

预期输出: `PASSED`

**步骤 3: 提交**

```bash
git add backend/tests/integration/test_user_flow.py
git commit -m "test: add user deactivate and reactivate integration test"
```

---

### 任务 8.2: 端到端手动测试清单

**测试场景：**

1. **管理后台 - 协议管理**
   - [ ] 登录管理后台，访问 `/agreements`
   - [ ] 切换「用户协议」和「隐私协议」标签
   - [ ] 使用富文本编辑器编辑内容
   - [ ] 点击保存，验证保存成功

2. **管理后台 - 开屏设置**
   - [ ] 访问 `/splash`
   - [ ] 上传图片
   - [ ] 设置欢迎文字和倒计时
   - [ ] 保存配置

3. **小程序 - 个人资料编辑**
   - [ ] 进入「我的」页面，点击头像
   - [ ] 跳转到个人资料编辑页面
   - [ ] 点击头像，选择图片上传
   - [ ] 点击昵称，修改昵称
   - [ ] 验证修改成功

4. **小程序 - 退出登录**
   - [ ] 进入设置页面
   - [ ] 点击「退出登录」
   - [ ] 验证退出成功，返回首页

5. **小程序 - 注销账号**
   - [ ] 进入设置页面
   - [ ] 点击「注销账号」
   - [ ] 确认注销
   - [ ] 验证注销成功
   - [ ] 重新登录，验证账号自动恢复

---

## 总结

完成以上所有任务后，您将实现：

1. ✅ 管理后台的富文本协议编辑功能（Quill.js）
2. ✅ 管理后台的开屏页面设置（图片上传 + 配置）
3. ✅ 小程序个人资料编辑页面（头像上传 + 昵称修改）
4. ✅ 小程序设置页面的退出登录功能
5. ✅ 小程序设置页面的账号注销功能（30天软删除恢复）

**预计总提交数：** ~25 个 commits

**预计开发时间：** 4-6 小时
