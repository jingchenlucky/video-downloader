<script setup>
function showComingSoon() {
  alert('付费功能即将上线，敬请期待！')
}
</script>

<template>
  <section class="section">
    <h2 class="section-title">选择适合你的方案</h2>
    <p class="section-subtitle">免费版已足够日常使用，Pro 解锁全部能力</p>

    <div class="pricing-grid">
      <div class="plan">
        <h3>免费版</h3>
        <p class="price">¥0<span>/月</span></p>
        <ul>
          <li>每日 3 次下载</li>
          <li>标准画质</li>
          <li>单链接下载</li>
        </ul>
        <button class="btn-outline" disabled>当前方案</button>
      </div>

      <div class="plan featured">
        <span class="badge">推荐</span>
        <h3>Pro 版</h3>
        <p class="price">¥19<span>/月</span></p>
        <ul>
          <li>无限次下载</li>
          <li>最高画质 + 仅音频</li>
          <li>批量下载（即将上线）</li>
          <li>视频总结 + 字幕翻译</li>
        </ul>
        <button class="btn-primary" @click="showComingSoon">升级 Pro</button>
      </div>
    </div>
  </section>
</template>

<style scoped>
.section {
  max-width: 760px;
  margin: 0 auto;
  padding: 0 1.5rem 4rem;
}

.pricing-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

.plan {
  position: relative;
  padding: 2rem 1.5rem;
  background: #fff;
  border: 2px solid var(--gray-200);
  border-radius: var(--radius);
  text-align: center;
}

.plan.featured {
  border-color: var(--blue-600);
  box-shadow: var(--shadow);
}

.badge {
  position: absolute;
  top: -12px;
  left: 50%;
  transform: translateX(-50%);
  background: var(--blue-600);
  color: #fff;
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.25rem 0.75rem;
  border-radius: 999px;
}

.plan h3 {
  margin: 0 0 0.5rem;
}

.price {
  font-size: 2rem;
  font-weight: 700;
  color: var(--blue-600);
  margin: 0 0 1.25rem;
}

.price span {
  font-size: 0.875rem;
  font-weight: 400;
  color: var(--gray-500);
}

.plan ul {
  list-style: none;
  padding: 0;
  margin: 0 0 1.5rem;
  text-align: left;
}

.plan li {
  padding: 0.35rem 0;
  font-size: 0.9rem;
  color: var(--gray-700);
}

.plan li::before {
  content: '✓ ';
  color: var(--blue-600);
  font-weight: 600;
}

.btn-outline,
.btn-primary {
  width: 100%;
  padding: 0.75rem;
  border-radius: 8px;
  font-weight: 600;
  border: none;
}

.btn-outline {
  background: var(--gray-100);
  color: var(--gray-500);
}

.btn-primary {
  background: var(--blue-600);
  color: #fff;
}

.btn-primary:hover {
  background: var(--blue-700);
}

@media (max-width: 640px) {
  .pricing-grid {
    grid-template-columns: 1fr;
  }
}
</style>
