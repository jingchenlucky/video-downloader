# SnapVid — 闪存视频

万能视频下载网站 MVP。粘贴链接，解析元数据，选择格式，下载到本地。

## 技术栈

- **后端**：Python 3.9+ · FastAPI · yt-dlp
- **前端**：Vue 3 · Vite

## 环境要求

- Python 3.9+
- Node.js 18+
- ffmpeg（yt-dlp 合并音视频时推荐安装）

## 快速启动

### 1. 后端

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.asgi:app --reload --port 8000
```

验证：访问 http://127.0.0.1:8000/api/health 应返回 `{"status":"ok"}`

### 2. 前端

```bash
cd frontend
npm install
npm run dev
```

访问 http://127.0.0.1:5173

前端通过 Vite proxy 将 `/api` 请求转发到后端 `:8000`。

## 运行测试

```bash
cd backend
source .venv/bin/activate
pytest tests/ -v
```

测试使用 TDD 风格，通过 HTTP API + FakeVideoDownloader 验证行为，不依赖真实网络。

## 手动验证真实下载

1. 确保后端和前端均已启动
2. 在输入框粘贴一个公开视频链接（如 YouTube 短视频）
3. 点击「解析视频」→ 确认封面和标题
4. 点击「下载到本地」→ 等待进度完成 → 浏览器保存文件

## 项目文档

- PRD：`.scratch/snapvid/PRD.md`
- Issues：`.scratch/snapvid/issues/`
- 领域词汇：`CONTEXT.md`

## Agent Skills 工作流

本项目使用以下 skills 开发：

1. **grill-me** — 需求对齐
2. **to-prd** — 生成 PRD
3. **to-issues** — 拆分为垂直切片 issue
4. **tdd** — 红→绿→重构，逐 issue 实现

## 注意事项

- 请遵守各平台服务条款，仅下载有权保存的内容
- MVP 不含真实支付、用户账号、批量下载 enforce
- 临时文件在下载交付后删除，30 分钟未取也会自动清理
