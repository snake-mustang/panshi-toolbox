# -*- coding: utf-8 -*-
"""
OCR：从图片（data URL 或文件）识别文字。
使用 RapidOCR，仅 pip 安装即可；打包进 exe 后用户无需安装任何其它东西。
注意：RapidOCR 仅支持 Python 3.6~3.12，打包时请使用 3.11 或 3.12。
"""
import base64
import io

from PIL import Image


def _decode_data_url(data_url: str) -> bytes:
    """从 data:image/xxx;base64,... 解析出图片二进制。"""
    if not data_url or not data_url.startswith("data:"):
        return b""
    i = data_url.find("base64,")
    if i == -1:
        return b""
    return base64.b64decode(data_url[i + 7:], validate=True)


class OcrHandler:
    """OCR 识别封装（RapidOCR）。未安装时返回友好提示，打包 exe 时带上 requirements-ocr 即可。"""

    _NOT_INSTALLED = False

    def __init__(self):
        self._engine = None

    def _get_engine(self):
        """懒加载 RapidOCR；未安装（如 3.13 环境）时返回 _NOT_INSTALLED。"""
        if self._engine is None:
            try:
                from rapidocr_onnxruntime import RapidOCR
                self._engine = RapidOCR()
            except ImportError:
                self._engine = self._NOT_INSTALLED
        return self._engine

    def _recognize_pil(self, img: Image.Image) -> str:
        """PIL Image 用 RapidOCR 识别。"""
        engine = self._get_engine()
        if engine is self._NOT_INSTALLED:
            return "[OCR 未安装] 打包时请用 Python 3.11/3.12 并执行 pip install -r requirements-ocr.txt，打好的 exe 将自带 OCR。"
        try:
            import numpy as np
            if img.mode != "RGB":
                img = img.convert("RGB")
            arr = np.array(img)
            result, _ = engine(arr)
            if not result:
                return ""
            lines = []
            for item in result:
                if len(item) >= 2 and item[1]:
                    lines.append(str(item[1]).strip())
            return "\n".join(lines)
        except Exception as e:
            return f"[OCR 错误] {e!s}"

    def recognize_from_data_url(self, data_url: str) -> str:
        """从 base64 数据 URL 识别文字。"""
        raw = _decode_data_url(data_url)
        if not raw:
            return ""
        try:
            img = Image.open(io.BytesIO(raw))
            return self._recognize_pil(img)
        except Exception as e:
            return f"[OCR 错误] {e!s}"

    def recognize_from_file(self, path: str) -> str:
        """从本地图片文件路径识别文字。"""
        try:
            with open(path, "rb") as f:
                img = Image.open(io.BytesIO(f.read()))
            return self._recognize_pil(img)
        except FileNotFoundError:
            return f"[OCR 错误] 文件不存在: {path}"
        except Exception as e:
            return f"[OCR 错误] {e!s}"
