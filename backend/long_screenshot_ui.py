# -*- coding: utf-8 -*-
"""
长截图 PixPin 式 UI：选区框（红框）+ 底部工具栏（尺寸、完成、取消）+ 右侧实时预览。
"""
import sys


def _set_window_click_through(hwnd):
    """设置窗口为鼠标穿透（仅 Windows）。"""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        from ctypes import wintypes
        GWL_EXSTYLE = -20
        WS_EX_LAYERED = 0x00080000
        WS_EX_TRANSPARENT = 0x00000020
        user32 = ctypes.windll.user32
        style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style | WS_EX_TRANSPARENT)
    except Exception:
        pass


def run_long_screenshot_ui(rect, stop_event, result_holder, current_result_holder, done_action):
    """
    显示 PixPin 式长截图界面：选区红框 + 底部工具栏 + 右侧预览。
    阻塞直到用户点击完成或取消。
    :param rect: (left, top, right, bottom) 屏幕坐标
    :param stop_event: threading.Event
    :param result_holder: [None] 最终结果由捕获线程写入
    :param current_result_holder: [None] 当前拼接图，供预览刷新
    :param done_action: [None] 返回 "done" 或 "cancel"
    """
    try:
        import tkinter as tk
        from tkinter import ttk
    except ImportError:
        return
    try:
        from PIL import Image, ImageTk
    except ImportError:
        ImageTk = None

    left, top, right, bottom = rect
    w_rect = right - left
    h_rect = bottom - top

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    # 1) 选区框：全屏透明窗口，只画红框，并设为鼠标穿透
    overlay = tk.Toplevel(root)
    overlay.overrideredirect(True)
    sw = overlay.winfo_screenwidth()
    sh = overlay.winfo_screenheight()
    overlay.geometry(f"{sw}x{sh}+0+0")
    overlay.attributes("-topmost", True)
    TRANSPARENT_COLOR = "#010101"
    overlay.configure(bg=TRANSPARENT_COLOR)
    if sys.platform == "win32":
        try:
            overlay.attributes("-transparentcolor", TRANSPARENT_COLOR)
        except Exception:
            pass
    canvas = tk.Canvas(overlay, width=sw, height=sh, bg=TRANSPARENT_COLOR, highlightthickness=0)
    canvas.pack(fill=tk.BOTH, expand=True)
    canvas.create_rectangle(left, top, right, bottom, outline="#e74c3c", width=3)
    overlay.update_idletasks()
    try:
        hwnd = overlay.winfo_id()
        _set_window_click_through(hwnd)
    except Exception:
        pass

    # 2) 底部工具栏：尺寸 + 完成 + 取消
    toolbar = tk.Toplevel(root)
    toolbar.overrideredirect(True)
    toolbar.attributes("-topmost", True)
    toolbar.configure(bg="#2c2c2e", padx=10, pady=8)
    tbar_inner = ttk.Frame(toolbar, padding=4)
    tbar_inner.pack()
    dim_label = ttk.Label(tbar_inner, text=f"{w_rect} × {h_rect}", font=("Segoe UI", 10))
    dim_label.pack(side=tk.LEFT, padx=(0, 16))
    btn_done = ttk.Button(tbar_inner, text="完成", width=8)
    btn_cancel = ttk.Button(tbar_inner, text="取消", width=8)
    btn_done.pack(side=tk.LEFT, padx=(0, 8))
    btn_cancel.pack(side=tk.LEFT)
    toolbar.geometry(f"+{left}+{bottom + 12}")
    toolbar.update_idletasks()
    tw, th = toolbar.winfo_reqwidth(), toolbar.winfo_reqheight()
    if left + tw > sw:
        left_t = sw - tw - 20
    else:
        left_t = left
    if bottom + 12 + th > sh:
        top_t = bottom - th - 12
    else:
        top_t = bottom + 12
    toolbar.geometry(f"+{left_t}+{top_t}")

    # 3) 右侧预览窗口
    PREVIEW_W = 280
    PREVIEW_H = 360
    preview = tk.Toplevel(root)
    preview.overrideredirect(True)
    preview.attributes("-topmost", True)
    preview.configure(bg="#1c1c1e", width=PREVIEW_W, height=PREVIEW_H)
    preview.geometry(f"{PREVIEW_W}x{PREVIEW_H}+{right + 16}+{top}")
    preview.update_idletasks()
    if right + 16 + PREVIEW_W > sw:
        preview.geometry(f"{PREVIEW_W}x{PREVIEW_H}+{left - PREVIEW_W - 16}+{top}")
    prev_label = tk.Label(preview, text="预览", bg="#1c1c1e", fg="#8e8e93", font=("Segoe UI", 9))
    prev_label.pack(pady=(8, 4))
    prev_canvas = tk.Canvas(preview, width=PREVIEW_W - 16, height=PREVIEW_H - 40, bg="#2c2c2e", highlightthickness=0)
    prev_canvas.pack(padx=8, pady=(0, 8))
    photo_ref = [None]

    def update_preview():
        if preview.winfo_exists() and current_result_holder and current_result_holder[0] is not None:
            try:
                img = current_result_holder[0]
                if img and ImageTk is not None:
                    r = min((PREVIEW_W - 16) / img.width, (PREVIEW_H - 44) / img.height, 1.0)
                    nw, nh = int(img.width * r), int(img.height * r)
                    from PIL import Image as PILImage
                    thumb = img.copy()
                    if thumb.mode != "RGB":
                        thumb = thumb.convert("RGB")
                    thumb = thumb.resize((nw, nh), PILImage.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(thumb)
                    photo_ref[0] = photo
                    prev_canvas.delete("all")
                    prev_canvas.create_image((PREVIEW_W - 16) // 2, (PREVIEW_H - 40) // 2, image=photo)
            except Exception:
                pass
        if toolbar.winfo_exists():
            toolbar.after(350, update_preview)

    def on_done():
        stop_event.set()
        done_action[0] = "done"
        try:
            overlay.destroy()
        except Exception:
            pass
        try:
            toolbar.destroy()
        except Exception:
            pass
        try:
            preview.destroy()
        except Exception:
            pass
        try:
            root.quit()
            root.destroy()
        except Exception:
            pass

    def on_cancel():
        stop_event.set()
        done_action[0] = "cancel"
        try:
            overlay.destroy()
        except Exception:
            pass
        try:
            toolbar.destroy()
        except Exception:
            pass
        try:
            preview.destroy()
        except Exception:
            pass
        try:
            root.quit()
            root.destroy()
        except Exception:
            pass

    btn_done.configure(command=on_done)
    btn_cancel.configure(command=on_cancel)
    toolbar.protocol("WM_DELETE_WINDOW", on_cancel)
    toolbar.after(400, update_preview)
    root.mainloop()
