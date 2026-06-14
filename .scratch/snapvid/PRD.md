Status: ready-for-agent

# PRD: SnapVid 万能视频下载器 MVP

## Problem Statement

许多用户需要将各平台视频保存到本地，但常遇到：平台不提供下载、无法批量下载、清晰度受限、手机端操作不便等问题。用户希望有一个随时随地可用、支持多平台的万能视频下载工具，并能在未来扩展总结、翻译、付费等增值能力。

## Solution

构建 **SnapVid（闪存视频）** — 一个 Web 应用：

1. 用户粘贴视频链接
2. 系统解析视频元数据（标题、封面、可选格式）
3. 用户选择格式（默认最佳画质，高级选项可折叠）
4. 后台通过 yt-dlp 下载，前端展示进度
5. 用户将文件保存到本地

首页采用工具优先布局，底部展示平台支持、即将上线功能、免费 vs Pro 定价对比（UI 占位）。UI 风格参考 ai.codefather.cn/painting：白底、蓝色主色、卡片网格、付费感文案。

## User Stories

1. As a 访客, I want to 粘贴视频链接并解析, so that 我能看到视频标题、封面和可用格式
2. As a 访客, I want to 使用默认最佳画质一键下载, so that 我不需要做复杂选择
3. As a 访客, I want to 展开高级选项选择 MP4/MP3 或指定清晰度, so that 我能满足进阶需求
4. As a 访客, I want to 看到下载进度, so that 我知道任务是否在进行
5. As a 访客, I want to 下载完成后保存文件到本地, so that 我能在设备上观看
6. As a 访客, I want to 在手机上使用同一网站, so that 我随时随地都能下载
7. As a 访客, I want to 看到支持的平台列表, so that 我知道哪些网站可用
8. As a 访客, I want to 看到免费版与 Pro 版对比, so that 我了解升级价值
9. As a 访客, I want to 看到批量下载/视频总结/字幕翻译「即将上线」, so that 我知道产品路线图
10. As a 访客, I want to 无效链接时看到清晰错误提示, so that 我知道如何修正
11. As a 开发者, I want to 本地一键启动前后端, so that 我能快速开发验证
12. As a 开发者, I want to 下载文件在交付后自动清理, so that 磁盘不会堆积

## Implementation Decisions

### 架构

- **后端**：Python + FastAPI + yt-dlp，无数据库，内存任务管理
- **前端**：Vue 3 + Vite
- **部署**：MVP 仅本地运行（backend :8000, frontend :5173），架构预留后续 Docker 部署
- **核心封装**：通过 `VideoDownloader` 协议封装 yt-dlp，生产用 `YtdlpVideoDownloader`，测试用 `FakeVideoDownloader`

### API 契约

| Method | Path | 行为 |
| ------ | ---- | ---- |
| GET | `/api/health` | 健康检查 |
| POST | `/api/analyze` | 解析链接 → 标题、封面、时长、格式列表、default_format_id |
| POST | `/api/download` | 发起下载 → 返回 task_id |
| GET | `/api/tasks/{id}` | 查询任务状态与进度 |
| GET | `/api/tasks/{id}/file` | 下载完成后的文件流 |

### 格式选择

- 默认 `default_format_id`（最佳可用画质）
- 高级选项折叠：MP4 清晰度列表、仅音频 MP3

### 文件清理

- 用户成功下载后删除服务端临时文件
- 30 分钟未下载自动清理

### 前端布局（方案 C）

1. Hero：品牌 + 主标语 + 大输入框
2. 工作区（紧贴 Hero）：解析结果 / 格式 / 进度 / 下载
3. 底部：平台卡片 → 功能亮点 → 定价对比

### 品牌

- 名称：**闪存视频 SnapVid**
- 主标语：**粘贴链接，秒存高清视频**

### 已有代码

项目已有部分后端骨架：`create_app` 工厂、health 端点、`VideoDownloader` 协议与 `FakeVideoDownloader`、health 测试与 analyze 测试（analyze 端点尚未实现）。

## Testing Decisions

### 测试哲学

- 通过**公共 HTTP API** 验证行为，不测试内部实现细节
- 采用 TDD **垂直切片**：一个测试 → 最少实现 → 重复
- 只在**系统边界** mock：`VideoDownloader`（yt-dlp 是外部依赖），不 mock 内部模块

### 测试切入点（Seams）

| Seam | 层级 | 用途 |
| ---- | ---- | ---- |
| **HTTP API（TestClient）** | 最高 | 所有用户行为的集成测试入口 |
| **VideoDownloader 协议** | 系统边界 | 隔离 yt-dlp，Fake 实现供测试注入 |
| **任务管理器** | 通过 API 间接测试 | 不单独测内部状态，通过 `/api/tasks/{id}` 验证 |

### 优先测试的行为

1. 健康检查返回 ok
2. 无效链接 analyze 返回 400
3. 有效链接 analyze 返回元数据
4. download 创建任务并返回 task_id
5. 任务状态从 downloading → completed
6. completed 任务可通过 file 端点获取文件
7. 失败任务返回 error 信息

### 不测（MVP）

- 真实 yt-dlp 网络调用（手动验收）
- 前端单元测试（手动/E2E 验收）
- 免费次数限制 enforce

## Out of Scope

- 真实支付与用户账号
- 数据库
- 批量下载（仅 UI 占位）
- 视频总结、字幕翻译（仅 UI 占位）
- Docker 部署脚本
- 免费版每日 3 次限制的后端 enforce

## Further Notes

- UI 参考：ai.codefather.cn/painting（白底、蓝色主色、卡片网格）
- yt-dlp 用法：封装 subprocess/YoutubeDL API，不 fork 修改上游代码
- grill-me 决策记录：MVP A、本地部署、格式 A、批量 A、清理 A、Vue3、品牌 B、定价 A、布局 C
