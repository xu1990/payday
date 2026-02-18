# PayDay 自动化测试文档

## 概述

本文档说明 PayDay 项目的自动化测试结构、运行方法和最佳实践。

## 测试结构

```
PayDay/
├── backend/                     # 后端测试 (pytest)
│   ├── tests/
│   │   ├── api/                 # API 集成测试
│   │   │   ├── test_auth_api.py
│   │   │   ├── test_user_api.py
│   │   │   ├── test_post_api.py
│   │   │   ├── test_salary_api.py
│   │   │   ├── test_payment_api.py
│   │   │   ├── test_membership_api.py
│   │   │   ├── test_payday_api.py
│   │   │   ├── test_comment_api.py
│   │   │   └── test_notification_api.py
│   │   ├── core/                # 核心功能测试
│   │   ├── services/            # 服务层测试
│   │   ├── tasks/               # 异步任务测试
│   │   ├── utils/               # 工具函数测试
│   │   ├── conftest.py          # pytest 配置和 fixtures
│   │   └── test_utils.py        # 测试辅助工具
│   └── pytest.ini               # pytest 配置文件
│
├── miniapp/                     # 小程序测试 (vitest)
│   ├── tests/
│   │   ├── unit/
│   │   │   ├── components/      # 组件测试
│   │   │   │   ├── LazyImage.test.ts
│   │   │   │   ├── Loading.test.ts
│   │   │   │   └── EmptyState.test.ts
│   │   │   └── utils/           # 工具函数测试
│   │   │       ├── format.test.ts
│   │   │       └── toast.test.ts
│   │   ├── setup.ts             # 测试环境设置
│   │   └── utils/               # 测试辅助工具
│   └── vitest.config.ts         # vitest 配置文件
│
├── admin-web/                   # 管理后台测试 (vitest)
│   ├── tests/
│   │   ├── unit/
│   │   │   ├── components/      # 组件测试
│   │   │   │   ├── ActionButtons.test.ts
│   │   │   │   └── StatusTag.test.ts
│   │   │   └── utils/           # 工具函数测试
│   │   ├── setup.ts             # 测试环境设置
│   │   └── utils/               # 测试辅助工具
│   └── vitest.config.ts         # vitest 配置文件
│
└── package.json                 # 根目录测试脚本
```

## 运行测试

### 运行所有测试

```bash
# 从项目根目录运行所有三端测试
npm run test

# 或者分别运行
npm run test:backend
npm run test:admin
npm run test:miniapp
```

### Backend 测试

```bash
cd backend

# 运行所有测试
python3 -m pytest

# 运行特定文件
python3 -m pytest tests/api/test_auth_api.py

# 运行特定测试
python3 -m pytest tests/api/test_auth_api.py::test_login_with_invalid_code

# 显示详细输出
python3 -m pytest -v

# 运行带覆盖率的测试
python3 -m pytest --cov=app --cov-report=html
open htmlcov/index.html

# 只运行单元测试
pytest -m "not integration and not slow"

# 运行特定标记的测试
pytest -m asyncio
```

### Miniapp 测试

```bash
cd miniapp

# 运行所有测试
npm run test:run

# 监听模式运行
npm run test

# UI 模式运行
npm run test:ui

# 运行带覆盖率的测试
npm run test:coverage
open coverage/index.html
```

### Admin-web 测试

```bash
cd admin-web

# 运行所有测试
npm run test:run

# 监听模式运行
npm run test

# UI 模式运行
npm run test:ui

# 运行带覆盖率的测试
npm run test:coverage
open coverage/index.html
```

## 测试编写规范

### Backend API 测试模板

```python
"""
API 集成测试模板
"""
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app


@pytest.mark.asyncio
async def test_list_endpoint(db_session: AsyncSession):
    """测试列表接口"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/ENDPOINT")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_create_endpoint(db_session: AsyncSession, user_headers: dict):
    """测试创建接口"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/ENDPOINT",
            headers=user_headers,
            json={}
        )
        assert response.status_code in [200, 201]


@pytest.mark.asyncio
async def test_unauthorized_request():
    """测试未认证请求"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/ENDPOINT", json={})
        assert response.status_code == 401
```

### Miniapp 组件测试模板

```typescript
/**
 * 组件测试模板
 */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ComponentName from '@/components/ComponentName.vue'

describe('ComponentName 组件', () => {
  it('应该渲染', () => {
    const wrapper = mount(ComponentName, {
      props: {
        // props
      },
    })

    expect(wrapper.find('.class-name').exists()).toBe(true)
  })

  it('应该触发事件', async () => {
    const wrapper = mount(ComponentName)

    await wrapper.find('.button').trigger('click')
    expect(wrapper.emitted('event-name')).toBeTruthy()
  })
})
```

### Admin-web 组件测试模板

```typescript
/**
 * Admin 组件测试模板
 */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ComponentName from '@/components/ComponentName.vue'

describe('ComponentName 组件', () => {
  it('应该正确渲染', () => {
    const wrapper = mount(ComponentName, {
      props: {
        // props
      },
    })

    expect(wrapper.text()).toContain('预期文本')
  })

  it('应该响应 props 变化', async () => {
    const wrapper = mount(ComponentName, {
      props: {
        value: 'initial',
      },
    })

    await wrapper.setProps({ value: 'updated' })
    expect(wrapper.props('value')).toBe('updated')
  })
})
```

## 测试辅助工具

### Backend TestDataFactory

```python
from tests.test_utils import TestDataFactory

# 创建测试用户
user = await TestDataFactory.create_user(db_session)

# 创建测试帖子
post = await TestDataFactory.create_post(db_session, user.id)

# 创建测试薪资记录
config = await TestDataFactory.create_payday_config(db_session, user.id)
salary = await TestDataFactory.create_salary(db_session, user.id, config.id)
```

### Miniapp test-helpers

```typescript
import { createTestUserData, mockUniApi } from '@/tests/utils/test-helpers'

// 创建测试用户数据
const user = createTestUserData()

// Mock uni API
const uni = mockUniApi()
global.uni = uni
```

### Admin-web test-helpers

```typescript
import { createTestUser, mockElementPlus } from '@/tests/utils/test-helpers'

// 创建测试用户
const user = createTestUser()

// Mock Element Plus
const components = mockElementPlus()
```

## 最佳实践

1. **测试命名**: 使用清晰、描述性的测试名称
2. **独立性**: 每个测试应该独立运行，不依赖其他测试
3. **快速**: 测试应该快速执行，避免不必要的延迟
4. **可读性**: 测试代码应该清晰易读
5. **覆盖率**: 尽量提高代码覆盖率，重点关注核心业务逻辑
6. **Mock**: 合理使用 mock，避免过度依赖外部服务
7. **边界测试**: 测试边界条件和异常情况

## 持续集成

测试应该在以下情况下自动运行：
- 每次提交代码
- 每次创建 Pull Request
- 合并到主分支前

CI 配置示例：

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run Backend Tests
        run: |
          cd backend
          pip install -r requirements-dev.txt
          pytest --cov=app

      - name: Run Miniapp Tests
        run: |
          cd miniapp
          npm install
          npm run test:coverage

      - name: Run Admin-web Tests
        run: |
          cd admin-web
          npm install
          npm run test:coverage
```

## 常见问题

### Backend 测试

**问题**: pytest 命令未找到
```bash
# 解决方案：使用 python3 -m pytest
python3 -m pytest
```

**问题**: 数据库连接错误
```bash
# 解决方案：确保测试配置正确
# tests 使用 SQLite 内存数据库，无需外部数据库
```

### Miniapp 测试

**问题**: 找不到测试文件
```bash
# 解决方案：确保 vitest.config.ts 的 include 包含 tests/ 目录
include: ['src/**/*.{test,spec}.*', 'tests/**/*.{test,spec}.*']
```

**问题**: uni API 未定义
```bash
# 解决方案：在 tests/setup.ts 中 mock uni 对象
global.uni = { ... }
```

### Admin-web 测试

**问题**: Element Plus 组件未渲染
```bash
# 解决方案：在测试中 stub Element Plus 组件
config.global.stubs = {
  ElButton: false,  // 使用真实组件
  ElTable: true,    // 使用 stub
}
```

## 资源

- [Pytest 文档](https://docs.pytest.org/)
- [Vitest 文档](https://vitest.dev/)
- [Vue Test Utils 文档](https://test-utils.vuejs.org/)
- [SQLAlchemy 文档](https://docs.sqlalchemy.org/)
