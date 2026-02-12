# -*- coding: utf-8 -*-
"""
应用入口：PyQt6 主窗口、QWebEngineView 加载 Vue、QWebChannel 桥接、全局快捷键 Ctrl+K。
"""
import os
import sys

# 在导入 Qt/WebEngine 之前设置，避免 Chromium GPU 初始化崩溃（如 DirectComposition 报错）
if sys.platform == "win32":
    os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--disable-gpu --disable-gpu-sandbox --no-sandbox")

def _log(msg):
    print(f"[启动] {msg}", flush=True)

_log("main.py 开始加载")
if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes

_log("导入 PyQt6...")
from PyQt6.QtCore import QUrl, QObject, pyqtSlot, QTimer, Qt
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel
# 不在此处导入 WebEngine，避免 import 时即初始化 Chromium 导致 show() 崩溃；在 _replace_with_web 内再导入
from PyQt6.QtGui import QKeySequence, QShortcut

# 不在此处导入任何 backend 子模块，全部延后到首次使用时导入，避免 show() 崩溃
_log("main.py 加载完成")


def _resource_path(relative: str) -> str:
    """开发/打包后资源路径：优先当前目录下的 frontend/dist。"""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    # 若在 backend 目录，则 base 为 backend，上一级为项目根
    root = os.path.dirname(base) if os.path.basename(base) == "backend" else base
    return os.path.join(root, relative)


# --------------- 全局热键：使用主窗口 HWND 注册，在 nativeEvent 中响应 ---------------
MOD_CTRL = 0x0002
MOD_NOREPEAT = 0x4000
WM_HOTKEY = 0x0312
VK_K = 0x4B
HOTKEY_ID = 1


class _MinimalWindow(QMainWindow):
    """占位窗口；同一窗口在定时器内升级为完整界面，不再 show 第二个窗口避免崩溃。"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("黄同学的AI工具箱")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)
        lab = QLabel("黄同学的AI工具箱\n\n功能暂未开放，后续可通过配置恢复。")
        lab.setStyleSheet("font-size: 14px; color: #666; padding: 40px;")
        lab.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCentralWidget(lab)
        self._ocr = None
        self._screenshot = None
        self._region_capture = None
        self._bridge = None
        self._web = None
        self._channel = None
        self._shortcut = None
        self._hotkey_registered = False

    def upgrade_to_full_ui(self):
        """在已显示的占位窗口上直接替换为 Web 界面，不新建窗口。"""
        _log("升级为完整界面")
        if self._shortcut is None:
            self._shortcut = QShortcut(QKeySequence("Ctrl+K"), self)
            self._shortcut.activated.connect(self._toggle_visibility)
        QTimer.singleShot(300, self._replace_with_web)

    def _replace_with_web(self):
        """进入事件循环后再导入并创建 Web 视图。"""
        if self._bridge is None:
            from backend.bridge import AppBridge
            self._bridge = AppBridge(screenshot_handler=None, ocr_handler=None, parent=self)
        _log("创建 OCR/截图 处理器")
        if self._ocr is None:
            from backend.ocr_engine import OcrHandler
            self._ocr = OcrHandler()
            self._bridge._ocr = self._ocr
        if self._screenshot is None:
            from backend.screenshot import ScreenshotHandler
            self._screenshot = ScreenshotHandler(on_region_captured=self._on_screenshot_captured)
            self._bridge._screenshot = self._screenshot
        _log("创建 Web 视图")
        from PyQt6.QtWebEngineWidgets import QWebEngineView
        from PyQt6.QtWebChannel import QWebChannel
        self._web = QWebEngineView(self)
        self._channel = QWebChannel(self._web.page())
        self._web.page().setWebChannel(self._channel)
        self._channel.registerObject("bridge", self._bridge)
        _log("替换为 Web 视图")
        self.takeCentralWidget()
        self.setCentralWidget(self._web)
        self._load_frontend()

    def _load_frontend(self):
        dist_dir = os.path.dirname(_resource_path("frontend/dist/index.html"))
        dist_index = os.path.join(dist_dir, "index.html")
        if os.path.isfile(dist_index):
            try:
                from backend.http_serve import start_server as start_http_server
                port = start_http_server(dist_dir)
                self._web.setUrl(QUrl(f"http://127.0.0.1:{port}/"))
            except Exception as e:
                print(f"[启动] HTTP 服务失败，改用 file: {e}", flush=True)
                self._web.setUrl(QUrl.fromLocalFile(os.path.abspath(dist_index)))
        else:
            # 开发模式：环境变量 TOOLBOX_DEV=1 时尝试加载 dev 服务器（需先 npm run dev）
            if os.environ.get("TOOLBOX_DEV") == "1":
                self._web.setUrl(QUrl("http://127.0.0.1:5173/"))
            else:
                # 未构建且未开 dev 时显示说明，避免 ERR_CONNECTION_REFUSED
                hint_html = """
                <!DOCTYPE html><html><head><meta charset="utf-8"><title>黄同学的AI工具箱</title></head>
                <body style="margin:40px;font-family:sans-serif;background:#1a1d23;color:#e4e6eb;">
                <h2>请先构建或启动前端</h2>
                <p><b>方式一（推荐）：</b>在项目目录执行：</p>
                <pre style="background:#222;padding:12px;border-radius:8px;">cd frontend\nnpm install\nnpm run build</pre>
                <p>然后关闭本窗口，重新运行 <code>python -m backend.main</code>。</p>
                <p><b>方式二：</b>先在一个终端执行 <code>cd frontend && npm run dev</code>，再在另一终端执行 <code>set TOOLBOX_DEV=1 && python -m backend.main</code>。</p>
                </body></html>
                """
                self._web.setHtml(hint_html, QUrl())

    def _toggle_visibility(self):
        if self.isVisible() and not self.isMinimized():
            self.hide()
        else:
            self.show()
            self.raise_()
            self.activateWindow()

    def _on_screenshot_captured(self, pil_image):
        """区域截图完成（全屏简化版），转 base64 通过 signal 发给前端。"""
        import base64
        import io
        buf = io.BytesIO()
        pil_image.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        self._bridge.screenshotFinished.emit(f"data:image/png;base64,{b64}")

    def _on_region_captured(self, data_url: str):
        """区域选区截图完成，发信号给前端并重新显示主窗口。"""
        self.show()
        self.raise_()
        self.activateWindow()
        self._bridge.screenshotFinished.emit(data_url)
        self._bridge.logReceived.emit("[截图] 区域截图已完成")

    def start_region_screenshot(self):
        """显示区域选区窗口；截完后由 _on_region_captured 处理。"""
        if self._region_capture is None:
            from backend.region_capture import RegionCaptureWidget
            self._region_capture = RegionCaptureWidget(
                on_captured=self._on_region_captured,
                parent=None,
            )
        self.hide()
        self._region_capture.run()

    def register_global_hotkey(self):
        """注册全局热键 Ctrl+K（需在 show 后调用）。"""
        if sys.platform != "win32":
            return
        try:
            hwnd = int(self.winId())
            if ctypes.windll.user32.RegisterHotKey(hwnd, HOTKEY_ID, MOD_CTRL | MOD_NOREPEAT, VK_K):
                self._hotkey_registered = True
        except Exception:
            pass

    def nativeEvent(self, eventType, message):
        """处理 Windows 原生消息，用于全局热键 WM_HOTKEY。"""
        if sys.platform == "win32" and eventType == b"windows_generic_MSG":
            msg = wintypes.MSG.from_address(message.__int__())
            if msg.message == WM_HOTKEY and msg.wParam == HOTKEY_ID:
                self._toggle_visibility()
                return True, 0
        return super().nativeEvent(eventType, message)

    def closeEvent(self, event):
        if sys.platform == "win32" and self._hotkey_registered:
            try:
                ctypes.windll.user32.UnregisterHotKey(int(self.winId()), HOTKEY_ID)
            except Exception:
                pass
        super().closeEvent(event)


def main():
    def log(msg):
        print(f"[启动] {msg}", flush=True)
    log("创建 QApplication")
    app = QApplication(sys.argv)
    app.setApplicationName("IT Toolbox")
    log("创建窗口")
    win = _MinimalWindow()
    log("显示窗口")
    win.show()
    log("processEvents")
    QApplication.processEvents()
    log("进入事件循环")
    code = app.exec()
    log(f"事件循环结束 code={code}")
    sys.exit(code)


if __name__ == "__main__":
    import traceback
    print("黄同学的AI工具箱启动中...", flush=True)
    try:
        main()
    except Exception as e:
        print("错误:", e, flush=True)
        traceback.print_exc()
        input("按回车键退出...")
        sys.exit(1)
