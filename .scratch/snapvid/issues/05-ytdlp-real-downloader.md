Status: ready-for-agent

# 05 — yt-dlp 真实下载器接入

## Parent

`.scratch/snapvid/PRD.md`

## What to build

实现 `YtdlpVideoDownloader`，封装 yt-dlp 的 analyze 与 download 能力，接入 `create_app` 默认依赖。支持默认最佳画质及 format_id 选择（含仅音频）。不修改 yt-dlp 上游代码，仅封装调用。

## Acceptance criteria

- [ ] 生产环境 `create_app()` 默认使用 `YtdlpVideoDownloader`
- [ ] analyze 能从真实链接提取 title、thumbnail、duration、formats
- [ ] download 能按 format_id 下载到指定目录
- [ ] 现有 Fake 驱动的集成测试仍全部通过
- [ ] 提供手动验证说明（README 或 issue comment）

## Blocked by

- `.scratch/snapvid/issues/04-file-delivery-and-cleanup.md`
