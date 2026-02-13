<template>
  <section class="page">
    <h2>截图识字</h2>
    <p class="sub">截屏并识别：先区域截图（拖拽选区），再识别选区内的文字</p>
    <div style="display: flex; gap: 12px; margin-bottom: 16px;">
      <button type="button" class="btn" @click="captureAndOcr" :disabled="loading">截屏并识别</button>
      <button type="button" class="btn btn-secondary" @click="fullScreenOcr" :disabled="loading">全屏识别</button>
    </div>
    <div style="margin-top:16px; font-size:15px; color:#3a3a3c; display: flex; align-items: center; gap: 8px;">
      <span>识别结果</span>
      <button 
        v-if="capturedImage" 
        type="button" 
        class="preview-icon-btn" 
        @click="showPreview = true"
        title="查看截图预览"
      >
        🖼️
      </button>
    </div>
    <textarea v-model="ocrResult" class="result-edit" placeholder="识别结果将显示在这里"></textarea>

    <!-- 截图预览弹窗 -->
    <div v-if="showPreview" class="preview-overlay" @click.self="showPreview = false">
      <div class="preview-box">
        <div class="preview-header">
          <span>截图预览</span>
          <button type="button" class="preview-close" @click="showPreview = false">✕</button>
        </div>
        <div class="preview-body">
          <img :src="capturedImage" alt="截图预览" class="preview-img" />
        </div>
      </div>
    </div>

    <!-- AI分析总结模块 -->
    <div class="ai-section">
      <div class="ai-header">
        <span class="ai-title">AI分析总结（诗悦私有化部署 · Qwen/Gemini）</span>
        <label class="switch">
          <input type="checkbox" v-model="aiEnabled" />
          <span class="slider"></span>
        </label>
      </div>
      
      <div v-show="aiEnabled" class="ai-content">
        <div class="ai-prompt-section">
          <label class="ai-label">提示词</label>
          <textarea 
            v-model="aiPrompt" 
            class="ai-prompt-input" 
            placeholder="请输入你的提示词，例如：&#10;- 总结上述文字的主要内容&#10;- 提取关键信息并分类&#10;- 翻译成英文"
            rows="4"
          ></textarea>
        </div>
        
        <button 
          type="button" 
          class="btn btn-ai" 
          @click="analyzeWithAi" 
          :disabled="aiAnalyzing || !ocrResult"
        >
          <span v-if="!aiAnalyzing">开始分析</span>
          <span v-else>分析中...</span>
        </button>
        
          <div class="ai-result-section">
            <label class="ai-label">
              <span>分析结果</span>
              <button 
                v-if="aiResult" 
                type="button" 
                class="copy-result-btn" 
                @click="copyAiResult"
                title="复制分析结果"
              >
                📋
              </button>
            </label>
            <div class="ai-result" :class="{ empty: !aiResult }">
              {{ aiResult || '分析结果将显示在这里' }}
            </div>
          </div>
      </div>
    </div>

    <!-- 复制成功提示 -->
    <transition name="toast-fade">
      <div v-if="copySuccess" class="toast-notification">
        <span class="toast-icon">✓</span>
        <span class="toast-text">复制成功</span>
      </div>
    </transition>
  </section>
</template>

<script setup>
import { ref, inject } from 'vue'

const log = inject('log')
const getApi = inject('getApi')
const ocrResult = ref('')
const loading = ref(false)
const capturedImage = ref('') // 保存截图用于预览
const showPreview = ref(false) // 控制预览弹窗
const copySuccess = ref(false) // 控制复制成功提示

// AI分析相关状态
const aiEnabled = ref(false)
const aiPrompt = ref('')
const aiResult = ref('')
const aiAnalyzing = ref(false)

async function captureAndOcr() {
  const api = await getApi()
  if (!api || !api.capture_region_interactive) {
    log('截图识字需要 pywebview 环境')
    return
  }
  loading.value = true
  ocrResult.value = '请拖拽选择要识别的区域…'
  capturedImage.value = '' // 清空之前的截图
  try {
    const dataUrl = await api.capture_region_interactive()
    if (!dataUrl) {
      ocrResult.value = ''
      return
    }
    capturedImage.value = dataUrl // 保存截图
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

async function fullScreenOcr() {
  const api = await getApi()
  if (!api || !api.capture_fullscreen_for_ocr) {
    log('全屏识别需要 pywebview 环境')
    return
  }
  loading.value = true
  ocrResult.value = '正在截取全屏…'
  capturedImage.value = '' // 清空之前的截图
  try {
    const dataUrl = await api.capture_fullscreen_for_ocr()
    if (!dataUrl) {
      ocrResult.value = ''
      log('全屏截图失败')
      return
    }
    capturedImage.value = dataUrl // 保存全屏截图
    ocrResult.value = '识别中…'
    const text = await api.ocr_from_data_url(dataUrl)
    ocrResult.value = text || '(无文字)'
    log('全屏识别完成')
  } catch (e) {
    ocrResult.value = '[错误] ' + (e.message || e)
    log('全屏识别错误: ' + e)
  } finally {
    loading.value = false
  }
}

async function analyzeWithAi() {
  if (!ocrResult.value) {
    log('请先进行截图识字')
    return
  }
  
  aiAnalyzing.value = true
  aiResult.value = ''
  log('开始 AI 分析...')
  
  try {
    const api = await getApi()
    if (!api || !api.analyze_text_with_ai_stream) {
      aiResult.value = '[错误] AI 分析功能不可用'
      log('AI 分析接口不存在')
      return
    }
    
    const result = await api.analyze_text_with_ai_stream(ocrResult.value, aiPrompt.value)
    
    if (result.status === 'success' && result.chunks && result.chunks.length > 0) {
      // 打字机效果：逐字显示
      aiResult.value = ''
      let fullText = result.content
      let currentIndex = 0
      
      const typeWriter = () => {
        if (currentIndex < fullText.length) {
          aiResult.value += fullText[currentIndex]
          currentIndex++
          // 调整速度：中文字符慢一点，标点符号快一点
          const char = fullText[currentIndex - 1]
          const delay = /[\u4e00-\u9fa5]/.test(char) ? 30 : 10
          setTimeout(typeWriter, delay)
        } else {
          log('AI 分析完成')
        }
      }
      
      typeWriter()
    } else {
      aiResult.value = result.content || '(无返回结果)'
      log('AI 分析完成')
    }
  } catch (e) {
    aiResult.value = '[错误] ' + (e.message || e)
    log('AI 分析错误: ' + e)
  } finally {
    aiAnalyzing.value = false
  }
}

async function copyAiResult() {
  if (!aiResult.value) {
    return
  }
  
  try {
    await navigator.clipboard.writeText(aiResult.value)
    log('分析结果已复制到剪贴板')
    showCopySuccess()
  } catch (e) {
    // 备用方案：使用后端复制
    try {
      const api = await getApi()
      if (api && api.copy_to_clipboard) {
        const success = await api.copy_to_clipboard(aiResult.value)
        if (success) {
          log('分析结果已复制到剪贴板')
          showCopySuccess()
        } else {
          log('复制失败')
        }
      }
    } catch (err) {
      log('复制失败: ' + (err.message || err))
    }
  }
}

function showCopySuccess() {
  copySuccess.value = true
  setTimeout(() => {
    copySuccess.value = false
  }, 2000)
}
</script>

<style scoped>
.page { 
  display: block;
  padding-bottom: 40px;
}

/* 预览图标按钮 */
.preview-icon-btn {
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: all 0.2s;
}

.preview-icon-btn:hover {
  background: #f3f4f6;
  transform: scale(1.1);
}

/* 截图预览弹窗 */
.preview-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.75);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  animation: fadeIn 0.2s;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.preview-box {
  background: white;
  border-radius: 8px;
  max-width: 90vw;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
  font-weight: 600;
  font-size: 16px;
}

.preview-close {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  color: #6b7280;
  padding: 4px 8px;
  border-radius: 4px;
  transition: all 0.2s;
}

.preview-close:hover {
  background: #f3f4f6;
  color: #1f2937;
}

.preview-body {
  padding: 20px;
  overflow: auto;
  max-height: calc(90vh - 60px);
}

.preview-img {
  max-width: 100%;
  height: auto;
  display: block;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* AI分析模块样式 - 简化版 */
.ai-section {
  margin-top: 32px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: white;
  overflow: hidden;
}

.ai-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 18px;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}

.ai-title {
  font-size: 15px;
  font-weight: 500;
  color: #374151;
}

/* Switch开关样式 */
.switch {
  position: relative;
  display: inline-block;
  width: 44px;
  height: 24px;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #d1d5db;
  transition: 0.3s;
  border-radius: 24px;
}

.slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: 0.3s;
  border-radius: 50%;
}

input:checked + .slider {
  background-color: #3b82f6;
}

input:checked + .slider:before {
  transform: translateX(20px);
}

/* AI内容区域 */
.ai-content {
  padding: 18px;
}

.ai-prompt-section,
.ai-result-section {
  margin-bottom: 14px;
}

.ai-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #374151;
}

.copy-result-btn {
  background: none;
  border: none;
  font-size: 16px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: all 0.2s;
  opacity: 0.6;
}

.copy-result-btn:hover {
  background: #f3f4f6;
  opacity: 1;
  transform: scale(1.1);
}

.ai-prompt-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 14px;
  font-family: inherit;
  resize: vertical;
  transition: border-color 0.2s;
}

.ai-prompt-input:focus {
  outline: none;
  border-color: #3b82f6;
}

.btn-ai {
  width: 100%;
  background: #3b82f6;
  color: white;
  padding: 10px 20px;
  font-size: 14px;
  font-weight: 500;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 14px;
}

.btn-ai:hover:not(:disabled) {
  background: #2563eb;
}

.btn-ai:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.ai-result {
  min-height: 100px;
  padding: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  background: #f9fafb;
  font-size: 14px;
  line-height: 1.6;
  color: #1f2937;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.ai-result.empty {
  color: #9ca3af;
  font-style: italic;
}

/* 复制成功提示 Toast */
.toast-notification {
  position: fixed;
  top: 80px;
  left: 50%;
  transform: translateX(-50%);
  background: #10b981;
  color: white;
  padding: 12px 24px;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 500;
  z-index: 10000;
}

.toast-icon {
  font-size: 18px;
  font-weight: bold;
}

.toast-fade-enter-active,
.toast-fade-leave-active {
  transition: all 0.3s ease;
}

.toast-fade-enter-from {
  opacity: 0;
  transform: translateX(-50%) translateY(-10px);
}

.toast-fade-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(-10px);
}
</style>
