# project_status

## 项目：医云问 · 中小医疗机构 AI 智能客服 SaaS 平台
## 答辩日期：2026-06-25

---

## 当前阶段
D7 联调（6/22）进行中，核心接口已补齐，演示链路基本跑通

## 已完成内容

### D1 设计阶段
- PRD 提交飞书
- 数据库 11 张表设计 + SQL
- Dify 云端账号注册 + 测试知识库体验

### D2 环境搭建
- docker-compose 跑通（MySQL / Redis / RabbitMQ / ES 全 healthy）
- 项目目录结构初始化
- JWT 登录接口跑通
- 依赖全部安装完毕（asyncmy → aiomysql，bcrypt 锁定 4.0.1）

### D3 后端核心 API
- ORM 建表（10张表全部创建成功）
- 机构注册接口（POST /api/v1/auth/register）
- 真实登录接口（bcrypt 验证 + JWT）
- JWT 依赖注入（get_current_user）
- 机构信息查看（GET /api/v1/organizations/me）
- 机构信息更新（PATCH /api/v1/organizations/me）
- 布隆过滤器（startup 重建 + 公开机构查询接口）
- Redis Cache-Aside（org slug 缓存）

### D4 Dify 对接 + 消息队列
- 知识库文件上传（POST /api/v1/knowledge/upload，转发 Dify API）
- 流式对话接口（POST /api/v1/chat/messages，StreamingResponse + SSE透传）
- 对话记录写 MySQL（conversations + messages 表）
- RabbitMQ 生产者（对话结束后发消息入队）
- ES 消费者（app/workers/es_consumer.py，异步写入 messages 索引）
- 预约接口（POST /api/v1/appointments/）
- Redis 防重复预约（SET NX，key=appt:dedup:{phone}:{slot_id}）
- 分布式锁防超卖（SET NX，key=appt:lock:{slot_id}）

### D5 前端管理后台
- Vue3 项目初始化（Element Plus + Pinia + Vue Router）
- vite.config.ts 配置 @ 路径别名
- main.ts 注册 Element Plus + 图标
- axios 封装（src/api/request.ts，请求拦截器自动带token，响应拦截器静默404/405）
- Pinia auth store（src/stores/auth.ts，token持久化到localStorage）
- 登录页（src/views/LoginView.vue，表单校验 + JWT登录 + 跳转）
- AdminLayout 侧边栏布局（绿色主题 #1D9E75，机构名显示，退出登录）
- 路由守卫（未登录跳转 /login）
- 知识库管理页（文件上传 → 调后端 → 本地插入记录，状态显示processing）
- 预约管理页（表格展示 + 状态筛选 + 确认/取消操作，演示数据兜底）
- 文章管理页（列表 + 新建/编辑弹窗 + 上线/下线 + 删除，演示数据兜底）

### D6 患者端页面
- AI 对话页（/patient/chat?org=slug）
  - 流式 SSE 接收，逐字显示
  - think 标签双重过滤（流式中 + 完整内容）
  - 快捷问题点击发送
  - 多轮对话（dify_conversation_id 传递）
  - 机构名从后端获取显示
  - 立即预约按钮跳转
- 在线预约页（/patient/appointment?org=slug）
  - 4步流程：选科室 → 选时间 → 填信息 → 完成
  - 号源剩余显示，已满不可选
  - 提交调后端接口，失败时本地模拟成功

### D7 联调（今日完成）
- 补齐 GET /api/v1/appointments/（预约列表，joinedload联表，JWT租户隔离）
- 补齐 PATCH /api/v1/appointments/{id}（确认/取消，取消自动释放号源）
- 补齐 Appointment 模型 time_slot relationship
- 新建 backend/app/api/v1/articles.py，实现完整 CRUD：
  - GET /api/v1/articles/（列表）
  - POST /api/v1/articles/（新建）
  - PATCH /api/v1/articles/{id}（编辑内容 + 上线/下线）
  - DELETE /api/v1/articles/{id}（删除）
- main.py 注册 articles router
- DataGrip 插入演示数据（departments 4条 + time_slots 4条）
- 联调验证：登录 ✅ 知识库上传 ✅ AI流式对话 ✅ 预约提交 ✅（数据库写入待最终确认）

## 待完成（明天优先级排序）

### 🔴 P0 明天必须完成
1. **演示链路最终确认**：预约数据真实写入数据库验证，管理后台预约列表从真实接口加载
2. **阿里云 OSS 集成**：
   - 安装 oss2：`pip install oss2`
   - .env 补充配置：OSS_ACCESS_KEY_ID / OSS_ACCESS_KEY_SECRET / OSS_BUCKET_NAME / OSS_ENDPOINT
   - 新建 backend/app/services/oss_service.py
   - 修改 knowledge.py 上传接口：文件同时上传 OSS，oss_url 字段写入真实地址
   - config.py 补充 OSS 配置项读取

### 🟡 P1 时间够再做
3. 答辩话术准备（布隆过滤器、RabbitMQ、多租户隔离、Snapshot Pattern）
4. 检查所有 Docker 服务正常启动
5. 准备演示账号和知识库内容（让 AI 能答得漂亮）

## 当前已知问题
- 预约页科室和时间段仍是前端硬编码演示数据，未对接真实接口
- 知识库文档状态永远显示"处理中"（未轮询 Dify 真实状态）
- Element Plus 按钮主题色未完全生效（部分按钮仍显示蓝色）
- 管理后台预约列表 GET 接口已实现，但前端联调未最终验证

## 演示路径（答辩核心链路）
1. 打开 http://localhost:5173/login，用账号登录
2. 进入知识库管理，展示已上传文档
3. 打开 http://localhost:5173/patient/chat?org=beijing-smile
4. 点快捷问题"洗牙多少钱？"，AI 流式回答
5. 点"立即预约"，走完4步预约流程
6. 回到管理后台 → 预约管理，看到预约记录

## Dify 配置
- API Base: https://api.dify.ai/v1
- App Key: app-KxfWJrD1cf2xFctT75N8tUou（对话用）
- Dataset Key: dataset-X8P2jWQuzG50eLBC7bZISjCN（知识库上传用）
- Dataset ID: 8395d924-128b-4c0e-99d0/50a63d75b507
- App ID: dd20605f-9a8f-4a36-868c-d2d420c98a3f
- 已上传知识库：口腔诊所中文知识库（洗牙价格、就诊流程、营业时间等）

## 启动方式
1. docker-compose up -d（启动基础设施）
2. cd backend && uvicorn app.main:app --reload（启动 FastAPI）
3. python -m app.workers.es_consumer（启动ES消费者，独立终端）
4. cd frontend && npm run dev（启动前端）

## 后端文件结构

backend/app/
├── models/
│   ├── base.py
│   ├── organization.py
│   ├── user.py
│   ├── knowledge.py
│   ├── conversation.py
│   ├── appointment.py        # 新增 time_slot relationship
│   └── article.py
├── schemas/
│   └── auth.py
├── services/
│   ├── dify_service.py
│   └── oss_service.py        # 待新建
├── workers/
│   └── es_consumer.py
├── api/v1/
│   ├── auth.py
│   ├── organizations.py
│   ├── public.py
│   ├── knowledge.py
│   ├── chat.py
│   ├── appointments.py       # 新增 GET + PATCH 接口
│   └── articles.py           # 新增完整 CRUD
└── core/
    ├── deps.py
    ├── security.py
    ├── config.py             # 待补充 OSS 配置项
    ├── database.py
    ├── redis_client.py
    ├── bloom_filter.py
    └── rabbitmq.py

## 前端文件结构

frontend/src/
├── api/request.ts
├── assets/
│   ├── base.css
│   └── main.css
├── components/
│   └── AdminLayout.vue
├── router/index.ts
├── stores/auth.ts
├── views/
│   ├── LoginView.vue
│   ├── admin/
│   │   ├── KnowledgeView.vue
│   │   ├── AppointmentsView.vue
│   │   └── ArticlesView.vue
│   └── patient/
│       ├── ChatView.vue
│       └── AppointmentView.vue
├── App.vue
└── main.ts