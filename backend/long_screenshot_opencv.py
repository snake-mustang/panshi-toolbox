# -*- coding: utf-8 -*-
"""
长截图 - PixPin 风格增量拼接算法
核心思路：相邻帧底部/顶部模板匹配 → 计算偏移量 → 增量拼接
"""
import sys
import time
import numpy as np
from PIL import Image

try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

try:
    from mss import mss
    MSS_AVAILABLE = True
except ImportError:
    MSS_AVAILABLE = False
    from PIL import ImageGrab

# 用户手动滚动时，每次截图的间隔（秒）
CAPTURE_INTERVAL = 0.25
# 两帧视为「几乎相同」的相似度阈值
SAME_FRAME_THRESHOLD = 0.98
# 模板匹配的重叠区域比例（30% = 底部30%与顶部30%匹配）
OVERLAP_RATIO = 0.3
# 模板匹配的置信度阈值（越高越严格，0.7 = 70%）
MATCH_CONFIDENCE_THRESHOLD = 0.7
# 最大存储帧数（避免内存溢出）
MAX_FRAMES = 150


def _capture_region_mss(rect):
    """使用 MSS 高速截取指定区域（返回 BGR numpy array）"""
    if MSS_AVAILABLE:
        with mss() as sct:
            monitor = {
                "top": rect[1],
                "left": rect[0],
                "width": rect[2],
                "height": rect[3]
            }
            sct_img = sct.grab(monitor)
            # 转换为 numpy array (BGRA)
            img = np.array(sct_img)
            # BGRA -> BGR
            if img.shape[2] == 4:
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            return img
    else:
        # 降级使用 PIL
        x, y, w, h = rect
        pil_img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
        # PIL RGB -> OpenCV BGR
        img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        return img


def _images_almost_same(img1, img2, threshold=SAME_FRAME_THRESHOLD):
    """
    判断两张图片是否几乎相同（使用快速像素比较）。
    
    Args:
        img1, img2: numpy arrays (H, W, 3), BGR format
        threshold: 相似度阈值（0-1），越接近 1 表示越相似
    
    Returns:
        bool: 如果相似度 >= threshold，返回 True
    """
    if img1 is None or img2 is None:
        return False
    if img1.shape != img2.shape:
        return False
    
    # 快速像素差异检测
    diff = np.sum(np.abs(img1.astype(np.int32) - img2.astype(np.int32)))
    max_diff = img1.shape[0] * img1.shape[1] * img1.shape[2] * 255
    similarity = 1.0 - (diff / max_diff)
    
    return similarity >= threshold


def _find_overlap_offset(base_img, new_img, overlap_ratio=OVERLAP_RATIO, threshold=MATCH_CONFIDENCE_THRESHOLD):
    """
    使用模板匹配找到两帧之间的垂直偏移量（增量拼接核心算法）。
    
    PixPin 的核心原理：
    1. 取基准图（已拼接长图）的底部 30% 作为模板
    2. 在新帧的顶部 60% 区域搜索该模板
    3. 找到最佳匹配位置，计算偏移量
    4. 根据偏移量裁剪掉重复部分，只拼接新内容
    
    Args:
        base_img: 基准图（已拼接的长图），numpy array (H, W, 3) BGR
        new_img: 新帧图，numpy array (H, W, 3) BGR
        overlap_ratio: 重叠区域比例（默认 0.3 = 30%）
        threshold: 匹配阈值（0-1，越高越严格）
    
    Returns:
        (offset, confidence): 
            - offset: 新内容的起始行（>0 表示有新内容），int
            - confidence: 匹配置信度（0-1），float
        如果匹配失败，返回 (0, 0.0)
    """
    if base_img is None or new_img is None:
        return 0, 0.0
    
    h_base, w_base = base_img.shape[:2]
    h_new, w_new = new_img.shape[:2]
    
    # 确保宽度一致
    if w_base != w_new:
        return 0, 0.0
    
    # 计算重叠区域高度（至少 20px）
    overlap_h = max(int(h_base * overlap_ratio), 20)
    overlap_h = min(overlap_h, h_base // 2, h_new // 2)
    
    if overlap_h < 20:
        return 0, 0.0
    
    # 基准图底部区域（模板）
    template = base_img[-overlap_h:, :]
    
    # 新图可搜索区域（允许新图顶部到中部范围，搜索范围为 overlap_h * 2）
    search_h = min(overlap_h * 2, h_new)
    search_region = new_img[:search_h, :]
    
    if search_region.shape[0] < template.shape[0]:
        return 0, 0.0
    
    # 模板匹配（使用归一化相关系数）
    try:
        result = cv2.matchTemplate(search_region, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        # 检查匹配质量
        if max_val >= threshold:
            # 计算新内容的起始行
            match_y = max_loc[1]  # 匹配位置的 Y 坐标
            # 新内容从 match_y + overlap_h 开始
            new_content_start = match_y + overlap_h
            return new_content_start, max_val
        else:
            return 0, max_val
    except Exception as e:
        return 0, 0.0


def _stitch_incremental(base_img, new_img, overlap_ratio=OVERLAP_RATIO, threshold=MATCH_CONFIDENCE_THRESHOLD):
    """
    增量拼接：将新帧拼接到基准图底部（仅拼接新内容）。
    
    Args:
        base_img: 基准图（已拼接的长图），numpy array (H, W, 3) BGR
        new_img: 新帧图，numpy array (H, W, 3) BGR
        overlap_ratio: 重叠区域比例
        threshold: 匹配阈值
    
    Returns:
        (stitched_img, success): 
            - stitched_img: 拼接后的图像，numpy array (H, W, 3) BGR
            - success: 是否成功拼接（True/False）
    """
    # 第一次拼接
    if base_img is None:
        return new_img, True
    
    # 查找重叠偏移量
    new_content_start, confidence = _find_overlap_offset(base_img, new_img, overlap_ratio, threshold)
    
    # 匹配失败
    if new_content_start == 0:
        # 返回原图，不拼接
        return base_img, False
    
    # 提取新内容
    new_content = new_img[new_content_start:, :]
    
    # 如果没有新内容（完全重叠），返回原图
    if new_content.shape[0] == 0:
        return base_img, False
    
    # 垂直拼接
    stitched = np.vstack([base_img, new_content])
    
    return stitched, True


def capture_long_screenshot_opencv(rect, stop_event, on_log=None, current_result_holder=None):
    """
    使用增量拼接算法进行长截图（PixPin 风格）
    
    Args:
        rect: (x, y, width, height) 截图区域
        stop_event: threading.Event，用于停止截图
        on_log: 日志回调函数
        current_result_holder: 实时预览容器 [PIL.Image]，同时用于传递匹配状态
    
    Returns:
        PIL.Image: 拼接后的长图
    """
    if not OPENCV_AVAILABLE:
        if on_log:
            on_log("[长截图] 未安装 OpenCV，请安装: pip install opencv-contrib-python")
        return None
    
    if on_log:
        on_log("已记录首帧，请手动滚动内容…")
    
    stitched_base = None  # 当前已拼接的长图（BGR）
    last_capture = None   # 上一帧（用于去重）
    frame_count = 0       # 总帧数
    stitch_count = 0      # 成功拼接次数
    
    # 用于传递匹配状态的标志（存储在 current_result_holder 的第二个元素）
    # current_result_holder: [PIL.Image, match_status]
    # match_status: True=成功, False=失败, None=初始
    
    try:
        while not stop_event.is_set():
            # 截取当前帧
            current_frame = _capture_region_mss(rect)
            
            # 跳过相同帧（用户未滚动）
            if last_capture is not None and _images_almost_same(last_capture, current_frame):
                time.sleep(CAPTURE_INTERVAL)
                continue
            
            frame_count += 1
            
            # 增量拼接
            stitched_base, success = _stitch_incremental(stitched_base, current_frame)
            
            if success:
                stitch_count += 1
            
            # 更新预览
            if current_result_holder is not None and stitched_base is not None:
                # BGR -> RGB -> PIL
                preview_rgb = cv2.cvtColor(stitched_base, cv2.COLOR_BGR2RGB)
                pil_preview = Image.fromarray(preview_rgb)
                
                # 更新预览图像和匹配状态
                if len(current_result_holder) >= 2:
                    current_result_holder[0] = pil_preview
                    current_result_holder[1] = success  # 传递匹配状态
                else:
                    current_result_holder[0] = pil_preview
            
            last_capture = current_frame
            
            # 每 5 帧输出一次日志
            if on_log and frame_count % 5 == 0:
                on_log(f"已捕获 {frame_count} 帧，成功拼接 {stitch_count} 次")
            
            # 限制最大帧数
            if frame_count >= MAX_FRAMES:
                if on_log:
                    on_log(f"已达到最大帧数 {MAX_FRAMES}，请点击完成")
                break
            
            time.sleep(CAPTURE_INTERVAL)
    
    except Exception as e:
        if on_log:
            on_log(f"[捕获异常] {e}")
        return None
    
    # 最终结果
    if stitched_base is None:
        if on_log:
            on_log("未捕获到任何内容")
        return None
    
    # 转换为 PIL Image (BGR -> RGB)
    result_rgb = cv2.cvtColor(stitched_base, cv2.COLOR_BGR2RGB)
    pil_result = Image.fromarray(result_rgb)
    
    if on_log:
        on_log(f"拼接完成，最终图像大小: {pil_result.width}x{pil_result.height}")
        on_log(f"统计：捕获 {frame_count} 帧，成功拼接 {stitch_count} 次")
    
    return pil_result


# 保持兼容性：提供旧接口名称
def capture_long_screenshot_manual(rect, stop_event, on_log=None, current_result_holder=None):
    """兼容性接口，调用新的增量拼接实现"""
    return capture_long_screenshot_opencv(rect, stop_event, on_log, current_result_holder)
