# -*- coding: utf-8 -*-
"""
区域截图：先隐藏主窗口，弹出全屏半透明遮罩，用户拖拽选区，松开后截取该区域。
类似微信截图。使用 tkinter（Python 自带）。
在子进程中运行 tk，避免与 pywebview 主线程冲突。
"""
import base64
import io
import sys
import multiprocessing

from PIL import ImageGrab


def _run_and_put(queue: multiprocessing.Queue) -> None:
    """供子进程调用，将结果放入 queue。"""
    queue.put(run_region_capture())


def run_region_capture() -> str:
    """
    显示全屏选区窗口，用户拖拽画矩形，松开后截取该区域。
    返回 data:image/png;base64,... 或空字符串（取消）。
    """
    url, _ = run_region_capture_with_rect()
    return url or ""


def run_region_capture_with_rect():
    """
    显示全屏选区窗口，用户拖拽画矩形，松开后截取该区域。
    返回 (data_url, rect)：
      - data_url: data:image/png;base64,... 或空字符串
      - rect: (left, top, right, bottom) 屏幕坐标，取消时为 None
    """
    try:
        import tkinter as tk
    except ImportError:
        return "", None

    result = [None]  # data_url
    result_rect = [None]  # (left, top, right, bottom)

    root = tk.Tk()
    root.attributes("-fullscreen", True)
    root.attributes("-topmost", True)
    root.attributes("-alpha", 0.35)
    root.configure(bg="black")
    root.cursor = "cross"

    canvas = tk.Canvas(
        root,
        cursor="cross",
        bg="black",
        highlightthickness=0,
    )
    canvas.pack(fill=tk.BOTH, expand=True)

    start_x, start_y = [None], [None]
    rect_id = [None]

    def to_screen(x, y):
        return canvas.winfo_rootx() + x, canvas.winfo_rooty() + y

    def on_press(e):
        start_x[0], start_y[0] = e.x, e.y
        if rect_id[0] is not None:
            canvas.delete(rect_id[0])
        # tk 不支持 8 位 hex 透明色，用描边即可
        rect_id[0] = canvas.create_rectangle(e.x, e.y, e.x, e.y, outline="#00aaff", width=2)

    def on_move(e):
        if start_x[0] is None:
            return
        canvas.coords(rect_id[0], start_x[0], start_y[0], e.x, e.y)

    def do_quit():
        try:
            root.quit()
        except Exception:
            pass
        try:
            root.destroy()
        except Exception:
            pass

    def on_release(e):
        if start_x[0] is None:
            return
        try:
            x1, y1 = min(start_x[0], e.x), min(start_y[0], e.y)
            x2, y2 = max(start_x[0], e.x), max(start_y[0], e.y)
            w, h = x2 - x1, y2 - y1
            if w >= 5 and h >= 5:
                sx1, sy1 = to_screen(x1, y1)
                sx2, sy2 = to_screen(x2, y2)
                box = (sx1, sy1, sx2, sy2)
                result_rect[0] = box
                img = ImageGrab.grab(bbox=box)
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                b64 = base64.b64encode(buf.getvalue()).decode("ascii")
                result[0] = f"data:image/png;base64,{b64}"
        except Exception:
            pass
        # 延迟退出，让当前事件处理完再 quit/destroy，否则 mainloop 可能不退出
        root.after(10, do_quit)

    def on_escape(e):
        if e.keysym == "Escape":
            root.after(10, do_quit)

    def on_right_click(e):
        root.after(10, do_quit)

    canvas.bind("<ButtonPress-1>", on_press)
    canvas.bind("<B1-Motion>", on_move)
    canvas.bind("<ButtonRelease-1>", on_release)
    root.bind("<Escape>", on_escape)
    canvas.bind("<ButtonPress-3>", on_right_click)

    # 高 DPI 下坐标修正（Windows）
    if sys.platform == "win32":
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

    root.after(100, root.focus_set)
    root.mainloop()
    return (result[0] or "", result_rect[0])


def run_region_capture_in_subprocess() -> str:
    """在子进程中运行选区截图，避免与 pywebview 冲突。返回 data URL 或空串。"""
    q = multiprocessing.Queue()
    p = multiprocessing.Process(target=_run_and_put, args=(q,))
    p.start()
    p.join(timeout=120)
    if p.is_alive():
        p.terminate()
        p.join(timeout=2)
        return ""
    try:
        return q.get_nowait() or ""
    except Exception:
        return ""
