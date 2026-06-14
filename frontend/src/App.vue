<script setup>
import { ref } from 'vue'
import { analyzeVideo } from './api.js'
import HeroSection from './components/HeroSection.vue'
import DownloadWorkspace from './components/DownloadWorkspace.vue'
import PlatformGrid from './components/PlatformGrid.vue'
import FeatureHighlights from './components/FeatureHighlights.vue'
import PricingSection from './components/PricingSection.vue'

const url = ref('')
const loading = ref(false)
const video = ref(null)
const error = ref('')
const workspaceRef = ref(null)

async function handleAnalyze() {
  if (!url.value.trim()) return

  loading.value = true
  error.value = ''
  video.value = null

  try {
    video.value = await analyzeVideo(url.value.trim())
    setTimeout(() => workspaceRef.value?.initFormat(), 0)
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

function handleWorkspaceError(message) {
  error.value = message
}
</script>

<template>
  <div class="app">
    <HeroSection v-model:url="url" :loading="loading" @analyze="handleAnalyze" />

    <p v-if="error" class="error-banner">{{ error }}</p>

    <DownloadWorkspace
      ref="workspaceRef"
      :video="video"
      :url="url"
      @error="handleWorkspaceError"
    />

    <PlatformGrid />
    <FeatureHighlights />
    <PricingSection />

    <footer class="footer">
      <p>⚡ 闪存视频 SnapVid — 基于 yt-dlp 开源项目</p>
    </footer>
  </div>
</template>

<style scoped>
.error-banner {
  max-width: 760px;
  margin: 0 auto 0;
  padding: 0.75rem 1.5rem;
  color: #b91c1c;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  text-align: center;
  font-size: 0.9rem;
}

.footer {
  text-align: center;
  padding: 2rem 1.5rem;
  color: var(--gray-500);
  font-size: 0.875rem;
  border-top: 1px solid var(--gray-200);
}

.footer p {
  margin: 0;
}
</style>
