智能液态界面设计系统 - 颜色规范 v2.0.6
一、设计哲学：色彩的“情绪感知”模型
本系统的色彩并非静态定义，而是遵循 “环境响应式” 原则。颜色会根据环境光传感器、用户情绪（通过输入节奏推断） 以及使用场景进行 ±5% 以内的动态漂移，以确保品牌识别度的同时，提供最舒适的视觉体验。

二、品牌核心色
Primary Palette
这组颜色定义了品牌的视觉身份。在界面中占比约 20%，主要用于核心Logo、关键行动点（Primary Button）和重要引导元素。

色样	色值 (HEX)	色值 (OKLCH) *推荐	Token 名称	应用场景
🟦	#4A6CF7	oklch(60% 0.18 270)	--brand-primary	品牌主色、默认按钮、选中状态
🟪	#9D7BFF	oklch(65% 0.16 290)	--brand-secondary	强调色、图标渐变起点、链接
🔵	#2A4AF0	oklch(50% 0.2 265)	--brand-primary-strong	悬停状态、深色背景下的品牌色
使用规则：

液态渐变： 主色与辅色常搭配使用，形成 120° 的线性渐变，模拟玻璃上的环境光反射。

动态调整： 在深色模式下，品牌色的明度（Lightness）自动提升 5%，以保持与深色背景的对比度。

三、语义色系统
Feedback & Status
用于传达信息、成功、警告和错误状态。所有语义色均需遵循 WCAG 2.2 无障碍标准。

色样	色值 (HEX)	Token 名称	对比度标准	应用场景
🟩	#00C48C	--semantic-success	AAA (7:1)	成功提示、完成状态、正向增长
🟥	#FF5C5C	--semantic-error	AAA (7:1)	错误提示、删除操作、重要警告
🟨	#FFB443	--semantic-warning	AA (4.5:1)	警示信息、等待确认、低电量
🟦	#54A0FF	--semantic-info	AA (4.5:1)	信息提示、帮助引导、通知角标
特殊规则：

玻璃背景适配： 当语义色放置在毛玻璃效果之上时，需额外添加 5% 的白色叠加层，确保色彩不因背景模糊而发灰。

四、液态玻璃中性色
Glass Neutrals
这组颜色是界面的“骨架”，用于背景、卡片、文字和分割线。通过精密的透明度层级，营造出深邃的玻璃质感。

4.1 背景层 (Background Layers)
基于 #FFFFFF 或 #000000 背景

透明度层	浅色模式 (HEX/RGBA)	深色模式 (HEX/RGBA)	Token 名称	用途
0%	#FFFFFF	#0A0C14	--bg-base	最底层画布
15%	rgba(0,0,0,0.02)	rgba(255,255,255,0.02)	--bg-glass-subtle	极隐晦的底纹
40%	rgba(255,255,255,0.4) + 模糊	rgba(20,25,40,0.7) + 模糊	--bg-glass-standard	标准卡片、对话框（需配合背景模糊）
70%	rgba(255,255,255,0.7) + 模糊	rgba(10,15,30,0.85) + 模糊	--bg-glass-prominent	导航栏、顶部操作区
4.2 边框与分割 (Borders & Strokes)
透明度层	浅色模式 (RGBA)	深色模式 (RGBA)	Token 名称	用途
10%	rgba(0,0,0,0.1)	rgba(255,255,255,0.08)	--border-subtle	分割线、网格线
20%	rgba(0,0,0,0.2)	rgba(255,255,255,0.15)	--border-regular	卡片描边、输入框边框
50% (高光)	rgba(255,255,255,0.5)	rgba(255,255,255,0.1)	--border-glow	玻璃边缘高光（用于顶部边缘）
4.3 文字层级 (Text Hierarchy)
使用透明度来区分信息层级，而非直接使用灰色。

透明度层	浅色模式 (基于 #000)	深色模式 (基于 #FFF)	Token 名称	用途
90%	rgba(0,0,0,0.9)	rgba(255,255,255,0.92)	--text-primary	标题、正文、重要信息
60%	rgba(0,0,0,0.6)	rgba(255,255,255,0.65)	--text-secondary	辅助信息、标签、说明文字
35%	rgba(0,0,0,0.35)	rgba(255,255,255,0.4)	--text-tertiary	占位符、禁用状态、时间戳
15%	rgba(0,0,0,0.12)	rgba(255,255,255,0.15)	--text-disabled	完全禁用的文本
五、动态功能色
AI & Gradient Accents
这组颜色专为“生成式 UI”和动态场景准备，用于表达AI的活性、数据流动和视觉钩子。

色样	色值 (HEX)	Token 名称	用途
🌈	#4A6CF7 / #9D7BFF / #FFB443	--gradient-ai-core	AI 生成内容的标识、加载时的流光效果
🌀	#00C4CC	--accent-cyan	数据流动画、连接状态
🌟	#FFD966	--accent-gold	新功能引导、会员权益、高亮标记
动态规则：

呼吸效果： 当 AI 正在工作时，--gradient-ai-core 会以 3s 为周期在色环上缓慢偏移，营造出“思考”的视觉反馈。

情绪映射： 若系统检测到用户情绪低落（如输入速度变慢、删除频率变高），--accent-gold 的饱和度会轻微提升，以提供温暖感。

六、无障碍与包容性
6.1 对比度标准
所有颜色组合必须满足以下标准（可在 Figma 中使用 Stark 插件验证）：

正文（<18pt）： 对比度 ≥ 4.5:1

大文本（>18pt 粗体 或 >24pt）： 对比度 ≥ 3:1

UI 组件（图标、描边）： 对比度 ≥ 3:1

6.2 高对比度模式
当用户开启系统高对比度模式时，所有透明度和毛玻璃效果将被覆盖为纯色：

所有 rgba() 透明度颜色转换为最接近的纯色（HEX）。

文字颜色变为纯黑 (#000000) 或纯白 (#FFFFFF)。

品牌色保持不变，但需确保与背景对比度 ≥ 7:1。

七、颜色 token 命名规范
建议在代码和设计工具中采用以下层级命名，以便于维护：

css
/* 类别-用途-状态-场景 */
:root {
  /* 品牌色 */
  --brand-primary-default: #4A6CF7;
  --brand-primary-hover: #2A4AF0;
  
  /* 背景色 */
  --background-glass-card: rgba(255,255,255,0.4);
  --background-glass-nav: rgba(255,255,255,0.7);
  
  /* 文字色 */
  --text-primary-light: rgba(0,0,0,0.9);
  --text-primary-dark: rgba(255,255,255,0.92);
  
  /* 语义色 - 深色模式变量 */
  --semantic-success-dark: #00BFA5;
}
