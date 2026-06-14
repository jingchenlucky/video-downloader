<script setup>
const platforms = [
  { name: 'YouTube', emoji: '▶️' },
  { name: 'Bilibili', emoji: '📺' },
  { name: 'Twitter/X', emoji: '🐦' },
  { name: 'TikTok', emoji: '🎵' },
  { name: 'Instagram', emoji: '📷' },
  { name: 'Facebook', emoji: '👥' },
  { name: 'Vimeo', emoji: '🎥' },
  { name: 'Reddit', emoji: '🔴' },
]
</script>

<template>
  <section class="section">
    <h2 class="section-title">支持 1000+ 视频平台</h2>
    <p class="section-subtitle">基于 yt-dlp，覆盖主流国内外平台</p>
    <div class="card-grid">
      <div v-for="p in platforms" :key="p.name" class="platform-card">
        <span class="emoji">{{ p.emoji }}</span>
        <span>{{ p.name }}</span>
      </div>
    </div>
  </section>
</template>

<style scoped>
.section {
  max-width: 960px;
  margin: 0 auto;
  padding: 3rem 1.5rem;
}

.platform-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  padding: 1.25rem 1rem;
  background: #fff;
  border: 1px solid var(--gray-200);
  border-radius: var(--radius);
  font-weight: 500;
  transition: box-shadow 0.15s, border-color 0.15s;
}

.platform-card:hover {
  border-color: var(--blue-600);
  box-shadow: var(--shadow);
}

.emoji {
  font-size: 1.75rem;
}
</style>
