<template>
  <section class="page">
    <h2>长截图</h2>
    <p class="sub">PixPin 式：点击「一键截图」后先框选要截取的屏幕区域，再手动用滚轮或滚动条滚动内容，程序会自动拼接成长图；在浮窗点「完成」结束并复制到剪贴板。</p>
    <button type="button" class="btn" @click="startLongScreenshot" :disabled="capturing">一键截图</button>
    <div class="preview-wrap" style="margin-top: 20px;">
      <img v-if="previewUrl" :src="previewUrl" alt="长图预览" style="max-width: 100%; max-height: 400px; border-radius: 8px;" />
      <span v-else class="placeholder">长图预览（完成后可在此查看，或直接 Ctrl+V 粘贴到其他应用）</span>
    </div>
    <div v-if="doneVisible" class="api-done-overlay visible" @click.self="doneVisible = false">
      <div class="api-done-box">
        <div class="title">截图已完成</div>
        <p class="tip">长图已复制到剪贴板，可直接 <strong>Ctrl + V</strong> 粘贴使用。</p>
        <button type="button" class="btn-ok" @click="doneVisible = false">知道了</button>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, inject, onMounted } from 'vue'

const log = inject('log')
const getApi = inject('getApi')
const previewUrl = ref('')
const capturing = ref(false)
const doneVisible = ref(false)

async function startLongScreenshot() {
  const api = await getApi()
  if (!api || !api.capture_long_screenshot) {
    log('长截图需要 pywebview 环境')
    return
  }
  capturing.value = true
  previewUrl.value = ''
  try {
    log('开始长截图（请框选区域，再手动滚动内容，完成后点击浮窗「完成」）')
    const dataUrl = await api.capture_long_screenshot()
    if (dataUrl) {
      previewUrl.value = dataUrl
      doneVisible.value = true
      log('长截图完成')
      if (api.bring_window_to_front) api.bring_window_to_front()
    } else {
      log('已取消或长截图未获取到内容')
    }
  } catch (e) {
    log('长截图错误: ' + (e.message || e))
  } finally {
    capturing.value = false
  }
}

onMounted(() => {
  log('长截图页：PixPin 式，框选区域后手动滚动，自动拼接')
})
</script>

<style scoped>
.page { display: block; }
</style>
