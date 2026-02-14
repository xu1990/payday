# 贡献者指南

感谢你考虑为 PayDay 项目做出贡献！🎉

这份指南将帮助你了解贡献流程、开发环境设置和代码规范。

## 📋 目录

- [快速开始](#快速开始)
- [开发环境设置](#开发环境设置)
- [项目结构](#项目结构)
- [开发工作流](#开发工作流)
- [代码规范](#代码规范)
- [提交规范](#提交规范)
- [Pull Request 流程](#pull-request-流程)
- [问题报告](#问题报告)
- [行为准则](#行为准则)

---

## 快速开始

### 前置条件

- Python 3.11+ (Backend)
- Node.js 18+ (Admin-Web & Miniapp)
- MySQL 8.0+ / MariaDB
- Redis 6+
- Git

### 克隆仓库

```bash
git clone https://github.com/your-org/payday.git
cd payday
```

---

## 开发环境设置

### 1. Backend (FastAPI)

#### 环境变量配置

```bash
cd backend
cp .env.example .env
# 编辑 .env 文件，填写实际的配置值
```

**必需配置**:
- MySQL 连接信息
- Redis 连接信息
- JWT 密钥
- 加密密钥
- 微信小程序凭证

#### 安装依赖

```bash
pip install -r requirements-dev.txt
```

#### 数据库迁移

```bash
python3 -m alembic upgrade head
```

#### 创建管理员用户

```bash
python3 scripts/create_first_admin.py
```

#### 运行开发服务器

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 运行 Celery Worker

```bash
# Terminal 1: Redis + Celery Worker
celery -A app.tasks.worker -l info

# Terminal 2: Celery Beat (定时任务)
celery -A app.tasks.beat -l info
```

---

### 2. Admin-Web (Vue3)

#### 安装依赖

```bash
cd admin-web
npm install
```

#### 环境变量

开发环境无需额外环境变量，API 请求通过 Vite proxy 到 Backend。

#### 运行开发服务器

```bash
npm run dev
```

访问: `http://localhost:5174`

#### 类型检查

```bash
npm run typecheck
```

---

### 3. Miniapp (uni-app)

#### 安装依赖

```bash
cd miniapp
npm install
```

#### 运行开发服务器

```bash
npm run dev
```

这会启动微信开发者工具。

---

## 项目结构

```
payday/
├── backend/               # 后端服务 (FastAPI)
│   ├── app/
│   │   ├── api/v1/    # API 路由
│   │   ├── core/      # 核心配置
│   │   ├── models/    # 数据模型
│   │   ├── schemas/   # Pydantic schemas
│   │   ├── services/  # 业务逻辑
│   │   ├── tasks/     # Celery 任务
│   │   └── utils/     # 工具函数
│   ├── alembic/        # 数据库迁移
│   ├── tests/          # 测试
│   └── scripts/        # 工具脚本
│
├── admin-web/            # 管理后台 (Vue3)
│   ├── src/
│   │   ├── api/          # API 客户端
│   │   ├── components/   # Vue 组件
│   │   ├── composables/  # Composition API
│   │   ├── stores/       # Pinia stores
│   │   ├── views/        # 页面组件
│   │   └── utils/        # 工具函数
│   └── tests/           # 测试
│
├── miniapp/              # 小程序 (uni-app)
│   ├── src/
│   │   ├── api/          # API 客户端
│   │   ├── components/   # 组件
│   │   ├── pages/        # 页面
│   │   ├── stores/       # Pinia stores
│   │   └── utils/        # 工具函数
│   └── tests/           # 测试
│
└── docs/                # 项目文档
    ├── 技术方案_v1.0.md
    └── 迭代规划_Sprint与任务.md
```

---

## 开发工作流

### 1. 分支策略

- `main`: 生产分支，保持稳定
- `develop`: 开发主分支
- `feature/xxx`: 功能分支
- `bugfix/xxx`: Bug 修复分支
- `hotfix/xxx`: 紧急修复分支

### 2. 开始新功能

```bash
# 更新 develop 分支
git checkout develop
git pull origin develop

# 创建功能分支
git checkout -b feature/your-feature-name

# 开始开发...
```

### 3. 提交代码

遵循 [提交规范](#提交规范)：

```bash
git add .
git commit -m "feat(user): 添加用户头像上传功能"
```

### 4. 推送分支

```bash
git push origin feature/your-feature-name
```

### 5. 创建 Pull Request

- 前往 GitHub 创建 Pull Request
- 填写 PR 模板
- 等待 CI 检查通过
- 请求代码审查

---

## 代码规范

### Backend (Python)

#### 风格指南

遵循 **PEP 8** 和项目约定：

```python
# 好的示例
async def get_user(db: AsyncSession, user_id: str) -> User:
    """获取用户信息"""
    user = await db.get(User, user_id)
    return user

# 避免的示例
async def getUser(db, userId):
    u=await db.get(User, userId);return u
```

#### 类型提示

**必须**使用类型提示：

```python
# 函数签名
async def create_order(
    db: AsyncSession,
    user_id: str,
    membership_id: str
) -> MembershipOrder:
    """创建订单"""
    pass

# 变量
user: User | None = None
orders: list[Order] = []
```

#### 文档字符串

为公共函数添加 docstring：

```python
def calculate_payday(date: int, job_name: str) -> datetime:
    """
    计算发薪日

    Args:
        date: 发薪日（1-31）
        job_name: 职位名称

    Returns:
        计算后的发薪日时间

    Raises:
        ValidationException: 日期或职位无效
    """
    # ...
```

---

### Frontend (TypeScript + Vue3)

#### 组件命名

- **PascalCase** for components: `UserList.vue`
- **camelCase** for functions: `getUserData`
- **kebab-case** for files: `user-service.ts`

#### Composition API

优先使用 `<script setup>`：

```vue
<script setup lang="ts">
import { ref, computed } from 'vue'

const count = ref(0)
const doubled = computed(() => count.value * 2)
</script>
```

#### Props 定义

```typescript
interface Props {
  title: string
  count?: number
}

const props = withDefaults(defineProps<Props>(), {
  count: 0,
})
```

---

## 提交规范

我们使用 [Conventional Commits](https://conventionalcommits.org/) 规范。

### 格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type 类型

| Type | 描述 | 示例 |
|-------|--------|--------|
| `feat` | 新功能 | `feat(user): 添加用户关注功能` |
| `fix` | Bug 修复 | `fix(auth): 修复 token 刷新失败` |
| `docs` | 文档更新 | `docs: 更新 API 文档` |
| `style` | 代码格式（不影响功能） | `style: 格式化导入语句` |
| `refactor` | 重构（不是新功能也不是修复） | `refactor(api): 简化错误处理` |
| `perf` | 性能优化 | `perf(cache): 优化 Redis 查询` |
| `test` | 添加测试 | `test(user): 添加用户模型测试` |
| `chore` | 构建/工具链配置 | `chore: 更新依赖版本` |

### Scope 范围

| Scope | 说明 |
|-------|--------|
| `user` | 用户相关 |
| `payday` | 薪日配置 |
| `salary` | 薪资记录 |
| `post` | 帖子和社区 |
| `auth` | 认证授权 |
| `admin` | 管理后台 |
| `db` | 数据库模型和迁移 |
| `api` | API 路由 |
| `ui` | 前端组件 |

### 示例

```bash
# 功能
feat(post): 添加帖子图片上传功能

# 修复
fix(auth): 修复刷新 token 时 401 错误

# 文档
docs(api): 更新 /api/v1/users 端点说明

# 重构
refactor(salary): 简化加密/解密逻辑

# 性能
perf(cache): 优化热帖查询性能，添加索引

# 测试
test(comment): 添加评论嵌套测试

# 构建
chore(deps): 升级 FastAPI 到 0.104.0
```

---

## Pull Request 流程

### PR 标题

使用与 commit 相同的格式：

```
feat(user): 添加用户头像上传功能
```

### PR 描述模板

创建 PR 时请填写：

```markdown
## 改动说明

简要描述这个 PR 做了什么。

## 改动类型

- [ ] 新功能 (feat)
- [ ] Bug 修复 (fix)
- [ ] 性能优化 (perf)
- [ ] 重构 (refactor)
- [ ] 文档更新 (docs)
- [ ] 测试补充 (test)

## 测试

描述你如何测试这些改动：

- [ ] 单元测试通过
- [ ] 集成测试通过
- [ ] 手动测试（描述测试场景）

## 截图/演示

如果是 UI 改动，添加截图或 GIF：

[上传截图]

## 相关 Issue

Closes #123
Related to #456

## Checklist

- [ ] 代码遵循项目规范
- [ ] 已自审代码
- [ ] 已添加必要的文档
- [ ] 已更新相关文档
- [ ] 所有测试通过
- [ ] 无合并冲突
```

### 审查标准

代码审查将检查：

1. **功能完整性**: 是否完整实现了需求
2. **代码质量**: 是否遵循规范
3. **类型安全**: 是否有类型错误
4. **测试覆盖**: 是否有足够测试
5. **性能影响**: 是否有性能问题
6. **安全性**: 是否有安全漏洞
7. **向后兼容**: 是否破坏现有功能

### 合并要求

- ✅ 至少一位维护者批准 (LGTM)
- ✅ CI 检查全部通过
- ✅ 无 unresolved conversations
- ✅ 分支可自动合并（无冲突）

---

## 问题报告

### Bug 报告

使用 Issue Tracker 报告 Bug：

**标题模板**:

```markdown
[Bug Title]

**环境信息**:
- Backend 版本:
- Admin-Web 版本:
- Miniapp 版本:
- 浏览器/平台:

**问题描述**:
清晰描述遇到的问题。

**复现步骤**:
1. 步骤一
2. 步骤二
3. ...

**预期行为**:
描述应该发生什么。

**实际行为**:
描述实际发生了什么。

**截图**:
如果可能，添加截图。

**日志**:
粘贴相关错误日志。

**附加信息**:
其他可能有助于解决问题的信息。
```

### 功能请求

```markdown
[Feature Title]

**问题描述**:
清晰描述你希望添加的功能。

**使用场景**:
描述在什么情况下会使用这个功能。

**建议方案**（可选）:
如果有想法，描述如何实现。

**替代方案**（可选）:
描述是否有其他方式达到同样目的。
```

---

## 行为准则

### 我们的承诺

- **尊重**: 尊重不同观点和经验水平
- **包容**: 欢迎不同背景的贡献者
- **协作**: 优先考虑团队和项目利益
- **建设性**: 关注解决问题，而非指责

### 不可接受的行为

- 骚扰或贬低言论
- 人身攻击或侮辱
- 垃圾信息或无关内容
- 侵犯隐私

如有违反行为，将立即处理。

---

## 获取帮助

### 官方渠道

- **GitHub Issues**: [项目 Issues](https://github.com/your-org/payday/issues)
- **GitHub Discussions**: [讨论区](https://github.com/your-org/payday/discussions)
- **Email**: support@payday.com

### 开发者联系

- **技术负责人**: [Name] (@github)
- **项目维护**: [Name] (@github)

---

## 致谢

感谢所有为 PayDay 项目做出贡献的开发者！💚

你的贡献让这个项目变得更好。

---

**更新日期**: 2026-02-14
**版本**: 1.0.0
