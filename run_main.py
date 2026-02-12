# -*- coding: utf-8 -*-
"""启动入口：完整界面 + 截图 / 截图识字 + 样式，backend 按需懒加载。"""
import sys
import base64

if __name__ == "__main__":
    print("黄同学的AI工具箱 启动中...", flush=True)
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QPushButton, QFrame, QStackedWidget, QMessageBox,
        QTextEdit, QScrollArea, QFileDialog,
    )
    from PyQt6.QtCore import Qt, QBuffer
    from PyQt6.QtGui import QImage, QPixmap

    app = QApplication(sys.argv)
    app.setApplicationName("IT Toolbox")
    app.setStyleSheet("""
        QMainWindow { background-color: #f2f2f7; }
        QWidget { background-color: transparent; font-family: "Segoe UI", "PingFang SC", sans-serif; }
        QPushButton {
            background-color: #007AFF; color: white; border: none;
            border-radius: 10px; padding: 10px 20px; font-size: 14px;
        }
        QPushButton:hover { background-color: #0051d5; }
        QPushButton:pressed { background-color: #004ec4; }
        QPushButton[flat="true"] {
            background-color: transparent; color: #3a3a3c; text-align: left;
        }
        QPushButton[flat="true"]:hover { background-color: rgba(0,0,0,0.04); }
        QPushButton[flat="true"][active="true"] { color: #007AFF; background-color: rgba(0,122,255,0.12); }
        QTextEdit { border: 1px solid rgba(0,0,0,0.1); border-radius: 10px; padding: 12px; font-size: 14px; }
    """)

    win = QMainWindow()
    win.setWindowTitle("黄同学的AI工具箱")
    win.setMinimumSize(900, 600)
    win.resize(1100, 750)

    # 用于显示截图、OCR 结果的共享数据（供截图页/OCR 页使用）
    last_screenshot_data_url = [None]  # 用 list 以便闭包修改

    def data_url_to_pixmap(data_url):
        if not data_url or not data_url.startswith("data:image"):
            return None
        i = data_url.find("base64,")
        if i == -1:
            return None
        raw = base64.b64decode(data_url[i + 7 :])
        img = QImage()
        if not img.loadFromData(raw):
            return None
        return QPixmap.fromImage(img)

    # ---------- 根布局：侧栏 + 内容栈 ----------
    root = QWidget()
    root.setObjectName("root")
    root.setStyleSheet("#root { background-color: #f2f2f7; }")
    layout_root = QHBoxLayout(root)
    layout_root.setContentsMargins(0, 0, 0, 0)
    layout_root.setSpacing(0)

    # 右侧：内容区 + 底部打印台（截图页单独放在 stack 外，避免 QStackedWidget 吞掉点击）
    right_widget = QWidget()
    right_layout = QVBoxLayout(right_widget)
    right_layout.setContentsMargins(0, 0, 0, 0)
    right_layout.setSpacing(0)
    content_switcher = QWidget()
    content_switcher_layout = QVBoxLayout(content_switcher)
    content_switcher_layout.setContentsMargins(0, 0, 0, 0)
    content_switcher_layout.setSpacing(0)
    console_edit = QTextEdit()
    console_edit.setReadOnly(True)
    console_edit.setMaximumHeight(200)
    console_edit.setPlaceholderText("打印台：日志与调试信息将显示在这里")
    console_edit.setStyleSheet("QTextEdit { font-family: Consolas, monospace; font-size: 12px; background-color: #1e1e1e; color: #d4d4d4; border-top: 1px solid rgba(0,0,0,0.1); padding: 8px; }")

    def log(msg: str):
        from datetime import datetime
        line = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
        console_edit.append(line)
        console_edit.verticalScrollBar().setValue(console_edit.verticalScrollBar().maximum())
        print(line, flush=True)

    # ---------- 左侧栏 ----------
    sidebar = QFrame()
    sidebar.setFixedWidth(220)
    sidebar.setStyleSheet("QFrame { background-color: #ffffff; border-right: 1px solid rgba(0,0,0,0.08); }")
    layout_side = QVBoxLayout(sidebar)
    layout_side.setContentsMargins(20, 24, 20, 16)
    layout_side.setSpacing(4)
    title = QLabel("黄同学的AI工具箱")
    title.setStyleSheet("font-size: 20px; font-weight: 600; color: #1d1d1f;")
    layout_side.addWidget(title)
    ver = QLabel("v1.0.0")
    ver.setStyleSheet("font-size: 13px; color: #8e8e93; margin-top: 6px;")
    layout_side.addWidget(ver)
    layout_side.addSpacing(20)

    stack = QStackedWidget()
    content_switcher_layout.addWidget(stack, 1)
    nav_buttons = []

    nav_style_inactive = "QPushButton { font-size: 15px; padding: 12px 16px; border-radius: 10px; text-align: left; background: transparent; color: #3a3a3c; } QPushButton:hover { background-color: rgba(0,0,0,0.04); }"
    nav_style_active   = "QPushButton { font-size: 15px; padding: 12px 16px; border-radius: 10px; text-align: left; color: #007AFF; background-color: rgba(0,122,255,0.12); }"

    def make_nav(name, index):
        btn = QPushButton(name)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        def go():
            for i, b in enumerate(nav_buttons):
                b.setStyleSheet(nav_style_active if i == index else nav_style_inactive)
            if index == 1:
                log("切换到: 截图页")
                stack.hide()
                page_screen.show()
            else:
                page_screen.hide()
                stack.show()
                stack.setCurrentIndex(0 if index == 0 else 1)
        btn.clicked.connect(go)
        nav_buttons.append(btn)
        return btn

    layout_side.addWidget(make_nav("首页", 0))
    layout_side.addWidget(make_nav("截图", 1))
    layout_side.addWidget(make_nav("截图识字", 2))
    nav_buttons[0].setStyleSheet(nav_style_active)
    for i in range(1, len(nav_buttons)):
        nav_buttons[i].setStyleSheet(nav_style_inactive)
    layout_side.addStretch()
    layout_root.addWidget(sidebar)

    # ---------- 首页 ----------
    page_home = QWidget()
    page_home.setStyleSheet("background-color: #f2f2f7;")
    lay_home = QVBoxLayout(page_home)
    lay_home.setContentsMargins(24, 24, 24, 24)
    lay_home.setSpacing(24)
    lbl_home_title = QLabel("推荐工具")
    lbl_home_title.setStyleSheet("font-size: 28px; font-weight: 700; color: #1d1d1f;")
    lay_home.addWidget(lbl_home_title)
    cards_home = QHBoxLayout()
    cards_home.setSpacing(20)

    def card_ui(title, desc, on_click):
        f = QFrame()
        f.setStyleSheet("QFrame { background-color: #ffffff; border-radius: 12px; padding: 24px; border: 1px solid rgba(0,0,0,0.06); }")
        f.setMinimumSize(260, 140)
        f.setCursor(Qt.CursorShape.PointingHandCursor)
        lay = QVBoxLayout(f)
        lay.setSpacing(8)
        lay.addWidget(QLabel(title, styleSheet="font-size: 17px; font-weight: 600; color: #1d1d1f;"))
        lay.addWidget(QLabel(desc, styleSheet="font-size: 14px; color: #8e8e93;"))
        btn = QPushButton("打开")
        btn.setFixedWidth(80)
        btn.clicked.connect(on_click)
        lay.addWidget(btn)
        return f

    card1 = card_ui("截图", "区域选择或全屏截图", lambda: stack.setCurrentIndex(1))
    card2 = card_ui("截图识字", "读取截图中的文字并输出", lambda: stack.setCurrentIndex(2))
    cards_home.addWidget(card1)
    cards_home.addWidget(card2)
    lay_home.addLayout(cards_home)
    lay_home.addWidget(QLabel("快捷键 Ctrl+K 唤起/隐藏窗口（若已启用）", styleSheet="font-size: 13px; color: #8e8e93;"))
    lay_home.addStretch()
    stack.addWidget(page_home)

    # ---------- 截图页 ----------
    page_screen = QWidget()
    page_screen.setStyleSheet("background-color: #f2f2f7;")
    lay_screen = QVBoxLayout(page_screen)
    lay_screen.setContentsMargins(24, 24, 24, 24)
    lay_screen.setSpacing(20)
    lay_screen.addWidget(QLabel("截图", styleSheet="font-size: 28px; font-weight: 700; color: #1d1d1f;"))
    btn_row = QHBoxLayout()
    btn_region = QPushButton("区域截图")
    btn_full = QPushButton("全屏截图")
    for b in (btn_region, btn_full):
        b.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        b.setMinimumSize(120, 44)
        b.setCursor(Qt.CursorShape.PointingHandCursor)

    def on_region_capture():
        log("点击: 区域截图")
        try:
            from backend.region_capture import RegionCaptureWidget
            win._region_capture = None

            def done(data_url):
                last_screenshot_data_url[0] = data_url
                win.show()
                win.raise_()
                win.activateWindow()
                if data_url:
                    pix = data_url_to_pixmap(data_url)
                    if pix and not pix.isNull():
                        lbl_preview.setPixmap(pix.scaled(600, 400, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                        lbl_preview.setVisible(True)

            w = RegionCaptureWidget(on_captured=done)
            win._region_capture = w

            def on_closed():
                win.show()
                win.raise_()
                win.activateWindow()
                win._region_capture = None

            w.destroyed.connect(on_closed)
            win.hide()
            QApplication.processEvents()
            w.run()
        except Exception as e:
            win.show()
            QMessageBox.warning(win, "错误", str(e))

    def on_full_capture():
        log("点击: 全屏截图")
        try:
            data_url = None
            try:
                from backend.screenshot import ScreenshotHandler
                h = ScreenshotHandler()
                data_url = h.capture_full_base64()
            except Exception:
                screen = QApplication.primaryScreen()
                if screen:
                    pixmap = screen.grabWindow(0)
                    img = pixmap.toImage()
                    buf = QBuffer()
                    buf.open(QBuffer.OpenModeFlag.WriteOnly)
                    img.save(buf, "PNG")
                    b64 = base64.b64encode(bytes(buf.data())).decode("ascii")
                    data_url = f"data:image/png;base64,{b64}"
            if not data_url:
                QMessageBox.warning(win, "错误", "全屏截图失败")
                return
            last_screenshot_data_url[0] = data_url
            pix = data_url_to_pixmap(data_url)
            if pix and not pix.isNull():
                lbl_preview.setPixmap(pix.scaled(600, 400, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                lbl_preview.setVisible(True)
        except Exception as e:
            QMessageBox.warning(win, "错误", str(e))

    btn_region.clicked.connect(on_region_capture)
    btn_full.clicked.connect(on_full_capture)
    btn_row.addWidget(btn_region)
    btn_row.addWidget(btn_full)
    lay_screen.addLayout(btn_row)
    lbl_preview = QLabel()
    lbl_preview.setVisible(False)
    lbl_preview.setStyleSheet("background: #fff; border-radius: 8px; padding: 8px;")
    lbl_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lay_screen.addWidget(lbl_preview, 1)
    content_switcher_layout.addWidget(page_screen, 1)
    page_screen.hide()

    # ---------- 截图识字页 ----------
    page_ocr = QWidget()
    page_ocr.setStyleSheet("background-color: #f2f2f7;")
    lay_ocr = QVBoxLayout(page_ocr)
    lay_ocr.setContentsMargins(24, 24, 24, 24)
    lay_ocr.setSpacing(20)
    lay_ocr.addWidget(QLabel("截图识字", styleSheet="font-size: 28px; font-weight: 700; color: #1d1d1f;"))
    btn_ocr_capture = QPushButton("截屏并识别")
    btn_ocr_file = QPushButton("从文件识别")
    result_edit = QTextEdit()
    result_edit.setPlaceholderText("识别结果将显示在这里")
    result_edit.setMinimumHeight(200)

    def do_ocr(data_url):
        try:
            from backend.ocr_engine import OcrHandler
            ocr = OcrHandler()
            text = ocr.recognize_from_data_url(data_url)
            result_edit.setPlainText(text or "(无文字)")
        except Exception as e:
            result_edit.setPlainText(f"[错误] {e}")

    def on_ocr_capture():
        try:
            from backend.screenshot import ScreenshotHandler
            h = ScreenshotHandler()
            data_url = h.capture_full_base64()
            last_screenshot_data_url[0] = data_url
            result_edit.setPlainText("识别中…")
            do_ocr(data_url)
        except Exception as e:
            result_edit.setPlainText(f"[错误] {e}")

    def on_ocr_file():
        path, _ = QFileDialog.getOpenFileName(win, "选择图片", "", "图片 (*.png *.jpg *.jpeg *.bmp)")
        if not path:
            return
        try:
            from backend.ocr_engine import OcrHandler
            ocr = OcrHandler()
            text = ocr.recognize_from_file(path)
            result_edit.setPlainText(text or "(无文字)")
        except Exception as e:
            result_edit.setPlainText(f"[错误] {e}")

    btn_ocr_capture.clicked.connect(on_ocr_capture)
    btn_ocr_file.clicked.connect(on_ocr_file)
    lay_ocr.addWidget(btn_ocr_capture)
    lay_ocr.addWidget(btn_ocr_file)
    lay_ocr.addWidget(QLabel("识别结果", styleSheet="font-size: 14px; color: #3a3a3c;"))
    lay_ocr.addWidget(result_edit, 1)
    stack.addWidget(page_ocr)

    right_layout.addWidget(content_switcher, 1)
    right_layout.addWidget(console_edit)
    layout_root.addWidget(right_widget, 1)

    # 全局热键 Ctrl+K 需在自定义 QMainWindow 子类中重写 nativeEvent，此处暂不注册

    log("启动完成")
    win.setCentralWidget(root)
    win.show()
    sys.exit(app.exec())
