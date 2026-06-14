Status: ready-for-agent

# 03 — 下载任务创建与进度查询

## Parent

`.scratch/snapvid/PRD.md`

## What to build

实现 `POST /api/download` 创建下载任务并返回 `task_id`；实现 `GET /api/tasks/{id}` 查询任务状态（queued / downloading / completed / failed）和进度（0.0–1.0）。后台异步执行下载，通过注入的 `VideoDownloader.download` 完成，测试仍使用 Fake 实现。

## Acceptance criteria

- [ ] `POST /api/download` 接受 url 和可选 format_id，返回 task_id
- [ ] `GET /api/tasks/{id}` 返回 status 与 progress
- [ ] 任务从不存在的 id 返回 404
- [ ] 下载成功时 status 变为 completed，progress 为 1.0
- [ ] 下载失败时 status 为 failed，含 error 信息

## Blocked by

- `.scratch/snapvid/issues/02-analyze-api.md`
