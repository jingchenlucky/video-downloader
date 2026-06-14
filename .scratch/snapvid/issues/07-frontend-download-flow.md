Status: ready-for-agent

# 07 — 前端工作区：解析 → 下载全链路

## Parent

`.scratch/snapvid/PRD.md`

## What to build

在 Hero 下方实现工作区：调用 `POST /api/analyze` 展示封面、标题、时长；默认选中最佳画质，高级选项折叠可选 MP4/MP3 与清晰度；调用 `POST /api/download` 并轮询 `GET /api/tasks/{id}` 显示进度；完成后触发 `GET /api/tasks/{id}/file` 浏览器下载。含 loading 与错误提示。

## Acceptance criteria

- [ ] 粘贴链接 → 解析 → 展示视频元数据
- [ ] 默认格式一键下载，高级选项可切换 format
- [ ] 下载过程显示进度条或百分比
- [ ] 完成后自动触发文件下载
- [ ] 无效链接与 API 错误有用户可读提示
- [ ] 开发环境通过 Vite proxy 或 CORS 连接 backend :8000

## Blocked by

- `.scratch/snapvid/issues/02-analyze-api.md`
- `.scratch/snapvid/issues/03-download-task-and-progress.md`
- `.scratch/snapvid/issues/04-file-delivery-and-cleanup.md`
- `.scratch/snapvid/issues/06-frontend-hero-and-brand.md`
