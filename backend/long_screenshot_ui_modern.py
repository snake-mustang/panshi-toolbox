# -*- coding: utf-8 -*-
"""
长截图现代化 UI：现代风格选区框 + 精美工具栏 + 高级预览面板
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
        WS_EX_TRANSPARENT = 0x00000020
        user32 = ctypes.windll.user32
        style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style | WS_EX_TRANSPARENT)
    except Exception:
        pass


def run_long_screenshot_ui(rect, stop_event, result_holder, current_result_holder, done_action):
    """
    显示现代化长截图界面：精美选区框 + 底部工具栏（右下角完成按钮）+ 实时预览。
    """
    try:
        import tkinter as tk
        from tkinter import font as tkfont
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

    # 1) 选区框：现代风格，带阴影效果的红色边框
    overlay = tk.Toplevel(root)
    overlay.overrideredirect(True)
    sw = overlay.winfo_screenwidth()
    sh = overlay.winfo_screenheight()
    overlay.geometry(f"{sw}x{sh}+0+0")
    overlay.attributes("-topmost", True)
    overlay.attributes("-alpha", 0.3)  # 半透明效果
    
    TRANSPARENT_COLOR = "#000001"
    overlay.configure(bg=TRANSPARENT_COLOR)
    
    if sys.platform == "win32":
        try:
            overlay.attributes("-transparentcolor", TRANSPARENT_COLOR)
            overlay.attributes("-alpha", 1.0)  # Windows上完全透明
        except Exception:
            pass
    
    canvas = tk.Canvas(overlay, width=sw, height=sh, bg=TRANSPARENT_COLOR, highlightthickness=0)
    canvas.pack(fill=tk.BOTH, expand=True)
    
    # 绘制现代化边框：外层阴影 + 内层高亮
    # 外层阴影（深红色，4px）
    canvas.create_rectangle(left-2, top-2, right+2, bottom+2, 
                           outline="#c0392b", width=4, dash=(8, 4))
    # 主边框（亮红色，2px）
    canvas.create_rectangle(left, top, right, bottom, 
                           outline="#e74c3c", width=2)
    # 四个角的加强标记
    corner_size = 20
    corner_width = 3
    # 左上角
    canvas.create_line(left, top, left+corner_size, top, fill="#e74c3c", width=corner_width)
    canvas.create_line(left, top, left, top+corner_size, fill="#e74c3c", width=corner_width)
    # 右上角
    canvas.create_line(right-corner_size, top, right, top, fill="#e74c3c", width=corner_width)
    canvas.create_line(right, top, right, top+corner_size, fill="#e74c3c", width=corner_width)
    # 左下角
    canvas.create_line(left, bottom-corner_size, left, bottom, fill="#e74c3c", width=corner_width)
    canvas.create_line(left, bottom, left+corner_size, bottom, fill="#e74c3c", width=corner_width)
    # 右下角
    canvas.create_line(right-corner_size, bottom, right, bottom, fill="#e74c3c", width=corner_width)
    canvas.create_line(right, bottom-corner_size, right, bottom, fill="#e74c3c", width=corner_width)
    
    overlay.update_idletasks()
    try:
        hwnd = overlay.winfo_id()
        _set_window_click_through(hwnd)
    except Exception:
        pass

    # 2) 底部工具栏：现代化设计，完成按钮在右下角
    toolbar = tk.Toplevel(root)
    toolbar.overrideredirect(True)
    toolbar.attributes("-topmost", True)
    toolbar.configure(bg="#1a1a1a")
    
    # 创建圆角效果容器
    tbar_frame = tk.Frame(toolbar, bg="#2d2d2d", padx=20, pady=12)
    tbar_frame.pack(fill=tk.BOTH, expand=True)
    
    # 左侧：尺寸信息
    info_frame = tk.Frame(tbar_frame, bg="#2d2d2d")
    info_frame.pack(side=tk.LEFT, fill=tk.Y)
    
    # 使用现代化字体
    try:
        modern_font = tkfont.Font(family="Segoe UI", size=10, weight="normal")
        title_font = tkfont.Font(family="Segoe UI", size=9, weight="normal")
    except:
        modern_font = ("Segoe UI", 10)
        title_font = ("Segoe UI", 9)
    
    size_label = tk.Label(info_frame, text=f"区域大小: {w_rect} × {h_rect} px", 
                         bg="#2d2d2d", fg="#ffffff", font=modern_font)
    size_label.pack(anchor=tk.W)
    
    tip_label = tk.Label(info_frame, text="滚动内容以继续拼接，完成后点击按钮", 
                        bg="#2d2d2d", fg="#8e8e93", font=title_font)
    tip_label.pack(anchor=tk.W, pady=(2, 0))
    
    # 右侧：按钮组
    btn_frame = tk.Frame(tbar_frame, bg="#2d2d2d")
    btn_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(20, 0))
    
    # 自定义按钮样式
    btn_style = {
        'font': modern_font,
        'bd': 0,
        'relief': tk.FLAT,
        'cursor': 'hand2',
        'padx': 20,
        'pady': 8
    }
    
    btn_cancel = tk.Button(btn_frame, text="✕", 
                          bg="#5a5a5a", fg="#cccccc",
                          activebackground="#6a6a6a", 
                          activeforeground="#ffffff",
                          font=tkfont.Font(family="Segoe UI", size=16),
                          **{k: v for k, v in btn_style.items() if k != 'font'})
    btn_cancel.pack(side=tk.LEFT, padx=(0, 10))
    
    btn_done = tk.Button(btn_frame, text="✓", 
                        bg="#27ae60", fg="#ffffff",
                        activebackground="#2ecc71", 
                        font=tkfont.Font(family="Segoe UI", size=16),
                        **{k: v for k, v in btn_style.items() if k != 'font'})
    btn_done.pack(side=tk.LEFT)
    
    # 工具栏位置：右下角
    toolbar.update_idletasks()
    tw = toolbar.winfo_reqwidth()
    th = toolbar.winfo_reqheight()
    
    # 定位在截图区域右下角
    toolbar_x = right - tw
    toolbar_y = bottom + 16
    
    # 边界检查
    if toolbar_x < 0:
        toolbar_x = 10
    elif toolbar_x + tw > sw:
        toolbar_x = sw - tw - 10
    
    if toolbar_y + th > sh:
        toolbar_y = bottom - th - 16
    
    toolbar.geometry(f"+{toolbar_x}+{toolbar_y}")

    # 3) 右侧预览窗口：现代化设计
    PREVIEW_W = 320
    PREVIEW_H = 400
    preview = tk.Toplevel(root)
    preview.overrideredirect(True)
    preview.attributes("-topmost", True)
    preview.configure(bg="#1a1a1a")
    
    # 预览窗口框架
    prev_frame = tk.Frame(preview, bg="#2d2d2d", padx=16, pady=16)
    prev_frame.pack(fill=tk.BOTH, expand=True)
    
    # 标题
    title_frame = tk.Frame(prev_frame, bg="#2d2d2d")
    title_frame.pack(fill=tk.X, pady=(0, 12))
    
    prev_title = tk.Label(title_frame, text="📸 实时预览", 
                         bg="#2d2d2d", fg="#ffffff", 
                         font=tkfont.Font(family="Segoe UI", size=11, weight="bold"))
    prev_title.pack(side=tk.LEFT)
    
    status_label = tk.Label(title_frame, text="正在捕获...", 
                           bg="#2d2d2d", fg="#27ae60", 
                           font=title_font)
    status_label.pack(side=tk.RIGHT)
    
    # 预览画布容器
    canvas_frame = tk.Frame(prev_frame, bg="#1a1a1a", 
                           highlightbackground="#3a3a3a", 
                           highlightthickness=1)
    canvas_frame.pack(fill=tk.BOTH, expand=True)
    
    prev_canvas = tk.Canvas(canvas_frame, 
                           width=PREVIEW_W - 32, 
                           height=PREVIEW_H - 100, 
                           bg="#1a1a1a", 
                           highlightthickness=0)
    prev_canvas.pack(padx=4, pady=4)
    
    # 底部信息和状态指示
    bottom_frame = tk.Frame(prev_frame, bg="#2d2d2d")
    bottom_frame.pack(fill=tk.X, pady=(8, 0))
    
    # 左侧：匹配状态指示器
    status_indicator = tk.Label(bottom_frame, text="●", 
                               bg="#2d2d2d", fg="#27ae60", 
                               font=tkfont.Font(family="Segoe UI", size=14))
    status_indicator.pack(side=tk.LEFT, padx=(0, 6))
    
    # 右侧：尺寸信息
    info_text = tk.Label(bottom_frame, text="", 
                        bg="#2d2d2d", fg="#8e8e93", 
                        font=title_font)
    info_text.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    # 预览窗口位置
    preview_x = right + 20
    preview_y = top
    
    if preview_x + PREVIEW_W > sw:
        preview_x = left - PREVIEW_W - 20
        if preview_x < 0:
            preview_x = 10
    
    if preview_y + PREVIEW_H > sh:
        preview_y = sh - PREVIEW_H - 10
    
    preview.geometry(f"{PREVIEW_W}x{PREVIEW_H}+{preview_x}+{preview_y}")
    
    photo_ref = [None]
    frame_count = [0]
    last_img_height = [0]
    
    def update_preview():
        if preview.winfo_exists() and current_result_holder and len(current_result_holder) > 0 and current_result_holder[0] is not None:
            try:
                img = current_result_holder[0]
                if img and ImageTk is not None:
                    current_height = img.height
                    
                    # 检测匹配状态（从 current_result_holder[1] 获取）
                    match_status = current_result_holder[1] if len(current_result_holder) > 1 else None
                    
                    if match_status is True:
                        # 匹配成功，显示绿色
                        status_indicator.config(fg="#27ae60", text="●")
                    elif match_status is False:
                        # 匹配失败，显示红色
                        status_indicator.config(fg="#e74c3c", text="●")
                    elif current_height > last_img_height[0]:
                        # 备用方案：高度增加也视为成功
                        status_indicator.config(fg="#27ae60", text="●")
                        last_img_height[0] = current_height
                    
                    if current_height > last_img_height[0]:
                        last_img_height[0] = current_height
                    
                    frame_count[0] += 1
                    
                    # 更新状态
                    status_label.config(text=f"已捕获 {frame_count[0]} 帧")
                    info_text.config(text=f"图像: {img.width} × {img.height} px")
                    
                    # 计算缩略图
                    canvas_w = PREVIEW_W - 40
                    canvas_h = PREVIEW_H - 108
                    r = min(canvas_w / img.width, canvas_h / img.height, 1.0)
                    nw, nh = int(img.width * r), int(img.height * r)
                    
                    thumb = img.copy()
                    if thumb.mode != "RGB":
                        thumb = thumb.convert("RGB")
                    thumb = thumb.resize((nw, nh), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(thumb)
                    photo_ref[0] = photo
                    prev_canvas.delete("all")
                    
                    # 计算画布上的偏移（居中）
                    canvas_x = (canvas_w - nw) // 2
                    canvas_y = (canvas_h - nh) // 2
                    
                    # 居中显示缩略图
                    prev_canvas.create_image(canvas_x + nw // 2, canvas_y + nh // 2, image=photo)
                    
                    # 绘制当前视口位置指示器（绿色矩形框）
                    if img.height > h_rect:
                        # 计算当前视口在长图中的相对位置
                        viewport_ratio = h_rect / img.height
                        indicator_h = max(int(nh * viewport_ratio), 15)  # 至少15px高
                        # 假设当前视口在底部（最新拼接的位置）
                        indicator_y = nh - indicator_h
                        
                        # 绘制半透明填充的矩形
                        prev_canvas.create_rectangle(
                            canvas_x + 1, 
                            canvas_y + indicator_y,
                            canvas_x + nw - 1,
                            canvas_y + indicator_y + indicator_h,
                            outline="#27ae60", 
                            width=3,
                            stipple="gray50"  # 半透明效果
                        )
            except Exception as e:
                pass
        if toolbar.winfo_exists():
            toolbar.after(250, update_preview)

    def on_done():
        stop_event.set()
        done_action[0] = "done"
        for widget in [overlay, toolbar, preview, root]:
            try:
                widget.destroy()
            except:
                pass

    def on_cancel():
        stop_event.set()
        done_action[0] = "cancel"
        for widget in [overlay, toolbar, preview, root]:
            try:
                widget.destroy()
            except:
                pass

    btn_done.configure(command=on_done)
    btn_cancel.configure(command=on_cancel)
    toolbar.protocol("WM_DELETE_WINDOW", on_cancel)
    toolbar.after(350, update_preview)
    root.mainloop()
