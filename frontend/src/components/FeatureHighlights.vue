<script setup>
const features = [
  { title: '批量下载', desc: '一次粘贴多个链接，批量保存', soon: true },
  { title: '视频总结', desc: 'AI 自动生成视频内容摘要', soon: true },
  { title: '字幕翻译', desc: '多语言字幕提取与翻译', soon: true },
  { title: '高清无损', desc: '支持最高可用画质下载', soon: false },
]
</script>

<template>
  <section class="section">
    <h2 class="section-title">更多能力，持续上线</h2>
    <p class="section-subtitle">Pro 用户将优先体验以下功能</p>
    <div class="card-grid">
      <div v-for="f in features" :key="f.title" class="feature-card">
        <div class="feature-head">
          <h3>{{ f.title }}</h3>
          <span v-if="f.soon" class="tag soon">即将上线</span>
        </div>
        <p>{{ f.desc }}</p>
      </div>
    </div>
  </section>
</template>

<style scoped>
.section {
  max-width: 960px;
  margin: 0 auto;
  padding: 0 1.5rem 3rem;
}

.feature-card {
  padding: 1.25rem;
  background: var(--gray-50);
  border: 1px solid var(--gray-200);
  border-radius: var(--radius);
}

.feature-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.feature-head h3 {
  margin: 0;
  font-size: 1rem;
}

.tag.soon {
  background: #fef3c7;
  color: #b45309;
  flex-shrink: 0;
}

.feature-card p {
  margin: 0;
  color: var(--gray-500);
  font-size: 0.875rem;
}
</style>
