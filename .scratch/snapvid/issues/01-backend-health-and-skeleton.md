Status: ready-for-agent

# 01 — 后端健康检查与项目骨架

## Parent

`.scratch/snapvid/PRD.md`

## What to build

搭建 SnapVid 后端基础：FastAPI 应用工厂 `create_app`、依赖注入（downloader、download_dir）、pytest 测试基础设施，以及 `GET /api/health` 健康检查端点。使开发者能通过 TestClient 验证后端环境就绪。

## Acceptance criteria

- [ ] `GET /api/health` 返回 `200` 和 `{"status": "ok"}`
- [ ] `create_app` 支持注入 `downloader` 与 `download_dir`（供测试使用）
- [ ] pytest 可通过 `conftest.py`  fixture 运行集成测试
- [ ] 项目依赖声明在 `requirements.txt`

## Blocked by

None — can start immediately
