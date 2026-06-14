Status: ready-for-agent

# 02 — 解析视频链接 analyze API

## Parent

`.scratch/snapvid/PRD.md`

## What to build

实现 `POST /api/analyze`：访客粘贴视频链接，系统通过 `VideoDownloader.analyze` 返回标题、封面、时长、格式列表和 `default_format_id`。无效或不支持的链接返回 400 及清晰错误信息。测试使用 `FakeVideoDownloader`，不调用真实 yt-dlp。

## Acceptance criteria

- [ ] 有效链接返回 200，包含 title、thumbnail、duration、formats、default_format_id
- [ ] 无效/不支持链接返回 400，detail 含可读错误信息
- [ ] 测试通过公共 HTTP API 验证，不 mock 内部模块

## Blocked by

- `.scratch/snapvid/issues/01-backend-health-and-skeleton.md`
