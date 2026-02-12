<template>
  <section class="page">
    <h2>一键接入API接口</h2>
    <p class="sub">从 APIFOX 复制 OpenAPI/Swagger，粘贴到弹窗后一键生成 Cursor Agent 可用的「规则+接口」内容，复制到剪贴板并在 Cursor 中粘贴即可。</p>
    <button type="button" class="btn" @click="modalVisible = true">一键应用</button>

    <div class="modal-overlay" :class="{ visible: modalVisible }" @click.self="modalVisible = false">
      <div class="modal-box" role="dialog">
        <div class="modal-header">一键接入API接口</div>
        <div class="modal-body">
          <p class="guide">请在 <strong>APIFOX</strong> 中复制为 OpenAPI/Swagger 后粘贴到下方。</p>
          <div class="guide-image-wrap">
            <img src="https://pingtai-img.shiyue.com/bbs/ai/ps-ex-api.png" alt="示例图" class="guide-image" @click="imageEnlarged = true" />
            <p class="guide-image-caption">（点击图片可查看大图）</p>
          </div>
          <textarea v-model="pasteText" class="api-paste" placeholder="在此粘贴 OpenAPI / Swagger 文档内容（JSON 或 YAML）…"></textarea>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn" @click="apply">应用</button>
          <button type="button" class="btn" style="background:#94a3b8;" @click="modalVisible = false">关闭</button>
        </div>
      </div>
    </div>

    <div class="image-lightbox" :class="{ visible: imageEnlarged }" @click="imageEnlarged = false">
      <img src="https://pingtai-img.shiyue.com/bbs/ai/ps-ex-api.png" alt="示例图" />
    </div>

    <div class="api-done-overlay" :class="{ visible: apiDoneVisible }" @click.self="apiDoneVisible = false">
      <div class="api-done-box">
        <div class="title">已复制到剪贴板</div>
        <p class="tip">请到 Cursor 的 <strong>Agent 输入区</strong> 使用：<kbd>Ctrl + V</kbd> 粘贴后发送。</p>
        <button type="button" class="btn-ok" @click="apiDoneVisible = false">知道了</button>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, inject, onMounted } from 'vue'

const log = inject('log')
const getApi = inject('getApi')
const modalVisible = ref(false)
const apiDoneVisible = ref(false)
const imageEnlarged = ref(false)
const pasteText = ref('')

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

async function apply() {
  const raw = pasteText.value.trim()
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
    modalVisible.value = false
    apiDoneVisible.value = true
    getApi().then(api => { if (api && api.open_cursor) api.open_cursor() })
  } catch (e) {
    log('剪贴板写入失败：' + (e.message || e))
  }
}

onMounted(() => {
  window.addEventListener('open-api-one-click-modal', () => { modalVisible.value = true })
})
</script>

<style scoped>
.page { display: block; }
.guide-image-wrap { margin: 16px 0; text-align: center; }
.guide-image { max-width: 100%; height: auto; cursor: pointer; border: 1px solid #e2e8f0; border-radius: 4px; transition: transform 0.2s; }
.guide-image:hover { transform: scale(1.02); }
.guide-image-caption { font-size: 12px; color: #64748b; margin-top: 8px; }
.image-lightbox { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.9); display: none; align-items: center; justify-content: center; z-index: 10000; cursor: pointer; }
.image-lightbox.visible { display: flex; }
.image-lightbox img { max-width: 90%; max-height: 90%; border-radius: 8px; box-shadow: 0 8px 32px rgba(0,0,0,0.5); }
</style>
