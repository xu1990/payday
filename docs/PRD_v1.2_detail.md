# 薪日 PayDay - 产品需求文档 v1.2

## 文档信息
- **文档版本**: v1.2
- **创建日期**: 2026-02-20
- **产品名称**: 薪日 PayDay
- **产品类型**: 微信小程序 + Web管理后台
- **文档状态**: 详细版
- **基于版本**: v1.1（优化版）

---

# 一、版本概述

## 1.1 版本更新说明

v1.2 版本在 v1.1 基础上新增以下核心功能模块：

| 序号 | 功能模块 | 说明 | 优先级 |
|------|----------|------|--------|
| 1 | 工资用途记录 | 记录第一笔工资的使用去向 | P1 |
| 2 | 每月支出明细 | 记录每月工资的花销明细 | P1 |
| 3 | 年终奖展示 | 晒出年终奖，增加社区互动 | P1 |
| 4 | 发薪情绪/延迟记录 | 记录发薪情绪、延迟发薪、拖欠情况 | P1 |
| 5 | 存款目标 | 设置每月存款目标，追踪储蓄进度 | P2 |
| 6 | 打卡功能 | 加班打卡、日常打卡等 | P2 |
| 7 | 能力值系统 | 用户能力值体系，关联多模块 | P2 |
| 8 | 能力值兑换 | 使用能力值兑换实物奖励 | P2 |
| 9 | 手机号登录 | 授权手机号登录，实现多端统一 | P0 |

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

### 2.1.2 用户流程

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

### 2.1.3 UI 设计

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

### 2.1.4 数据模型

**用户表扩展**：
```sql
ALTER TABLE users ADD COLUMN phone_number VARCHAR(20) COMMENT '手机号（脱敏）';
ALTER TABLE users ADD COLUMN phone_verified TINYINT DEFAULT 0 COMMENT '手机号是否验证';
ALTER TABLE users ADD INDEX idx_phone (phone_number);
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

### 2.1.5 API 接口

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
    "phoneNumber": string?,    // 已绑定时返回
    "isNewUser": boolean
  }
}

// 绑定手机号（后续绑定）
POST /api/v1/user/bind-phone
Request Body:
{
  "phoneNumberCode": string
}

// 更换手机号
POST /api/v1/user/change-phone
Request Body:
{
  "newPhoneNumberCode": string,
  "verificationCode": string    // 短信验证码
}
```

### 2.1.6 手机号脱敏策略

- 存储时加密（AES-256）
- 展示时脱敏（138****8888）
- 仅用户本人可见完整手机号
- 管理后台查看需权限审批

---

## 2.2 工资用途记录

### 2.2.1 功能描述

记录「第一笔工资」的使用去向，打造职场人的「第一次」仪式感。

### 2.2.2 业务流程

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

### 2.2.3 用途分类预设

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

### 2.2.4 UI 设计

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

### 2.2.5 数据模型

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

### 2.2.6 API 接口

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

// 获取用途记录
GET /api/v1/salary/:recordId/usage

// 获取第一笔工资用途（社区展示）
GET /api/v1/first-salary-usage?limit=20
```

### 2.2.7 社区互动

- **「第一笔工资」话题**：社区内自动创建话题 #第一笔工资
- **用途排行榜**：展示最热门的用途分类
- **年代对比**：80后/90后/00后的第一笔工资用途对比

---

## 2.3 每月支出明细

### 2.3.1 功能描述

在工资记录基础上，增加支出明细记录，形成「收入-支出-结余」的完整财务闭环。

### 2.3.2 支出分类体系

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

### 2.3.3 UI 设计

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

### 2.3.4 数据模型

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

### 2.3.5 统计与展示

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

### 2.3.6 API 接口

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

// 更新/删除支出
PUT /api/v1/expenses/:id
DELETE /api/v1/expenses/:id
```

---

## 2.4 年终奖展示

### 2.4.1 功能描述

- 专门的「年终奖」工资类型
- 年终奖专题社区话题
- 年终奖排行榜（匿名）

### 2.4.2 工资类型扩展

**现有类型**：normal（正常工资）、bonus（奖金）、allowance（补贴）、other（其他）

**新增类型**：year_end_bonus（年终奖）

### 2.4.3 社区专题

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

### 2.4.4 年终奖排行榜

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

### 2.4.5 API 接口

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

---

## 2.5 发薪情绪/延迟记录

### 2.5.1 功能描述

记录发薪相关情绪体验：
- 发薪心情（已存在）
- **新增**：是否延迟发薪
- **新增**：是否拖欠工资
- **新增**：发薪带来的好处/感受

### 2.5.2 工资记录扩展字段

```sql
ALTER TABLE salary_records ADD COLUMN is_delayed TINYINT DEFAULT 0 COMMENT '是否延迟发薪';
ALTER TABLE salary_records ADD COLUMN delayed_days INT DEFAULT 0 COMMENT '延迟天数';
ALTER TABLE salary_records ADD COLUMN is_arrears TINYINT DEFAULT 0 COMMENT '是否拖欠';
ALTER TABLE salary_records ADD COLUMN arrears_amount DECIMAL(10,2) COMMENT '拖欠金额';
ALTER TABLE salary_records ADD COLUMN mood_note TEXT COMMENT '心情备注（发薪带来的好处/感受）';
```

### 2.5.3 UI 更新

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

### 2.5.4 心情标签预设

**「发薪带来的好处」选项**：
- 💰 可以买买买了
- 😌 心里踏实了
- 💳 可以还花呗/信用卡了
- 🏠 可以交房租了
- 🍖 可以吃顿好的
- 🎉 感觉生活有希望了
- 😐 没什么特别感觉
- 📝 自定义...

### 2.5.5 统计展示

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

### 2.5.6 API 接口

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

---

## 2.6 存款目标

### 2.6.1 功能描述

设置每月存款目标，追踪储蓄进度，培养理财意识。

### 2.6.2 功能流程

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

### 2.6.3 UI 设计

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

**存款目标详情页**：
```
┌─────────────────────────────────┐
│  ← 买房基金                     │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│                                 │
│  目标金额 ¥50,000               │
│  已存 ¥12,000                   │
│  ████████░░░░░░░░  24%         │
│                                 │
│  [柱状图：每月存款进度]         │
│                                 │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│  本月目标                       │
│  目标：¥2,000                   │
│  实际：¥1,500                   │
│  ██████████░░  75%              │
│  还差 ¥500                      │
│                                 │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│  历史记录                       │
│  2024-01  ¥2,000  ✓ 达成       │
│  2023-12  ¥2,000  ✓ 达成       │
│  2023-11  ¥1,800  ✗ 未达成     │
│                                 │
│     [编辑目标]                  │
└─────────────────────────────────┘
```

### 2.6.4 数据模型

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

### 2.6.5 API 接口

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

---

## 2.7 打卡功能

### 2.7.1 功能描述

用户日常打卡功能，包括：
- 加班打卡
- 发薪日打卡
- 存款打卡
- 自定义打卡

### 2.7.2 打卡类型

| 打卡类型 | 触发条件 | 奖励 |
|----------|----------|------|
| 加班打卡 | 记录加班时间 | 能力值+5 |
| 发薪打卡 | 发薪日打卡 | 能力值+10 |
| 存款打卡 | 完成存款目标 | 能力值+20 |
| 连续打卡 | 连续N天 | 能力值+N*2 |

### 2.7.3 UI 设计

**打卡页**：
```
┌─────────────────────────────────┐
│  打卡                           │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│                                 │
│  今日已连续打卡 15 天 🔥         │
│                                 │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│                                 │
│  ┌───────────────────────────┐  │
│  │  💼 加班打卡              │  │
│  │  记录今日加班时长          │  │
│  │  [2] 小时                 │  │
│  │                           │  │
│  │     [立即打卡]             │  │
│  └───────────────────────────┘  │
│                                 │
│  ┌───────────────────────────┐  │
│  │  💰 发薪打卡              │  │
│  │  今天发薪啦！              │  │
│  │                           │  │
│  │     [立即打卡]             │  │
│  └───────────────────────────┘  │
│                                 │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│                                 │
│  打卡日历                       │
│  [日历视图：显示打卡记录]        │
│                                 │
└─────────────────────────────────┘
```

**打卡成功页**：
```
┌─────────────────────────────────┐
│                                 │
│          ✅ 打卡成功！           │
│                                 │
│        能力值 +5 🔥             │
│                                 │
│     已连续打卡 16 天            │
│                                 │
│     [分享]  [继续打卡]          │
│                                 │
└─────────────────────────────────┘
```

### 2.7.4 数据模型

```sql
CREATE TABLE check_ins (
  id VARCHAR(36) PRIMARY KEY,
  user_id VARCHAR(36) NOT NULL,
  check_in_type ENUM('overtime', 'payday', 'savings', 'custom') NOT NULL,
  check_in_date DATE NOT NULL COMMENT '打卡日期',
  overtime_hours INT COMMENT '加班小时数',
  note TEXT COMMENT '备注',
  reward_points INT DEFAULT 0 COMMENT '奖励能力值',
  consecutive_days INT DEFAULT 1 COMMENT '连续天数',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  UNIQUE KEY uk_user_date_type (user_id, check_in_date, check_in_type),
  INDEX idx_user_id (user_id),
  INDEX idx_check_in_date (check_in_date),
  FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='打卡记录表';
```

### 2.7.5 API 接口

```typescript
// 打卡
POST /api/v1/check-in
Request Body: {
  checkInType: 'overtime' | 'payday' | 'savings' | 'custom';
  overtimeHours?: number;
  note?: string;
}

Response: {
  success: boolean;
  rewardPoints: number;
  consecutiveDays: number;
  message: string;
}

// 获取打卡记录
GET /api/v1/check-in/records
Query: {
  startDate?: string;
  endDate?: string;
  type?: string;
}

// 获取打卡统计
GET /api/v1/check-in/statistics
Response: {
  consecutiveDays: number;
  totalCheckIns: number;
  monthlyCount: number;
  totalRewardPoints: number;
}

// 检查今日是否已打卡
GET /api/v1/check-in/today
```

---

## 2.8 能力值系统

### 2.8.1 功能描述

建立用户能力值（成长值）体系，关联多模块，提升用户活跃度和粘性。

### 2.8.2 能力值获取规则

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

### 2.8.3 能力值等级

| 等级 | 名称 | 能力值范围 | 特权 |
|------|------|------------|------|
| 1 | 职场新人 | 0-99 | 基础功能 |
| 2 | 打工小白 | 100-499 | 发帖+表情 |
| 3 | 熟练工 | 500-999 | 自定义头像 |
| 4 | 职场老手 | 1000-2999 | 优先展示 |
| 5 | 打工皇帝 | 3000+ | 独家勋章、专属客服 |

### 2.8.4 UI 设计

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

### 2.8.5 数据模型

```sql
ALTER TABLE users ADD COLUMN ability_points INT DEFAULT 0 COMMENT '能力值';
ALTER TABLE users ADD COLUMN ability_level INT DEFAULT 1 COMMENT '能力等级';
ALTER TABLE users ADD COLUMN ability_level_updated_at TIMESTAMP NULL COMMENT '等级更新时间';

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

### 2.8.6 API 接口

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
```

---

## 2.9 能力值兑换

### 2.9.1 功能描述

使用能力值兑换实物奖励，提升能力值的价值感和用户参与度。

### 2.9.2 兑换物分类

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

### 2.9.3 UI 设计

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

**兑换确认页**：
```
┌─────────────────────────────────┐
│  ← 确认兑换                     │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│                                 │
│  🎁 春节礼包                    │
│                                 │
│  兑换详情：                     │
│  - 坚果大礼包 x1                │
│  - 零食礼盒 x1                  │
│  - 新春红包 x1                  │
│                                 │
│  所需能力值：2000               │
│  当前余额：1280                 │
│  ❌ 能力值不足                  │
│                                 │
│     [去赚取能力值]              │
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

### 2.9.4 数据模型

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

### 2.9.5 兑换流程

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

### 2.9.6 API 接口

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

---

# 三、数据库变更汇总

## 3.1 表结构变更

```sql
-- 用户表扩展
ALTER TABLE users
ADD COLUMN phone_number VARCHAR(20) COMMENT '手机号（加密）',
ADD COLUMN phone_verified TINYINT DEFAULT 0 COMMENT '手机号是否验证',
ADD COLUMN ability_points INT DEFAULT 0 COMMENT '能力值',
ADD COLUMN ability_level INT DEFAULT 1 COMMENT '能力等级',
ADD COLUMN ability_level_updated_at TIMESTAMP NULL COMMENT '等级更新时间',
ADD INDEX idx_phone (phone_number);

-- 工资记录表扩展
ALTER TABLE salary_records
ADD COLUMN is_delayed TINYINT DEFAULT 0 COMMENT '是否延迟发薪',
ADD COLUMN delayed_days INT DEFAULT 0 COMMENT '延迟天数',
ADD COLUMN is_arrears TINYINT DEFAULT 0 COMMENT '是否拖欠',
ADD COLUMN arrears_amount DECIMAL(10,2) COMMENT '拖欠金额',
ADD COLUMN mood_note TEXT COMMENT '心情备注',
ADD COLUMN mood_tags JSON COMMENT '心情标签';

-- 新表
-- 见前述各模块的数据模型
```

---

# 四、API 接口汇总

## 4.1 新增接口列表

### 用户认证与账号
```
POST /api/v1/auth/login                 # 登录（支持手机号）
POST /api/v1/user/bind-phone            # 绑定手机号
POST /api/v1/user/change-phone          # 更换手机号
```

### 工资用途
```
POST /api/v1/salary/:recordId/usage     # 创建用途记录
GET /api/v1/salary/:recordId/usage      # 获取用途记录
GET /api/v1/first-salary-usage          # 第一笔工资用途展示
```

### 支出记录
```
POST /api/v1/salary/:recordId/expenses  # 创建支出记录
GET /api/v1/salary/:recordId/expenses   # 获取支出列表
GET /api/v1/expenses/statistics         # 支出统计
PUT /api/v1/expenses/:id                # 更新支出
DELETE /api/v1/expenses/:id             # 删除支出
```

### 年终奖
```
POST /api/v1/posts/year-end-bonus       # 发布年终奖帖子
GET /api/v1/statistics/year-end-bonus   # 年终奖统计
GET /api/v1/posts?topic=year_end_bonus  # 年终奖话题帖子
```

### 发薪准点率
```
GET /api/v1/statistics/punctuality      # 发薪准点率统计
```

### 存款目标
```
POST /api/v1/savings/goals              # 创建目标
GET /api/v1/savings/goals               # 获取目标列表
PUT /api/v1/savings/goals/:id           # 更新目标
POST /api/v1/savings/records            # 记录存款
GET /api/v1/savings/records             # 获取存款记录
GET /api/v1/savings/statistics          # 目标统计
```

### 打卡
```
POST /api/v1/check-in                   # 打卡
GET /api/v1/check-in/records            # 打卡记录
GET /api/v1/check-in/statistics         # 打卡统计
GET /api/v1/check-in/today              # 今日打卡状态
```

### 能力值
```
GET /api/v1/user/ability-points         # 能力值统计
GET /api/v1/user/ability-points/logs    # 能力值日志
GET /api/v1/leaderboard/ability-points  # 能力值排行榜
```

### 能力值兑换
```
GET /api/v1/reward/items                # 商城物品列表
GET /api/v1/reward/items/:id            # 物品详情
POST /api/v1/reward/orders              # 兑换物品
GET /api/v1/reward/orders               # 我的订单
GET /api/v1/reward/orders/:id           # 订单详情
POST /api/v1/reward/orders/:id/cancel   # 取消订单
POST /api/v1/reward/orders/:id/confirm  # 确认收货
```

---

# 五、开发计划

## 5.1 迭代规划

### Sprint 4.1：基础能力（2周）
- 手机号登录
- 工资用途记录
- 数据库设计与迁移

### Sprint 4.2：支出与年终奖（2周）
- 每月支出明细
- 年终奖展示
- 相关统计接口

### Sprint 4.3：情绪与延迟（2周）
- 发薪情绪扩展
- 延迟/拖欠记录
- 准点率统计

### Sprint 4.4：目标与打卡（2周）
- 存款目标
- 打卡功能
- 能力值基础

### Sprint 4.5：兑换体系（2周）
- 能力值完善
- 能力值商城
- 订单系统

### Sprint 4.6：测试与上线（2周）
- 集成测试
- 性能优化
- 上线准备

## 5.2 优先级说明

| 模块 | 优先级 | 原因 |
|------|--------|------|
| 手机号登录 | P0 | 账号体系基础，必须优先 |
| 工资用途 | P1 | 增强用户首次体验 |
| 支出明细 | P1 | 完善财务闭环 |
| 年终奖 | P1 | 社区活跃度 |
| 发薪情绪 | P1 | 情绪价值强化 |
| 存款目标 | P2 | 理财属性增强 |
| 打卡 | P2 | 用户活跃度 |
| 能力值 | P2 | 成长体系基础 |
| 能力值兑换 | P2 | 商业化前置 |

---

# 六、附录

## 6.1 用途分类完整列表

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

## 6.2 支出分类完整列表

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

## 6.3 能力值获取规则汇总

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

---

**文档版本**: v1.2 详细版
**最后更新**: 2026-02-20
**编写人**: Claude (PM Agent)

---

**文档结束**
