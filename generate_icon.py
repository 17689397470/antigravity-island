import os
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPainter, QPixmap, QColor, QBrush, QPen, QLinearGradient
from PIL import Image

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(CURRENT_DIR, "assets")
os.makedirs(ASSETS_DIR, exist_ok=True)
ICO_PATH = os.path.join(ASSETS_DIR, "app.ico")

def create_pixmap(size):
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

    scale = size / 256.0
    
    # 1. 黑曜石胶囊底座 (居中 236x140 胶囊)
    w = 236.0 * scale
    h = 136.0 * scale
    x = (size - w) / 2.0
    y = (size - h) / 2.0
    r = h / 2.0
    rect = QRectF(x, y, w, h)

    # 深邃黑曜石渐变底座
    bg_grad = QLinearGradient(x, y, x, y + h)
    bg_grad.setColorAt(0.0, QColor(18, 18, 22, 255))
    bg_grad.setColorAt(1.0, QColor(8, 8, 10, 255))
    painter.setBrush(QBrush(bg_grad))

    # 菲涅尔高光微发丝外框
    border_grad = QLinearGradient(x, y, x, y + h)
    border_grad.setColorAt(0.0, QColor(255, 255, 255, 120))
    border_grad.setColorAt(0.5, QColor(255, 255, 255, 45))
    border_grad.setColorAt(1.0, QColor(255, 255, 255, 15))
    painter.setPen(QPen(QBrush(border_grad), max(1.0, 3.2 * scale)))
    painter.drawRoundedRect(rect, r, r)

    # 2. 左侧状态冷光翡翠绿宝石指示灯
    core_cx = x + 48.0 * scale
    core_cy = y + h / 2.0
    core_r = 16.0 * scale

    # 外圈暗环微光
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(QColor(16, 185, 129, 45)))
    painter.drawEllipse(QPointF(core_cx, core_cy), core_r * 1.5, core_r * 1.5)

    # 晶体实体核
    painter.setBrush(QBrush(QColor(16, 185, 129, 245)))
    painter.drawEllipse(QPointF(core_cx, core_cy), core_r, core_r)

    # 晶体中心极细高光点
    painter.setBrush(QBrush(QColor(255, 255, 255, 210)))
    painter.drawEllipse(QPointF(core_cx - 3.0 * scale, core_cy - 3.0 * scale), 4.0 * scale, 4.0 * scale)

    # 3. 右侧 Token 环形进度圈 (72% 翡翠绿转金橙)
    ring_cx = x + w - 52.0 * scale
    ring_cy = core_cy
    ring_r = 28.0 * scale
    ring_rect = QRectF(ring_cx - ring_r, ring_cy - ring_r, ring_r * 2.0, ring_r * 2.0)

    # 凹槽暗轨
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.setPen(QPen(QColor(255, 255, 255, 35), max(1.5, 6.0 * scale)))
    painter.drawEllipse(QPointF(ring_cx, ring_cy), ring_r, ring_r)

    # 活跃流光弧度
    prog_pen = QPen(QColor(56, 189, 248, 240), max(1.5, 6.0 * scale), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
    painter.setPen(prog_pen)
    painter.drawArc(ring_rect, 90 * 16, int(-260 * 16))

    painter.end()
    return pix

def main():
    app = QApplication(sys.argv)
    sizes = [16, 32, 48, 64, 128, 256]
    images = []

    for s in sizes:
        pix = create_pixmap(s)
        temp_png = os.path.join(ASSETS_DIR, f"icon_{s}.png")
        pix.save(temp_png, "PNG")
        im = Image.open(temp_png)
        images.append(im)

    # 合并为包含全尺寸的 Windows .ico
    images[-1].save(ICO_PATH, format="ICO", sizes=[(s, s) for s in sizes], append_images=images[:-1])
    print(f"Successfully generated {ICO_PATH} with sizes: {sizes}")

    # 清理临时 png
    for s in sizes:
        p = os.path.join(ASSETS_DIR, f"icon_{s}.png")
        if os.path.exists(p):
            os.remove(p)

if __name__ == "__main__":
    main()
