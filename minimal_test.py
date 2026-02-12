# -*- coding: utf-8 -*-
"""最小测试：仅 PyQt6 窗口，不导入 backend。若此脚本能正常显示窗口，则问题在 backend 或 MainWindow。"""
import sys
print("minimal_test: 导入 PyQt6...", flush=True)
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt6.QtCore import Qt
print("minimal_test: 创建 QApplication...", flush=True)
app = QApplication(sys.argv)
print("minimal_test: 创建窗口...", flush=True)
win = QMainWindow()
win.setWindowTitle("最小测试")
win.setMinimumSize(400, 300)
lab = QLabel("若能看到此窗口且不退出，说明 PyQt6 正常，问题在 backend/main。")
lab.setAlignment(Qt.AlignmentFlag.AlignCenter)
win.setCentralWidget(lab)
print("minimal_test: show()...", flush=True)
win.show()
print("minimal_test: 进入事件循环...", flush=True)
sys.exit(app.exec())
