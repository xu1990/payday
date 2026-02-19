# 用户协议、开屏页面、个人资料编辑功能设计

**日期**: 2026-02-19
**设计师**: Claude
**状态**: ✅ 已批准

---

## 1. 概述

本文档描述了以下5个功能的完整设计方案：

1. 管理后台增加用户协议和隐私协议编辑功能（支持富文本）
2. 管理后台增加开屏页面设置（支持图文和显示倒计时）
3. 小程序「我的」页面增加用户头像和昵称，点击可修改
4. 设置页面增加个人信息显示且支持修改头像和昵称
5. 设置页面增加退出和注销功能

---

## 2. 整体架构

### 2.1 架构方案

采用 **方案 A：一体化用户服务**，所有功能在现有架构基础上扩展。

**理由：**
- 与现有架构模式一致
- 复用现有 MiniprogramConfig 表
- 减少复杂度，易于维护

### 2.2 后端变更

**新增/修改 API：**
- `/api/v1/admin/config/agreements` - 协议管理（GET/POST）
- `/api/v1/admin/config/splash` - 开屏配置（GET/POST）
- `/api/v1/user/me/upload-avatar` - 头像上传（POST）
- `/api/v1/user/me/deactivate` - 注销账号（POST）
- `/api/v1/user/me/reactivate` - 恢复账号（POST）
- `/api/v1/auth/logout` - 退出登录（POST）
- `/api/v1/config/public` - 小程序获取公共配置（GET）

**数据库变更：**
- `users` 表添加 `deactivated_at` 列（软删除）
- 使用现有 `miniprogram_configs` 表存储协议和开屏配置

### 2.3 管理后台变更

**新增页面：**
- `AgreementManagement.vue` - 协议管理页面（富文本编辑器）
- `SplashSettings.vue` - 开屏页面设置

### 2.4 小程序变更

**新增页面：**
- `pages/profile-edit/index.vue` - 个人资料编辑页面

**修改页面：**
- `pages/settings/index.vue` - 添加退出登录和注销账号功能

---

## 3. 详细设计

### 3.1 管理后台 - 协议管理

#### 3.1.1 功能需求

- 两个标签页：「用户协议」和「隐私协议」
- 富文本编辑器：使用 Quill.js
- 支持格式：加粗、斜体、列表、链接、标题
- 保存按钮
- 预览模式
- 显示最后更新时间

#### 3.1.2 API 设计

```
GET /api/v1/admin/config/agreements
Response: {
  user_agreement: string,      // HTML 内容
  privacy_agreement: string,   // HTML 内容
  updated_at: string
}

POST /api/v1/admin/config/agreements
Request: {
  type: 'user' | 'privacy',
  content: string  // HTML 内容
}
Response: {
  message: string,
  updated_at: string
}
```

#### 3.1.3 数据存储

使用 `miniprogram_configs` 表：

| key | value 类型 | 说明 |
|-----|-----------|------|
| user_agreement | Text (HTML) | 用户协议内容 |
| privacy_agreement | Text (HTML) | 隐私协议内容 |

#### 3.1.4 UI 设计

```
+------------------------------------------+
| 协议管理                                 |
+------------------------------------------+
| [用户协议] [隐私协议]                    |
+------------------------------------------+
| +--------------------------------------+ |
| | [B] [I] [U] [列表] [链接] [标题]     | |
| +--------------------------------------+ |
| |                                      | |
| | [富文本编辑区域]                      | |
| |                                      | |
| +--------------------------------------+ |
| 最后更新: 2025-01-15 10:30              |
| [保存] [预览]                           |
+------------------------------------------+
```

---

### 3.2 管理后台 - 开屏页面设置

#### 3.2.1 功能需求

- 上传开屏图片（支持 COS 上传）
- 配置欢迎文字
- 配置倒计时时长（秒）
- 启用/禁用开关
- 预览功能

#### 3.2.2 API 设计

```
GET /api/v1/admin/config/splash
Response: {
  image_url: string,
  content: string,
  countdown: number,
  is_active: boolean
}

POST /api/v1/admin/config/splash
Request: {
  image_url: string,
  content: string,
  countdown: number,
  is_active: boolean
}
Response: { message: string }
```

#### 3.2.3 数据存储

使用 `miniprogram_configs` 表：

| key | value 类型 | 说明 |
|-----|-----------|------|
| splash_config | JSON | 开屏配置（JSON 字符串） |

JSON 结构：
```json
{
  "image_url": "https://xxx.cos.ap-beijing.myqcloud.com/splash.jpg",
  "content": "欢迎使用薪日 PayDay",
  "countdown": 3,
  "is_active": true
}
```

#### 3.2.4 UI 设计

```
+------------------------------------------+
| 开屏页面设置                             |
+------------------------------------------+
| 上传图片: [选择文件]                     |
|          [当前图片预览 200x300]          |
| 欢迎文字: [_____________________________] |
| 倒计时时长: [3] 秒                       |
| 启用状态: [开关 ✅]                       |
| [保存配置] [预览效果]                    |
+------------------------------------------+
```

---

### 3.3 小程序 - 个人资料编辑页面

#### 3.3.1 功能需求

- 显示当前头像和昵称
- 点击头像 → 选择图片 → 上传 → 保存
- 点击昵称 → 弹出输入框 → 保存
- 实时保存到服务器

#### 3.3.2 API 设计

```
POST /api/v1/user/me/upload-avatar
Content-Type: multipart/form-data
Request: { file: binary }
Response: {
  url: string  // COS URL
}

PUT /api/v1/user/me  # 已存在
Request: { nickname: string }
Response: UserInfo
```

#### 3.3.3 UI 设计

```
+------------------------------------------+
| 编辑个人资料              [保存]         |
+------------------------------------------+
|                                          |
|        [头像预览 120x120]                |
|        点击更换头像                      |
|                                          |
+------------------------------------------+
| 昵称                                    |
| [当前昵称_______________] [修改]         |
+------------------------------------------+
```

#### 3.3.4 头像上传流程

```
用户操作          小程序前端         后端API         腾讯云COS
   |                 |                 |               |
选择图片      uni.chooseImage()          |               |
   |---------------->|                  |               |
   |           tempFilePath             |               |
上传文件       uni.uploadFile()          |               |
   |-------------------------------->|               |
   |        multipart/form-data        |               |
   |                 |         上传到COS               |
   |                 |---------------->|               |
   |                 |           返回URL               |
   |                 |<----------------|               |
   |                 |      保存到用户表                |
   |                 |<---------------|               |
   |          返回 avatar_url          |               |
   |<--------------------------------|               |
显示新头像        更新UI                 |               |
```

---

### 3.4 设置页面 - 退出登录和注销

#### 3.4.1 功能需求

**退出登录：**
- 清除本地 token 和用户信息
- 跳转到首页

**注销账号：**
- 二次确认弹窗（警告 30 天恢复期）
- 软删除账号
- 清除本地数据
- 跳转到首页

#### 3.4.2 API 设计

```
POST /api/v1/user/me/deactivate
Response: {
  message: string,
  recovery_until: string  // ISO 8601 日期
}

POST /api/v1/user/me/reactivate
Request: { openid: string }
Response: { message: string, user: UserInfo }

POST /api/v1/auth/logout
Response: { message: string }
```

#### 3.4.3 数据库变更

`users` 表添加列：

```sql
ALTER TABLE users ADD COLUMN deactivated_at DATETIME NULL COMMENT '注销时间（软删除）';
```

- 注销时：`deactivated_at = NOW()`
- 恢复时：`deactivated_at = NULL`

#### 3.4.4 UI 设计

```
+------------------------------------------+
| 退出登录                                 |
| [退出登录]                               |
+------------------------------------------+
| 账号操作                                 |
| [注销账号]                               |
| ⚠️ 注销后30天内可通过登录恢复            |
+------------------------------------------+
```

---

## 4. 错误处理

### 4.1 网络错误

- 所有 API 调用使用 try-catch
- 显示 `uni.showToast({ title: '网络错误', icon: 'none' })`

### 4.2 上传失败

| 错误场景 | 提示文案 |
|---------|---------|
| 图片过大（>5MB） | 「图片太大，请选择5MB以内的图片」 |
| 上传超时 | 「上传失败，请重试」 |
| COS 错误 | 「上传失败，请联系客服」 |

### 4.3 账号操作

| 操作 | 成功提示 | 失败提示 |
|-----|---------|---------|
| 退出登录 | 「已退出登录」 | 「退出失败，请重试」 |
| 注销账号 | 「注销成功，30天内可恢复」 | 「注销失败：{原因}」 |
| 恢复账号 | 「账号已恢复」 | 「恢复失败：{原因}」 |

---

## 5. 缓存策略

### 5.1 个人资料

- 修改后立即更新 userStore
- 下次启动时重新获取

### 5.2 协议和开屏配置

- 小程序启动时获取
- 缓存 1 小时（避免频繁请求）

---

## 6. 技术选型

### 6.1 富文本编辑器

**选择：Quill.js**

**理由：**
- 轻量级（~43KB gzipped）
- API 简单易用
- 良好的移动端支持
- Vue 3 友好

**安装：**
```bash
npm install @vueup/vue-quill quill
```

### 6.2 图片上传

**选择：腾讯云 COS（已配置）**

**理由：**
- 项目已集成
- 稳定可靠
- 成本低廉

---

## 7. 安全考虑

### 7.1 协议内容

- 存储为 HTML，需要进行 XSS 防护
- 显示时使用富文本组件的默认安全过滤

### 7.2 图片上传

- 限制文件类型：仅允许 jpg/png/gif
- 限制文件大小：最大 5MB
- 文件名使用 UUID 避免冲突

### 7.3 账号注销

- 软删除确保数据可恢复
- 30 天后可彻底清理（后台任务）
- 注销后无法访问任何需要登录的功能

---

## 8. 测试计划

### 8.1 单元测试

- 协议 CRUD 操作
- 开屏配置 CRUD 操作
- 头像上传流程
- 账号注销/恢复流程

### 8.2 集成测试

- 管理后台编辑协议 → 小程序显示协议
- 管理后台配置开屏 → 小程序显示开屏
- 小程序上传头像 → 数据库更新
- 小程序注销账号 → 登录时自动恢复

### 8.3 UI 测试

- 富文本编辑器功能
- 图片上传交互
- 二次确认弹窗

---

## 9. 实施顺序

1. **数据库变更** - 添加 `deactivated_at` 列
2. **后端 API** - 实现所有新增接口
3. **管理后台** - 协议管理和开屏设置页面
4. **小程序** - 个人资料编辑页面
5. **小程序** - 设置页面添加退出/注销功能
6. **测试** - 端到端测试
7. **部署** - 上线

---

## 附录：数据库迁移 SQL

```sql
-- 添加账号注销时间列
ALTER TABLE users
ADD COLUMN deactivated_at DATETIME NULL
COMMENT '注销时间（软删除）';

-- 添加索引
CREATE INDEX idx_users_deactivated_at ON users(deactivated_at);
```
