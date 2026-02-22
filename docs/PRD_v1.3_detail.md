# 薪日 PayDay - 产品需求文档 v1.3

## 文档信息
- **文档版本**: v1.3
- **创建日期**: 2026-02-21
- **产品名称**: 薪日 PayDay
- **产品类型**: 微信小程序 + Web管理后台
- **文档状态**: 增强版（含实现分析）
- **基于版本**: v1.2（详细版）
- **增强内容**: 实现状态分析 + Sprint任务分解 + 数据库迁移指南 + API影响分析

---

# 文档修订说明

## v1.3 新增内容

本版本在v1.2基础上新增以下章节：

1. **实现状态分析** - 每个功能模块的当前实现差距分析
2. **数据库迁移清单** - 具体的迁移脚本和验证方法
3. **API影响分析** - 新增/修改端点的详细说明
4. **验收标准** - 每个功能的明确验收条件
5. **Sprint任务分解** - 6个Sprint的详细任务卡片
6. **实现追踪矩阵** - 项目管理用的动态追踪表
7. **风险与阻塞跟踪** - 风险识别和缓解措施

## 使用指南

- **产品经理** - 重点阅读功能描述、UI设计、验收标准
- **后端开发** - 重点阅读数据模型、API接口、数据库迁移指南
- **前端开发** - 重点阅读UI设计、API影响分析
- **测试工程师** - 重点阅读验收标准、测试用例集
- **项目经理** - 重点阅读Sprint任务分解、实现追踪矩阵

---

# 一、版本概述

## 1.1 版本更新说明

v1.2 版本在 v1.1 基础上新增以下核心功能模块：

| 序号 | 功能模块 | 说明 | 优先级 | 实现状态 |
|------|----------|------|--------|----------|
| 1 | 手机号登录 | 授权手机号登录，实现多端统一 | P0 | 🟡 部分实现 |
| 2 | 工资用途记录 | 记录第一笔工资的使用去向 | P1 | 🔴 未开始 |
| 3 | 每月支出明细 | 记录每月工资的花销明细 | P1 | 🔴 未开始 |
| 4 | 年终奖展示 | 晒出年终奖，增加社区互动 | P1 | 🔴 未开始 |
| 5 | 发薪情绪/延迟记录 | 记录发薪情绪、延迟发薪、拖欠情况 | P1 | 🟡 部分实现 |
| 6 | 存款目标 | 设置每月存款目标，追踪储蓄进度 | P2 | 🔴 未开始 |
| 7 | 打卡功能 | 加班打卡、日常打卡等 | P2 | 🟢 已完成 |
| 8 | 能力值系统 | 用户能力值体系，关联多模块 | P2 | 🔴 未开始 |
| 9 | 能力值兑换 | 使用能力值兑换实物奖励 | P2 | 🔴 未开始 |

**状态图例：**
- 🟢 已完成（Phase 3已实现）
- 🟡 部分完成（有基础，需扩展）
- 🔴 未开始（全新开发）

## 1.2 版本定位

v1.2 是薪日 PayDay 从「工资记录社区」向「职场生活+轻理财+成长体系」升级的关键版本，通过：
- **增强理财属性**：支出记录、存款目标
- **强化情绪价值**：年终奖、发薪情绪、延迟吐槽
- **引入成长体系**：能力值系统、打卡、兑换

提升用户粘性和活跃度，为后续商业化奠定基础。

---

# 二、新增功能详细说明

## 2.1 手机号登录（P0 - 最高优先级）

### 2.1.1 功能描述

在现有微信 openid 登录基础上，增加手机号授权登录，实现：
- 同一手机号对应同一个用户
- 多设备登录（小程序 + 未来H5/App）
- 更好的账号安全管控

### 2.1.2 实现状态分析

**实现状态**: 🟡 部分实现

**已有内容**:
- ✅ 微信openid登录 (backend/app/api/v1/auth.py)
- ✅ JWT认证体系 (backend/app/core/security.py)
- ✅ User模型基础字段 (backend/app/models/user.py)

**需要新增**:
- ❌ 手机号授权获取（前端）
- ❌ 手机号绑定/解绑逻辑（后端API）
- ❌ 手机号验证流程
- ❌ 多端统一登录逻辑

**模型变更**:
```diff
# backend/app/models/user.py
+ phone_number = Column(String(20), nullable=True, index=True, comment="手机号（加密）")
+ phone_verified = Column(Integer, default=0, comment="手机号是否验证")
```

**API影响**:
- 修改: `POST /api/v1/auth/login` (新增phoneNumberCode参数)
- 新增: `POST /api/v1/user/bind-phone`
- 新增: `POST /api/v1/user/change-phone`
- 新增: `GET /api/v1/user/phone-status`

**预估工作量**: 3人日（后端2人日 + 前端1人日）

**依赖关系**: 无（可独立开发）

### 2.1.3 用户流程

```
首次登录
    ↓
微信授权获取用户信息
    ↓
【新增】请求手机号授权
    ├─ 同意 → 获取手机号
    │         ↓
    │         检查手机号是否已注册
    │         ├─ 已注册 → 绑定到现有账号
    │         └─ 未注册 → 创建新账号
    │
    └─ 拒绝 → 使用 openid 登录（降级体验）
              提示后续可在设置中绑定手机号
```

### 2.1.4 UI 设计

**登录页面更新**：
```
┌─────────────────────────────────┐
│         薪日 PayDay              │
│                                 │
│    ┌─────────────────────┐      │
│    │   [微信图标]         │      │
│    │   微信一键登录        │      │
│    └─────────────────────┘      │
│                                 │
│    ┌─────────────────────┐      │
│    │   [手机号图标]       │      │
│    │   获取手机号         │      │
│    └─────────────────────┘      │
│                                 │
│  登录即表示同意《用户协议》      │
│  和《隐私政策》                  │
└─────────────────────────────────┘
```

**设置页入口**：
```
┌─────────────────────────────────┐
│  设置                            │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│  账号安全                        │
│    手机号    138****8888  [已绑定]│
│    微信账号  已绑定              │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│  隐私设置                        │
└─────────────────────────────────┘
```

### 2.1.5 数据模型

**用户表扩展**：
```sql
ALTER TABLE users
ADD COLUMN phone_number VARCHAR(20) COMMENT '手机号（加密存储）',
ADD COLUMN phone_verified TINYINT DEFAULT 0 COMMENT '手机号是否验证（0=未验证，1=已验证）',
ADD INDEX idx_phone (phone_number);
```

**TypeScript 类型定义**：
```typescript
interface User {
  // ... 现有字段
  phoneNumber?: string;        // 手机号（加密存储）
  phoneVerified: boolean;      // 是否已验证
}

interface LoginDTO {
  code: string;                // wx.login 获取的 code
  phoneNumberCode?: string;    // 手机号授权 code（可选）
}
```

### 2.1.6 数据库迁移清单

**迁移脚本**: `backend/alembic/versions/4_1_001_phone_login.py`

```python
from alembic import op
import sqlalchemy as sa

def upgrade():
    # 添加手机号字段
    op.add_column('users', sa.Column('phone_number', sa.String(20), nullable=True))
    op.add_column('users', sa.Column('phone_verified', sa.Integer, default=0))

    # 创建索引
    op.create_index('idx_users_phone', 'users', ['phone_number'])

    # 数据注释
    op.execute("COMMENT ON COLUMN users.phone_number IS '手机号（加密存储）'")
    op.execute("COMMENT ON COLUMN users.phone_verified IS '手机号是否验证（0=未验证，1=已验证）'")

def downgrade():
    op.drop_index('idx_users_phone', 'users')
    op.drop_column('users', 'phone_verified')
    op.drop_column('users', 'phone_number')
```

**验证SQL**：
```sql
-- 验证字段是否添加成功
DESCRIBE users;

-- 验证索引
SHOW INDEX FROM users WHERE Key_name = 'idx_users_phone';

-- 数据完整性检查
SELECT COUNT(*) as total_users,
       COUNT(phone_number) as users_with_phone
FROM users;
```

**风险提示**:
- 🟢 低风险：仅添加字段，不影响现有数据
- ⚠️ 注意：手机号需要加密存储（使用app/utils/encryption.py）
- 📋 回滚方案：提供downgrade脚本

### 2.1.7 API 接口

```typescript
// 小程序端
POST /api/v1/auth/login
Request Body:
{
  "code": string,              // 微信登录 code
  "phoneNumberCode": string?   // 手机号授权 code（可选）
}

Response:
{
  "access_token": string,
  "user": {
    "id": string,
    "anonymousName": string,
    "avatar": string,
    "phoneNumber": string?,    // 已绑定时返回（脱敏：138****8888）
    "phoneVerified": boolean,
    "isNewUser": boolean
  }
}

// 绑定手机号（后续绑定）
POST /api/v1/user/bind-phone
Request Body:
{
  "phoneNumberCode": string
}

Response:
{
  "success": true,
  "phoneNumber": string  // 脱敏显示
}

// 更换手机号
POST /api/v1/user/change-phone
Request Body:
{
  "newPhoneNumberCode": string,
  "verificationCode": string    // 短信验证码（暂不实现）
}

Response:
{
  "success": true
}

// 查询手机号状态
GET /api/v1/user/phone-status
Response:
{
  "hasPhone": boolean,
  "phoneNumber": string?,  // 脱敏显示
  "phoneVerified": boolean
}
```

### 2.1.8 手机号脱敏策略

- 存储时加密（AES-256，使用 `app/utils/encryption.py`）
- 展示时脱敏（138****8888）
- 仅用户本人可见完整手机号
- 管理后台查看需权限审批

### 2.1.9 验收标准

**功能验收**:
- ✅ 用户首次登录可选择授权手机号
- ✅ 授权手机号后自动绑定/创建账号
- ✅ 拒绝授权仍可使用openid登录（降级体验）
- ✅ 可在设置中查看/绑定/更换手机号
- ✅ 手机号展示时脱敏显示
- ✅ 手机号加密存储

**技术验收**:
- ✅ 数据库迁移成功执行
- ✅ API接口返回正确数据
- ✅ 加密存储验证通过
- ✅ 降级方案测试通过

**测试用例**:
- 授权手机号成功场景
- 拒绝手机号授权场景
- 手机号已存在账号绑定场景
- 手机号解绑/更换场景
- 手机号加密/脱敏验证

---

## 2.2 工资用途记录

### 2.2.1 功能描述

记录「第一笔工资」的使用去向，打造职场人的「第一次」仪式感。

### 2.2.2 实现状态分析

**实现状态**: 🔴 未开始

**需要新增**:
- ❌ SalaryUsageRecord模型
- ❌ 工资用途记录API（CRUD）
- ❌ 第一笔工资用途社区展示
- ❌ 用途统计接口

**预估工作量**: 5人日（后端3人日 + 前端2人日）

**依赖关系**:
- 依赖SalaryRecord模型（已存在）
- 建议在Sprint 4.1第一周完成

### 2.2.3 业务流程

```
用户记录第一笔工资后
    ↓
自动弹出引导："记录你的第一笔工资是怎么用的？"
    ↓
进入工资用途记录页面
    ↓
选择/填写用途分类
    ↓
保存并生成分享卡片
```

### 2.2.4 用途分类预设

| 一级分类 | 二级分类 | 图标 |
|----------|----------|------|
| 💰 存起来 | 银行存款、理财、余额宝 | 钱袋 |
| 🏠 交家里 | 给父母、还房贷、家用 | 房子 |
| 🛒 买东西 | 数码产品、衣服、日用品 | 购物袋 |
| 🍖 吃顿好的 | 大餐、火锅、自助餐 | 美食 |
| 🎉 娱乐玩乐 | KTV、游戏、旅游 | 游戏手柄 |
| 🎁 送礼请客 | 请同事吃饭、送礼 | 礼物 |
| 📚 学习提升 | 买书、课程、考证 | 书本 |
| 💸 还债还贷 | 信用卡、花呗、网贷 | 账单 |
| 📱 其他 | 自定义输入 | 省略号 |

### 2.2.5 UI 设计

**工资用途记录页**：
```
┌─────────────────────────────────┐
│  ← 第一笔工资用途                │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│                                 │
│  你的第一笔工资（¥3,500）       │
│  是怎么用的？                    │
│                                 │
│  💰 存起来        [¥2000]        │
│  🏠 交家里        [¥1000]        │
│  🍖 吃顿好的      [¥500]         │
│                                 │
│  [+ 添加用途]                    │
│                                 │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│  总计：¥3,500                   │
│                                 │
│     [保存并生成分享卡]           │
└─────────────────────────────────┘
```

**分享卡片样式**：
```
┌─────────────────────────────────┐
│     我的职场第一笔工资           │
│                                 │
│     💰 ¥3,500                   │
│                                 │
│  用途：                         │
│  💰 存起来    57%               │
│  🏠 交家里    29%               │
│  🍖 吃顿好的  14%               │
│                                 │
│  @薪日 PayDay                   │
│  记录每一步成长                 │
└─────────────────────────────────┘
```

### 2.2.6 数据模型

```sql
CREATE TABLE salary_usage_records (
  id VARCHAR(36) PRIMARY KEY,
  user_id VARCHAR(36) NOT NULL,
  salary_record_id VARCHAR(36) NOT NULL COMMENT '关联的工资记录',
  usage_category VARCHAR(50) NOT NULL COMMENT '用途分类',
  usage_subcategory VARCHAR(50) COMMENT '子分类',
  amount DECIMAL(10,2) NOT NULL COMMENT '用途金额',
  note TEXT COMMENT '备注',
  is_first_salary TINYINT DEFAULT 1 COMMENT '是否为第一笔工资',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  INDEX idx_user_id (user_id),
  INDEX idx_salary_record_id (salary_record_id),
  INDEX idx_is_first_salary (is_first_salary),
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (salary_record_id) REFERENCES salary_records(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工资用途记录表';
```

**数据库迁移清单**：

**迁移脚本**: `backend/alembic/versions/4_1_002_salary_usage.py`

```python
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    op.create_table(
        'salary_usage_records',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('salary_record_id', sa.String(36), nullable=False),
        sa.Column('usage_category', sa.String(50), nullable=False, comment='用途分类'),
        sa.Column('usage_subcategory', sa.String(50), comment='子分类'),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False, comment='用途金额'),
        sa.Column('note', sa.Text, comment='备注'),
        sa.Column('is_first_salary', sa.Integer, default=1, comment='是否为第一笔工资'),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['salary_record_id'], ['salary_records.id'])
    )

    # 创建索引
    op.create_index('idx_sur_user_id', 'salary_usage_records', ['user_id'])
    op.create_index('idx_sur_salary_record_id', 'salary_usage_records', ['salary_record_id'])
    op.create_index('idx_sur_is_first_salary', 'salary_usage_records', ['is_first_salary'])

def downgrade():
    op.drop_table('salary_usage_records')
```

### 2.2.7 API 接口

```typescript
interface SalaryUsageRecord {
  id: string;
  salaryRecordId: string;
  usageCategory: string;
  usageSubcategory?: string;
  amount: number;
  note?: string;
  isFirstSalary: boolean;
}

// 创建用途记录
POST /api/v1/salary/:recordId/usage
Request Body: {
  usages: Array<{
    usageCategory: string;
    usageSubcategory?: string;
    amount: number;
    note?: string;
  }>
}

Response: {
  "success": true,
  "records": SalaryUsageRecord[]
}

// 获取用途记录
GET /api/v1/salary/:recordId/usage

Response: {
  "records": SalaryUsageRecord[],
  "totalAmount": number
}

// 更新用途记录
PUT /api/v1/salary/usage/:id
Request Body: {
  usageCategory?: string;
  usageSubcategory?: string;
  amount?: number;
  note?: string;
}

// 删除用途记录
DELETE /api/v1/salary/usage/:id

// 获取第一笔工资用途（社区展示）
GET /api/v1/first-salary-usage?limit=20

Response: {
  "records": Array<{
    id: string;
    anonymousName: string;
    salaryAmount: number;
    usages: Array<{
      category: string;
      amount: number;
      percentage: number;
    }>;
    createdAt: string;
  }>,
  "total": number
}
```

### 2.2.8 社区互动

- **「第一笔工资」话题**：社区内自动创建话题 #第一笔工资
- **用途排行榜**：展示最热门的用途分类
- **年代对比**：80后/90后/00后的第一笔工资用途对比

### 2.2.9 验收标准

**功能验收**:
- ✅ 第一笔工资记录后自动弹出用途记录引导
- ✅ 可选择/添加用途分类和金额
- ✅ 金额总和验证（不能超过工资总额）
- ✅ 生成分享卡片
- ✅ 社区展示第一笔工资用途

**技术验收**:
- ✅ 数据库表创建成功
- ✅ CRUD接口正常工作
- ✅ 金额计算准确
- ✅ 分享卡片生成成功

---

## 2.3 每月支出明细

### 2.3.1 功能描述

在工资记录基础上，增加支出明细记录，形成「收入-支出-结余」的完整财务闭环。

### 2.3.2 实现状态分析

**实现状态**: 🔴 未开始

**需要新增**:
- ❌ ExpenseRecord模型
- ❌ 支出记录API（CRUD）
- ❌ 支出统计接口
- ❌ 支出分类预设数据

**预估工作量**: 6人日（后端3人日 + 前端3人日）

**依赖关系**:
- 依赖SalaryRecord模型（已存在）
- 建议在Sprint 4.2实现

### 2.3.3 支出分类体系

| 一级分类 | 二级分类 | 示例 |
|----------|----------|------|
| 🏠 居住 | 房租、水电、物业、网费 | 房租 ¥2000 |
| 🍚 饮食 | 三餐、外卖、聚餐、烟酒 | 外卖 ¥800 |
| 🚌 交通 | 公交、地铁、打车、加油 | 地铁 ¥200 |
| 🛒 购物 | 服装、日用品、数码 | 衣服 ¥500 |
| 💊 医疗 | 看病、买药、体检 | 买药 ¥100 |
| 🎮 娱乐 | 游戏、电影、会员 | 视频会员 ¥25 |
| 📚 学习 | 书籍、课程、培训 | 在线课程 ¥199 |
| 📱 通讯 | 话费、宽带 | 话费 ¥88 |
| 🎁 礼物 | 人情往来、红包 | 红包 ¥500 |
| 💸 还贷 | 信用卡、花呗、房贷 | 信用卡还款 ¥2000 |
| 📂 其他 | 宠物、美容、其他 | - |

### 2.3.4 UI 设计

**支出记录页**（工资记录后的扩展）：
```
┌─────────────────────────────────┐
│  ← 记录支出                     │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│                                 │
│  本月工资收入  ¥8,500           │
│                                 │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│  本月支出                       │
│                                 │
│  🏠 居住         ¥2,000  >      │
│  🍚 饮食         ¥1,500  >      │
│  🚌 交通           ¥300  >      │
│  🛒 购物           ¥800  >      │
│  💸 还贷         ¥2,000  >      │
│                                 │
│  [+ 添加支出]                   │
│                                 │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│  总支出：¥6,600                 │
│  结余：¥1,900                   │
│                                 │
│     [保存]                      │
└─────────────────────────────────┘
```

**支出分类选择器**：
```
┌─────────────────────────────────┐
│  选择支出分类                   │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│  🔍 搜索分类                    │
│                                 │
│  🏠 居住                        │
│  🍚 饮食                        │
│  🚌 交通                        │
│  🛒 购物                        │
│  💊 医疗                        │
│  🎮 娱乐                        │
│  📚 学习                        │
│  📱 通讯                        │
│  🎁 礼物                        │
│  💸 还贷                        │
│  📂 其他                        │
└─────────────────────────────────┘
```

### 2.3.5 数据模型

```sql
CREATE TABLE expense_records (
  id VARCHAR(36) PRIMARY KEY,
  user_id VARCHAR(36) NOT NULL,
  salary_record_id VARCHAR(36) NOT NULL COMMENT '关联的工资记录',
  expense_date DATE NOT NULL COMMENT '支出日期',
  category VARCHAR(50) NOT NULL COMMENT '支出分类',
  subcategory VARCHAR(50) COMMENT '子分类',
  amount DECIMAL(10,2) NOT NULL,
  note TEXT COMMENT '备注',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  INDEX idx_user_id (user_id),
  INDEX idx_salary_record_id (salary_record_id),
  INDEX idx_expense_date (expense_date),
  INDEX idx_category (category),
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (salary_record_id) REFERENCES salary_records(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='支出记录表';
```

### 2.3.6 统计与展示

**支出统计页**：
```
┌─────────────────────────────────┐
│  支出统计                       │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│                                 │
│  本月支出 ¥6,600                │
│  上月支出 ¥6,200  ↑6.5%        │
│                                 │
│  [折线图：近6个月支出趋势]       │
│                                 │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│  支出构成                       │
│                                 │
│  🏠 居住    30%  ¥2,000  ████ │
│  💸 还贷    30%  ¥2,000  ████ │
│  🍚 饮食    23%  ¥1,500  ███  │
│  🛒 购物    12%  ¥800   ██   │
│  🚌 交通     5%  ¥300   █    │
│                                 │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│  收支对比                       │
│                                 │
│  收入  ████████████████ ¥8,500 │
│  支出  ██████████████   ¥6,600 │
│  结余  ██               ¥1,900 │
└─────────────────────────────────┘
```

### 2.3.7 API 接口

```typescript
// 创建支出记录
POST /api/v1/salary/:recordId/expenses
Request Body: {
  expenses: Array<{
    expenseDate: string;    // YYYY-MM-DD
    category: string;
    subcategory?: string;
    amount: number;
    note?: string;
  }>
}

// 获取支出列表
GET /api/v1/salary/:recordId/expenses

// 获取支出统计
GET /api/v1/expenses/statistics
Query: {
  startDate?: string;
  endDate?: string;
  groupBy?: 'category' | 'month';
}

Response: {
  "total": number,
  "byCategory": Array<{
    category: string;
    amount: number;
    percentage: number;
  }>,
  "byMonth": Array<{
    month: string;
    amount: number;
  }>
}

// 更新/删除支出
PUT /api/v1/expenses/:id
DELETE /api/v1/expenses/:id
```

### 2.3.8 验收标准

**功能验收**:
- ✅ 可添加多条支出记录
- ✅ 支出分类选择器可用
- ✅ 计算总支出和结余
- ✅ 支出统计图表展示
- ✅ 收支对比可视化

**技术验收**:
- ✅ 支出数据CRUD正常
- ✅ 统计计算准确
- ✅ 图表渲染正常

---

## 2.4 年终奖展示

### 2.4.1 功能描述

- 专门的「年终奖」工资类型
- 年终奖专题社区话题
- 年终奖排行榜（匿名）

### 2.4.2 实现状态分析

**实现状态**: 🔴 未开始

**已有基础**:
- ✅ Post模型（社区帖子）
- ✅ SalaryRecord模型（salary_type字段已支持扩展）

**需要新增**:
- ❌ SalaryRecord.salary_type 新增 `year_end_bonus` 枚举值
- ❌ 年终奖统计接口
- ❌ 年终奖话题聚合

**预估工作量**: 4人日（后端2人日 + 前端2人日）

**依赖关系**:
- 依赖Post、SalaryRecord模型
- 建议在Sprint 4.2实现

### 2.4.3 工资类型扩展

**现有类型**：normal（正常工资）、bonus（奖金）、allowance（补贴）、other（其他）

**新增类型**：year_end_bonus（年终奖）

**数据库迁移**：
```sql
ALTER TABLE salary_records
MODIFY COLUMN salary_type
ENUM('normal', 'bonus', 'allowance', 'other', 'year_end_bonus');
```

### 2.4.4 社区专题

**「晒年终奖」话题页**：
```
┌─────────────────────────────────┐
│  ← 晒年终奖                     │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│                                 │
│  #晒年终奖                      │
│  3,256 人参与                   │
│                                 │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│                                 │
│  👤 匿名用户_8a3f               │
│  2小时前  #年终奖               │
│  ─────────────────────────      │
│  今年公司效益不错，发了3个月工资 │
│  作为年终奖，开心！             │
│  💬 56  👍 892                 │
│                                 │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│                                 │
│  👤 匿名用户_b2d1               │
│  5小时前  #年终奖               │
│  ─────────────────────────      │
│  说是有年终奖，结果就发了500...  │
│  💬 23  👍 156                 │
│                                 │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│                                 │
│  [我要晒年终奖]                 │
└─────────────────────────────────┘
```

### 2.4.5 年终奖排行榜

**匿名统计排行**：
```
┌─────────────────────────────────┐
│  年终奖排行（匿名）             │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│                                 │
│  🏆 按行业                      │
│                                 │
│  🥇 金融行业     平均 4.2个月   │
│  🥈 互联网       平均 3.5个月   │
│  🥉 制造业       平均 2.8个月   │
│                                 │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│                                 │
│  🏆 按城市                      │
│                                 │
│  🥇 北京         平均 4.0个月   │
│  🥈 上海         平均 3.8个月   │
│  🥉 深圳         平均 3.6个月   │
│                                 │
└─────────────────────────────────┘
```

### 2.4.6 API 接口

```typescript
// 发布年终奖帖子（特殊类型）
POST /api/v1/posts/year-end-bonus
Request Body: {
  content: string;
  months: number;              // 年终奖月数
  images?: string[];
  industry?: string;
  city?: string;
}

// 年终奖统计
GET /api/v1/statistics/year-end-bonus
Response: {
  byIndustry: Array<{
    industry: string;
    averageMonths: number;
    count: number;
  }>;
  byCity: Array<{
    city: string;
    averageMonths: number;
    count: number;
  }>;
  overall: {
    averageMonths: number;
    totalCount: number;
  };
}

// 年终奖话题帖子
GET /api/v1/posts?topic=year_end_bonus
```

### 2.4.7 验收标准

**功能验收**:
- ✅ 工资类型可选择「年终奖」
- ✅ 年终奖帖子带月数标签
- ✅ 年终奖排行榜展示
- ✅ 行业/城市统计准确

---

## 2.5 发薪情绪/延迟记录

### 2.5.1 功能描述

记录发薪相关情绪体验：
- 发薪心情（已存在）
- **新增**：是否延迟发薪
- **新增**：是否拖欠工资
- **新增**：发薪带来的好处/感受

### 2.5.2 实现状态分析

**实现状态**: 🟡 部分实现

**已有基础**:
- ✅ SalaryRecord模型（mood字段已存在）
- ✅ SalaryRecord模型（delayed_days字段已存在 - Sprint 3.3）

**需要新增**:
- ❌ SalaryRecord新增字段：is_arrears, arrears_amount, mood_note, mood_tags
- ❌ 发薪准点率统计接口
- ❌ 心情标签预设数据

**模型变更**:
```diff
# backend/app/models/salary.py (已有delayed_days)
+ is_arrears = Column(Integer, default=0, comment="是否拖欠（0=否，1=是）")
+ arrears_amount = Column(Numeric(10, 2), nullable=True, comment="拖欠金额")
+ mood_note = Column(Text, nullable=True, comment="心情备注")
+ mood_tags = Column(JSON, nullable=True, comment="心情标签")
```

**预估工作量**: 3人日（后端2人日 + 前端1人日）

**依赖关系**:
- 扩展现有SalaryRecord模型
- 建议在Sprint 4.3实现

### 2.5.3 工资记录扩展字段

**数据库迁移**：
```sql
ALTER TABLE salary_records
ADD COLUMN is_arrears TINYINT DEFAULT 0 COMMENT '是否拖欠（0=否，1=是）',
ADD COLUMN arrears_amount DECIMAL(10,2) COMMENT '拖欠金额',
ADD COLUMN mood_note TEXT COMMENT '心情备注（发薪带来的好处/感受）',
ADD COLUMN mood_tags JSON COMMENT '心情标签';
```

### 2.5.4 UI 更新

**工资记录页扩展**：
```
┌─────────────────────────────────┐
│  ← 记工资                       │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│  实发金额    [¥8500]            │
│  发薪日期    [2024-02-10]       │
│  工资类型    [正常工资 ▼]       │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│  本次心情                        │
│  [😊开心] 😌续命 😭崩溃         │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│  [新增] 是否延迟发薪？           │
│  ○ 正常发放                     │
│  ● 延迟了 [5] 天                │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│  [新增] 是否拖欠？               │
│  ○ 无拖欠                       │
│  ● 有拖欠 [¥2000]               │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│  [新增] 这笔工资对你来说？       │
│  (多选)                         │
│  ☑ 可以买买买了                 │
│  ☑ 心里踏实了                   │
│  ☐ 终于可以还花呗了             │
│  ☐ 其他...                      │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│  上传工资条                      │
│  [+ 添加图片]                   │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│     [保存]                      │
└─────────────────────────────────┘
```

### 2.5.5 心情标签预设

**「发薪带来的好处」选项**：
- 💰 可以买买买了
- 😌 心里踏实了
- 💳 可以还花呗/信用卡了
- 🏠 可以交房租了
- 🍖 可以吃顿好的
- 🎉 感觉生活有希望了
- 😐 没什么特别感觉
- 📝 自定义...

### 2.5.6 统计展示

**发薪准点率统计**：
```
┌─────────────────────────────────┐
│  发薪准点率                     │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│                                 │
│  本月准点率  ████████░░  80%    │
│  延迟 2 次，共延迟 5 天         │
│                                 │
│  [折线图：近6个月准点率]        │
│                                 │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│  行业对比（匿名）               │
│                                 │
│  互联网     平均准点率  85%     │
│  制造业     平均准点率  72%     │
│  服务业     平均准点率  68%     │
│                                 │
└─────────────────────────────────┘
```

### 2.5.7 API 接口

```typescript
// 工资记录创建扩展
POST /api/v1/salary/record
Request Body: {
  // ... 现有字段
  isDelayed: boolean;
  delayedDays?: number;
  isArrears: boolean;
  arrearsAmount?: number;
  moodNote?: string;
  moodTags?: string[];        // 心情标签
}

// 发薪准点率统计
GET /api/v1/statistics/punctuality
Response: {
  userPunctuality: {
    onTimeRate: number;      // 准点率
    delayedCount: number;
    totalDelayedDays: number;
    trend: Array<{           // 趋势
      month: string;
      onTimeRate: number;
    }>;
  };
  industryPunctuality: Array<{
    industry: string;
    onTimeRate: number;
  }>;
}
```

### 2.5.8 验收标准

**功能验收**:
- ✅ 可记录延迟发薪情况
- ✅ 可记录拖欠工资情况
- ✅ 可选择心情标签
- ✅ 发薪准点率统计准确

**技术验收**:
- ✅ 数据库迁移成功
- ✅ 统计接口计算准确
- ✅ 图表展示正常

---

## 2.6 存款目标

### 2.6.1 功能描述

设置每月存款目标，追踪储蓄进度，培养理财意识。

### 2.6.2 实现状态分析

**实现状态**: 🔴 未开始

**需要新增**:
- ❌ SavingsGoal模型
- ❌ SavingsRecord模型
- ❌ 存款目标API（CRUD）
- ❌ 存款记录API
- ❌ 存款统计接口

**预估工作量**: 6人日（后端3人日 + 前端3人日）

**依赖关系**:
- 建议在Sprint 4.4实现
- 为能力值系统做铺垫

### 2.6.3 功能流程

```
设置目标
    ↓
输入每月存款目标金额
    ↓
选择目标类型（固定/按比例）
    ↓
从工资中自动扣除计算
    ↓
展示进度和达成情况
```

### 2.6.4 UI 设计

**存款目标设置页**：
```
┌─────────────────────────────────┐
│  ← 存款目标                     │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│                                 │
│  每月存款目标                   │
│                                 │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│  目标金额                        │
│  [¥2,000]                       │
│                                 │
│  目标类型                        │
│  ● 固定金额                     │
│  ○ 工资比例 [20]%              │
│                                 │
│  目标名称                        │
│  [买房基金]                     │
│                                 │
│  目标图片                       │
│  [🏠 选择图标]                  │
│                                 │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│  当前进度                       │
│  已存 ¥12,000 / ¥50,000         │
│  ████████░░░░░░░░  24%         │
│                                 │
│     [保存目标]                  │
└─────────────────────────────────┘
```

**个人中心展示**：
```
┌─────────────────────────────────┐
│  个人中心                       │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│                                 │
│  👤 匿名用户_8a3f               │
│  打工 365 天                    │
│                                 │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│  [本月工资]                     │
│  [工资记录]                     │
│  [存款目标]  🎯                 │
│  [社区]                         │
│  [设置]                         │
└─────────────────────────────────┘
```

### 2.6.5 数据模型

```sql
CREATE TABLE savings_goals (
  id VARCHAR(36) PRIMARY KEY,
  user_id VARCHAR(36) NOT NULL,
  goal_name VARCHAR(100) NOT NULL COMMENT '目标名称',
  target_amount DECIMAL(10,2) NOT NULL COMMENT '目标金额',
  current_amount DECIMAL(10,2) DEFAULT 0 COMMENT '当前金额',
  goal_type ENUM('fixed', 'percentage') DEFAULT 'fixed' COMMENT '目标类型',
  monthly_target DECIMAL(10,2) COMMENT '每月目标金额',
  percentage INT COMMENT '工资比例(当type=percentage)',
  icon VARCHAR(50) COMMENT '目标图标',
  is_active TINYINT DEFAULT 1 COMMENT '是否启用',
  achieved_at TIMESTAMP NULL COMMENT '达成时间',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  INDEX idx_user_id (user_id),
  INDEX idx_is_active (is_active),
  FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='存款目标表';

CREATE TABLE savings_records (
  id VARCHAR(36) PRIMARY KEY,
  user_id VARCHAR(36) NOT NULL,
  goal_id VARCHAR(36) NOT NULL COMMENT '关联目标',
  salary_record_id VARCHAR(36) COMMENT '关联工资记录',
  amount DECIMAL(10,2) NOT NULL COMMENT '存款金额',
  record_date DATE NOT NULL COMMENT '记录日期',
  note TEXT COMMENT '备注',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  INDEX idx_user_id (user_id),
  INDEX idx_goal_id (goal_id),
  INDEX idx_record_date (record_date),
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (goal_id) REFERENCES savings_goals(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='存款记录表';
```

### 2.6.6 API 接口

```typescript
// 创建目标
POST /api/v1/savings/goals
Request Body: {
  goalName: string;
  targetAmount: number;
  goalType: 'fixed' | 'percentage';
  monthlyTarget?: number;
  percentage?: number;
  icon?: string;
}

// 获取目标列表
GET /api/v1/savings/goals

// 更新目标
PUT /api/v1/savings/goals/:id

// 记录存款
POST /api/v1/savings/records
Request Body: {
  goalId: string;
  salaryRecordId?: string;
  amount: number;
  note?: string;
}

// 获取存款记录
GET /api/v1/savings/records?goalId=xxx

// 目标统计
GET /api/v1/savings/statistics
Response: {
  totalGoals: number;
  achievedGoals: number;
  totalSaved: number;
  monthlyProgress: Array<{
    month: string;
    target: number;
    actual: number;
  }>;
}
```

### 2.6.7 验收标准

**功能验收**:
- ✅ 可创建存款目标
- ✅ 可记录存款
- ✅ 进度计算准确
- ✅ 目标达成提示

---

## 2.7 打卡功能

### 2.7.1 功能描述

用户日常打卡功能，包括：
- 加班打卡
- 发薪日打卡
- 存款打卡
- 自定义打卡

### 2.7.2 实现状态分析

**实现状态**: 🟢 已完成

**已有基础**:
- ✅ CheckIn模型 (backend/app/models/checkin.py)
- ✅ 打卡API已实现
- ✅ 小程序打卡页面已实现

**无需新增开发**

### 2.7.3 打卡类型

| 打卡类型 | 触发条件 | 奖励 |
|----------|----------|------|
| 加班打卡 | 记录加班时间 | 能力值+5 |
| 发薪打卡 | 发薪日打卡 | 能力值+10 |
| 存款打卡 | 完成存款目标 | 能力值+20 |
| 连续打卡 | 连续N天 | 能力值+N*2 |

---

## 2.8 能力值系统

### 2.8.1 功能描述

建立用户能力值（成长值）体系，关联多模块，提升用户活跃度和粘性。

### 2.8.2 实现状态分析

**实现状态**: 🔴 未开始

**需要新增**:
- ❌ User模型扩展：ability_points, ability_level, ability_level_updated_at
- ❌ AbilityPointsLog模型
- ❌ 能力值服务层（获取规则、升级逻辑）
- ❌ 能力值统计接口
- ❌ 能力值排行榜

**预估工作量**: 8人日（后端5人日 + 前端3人日）

**依赖关系**:
- 需要User模型扩展
- 关联打卡、工资、社区等多个模块
- 建议在Sprint 4.5实现

### 2.8.3 能力值获取规则

| 行为 | 能力值 | 上限/周期 |
|------|--------|-----------|
| 每日登录 | +1 | 1次/天 |
| 记工资 | +10 | 无上限 |
| 记支出 | +5 | 无上限 |
| 发布帖子 | +20 | 10次/天 |
| 评论 | +5 | 20次/天 |
| 点赞 | +1 | 50次/天 |
| 被点赞 | +2 | 无上限 |
| 被关注 | +10 | 无上限 |
| 打卡 | +5 | 3次/天 |
| 完成存款目标 | +50 | 无上限 |
| 邀请好友 | +100 | 10人 |

### 2.8.4 能力值等级

| 等级 | 名称 | 能力值范围 | 特权 |
|------|------|------------|------|
| 1 | 职场新人 | 0-99 | 基础功能 |
| 2 | 打工小白 | 100-499 | 发帖+表情 |
| 3 | 熟练工 | 500-999 | 自定义头像 |
| 4 | 职场老手 | 1000-2999 | 优先展示 |
| 5 | 打工皇帝 | 3000+ | 独家勋章、专属客服 |

### 2.8.5 UI 设计

**能力值展示**（个人中心）：
```
┌─────────────────────────────────┐
│  👤 匿名用户_8a3f               │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│                                 │
│     🏆 熟练工                   │
│     能力值 1,280 / 3,000        │
│     ████████░░░░░░  43%        │
│                                 │
│     [查看详情]                  │
│                                 │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│  今日获取能力值                 │
│  ✅ 登录       +1               │
│  ✅ 记工资     +10              │
│  ⬜ 发布帖子   +20              │
│  ⬜ 打卡       +5               │
│                                 │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│  能力值商城                     │
│  🎁 实物兑换                   │
│                                 │
└─────────────────────────────────┘
```

**能力值明细页**：
```
┌─────────────────────────────────┐
│  ← 能力值明细                   │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│                                 │
│  当前能力值：1,280              │
│  距下一等级：1,720              │
│                                 │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│  获取记录                       │
│  2024-02-20                    │
│  ✅ 记工资       +10            │
│  ✅ 登录         +1             │
│  ✅ 被点赞       +4 (x2)        │
│  ─────────────────────────      │
│  今日合计：+15                  │
│                                 │
│  2024-02-19                    │
│  ✅ 发布帖子     +20            │
│  ✅ 评论         +5             │
│  ✅ 打卡         +5             │
│  ─────────────────────────      │
│  昨日合计：+30                  │
│                                 │
└─────────────────────────────────┘
```

### 2.8.6 数据模型

```sql
-- 用户表扩展
ALTER TABLE users
ADD COLUMN ability_points INT DEFAULT 0 COMMENT '能力值',
ADD COLUMN ability_level INT DEFAULT 1 COMMENT '能力等级',
ADD COLUMN ability_level_updated_at TIMESTAMP NULL COMMENT '等级更新时间',
ADD INDEX idx_ability_points (ability_points);

CREATE TABLE ability_points_logs (
  id VARCHAR(36) PRIMARY KEY,
  user_id VARCHAR(36) NOT NULL,
  points_change INT NOT NULL COMMENT '能力值变化（正负）',
  action_type VARCHAR(50) NOT NULL COMMENT '行为类型',
  target_id VARCHAR(36) COMMENT '关联内容ID',
  description VARCHAR(200) COMMENT '描述',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  INDEX idx_user_id (user_id),
  INDEX idx_created_at (created_at),
  FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='能力值日志表';
```

### 2.8.7 API 接口

```typescript
// 获取能力值统计
GET /api/v1/user/ability-points
Response: {
  currentPoints: number;
  level: number;
  levelName: string;
  nextLevelPoints: number;
  progress: number;           // 0-100
  todayGained: number;
  todayActions: Array<{
    type: string;
    points: number;
    completed: boolean;
  }>;
}

// 获取能力值日志
GET /api/v1/user/ability-points/logs
Query: {
  limit?: number;
  offset?: number;
}

// 能力值排行榜
GET /api/v1/leaderboard/ability-points
Query: {
  type?: 'daily' | 'weekly' | 'monthly' | 'total';
}

Response: {
  leaderboard: Array<{
    rank: number;
    anonymousName: string;
    level: number;
    points: number;
  }>;
  myRank?: {
    rank: number;
    points: number;
  };
}
```

### 2.8.8 验收标准

**功能验收**:
- ✅ 各行为能正确获取能力值
- ✅ 能力值等级自动升级
- ✅ 能力值日志记录完整
- ✅ 排行榜实时更新

**技术验收**:
- ✅ 能力值计算准确
- ✅ 并发场景下数据一致性
- ✅ 排行榜性能优化（缓存）

---

## 2.9 能力值兑换

### 2.9.1 功能描述

使用能力值兑换实物奖励，提升能力值的价值感和用户参与度。

### 2.9.2 实现状态分析

**实现状态**: 🔴 未开始

**需要新增**:
- ❌ RewardItem模型（奖励物品）
- ❌ RewardOrder模型（兑换订单）
- ❌ 兑换API（下单、查询、取消）
- ❌ 管理后台奖励管理

**预估工作量**: 10人日（后端5人日 + 前端3人日 + 管理后台2人日）

**依赖关系**:
- 依赖能力值系统
- 需要运营配置奖励物品
- 建议在Sprint 4.5实现

### 2.9.3 兑换物分类

| 分类 | 兑换物 | 所需能力值 |
|------|--------|-----------|
| 🎁 节假日礼包 | 春节礼包 | 2000 |
| 🎁 节假日礼包 | 中秋礼包 | 1500 |
| 🎁 节假日礼包 | 端午礼包 | 1000 |
| 🛒 超市卡 | 50元超市卡 | 500 |
| 🛒 超市卡 | 100元超市卡 | 1000 |
| 🛒 超市卡 | 200元超市卡 | 2000 |
| 🧤 劳保用品 | 防护口罩 | 300 |
| 🧤 劳保用品 | 劳保手套 | 200 |
| 🧤 劳保用品 | 保温杯 | 800 |
| 🎮 虚拟物品 | 专属头像框 | 500 |
| 🎮 虚拟物品 | 个性昵称颜色 | 300 |
| 🎮 虚拟物品 | 独家勋章 | 1000 |

### 2.9.4 UI 设计

**能力值商城**：
```
┌─────────────────────────────────┐
│  能力值商城                     │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│                                 │
│  我的余额：1,280 能力值         │
│                                 │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│  [全部] [礼包] [超市卡] [劳保]  │
│                                 │
│  ┌───────────────────────────┐  │
│  │ 🎁 春节礼包               │  │
│  │                           │  │
│  │ 包含：坚果、零食、礼盒    │  │
│  │                           │  │
│  │ 库存：156 份              │  │
│  │                           │  │
│  │ 💰 2000 能力值            │  │
│  │                           │  │
│  │     [立即兑换]             │  │
│  └───────────────────────────┘  │
│                                 │
│  ┌───────────────────────────┐  │
│  │ 🛒 100元超市卡            │  │
│  │                           │  │
│  │ 通用超市购物卡            │  │
│  │                           │  │
│  │ 库存：89 张               │  │
│  │                           │  │
│  │ 💰 1000 能力值            │  │
│  │                           │  │
│  │     [立即兑换]             │  │
│  └───────────────────────────┘  │
│                                 │
└─────────────────────────────────┘
```

**兑换成功页**：
```
┌─────────────────────────────────┐
│                                 │
│       🎉 兑换成功！             │
│                                 │
│      您的礼包将在3个工作日内     │
│      安排发货                   │
│                                 │
│  快递信息将发送到您的消息       │
│                                 │
│       [查看订单]  [继续逛]      │
│                                 │
└─────────────────────────────────┘
```

### 2.9.5 数据模型

```sql
CREATE TABLE reward_items (
  id VARCHAR(36) PRIMARY KEY,
  name VARCHAR(100) NOT NULL COMMENT '奖励名称',
  category VARCHAR(50) NOT NULL COMMENT '分类',
  description TEXT COMMENT '描述',
  image_url VARCHAR(255) COMMENT '图片',
  points_cost INT NOT NULL COMMENT '所需能力值',
  stock_count INT DEFAULT 0 COMMENT '库存',
  is_active TINYINT DEFAULT 1 COMMENT '是否上架',
  sort_order INT DEFAULT 0 COMMENT '排序',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  INDEX idx_category (category),
  INDEX idx_is_active (is_active),
  INDEX idx_sort_order (sort_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='奖励物品表';

CREATE TABLE reward_orders (
  id VARCHAR(36) PRIMARY KEY,
  user_id VARCHAR(36) NOT NULL,
  reward_item_id VARCHAR(36) NOT NULL,
  points_used INT NOT NULL COMMENT '使用的能力值',
  status ENUM('pending', 'processing', 'shipped', 'completed', 'cancelled') DEFAULT 'pending',
  shipping_info JSON COMMENT '物流信息',
  shipping_name VARCHAR(100) COMMENT '收货人',
  shipping_phone VARCHAR(20) COMMENT '收货电话',
  shipping_address TEXT COMMENT '收货地址',
  note TEXT COMMENT '备注',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  INDEX idx_user_id (user_id),
  INDEX idx_status (status),
  INDEX idx_created_at (created_at),
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (reward_item_id) REFERENCES reward_items(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='奖励订单表';
```

### 2.9.6 兑换流程

```
用户选择兑换物品
    ↓
检查能力值是否足够
    ↓
填写收货地址
    ↓
确认兑换
    ↓
扣除能力值
    ↓
创建订单（status=pending）
    ↓
运营处理订单
    ↓
发货（status=shipped）
    ↓
用户确认收货（status=completed）
```

### 2.9.7 API 接口

```typescript
// 获取商城物品列表
GET /api/v1/reward/items
Query: {
  category?: string;
  page?: number;
  pageSize?: number;
}

// 获取物品详情
GET /api/v1/reward/items/:id

// 兑换物品
POST /api/v1/reward/orders
Request Body: {
  rewardItemId: string;
  shippingName: string;
  shippingPhone: string;
  shippingAddress: string;
  note?: string;
}

Response: {
  "success": true,
  "orderId": string,
  "pointsRemaining": number
}

// 获取我的订单
GET /api/v1/reward/orders
Query: {
  status?: string;
  page?: number;
}

// 获取订单详情
GET /api/v1/reward/orders/:id

// 取消订单
POST /api/v1/reward/orders/:id/cancel

// 确认收货
POST /api/v1/reward/orders/:id/confirm
```

### 2.9.8 验收标准

**功能验收**:
- ✅ 可浏览商城物品
- ✅ 能力值不足时无法兑换
- ✅ 兑换成功扣除能力值
- ✅ 订单状态流转正确
- ✅ 库存扣减准确

**技术验收****
- ✅ 能力值扣减事务一致性
- ✅ 库存并发安全
- ✅ 订单状态机正确

---

# 三、数据库变更汇总

## 3.1 表结构变更总览

| 表名 | 操作类型 | 说明 | 风险等级 |
|------|----------|------|----------|
| users | ALTER | 添加phone_number, phone_verified, ability_points, ability_level | 🟢 低 |
| salary_records | ALTER | 添加is_arrears, arrears_amount, mood_note, mood_tags; 修改salary_type枚举 | 🟡 中 |
| salary_usage_records | CREATE | 新建工资用途记录表 | 🟢 低 |
| expense_records | CREATE | 新建支出记录表 | 🟢 低 |
| savings_goals | CREATE | 新建存款目标表 | 🟢 低 |
| savings_records | CREATE | 新建存款记录表 | 🟢 低 |
| ability_points_logs | CREATE | 新建能力值日志表 | 🟢 低 |
| reward_items | CREATE | 新建奖励物品表 | 🟢 低 |
| reward_orders | CREATE | 新建奖励订单表 | 🟢 低 |

## 3.2 迁移脚本清单

| 迁移脚本 | 描述 | 依赖 | 执行顺序 |
|---------|------|------|----------|
| 4_1_001_phone_login.py | 手机号登录字段 | 无 | 1 |
| 4_1_002_salary_usage.py | 工资用途表 | 无 | 2 |
| 4_2_001_expense_records.py | 支出记录表 | 无 | 3 |
| 4_2_002_year_end_bonus.py | 年终奖枚举 | salary_records表 | 4 |
| 4_3_001_arrears_mood.py | 拖欠/心情字段 | salary_records表 | 5 |
| 4_4_001_savings_goals.py | 存款目标表 | 无 | 6 |
| 4_4_002_savings_records.py | 存款记录表 | savings_goals表 | 7 |
| 4_5_001_ability_points.py | 能力值字段 | users表 | 8 |
| 4_5_002_ability_logs.py | 能力值日志表 | users表 | 9 |
| 4_5_003_reward_items.py | 奖励物品表 | 无 | 10 |
| 4_5_004_reward_orders.py | 奖励订单表 | users表, reward_items表 | 11 |

**执行方式**：
```bash
cd backend
alembic upgrade head  # 执行所有迁移
alembic downgrade -1  # 回滚最后一个迁移
```

---

# 四、API 接口汇总

## 4.1 API变更总览

| 分类 | 数量 | 说明 |
|------|------|------|
| 🔴 新增端点 | 47个 | 全新的API接口 |
| 🟡 修改端点 | 3个 | 现有接口扩展参数或返回值 |
| 🟢 不变端点 | - | 现有接口保持兼容 |

## 4.2 修改的API端点

### POST /api/v1/auth/login

**现有签名**：
```typescript
{
  "code": string  // 微信登录code
}
```

**修改后签名**：
```typescript
{
  "code": string,
  "phoneNumberCode"?: string  // 新增：手机号授权code
}
```

**向后兼容性**: ✅ 兼容（phoneNumberCode为可选参数）

**响应变更**：
```typescript
{
  "access_token": string,
  "user": {
    // ... 现有字段
    "phoneNumber"?: string,      // 新增
    "phoneVerified": boolean     // 新增
  }
}
```

### POST /api/v1/salary/record

**新增字段**：
```typescript
{
  // ... 现有字段
  "isArrears": boolean,
  "arrearsAmount"?: number,
  "moodNote"?: string,
  "moodTags"?: string[]
}
```

### Enum: salary_records.salary_type

**新增枚举值**：
```typescript
type SalaryType = 'normal' | 'bonus' | 'allowance' | 'other' | 'year_end_bonus';
//                                                                          ↑ 新增
```

## 4.3 新增API端点列表

### 手机号登录（3个端点）
```
POST /api/v1/user/bind-phone          # 绑定手机号
POST /api/v1/user/change-phone        # 更换手机号
GET  /api/v1/user/phone-status        # 查询手机号状态
```

### 工资用途（5个端点）
```
POST /api/v1/salary/:recordId/usage           # 创建用途记录
GET  /api/v1/salary/:recordId/usage            # 获取用途记录
PUT  /api/v1/salary/usage/:id                  # 更新用途
DELETE /api/v1/salary/usage/:id                # 删除用途
GET  /api/v1/first-salary-usage                # 社区展示
```

### 支出记录（5个端点）
```
POST /api/v1/salary/:recordId/expenses         # 创建支出记录
GET  /api/v1/salary/:recordId/expenses         # 获取支出列表
GET  /api/v1/expenses/statistics               # 支出统计
PUT  /api/v1/expenses/:id                      # 更新支出
DELETE /api/v1/expenses/:id                    # 删除支出
```

### 年终奖（3个端点）
```
POST /api/v1/posts/year-end-bonus              # 发布年终奖帖子
GET  /api/v1/statistics/year-end-bonus         # 年终奖统计
GET  /api/v1/posts?topic=year_end_bonus        # 年终奖话题帖子
```

### 发薪准点率（1个端点）
```
GET  /api/v1/statistics/punctuality            # 发薪准点率统计
```

### 存款目标（5个端点）
```
POST /api/v1/savings/goals                     # 创建目标
GET  /api/v1/savings/goals                     # 获取目标列表
PUT  /api/v1/savings/goals/:id                 # 更新目标
POST /api/v1/savings/records                   # 记录存款
GET  /api/v1/savings/records?goalId=xxx        # 获取存款记录
GET  /api/v1/savings/statistics                 # 目标统计
```

### 能力值（3个端点）
```
GET  /api/v1/user/ability-points               # 能力值统计
GET  /api/v1/user/ability-points/logs          # 能力值日志
GET  /api/v1/leaderboard/ability-points        # 能力值排行榜
```

### 能力值兑换（7个端点）
```
GET  /api/v1/reward/items                      # 商城物品列表
GET  /api/v1/reward/items/:id                  # 物品详情
POST /api/v1/reward/orders                     # 兑换物品
GET  /api/v1/reward/orders                     # 我的订单
GET  /api/v1/reward/orders/:id                 # 订单详情
POST /api/v1/reward/orders/:id/cancel          # 取消订单
POST /api/v1/reward/orders/:id/confirm         # 确认收货
```

---

# 五、Sprint任务分解

## 5.1 Sprint 4.1：基础能力（Week 1-2）

**目标**: 手机号登录 + 工资用途记录

### 后端任务

#### T-4.1.1: 手机号登录接口 (2人日)
- [ ] 修改`POST /api/v1/auth/login`支持phoneNumberCode参数
- [ ] 实现`POST /api/v1/user/bind-phone`绑定逻辑
- [ ] 实现`POST /api/v1/user/change-phone`更换逻辑
- [ ] 实现`GET /api/v1/user/phone-status`查询接口
- [ ] 手机号加密存储（使用`app/utils/encryption.py`）
- [ ] **验收**: 可通过手机号登录，返回脱敏手机号
- [ ] **依赖**: T-4.1.2

#### T-4.1.2: 用户模型扩展 (0.5人日)
- [ ] 添加`phone_number`, `phone_verified`字段到User模型
- [ ] 编写Alembic迁移脚本`4_1_001_phone_login.py`
- [ ] 添加数据库索引
- [ ] **验收**: 迁移成功，数据完整性检查通过
- [ ] **依赖**: 无

#### T-4.1.3: 工资用途记录CRUD (3人日)
- [ ] 创建SalaryUsageRecord模型
- [ ] 编写迁移脚本`4_1_002_salary_usage.py`
- [ ] 实现`POST /api/v1/salary/:recordId/usage`
- [ ] 实现`GET /api/v1/salary/:recordId/usage`
- [ ] 实现`PUT /api/v1/salary/usage/:id`
- [ ] 实现`DELETE /api/v1/salary/usage/:id`
- [ ] 实现`GET /api/v1/first-salary-usage`社区展示
- [ ] **验收**: 可记录、查询、统计工资用途
- [ ] **依赖**: T-4.1.2

### 前端任务（小程序）

#### T-4.1.4: 登录页手机号授权 (1人日)
- [ ] 添加手机号授权按钮
- [ ] 实现授权流程（使用`<button open-type="getPhoneNumber">`）
- [ ] 处理拒绝授权降级场景
- [ ] 手机号脱敏显示
- [ ] **验收**: 用户可选择授权手机号或拒绝
- [ ] **依赖**: T-4.1.1

#### T-4.1.5: 工资用途记录页 (2人日)
- [ ] 创建用途记录页面
- [ ] 实现用途分类选择器
- [ ] 实现金额输入和验证
- [ ] 生成分享卡片（canvas绘制）
- [ ] **验收**: 可记录用途并生成分享卡
- [ ] **依赖**: T-4.1.3

### 测试任务

#### T-4.1.6: 手机号登录测试 (0.5人日)
- [ ] 授权成功场景测试
- [ ] 拒绝授权降级测试
- [ ] 手机号已存在绑定测试
- [ ] 手机号加密/脱敏验证

#### T-4.1.7: 工资用途测试 (0.5人日)
- [ ] 用途记录CRUD测试
- [ ] 金额总和验证测试
- [ ] 分享卡片生成测试

### Sprint 4.1交付物
- ✅ 用户可使用手机号登录
- ✅ 第一笔工资可记录用途
- ✅ 数据库迁移脚本已执行

### Sprint 4.1风险与阻塞
- ⚠️ 微信手机号授权需要企业认证（需确认）

---

## 5.2 Sprint 4.2：支出与年终奖（Week 3-4）

**目标**: 每月支出明细 + 年终奖展示

### 后端任务

#### T-4.2.1: 支出记录CRUD (3人日)
- [ ] 创建ExpenseRecord模型
- [ ] 编写迁移脚本`4_2_001_expense_records.py`
- [ ] 实现`POST /api/v1/salary/:recordId/expenses`
- [ ] 实现`GET /api/v1/salary/:recordId/expenses`
- [ ] 实现`GET /api/v1/expenses/statistics`
- [ ] 实现`PUT /api/v1/expenses/:id`
- [ ] 实现`DELETE /api/v1/expenses/:id`
- [ ] **验收**: 支出记录和统计功能正常

#### T-4.2.2: 年终奖类型支持 (1人日)
- [ ] 修改salary_type枚举，添加`year_end_bonus`
- [ ] 编写迁移脚本`4_2_002_year_end_bonus.py`
- [ ] **验收**: 工资类型可选择年终奖

#### T-4.2.3: 年终奖统计接口 (2人日)
- [ ] 实现`POST /api/v1/posts/year-end-bonus`
- [ ] 实现`GET /api/v1/statistics/year-end-bonus`
- [ ] 按行业/城市统计平均月数
- [ ] **验收**: 年终奖统计数据准确

### 前端任务（小程序）

#### T-4.2.4: 支出记录页 (2人日)
- [ ] 创建支出记录页面
- [ ] 实现支出分类选择器
- [ ] 实现多条支出添加
- [ ] 计算总支出和结余
- [ ] **验收**: 可记录支出并查看结余

#### T-4.2.5: 支出统计页 (1.5人日)
- [ ] 创建支出统计页面
- [ ] 集成ECharts展示趋势图
- [ ] 支出构成饼图
- [ ] 收支对比图
- [ ] **验收**: 图表展示正确

#### T-4.2.6: 年终奖专题页 (1.5人日)
- [ ] 创建年终奖话题页
- [ ] 年终奖帖子展示（带月数标签）
- [ ] 年终奖排行榜（按行业/城市）
- [ ] **验收**: 年终奖专题功能完整

### Sprint 4.2交付物
- ✅ 可记录每月支出明细
- ✅ 支出统计可视化
- ✅ 年终奖专题社区

---

## 5.3 Sprint 4.3：情绪与延迟（Week 5-6）

**目标**: 发薪情绪扩展 + 延迟/拖欠记录 + 准点率统计

### 后端任务

#### T-4.3.1: 工资记录情绪扩展 (2人日)
- [ ] 添加字段：`is_arrears`, `arrears_amount`, `mood_note`, `mood_tags`
- [ ] 编写迁移脚本`4_3_001_arrears_mood.py`
- [ ] 修改`POST /api/v1/salary/record`接口
- [ ] **验收**: 可记录延迟、拖欠、心情标签

#### T-4.3.2: 发薪准点率统计 (2人日)
- [ ] 实现`GET /api/v1/statistics/punctuality`
- [ ] 计算用户准点率
- [ ] 计算行业平均准点率（匿名）
- [ ] 准点率趋势数据
- [ ] **验收**: 统计数据准确

### 前端任务（小程序）

#### T-4.3.3: 记工资页扩展 (1.5人日)
- [ ] 添加延迟发薪选项
- [ ] 添加拖欠选项
- [ ] 添加心情标签多选
- [ ] **验收**: 记工资页功能完整

#### T-4.3.4: 准点率统计页 (1.5人日)
- [ ] 创建准点率统计页面
- [ ] 准点率进度条
- [ ] 趋势折线图
- [ ] 行业对比
- [ ] **验收**: 准点率数据可视化

### Sprint 4.3交付物
- ✅ 可记录发薪延迟/拖欠
- ✅ 可记录心情标签
- ✅ 发薪准点率统计

---

## 5.4 Sprint 4.4：目标与打卡（Week 7-8）

**目标**: 存款目标 + 打卡功能验证

### 后端任务

#### T-4.4.1: 存款目标CRUD (3人日)
- [ ] 创建SavingsGoal、SavingsRecord模型
- [ ] 编写迁移脚本`4_4_001_savings_goals.py`、`4_4_002_savings_records.py`
- [ ] 实现`POST /api/v1/savings/goals`
- [ ] 实现`GET /api/v1/savings/goals`
- [ ] 实现`PUT /api/v1/savings/goals/:id`
- [ ] 实现`POST /api/v1/savings/records`
- [ ] 实现`GET /api/v1/savings/records`
- [ ] **验收**: 存款目标和记录功能正常

#### T-4.4.2: 存款统计接口 (1人日)
- [ ] 实现`GET /api/v1/savings/statistics`
- [ ] 计算达成率
- [ ] 月度进度数据
- [ ] **验收**: 统计数据准确

### 前端任务（小程序）

#### T-4.4.3: 存款目标设置页 (2人日)
- [ ] 创建目标设置页面
- [ ] 目标类型选择（固定/按比例）
- [ ] 目标图标选择
- [ ] 进度展示
- [ ] **验收**: 可创建和查看存款目标

#### T-4.4.4: 打卡功能验证 (1人日)
- [ ] 验证现有打卡功能
- [ ] 与能力值系统集成准备
- [ ] **验收**: 打卡功能正常

### Sprint 4.4交付物
- ✅ 可设置存款目标
- ✅ 可记录存款
- ✅ 存款进度可视化

---

## 5.5 Sprint 4.5：兑换体系（Week 9-10）

**目标**: 能力值系统 + 能力值商城

### 后端任务

#### T-4.5.1: 能力值基础 (3人日)
- [ ] User模型添加`ability_points`, `ability_level`, `ability_level_updated_at`
- [ ] 创建AbilityPointsLog模型
- [ ] 编写迁移脚本`4_5_001_ability_points.py`、`4_5_002_ability_logs.py`
- [ ] 实现能力值服务层（获取规则、升级逻辑）
- [ ] **验收**: 能力值计算正确

#### T-4.5.2: 能力值接口 (2人日)
- [ ] 实现`GET /api/v1/user/ability-points`
- [ ] 实现`GET /api/v1/user/ability-points/logs`
- [ ] 实现`GET /api/v1/leaderboard/ability-points`
- [ ] 排行榜缓存优化
- [ ] **验收**: 能力值接口正常

#### T-4.5.3: 奖励兑换CRUD (3人日)
- [ ] 创建RewardItem、RewardOrder模型
- [ ] 编写迁移脚本`4_5_003_reward_items.py`、`4_5_004_reward_orders.py`
- [ ] 实现`GET /api/v1/reward/items`
- [ ] 实现`POST /api/v1/reward/orders`（事务：扣能力值+扣库存）
- [ ] 实现`GET /api/v1/reward/orders`
- [ ] 实现`POST /api/v1/reward/orders/:id/cancel`
- [ ] 实现`POST /api/v1/reward/orders/:id/confirm`
- [ ] **验收**: 兑换流程完整

### 前端任务（小程序）

#### T-4.5.4: 能力值展示 (1.5人日)
- [ ] 个人中心显示能力值和等级
- [ ] 能力值明细页
- [ ] 获取记录列表
- [ ] **验收**: 能力值展示完整

#### T-4.5.5: 能力值商城 (2人日)
- [ ] 创建商城页面
- [ ] 物品列表和筛选
- [ ] 兑换确认页
- [ ] 我的订单页
- [ ] **验收**: 商城功能完整

### 管理后台任务

#### T-4.5.6: 奖励管理 (2人日)
- [ ] 奖励物品CRUD
- [ ] 库存管理
- [ ] 订单管理
- [ ] 发货处理
- [ ] **验收**: 后台可管理奖励和订单

### Sprint 4.5交付物
- ✅ 能力值系统完整
- ✅ 能力值商城可用
- ✅ 管理后台可运营

---

## 5.6 Sprint 4.6：测试与上线（Week 11-12）

**目标**: 集成测试 + 性能优化 + 上线准备

### 测试任务

#### T-4.6.1: 集成测试 (3人日)
- [ ] 端到端功能测试
- [ ] 数据一致性测试
- [ ] 并发场景测试
- [ ] 兼容性测试

#### T-4.6.2: 性能测试 (2人日)
- [ ] API性能测试
- [ ] 数据库查询优化
- [ ] 缓存策略验证
- [ ] 压力测试

#### T-4.6.3: 安全测试 (1人日)
- [ ] 手机号加密验证
- [ ] API权限测试
- [ ] SQL注入测试
- [ ] XSS测试

### 上线准备

#### T-4.6.4: 数据库迁移准备 (1人日)
- [ ] 生产环境迁移脚本准备
- [ ] 回滚方案准备
- [ ] 数据备份

#### T-4.6.5: 小程序提审 (1人日)
- [ ] 小程序功能自查
- [ ] 隐私协议更新
- [ ] 提交审核

### Sprint 4.6交付物
- ✅ 集成测试通过
- ✅ 性能达标
- ✅ 安全测试通过
- ✅ 上线准备完成

---

# 六、实现追踪矩阵

## 6.1 功能模块追踪表

| ID | 功能模块 | 优先级 | 状态 | Sprint | 开始日期 | 完成日期 | 进度 | 阻塞 |
|----|---------|--------|------|--------|----------|----------|------|------|
| F-4.1 | 手机号登录 | P0 | 🔴 未开始 | 4.1 | - | - | 0% | - |
| F-4.2 | 工资用途记录 | P1 | 🔴 未开始 | 4.1 | - | - | 0% | - |
| F-4.3 | 每月支出明细 | P1 | 🔴 未开始 | 4.2 | - | - | 0% | - |
| F-4.4 | 年终奖展示 | P1 | 🔴 未开始 | 4.2 | - | - | 0% | - |
| F-4.5 | 发薪情绪/延迟 | P1 | 🔴 未开始 | 4.3 | - | - | 0% | - |
| F-4.6 | 存款目标 | P2 | 🔴 未开始 | 4.4 | - | - | 0% | - |
| F-4.7 | 打卡功能 | P2 | 🟢 已完成 | 4.4 | - | - | 100% | - |
| F-4.8 | 能力值系统 | P2 | 🔴 未开始 | 4.5 | - | - | 0% | - |
| F-4.9 | 能力值兑换 | P2 | 🔴 未开始 | 4.5 | - | - | 0% | - |

**状态图例：**
- 🟢 已完成
- 🟡 开发中
- 🔴 未开始
- ⚪ 已取消

## 6.2 技术任务追踪表（Sprint 4.1）

| ID | 任务类型 | 所属功能 | 描述 | 状态 | 指派 | 工时估算 |
|----|---------|---------|------|------|------|----------|
| T-4.1.1 | API | 手机号登录 | 修改登录接口支持手机号 | 🔴 未开始 | - | 2d |
| T-4.1.2 | Model | 手机号登录 | User模型添加字段 | 🔴 未开始 | - | 0.5d |
| T-4.1.3 | API | 工资用途 | 工资用途记录CRUD | 🔴 未开始 | - | 3d |
| T-4.1.4 | UI-小程序 | 手机号登录 | 登录页手机号授权 | 🔴 未开始 | - | 1d |
| T-4.1.5 | UI-小程序 | 工资用途 | 工资用途记录页 | 🔴 未开始 | - | 2d |
| T-4.1.6 | Test | 手机号登录 | 手机号登录测试 | 🔴 未开始 | - | 0.5d |
| T-4.1.7 | Test | 工资用途 | 工资用途测试 | 🔴 未开始 | - | 0.5d |

**Sprint 4.1总工时**: 后端5.5人日 + 前端3人日 + 测试1人日 = **9.5人日**

## 6.3 Sprint进度看板

### Sprint 4.1 (Week 1-2)
```
待开始 (7)  |  进行中 (0)  |  已完成 (0)  |  已验收 (0)
  🔴🔴🔴🔴🔴🔴🔴

进度: 0% | 预计完成: 2024-03-05 | 状态: ⏳ 未开始
```

### Sprint 4.2 (Week 3-4)
```
待开始 (6)  |  进行中 (0)  |  已完成 (0)  |  已验收 (0)
  🔴🔴🔴🔴🔴🔴

进度: 0% | 预计完成: 2024-03-19 | 状态: ⏳ 未开始
```

### Sprint 4.3 (Week 5-6)
```
待开始 (4)  |  进行中 (0)  |  已完成 (0)  |  已验收 (0)
  🔴🔴🔴🔴

进度: 0% | 预计完成: 2024-04-02 | 状态: ⏳ 未开始
```

### Sprint 4.4 (Week 7-8)
```
待开始 (4)  |  进行中 (0)  |  已完成 (0)  |  已验收 (0)
  🔴🔴🔴🔴

进度: 0% | 预计完成: 2024-04-16 | 状态: ⏳ 未开始
```

### Sprint 4.5 (Week 9-10)
```
待开始 (6)  |  进行中 (0)  |  已完成 (0)  |  已验收 (0)
  🔴🔴🔴🔴🔴🔴

进度: 0% | 预计完成: 2024-04-30 | 状态: ⏳ 未开始
```

### Sprint 4.6 (Week 11-12)
```
待开始 (5)  |  进行中 (0)  |  已完成 (0)  |  已验收 (0)
  🔴🔴🔴🔴🔴

进度: 0% | 预计完成: 2024-05-14 | 状态: ⏳ 未开始
```

## 6.4 依赖关系图

```
手机号登录 (F-4.1)
    ↓
工资用途记录 (F-4.2)
    ↓
年终奖展示 (F-4.4) ─── 并行 ───→ 支出明细 (F-4.3)
    ↓                           ↓
发薪情绪/延迟 (F-4.5) ───→ 存款目标 (F-4.6)
                              ↓
                         打卡功能 (F-4.7) ✅
                              ↓
                    ┌─────┴─────┐
              能力值系统      能力值兑换
               (F-4.8)         (F-4.9)
```

## 6.5 风险与阻塞跟踪

| ID | 风险描述 | 影响 | 概率 | 负责人 | 状态 | 缓解措施 |
|----|---------|------|------|--------|------|----------|
| R-4.1 | 微信手机号授权需要企业认证 | 高 | 高 | @产品 | 🔴 阻塞 | 确认认证状态，准备降级方案 |
| R-4.2 | 能力值兑换需采购实物 | 中 | 中 | @运营 | 🟡 监控 | 提前联系供应商，确定采购流程 |
| R-4.3 | 数据库迁移影响现有数据 | 中 | 低 | @后端 | 🟢 监控 | 充分测试，准备回滚脚本 |
| R-4.4 | 能力值系统性能问题 | 中 | 中 | @后端 | 🟡 监控 | 排行榜使用Redis缓存 |
| R-4.5 | 支出记录数据量大 | 低 | 中 | @后端 | 🟢 监控 | 分表存储，按月归档 |

---

# 七、附录

## 7.1 用途分类完整列表

```
一级分类          二级分类
💰 存起来         银行存款、理财、余额宝、基金
🏠 交家里         给父母、还房贷、家用
🛒 买东西         数码产品、衣服、日用品、化妆品
🍖 吃顿好的       大餐、火锅、自助餐、烧烤
🎉 娱乐玩乐       KTV、游戏、旅游、电影
🎁 送礼请客       请同事吃饭、送礼、红包
📚 学习提升       买书、课程、考证、培训
💸 还债还贷       信用卡、花呗、网贷、房贷
📱 其他           自定义
```

## 7.2 支出分类完整列表

```
一级分类          二级分类
🏠 居住           房租、水电、物业、网费、燃气
🍚 饮食           三餐、外卖、聚餐、烟酒、零食
🚌 交通           公交、地铁、打车、加油、停车
🛒 购物           服装、日用品、数码、美妆
💊 医疗           看病、买药、体检、保健品
🎮 娱乐           游戏、电影、会员、KTV
📚 学习           书籍、课程、培训、考证
📱 通讯           话费、宽带
🎁 礼物           人情往来、红包、礼品
💸 还贷           信用卡、花呗、房贷
📂 其他           宠物、美容、其他
```

## 7.3 能力值获取规则汇总

| 行为 | 能力值 | 限制 |
|------|--------|------|
| 每日登录 | +1 | 1次/天 |
| 记工资 | +10 | 无 |
| 记支出 | +5 | 无 |
| 发布帖子 | +20 | 10次/天 |
| 评论 | +5 | 20次/天 |
| 点赞 | +1 | 50次/天 |
| 被点赞 | +2 | 无 |
| 被关注 | +10 | 无 |
| 打卡 | +5 | 3次/天 |
| 完成存款目标 | +50 | 无 |
| 邀请好友 | +100 | 10人 |
| 年终奖打卡 | +20 | 1次/年 |

## 7.4 心情标签预设

**「发薪带来的好处」选项**：
- 💰 可以买买买了
- 😌 心里踏实了
- 💳 可以还花呗/信用卡了
- 🏠 可以交房租了
- 🍖 可以吃顿好的
- 🎉 感觉生活有希望了
- 😐 没什么特别感觉
- 📝 自定义...

---

**文档版本**: v1.3 增强版
**创建日期**: 2026-02-21
**最后更新**: 2026-02-21
**编写人**: Claude (PM Agent + Dev Agent)
**基于版本**: PRD v1.2

---

**文档结束**
