<template>
  <section class="page">
    <h2 class="section-title">运营工具箱</h2>
    <p class="sub">运营相关工具（敬请期待）</p>
    <div class="cards">
      <div class="card placeholder">
        <div class="card-head"><h3>运营工具</h3><span class="card-by">--by: 黄通</span></div>
        <p>即将上线</p>
        <div class="card-footer"><button type="button" class="btn">GO</button></div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { inject } from 'vue'
inject('log')('运营工具箱')
</script>

<style scoped>
.page { display: block; }
</style>
