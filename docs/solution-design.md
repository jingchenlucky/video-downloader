# 视频下载平台方案设计（当前实现 + 演进蓝图）

## 1. 文档目标

定义系统的技术方案、模块边界、数据模型、接口契约与演进路径，帮助后续开发者或 AI 在不破坏现有能力的前提下持续扩展。

---

## 2. 技术栈与部署形态

### 2.1 技术栈
- 前端：Vue 3 + Vite
- 后端：FastAPI
- 下载引擎：yt-dlp
- 媒体合并：ffmpeg（通过系统路径 / `FFMPEG_PATH` / `imageio-ffmpeg` 解析）

### 2.2 当前部署形态
- 前后端本地开发模式（前端 dev server + 后端 API）
- 文件存储使用本地目录：`backend/downloads`
- 任务状态主要使用进程内存字典

---

## 3. 架构设计

### 3.1 逻辑分层

1. **展示层（Frontend）**
   - 提供下载操作入口、任务列表与统计展示
   - 通过轮询 `/api/tasks` 刷新状态

2. **接口层（FastAPI Router）**
   - 接收请求、参数校验、统一返回结构
   - 提供健康检查、解析、下载、任务查询等 API

3. **任务管理层（Task Store）**
   - 内存任务创建、更新、查询、状态流转
   - 合并文件系统完成任务，形成对外统一任务视图

4. **下载执行层（yt-dlp Wrapper）**
   - 封装 yt-dlp 参数策略与进度回调
   - 处理格式不可用回退、异常映射

5. **文件层（Local FS）**
   - 下载落盘
   - 从 `downloads` 目录反向构建“历史完成任务”

---

## 4. 核心流程设计

### 4.1 视频信息解析
`POST /api/video/info`
1. 校验 URL
2. 调用 yt-dlp `extract_info(download=False)`
3. 规范化输出：标题、统计、格式列表、推荐格式

### 4.2 单视频下载
`POST /api/video/download`
1. 根据 `format_id` 构建下载参数
2. 调用 yt-dlp 下载
3. 若格式不可用，回退默认格式重试
4. 返回完成结果（标题、输出路径）

### 4.3 批量下载（异步）
`POST /api/video/download/batch`
1. 遍历 URL 创建任务（状态 `queued`）
2. 通过后台任务触发下载线程
3. 进度回调更新任务（`downloading` -> `completed/failed`）

### 4.4 任务列表查询
`GET /api/tasks`
1. 读取内存任务
2. 扫描 `downloads` 目录，生成文件系统完成任务
3. 以 `output_file` 去重合并
4. 按时间倒序返回

---

## 5. 数据模型（建议作为统一契约）

## 5.1 Task
- `task_id: string`
- `url: string`
- `format_id: string | null`
- `status: queued | downloading | completed | failed`
- `progress: number (0-100)`
- `downloaded_bytes: number`
- `total_bytes: number | null`
- `speed: number | null`
- `eta: number | null`
- `title: string | null`
- `output_file: string | null`
- `error: string | null`
- `created_at: ISO datetime`
- `updated_at: ISO datetime`

### 5.2 状态机定义
- 初始：`queued`
- 运行：`downloading`
- 结束：`completed` 或 `failed`
- 不允许从终态回到运行态（除非新建重试任务）

---

## 6. API 设计约定

### 6.1 统一约定
- 成功：HTTP 2xx + JSON 正文
- 业务错误：HTTP 4xx + `detail`
- 系统错误：HTTP 5xx + `detail`

### 6.2 兼容性约束
- 增加字段可向后兼容
- 修改字段语义或删除字段必须走版本策略（如 `/api/v2`）
- 前端依赖字段需在设计文档同步更新

---

## 7. 可扩展设计（推荐落地顺序）

### 7.1 阶段 A：稳态化（低成本）
- 提取 `task_service.py`、`download_service.py`，降低 `main.py` 复杂度
- 引入 `schemas.py`，统一请求/响应与状态枚举
- 增加日志与基础单元测试

### 7.2 阶段 B：持久化
- 接入 SQLite（后续可迁移 PostgreSQL）
- 任务与下载文件建立表结构：
  - `download_tasks`
  - `download_artifacts`
- 重启后完整恢复任务历史（不仅仅是文件扫描）

### 7.3 阶段 C：队列化
- 引入 Redis + Celery/RQ
- API 仅负责创建任务，Worker 执行下载
- 支持取消、重试、并发配额和优先级

### 7.4 阶段 D：实时化与平台化
- WebSocket/SSE 推送进度，减少轮询
- 用户系统与权限隔离
- 对象存储（S3/OSS）与临时下载链接

---

## 8. 目录重构建议（目标形态）

```text
backend/
  app/
    main.py
    api/
      health.py
      video.py
      tasks.py
    services/
      task_service.py
      download_service.py
      media_service.py
    models/
      task.py
    repositories/
      task_repo.py
    core/
      config.py
      logger.py
frontend/
  src/
    api/
      client.js
      tasks.js
      video.js
    stores/
      taskStore.js
    views/
      DownloadWorkspace.vue
    components/
      TaskStats.vue
      TaskList.vue
docs/
  requirements-analysis.md
  solution-design.md
```

---

## 9. AI 接手开发规范

每次新增功能前，AI 需先回答以下问题再编码：

1. 改动是否影响任务状态机？
2. 是否新增/修改 API 字段？前端是否同步？
3. 失败场景如何返回，是否可被前端直接展示？
4. 重启后数据是否可恢复，或是否可接受丢失？
5. 是否需要补充测试用例？

推荐提示模板（可复制给 AI）：

```text
请先阅读 docs/requirements-analysis.md 和 docs/solution-design.md，
按“任务状态一致性优先、前后端契约一致、向后兼容”的原则实现功能。
输出内容必须包含：变更点、API 影响、状态流转影响、验证步骤。
```

---

## 10. 当前已知技术债

- `main.py` 体积较大，职责未充分拆分。
- 前端页面职责集中在单文件组件，后续维护成本会上升。
- 任务来源（单下载/批量/文件系统）仍需统一抽象，避免口径分叉。
- 缺乏 CI（lint/test/build）和发布流程定义。

