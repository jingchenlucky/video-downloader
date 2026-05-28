<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'

const apiStatus = ref('checking')
const message = ref('正在连接下载引擎...')
const payload = ref(null)
const videoUrl = ref('')
const selectedFormat = ref('')
const infoLoading = ref(false)
const downloadLoading = ref(false)
const infoError = ref('')
const downloadError = ref('')
const downloadResult = ref(null)
const videoInfo = ref(null)
const batchUrls = ref('')
const batchLoading = ref(false)
const taskList = ref([])
let pollTimer = null

const checkBackend = async () => {
  apiStatus.value = 'checking'
  message.value = '正在连接下载引擎...'

  try {
    const response = await fetch('/api/health')
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }
    const data = await response.json()
    payload.value = data
    apiStatus.value = 'online'
    message.value = '后端连接正常，已准备好进入下一里程碑。'
  } catch (error) {
    apiStatus.value = 'offline'
    message.value = `后端连接失败：${error.message}`
  }
}

const formatLabel = (fmt) => {
  const sizeText = fmt.filesize ? `${(fmt.filesize / 1024 / 1024).toFixed(1)} MB` : '未知大小'
  const fpsText = fmt.fps ? `${fmt.fps}fps` : 'fps?'
  const kindText = fmt.kind ? ` · ${fmt.kind}` : ''
  return `${fmt.resolution || '未知分辨率'} · ${fmt.ext || '未知格式'} · ${fpsText}${kindText} · ${sizeText}`
}

const formatNumber = (num) => {
  if (num === null || num === undefined) return '-'
  if (num >= 100000000) return `${(num / 100000000).toFixed(1)}亿`
  if (num >= 10000) return `${(num / 10000).toFixed(1)}万`
  return `${num}`
}

const formatDuration = (seconds) => {
  if (!seconds && seconds !== 0) return '-'
  const total = Math.floor(seconds)
  const h = Math.floor(total / 3600)
  const m = Math.floor((total % 3600) / 60)
  const s = total % 60
  if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
  return `${m}:${String(s).padStart(2, '0')}`
}

const fetchVideoInfo = async () => {
  infoError.value = ''
  downloadError.value = ''
  downloadResult.value = null
  videoInfo.value = null

  if (!videoUrl.value.trim()) {
    infoError.value = '请先输入视频链接。'
    return
  }

  infoLoading.value = true
  try {
    const response = await fetch('/api/video/info', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: videoUrl.value.trim() }),
    })

    const data = await response.json()
    if (!response.ok) {
      throw new Error(data.detail || `HTTP ${response.status}`)
    }

    videoInfo.value = data
    selectedFormat.value = data.recommended_format
  } catch (error) {
    infoError.value = `解析失败：${error.message}`
  } finally {
    infoLoading.value = false
  }
}

const downloadVideo = async () => {
  downloadError.value = ''
  downloadResult.value = null

  if (!videoUrl.value.trim()) {
    downloadError.value = '请先输入视频链接。'
    return
  }

  downloadLoading.value = true
  try {
    const response = await fetch('/api/video/download', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        url: videoUrl.value.trim(),
        format_id: selectedFormat.value || undefined,
      }),
    })

    const data = await response.json()
    if (!response.ok) {
      throw new Error(data.detail || `HTTP ${response.status}`)
    }
    downloadResult.value = data
  } catch (error) {
    downloadError.value = `下载失败：${error.message}`
  } finally {
    downloadLoading.value = false
  }
}

const refreshTasks = async () => {
  try {
    const response = await fetch('/api/tasks?limit=50')
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }
    const data = await response.json()
    taskList.value = data.tasks || []
  } catch (error) {
    // keep silent to avoid noisy UI while polling
  }
}

const submitBatch = async () => {
  downloadError.value = ''
  const urls = batchUrls.value
    .split('\n')
    .map((item) => item.trim())
    .filter(Boolean)

  if (!urls.length) {
    downloadError.value = '请先输入至少一个链接（每行一个）。'
    return
  }

  batchLoading.value = true
  try {
    const response = await fetch('/api/video/download/batch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        urls,
        format_id: selectedFormat.value || undefined,
      }),
    })
    const data = await response.json()
    if (!response.ok) {
      throw new Error(data.detail || `HTTP ${response.status}`)
    }
    await refreshTasks()
  } catch (error) {
    downloadError.value = `批量任务提交失败：${error.message}`
  } finally {
    batchLoading.value = false
  }
}

const formatSpeed = (speed) => {
  if (!speed) return '-'
  return `${(speed / 1024 / 1024).toFixed(2)} MB/s`
}

const formatProgress = (task) => {
  if (task.status === 'completed') return '100%'
  if (!task.total_bytes) return `${(task.downloaded_bytes / 1024 / 1024).toFixed(2)} MB`
  return `${task.progress.toFixed(1)}%`
}

const runningTaskCount = computed(
  () => taskList.value.filter((task) => ['queued', 'downloading'].includes(task.status)).length,
)
const completedTaskCount = computed(
  () => taskList.value.filter((task) => task.status === 'completed').length,
)
const failedTaskCount = computed(() => taskList.value.filter((task) => task.status === 'failed').length)

const scrollToWorkspace = () => {
  const target = document.getElementById('workspace')
  if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

const fillDemoLink = () => {
  videoUrl.value = 'https://samplelib.com/lib/preview/mp4/sample-5s.mp4'
}

onMounted(() => {
  checkBackend()
  refreshTasks()
  pollTimer = window.setInterval(refreshTasks, 2000)
})

onUnmounted(() => {
  if (pollTimer) {
    window.clearInterval(pollTimer)
    pollTimer = null
  }
})
</script>

<template>
  <main class="page">
    <section class="hero-banner">
      <div class="hero-inner">
        <p class="badge">MVP · Milestone 4</p>
        <h1>全平台视频下载站</h1>
        <p class="subtitle">
          不受平台下载限制，复制链接即可下载。支持单个解析、批量任务、实时进度追踪。
        </p>
        <div class="hero-actions">
          <button class="cta-btn" type="button" @click="scrollToWorkspace">立即下载视频</button>
          <button class="ghost-btn" type="button" @click="fillDemoLink">填充演示链接</button>
        </div>
        <div class="hero-stats">
          <div class="stat-item">
            <span class="stat-num">{{ runningTaskCount }}</span>
            <span class="stat-label">运行中任务</span>
          </div>
          <div class="stat-item">
            <span class="stat-num">{{ completedTaskCount }}</span>
            <span class="stat-label">已完成任务</span>
          </div>
          <div class="stat-item">
            <span class="stat-num">{{ failedTaskCount }}</span>
            <span class="stat-label">失败任务</span>
          </div>
        </div>
      </div>
    </section>

    <section class="feature-grid">
      <article class="feature-card">
        <h3>极速批量下载</h3>
        <p>支持多链接同时提交，自动排队执行，移动端也可用。</p>
      </article>
      <article class="feature-card">
        <h3>高清格式可选</h3>
        <p>解析视频可用格式，按清晰度和体积选择最合适的版本。</p>
      </article>
      <article class="feature-card">
        <h3>实时进度追踪</h3>
        <p>下载状态、速度、ETA 实时显示，失败任务可快速定位。</p>
      </article>
    </section>

    <section id="workspace" class="download-panel">
      <div class="workspace-head">
        <h2>下载工作台</h2>
        <div class="inline-status">
          <span class="dot" :class="apiStatus" />
          <span>{{ apiStatus === 'online' ? '服务在线' : apiStatus === 'offline' ? '服务离线' : '检测中' }}</span>
        </div>
      </div>
      <p class="panel-tip">支持单视频与批量任务，任务进度自动刷新。</p>

      <div class="status-card">
        <p class="status-title">服务状态</p>
        <p :class="['status-value', apiStatus]">
          {{
            apiStatus === 'online'
              ? '在线'
              : apiStatus === 'offline'
                ? '离线'
                : '检测中'
          }}
        </p>
        <p class="status-msg">{{ message }}</p>
        <button class="retry-btn" type="button" @click="checkBackend">重新检测</button>
      </div>

      <details class="debug-panel">
        <summary>查看健康检查详情</summary>
        <pre v-if="payload" class="payload">{{ JSON.stringify(payload, null, 2) }}</pre>
      </details>

      <section>
        <h2>开始下载</h2>
        <p class="panel-tip">先粘贴链接，解析后可选择格式并立即下载。</p>

        <input
          v-model="videoUrl"
          class="url-input"
          type="text"
          placeholder="粘贴视频链接，例如：https://www.youtube.com/watch?v=..."
        />

        <div class="action-row">
          <button class="retry-btn" type="button" :disabled="infoLoading" @click="fetchVideoInfo">
            {{ infoLoading ? '解析中...' : '解析视频信息' }}
          </button>
          <button class="retry-btn" type="button" :disabled="downloadLoading" @click="downloadVideo">
            {{ downloadLoading ? '下载中...' : '开始下载' }}
          </button>
        </div>

        <p v-if="infoError" class="error-msg">{{ infoError }}</p>
        <p v-if="downloadError" class="error-msg">{{ downloadError }}</p>

        <div v-if="videoInfo" class="result-card">
          <div class="video-summary">
            <img
              v-if="videoInfo.thumbnail"
              class="video-cover"
              :src="videoInfo.thumbnail"
              alt="视频封面"
              referrerpolicy="no-referrer"
            />
            <div class="video-meta">
              <p><strong>标题：</strong>{{ videoInfo.title || '未知标题' }}</p>
              <p><strong>作者：</strong>{{ videoInfo.uploader || '未知作者' }}</p>
              <p><strong>时长：</strong>{{ formatDuration(videoInfo.duration) }}</p>
            </div>
          </div>

          <div class="stats-grid">
            <div class="stats-item">
              <span class="stats-key">播放</span>
              <span class="stats-value">{{ formatNumber(videoInfo.stats?.view_count) }}</span>
            </div>
            <div class="stats-item">
              <span class="stats-key">点赞</span>
              <span class="stats-value">{{ formatNumber(videoInfo.stats?.like_count) }}</span>
            </div>
            <div class="stats-item">
              <span class="stats-key">收藏</span>
              <span class="stats-value">{{ formatNumber(videoInfo.stats?.favorite_count) }}</span>
            </div>
            <div class="stats-item">
              <span class="stats-key">评论</span>
              <span class="stats-value">{{ formatNumber(videoInfo.stats?.comment_count) }}</span>
            </div>
            <div class="stats-item">
              <span class="stats-key">弹幕</span>
              <span class="stats-value">{{ formatNumber(videoInfo.stats?.danmaku_count) }}</span>
            </div>
            <div class="stats-item">
              <span class="stats-key">转发</span>
              <span class="stats-value">{{ formatNumber(videoInfo.stats?.repost_count) }}</span>
            </div>
          </div>

          <label class="select-label" for="formatSelect">选择清晰度 / 格式</label>
          <select id="formatSelect" v-model="selectedFormat" class="format-select">
            <option :value="videoInfo.recommended_format">推荐（自动选择最佳音视频）</option>
            <option
              v-for="fmt in videoInfo.formats"
              :key="fmt.format_id"
              :value="fmt.format_id"
            >
              {{ fmt.format_id }} · {{ formatLabel(fmt) }}
            </option>
          </select>
        </div>

        <div v-if="downloadResult" class="result-card success">
          <p><strong>下载完成：</strong>{{ downloadResult.title }}</p>
          <p><strong>保存路径：</strong>{{ downloadResult.output_file }}</p>
        </div>

        <h3 class="section-title">批量下载（每行一个链接）</h3>
        <textarea
          v-model="batchUrls"
          class="url-textarea"
          rows="6"
          placeholder="https://example.com/video1&#10;https://example.com/video2"
        />
        <button class="retry-btn" type="button" :disabled="batchLoading" @click="submitBatch">
          {{ batchLoading ? '提交中...' : '创建批量任务' }}
        </button>

        <div class="task-header">
          <h3 class="section-title no-margin">任务列表</h3>
          <span class="task-meta">运行中：{{ runningTaskCount }}</span>
        </div>

        <div v-if="taskList.length" class="task-list">
          <div v-for="task in taskList" :key="task.task_id" class="task-card">
            <div class="task-top">
              <p class="task-url">{{ task.url }}</p>
              <span :class="['task-status', task.status]">{{ task.status }}</span>
            </div>
            <p class="task-info">
              进度：{{ formatProgress(task) }} · 速度：{{ formatSpeed(task.speed) }} · ETA：
              {{ task.eta ?? '-' }}
            </p>
            <p v-if="task.output_file" class="task-info">文件：{{ task.output_file }}</p>
            <p v-if="task.error" class="error-msg">{{ task.error }}</p>
          </div>
        </div>
        <p v-else class="panel-tip">暂无任务，创建批量任务后会显示在这里。</p>
      </section>
    </section>
  </main>
</template>
