# SnapVid Domain Glossary

## Product

**SnapVid（闪存视频）** — 万能视频下载网站。用户粘贴视频链接，解析元数据，选择格式，下载到本地。

## Core concepts

| Term | Definition |
| ---- | ---------- |
| **Analyze（解析）** | 从视频链接提取标题、封面、时长、可用格式列表 |
| **Download task（下载任务）** | 一次下载请求的生命周期：queued → downloading → completed / failed |
| **Format（格式）** | 可选的视频/音频输出选项（如最佳画质 MP4、720p、仅音频 MP3） |
| **VideoDownloader** | 系统边界接口，封装 yt-dlp；测试时使用 FakeVideoDownloader |

## Actors

| Actor | Description |
| ----- | ----------- |
| **Visitor（访客）** | 未登录用户，使用免费下载能力 |
| **Pro user（Pro 用户）** | MVP 仅占位，无真实账号 |

## Out of scope (MVP)

批量下载、视频总结、字幕翻译、真实支付、用户账号、数据库。
