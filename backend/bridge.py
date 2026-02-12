# -*- coding: utf-8 -*-
"""
Qt-WebChannel 桥接对象：暴露给 Vue3 前端的 Python 方法。
"""
from PyQt6.QtCore import QObject, pyqtSlot, pyqtSignal


class AppBridge(QObject):
    """供 QWebChannel 暴露给前端的桥接对象。"""

    # 信号：可从前端 connect 监听
    screenshotFinished = pyqtSignal(str)   # base64 图片数据 URL
    ocrFinished = pyqtSignal(str)          # 识别出的文字
    errorOccurred = pyqtSignal(str)        # 错误信息
    logReceived = pyqtSignal(str)          # 打印台日志（前端/后端均可触发）

    def __init__(self, screenshot_handler=None, ocr_handler=None, parent=None):
        super().__init__(parent)
        self._screenshot = screenshot_handler
        self._ocr = ocr_handler

    @pyqtSlot(result=str)
    def getAppVersion(self):
        """返回应用版本，供前端显示。"""
        return "v1.0.0"

    @pyqtSlot(result=str)
    def getPlatform(self):
        """返回当前平台：windows / darwin / linux。"""
        import sys
        if sys.platform == "win32":
            return "windows"
        if sys.platform == "darwin":
            return "darwin"
        return "linux"

    # --------------- 截图 ---------------
    @pyqtSlot()
    def startScreenshot(self):
        """开始截图（区域选择）。完成后通过 screenshotFinished 信号通知。"""
        self.logReceived.emit("[截图] 开始区域选择…")
        main_win = self.parent()
        if main_win and hasattr(main_win, "start_region_screenshot"):
            main_win.start_region_screenshot()
        elif self._screenshot:
            self._screenshot.start_region_capture()
        else:
            self.errorOccurred.emit("截图模块未初始化")

    @pyqtSlot(result=str)
    def captureFullScreen(self):
        """全屏截图，返回 base64 数据 URL（data:image/png;base64,...）。"""
        if self._screenshot:
            return self._screenshot.capture_full_base64()
        self.errorOccurred.emit("截图模块未初始化")
        return ""

    # --------------- OCR ---------------
    @pyqtSlot(str, result=str)
    def recognizeImageFromBase64(self, data_url: str) -> str:
        """
        从 base64 数据 URL 识别文字并返回文本。
        :param data_url: 如 "data:image/png;base64,..."
        :return: 识别出的文字，失败返回空字符串并触发 errorOccurred
        """
        if self._ocr:
            return self._ocr.recognize_from_data_url(data_url)
        self.errorOccurred.emit("OCR 模块未初始化")
        return ""

    @pyqtSlot(str, result=str)
    def recognizeImageFromPath(self, path: str) -> str:
        """从本地图片路径识别文字。"""
        if self._ocr:
            return self._ocr.recognize_from_file(path)
        self.errorOccurred.emit("OCR 模块未初始化")
        return ""

    @pyqtSlot(str)
    def logMessage(self, text: str):
        """向后端打印台输出一行（供前端调用）。"""
        self.logReceived.emit(str(text))
