# 薪日 PayDay - 产品需求文档 v1.0

## 文档信息
- **文档版本**: v1.0
- **创建日期**: 2025-02-11
- **产品名称**: 薪日 PayDay
- **产品类型**: 微信小程序 + Web管理后台
- **文档状态**: 初稿

---

# 一、产品概述

## 1.1 产品定位
**薪日 PayDay** - 社交娱乐型打工人薪资状态与情绪互动平台，聚焦发薪情绪节点，为打工人提供工资记录、情绪表达、社区互动的综合服务。

## 1.2 目标用户
- **核心用户**: 18-40岁职场人群
- **次要用户**: 自由职业者、兼职人群
- **用户特征**:
  - 有工资收入焦虑
  - 喜欢情绪表达和社交互动
  - 关注个人财务状况

## 1.3 核心价值
- **情绪价值**: 发薪日的情绪释放与共鸣
- **社交价值**: 匿名社区的安全表达空间
- **工具价值**: 工资记录与财务管理

## 1.4 产品愿景
打造打工人专属的"发薪情绪社交平台"，逐步演变为职场文化与轻理财结合的社区型产品。

---

# 二、产品架构

## 2.1 产品组成
```
┌─────────────────────────────────────────────────┐
│                  薪日 PayDay                    │
├─────────────────────┬───────────────────────────┤
│   微信小程序端        │      Web管理后台          │
│   (C端用户)          │      (B端运营)            │
├─────────────────────┼───────────────────────────┤
│ • 首页/状态页        │ • 用户管理                │
│ • 工资记录           │ • 内容管理                │
│ • 社区/吐槽          │ • 数据统计                │
│ • 个人中心           │ • 系统配置                │
└─────────────────────┴───────────────────────────┘
```

## 2.2 技术栈
- **小程序前端**: uni-app (Vue3 + TypeScript)
- **Web后台**: Vue3 + Element Plus
- **后端服务**: FastAPI (Python)
- **数据库**: MySQL 8.0 + Redis
- **文件存储**: 腾讯云 COS 或 阿里云 oss
- **推送服务**: 微信订阅消息

---

# 三、小程序端功能需求

## 3.1 首页模块

### 3.1.1 发薪状态展示
**功能描述**: 首页展示今日发薪状态和倒计时

**UI元素**:
| 元素 | 类型 | 说明 | 交互 |
|------|------|------|------|
| 发薪状态文案 | 文本 | "今天发薪啦"/"距离发薪还有X天" | 点击进入详情 |
| 倒计时数字 | 数字 | 大字号显示剩余天数 | 可点击编辑发薪日 |
| 心情表情 | 表情选择器 | 开心/续命/崩溃/期待 | 点击切换心情 |
| 进度条 | 进度组件 | 本月时间进度 | 可点击查看日历 |

**数据属性**:
```typescript
interface PaydayStatus {
  isPaydayToday: boolean;          // 今天是否发薪
  daysUntilPayday: number;          // 距离发薪天数
  currentMood: MoodType;            // 当前心情
  monthProgress: number;            // 本月进度 0-100
  nextPaydayDate: Date;             // 下次发薪日期
}
```

### 3.1.2 快捷操作区
**功能入口**:
- 记工资 → 跳转工资记录页
- 吐槽一句 → 跳转社区发帖页
- 分享状态 → 生成分享海报
- 设置发薪日 → 跳转发薪日配置页

### 3.1.3 发薪日设置入口
**功能描述**: 用户可设置和管理自己的发薪日

**设置入口**:
1. 首页快捷操作区「设置发薪日」按钮
2. 首页倒计时数字点击进入
3. 个人中心 → 发薪日设置

**设置页面结构**:
```
┌─────────────────────────────────┐
│  发薪日设置                      │
├─────────────────────────────────┤
│  ┌───────────────────────────┐  │
│  │ 工作名称: [_________]      │  │
│  │ 发薪日:   [10] 日         │  │
│  │ 日历类型: ○公历 ●农历     │  │
│  │ 预估工资: [15000] 元      │  │
│  │                             │  │
│  │ [取消]        [保存]       │  │
│  └───────────────────────────┘  │
│                                  │
│  已配置的工作:                   │
│  ┌───────────────────────────┐  │
│  │ ☑ 某某公司-主业 (10日)    │  │ [编辑] [删除]
│  │ ☐ 兼职工作 (25日)         │  │ [编辑] [删除]
│  └───────────────────────────┘  │
│                                  │
│  [+ 添加新工作]                  │
└─────────────────────────────────┘
```

---

## 3.2 工资记录模块

### 3.2.1 发薪日设置
**功能描述**: 设置工资发放日期

**表单字段**:
| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| 工作名称 | 文本 | 是 | 主业/副业标识 | "某某公司-主业" |
| 发薪日 | 数字 | 是 | 每月几号 | 10/15/25/月底 |
| 日历类型 | 选择 | 是 | 公历/农历 | 公历 |
| 金额(预估) | 数字 | 否 | 用于收入统计 | 15000 |

**数据模型**:
```typescript
interface PaydayConfig {
  id: string;
  userId: string;
  jobName: string;               // 工作名称
  payday: number;                // 发薪日 1-31
  calendarType: 'solar' | 'lunar'; // 公历/农历
  estimatedSalary?: number;      // 预估金额
  isActive: boolean;             // 是否启用
  createdAt: Date;
  updatedAt: Date;
}
```

### 3.2.2 工资记录
**功能描述**: 记录每次收到的工资

**表单字段**:
| 字段 | 类型 | 必填 | 说明 | 验证规则 |
|------|------|------|------|----------|
| 关联工作 | 选择 | 是 | 选择已配置的工作 | 必须先配置工作 |
| 实发金额 | 数字 | 是 | 税后到账金额 | >0 |
| 发薪日期 | 日期 | 是 | 实际到账日期 | 默认今天 |
| 工资类型 | 选择 | 否 | 正常工资/奖金/补贴 | 枚举 |
| 工资条图片 | 上传 | 否 | 上传工资条截图 | 最多3张，支持jpg/png |
| 备注 | 文本 | 否 | 备注信息 | 最多200字 |
| 心情 | 表情 | 是 | 本次发薪心情 | 必选 |

**图片上传功能**:
- 支持拍照或相册选择
- 最多上传3张图片
- 支持格式: jpg、png
- 单张图片大小限制: < 5MB
- 图片会自动进行OCR识别(可选功能)
- 图片上传后进入风控审核队列

**数据模型**:
```typescript
interface SalaryRecord {
  id: string;
  userId: string;
  configId: string;              // 关联的PaydayConfig
  amount: number;                // 实发金额
  paydayDate: Date;              // 发薪日期
  salaryType: 'normal' | 'bonus' | 'allowance' | 'other';
  images?: string[];             // 工资条图片URLs
  note?: string;
  mood: MoodType;

  // 风控相关
  riskStatus: 'pending' | 'approved' | 'rejected'; // 风控状态
  riskCheckTime?: Date;          // 风控审核时间

  createdAt: Date;
  updatedAt: Date;
}

type MoodType = 'happy' | 'relief' | 'sad' | 'angry' | 'expect';
```

### 3.2.3 工资统计
**统计维度**:
- 月度收入趋势图
- 年度收入汇总
- 工资类型占比饼图
- 发薪准时率

---

## 3.3 社区模块

### 3.3.1 吐槽广场
**功能描述**: 匿名工资吐槽社区，用户可发帖、浏览、互动

**页面结构**:
```
┌─────────────────────────────────┐
│  🔥 热门  🆕 最新  📝 我的      │  <- Tab切换
├─────────────────────────────────┤
│  ┌───────────────────────────┐  │
│  │ 👤 匿名用户_8a3f          │  │
│  │ 2小时前  #工资低          │  │
│  │ ─────────────────────────  │  │
│  │ 今天发工资了，扣完五险一金│  │
│  │ 就剩这点了，这日子没法过了│  │
│  │ 💬 23  👍 156  👁️ 2.3k   │  │
│  └───────────────────────────┘  │
│                                  │
│  ┌───────────────────────────┐  │
│  │ [更多帖子列表...]          │  │
│  └───────────────────────────┘  │
└─────────────────────────────────┘
```

**帖子数据模型**:
```typescript
interface Post {
  id: string;
  authorId: string;              // 作者ID(不对外展示)
  anonymousName: string;         // 匿名昵称
  content: string;               // 帖子内容
  images?: string[];             // 图片URLs(可选，最多9张)
  tags?: string[];               // 标签 #工资低 #加班
  type: 'complaint' | 'sharing' | 'question'; // 帖子类型

  // 统计数据
  viewCount: number;             // 浏览量
  likeCount: number;             // 点赞数
  commentCount: number;          // 评论数
  shareCount: number;            // 分享数

  // 状态
  status: 'normal' | 'hidden' | 'deleted'; // 帖子状态

  // 风控相关
  riskStatus: 'pending' | 'approved' | 'rejected'; // 风控审核状态
  riskScore?: number;            // 风控评分 0-100
  riskReason?: string;           // 风控原因
  riskCheckTime?: Date;          // 风控审核时间

  // 时间戳
  createdAt: Date;
  updatedAt: Date;

  // 关联
  salaryRange?: string;          // 工资区间(可选)
  industry?: string;             // 行业(可选)
  city?: string;                 // 城市(可选)
}
```

### 3.3.2 发帖功能
**功能描述**: 用户发布匿名吐槽内容

**发布表单**:
| 字段 | 类型 | 必填 | 说明 | 限制 |
|------|------|------|------|------|
| 帖子类型 | 选择 | 是 | 吐槽/分享/提问 | 单选 |
| 内容 | 文本域 | 是 | 帖子正文 | 10-1000字 |
| 图片 | 上传 | 否 | 最多9张 | 支持jpg/png |
| 工资区间 | 选择 | 否 | 匿名展示 | 5个区间 |
| 行业 | 选择 | 否 | 互联网/金融等 | 下拉选择 |
| 城市 | 选择 | 否 | 可选填 | 下拉选择 |
| 标签 | 文本 | 否 | 自定义标签 | 最多3个 |

**图片上传规则**:
- 支持拍照或相册选择
- 最多上传9张图片
- 支持格式: jpg、png
- 单张图片大小限制: < 5MB
- 图片上传后进入风控审核队列

**内容审核规则**:
- 禁止发布真实姓名、公司名
- 禁止发布手机号、微信号等联系方式
- 敏感词过滤
- 图片违规检测

**数据模型**:
```typescript
interface CreatePostDTO {
  type: 'complaint' | 'sharing' | 'question';
  content: string;                // 10-1000字符
  images?: string[];              // 最多9张
  salaryRange?: string;           // '3-5k', '5-8k', '8-12k', '12-20k', '20k+'
  industry?: string;
  city?: string;
  tags?: string[];                // 最多3个
}
```

---

### 3.3.2.1 风控机制设计
**功能描述**: 对用户发布的文字内容和图片进行风控审核，确保平台内容安全

#### 风控流程
```
用户发布内容
    ↓
内容立即发布(风险预判)
    ↓
标记风控状态: pending
    ↓
异步风控检测
    ├── 文字内容检测
    │   ├── 敏感词过滤
    │   ├── 垃圾内容识别
    │   └── 语义分析
    ├── 图片内容检测
    │   ├── 色情识别
    │   ├── 暴力识别
    │   ├── 广告识别
    │   └── OCR文字提取
    └── 用户行为评分
        ├── 发帖频率
        ├── 被举报次数
        └── 账号信誉分
    ↓
风控判定
    ├── 通过 → riskStatus: approved (正常展示)
    ├── 拒绝 → riskStatus: rejected (下架内容)
    └── 人工复核 → 疑似内容转人工审核
```

#### 风控状态说明
| 状态 | 说明 | 展示逻辑 |
|------|------|----------|
| pending | 待审核 | 内容正常展示，后台标记为待审核 |
| approved | 审核通过 | 内容正常展示 |
| rejected | 审核拒绝 | 内容下架，用户不可见，通知用户 |

#### 风控评分规则
```typescript
interface RiskCheckResult {
  passed: boolean;                // 是否通过
  score: number;                  // 风控评分 0-100 (越高越危险)
  reasons: string[];              // 风控原因
  suggestedAction: 'approve' | 'reject' | 'manual'; // 建议操作
}

// 风控触发条件
const RISK_RULES = {
  // 文字内容
  sensitiveWords: { threshold: 1, score: 90 },      // 命中敏感词
  contactInfo: { threshold: 1, score: 80 },         // 包含联系方式
  spamContent: { threshold: 1, score: 70 },         // 垃圾内容

  // 图片内容
  pornImage: { threshold: 1, score: 95 },           // 色情图片
  violenceImage: { threshold: 1, score: 95 },       // 暴力图片
  adImage: { threshold: 1, score: 60 },             // 广告图片

  // 用户行为
  highFrequency: { threshold: 5, score: 50 },       // 短时间内大量发帖
  lowReputation: { threshold: 60, score: 30 },      // 信誉分低于60
  reportedCount: { threshold: 3, score: 70 },       // 被举报超过3次
};

// 判定逻辑
if (score >= 80) {
  action = 'reject';           // 直接拒绝
} else if (score >= 50) {
  action = 'manual';           // 人工复核
} else {
  action = 'approve';          // 自动通过
}
```

#### 用户通知机制
**审核通过**: 无需通知，内容正常展示

**审核拒绝**:
```
通知标题: 内容审核未通过
通知内容: 您发布的内容未通过审核，已被下架。
原因: {riskReason}
如有疑问，请联系客服。
```

#### 风控数据模型
```typescript
interface RiskCheck {
  id: string;
  targetId: string;             // 目标内容ID (帖子/评论/工资记录)
  targetType: 'post' | 'comment' | 'salary_record';
  userId: string;               // 发布者ID

  // 检测结果
  status: 'pending' | 'approved' | 'rejected' | 'manual';
  score: number;                // 风控评分 0-100
  reasons: string[];            // 风控原因列表

  // 检测详情
  textCheckResult?: {
    sensitiveWords: string[];   // 命中的敏感词
    hasContactInfo: boolean;
    spamScore: number;
  };
  imageCheckResult?: {
    totalCount: number;
    pornCount: number;
    violenceCount: number;
    adCount: number;
    ocrText?: string;           // OCR提取的文字
  };
  userBehaviorScore?: {
    frequencyScore: number;
    reputationScore: number;
    reportCount: number;
  };

  // 审核信息
  checkerType: 'auto' | 'manual'; // 审核类型
  checkerId?: string;           // 人工审核员ID
  checkNote?: string;           // 审核备注

  createdAt: Date;
  updatedAt: Date;
}
```

#### 风控查询接口
```
GET  /api/v1/admin/risk/pending      获取待审核列表
GET  /api/v1/admin/risk/:id          获取审核详情
POST /api/v1/admin/risk/:id/approve  人工审核通过
POST /api/v1/admin/risk/:id/reject   人工审核拒绝
GET  /api/v1/admin/risk/stats        风控统计数据
```

#### 管理后台风控管理页面
**列表字段**:
| 字段 | 说明 |
|------|------|
| 内容ID | 目标内容ID |
| 内容类型 | 帖子/评论/工资记录 |
| 作者 | 匿名昵称 |
| 风控评分 | 0-100分 |
| 风控状态 | 待审核/通过/拒绝/人工复核 |
| 风控原因 | 触发规则 |
| 创建时间 | 提交时间 |
| 操作 | 查看/通过/拒绝 |

**统计展示**:
- 今日待审核数量
- 今日自动通过率
- 今日人工审核数量
- 风控触发趋势图

### 3.3.3 互动功能

#### 3.3.3.1 评论系统
**功能描述**: 对帖子进行评论回复

**评论数据模型**:
```typescript
interface Comment {
  id: string;
  postId: string;                 // 关联帖子
  authorId: string;               // 评论者ID
  anonymousName: string;          // 匿名昵称
  content: string;                // 评论内容
  parentId?: string;              // 父评论ID(回复功能)

  // 统计
  likeCount: number;

  // 风控相关
  riskStatus: 'pending' | 'approved' | 'rejected'; // 风控状态

  // 时间
  createdAt: Date;
  updatedAt: Date;
}

interface CreateCommentDTO {
  postId: string;
  content: string;                // 1-500字符
  parentId?: string;              // 回复评论时必填
}
```

**评论展示规则**:
- 楼层式展示
- 支持二级回复
- 热门评论置顶
- 被风控拒绝的评论不展示

#### 3.3.3.2 点赞功能
**功能描述**: 对帖子/评论进行点赞

**数据模型**:
```typescript
interface Like {
  id: string;
  userId: string;
  targetType: 'post' | 'comment'; // 点赞目标类型
  targetId: string;               // 目标ID
  createdAt: Date;

  // 联合唯一索引: userId + targetType + targetId
}
```

#### 3.3.3.3 关注功能
**功能描述**: 关注感兴趣的匿名用户

**数据模型**:
```typescript
interface Follow {
  id: string;
  followerId: string;             // 粉丝ID
  followingId: string;            // 被关注者ID
  createdAt: Date;

  // 联合唯一索引: followerId + followingId
}

// 用户关注统计
interface UserFollowStats {
  userId: string;
  followerCount: number;          // 粉丝数
  followingCount: number;         // 关注数
}
```

**关注规则**:
- 不能关注自己
- 匿名状态下只能看到对方的匿名昵称
- 关注后可在"我关注的"列表查看对方新帖

### 3.3.4 消息通知
**通知类型**:
| 通知类型 | 触发条件 | 内容 |
|----------|----------|------|
| 评论通知 | 有人评论你的帖子 | "匿名用户xxx评论了你的帖子" |
| 回复通知 | 有人回复你的评论 | "匿名用户xxx回复了你的评论" |
| 点赞通知 | 有人点赞你的帖子/评论 | "匿名用户xxx赞了你的内容" |
| 关注通知 | 有人关注了你 | "匿名用户xxx关注了你" |
| 系统通知 | 系统公告 | 运营推送消息 |

**通知数据模型**:
```typescript
interface Notification {
  id: string;
  userId: string;                 // 接收者
  type: 'comment' | 'reply' | 'like' | 'follow' | 'system';
  title: string;
  content: string;
  relatedId?: string;             // 关联的帖子/评论ID
  isRead: boolean;
  createdAt: Date;
}
```

### 3.3.5 用户主页
**功能描述**: 查看某个用户的公开信息

**页面元素**:
- 匿名昵称 + 随机头像
- 粉丝数 / 关注数
- 发帖数
- 简介(可选填)
- 发布的帖子列表

**用户数据模型**:
```typescript
interface User {
  id: string;
  openid: string;                 // 微信openid
  anonymousName: string;          // 系统生成的匿名昵称
  avatar?: string;                // 默认随机头像
  bio?: string;                   // 个人简介
  followerCount: number;
  followingCount: number;
  postCount: number;

  // 设置
  allowFollow: boolean;           // 允许被关注
  allowComment: boolean;          // 允许评论

  createdAt: Date;
  updatedAt: Date;
}
```

---

## 3.4 个人中心模块

### 3.4.1 个人信息
**展示内容**:
- 微信头像/昵称(脱敏)
- 匿名昵称
- 入职天数/打工天数

### 3.4.2 功能入口
| 功能 | 说明 |
|------|------|
| 我的工资 | 工资记录列表 |
| 我的帖子 | 发布的帖子列表 |
| 我的收藏 | 收藏的帖子 |
| 我关注的 | 关注的用户列表 |
| 消息通知 | 通知消息列表 |
| 设置 | 应用设置 |

---

# 四、Web管理后台功能需求

## 4.1 用户管理

### 4.1.1 用户列表
**功能描述**: 查看和管理所有注册用户

**列表字段**:
| 字段 | 说明 | 操作 |
|------|------|------|
| 用户ID | 系统唯一标识 | 复制 |
| 匿名昵称 | 匿名展示名称 | - |
| 微信昵称 | 真实昵称(脱敏) | - |
| 注册时间 | 注册日期 | - |
| 最后活跃 | 最后登录时间 | - |
| 状态 | 正常/禁用 | 切换 |
| 操作 | - | 查看详情/禁用/解禁 |

**筛选功能**:
- 按注册时间筛选
- 按活跃状态筛选
- 按用户状态筛选
- 搜索匿名昵称

### 4.1.2 用户详情
**展示内容**:
- 基本信息
- 统计数据(发帖数、评论数、粉丝数)
- 行为记录(登录日志、操作记录)
- 内容管理(查看/删除用户的帖子、评论)

---

## 4.2 内容管理

### 4.2.1 帖子管理
**功能描述**: 审核和管理社区帖子

**列表字段**:
| 字段 | 说明 |
|------|------|
| 帖子ID | 唯一标识 |
| 作者 | 匿名昵称 |
| 内容摘要 | 前100字 |
| 类型 | 吐槽/分享/提问 |
| 状态 | 正常/隐藏/删除 |
| 互动数据 | 浏览/点赞/评论 |
| 发布时间 | - |
| 操作 | 查看/隐藏/删除/置顶 |

**内容审核**:
- 查看帖子详情
- 隐藏帖子(用户不可见)
- 删除帖子(永久删除)
- 置顶帖子(设置推荐)
- 添加官方标签

**审核规则**:
```
自动审核:
- 敏感词过滤
- 图片违规检测
- 重复内容检测

人工审核:
- 用户举报内容
- 热门内容复核
- 可疑内容标记
```

### 4.2.2 评论管理
**功能描述**: 管理帖子评论

**功能**:
- 查看评论列表
- 删除违规评论
- 评论敏感词过滤
- 评论数据统计

### 4.2.3 举报管理
**功能描述**: 处理用户举报

**举报类型**:
| 类型 | 说明 |
|------|------|
| 违规内容 | 色情/暴力/政治敏感 |
| 垃圾广告 | 营销推广 |
| 人身攻击 | 辱骂/歧视 |
| 虚假信息 | 谣言/诈骗 |

**处理流程**:
```
1. 接收举报 → 2. 审核内容 → 3. 处理(删除/忽略) → 4. 通知举报人
```

---

## 4.3 数据统计

### 4.3.1 用户统计
**统计维度**:
- 总用户数
- 日活跃用户(DAU)
- 月活跃用户(MAU)
- 新增用户趋势(折线图)
- 用户留存率

**图表展示**:
```
┌────────────────────────────────┐
│  用户总览                       │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│  总用户: 12,345                │
│  今日新增: 156                 │
│  日活: 3,456                   │
│  月活: 8,901                   │
└────────────────────────────────┘
```

### 4.3.2 内容统计
**统计维度**:
- 帖子总数
- 日均发帖数
- 评论总数
- 互动率(点赞+评论/浏览)

### 4.3.3 工资数据统计
**统计维度**:
- 记录总数
- 行业工资分布
- 城市工资对比
- 发薪日分布

**数据脱敏**:
- 只展示区间统计
- 不展示个人数据
- 最小样本量保护(<10人不显示)

---

## 4.4 运营功能

### 4.4.1 内容推荐
**功能描述**: 设置推荐内容

**推荐位**:
- 首页热门帖子
- 发现页精选内容
- 话题标签推荐

### 4.4.2 话题管理
**功能描述**: 创建和管理社区话题

**数据模型**:
```typescript
interface Topic {
  id: string;
  name: string;                  // 话题名称
  description?: string;          // 话题描述
  coverImage?: string;           // 封面图
  postCount: number;             // 参与帖子数
  isHot: boolean;                // 是否热门
  sortOrder: number;             // 排序值
  createdAt: Date;
}
```

**示例话题**:
- #发薪日打卡
- #工资吐槽大会
- #涨薪那些事
- #公司福利对比

### 4.4.3 系统通知
**功能描述**: 向用户发送系统通知

**通知类型**:
- 全员公告
- 分组推送(按行业/城市)
- 单人通知

**发送表单**:
| 字段 | 说明 |
|------|------|
| 通知类型 | 公告/活动/更新 |
| 标题 | 通知标题 |
| 内容 | 通知内容 |
| 目标用户 | 全员/分组/单人 |
| 发送时间 | 立即/定时 |

---

## 4.5 系统设置

### 4.5.1 敏感词管理
**功能描述**: 管理内容敏感词库

**功能**:
- 添加/删除敏感词
- 导入敏感词库
- 敏感词分类(政治/色情/暴力等)

### 4.5.2 基础配置
**配置项**:
- 小程序基本信息
- 默认头像库
- 工资区间设置
- 行业分类管理
- 城市列表管理

---

# 五、数据模型定义

## 5.1 核心数据表

### 5.1.1 用户表 (users)
```sql
CREATE TABLE users (
  id VARCHAR(36) PRIMARY KEY,
  openid VARCHAR(64) UNIQUE NOT NULL COMMENT '微信openid',
  unionid VARCHAR(64) COMMENT '微信unionid',
  anonymous_name VARCHAR(50) NOT NULL COMMENT '匿名昵称',
  avatar VARCHAR(255) COMMENT '头像URL',
  bio VARCHAR(200) COMMENT '个人简介',

  follower_count INT DEFAULT 0 COMMENT '粉丝数',
  following_count INT DEFAULT 0 COMMENT '关注数',
  post_count INT DEFAULT 0 COMMENT '发帖数',

  allow_follow TINYINT DEFAULT 1 COMMENT '允许被关注',
  allow_comment TINYINT DEFAULT 1 COMMENT '允许评论',

  status ENUM('normal', 'disabled') DEFAULT 'normal',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  INDEX idx_openid (openid),
  INDEX idx_status (status),
  INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';
```

### 5.1.2 发薪日配置表 (payday_configs)
```sql
CREATE TABLE payday_configs (
  id VARCHAR(36) PRIMARY KEY,
  user_id VARCHAR(36) NOT NULL,
  job_name VARCHAR(50) NOT NULL COMMENT '工作名称',
  payday TINYINT NOT NULL COMMENT '发薪日1-31',
  calendar_type ENUM('solar', 'lunar') DEFAULT 'solar',
  estimated_salary DECIMAL(10,2) COMMENT '预估工资',
  is_active TINYINT DEFAULT 1 COMMENT '是否启用',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  INDEX idx_user_id (user_id),
  INDEX idx_is_active (is_active),
  FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='发薪日配置表';
```

### 5.1.3 工资记录表 (salary_records)
```sql
CREATE TABLE salary_records (
  id VARCHAR(36) PRIMARY KEY,
  user_id VARCHAR(36) NOT NULL,
  config_id VARCHAR(36) NOT NULL,
  amount DECIMAL(10,2) NOT NULL COMMENT '实发金额',
  payday_date DATE NOT NULL COMMENT '发薪日期',
  salary_type ENUM('normal', 'bonus', 'allowance', 'other') DEFAULT 'normal',
  images JSON COMMENT '工资条图片URLs',
  note TEXT COMMENT '备注',
  mood ENUM('happy', 'relief', 'sad', 'angry', 'expect') NOT NULL,

  -- 风控相关
  risk_status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending' COMMENT '风控状态',
  risk_check_time TIMESTAMP NULL COMMENT '风控审核时间',

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  INDEX idx_user_id (user_id),
  INDEX idx_config_id (config_id),
  INDEX idx_payday_date (payday_date),
  INDEX idx_risk_status (risk_status),
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (config_id) REFERENCES payday_configs(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工资记录表';
```

### 5.1.4 帖子表 (posts)
```sql
CREATE TABLE posts (
  id VARCHAR(36) PRIMARY KEY,
  user_id VARCHAR(36) NOT NULL,
  anonymous_name VARCHAR(50) NOT NULL,
  content TEXT NOT NULL,
  images JSON COMMENT '图片URLs',
  tags JSON COMMENT '标签',
  type ENUM('complaint', 'sharing', 'question') DEFAULT 'complaint',

  salary_range VARCHAR(20) COMMENT '工资区间',
  industry VARCHAR(50) COMMENT '行业',
  city VARCHAR(50) COMMENT '城市',

  view_count INT DEFAULT 0,
  like_count INT DEFAULT 0,
  comment_count INT DEFAULT 0,
  share_count INT DEFAULT 0,

  is_top TINYINT DEFAULT 0 COMMENT '是否置顶',
  status ENUM('normal', 'hidden', 'deleted') DEFAULT 'normal',

  -- 风控相关
  risk_status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending' COMMENT '风控状态',
  risk_score INT COMMENT '风控评分 0-100',
  risk_reason VARCHAR(500) COMMENT '风控原因',
  risk_check_time TIMESTAMP NULL COMMENT '风控审核时间',

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  INDEX idx_user_id (user_id),
  INDEX idx_type (type),
  INDEX idx_status (status),
  INDEX idx_risk_status (risk_status),
  INDEX idx_created_at (created_at),
  INDEX idx_like_count (like_count),
  FULLTEXT idx_content (content)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='帖子表';
```

### 5.1.5 评论表 (comments)
```sql
CREATE TABLE comments (
  id VARCHAR(36) PRIMARY KEY,
  post_id VARCHAR(36) NOT NULL,
  user_id VARCHAR(36) NOT NULL,
  parent_id VARCHAR(36) COMMENT '父评论ID',
  anonymous_name VARCHAR(50) NOT NULL,
  content TEXT NOT NULL,
  like_count INT DEFAULT 0,
  status ENUM('normal', 'deleted') DEFAULT 'normal',

  -- 风控相关
  risk_status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending' COMMENT '风控状态',

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  INDEX idx_post_id (post_id),
  INDEX idx_user_id (user_id),
  INDEX idx_parent_id (parent_id),
  INDEX idx_risk_status (risk_status),
  INDEX idx_created_at (created_at),
  FOREIGN KEY (post_id) REFERENCES posts(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='评论表';
```

### 5.1.6 点赞表 (likes)
```sql
CREATE TABLE likes (
  id VARCHAR(36) PRIMARY KEY,
  user_id VARCHAR(36) NOT NULL,
  target_type ENUM('post', 'comment') NOT NULL,
  target_id VARCHAR(36) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  UNIQUE KEY uk_user_target (user_id, target_type, target_id),
  INDEX idx_target (target_type, target_id),
  INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='点赞表';
```

### 5.1.7 关注表 (follows)
```sql
CREATE TABLE follows (
  id VARCHAR(36) PRIMARY KEY,
  follower_id VARCHAR(36) NOT NULL COMMENT '关注者',
  following_id VARCHAR(36) NOT NULL COMMENT '被关注者',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  UNIQUE KEY uk_follow (follower_id, following_id),
  INDEX idx_follower (follower_id),
  INDEX idx_following (following_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='关注表';
```

### 5.1.8 通知表 (notifications)
```sql
CREATE TABLE notifications (
  id VARCHAR(36) PRIMARY KEY,
  user_id VARCHAR(36) NOT NULL,
  type ENUM('comment', 'reply', 'like', 'follow', 'system') NOT NULL,
  title VARCHAR(100) NOT NULL,
  content TEXT,
  related_id VARCHAR(36) COMMENT '关联内容ID',
  is_read TINYINT DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  INDEX idx_user_id (user_id),
  INDEX idx_is_read (is_read),
  INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='通知表';
```

### 5.1.9 风控审核表 (risk_checks)
```sql
CREATE TABLE risk_checks (
  id VARCHAR(36) PRIMARY KEY,
  target_id VARCHAR(36) NOT NULL COMMENT '目标内容ID',
  target_type ENUM('post', 'comment', 'salary_record') NOT NULL,
  user_id VARCHAR(36) NOT NULL COMMENT '发布者ID',

  -- 检测结果
  status ENUM('pending', 'approved', 'rejected', 'manual') DEFAULT 'pending',
  score INT COMMENT '风控评分 0-100',
  reasons JSON COMMENT '风控原因列表',

  -- 检测详情
  text_check_result JSON COMMENT '文字检测结果',
  image_check_result JSON COMMENT '图片检测结果',
  user_behavior_score JSON COMMENT '用户行为评分',

  -- 审核信息
  checker_type ENUM('auto', 'manual') DEFAULT 'auto',
  checker_id VARCHAR(36) COMMENT '人工审核员ID',
  check_note TEXT COMMENT '审核备注',

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  INDEX idx_target (target_type, target_id),
  INDEX idx_user_id (user_id),
  INDEX idx_status (status),
  INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='风控审核表';
```

---

# 六、API接口设计

## 6.1 小程序端接口

### 6.1.1 用户相关
```
POST   /api/v1/auth/login              微信登录
GET    /api/v1/user/profile            获取用户信息
PUT    /api/v1/user/profile            更新用户信息
```

### 6.1.2 工资相关
```
POST   /api/v1/payday/config           创建发薪日配置
GET    /api/v1/payday/config           获取配置列表
PUT    /api/v1/payday/config/:id       更新配置
DELETE /api/v1/payday/config/:id       删除配置

GET    /api/v1/payday/status           获取发薪状态

POST   /api/v1/salary/record           创建工资记录
GET    /api/v1/salary/record           获取记录列表
GET    /api/v1/salary/record/:id       获取记录详情
PUT    /api/v1/salary/record/:id       更新记录
DELETE /api/v1/salary/record/:id       删除记录

GET    /api/v1/salary/statistics       获取工资统计
```

### 6.1.3 社区相关
```
GET    /api/v1/posts                   获取帖子列表(热门/最新)
POST   /api/v1/posts                   发布帖子
GET    /api/v1/posts/:id               获取帖子详情
DELETE /api/v1/posts/:id               删除帖子

GET    /api/v1/posts/:id/comments      获取评论列表
POST   /api/v1/posts/:id/comments      发表评论
DELETE /api/v1/comments/:id            删除评论

POST   /api/v1/posts/:id/like          点赞/取消点赞
POST   /api/v1/comments/:id/like       点赞/取消点赞评论

POST   /api/v1/user/:id/follow         关注/取消关注
GET    /api/v1/user/:id/posts          获取用户帖子
GET    /api/v1/user/following          获取关注列表
GET    /api/v1/user/followers          获取粉丝列表

GET    /api/v1/notifications           获取通知列表
PUT    /api/v1/notifications/read      标记已读
```

## 6.2 管理后台接口
```
POST   /api/v1/admin/login             管理员登录

# 用户管理
GET    /api/v1/admin/users             用户列表
GET    /api/v1/admin/users/:id         用户详情
PUT    /api/v1/admin/users/:id/status  更新用户状态

# 内容管理
GET    /api/v1/admin/posts             帖子列表
PUT    /api/v1/admin/posts/:id/status  更新帖子状态
DELETE /api/v1/admin/posts/:id         删除帖子

GET    /api/v1/admin/comments          评论列表
DELETE /api/v1/admin/comments/:id      删除评论

GET    /api/v1/admin/reports           举报列表
PUT    /api/v1/admin/reports/:id       处理举报

# 风控管理
GET    /api/v1/admin/risk/pending      获取待审核列表
GET    /api/v1/admin/risk/:id          获取审核详情
POST   /api/v1/admin/risk/:id/approve  人工审核通过
POST   /api/v1/admin/risk/:id/reject   人工审核拒绝
GET    /api/v1/admin/risk/stats        风控统计数据

# 数据统计
GET    /api/v1/admin/stats/users       用户统计
GET    /api/v1/admin/stats/posts       内容统计
GET    /api/v1/admin/stats/salary      工资统计

# 系统设置
GET    /api/v1/admin/topics            话题列表
POST   /api/v1/admin/topics            创建话题
PUT    /api/v1/admin/topics/:id        更新话题
DELETE /api/v1/admin/topics/:id        删除话题

POST   /api/v1/admin/notifications     发送系统通知
```

---

# 七、非功能需求

## 7.1 性能要求
- 接口响应时间 < 500ms (P95)
- 页面加载时间 < 2s
- 支持并发用户数 > 1000

## 7.2 安全要求
- 用户数据加密存储
- API接口签名验证
- 内容敏感词过滤
- 防刷机制(频率限制)

## 7.3 可用性
- 系统可用性 > 99.5%
- 数据备份: 每日自动备份
- 灾备方案: 主从热备

---

# 八、开发计划

## 8.1 迭代规划

### Phase 1: MVP (1-2个月)
**小程序端**:
- 首页发薪状态
- 发薪日设置
- 工资记录
- 基础统计

**管理后台**:
- 用户管理
- 内容管理
- 基础统计

### Phase 2: 社区版 (2-3个月)
**新增功能**:
- 吐槽社区
- 评论系统
- 点赞功能
- 通知系统

### Phase 3: 完整版 (3-4个月)
**新增功能**:
- 关注功能
- 用户主页
- 数据洞察
- 商业化模块

## 8.2 里程碑
| 阶段 | 时间 | 交付物 |
|------|------|--------|
| 需求确认 | Week 1 | PRD v1.0 |
| 技术设计 | Week 2 | 技术方案文档 |
| 开发 | Week 3-10 | 可测试版本 |
| 测试 | Week 11-12 | 测试报告 |
| 上线 | Week 13 | 正式发布 |

---

# 九、附录

## 9.1 工资区间定义
```
区间1: 3k以下
区间2: 3k-5k
区间3: 5k-8k
区间4: 8k-12k
区间5: 12k-20k
区间6: 20k以上
```

## 9.2 行业分类
```
1. 互联网/IT
2. 金融
3. 教育
4. 制造业
5. 零售/电商
6. 医疗健康
7. 房地产
8. 文化传媒
9. 交通运输
10. 其他
```

## 9.3 匿名昵称生成规则
```
格式: 匿名用户_{随机4位字符}
示例: 匿名用户_8a3f, 匿名用户_b2d1
```

---

# 九: 设计风格
简单，大气，清新
**文档结束**
