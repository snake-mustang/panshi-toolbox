# -*- coding: utf-8 -*-
"""
截图功能：全屏截图、区域选择截图，返回 PIL Image 或 base64。
"""
import base64
import io
import sys

from PIL import ImageGrab


def _get_scale_factor():
    """Windows 高 DPI 缩放因子（可选，后续可改为从 Qt 获取）。"""
    if sys.platform != "win32":
        return 1.0
    try:
        import ctypes
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass
    return 1.0


class ScreenshotHandler:
    """截图处理：全屏截图、区域截图（区域由外部传入或后续用 Qt 选区窗口）。"""

    def __init__(self, on_region_captured=None):
        """
        :param on_region_captured: 可选回调 (pil_image) -> None，区域截图完成时调用
        """
        self._on_region_captured = on_region_captured
        self._scale = _get_scale_factor()

    def capture_full_pil(self):
        """全屏截图，返回 PIL.Image。"""
        return ImageGrab.grab()

    def capture_full_base64(self) -> str:
        """全屏截图，返回 data:image/png;base64,..."""
        img = self.capture_full_pil()
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        return f"data:image/png;base64,{b64}"

    def capture_region_base64(self, x1: int, y1: int, x2: int, y2: int) -> str:
        """指定矩形区域截图，返回 data URL。坐标可为屏幕坐标。"""
        box = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
        img = ImageGrab.grab(bbox=box)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        return f"data:image/png;base64,{b64}"

    def start_region_capture(self):
        """
        开始区域截图。需要与 Qt 配合：先隐藏主窗口，显示全屏遮罩+选区，
        用户拖拽完成后调用 capture_region_base64 或把 PIL 转 base64 后通过 bridge 传回。
        此处先简化为触发全屏截图并回调（等同 capture_full_base64）。
        """
        if self._on_region_captured:
            self._on_region_captured(self.capture_full_pil())
        # 若没有选区 UI，前端可先调用 captureFullScreen 作为简单版
        return
