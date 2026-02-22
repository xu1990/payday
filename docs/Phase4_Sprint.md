# 薪日 PayDay - Phase 4：Sprint 与任务列表（PRD v1.2）

基于 [PRD_v1.2_detail.md](PRD_v1.2_detail.md) 将 v1.2 版本拆为 6 个 Sprint（每轮 2 周），并列出每轮任务与验收点。v1.2 是薪日 PayDay 从「工资记录社区」向「职场生活+轻理财+成长体系」升级的关键版本。

---

## Phase 4：v1.2 版本（12 周，6 个 Sprint）

**核心目标**：
- ✅ 手机号登录（P0）- 多端统一账号体系
- ✅ 工资用途记录（P1）- 打造「第一笔工资」仪式感
- ✅ 每月支出明细（P1）- 收入-支出-结余闭环
- ✅ 年终奖展示（P1）- 社区互动增强
- ✅ 发薪情绪/延迟记录（P1）- 情绪价值强化
- ✅ 存款目标（P2）- 轻理财属性
- ✅ 打卡功能（P2）- 用户活跃度提升
- ✅ 能力值系统（P2）- 成长体系基础
- ✅ 能力值兑换（P2）- 商业化前置

---

## Sprint 4.1（Week 1–2）：手机号登录 + 工资用途记录

**目标**：手机号登录实现多端统一，第一笔工资用途打造仪式感。

### 后端任务

| 任务 | 说明 | 验收 |
|------|------|------|
| 用户表扩展 | ALTER TABLE users ADD phone_number, phone_verified, ability_points, ability_level, ability_level_updated_at, idx_phone | 迁移成功，字段可查询 |
| 登录接口扩展 | POST /api/v1/auth/login 支持 phoneNumberCode 参数，复用现有 WeChat code2session + JWT 流程 | 可选手机号登录，返回用户信息含 phone 字段 |
| 手机号绑定 | POST /api/v1/user/bind-phone，手机号验证、绑定现有用户、新建用户逻辑 | 未登录/已登录用户均可绑定 |
| 更换手机号 | POST /api/v1/user/change-phone，新手机号 + 短信验证码，解绑旧号 | 可更换并通知用户 |
| 手机号脱敏 | 存储加密（AES-256），展示脱敏（138****8888），管理后台权限审批 | 数据安全合规 |
| 工资用途表 | CREATE TABLE salary_usage_records (id, user_id, salary_record_id, usage_category, usage_subcategory, amount, note, is_first_salary, created_at) | 表结构与索引正确 |
| 用途记录 API | POST /api/v1/salary/:recordId/usage，GET /api/v1/salary/:recordId/usage | 可创建/查询用途记录 |
| 第一笔工资用途 | GET /api/v1/first-salary-usage?limit=20，社区展示，按创建时间排序 | 返回匿名用途列表 |
| 能力值钩子（基础） | 记工资 +10 能力值，复用 salary_service，创建 ability_points_log | 记工资后能力值正确增加 |

### 小程序任务

| 任务 | 说明 | 验收 |
|------|------|------|
| 登录页扩展 | 新增「获取手机号」按钮，<button open-type="getPhoneNumber">，同意授权后调用登录接口 | 授权流程正确，拒绝可降级体验 |
| 设置页手机号 | 显示手机号（脱敏）、绑定状态、更改入口，样式与 PRD 一致 | 可查看/绑定/更换手机号 |
| 手机号绑定弹窗 | 引导文案、授权按钮、跳过逻辑（降级体验） | 与 PRD UI 一致 |
| 工资用途记录页 | 记录第一笔工资后自动弹出引导，用途分类选择（9 个一级分类），金额输入，总计显示 | 与 PRD UI 一致 |
| 用途分类选择器 | 网格布局、图标 + 文字、支持自定义「其他」 | 交互流畅 |
| 分享卡片生成 | 第一笔工资用途 + 金额 + 用途占比 + @薪日 PayDay，canvas 绘制 | 可保存并分享 |
| 社区话题页 | #第一笔工资 话题，用途排行榜（最热门分类），年代对比（80/90/00 后） | 可浏览其他用户用途 |
| API 客户端 | auth.ts（login, bindPhone, changePhone），salary.ts（createUsage, getUsage, getFirstSalaryUsage） | 请求正确封装 |

### 管理后台任务

| 任务 | 说明 | 验收 |
|------|------|------|
| 用户管理扩展 | 用户列表显示手机号（脱敏），搜索支持手机号 | 可通过手机号搜索用户 |
| 用途记录管理 | 列表、详情、删除，关联工资记录 | 可管理用户用途记录 |

### 数据任务

| 任务 | 说明 | 验收 |
|------|------|------|
| 用途分类配置 | 创建 config/salary_usage_categories.json，9 个一级分类 + 二级分类 | 可被前端读取 |
| 能力值规则配置 | 创建 config/ability_points_rules.json，行为与能力值映射 | 配置化能力值规则 |

**交付**：
- ✅ 手机号登录 + 绑定 + 更换
- ✅ 第一笔工资用途记录 + 分享卡片
- ✅ #第一笔工资 社区话题

---

## Sprint 4.2（Week 3–4）：每月支出明细 + 年终奖展示

**目标**：收入-支出-结余财务闭环，年终奖专题社区互动。

### 后端任务

| 任务 | 说明 | 验收 |
|------|------|------|
| 支出记录表 | CREATE TABLE expense_records (id, user_id, salary_record_id, expense_date, category, subcategory, amount, note, created_at) | 表结构与索引正确 |
| 支出 CRUD API | POST /api/v1/salary/:recordId/expenses，GET /api/v1/salary/:recordId/expenses，PUT /api/v1/expenses/:id，DELETE /api/v1/expenses/:id | 可创建/查询/更新/删除支出 |
| 支出统计 API | GET /api/v1/expenses/statistics，支持 startDate/endDate/groupBy（category/month） | 返回分类汇总、月度趋势 |
| 工资类型扩展 | ALTER TABLE salary_records，salary_type ENUM 增加 'year_end_bonus' | 迁移成功 |
| 年终奖帖子 API | POST /api/v1/posts/year-end-bonus，content, months, images, industry, city | 可发布年终奖帖子 |
| 年终奖统计 API | GET /api/v1/statistics/year-end-bonus，返回 byIndustry, byCity, overall | 返回平均月数统计 |
| 年终奖话题 | GET /api/v1/posts?topic=year_end_bonus，筛选年终奖类型帖子 | 返回专题帖子列表 |
| 能力值钩子（扩展） | 记支出 +5 能力值，发布年终奖帖子 +20 能力值 | 能力值正确增加 |
| 薪资加密复用 | 支出金额使用 encryption_service.encrypt_amount() | 加密存储 |

### 小程序任务

| 任务 | 说明 | 验收 |
|------|------|------|
| 支出记录页 | 工资记录后自动引导，显示本月工资收入，支出列表（11 个一级分类），总支出 + 结余 | 与 PRD UI 一致 |
| 支出分类选择器 | 搜索框 + 网格布局（11 个一级分类），图标 + 文字 | 交互流畅 |
| 支出编辑页 | 修改金额、分类、备注，删除支出 | 可编辑已记录支出 |
| 支出统计页 | 本月/上月支出对比，近 6 个月折线图，支出构成（饼图/进度条），收支对比柱状图 | ECharts 图表正确展示 |
| 工资记录页扩展 | 工资类型增加「年终奖」选项 | 可选择年终奖类型 |
| 年终奖专题页 | #晒年终奖 话题标题，参与人数，帖子列表（匿名），「我要晒年终奖」按钮 | 与 PRD UI 一致 |
| 年终奖排行页 | 按行业/城市统计，匿名平均月数排行（🥇🥈🥉） | 可切换行业/城市 |
| API 客户端 | expense.ts（create, list, update, delete, statistics），posts.ts（createYearEndBonus, listByTopic） | 请求正确封装 |
| 图表组件 | ExpenseChart.vue（折线图、饼图、柱状图） | ECharts 封装可复用 |

### 管理后台任务

| 任务 | 说明 | 验收 |
|------|------|------|
| 支出管理 | 用户支出列表、统计汇总、导出 | 可查看所有用户支出 |
| 年终奖统计 | 行业/城市分布图表，平均月数 | 数据可视化 |
| 支出分类配置 | 支出分类管理（11 个一级分类） | 可自定义分类 |

### 数据任务

| 任务 | 说明 | 验收 |
|------|------|------|
| 支出分类配置 | 创建 config/expense_categories.json，11 个一级分类 + 二级分类 | 可被前端读取 |
| 年终奖统计数据 | 定时任务统计年终奖数据（按行业/城市），缓存到 Redis | 统计数据准确 |

**交付**：
- ✅ 每月支出记录 + 统计图表
- ✅ 年终奖专题 + 匿名排行榜
- ✅ 收支对比展示

---

## Sprint 4.3（Week 5–6）：发薪情绪/延迟记录

**目标**：发薪情绪价值强化，准点率统计，行业对比。

### 后端任务

| 任务 | 说明 | 验收 |
|------|------|------|
| 工资记录表扩展 | ALTER TABLE salary_records ADD is_delayed, delayed_days, is_arrears, arrears_amount, mood_note, mood_tags (JSON) | 迁移成功 |
| 工资记录 API 扩展 | POST /api/v1/salary/record 支持新字段，PUT /api/v1/salary/records/:id 支持更新 | 可记录延迟/拖欠/心情 |
| 准点率统计 API | GET /api/v1/statistics/punctuality，返回 userPunctuality（onTimeRate, delayedCount, totalDelayedDays, trend），industryPunctuality | 统计准确 |
| 行业对比数据 | 按行业统计平均准点率（匿名），缓存到 Redis | 数据准确 |
| 心情标签配置 | 创建 config/mood_tags.json，发薪带来的好处标签（8 个预设） | 可被前端读取 |
| 能力值钩子（扩展） | 记录延迟工资 +5 能力值（吐槽奖励） | 能力值正确增加 |

### 小程序任务

| 任务 | 说明 | 验收 |
|------|------|------|
| 工资记录页扩展 | 新增「是否延迟发薪」单选（正常/延迟天数），「是否拖欠」单选（无拖欠/拖欠金额），「这笔工资对你」多选（8 个预设 + 自定义） | 与 PRD UI 一致 |
| 心情标签选择器 | 多选框布局，预设标签（💰可以买买买了、😌心里踏实了、💳可以还花呗等） | 交互流畅 |
| 准点率统计页 | 本月准点率（进度条），延迟次数/天数，近 6 个月趋势折线图，行业对比（匿名） | 与 PRD UI 一致 |
| 延迟吐槽帖子 | 记录延迟工资后自动引导发帖，预填内容「公司又延迟发薪了 X 天...」 | 一键发帖吐槽 |
| API 客户端 | salary.ts（create 扩展），statistics.ts（getPunctuality） | 请求正确封装 |
| 图表组件 | PunctualityChart.vue（准点率折线图、行业对比柱状图） | ECharts 封装可复用 |

### 管理后台任务

| 任务 | 说明 | 验收 |
|------|------|------|
| 延迟工资统计 | 全站延迟统计，行业/城市分布，延迟 Top 企业（匿名） | 数据可视化 |
| 工资记录审核 | 延迟/拖欠记录列表，人工核实 | 可管理异常记录 |

### 数据任务

| 任务 | 说明 | 验收 |
|------|------|------|
| 准点率统计任务 | 定时任务（每日凌晨）计算用户准点率，缓存到 Redis punctuality:status:{user_id}:{month} | 统计准确 |
| 行业统计任务 | 定时任务（每周）统计行业准点率，缓存到 Redis punctuality:industry:{industry} | 统计准确 |

**交付**：
- ✅ 发薪情绪扩展（延迟/拖欠/心情标签）
- ✅ 准点率统计 + 趋势图
- ✅ 行业对比（匿名）

---

## Sprint 4.4（Week 7–8）：存款目标 + 打卡功能

**目标**：轻理财属性养成，用户活跃度提升（打卡）。

### 后端任务

| 任务 | 说明 | 验收 |
|------|------|------|
| 存款目标表 | CREATE TABLE savings_goals (id, user_id, goal_name, target_amount, current_amount, goal_type, monthly_target, percentage, icon, is_active, achieved_at, created_at, updated_at) | 表结构与索引正确 |
| 存款记录表 | CREATE TABLE savings_records (id, user_id, goal_id, salary_record_id, amount, record_date, note, created_at) | 表结构与索引正确 |
| 存款目标 API | POST /api/v1/savings/goals，GET /api/v1/savings/goals，PUT /api/v1/savings/goals/:id，DELETE /api/v1/savings/goals/:id | 可 CRUD 存款目标 |
| 存款记录 API | POST /api/v1/savings/records，GET /api/v1/savings/records?goalId=xxx | 可记录/查询存款 |
| 存款统计 API | GET /api/v1/savings/statistics，返回 totalGoals, achievedGoals, totalSaved, monthlyProgress | 统计准确 |
| 打卡表 | CREATE TABLE check_ins (id, user_id, check_in_type, check_in_date, overtime_hours, note, reward_points, consecutive_days, created_at)，UNIQUE KEY uk_user_date_type | 表结构与索引正确 |
| 打卡 API | POST /api/v1/check-in，GET /api/v1/check-in/records，GET /api/v1/check-in/statistics，GET /api/v1/check-in/today | 可打卡/查询记录/统计 |
| 打卡奖励逻辑 | 加班打卡 +5，发薪打卡 +10，存款打卡 +20，连续打卡 +N*2，每日上限 3 次 | 奖励计算正确 |
| 连续天数计算 | 查询用户打卡记录，计算连续天数（断日重置） | 逻辑正确 |
| 能力值钩子（扩展） | 打卡 +5 能力值，完成存款目标 +50 能力值 | 能力值正确增加 |
| 目标达成逻辑 | current_amount >= target_amount 时更新 achieved_at，发送通知 | 自动检测并通知 |

### 小程序任务

| 任务 | 说明 | 验收 |
|------|------|------|
| 存款目标设置页 | 目标金额、目标类型（固定/比例）、每月目标/比例、目标名称、图标选择（🏠💰🚗等） | 与 PRD UI 一致 |
| 存款目标列表页 | 个人中心入口，卡片展示目标（名称、进度、已存/目标），点击进入详情 | 可查看所有目标 |
| 存款目标详情页 | 目标金额、已存金额、进度条、柱状图（每月进度），本月目标（目标/实际/还差），历史记录（达成/未达成） | 与 PRD UI 一致 |
| 存款记录引导 | 工资记录后自动引导「记录到存款目标」，选择目标 + 输入金额 | 一键记录存款 |
| 打卡主页 | 今日连续打卡天数（🔥），打卡卡片（加班/发薪/存款），打卡日历（显示打卡记录） | 与 PRD UI 一致 |
| 加班打卡卡 | 输入加班小时数，立即打卡按钮 | 可打卡 |
| 发薪打卡卡 | 今天发薪啦文案，立即打卡按钮 | 可打卡 |
| 打卡成功页 | ✅ 打卡成功，能力值 +X，已连续打卡 X 天，分享/继续打卡按钮 | 动画流畅 |
| 打卡日历 | 日历视图，显示打卡记录（不同类型不同图标），月份切换 | 可查看历史打卡 |
| API 客户端 | savings.ts（goals, records, statistics），checkin.ts（checkIn, records, statistics, today） | 请求正确封装 |
| 组件 | SavingsProgress.vue（进度条），CheckinCard.vue（打卡卡片），Calendar.vue（打卡日历） | 组件可复用 |

### 管理后台任务

| 任务 | 说明 | 验收 |
|------|------|------|
| 存款目标管理 | 用户目标列表，达成统计 | 可查看所有用户目标 |
| 打卡管理 | 打卡记录列表，打卡统计（连续天数分布） | 可查看打卡数据 |
| 打卡配置 | 打卡类型配置，奖励能力值配置 | 可自定义打卡规则 |

### 数据任务

| 任务 | 说明 | 验收 |
|------|------|------|
| 目标图标配置 | 创建 config/savings_goal_icons.json，图标列表（🏠💰🚗✈️📱💻等） | 可被前端读取 |
| 打卡类型配置 | 创建 config/checkin_types.json，打卡类型 + 奖励规则 | 配置化打卡规则 |

**交付**：
- ✅ 存款目标（固定/比例）+ 进度追踪
- ✅ 打卡功能（加班/发薪/存款）+ 连续天数
- ✅ 打卡日历视图

---

## Sprint 4.5（Week 9–10）：能力值系统 + 能力值兑换

**目标**：能力值成长体系，能力值商城商业化前置。

### 后端任务

| 任务 | 说明 | 验收 |
|------|------|------|
| 能力值日志表 | CREATE TABLE ability_points_logs (id, user_id, points_change, action_type, target_id, description, created_at) | 表结构与索引正确 |
| 用户表扩展 | 已在 Sprint 4.1 完成（ability_points, ability_level, ability_level_updated_at） | - |
| 能力值服务 | AbilityService.add_points(user_id, action, points, target_id, description)，自动更新 level，写入日志 | 服务可调用 |
| 能力值等级规则 | LEVEL_1（职场新人 0-99），LEVEL_2（打工小白 100-499），LEVEL_3（熟练工 500-999），LEVEL_4（职场老手 1000-2999），LEVEL_5（打工皇帝 3000+） | 等级计算正确 |
| 能力值 API | GET /api/v1/user/ability-points（返回 currentPoints, level, levelName, nextLevelPoints, progress, todayGained, todayActions），GET /api/v1/user/ability-points/logs，GET /api/v1/leaderboard/ability-points | 接口返回正确 |
| 能力值排行榜 | Redis ZSet leaderboard:ability_points:total，leaderboard:ability-points:daily，leaderboard:ability-points:weekly，leaderboard:ability-points:monthly | 排行榜实时更新 |
| 能力值钩子（全量） | 登录 +1，记工资 +10，记支出 +5，发帖 +20，评论 +5，点赞 +1，被点赞 +2，被关注 +10，打卡 +5，完成存款目标 +50，邀请好友 +100 | 所有点位集成完成 |
| 每日限制逻辑 | 发布帖子 10 次/天，评论 20 次/天，点赞 50 次/天，打卡 3 次/天，邀请好友 10 人 | 限制正确执行 |
| 奖励物品表 | CREATE TABLE reward_items (id, name, category, description, image_url, points_cost, stock_count, is_active, sort_order, created_at, updated_at) | 表结构与索引正确 |
| 奖励订单表 | CREATE TABLE reward_orders (id, user_id, reward_item_id, points_used, status, shipping_info, shipping_name, shipping_phone, shipping_address, note, created_at, updated_at) | 表结构与索引正确 |
| 奖励商城 API | GET /api/v1/reward/items（category, page, pageSize），GET /api/v1/reward/items/:id | 可查询商城物品 |
| 兑换 API | POST /api/v1/reward/orders，检查能力值是否足够，扣除能力值，创建订单（status=pending） | 可兑换物品 |
| 订单 API | GET /api/v1/reward/orders（status, page），GET /api/v1/reward/orders/:id，POST /api/v1/reward/orders/:id/cancel，POST /api/v1/reward/orders/:id/confirm | 可管理订单 |
| 库存扣减逻辑 | 兑换时原子扣减 stock_count，使用数据库行锁或 Redis 分布式锁 | 库存不超卖 |

### 小程序任务

| 任务 | 说明 | 验收 |
|------|------|------|
| 个人中心扩展 | 显示等级（🏆熟练工），能力值（1,280 / 3,000），进度条，查看详情入口 | 与 PRD UI 一致 |
| 能力值明细页 | 当前能力值，距下一等级，获取记录（按日期分组），今日获取能力值列表（✅完成 ⬜未完成） | 与 PRD UI 一致 |
| 能力值排行榜页 | 日榜/周榜/月榜/总榜 Tab，Top 100 列表（排名、匿名昵称、能力值），自己排名高亮 | 与 PRD UI 一致 |
| 能力值商城 | 分类 Tab（全部/礼包/超市卡/劳保），物品卡片（图片、名称、描述、库存、能力值价格），立即兑换按钮 | 与 PRD UI 一致 |
| 物品详情页 | 物品图片、名称、描述、库存、所需能力值、立即兑换按钮 | 与 PRD UI 一致 |
| 兑换确认页 | 物品信息，兑换详情，所需能力值，当前余额，确认兑换按钮（不足时提示） | 与 PRD UI 一致 |
| 兑换成功页 | 🎉 兑换成功，发货说明（3 个工作日内），快递信息通知，查看订单/继续逛按钮 | 与 PRD UI 一致 |
| 我的订单页 | 订单列表（全部/待发货/已发货/已完成/已取消 Tab），订单卡片（物品、状态、时间），点击进入详情 | 可查看订单 |
| 订单详情页 | 订单信息，物品信息，物流信息（快递单号、状态），确认收货按钮（已发货时） | 与 PRD UI 一致 |
| API 客户端 | ability.ts（getPoints, getLogs, getLeaderboard），reward.ts（getItems, getItemDetail, createOrder, getOrders, getOrderDetail, cancelOrder, confirmOrder） | 请求正确封装 |
| 组件 | AbilityBar.vue（能力值进度条），RewardItem.vue（物品卡片），OrderCard.vue（订单卡片） | 组件可复用 |

### 管理后台任务

| 任务 | 说明 | 验收 |
|------|------|------|
| 能力值管理 | 用户能力值列表，能力值日志查询，排行榜 | 可查看所有用户能力值 |
| 奖励物品管理 | 物品列表，添加/编辑物品（名称、分类、描述、图片、能力值价格、库存），上架/下架 | 可管理商城物品 |
| 订单管理 | 订单列表（全部/待处理/已发货/已完成/已取消 Tab），订单详情，发货（填写快递信息），取消订单 | 可管理订单 |
| 库存预警 | 库存 < 10 的物品列表，低库存提醒 | 可查看低库存物品 |
| 订单统计 | 兑换统计（今日/本周/本月），热门物品排行，能力值消耗统计 | 数据可视化 |

### 数据任务

| 任务 | 说明 | 验收 |
|------|------|------|
| 能力值规则配置 | 扩展 config/ability_points_rules.json，所有行为与能力值映射 + 每日限制 | 配置完整 |
| 奖励分类配置 | 创建 config/reward_categories.json，分类列表（礼包/超市卡/劳保/虚拟物品） | 可被前端读取 |
| 排行榜缓存任务 | 定时任务（每小时）更新排行榜到 Redis ZSet | 排行榜实时更新 |

**交付**：
- ✅ 能力值系统（等级、获取、日志、排行榜）
- ✅ 能力值商城（物品浏览、兑换、订单管理）
- ✅ 订单系统（发货、确认收货）

---

## Sprint 4.6（Week 11–12）：集成测试 + 上线准备

**目标**：全模块集成测试、性能优化、安全审计、文档完善、上线部署。

### 测试任务

| 任务 | 说明 | 验收 |
|------|------|------|
| 集成测试 | 编写端到端测试用例，覆盖所有新增模块（手机号、用途、支出、年终奖、延迟、存款、打卡、能力值、兑换） | 测试用例通过率 100% |
| 性能测试 | 压力测试关键接口（登录、工资记录、支出统计、打卡、兑换），QPS 目标 500+ | 性能达标 |
| 安全审计 | 手机号加密存储验证，金额加密验证，SQL 注入检查，XSS 检查，权限检查 | 安全漏洞修复 |
| 数据一致性 | 能力值钩子一致性测试（所有行为能力值是否正确），库存扣减并发测试，连续打卡逻辑测试 | 数据一致无异常 |

### 优化任务

| 任务 | 说明 | 验收 |
|------|------|------|
| 数据库查询优化 | 慢查询分析，索引优化，N+1 查询优化 | 查询时间 < 500ms |
| 缓存优化 | 热点数据缓存（用户信息、能力值、排行榜、库存），缓存命中率 > 80% | 缓存生效 |
| 接口响应优化 | 接口响应时间优化，目标 P95 < 1s | 响应时间达标 |
| 前端性能优化 | 组件懒加载，图片懒加载，首屏加载优化 | 首屏加载 < 2s |

### 文档任务

| 任务 | 说明 | 验收 |
|------|------|------|
| API 文档 | 更新 Swagger/OpenAPI 文档，所有新增接口标注完整 | 文档完整准确 |
| 部署文档 | 更新部署文档，新增模块部署步骤，数据库迁移步骤 | 文档可执行 |
| 用户手册 | 小程序用户使用手册（帮助中心） | 用户可自助查阅 |

### 管理后台任务

| 任务 | 说明 | 验收 |
|------|------|------|
| 全模块管理页面 | 补全所有模块管理页面（用途、支出、年终奖、延迟、存款、打卡、能力值、兑换） | 可管理所有模块 |
| 数据大盘 | 新增 v1.2 数据大盘，展示所有模块关键指标（手机号绑定率、用途记录数、支出统计、年终奖统计、准点率、存款目标达成率、打卡活跃度、能力值分布、兑换统计） | 数据可视化 |
| 运营配置中心 | 统一运营配置（用途分类、支出分类、心情标签、打卡类型、能力值规则、奖励分类） | 可配置化 |

### 上线准备任务

| 任务 | 说明 | 验收 |
|------|------|------|
| 数据库迁移准备 | 生产环境迁移脚本 review，回滚方案准备 | 可安全迁移 |
| 灰度发布方案 | 灰度发布计划（按用户 ID 分段灰度），监控指标 | 可灰度发布 |
| 监控告警 | 新增模块监控告警（接口错误率、能力值异常、库存异常、订单异常） | 可及时发现问题 |
| 应急预案 | 回滚预案，数据修复脚本，客服 FAQ | 可快速响应问题 |

### 验收任务

| 任务 | 说明 | 验收 |
|------|------|------|
| 功能验收 | 按 PRD v1.2 逐项验收所有功能 | 功能无遗漏 |
| 性能验收 | 接口响应时间、并发能力、数据库负载 | 性能达标 |
| 安全验收 | 数据加密、权限控制、SQL 注入、XSS | 安全无漏洞 |
| 兼容性验收 | 微信小程序版本兼容，iOS/Android 兼容 | 兼容性良好 |
| 用户体验验收 | 交互流畅度，UI 一致性，错误提示友好 | 用户体验良好 |

**交付**：
- ✅ 集成测试通过
- ✅ 性能优化完成
- ✅ 安全审计通过
- ✅ 文档完善
- ✅ 管理后台全模块可用
- ✅ 上线准备就绪

---

## 与模块技术方案对应关系

### Phase 4 新增模块
- **手机号登录**：Sprint 4.1（复用 auth_service，扩展 users 表）
- **工资用途记录**：Sprint 4.1（新建 salary_usage_records 表，复用 salary_service 模式）
- **每月支出明细**：Sprint 4.2（新建 expense_records 表，复用 encryption_service，复用 pagination）
- **年终奖展示**：Sprint 4.2（扩展 salary_records.salary_type，复用 post_service）
- **发薪情绪/延迟**：Sprint 4.3（扩展 salary_records 表，新增 punctuality 统计）
- **存款目标**：Sprint 4.4（新建 savings_goals + savings_records 表）
- **打卡功能**：Sprint 4.4（新建 check_ins 表，连续天数逻辑）
- **能力值系统**：Sprint 4.5（扩展 users 表，新建 ability_points_logs 表，钩子系统）
- **能力值兑换**：Sprint 4.5（新建 reward_items + reward_orders 表，复用 membership 订单模式）

### 复用现有模块
- **认证授权**：复用 app/core/security.py，JWT + scope
- **数据加密**：复用 app/utils/encryption.py，金额加密
- **异常处理**：复用 app/core/exceptions.py，统一异常
- **服务层模式**：复用 app/services/ 模式，业务逻辑分离
- **缓存策略**：复用 Redis 缓存模式，user:info, payday:status 等
- **异步任务**：复用 Celery，定时任务、队列任务
- **前端组件**：复用 miniapp/components/，LazyImage, Loading, EmptyState
- **前端状态**：复用 Pinia stores 模式
- **前端 API**：复用 api/ 封装模式

---

## 依赖关系说明

### Sprint 间依赖
- Sprint 4.1 是基础（手机号登录、能力值基础表）
- Sprint 4.2 依赖 Sprint 4.1（支出关联工资记录，年终奖复用帖子）
- Sprint 4.3 依赖 Sprint 4.1（延迟工资扩展工资记录表）
- Sprint 4.4 依赖 Sprint 4.1（存款关联工资记录，打卡获取能力值）
- Sprint 4.5 依赖 Sprint 4.1+4.2+4.3+4.4（能力值钩子全量集成）
- Sprint 4.6 依赖所有前置 Sprint（集成测试）

### 模块间依赖
- **能力值** 依赖所有模块（钩子集成）
- **打卡** 依赖工资记录（发薪打卡）、存款目标（存款打卡）
- **存款** 依赖工资记录（可选关联）
- **支出** 依赖工资记录（强制关联）
- **用途** 依赖工资记录（强制关联）
- **年终奖** 复用帖子系统
- **延迟** 扩展工资记录

---

## 关键技术决策

### 代码复用策略
1. **服务层复用**：所有新服务遵循现有 service 层模式
2. **数据模型复用**：扩展现有表而非新建表（如 salary_records, users）
3. **加密复用**：所有金额字段使用 encryption_service
4. **异常处理复用**：统一使用 app/core/exceptions.py
5. **API 模式复用**：统一使用 Pydantic schemas，统一返回格式
6. **前端组件复用**：尽量复用现有组件（LazyImage, Loading 等）
7. **前端 API 复用**：遵循现有封装模式
8. **前端状态复用**：遵循 Pinia stores 模式

### 数据安全策略
1. **手机号加密**：AES-256 加密存储，脱敏展示
2. **金额加密**：复用现有 encryption_service
3. **敏感信息权限**：管理后台需权限审批查看
4. **日志脱敏**：能力值日志不记录敏感信息

### 性能优化策略
1. **缓存优先**：用户信息、能力值、排行榜、库存
2. **异步处理**：能力值增加、库存扣减、通知发送
3. **数据库索引**：所有新表建立合理索引
4. **分页查询**：所有列表接口支持分页

### 可扩展性策略
1. **配置化**：分类、规则、配置均使用 JSON 文件
2. **钩子系统**：能力值使用钩子模式，易于扩展
3. **服务解耦**：各模块服务独立，易于维护
4. **接口版本化**：所有新接口使用 /api/v1/ 前缀

---

## 验收标准总结

### Sprint 4.1 验收
- [ ] 手机号登录流程完整
- [ ] 第一笔工资用途记录 + 分享
- [ ] 能力值基础系统可用
- [ ] 社区话题 #第一笔工资 可浏览

### Sprint 4.2 验收
- [ ] 支出记录 + 统计图表
- [ ] 年终奖专题 + 排行榜
- [ ] 收支对比展示
- [ ] 能力值钩子（记工资、记支出、发帖）

### Sprint 4.3 验收
- [ ] 发薪情绪扩展（延迟/拖欠/心情标签）
- [ ] 准点率统计 + 趋势
- [ ] 行业对比（匿名）
- [ ] 能力值钩子（延迟吐槽）

### Sprint 4.4 验收
- [ ] 存款目标 + 进度追踪
- [ ] 打卡功能 + 连续天数
- [ ] 打卡日历视图
- [ ] 能力值钩子（打卡、完成存款目标）

### Sprint 4.5 验收
- [ ] 能力值系统完整（等级、日志、排行榜）
- [ ] 能力值商城 + 兑换
- [ ] 订单系统
- [ ] 能力值钩子全量集成

### Sprint 4.6 验收
- [ ] 集成测试通过率 100%
- [ ] 性能达标（P95 < 1s）
- [ ] 安全审计通过
- [ ] 文档完善
- [ ] 管理后台全模块可用
- [ ] 上线准备就绪

---

**文档版本**: v1.0
**创建日期**: 2026-02-21
**对应 PRD**: PRD_v1.2_detail.md
**预计工期**: 12 周（6 个 Sprint）
**编写人**: Technical Architect

---

**文档结束**
