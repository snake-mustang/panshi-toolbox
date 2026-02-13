# -*- coding: utf-8 -*-
"""
pywebview 暴露给前端的 API：截图、裁剪、OCR、日志。
所有方法会被 pywebview 暴露为 window.pywebview.api.xxx()。
"""
import base64
import io
import os
import sys
import time
import threading
import json
import urllib.request
import urllib.error

from PIL import Image, ImageGrab


def _get_scale_factor():
    if sys.platform != "win32":
        return 1.0
    try:
        import ctypes
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass
    return 1.0


def _data_url_to_pil(data_url: str):
    """data:image/...;base64,... -> PIL Image."""
    if not data_url or "base64," not in data_url:
        return None
    raw = base64.b64decode(data_url.split("base64,", 1)[1])
    return Image.open(io.BytesIO(raw)).convert("RGB")


def _pil_to_data_url(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def _set_clipboard_image(img: Image.Image) -> bool:
    """将 PIL 图像写入系统剪贴板（Windows 使用 pywin32）。返回是否成功。"""
    if sys.platform != "win32":
        return False
    
    try:
        import win32clipboard
        from io import BytesIO
        
        # 确保是RGB模式
        if img.mode != "RGB":
            img = img.convert("RGB")
        
        # 转换为BMP格式
        output = BytesIO()
        img.save(output, "BMP")
        data = output.getvalue()[14:]  # 去掉BMP文件头（14字节）
        
        # 尝试打开剪贴板（重试机制）
        for attempt in range(5):
            try:
                win32clipboard.OpenClipboard()
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
                win32clipboard.CloseClipboard()
                return True
            except Exception as e:
                try:
                    win32clipboard.CloseClipboard()
                except:
                    pass
                if attempt < 4:
                    time.sleep(0.15)
                else:
                    print(f"剪贴板复制失败: {e}")
                    return False
        
        return False
        
    except ImportError:
        # 如果没有 pywin32，尝试使用 PIL 的内置方法
        try:
            import subprocess
            # 保存临时文件
            temp_path = os.path.join(os.getenv('TEMP', '.'), 'temp_screenshot.png')
            img.save(temp_path, 'PNG')
            # 使用 PowerShell 复制图片到剪贴板
            ps_script = f'''
            Add-Type -AssemblyName System.Windows.Forms
            $img = [System.Drawing.Image]::FromFile("{temp_path}")
            [System.Windows.Forms.Clipboard]::SetImage($img)
            $img.Dispose()
            '''
            subprocess.run(['powershell', '-Command', ps_script], 
                          capture_output=True, timeout=5)
            try:
                os.remove(temp_path)
            except:
                pass
            return True
        except Exception as e:
            print(f"备用剪贴板方法失败: {e}")
            return False
    
    except Exception as e:
        import traceback
        print(f"剪贴板错误: {e}")
        traceback.print_exc()
        return False


class Api:
    """供 pywebview 使用的 API 类，方法会暴露给 JS。"""

    def __init__(self, on_log=None):
        self._on_log = on_log or (lambda msg: None)
        self._window = None

    def set_window(self, window) -> None:
        """由 run_webview 在创建窗口后注入，用于文件对话框、最小化等。F1 最小化，任务栏恢复。"""
        self._window = window

    def minimize_window(self) -> None:
        """最小化窗口（仅在本窗口内按 F1 时由前端调用，任务栏点击可恢复）。"""
        if self._window:
            try:
                self._window.minimize()
            except Exception as e:
                self._on_log(f"最小化窗口: {e}")

    def log(self, msg: str) -> None:
        """打印到控制台/打印台。"""
        self._on_log(str(msg))

    def capture_full(self) -> str:
        """全屏截图，返回 data:image/png;base64,..."""
        try:
            img = ImageGrab.grab()
            return _pil_to_data_url(img)
        except Exception as e:
            self._on_log(f"[截图错误] {e}")
            return ""

    def get_full_screen_image(self) -> str:
        """获取当前全屏图（用于前端做区域选择），返回 data URL。"""
        return self.capture_full()

    def capture_region_interactive(self) -> str:
        """
        区域截图（类似微信）：先隐藏工具箱，桌面全屏半透明遮罩，拖拽选区，松开即截取该区域。
        返回 data URL，取消则返回空字符串。
        """
        if self._window:
            try:
                self._window.hide()
            except Exception:
                pass
            time.sleep(0.35)
        data_url = ""
        try:
            from backend.region_capture_tk import run_region_capture
            data_url = run_region_capture() or ""
        except Exception as e:
            self._on_log(f"[区域截图] {e}")
        finally:
            if self._window:
                try:
                    self._window.show()
                except Exception:
                    pass
        self._on_log("区域截图完成" if data_url else "区域截图已取消")
        return data_url

    def capture_fullscreen_for_ocr(self) -> str:
        """
        全屏识别：直接截取当前全屏（隐藏工具箱后），返回 data URL。
        """
        if self._window:
            try:
                self._window.hide()
            except Exception:
                pass
            time.sleep(0.35)
        
        data_url = ""
        try:
            img = ImageGrab.grab()
            data_url = _pil_to_data_url(img)
            self._on_log("全屏截图完成")
        except Exception as e:
            self._on_log(f"[全屏截图错误] {e}")
        finally:
            if self._window:
                try:
                    self._window.show()
                except Exception:
                    pass
        
        return data_url

    def capture_long_screenshot(self) -> str:
        """
        长截图（PixPin 式）：先隐藏工具箱，用户框选区域，再由用户手动滚动内容，
        程序持续捕获该区域并拼接；用户点击「完成」后生成长图并写入剪贴板。
        返回 data URL；取消或失败返回空字符串。
        """
        if self._window:
            try:
                self._window.hide()
            except Exception:
                pass
            time.sleep(0.35)
        data_url = ""
        try:
            from backend.region_capture_tk import run_region_capture_with_rect
            from backend.long_screenshot_opencv import capture_long_screenshot_manual
            region_data_url, rect = run_region_capture_with_rect()
            if rect is None:
                self._on_log("已取消选区")
            else:
                self._on_log("选区已定，请手动滚动内容，完成后点击「完成」")
                stop_event = threading.Event()
                result_holder = [None]
                current_result_holder = [None, None]  # [预览图像, 匹配状态]
                done_action = [None]  # "done" | "cancel"

                def run_capture():
                    result_holder[0] = capture_long_screenshot_manual(
                        rect, stop_event, on_log=self._on_log,
                        current_result_holder=current_result_holder,
                    )

                cap_thread = threading.Thread(target=run_capture, daemon=True)
                cap_thread.start()
                from backend.long_screenshot_ui_modern import run_long_screenshot_ui
                run_long_screenshot_ui(
                    rect, stop_event, result_holder, current_result_holder, done_action
                )
                cap_thread.join(timeout=3)
                if done_action[0] == "done" and result_holder[0] is not None:
                    img = result_holder[0]
                    data_url = _pil_to_data_url(img)
                    
                    # 多次尝试复制到剪贴板
                    copy_success = False
                    for attempt in range(3):
                        if _set_clipboard_image(img):
                            copy_success = True
                            break
                        time.sleep(0.1)
                    
                    if copy_success:
                        self._on_log("长截图已复制到剪贴板，可直接 Ctrl+V 粘贴")
                    else:
                        self._on_log("长截图完成，但复制到剪贴板失败（可能被其他程序占用）")
                elif done_action[0] == "cancel":
                    self._on_log("已取消长截图")
        except Exception as e:
            self._on_log(f"[长截图] {e}")
        finally:
            if self._window:
                try:
                    self._window.show()
                except Exception:
                    pass
        return data_url

    def crop_image(self, data_url: str, x, y, w, h) -> str:
        """
        从整图 data_url 中裁剪矩形 (x,y,w,h)，返回新 data URL。
        坐标与尺寸为原图像素。x,y,w,h 若为 None 则按 0 或跳过。
        """
        try:
            img = _data_url_to_pil(data_url)
            if img is None:
                return ""
            x = int(x) if x is not None else 0
            y = int(y) if y is not None else 0
            w = int(w) if w is not None else 0
            h = int(h) if h is not None else 0
            if w <= 0 or h <= 0:
                return ""
            box = (x, y, x + w, y + h)
            cropped = img.crop(box)
            return _pil_to_data_url(cropped)
        except Exception as e:
            self._on_log(f"[裁剪错误] {e}")
            return ""

    def ocr_from_data_url(self, data_url: str) -> str:
        """从 data URL 识别文字。"""
        try:
            from backend.ocr_engine import OcrHandler
            ocr = OcrHandler()
            return ocr.recognize_from_data_url(data_url)
        except Exception as e:
            self._on_log(f"[OCR 错误] {e}")
            return f"[OCR 错误] {e}"

    def ocr_from_file(self, path: str) -> str:
        """从本地文件路径识别。"""
        try:
            from backend.ocr_engine import OcrHandler
            ocr = OcrHandler()
            return ocr.recognize_from_file(path)
        except Exception as e:
            self._on_log(f"[OCR 错误] {e}")
            return f"[OCR 错误] {e}"

    def open_cursor(self) -> None:
        """优先激活已打开的、最近使用的 Cursor 窗口（玩家通常已开着 Cursor）；若无则再尝试启动 Cursor。"""
        try:
            import subprocess
            import sys
            if sys.platform == "win32":
                # Windows：先尝试找到标题含 "Cursor" 的窗口并置前（Z-order 中第一个即为当前最前/最近使用的）
                try:
                    import ctypes
                    from ctypes import wintypes
                    user32 = ctypes.windll.user32
                    SW_RESTORE = 9
                    SW_MAXIMIZE = 3
                    cursor_hwnd = None

                    def enum_cb(hwnd, _):
                        nonlocal cursor_hwnd
                        if not user32.IsWindowVisible(hwnd):
                            return True
                        buf = ctypes.create_unicode_buffer(260)
                        if user32.GetWindowTextW(hwnd, buf, 260) and "Cursor" in buf.value:
                            cursor_hwnd = hwnd
                            return False  # 停止枚举，保留第一个（最前）匹配
                        return True

                    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
                    user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
                    if cursor_hwnd:
                        # 直接最大化，避免先恢复再最大化导致的闪烁
                        user32.ShowWindow(cursor_hwnd, SW_MAXIMIZE)
                        user32.SetForegroundWindow(cursor_hwnd)
                        return
                except Exception:
                    pass
                # 未找到已打开的 Cursor 窗口时，再尝试启动
                try:
                    subprocess.Popen(
                        ["cursor", "."],
                        shell=True,
                        stdin=subprocess.DEVNULL,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                except Exception:
                    pass
            else:
                try:
                    subprocess.Popen(
                        ["cursor", "."],
                        stdin=subprocess.DEVNULL,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                except Exception:
                    pass
        except Exception as e:
            self._on_log(f"[打开 Cursor] {e}")

    def bring_window_to_front(self) -> None:
        """将本应用窗口置于前台（如显示完成提示前调用，避免被 Cursor 挡住）。"""
        if sys.platform != "win32":
            return
        try:
            import ctypes
            from ctypes import wintypes
            user32 = ctypes.windll.user32
            SW_RESTORE = 9
            found = [None]

            def enum_cb(hwnd, _):
                if not user32.IsWindowVisible(hwnd):
                    return True
                buf = ctypes.create_unicode_buffer(260)
                if user32.GetWindowTextW(hwnd, buf, 260):
                    t = buf.value
                    if "盘古" in t or "工具箱" in t:
                        found[0] = hwnd
                        return False
                return True

            WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
            user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
            if found[0]:
                user32.ShowWindow(found[0], SW_RESTORE)
                user32.SetForegroundWindow(found[0])
        except Exception as e:
            self._on_log(f"[窗口置前] {e}")

    def show_message_box(self, title: str, message: str) -> None:
        """显示系统原生弹窗（如 Windows MessageBox），可浮在所有窗口之上。"""
        if sys.platform == "win32":
            try:
                import ctypes
                ctypes.windll.user32.MessageBoxW(
                    None,
                    message,
                    title,
                    0x40 | 0x0,  # MB_ICONINFORMATION | MB_OK
                )
            except Exception as e:
                self._on_log(f"[系统弹窗] {e}")
        else:
            try:
                import tkinter as tk
                from tkinter import messagebox
                root = tk.Tk()
                root.withdraw()
                root.attributes("-topmost", True)
                messagebox.showinfo(title, message, parent=root)
                root.destroy()
            except Exception as e:
                self._on_log(f"[系统弹窗] {e}")

    def open_file_dialog(self, title: str, file_types: str) -> str:
        """打开文件选择对话框，返回选中路径或空字符串。"""
        if self._window is None:
            return ""
        try:
            import webview
            # pywebview：file_types 为元组，每项为 "描述 (扩展名)"，扩展名用分号分隔
            file_types = (
                "图片 (*.png;*.jpg;*.jpeg;*.bmp)",
                "All files (*.*)",
            )
            result = self._window.create_file_dialog(
                webview.OPEN_DIALOG,
                allow_multiple=False,
                file_types=file_types,
            )
            if result and len(result) > 0:
                return result[0]
            return ""
        except Exception as e:
            self._on_log(f"[文件选择错误] {e}")
            return ""

    def copy_to_clipboard(self, text: str) -> bool:
        """将文本写入系统剪贴板，供前端「复制日志」等使用。返回是否成功。"""
        if not text:
            return True
        try:
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()
            root.clipboard_clear()
            root.clipboard_append(text)
            root.update()
            root.destroy()
            return True
        except Exception as e:
            self._on_log(f"[剪贴板] {e}")
            return False

    def analyze_text_with_ai_stream(self, text: str, prompt: str = "") -> dict:
        """
        使用 Qwen3 AI 分析文本（流式输出）。
        
        Args:
            text: 要分析的文本（OCR 识别结果）
            prompt: 用户自定义提示词
        
        Returns:
            dict: {"status": "success/error", "content": "结果", "chunks": [...]}
        """
        if not text:
            return {"status": "error", "content": "没有可分析的文本"}
        
        # Qwen3 配置
        QWEN3_URL = "http://1318411781707473.cn-shanghai.pai-eas.aliyuncs.com/api/predict/xuchuan_qwen3_coder/v1/chat/completions"
        QWEN3_API_KEY = "MDA2ZWZiOGE4MGM3MTEzYmEwYzg3YTQ1YjBhYWFjMGVlMTg0NTNlZg=="
        QWEN3_MODEL = "Qwen3-Coder-480B-A35B-Instruct-PAI-optimized"
        
        try:
            # 构建消息
            system_message = "你是一个专业的文本分析助手，请根据用户的要求分析下面的文本内容。"
            
            if prompt:
                user_message = f"用户要求：{prompt}\n\n文本内容：\n{text}"
            else:
                user_message = f"请分析以下文本内容：\n{text}"
            
            # 构建请求数据（启用流式输出）
            data = {
                "model": QWEN3_MODEL,
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                "temperature": 0.7,
                "max_tokens": 2000,
                "stream": True  # 启用流式输出
            }
            
            # 发送请求
            req = urllib.request.Request(
                QWEN3_URL,
                data=json.dumps(data).encode('utf-8'),
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {QWEN3_API_KEY}'
                }
            )
            
            self._on_log("正在请求 Qwen3 AI 分析（流式）...")
            
            full_content = ""
            chunks = []
            
            with urllib.request.urlopen(req, timeout=120) as response:
                # 读取流式数据
                for line in response:
                    line = line.decode('utf-8').strip()
                    if not line or line == "data: [DONE]":
                        continue
                    
                    if line.startswith("data: "):
                        line = line[6:]  # 去掉 "data: " 前缀
                        
                        try:
                            chunk_data = json.loads(line)
                            if 'choices' in chunk_data and len(chunk_data['choices']) > 0:
                                delta = chunk_data['choices'][0].get('delta', {})
                                content = delta.get('content', '')
                                if content:
                                    full_content += content
                                    chunks.append(content)
                        except json.JSONDecodeError:
                            continue
                
                if full_content:
                    self._on_log("AI 分析完成")
                    return {
                        "status": "success",
                        "content": full_content,
                        "chunks": chunks
                    }
                else:
                    return {
                        "status": "error",
                        "content": "AI 返回了空结果"
                    }
        
        except urllib.error.HTTPError as e:
            error_msg = f"HTTP 错误 {e.code}"
            try:
                error_detail = e.read().decode('utf-8')
                self._on_log(f"[AI 分析错误] {error_msg}: {error_detail}")
                return {
                    "status": "error",
                    "content": f"请求失败：{error_msg}\n{error_detail}"
                }
            except:
                self._on_log(f"[AI 分析错误] {error_msg}")
                return {
                    "status": "error",
                    "content": f"请求失败：{error_msg}"
                }
        
        except urllib.error.URLError as e:
            error_msg = f"网络错误: {e.reason}"
            self._on_log(f"[AI 分析错误] {error_msg}")
            return {
                "status": "error",
                "content": f"网络连接失败：{error_msg}"
            }
        
        except Exception as e:
            error_msg = str(e)
            self._on_log(f"[AI 分析错误] {error_msg}")
            return {
                "status": "error",
                "content": f"分析失败：{error_msg}"
            }
