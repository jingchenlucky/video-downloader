Status: ready-for-agent

# 04 — 文件交付与临时文件清理

## Parent

`.scratch/snapvid/PRD.md`

## What to build

实现 `GET /api/tasks/{id}/file`：任务 completed 时返回文件流供浏览器下载；未完成任务返回 409 或 404。实现临时文件策略：用户成功下载后删除文件；任务创建超过 30 分钟未下载则自动清理。

## Acceptance criteria

- [ ] completed 任务可通过 file 端点下载，Content-Disposition 含文件名
- [ ] 非 completed 任务访问 file 端点返回合适错误状态
- [ ] 文件成功交付后服务端临时文件被删除
- [ ] 超过 30 分钟未下载的任务文件被清理（可通过注入 clock 或 TTL 参数测试）

## Blocked by

- `.scratch/snapvid/issues/03-download-task-and-progress.md`
