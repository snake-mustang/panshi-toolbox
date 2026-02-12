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
        <button type="button" class="console-toggle" @click="consoleOpen = !consoleOpen" title="点击展开/收起">📋 日志</button>
        <button type="button" class="console-copy" @click="copyLogs" title="复制全部日志">复制日志</button>
      </div>
      <div class="console" :class="{ open: consoleOpen }" ref="consoleEl">
        <div v-for="(line, i) in logLines" :key="i" class="line">{{ line }}</div>
      </div>
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

onMounted(() => {
  if (import.meta.env.DEV) log('Vue 开发模式')
  window.addEventListener('keydown', (e) => {
    if (e.key === 'F1') {
      e.preventDefault()
      getApi().then(api => { if (api && api.minimize_window) api.minimize_window(); log('已最小化') })
    }
  })
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
</style>
