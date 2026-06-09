# Task 10：前端界面开发（7.5天）

> Vue3 项目搭建、5 个页面全量开发、设计系统、SSE 流式对话

---

## 10.1 项目初始化

- [x] 选择框架：Vue3 + Vite + Pinia + Element Plus + ECharts
- [x] 项目结构：src/api / components / views / stores / router / styles
- [x] 依赖安装：axios / echarts / markdown-it / highlight.js

## 10.2 设计系统

- [x] CSS 变量体系（styles/tokens.css）— Deep Space Academy 暗色主题
- [x] Element Plus 暗色主题完整覆盖（styles/element-overrides.css）
- [x] 页面过渡动画（styles/transitions.css）
- [x] 关键帧动画（styles/animations.css）— pulse-ring / shimmer / float
- [x] 粒子网络背景（components/background/ParticleField.vue）
- [x] 动态渐变光晕（components/background/AnimatedGradient.vue）
- [x] SVG spark logo + 脉冲光环（components/branding/Logo.vue）
- [x] 打字机文字动画（components/effects/TypewriterText.vue）

## 10.3 布局组件

- [x] 玻璃态侧边栏布局（AppLayout.vue — 64px→220px hover展开）
- [x] 侧边栏导航（AppSidebar.vue — 图标+文字，hover展开动画）
- [x] 玻璃态顶栏（AppHeader.vue）

## 10.4 对话界面（Chat.vue）

- [x] SSE 流式连接 + 逐字显示
- [x] 消息气泡（MessageBubble.vue — Markdown渲染 + 语法高亮）
- [x] Agent 状态面板（AgentStatusPanel.vue — 脉冲动画 + 进度条）
- [x] 自动增高输入框（ChatInput.vue）
- [x] AbortController 切换对话中断旧连接
- [x] Agent 名称映射：profile/tutor/resource/path/evaluation

## 10.5 学习画像展示（Profile.vue）

- [x] ECharts 6维度雷达图
- [x] 3x2 维度卡片网格（百分比 + 进度条 + 描述文字）
- [x] 空状态引导（"去对话页面与AI聊聊"）
- [x] NaN 防护（Number.isFinite + safeScore）

## 10.6 资源卡片化展示（Resources.vue）

- [x] 5种资源类型分类 pill 筛选（文档/题库/导图/代码/视频）
- [x] 玻璃态卡片网格 + 详情弹窗
- [x] 课程筛选 + 空状态
- [x] 创建时间/进度显示

## 10.7 学习路径可视化（LearningPath.vue）

- [x] SVG 进度环
- [x] 路径卡片网格
- [x] 时间线弹窗（含每个步骤的详情）
- [x] 知识点标签
- [x] 跨组件自动刷新（usePathRefresh）

## 10.8 登录/注册界面（Login.vue）

- [x] 分屏布局（左：品牌展示 + 打字机文案 / 右：登录注册Tab）
- [x] 粒子背景
- [x] 玻璃态卡片
- [x] Token 存储 + 路由守卫

## 10.9 API 封装与路由

- [x] axios 拦截器（token 自动注入 + 401 自动跳转登录）
- [x] vue-router 路由配置（5个页面 + 路由守卫）
- [x] 响应式布局适配

---

## 输出物

- [x] 前端项目代码（Vue3 + Vite + Pinia + Element Plus + ECharts）
- [x] 完整设计系统（Deep Space Academy 暗色主题）
- [x] 5个页面全部完成（Login / Chat / Profile / Resources / LearningPath）
- [x] 组件库（AppLayout / AppSidebar / MessageBubble / AgentStatusPanel 等）
- [x] SSE 流式对话 + Agent 状态可视化
- [x] 路由守卫 + API 封装

---

> **实际状态**：已完成。5个页面全部开发完毕，设计系统完整，SSE流式对话 + Agent状态可视化 + 雷达图/卡片/路径展示全部就绪。
