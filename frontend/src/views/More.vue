<template>
  <section class="page">
    <h2 class="section-title">更多工具</h2>
    <p class="sub">更多功能敬请期待</p>
    <div class="cards">
      <div class="card placeholder" @click="log('该功能开发中')">
        <div class="card-head"><h3>更多</h3><span class="card-by">--by: 黄通</span></div>
        <p>即将上线</p>
        <div class="card-footer"><button type="button" class="btn">GO</button></div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { inject } from 'vue'
const log = inject('log')
</script>

<style scoped>
.page { display: block; }
</style>
