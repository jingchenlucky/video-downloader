<script setup>
import { computed, ref } from 'vue'
import { downloadTaskFile, formatDuration, getTaskStatus, startDownload } from '../api.js'

const props = defineProps({
  video: { type: Object, default: null },
  url: { type: String, required: true },
})

const emit = defineEmits(['error'])

const showAdvanced = ref(false)
const selectedFormat = ref('')
const downloading = ref(false)
const progress = ref(0)
const statusText = ref('')

const activeFormat = computed(() => {
  if (!props.video) return null
  return selectedFormat.value || props.video.default_format_id
})

function initFormat() {
  if (props.video) {
    selectedFormat.value = props.video.default_format_id
  }
}

defineExpose({ initFormat })

async function handleDownload() {
  if (!props.video || downloading.value) return

  downloading.value = true
  progress.value = 0
  statusText.value = '准备下载…'

  try {
    const taskId = await startDownload(props.url, activeFormat.value)

    let finalStatus = null
    for (let i = 0; i < 120; i++) {
      const status = await getTaskStatus(taskId)
      progress.value = Math.round((status.progress || 0) * 100)
      statusText.value =
        status.status === 'downloading'
          ? `下载中 ${progress.value}%`
          : status.status === 'queued'
            ? '排队中…'
            : status.status

      if (status.status === 'completed') {
        finalStatus = status
        break
      }
      if (status.status === 'failed') {
        throw new Error(status.error || '下载失败')
      }
      await sleep(1000)
    }

    if (!finalStatus) {
      throw new Error('下载超时，请重试')
    }

    await downloadTaskFile(taskId, finalStatus.filename || 'video.mp4')
    statusText.value = '下载完成！'
  } catch (err) {
    emit('error', err.message)
    statusText.value = ''
  } finally {
    downloading.value = false
  }
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}
</script>

<template>
  <section v-if="video" class="workspace">
    <div class="workspace-card">
      <div class="video-preview">
        <img
          v-if="video.thumbnail"
          :src="video.thumbnail"
          :alt="video.title"
          referrerpolicy="no-referrer"
        />
        <div v-else class="thumb-placeholder">🎬</div>
      </div>

      <div class="video-info">
        <h2>{{ video.title }}</h2>
        <p class="meta">时长 {{ formatDuration(video.duration) }}</p>

        <div class="format-row">
          <label>格式</label>
          <select v-model="selectedFormat">
            <option v-for="fmt in video.formats" :key="fmt.format_id" :value="fmt.format_id">
              {{ fmt.label }}
            </option>
          </select>
        </div>

        <button class="toggle-advanced" type="button" @click="showAdvanced = !showAdvanced">
          {{ showAdvanced ? '收起高级选项 ▲' : '高级选项 ▼' }}
        </button>

        <div v-if="showAdvanced" class="advanced">
          <p v-for="fmt in video.formats" :key="fmt.format_id" class="format-hint">
            <strong>{{ fmt.label }}</strong> — .{{ fmt.ext }}
            <span v-if="fmt.is_audio_only">（仅音频）</span>
          </p>
        </div>

        <button class="btn-download" :disabled="downloading" @click="handleDownload">
          {{ downloading ? statusText : '⬇ 下载到本地' }}
        </button>

        <div v-if="downloading" class="progress-bar">
          <div class="progress-fill" :style="{ width: progress + '%' }" />
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.workspace {
  max-width: 760px;
  margin: 0 auto;
  padding: 1.5rem;
}

.workspace-card {
  display: flex;
  gap: 1.5rem;
  background: #fff;
  border: 1px solid var(--gray-200);
  border-radius: var(--radius);
  padding: 1.5rem;
  box-shadow: var(--shadow);
}

.video-preview img,
.thumb-placeholder {
  width: 200px;
  height: 112px;
  object-fit: cover;
  border-radius: 8px;
  background: var(--gray-100);
}

.thumb-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
}

.video-info {
  flex: 1;
  min-width: 0;
}

.video-info h2 {
  margin: 0 0 0.5rem;
  font-size: 1.1rem;
  line-height: 1.4;
}

.meta {
  color: var(--gray-500);
  font-size: 0.875rem;
  margin: 0 0 1rem;
}

.format-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.format-row select {
  flex: 1;
  padding: 0.5rem;
  border: 1px solid var(--gray-200);
  border-radius: 8px;
}

.toggle-advanced {
  background: none;
  border: none;
  color: var(--blue-600);
  font-size: 0.875rem;
  padding: 0;
  margin-bottom: 0.75rem;
}

.advanced {
  background: var(--gray-50);
  border-radius: 8px;
  padding: 0.75rem 1rem;
  margin-bottom: 1rem;
  font-size: 0.875rem;
}

.format-hint {
  margin: 0.25rem 0;
}

.btn-download {
  width: 100%;
  background: var(--blue-600);
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 0.85rem;
  font-weight: 600;
  font-size: 1rem;
}

.btn-download:hover:not(:disabled) {
  background: var(--blue-700);
}

.btn-download:disabled {
  opacity: 0.7;
}

.progress-bar {
  margin-top: 0.75rem;
  height: 6px;
  background: var(--gray-200);
  border-radius: 999px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--blue-600);
  transition: width 0.3s;
}

@media (max-width: 640px) {
  .workspace-card {
    flex-direction: column;
  }

  .video-preview img,
  .thumb-placeholder {
    width: 100%;
    height: auto;
    aspect-ratio: 16/9;
  }
}
</style>
