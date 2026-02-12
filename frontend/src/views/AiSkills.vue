<template>
  <section class="page">
    <h2 class="section-title">AI-Skills</h2>
    <p class="sub">技能与效率工具</p>
    <div class="cards">
      <div class="card placeholder" @click="log('SY-Skills 开发中')">
        <div class="card-head"><h3>SY-Skills</h3><span class="card-by">--by: 黄通</span></div>
        <p>技能与效率工具集</p>
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
