# -*- coding: utf-8 -*-
"""
黄同学的AI工具箱 - pywebview 入口。
F1 全局热键：任意位置按 F1 可唤起/前置工具箱；窗口内按 F1 可最小化。
使用方式：
  1. 先打包前端：cd frontend && npm run build
  2. 再启动：python run_webview.py
  或一条命令（先 build 再启动）：python run_webview.py --build
"""
import sys
import os
import threading
import subprocess

# 项目根目录（打包后 PyInstaller 解压资源到 _MEIPASS）
if getattr(sys, "frozen", False):
    ROOT = sys._MEIPASS
    STATIC_DIR = os.path.join(ROOT, "frontend", "dist")
    if not os.path.isdir(STATIC_DIR):
        STATIC_DIR = os.path.join(ROOT, "frontend")
else:
    ROOT = os.path.dirname(os.path.abspath(__file__))
    FRONTEND_DIR = os.path.join(ROOT, "frontend")
    DIST_DIR = os.path.join(FRONTEND_DIR, "dist")
    # 优先使用已打包的 frontend/dist；若无则使用 frontend（需先 npm run build）
    if os.path.isdir(DIST_DIR):
        STATIC_DIR = DIST_DIR
    else:
        STATIC_DIR = FRONTEND_DIR
if not os.path.isdir(STATIC_DIR):
    os.makedirs(STATIC_DIR)

# 打印台回调
def _on_log(msg: str) -> None:
    print(f"[Toolbox] {msg}", flush=True)


def _start_global_f1(window_ref: list, minimized_state: list) -> None:
    """后台线程：注册全局 F1，按下时切换窗口（已最小化则恢复，否则最小化）。仅 Windows。"""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        from ctypes import wintypes
        user32 = ctypes.windll.user32
        WM_HOTKEY = 0x0312
        VK_F1 = 0x70
        MOD_NONE = 0
        HOTKEY_ID = 1
        if not user32.RegisterHotKey(None, HOTKEY_ID, MOD_NONE, VK_F1):
            return
        msg = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            if msg.message == WM_HOTKEY and msg.wParam == HOTKEY_ID:
                w = window_ref[0] if window_ref else None
                if w:
                    try:
                        if minimized_state and minimized_state[0]:
                            w.restore()
                            w.show()
                        else:
                            w.minimize()
                    except Exception:
                        pass
        user32.UnregisterHotKey(None, HOTKEY_ID)
    except Exception:
        pass


def main() -> None:
    import http.server
    import webview

    # 可选：先打包前端再启动（同一方法内完成）
    if not getattr(sys, "frozen", False) and len(sys.argv) > 1 and sys.argv[1] == "--build":
        frontend_dir = os.path.join(ROOT, "frontend")
        if os.path.isdir(frontend_dir):
            _on_log("正在打包前端 (npm run build)...")
            ret = subprocess.run(
                ["npm", "run", "build"],
                cwd=frontend_dir,
                shell=sys.platform == "win32",
            )
            if ret.returncode != 0:
                _on_log("前端打包失败，请检查 frontend 目录并执行 npm run build")
                sys.exit(1)
            _on_log("前端打包完成")
            global STATIC_DIR
            STATIC_DIR = os.path.join(frontend_dir, "dist")

    # 后端 API（暴露给前端）
    from backend.api_webview import Api
    api = Api(on_log=_on_log)

    # 本地 HTTP 服务
    port = 8765
    os.chdir(STATIC_DIR)
    server = http.server.HTTPServer(("127.0.0.1", port), http.server.SimpleHTTPRequestHandler)
    server.allow_reuse_address = True

    def serve():
        server.serve_forever()

    t = threading.Thread(target=serve, daemon=True)
    t.start()

    url = f"http://127.0.0.1:{port}/index.html"
    window = webview.create_window(
        "【盘古】开发工具箱",
        url,
        width=1100,
        height=750,
        min_size=(900, 600),
        js_api=api,
    )
    api.set_window(window)

    # 全局 F1：按 F1 切换窗口（最小化 ⇄ 恢复），用 events 同步状态
    minimized_state = [False]

    def _on_minimized():
        minimized_state[0] = True

    def _on_restored():
        minimized_state[0] = False

    window.events.minimized += _on_minimized
    window.events.restored += _on_restored

    window_ref = [window]
    f1_thread = threading.Thread(
        target=_start_global_f1,
        args=(window_ref, minimized_state),
        daemon=True,
    )
    f1_thread.start()

    # Windows 优先用 EdgeChromium（WebView2），避免 WinForms/pythonnet 依赖 .NET 和 cffi
    webview.start(debug=False, gui="edgechromium")

    server.shutdown()
    sys.exit(0)


if __name__ == "__main__":
    main()
