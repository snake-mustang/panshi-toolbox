<template>
  <section class="page">
    <div class="hero-wrap">
      <div class="hero-left">
        <div class="hero-dots">
          <span class="r"></span><span class="y"></span><span class="g"></span>
          <span class="hero-dots-label">PanGu · ToolBox · 运营服务组</span>
        </div>
        <div class="hero-file"><span class="slash">//</span> main.ts</div>
        <h1 class="hero-title"><span class="gt">&gt;</span> <span class="hero-title-main">盘古</span><span class="hero-title-sub">开发工具箱</span><span class="hero-cursor"></span></h1>
        <p class="hero-sub"><span class="gt">&gt;</span> 贴合 AI 工作流与智能助手生态，支持自动化脚本、快捷指令与工作流编排，提升日常与开发效率。</p>
        <div class="hero-code-card">
          <div>
            <div class="code-line"><span class="kw">const</span> usageCount <span class="muted">=</span> <span class="num">{{ usageCount }}</span><span class="muted">;</span></div>
            <div class="cm"><span class="green">// </span>平台累计使用次数</div>
          </div>
          <button type="button" class="hero-usage-refresh" @click="refreshUsage" title="刷新">↻</button>
        </div>
      </div>
      <div class="hero-right">
        <div class="hero-chart-panel">
          <div class="hero-chart-header">
            <span class="dot tr"></span><span class="dot ty"></span><span class="dot tg"></span>
            <span class="label">trend-analytics.tsx</span>
          </div>
          <div class="hero-chart-body">
            <div class="hero-chart-inner">
              <svg viewBox="0 0 486 288" width="100%" height="100%" style="display:block" preserveAspectRatio="xMidYMid meet">
                <defs><linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="rgba(14,165,233,0.5)"/><stop offset="100%" stop-color="rgba(14,165,233,0)"/></linearGradient></defs>
                <path fill="url(#areaGrad)" stroke="none" d="M40,250 C120,250 120,160 200,130 C280,100 360,70 481,47 L481,258 L40,258 Z"/>
                <path class="hero-chart-line" d="M40,250 C120,250 120,160 200,130 C280,100 360,70 481,47"/>
              </svg>
            </div>
            <p class="hero-chart-caption">根据 skill 最后 push 时间统计，非当日提交的数量</p>
          </div>
        </div>
      </div>
    </div>
    <div class="section-title section-title-recommend">推荐工具</div>
    <div class="cards">
      <div class="card card-wrap card-featured" @click="openApiModal">
        <span class="card-badge" title="推荐"><svg viewBox="0 0 24 24"><polygon points="12 2 15 9 22 9 17 14 18 22 12 18 6 22 7 14 2 9 9 9"/></svg></span>
        <div class="card-head"><h3>一键接入API接口</h3><span class="card-by">--by: 黄通</span></div>
        <p>从 APIFOX 复制 OpenAPI/Swagger，生成规则并复制到剪贴板，在 Cursor Agent 中粘贴即可快速生成前端接口。</p>
        <div class="card-footer"><button type="button" class="btn" aria-label="一键应用">一键应用</button></div>
      </div>
      <div class="card" @click="go('/ocr')">
        <div class="card-head"><h3>截图识字</h3><span class="card-by">--by: 黄通</span></div>
        <p>框选区域截图，自动识别图中文字并复制到剪贴板</p>
        <div class="card-footer"><button type="button" class="btn" aria-label="打开">打开</button></div>
      </div>
      <div class="card placeholder">
        <div class="card-head"><h3>批量添加水印</h3><span class="card-by">--by: 黄通</span></div>
        <p>为多张图片/多个视频批量添加文字水印</p>
        <div class="card-footer"><button type="button" class="btn">已完成，待接入</button></div>
      </div>
      <div class="card placeholder">
        <div class="card-head"><h3>数据分析</h3><span class="card-by">--by: 黄通</span></div>
        <p>数据统计与可视化</p>
        <div class="card-footer"><button type="button" class="btn">打开</button></div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, inject, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const log = inject('log')
const getApi = inject('getApi')
const usageCount = ref(0)

const QS_BASE = 'https://pre-qs-api.shiyue.com/api/curd'
const QS_SECRET = 'Guf0jwTNrHXpJgxe9L16h4Y0Vcvme=6U'
const QS_PLATFORM = 'pangu-toolbox'
const QS_SCOPE = 'api-one-click-usage'

async function getUsage() {
  try {
    const ts = Math.floor(Date.now() / 1000)
    const msg = 'timestamp=' + ts
    const key = await crypto.subtle.importKey('raw', new TextEncoder().encode(QS_SECRET), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign'])
    const sig = await crypto.subtle.sign('HMAC', key, new TextEncoder().encode(msg))
    const signHex = Array.from(new Uint8Array(sig)).map(b => ('0' + b.toString(16)).slice(-2)).join('')
    const r = await fetch(QS_BASE + '/list', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Timestamp': String(ts), 'X-Sign': signHex },
      body: JSON.stringify({ platform: QS_PLATFORM, scope: QS_SCOPE, page: 1, page_size: 1 }),
    })
    const res = await r.json()
    if (res.data && typeof res.data.total === 'number') usageCount.value = res.data.total
    else if (res.data?.list?.length) usageCount.value = res.data.list.length
  } catch (e) {
    log('使用次数拉取失败：' + (e.message || e))
  }
}

function refreshUsage() {
  getUsage()
  log('已刷新使用次数')
}

function go(path) {
  router.push(path)
}

function openApiModal() {
  const event = new CustomEvent('open-api-one-click-modal')
  window.dispatchEvent(event)
}

onMounted(() => {
  getUsage()
})
</script>

<style scoped>
.page { display: block; }
</style>
