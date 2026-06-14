<script setup>
defineProps({
  url: { type: String, required: true },
  loading: { type: Boolean, default: false },
})

const emit = defineEmits(['update:url', 'analyze'])
</script>

<template>
  <header class="hero">
    <div class="hero-inner">
      <div class="brand-row">
        <span class="logo">⚡</span>
        <div>
          <h1 class="brand">闪存视频 <span class="brand-en">SnapVid</span></h1>
          <p class="tagline">粘贴链接，秒存高清视频</p>
        </div>
      </div>

      <p class="hero-desc">多平台支持 · 免安装 · 手机也能用 · 高清保存到本地</p>

      <div class="search-bar">
        <input
          :value="url"
          type="url"
          placeholder="粘贴视频链接，例如 https://www.youtube.com/watch?v=..."
          @input="emit('update:url', $event.target.value)"
          @keyup.enter="emit('analyze')"
        />
        <button class="btn-primary" :disabled="loading || !url.trim()" @click="emit('analyze')">
          {{ loading ? '解析中…' : '解析视频' }}
        </button>
      </div>

      <div class="hero-tags">
        <span class="tag">YouTube</span>
        <span class="tag">Bilibili</span>
        <span class="tag">Twitter/X</span>
        <span class="tag">TikTok</span>
        <span class="tag">1000+ 平台</span>
      </div>
    </div>
  </header>
</template>

<style scoped>
.hero {
  background: linear-gradient(180deg, var(--blue-50) 0%, #fff 100%);
  padding: 3rem 1.5rem 2rem;
  border-bottom: 1px solid var(--gray-200);
}

.hero-inner {
  max-width: 760px;
  margin: 0 auto;
}

.brand-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 0.75rem;
}

.logo {
  font-size: 2.5rem;
  line-height: 1;
}

.brand {
  margin: 0;
  font-size: 1.75rem;
  font-weight: 700;
}

.brand-en {
  color: var(--blue-600);
}

.tagline {
  margin: 0.15rem 0 0;
  color: var(--gray-500);
  font-size: 0.95rem;
}

.hero-desc {
  text-align: center;
  color: var(--gray-700);
  margin: 1.25rem 0 1.5rem;
  font-size: 0.95rem;
}

.search-bar {
  display: flex;
  gap: 0.75rem;
  background: #fff;
  border: 2px solid var(--gray-200);
  border-radius: var(--radius);
  padding: 0.5rem;
  box-shadow: var(--shadow);
}

.search-bar input {
  flex: 1;
  border: none;
  outline: none;
  padding: 0.75rem 1rem;
  font-size: 1rem;
  min-width: 0;
}

.btn-primary {
  background: var(--blue-600);
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 0.75rem 1.5rem;
  font-weight: 600;
  white-space: nowrap;
  transition: background 0.15s;
}

.btn-primary:hover:not(:disabled) {
  background: var(--blue-700);
}

.btn-primary:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.hero-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  justify-content: center;
  margin-top: 1.25rem;
}

@media (max-width: 640px) {
  .search-bar {
    flex-direction: column;
  }

  .btn-primary {
    width: 100%;
  }
}
</style>
