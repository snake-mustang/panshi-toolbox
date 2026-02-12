<template>
  <section class="page">
    <h2 class="section-title">开发工具箱</h2>
    <p class="sub">截图、识字等开发常用工具</p>
    <div class="cards">
      <div class="card" @click="$router.push('/api-one-click')">
        <div class="card-head"><h3>一键接入API接口</h3><span class="card-by">--by: 黄通</span></div>
        <p>从 APIFOX 复制 OpenAPI/Swagger，生成规则并复制到剪贴板。</p>
        <div class="card-footer"><button type="button" class="btn">一键应用</button></div>
      </div>
      <div class="card" @click="$router.push('/screenshot')">
        <div class="card-head"><h3>长截图</h3><span class="card-by">--by: 黄通</span></div>
        <p>框选区域后手动滚动，自动拼接成长图（PixPin 式）</p>
        <div class="card-footer"><button type="button" class="btn">打开</button></div>
      </div>
      <div class="card" @click="$router.push('/ocr')">
        <div class="card-head"><h3>截图识字</h3><span class="card-by">--by: 黄通</span></div>
        <p>先区域截图，再识别图中的文字</p>
        <div class="card-footer"><button type="button" class="btn">打开</button></div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { inject } from 'vue'
defineOptions({ name: 'Dev' })
inject('log')('开发工具箱')
</script>

<style scoped>
.page { display: block; }
</style>
