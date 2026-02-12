# -*- coding: utf-8 -*-
"""
区域截图：全屏半透明遮罩，鼠标拖拽选区，松开后截取区域并回调。
"""
import base64
import io

from PyQt6.QtCore import Qt, QRect, QPoint
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtGui import QPainter, QColor, QPen


class RegionCaptureWidget(QWidget):
    """全屏选区窗口：半透明背景，拖拽绘制矩形，松开后截取该区域。"""

    def __init__(self, on_captured=None, parent=None):
        super().__init__(parent)
        self._on_captured = on_captured  # (base64_data_url: str) -> None
        self._start = QPoint()
        self._end = QPoint()
        self._pressing = False
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.CrossCursor)

    def run(self):
        """显示全屏遮罩并开始选区。"""
        self.setGeometry(QApplication.primaryScreen().geometry())
        self.showFullScreen()
        self.raise_()
        self.activateWindow()
        self._start = QPoint()
        self._end = QPoint()
        self._pressing = False
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._pressing = True
            self._start = self._end = event.globalPosition().toPoint()
            self.update()
        elif event.button() == Qt.MouseButton.RightButton:
            self._cancel()

    def mouseMoveEvent(self, event):
        if self._pressing:
            self._end = event.globalPosition().toPoint()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton or not self._pressing:
            return
        self._pressing = False
        r = self._normalized_rect()
        if r.width() >= 5 and r.height() >= 5:
            self._capture_region(r)
        self._cancel()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Escape, Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._cancel()

    def _normalized_rect(self):
        x1, y1 = self._start.x(), self._start.y()
        x2, y2 = self._end.x(), self._end.y()
        return QRect(
            min(x1, x2), min(y1, y2),
            abs(x2 - x1), abs(y2 - y1),
        )

    def _capture_region(self, rect: QRect):
        screen = QApplication.primaryScreen()
        if screen is None:
            self._cancel()
            return
        pixmap = screen.grabWindow(0, rect.x(), rect.y(), rect.width(), rect.height())
        # 转 PIL 再转 base64，与现有接口一致
        img = pixmap.toImage()
        # QImage -> PNG 字节 -> base64
        from PyQt6.QtCore import QBuffer
        buf = QBuffer()
        buf.open(QBuffer.OpenModeFlag.WriteOnly)
        img.save(buf, "PNG")
        b = bytes(buf.data().data())
        buf.close()
        b64 = base64.b64encode(b).decode("ascii")
        data_url = f"data:image/png;base64,{b64}"
        if self._on_captured:
            self._on_captured(data_url)
        self.close()

    def _cancel(self):
        self.close()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        # 半透明全屏
        painter.fillRect(self.rect(), QColor(0, 0, 0, 120))
        r = self._normalized_rect()
        if r.width() > 0 and r.height() > 0:
            # 选区内部透明（挖空）
            from PyQt6.QtGui import QRegion
            painter.setCompositionMode(QPainter.CompositionMode.Composition_Clear)
            painter.fillRect(r, Qt.GlobalColor.transparent)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            # 选区边框
            painter.setPen(QPen(QColor(0, 180, 255), 2, Qt.PenStyle.SolidLine))
            painter.drawRect(r)
        painter.end()
