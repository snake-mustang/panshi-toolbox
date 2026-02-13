# 长截图功能升级说明

## 🎉 功能升级

长截图功能已升级为 **OpenCV Stitcher + MSS** 组合方案，拼接质量大幅提升！

### 新功能特点：

1. **智能拼接算法**：使用 OpenCV 的特征检测和匹配，类似 PixPin
2. **高速截图**：MSS 库截图速度提升 10 倍（< 10ms）
3. **更强容错性**：支持不规则滚动、轻微抖动
4. **自动降级**：OpenCV 失败时自动使用备用简单拼接

### 使用方式：

点击首页的"长截图"卡片中的 **"一键截图"** 按钮即可开始：

1. 工具箱自动隐藏
2. 框选需要截图的区域
3. 手动滚动内容
4. 点击浮窗的"完成"按钮
5. 自动拼接并复制到剪贴板

## 📦 安装新依赖

```bash
# 进入项目目录
cd d:\1-exe\app-toolbox

# 安装新依赖
pip install -r requirements.txt

# 或者单独安装
pip install opencv-contrib-python>=4.8.0
pip install mss>=9.0.0  
pip install numpy>=1.24.0
```

## ⚠️ 注意事项

1. **opencv-contrib-python** 包体积较大（约 50MB），首次安装需要时间
2. 如果网络较慢，可以使用国内镜像：
   ```bash
   pip install -i https://pypi.tuna.tsinghua.edu.cn/simple opencv-contrib-python mss numpy
   ```
3. 已安装过 `opencv-python` 的需要先卸载：
   ```bash
   pip uninstall opencv-python
   pip install opencv-contrib-python
   ```

## 🧪 测试步骤

1. 安装依赖后，刷新应用（F5）
2. 点击首页"长截图"卡片的"一键截图"按钮
3. 框选一个有滚动内容的窗口（如浏览器、文档）
4. 缓慢滚动内容
5. 点击完成，检查拼接效果

## 🔄 回退方案

如果遇到问题，可以临时回退到旧算法：

修改 `backend/api_webview.py` 第 158 行：
```python
# 新算法（OpenCV）
from backend.long_screenshot_opencv import capture_long_screenshot_manual

# 改回旧算法
from backend.long_screenshot import capture_long_screenshot_manual
```

## 📝 技术细节

### OpenCV Stitcher 工作原理：

1. **特征检测**：使用 ORB/SIFT 检测图像特征点
2. **特征匹配**：找到相邻帧的对应关系
3. **变换估计**：计算图像之间的变换矩阵
4. **图像配准**：对齐图像
5. **融合拼接**：无缝合并重叠区域

### MSS 截图优势：

- 跨平台（Windows/macOS/Linux）
- 使用底层 ctypes API，无需额外依赖
- 截图速度 < 10ms（PIL ImageGrab ~100ms）

## 🐛 常见问题

**Q: 提示"未安装 OpenCV"？**  
A: 运行 `pip install opencv-contrib-python>=4.8.0`

**Q: 拼接失败？**  
A: 可能原因：
   - 滚动过快 → 放慢滚动速度
   - 内容太单一（纯色） → 尽量包含复杂内容
   - 内容大量重复 → 会自动降级到简单拼接

**Q: 提示需要 numpy？**  
A: 运行 `pip install numpy>=1.24.0`

## 📞 问题反馈

如有问题，请提供：
1. 错误日志（工具箱底部日志面板）
2. Python 版本（`python --version`）
3. 操作系统版本
