# 【盘古】开发工具箱

本地开发与效率小工具：截图、OCR 识字、批量处理等，贴合 AI 与自动化工作流。支持按 F1 全局唤起/最小化。

## 运行方式

- **桌面应用（完整功能）**  
  ```bash
  python run_webview.py
  ```
  或双击 `run_webview.bat`。会启动 pywebview 窗口并加载 `static/index.html`，后端 API 通过 `window.pywebview.api` 暴露给前端。

- **仅预览页面（不启动 Python）**  
  在项目根目录执行：
  ```bash
  npm run dev
  ```
  会启动静态服务，浏览器访问 http://localhost:5173 查看 `static/` 下的页面。此时无后端，截图、OCR 等需后端的功能不可用。

## 前端：static 与 frontend 的关系

- **当前实际使用的是 `static/`**  
  `run_webview.py` 启动的本地服务根目录是 `static/`，打开的地址是 `http://127.0.0.1:8765/index.html`，即 **`static/index.html`**。所有你看到的界面和交互都来自这里（单页 HTML + 内联/同目录下的 CSS、JS）。

- **`frontend/` 是独立的 Vue 项目**  
  未在 `run_webview.py` 里被引用，属于历史或备用前端。若以后要改用 Vue 作为界面，需要修改 `run_webview.py` 的 `STATIC_DIR` 和入口 URL 指向 `frontend/dist`（并先执行 `npm run build`）。

## 如何加逻辑

逻辑都围绕 **static 单页 + Python 后端**：

1. **页面与交互**  
   - 在 `static/index.html` 里改 HTML、样式和 `<script>`。
   - 需要更清晰结构时，可把脚本拆到 `static/app.js`，在 HTML 里用 `<script src="app.js"></script>` 引入。

2. **调用后端**  
   - 在页面脚本中通过 `window.pywebview.api.方法名()` 调用后端。
   - 仅在「用 `python run_webview.py` 启动的桌面窗口」里才有 `pywebview.api`；用 `npm run dev` 纯静态预览时 `window.pywebview` 不存在，需做存在性判断或兼容。

3. **后端接口**  
   - 在 `backend/api_webview.py` 的 `Api` 类里增加方法，保存后重启 `run_webview.py`，即可在前端用 `window.pywebview.api.新方法名()` 调用。

示例（前端调用后端）：

```javascript
if (window.pywebview && window.pywebview.api) {
  window.pywebview.api.capture_full().then(function(dataUrl) {
    // 使用 dataUrl
  });
}
```

## 项目结构（简要）

```
├── run_webview.py      # 桌面应用入口（pywebview + 本地 HTTP 服务）
├── static/
│   └── index.html      # 当前唯一在用的前端页面（含样式与脚本）
├── backend/
│   ├── api_webview.py  # 暴露给前端的 API（截图、OCR、最小化等）
│   ├── region_capture.py
│   ├── screenshot.py
│   └── ocr_engine.py
├── frontend/            # Vue 项目，当前未接入 run_webview
├── package.json         # 根目录：npm run dev 用于预览 static
└── requirements.txt
```

## 打包

使用 PyInstaller 打包为 exe 时，需把 `static/` 打进包内；`run_webview.py` 中已通过 `sys._MEIPASS` 处理打包后的资源路径。具体可参考项目内的 `build.bat` 或打包说明。

## 快捷键

- **F1**：在窗口内按可最小化；在任意位置按可唤起/前置工具箱（需以 `run_webview.py` 启动的桌面应用为准）。
