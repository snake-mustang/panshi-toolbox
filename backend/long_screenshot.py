# -*- coding: utf-8 -*-
"""
长截图（PixPin 式）：用户框选区域后，由用户手动滚动内容，程序持续捕获该区域并实时拼接。
参考：https://pixpin.cn/docs/capture/long-capture.html
"""
import sys
import time

from PIL import Image, ImageGrab

# 用户手动滚动时，每次截图的间隔（秒）
CAPTURE_INTERVAL = 0.35
# 用于查找重叠区域的高度（像素），越大越稳但越慢
OVERLAP_SEARCH_HEIGHT = 120
# 重叠区比较步长（像素）
OVERLAP_STEP = 4
# 两帧视为「几乎相同」的像素差阈值（用于跳过未滚动时的重复帧）
SAME_FRAME_DIFF_THRESHOLD = 8000


def _images_almost_same(img1, img2, strip_height=40, threshold=SAME_FRAME_DIFF_THRESHOLD):
    """比较两图底部 strip_height 像素，差异小于 threshold 视为相同（用户未滚动）。"""
    if img1.size != img2.size or img1.height < strip_height or img2.height < strip_height:
        return False
    s1 = img1.crop((0, img1.height - strip_height, img1.width, img1.height))
    s2 = img2.crop((0, img2.height - strip_height, img2.width, img2.height))
    a, b = list(s1.getdata()), list(s2.getdata())
    if len(a) != len(b):
        return False
    diff = sum(abs(x - y) for x, y in zip(a, b))
    return diff < threshold


def _find_overlap(img_top, img_bottom, step=OVERLAP_STEP, search_h=OVERLAP_SEARCH_HEIGHT):
    """
    在 img_bottom 中找与 img_top 底部重叠的 y 偏移。
    img_top: 上一张图（或其上部分）
    img_bottom: 下一张图
    返回: (overlap_height, diff_score)，即从 img_bottom 的哪一行起与 img_top 底部重合，以及该处差异得分（越小越像）。
    """
    w1, h1 = img_top.size
    w2, h2 = img_bottom.size
    if w1 != w2 or h1 < search_h or h2 < search_h:
        return 0, float("inf")
    # 取 img_top 底部 search_h 高的一条
    strip = img_top.crop((0, h1 - search_h, w1, h1))
    strip_arr = list(strip.getdata())
    best_y = 0
    best_score = float("inf")
    for y0 in range(0, min(h2 - search_h + 1, h1), step):
        region = img_bottom.crop((0, y0, w2, y0 + search_h))
        region_arr = list(region.getdata())
        if len(strip_arr) != len(region_arr):
            continue
        score = sum(
            abs(a - b) for a, b in zip(strip_arr, region_arr)
        )
        if score < best_score:
            best_score = score
            best_y = y0
    return best_y, best_score


def capture_long_screenshot_manual(rect, stop_event, on_log=None, current_result_holder=None):
    """
    PixPin 式长截图：在用户手动滚动内容时，持续截取指定区域并实时拼接。
    直到 stop_event 被 set 后结束并返回拼接结果。
    :param rect: (left, top, right, bottom) 屏幕坐标
    :param stop_event: threading.Event，set 后停止捕获
    :param on_log: 可选 (msg: str) -> None 日志回调
    :param current_result_holder: 可选 [None]，每次拼接后将当前长图写入 current_result_holder[0] 供预览
    :return: PIL.Image 或 None
    """
    log = on_log or (lambda msg: None)
    left, top, right, bottom = rect
    if right <= left or bottom <= top:
        return None
    result = None
    last_capture = None
    while not stop_event.is_set():
        try:
            img = ImageGrab.grab(bbox=(left, top, right, bottom))
        except Exception:
            img = None
        if img is None:
            time.sleep(CAPTURE_INTERVAL)
            continue
        if result is None:
            result = img.copy()
            last_capture = img
            if current_result_holder is not None:
                current_result_holder[0] = result
            log("已记录首帧，请手动滚动内容…")
        else:
            if _images_almost_same(last_capture, img):
                time.sleep(CAPTURE_INTERVAL)
                continue
            overlap_y, _ = _find_overlap(result, img)
            add_h = img.height - overlap_y
            if add_h > 5:
                new_h = result.height + add_h
                new_img = Image.new("RGB", (result.width, new_h), (255, 255, 255))
                new_img.paste(result, (0, 0))
                new_img.paste(
                    img.crop((0, overlap_y, img.width, img.height)),
                    (0, result.height),
                )
                result = new_img
                if current_result_holder is not None:
                    current_result_holder[0] = result
                log("已拼接一帧")
            last_capture = img
        time.sleep(CAPTURE_INTERVAL)
    return result
