<template>
  <section class="page">
    <h2>截图识字</h2>
    <p class="sub">截屏并识别：先区域截图（拖拽选区），再识别选区内的文字</p>
    <button type="button" class="btn" @click="captureAndOcr" :disabled="loading">截屏并识别</button>
    <div style="margin-top:16px; font-size:15px; color:#3a3a3c;">识别结果</div>
    <textarea v-model="ocrResult" class="result-edit" placeholder="识别结果将显示在这里"></textarea>
  </section>
</template>

<script setup>
import { ref, inject } from 'vue'

const log = inject('log')
const getApi = inject('getApi')
const ocrResult = ref('')
const loading = ref(false)

async function captureAndOcr() {
  const api = await getApi()
  if (!api || !api.capture_region_interactive) {
    log('截图识字需要 pywebview 环境')
    return
  }
  loading.value = true
  ocrResult.value = '请拖拽选择要识别的区域…'
  try {
    const dataUrl = await api.capture_region_interactive()
    if (!dataUrl) {
      ocrResult.value = ''
      return
    }
    ocrResult.value = '识别中…'
    const text = await api.ocr_from_data_url(dataUrl)
    ocrResult.value = text || '(无文字)'
    log('识别完成')
  } catch (e) {
    ocrResult.value = '[错误] ' + (e.message || e)
    log('OCR 错误: ' + e)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.page { display: block; }
</style>
