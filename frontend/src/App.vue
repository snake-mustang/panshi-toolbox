<template>
  <div class="app">
    <div class="root">
      <aside class="sidebar" :class="{ collapsed }">
        <div class="sidebar-header">
          <span class="sidebar-title">盘古</span>
          <button type="button" class="sidebar-toggle" @click="collapsed = !collapsed" title="展开/收起侧边栏">
            <span class="chevron">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#cc7a60" stroke-width="2"><path d="M15 18l-6-6 6-6"/></svg>
            </span>
          </button>
        </div>
        <div class="nav-wrap">
          <nav class="nav">
            <router-link v-for="item in navItems" :key="item.path" :to="item.path" class="nav-link" active-class="router-link-active">
              <span class="nav-btn-icon" v-html="item.icon"></span>
              <span>{{ item.label }}</span>
            </router-link>
          </nav>
        </div>
        <div class="sidebar-footer">
          【盘古】开发工具箱 · v1.0.0<br />按 F1 最小化 / 唤起
        </div>
      </aside>
      <main class="content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" :key="$route.path" />
          </transition>
        </router-view>
      </main>
    </div>
    <div class="console-wrap">
      <div class="console-actions">
        <button type="button" class="console-toggle" @click="consoleOpen = !consoleOpen" title="点击展开/收起">📋</button>
      </div>
      <div class="console" :class="{ open: consoleOpen }" ref="consoleEl">
        <div v-for="(line, i) in logLines" :key="i" class="line">{{ line }}</div>
      </div>
    </div>

    <!-- API一键接入弹窗 -->
    <div class="modal-overlay" :class="{ visible: apiModalVisible }" @click.self="apiModalVisible = false">
      <div class="modal-box" role="dialog">
        <div class="modal-header">一键接入API接口</div>
        <div class="modal-body">
          <p class="guide">请在 <strong>APIFOX</strong> 中复制为 OpenAPI/Swagger 后粘贴到下方。</p>
          <div class="guide-image-wrap">
            <img src="https://pingtai-img.shiyue.com/bbs/ai/ps-ex-api.png" alt="示例图" class="guide-image" @click="imageEnlarged = true" />
            <p class="guide-image-caption">（点击图片可查看大图）</p>
          </div>
          <textarea v-model="apiPasteText" class="api-paste" placeholder="在此粘贴 OpenAPI / Swagger 文档内容（JSON 或 YAML）…"></textarea>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn" @click="applyApi">应用</button>
          <button type="button" class="btn btn-close" @click="apiModalVisible = false">关闭</button>
        </div>
      </div>
    </div>

    <div class="image-lightbox" :class="{ visible: imageEnlarged }" @click="imageEnlarged = false">
      <img src="https://pingtai-img.shiyue.com/bbs/ai/ps-ex-api.png" alt="示例图" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, provide, nextTick } from 'vue'
import { usePywebview } from '@/composables/usePywebview'

const collapsed = ref(JSON.parse(localStorage.getItem('sidebarCollapsed') || 'true'))
const consoleOpen = ref(false)
const logLines = ref([])
const consoleEl = ref(null)
const apiModalVisible = ref(false)
const imageEnlarged = ref(false)
const apiPasteText = ref('')

const navItems = [
  { path: '/', label: '首页', icon: '<svg viewBox="0 0 24 24"><path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>' },
  { path: '/ai-skills', label: 'AI-Skills', icon: '<svg viewBox="0 0 24 24"><polygon points="12 2 15 9 22 9 17 14 18 22 12 18 6 22 7 14 2 9 9 9"/></svg>' },
  { path: '/dev', label: '开发工具箱', icon: '<svg viewBox="0 0 24 24"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>' },
  { path: '/ops', label: '运营工具箱', icon: '<svg viewBox="0 0 24 24"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>' },
  { path: '/more', label: '更多工具', icon: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/><circle cx="5" cy="12" r="1"/></svg>' },
]

const { getApi } = usePywebview()

function log(msg) {
  const line = '[' + new Date().toLocaleTimeString('zh-CN', { hour12: false }) + '] ' + msg
  logLines.value.push(line)
  getApi().then(api => { if (api && api.log) api.log(msg) })
  nextTick(() => {
    if (consoleEl.value) consoleEl.value.scrollTop = consoleEl.value.scrollHeight
  })
}

function copyLogs() {
  const text = logLines.value.join('\n').trim()
  if (!text) { log('当前无日志可复制'); return }
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(() => log('已复制日志到剪贴板')).catch(() => fallbackCopy(text))
  } else {
    fallbackCopy(text)
  }
}

function fallbackCopy(text) {
  const ta = document.createElement('textarea')
  ta.value = text
  ta.style.cssText = 'position:fixed;left:-9999px;'
  document.body.appendChild(ta)
  ta.select()
  try {
    document.execCommand('copy')
    log('已复制日志到剪贴板')
  } catch (e) {
    log('复制失败')
  }
  document.body.removeChild(ta)
}

provide('log', log)
provide('getApi', getApi)

const API_RULE_PREFIX = `请严格根据下方提供的 OpenAPI/Swagger 文档，为当前 WEB 前端项目生成或更新完整的接口封装层。请按以下规则逐项落实：

## 一、总体要求
1. 以文档中的 paths 为准，为每个接口生成对应的请求函数，不要遗漏或合并接口。
2. 若项目已有接口文件（如 api/*.ts、services/*.ts、request 封装等），请在现有结构上增量更新或新增，保持风格一致；若没有则新建合理的目录与文件（如 src/api 或 src/services）。
3. 所有生成的代码需符合当前项目已使用的技术栈（如 axios/fetch、Vue/React 等），并遵循项目现有代码风格与目录约定。

## 二、请求函数规范
1. 命名：按接口 path 与 method 生成语义化函数名，如 getUserId、postLogin、putUserInfo。优先使用文档中的 summary/operationId，若无则自拟。
2. 参数：路径参数、query 参数、header 按文档定义为准，以函数参数或 options 对象传入；requestBody 作为单独参数或合并进 options，类型与文档 schema 一致。
3. 返回值：函数返回类型为 Promise<ResponseType>，ResponseType 由文档中该接口的 responses（优先 200）的 schema 推导出 TypeScript 类型。
4. 每个请求函数需带上完整的 JSDoc：描述、@param、@returns、必要时 @example，便于编辑器提示与后续维护。

## 三、TypeScript 类型
1. 为文档中的 requestBody、responses、parameters 等生成对应的 interface 或 type，集中放在类型文件（如 api/types.ts）或与接口同文件。
2. 若文档使用 components/schemas，请为每个 schema 生成 TS 类型，并在接口请求/响应中引用。
3. 泛型：若响应为通用结构（如 { code, data, message }），请使用泛型表示 data 部分，便于各接口复用。
4. 枚举与字面量：文档中的 enum 请生成为 TypeScript 的 union 或 enum 类型。

## 四、JSDoc 与注释
1. 每个请求函数上方必须有 JSDoc 块，包含：接口说明、参数说明、返回值说明。
2. 若文档中有 description、summary、deprecated 等，请体现在注释中。
3. 复杂参数或业务含义请在注释中简要说明，便于 Cursor 与后续开发者理解。

## 五、统一错误处理与请求封装
1. 若项目已有 axios/fetch 封装与统一错误处理（如拦截器、错误码映射），请在生成的接口中复用，不要重复造轮子。
2. 若没有，可生成或补充：请求 baseURL 配置、超时、请求/响应拦截器、统一错误提示（如 message 或 toast）、未授权时的处理（如跳转登录）。
3. 接口函数内部应调用统一封装后的 request 方法，不要裸写 fetch/axios。

## 六、其他约定
1. baseURL：可从环境变量或项目现有配置读取（如 import.meta.env.VITE_API_BASE、process.env.REACT_APP_API 等），与文档中 server 或 host 对应即可。
2. 请求头：若文档要求固定 header（如 Content-Type、Authorization），请在封装层或接口注释中体现；鉴权 token 建议从统一位置（如 store、cookie）读取并注入。
3. 路径与文档一致：接口 path 与 method 必须与 OpenAPI 文档一致，避免手写错误；若有 path 参数，请用占位符或模板字符串正确拼接。
4. 生成后请自检：类型无 any 遗漏、无未定义变量、导出名称与用法一致，并符合项目现有 ESLint/TS 规则。

请先阅读下方完整的 OpenAPI/Swagger 文档，再按上述规则生成或更新前端接口代码。

---\n\n`

function isOpenApi(text) {
  if (!text || typeof text !== 'string') return false
  const t = text.trim()
  if (t.startsWith('{')) {
    try {
      const j = JSON.parse(t)
      return !!(j.openapi || j.swagger || j.paths)
    } catch { return false }
  }
  return t.startsWith('openapi:') || t.startsWith('swagger:') || t.includes('\npaths:')
}

async function applyApi() {
  const raw = apiPasteText.value.trim()
  if (!raw) {
    log('请先粘贴 OpenAPI/Swagger 内容')
    return
  }
  if (!isOpenApi(raw)) {
    log('内容看起来不是有效的 OpenAPI/Swagger 文档')
    return
  }
  const full = API_RULE_PREFIX + raw
  try {
    await navigator.clipboard.writeText(full)
    log('已复制到剪贴板（规则+接口文档）')
    apiModalVisible.value = false
    getApi().then(api => { if (api && api.open_cursor) api.open_cursor() })
    setTimeout(() => {
      getApi().then(api => {
        if (api && api.show_message_box) {
          api.show_message_box('已复制到剪贴板', '请到 Cursor 的 Agent 输入区按 Ctrl+V 粘贴后发送。\n\n在 Agent 对话框中粘贴即可让 AI 按规则生成接口代码。')
        }
      })
    }, 1500)
  } catch (e) {
    log('剪贴板写入失败：' + (e.message || e))
  }
}

onMounted(() => {
  if (import.meta.env.DEV) log('Vue 开发模式')
  window.addEventListener('keydown', (e) => {
    if (e.key === 'F1') {
      e.preventDefault()
      getApi().then(api => { if (api && api.minimize_window) api.minimize_window(); log('已最小化') })
    }
  })
  window.addEventListener('open-api-one-click-modal', () => { apiModalVisible.value = true })
})

import { watch } from 'vue'
watch(collapsed, v => localStorage.setItem('sidebarCollapsed', JSON.stringify(v)))
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from,
.fade-leave-to { opacity: 0; }
.app { display: flex; flex-direction: column; height: 100vh; }

.guide { font-size: 13px; color: #64748b; line-height: 1.5; margin-bottom: 12px; }
.guide-image-wrap { margin: 16px 0; text-align: center; }
.guide-image { max-width: 100%; height: auto; cursor: pointer; border: 1px solid #e2e8f0; border-radius: 4px; transition: transform 0.2s; }
.guide-image:hover { transform: scale(1.02); }
.guide-image-caption { font-size: 12px; color: #64748b; margin-top: 8px; }
.api-paste { width: 100%; min-height: 220px; border: 0.5px solid rgba(0,0,0,0.12); border-radius: 12px; padding: 12px; font-size: 13px; font-family: ui-monospace, monospace; background: #f8fafc; resize: vertical; box-sizing: border-box; }
.btn-close { background: #94a3b8; }
.image-lightbox { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.9); display: none; align-items: center; justify-content: center; z-index: 10000; cursor: pointer; }
.image-lightbox.visible { display: flex; }
.image-lightbox img { max-width: 90%; max-height: 90%; border-radius: 8px; box-shadow: 0 8px 32px rgba(0,0,0,0.5); }
</style>
