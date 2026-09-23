#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Antigravity Dynamic Island (苹果灵动岛纯黑悬浮窗) - 沉稳无抖动 + 错位落体弹跳与悬浮小字提示版
1. [彻底消除岛体抖动] 右键点击时灵动岛主屏保持绝对沉稳（零位移零形变），消灭抖动。
2. [落体微弹跳错位动效] 85ms 黄金节律差 + Y 轴下落物理弹簧（Spring Drop & Bounce），肉眼清晰可见 1->2->3 依次跳出，3->2->1 逆序收回。
3. [悬浮小字智能提示] 鼠标悬停在微圆上时，下方即刻以流体透明度浮现高精细小字徽章（“立即刷新数据”、“重置顶部居中”、“退出灵动岛”），移开即隐。
4. [移出灵动岛智能收回] 鼠标移出灵动岛与药丸栏整体热区时，自动触发逆序收回。
5. [100% 纯矢量微线条] QPainterPath 手绘 1.2px 极细线条（0 廉价 Emoji）。
6. [满血 144Hz 弹簧引擎] 7ms 高精度时钟，静止待机 0.0% CPU 极低功耗。
"""

import os
import sys
import json
import time
import math
import ctypes
import ctypes.wintypes

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(CURRENT_DIR)
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

# 确保在 pythonw 下 stdout/stderr 安全重定向
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.path.join(CURRENT_DIR, "capsule_runtime.log"), "a", encoding="utf-8")

import winreg

from PyQt6.QtWidgets import (
    QApplication, QWidget, QSystemTrayIcon, QMenu
)
from PyQt6.QtCore import (
    Qt, QRect, QRectF, QPoint, QPointF,
    QTimer, QThread, pyqtSignal, QEvent, QUrl
)
from PyQt6.QtGui import (
    QPainter, QPainterPath, QColor, QFont, QFontMetrics,
    QPen, QBrush, QRegion, QCursor, QPixmap, QLinearGradient,
    QIcon, QAction
)
from PyQt6.QtWebSockets import QWebSocket
from PyQt6.QtNetwork import QLocalServer, QLocalSocket
import urllib.request

from brain_monitor import get_context_metrics, TOTAL_CAPACITY
from process_daemon import (
    is_antigravity_running,
    is_antigravity_foreground,
    bring_antigravity_to_foreground,
    get_antigravity_window_rect
)

CONFIG_FILE = os.path.join(CURRENT_DIR, "config.json")
WINDOW_TITLE = "AntigravityDynamicIsland"

AUTOSTART_REG_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
AUTOSTART_APP_NAME = "AntigravityIsland"


def is_autostart_enabled():
    """读取注册表当前用户启动项，检测是否已开启开机自启"""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, AUTOSTART_REG_KEY, 0, winreg.KEY_READ) as key:
            val, _ = winreg.QueryValueEx(key, AUTOSTART_APP_NAME)
            return bool(val)
    except Exception:
        return False


def set_autostart_enabled(enable: bool):
    """设置或移除注册表开机静默自启项"""
    vbs_path = os.path.join(CURRENT_DIR, "run_silent.vbs")
    cmd = f'wscript.exe "{vbs_path}"'
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, AUTOSTART_REG_KEY, 0, winreg.KEY_SET_VALUE) as key:
            if enable:
                winreg.SetValueEx(key, AUTOSTART_APP_NAME, 0, winreg.REG_SZ, cmd)
            else:
                try:
                    winreg.DeleteValue(key, AUTOSTART_APP_NAME)
                except FileNotFoundError:
                    pass
        return True
    except Exception:
        return False


def generate_tray_icon(is_busy=False, percent=0.0, pending_act=None):
    """
    手绘 32x32 高清矢量系统托盘图标：
    - 黑曜石胶囊底座 + 微光边框
    - 左侧状态指示灯 (待机绿 / 忙碌蓝 / 阻断待办橙或蓝)
    - 右侧根据 Token 百分比动态绘制的环形进度圈
    """
    pix = QPixmap(32, 32)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    # 1. 胶囊底座 (30x18 居中圆角胶囊)
    rect = QRectF(1.0, 7.0, 30.0, 18.0)
    painter.setBrush(QBrush(QColor(16, 16, 20, 240)))
    painter.setPen(QPen(QColor(255, 255, 255, 80), 1.0))
    painter.drawRoundedRect(rect, 9.0, 9.0)

    # 2. 状态核心指示灯
    if pending_act == "ask_question":
        core_color = QColor(245, 158, 11)   # 琥珀橙
    elif pending_act == "plan_approval":
        core_color = QColor(59, 130, 246)   # 宝石蓝
    elif is_busy:
        core_color = QColor(56, 189, 248)   # 天空蓝
    else:
        core_color = QColor(16, 185, 129)   # 翡翠绿

    # 左侧状态晶核 (半径 2.6px)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(core_color))
    painter.drawEllipse(QPointF(9.5, 16.0), 2.6, 2.6)

    # 3. 右侧环形进度圈
    ring_cx = 22.0
    ring_cy = 16.0
    ring_r = 4.6
    ring_rect = QRectF(ring_cx - ring_r, ring_cy - ring_r, ring_r * 2.0, ring_r * 2.0)

    # 暗轨底环
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.setPen(QPen(QColor(255, 255, 255, 45), 1.4))
    painter.drawEllipse(QPointF(ring_cx, ring_cy), ring_r, ring_r)

    # 前景进度弧 (顺时针展开)
    if percent > 0.5:
        if percent < 60.0:
            arc_c = QColor(16, 185, 129)
        elif percent < 85.0:
            arc_c = QColor(245, 158, 11)
        else:
            arc_c = QColor(239, 68, 68)
        prog_pen = QPen(arc_c, 1.4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(prog_pen)
        span_angle = int(-min(100.0, max(0.0, percent)) / 100.0 * 360.0 * 16)
        painter.drawArc(ring_rect, 90 * 16, span_angle)

    painter.end()
    return QIcon(pix)


def send_decision_via_cdp(action_type, choice=""):
    """
    通过 Chrome DevTools Protocol 尝试在当前活动页面中执行自动化点击/答题/放行
    完全后台静默执行，无需切屏打扰用户
    """
    port_file = os.path.expanduser(r"~\AppData\Roaming\Antigravity\DevToolsActivePort")
    if not os.path.exists(port_file):
        return
    try:
        with open(port_file, "r", encoding="utf-8") as f:
            port = f.readline().strip()
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/json", timeout=0.25) as resp:
            targets = json.loads(resp.read().decode("utf-8", errors="ignore"))
        if not targets:
            return
        page_targets = [t for t in targets if t.get("type") == "page" and t.get("webSocketDebuggerUrl")]
        if not page_targets:
            page_targets = [t for t in targets if t.get("webSocketDebuggerUrl")]
        if not page_targets:
            return

        safe_choice = json.dumps(choice, ensure_ascii=False)
        safe_act = json.dumps(action_type, ensure_ascii=False)
        js_code = f"""
        (() => {{
            const choice = {safe_choice};
            const actType = {safe_act};

            function triggerClick(el) {{
                if (!el) return;
                try {{ el.scrollIntoView({{ behavior: 'instant', block: 'center' }}); }} catch(e) {{}}
                const opts = {{ bubbles: true, cancelable: true, view: window }};
                el.dispatchEvent(new MouseEvent('mousedown', opts));
                el.dispatchEvent(new MouseEvent('mouseup', opts));
                el.click();
            }}

            const norm = (s) => (s || '').replace(/\\s+/g, ' ').trim();

            // 1. 如果是提问选项：精准定位叶子节点并向上寻找点击容器
            if (choice) {{
                const cleanChoice = choice.replace(/^\\(Recommended\\)\\s*/i, '').trim();
                const targetText = norm(cleanChoice);
                if (targetText) {{
                    // 找出所有可见且包含目标文字的元素
                    const matchingElements = Array.from(document.querySelectorAll('*')).filter(el => {{
                        return el.offsetParent !== null && norm(el.innerText).includes(targetText);
                    }});

                    // 筛选出最深层的叶子节点（即子元素都不再包含该文字，彻底杜绝误命中祖先容器）
                    const leafNodes = matchingElements.filter(el => {{
                        return !Array.from(el.children).some(child => child.innerText && norm(child.innerText).includes(targetText));
                    }});

                    if (leafNodes.length > 0) {{
                        const leaf = leafNodes[0];
                        // 向上寻找最近的可点击容器 (label, button, role=radio, role=checkbox 等)
                        const clickable = leaf.closest('button, label, [role="radio"], [role="checkbox"], [role="button"], [class*="option"], [class*="choice"], [class*="item"]') || leaf;
                        triggerClick(clickable);

                        // 如果内部有 radio 或 checkbox input，确保状态同步更新
                        const input = clickable.querySelector('input') || clickable.parentElement?.querySelector('input');
                        if (input && !input.checked) {{
                            input.checked = true;
                            input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                            input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        }}

                        // 延迟 180ms 自动触发 Submit / 提交
                        setTimeout(() => {{
                            const sub = Array.from(document.querySelectorAll('button')).find(b => {{
                                const t = norm(b.innerText);
                                return (t === 'Submit' || t === '提交' || t.includes('提交')) && b.offsetParent !== null;
                            }});
                            if (sub) triggerClick(sub);
                        }}, 180);
                        return true;
                    }}
                }}
            }}

            // 2. 如果是方案审批：寻找 Proceed / 批准 / 开始 按钮
            if (actType === 'plan_approval' || !choice) {{
                const proceedBtn = Array.from(document.querySelectorAll('button')).find(b => {{
                    const t = norm(b.innerText);
                    return (t === 'Proceed' || t === '批准' || t.includes('开始') || t.includes('Proceed')) && b.offsetParent !== null;
                }});
                if (proceedBtn) {{
                    triggerClick(proceedBtn);
                    return true;
                }}
            }}

            // 3. 兜底在输入框注入并回车发送
            const ed = document.querySelector('[contenteditable="true"], textarea');
            if (ed) {{
                ed.focus();
                document.execCommand('insertText', false, choice || '开始');
                setTimeout(() => {{
                    const enterEvent = new KeyboardEvent('keydown', {{
                        key: 'Enter',
                        code: 'Enter',
                        keyCode: 13,
                        which: 13,
                        bubbles: true,
                        cancelable: true
                    }});
                    ed.dispatchEvent(enterEvent);
                }}, 100);
                return true;
            }}
            return false;
        }})()
        """

        if not hasattr(send_decision_via_cdp, "_sockets"):
            send_decision_via_cdp._sockets = []

        for target in page_targets:
            ws_url = target.get("webSocketDebuggerUrl")
            if not ws_url:
                continue
            ws = QWebSocket()
            def make_on_open(sock, script):
                def on_open():
                    req = {
                        "id": 888,
                        "method": "Runtime.evaluate",
                        "params": {
                            "expression": script,
                            "returnByValue": True
                        }
                    }
                    sock.sendTextMessage(json.dumps(req))
                    QTimer.singleShot(600, sock.close)
                return on_open

            ws.connected.connect(make_on_open(ws, js_code))
            ws.open(QUrl(ws_url))
            send_decision_via_cdp._sockets.append(ws)

        if len(send_decision_via_cdp._sockets) > 12:
            send_decision_via_cdp._sockets = send_decision_via_cdp._sockets[-6:]

    except Exception:
        pass

# 虚拟画布尺寸（固定大小，杜绝频繁 Resize 导致的掉帧）
CANVAS_W = 340
CANVAS_H = 156
PADDING_TOP = 8

# 灵动岛物理尺寸
COMPACT_W = 182
COMPACT_H = 30
EXPANDED_W = 320
EXPANDED_H = 138
NOTIFY_W = 236

# 横向迷你药丸栏尺寸 (支持 4 颗精致微按钮)
PILL_W = 174
PILL_H = 28


def load_config():
    default_cfg = {
        "x": None,
        "y": 12,
        "on_top": True,
        "auto_hide": True,
        "auto_tuck": True,
        "tuck_delay_ms": 4000
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                default_cfg.update(saved)
        except Exception:
            pass
    return default_cfg


def save_config(cfg):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


IPC_PIPE_NAME = "AntigravityIsland_IPC_Server_Pipe"
MUTEX_NAME = "Local\\AntigravityIsland_SingleInstance_Mutex"
_GLOBAL_MUTEX_HANDLE = None


def check_single_instance_or_wake():
    """
    工业级单实例互斥与进程间唤醒：
    1. 使用 Windows 内核命名互斥体 (CreateMutexW)，无论主岛处于显示、隐藏、极简还是托盘，100% 杜绝多开；
    2. 若检测到实例已存在，通过 QLocalSocket 向已运行实例发送 WAKE_UP 指令，将其从后台/托盘唤醒至屏幕前台；
    3. 进程异常退出时，Windows 内核自动释放 Mutex，绝不残留死锁。
    """
    global _GLOBAL_MUTEX_HANDLE
    ERROR_ALREADY_EXISTS = 183
    mutex = ctypes.windll.kernel32.CreateMutexW(None, False, MUTEX_NAME)
    last_err = ctypes.windll.kernel32.GetLastError()

    if last_err == ERROR_ALREADY_EXISTS:
        if mutex:
            ctypes.windll.kernel32.CloseHandle(mutex)
        # 向已运行的旧实例发送唤醒指令
        sent_wakeup = False
        try:
            sock = QLocalSocket()
            sock.connectToServer(IPC_PIPE_NAME)
            if sock.waitForConnected(600):
                sock.write(b"WAKE_UP\n")
                sock.waitForBytesWritten(400)
                sock.disconnectFromServer()
                sent_wakeup = True
        except Exception:
            pass

        # 若旧实例连不上（说明处于僵死/无响应状态），自动清理残留进程并接管启动，确保 100% 能双击拉起！
        if not sent_wakeup:
            try:
                import subprocess
                subprocess.run(
                    ["powershell", "-NoProfile", "-Command",
                     "Get-Process python*, pythonw* -ErrorAction SilentlyContinue | "
                     f"Where-Object Id -ne {os.getpid()} | "
                     "ForEach-Object { try { $c = (Get-CimInstance Win32_Process -Filter ('ProcessId=' + $_.Id)).CommandLine; if ($c -like '*capsule_gui.py*') { Stop-Process -Id $_.Id -Force } } catch {} }"],
                    capture_output=True, timeout=2.0
                )
                time.sleep(0.3)
                m2 = ctypes.windll.kernel32.CreateMutexW(None, False, MUTEX_NAME)
                _GLOBAL_MUTEX_HANDLE = m2
                return True
            except Exception:
                pass

        return False

    _GLOBAL_MUTEX_HANDLE = mutex
    return True


# =================================================================
# 横向迷你药丸栏 (MiniPillBar) - 落体弹跳 + 悬浮小字提示
# =================================================================
class MiniPillBar(QWidget):
    """
    横向迷你微药丸栏：
    - 尺寸仅 136x28px 全圆角胶囊；
    - 弹出时：3 个微圆选项依次 1->2->3 错位“落体弹跳（Spring Drop & Bounce）”跳出，间隔 85ms 节奏鲜明；
    - 消失时：3->2->1 逆序阶梯吸回；
    - 鼠标悬停在微圆上时，下方即刻以流体透明度浮现小字提示徽章；
    - 鼠标移出灵动岛与药丸栏范围自动收回。
    """
    refresh_requested = pyqtSignal()
    reset_requested = pyqtSignal()
    minimal_mode_requested = pyqtSignal()
    quit_requested = pyqtSignal()
    dismissed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.SubWindow
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setMouseTracking(True)

        self.PADDING = 8
        # 为下方悬浮小字提示徽章预留 24px 高度
        self.TIP_H = 24
        self.WIN_W = PILL_W + self.PADDING * 2
        self.WIN_H = PILL_H + self.TIP_H + self.PADDING * 2
        self.resize(self.WIN_W, self.WIN_H)

        # 4 个按钮中心坐标 (严丝合缝对称布局，间距 40px)
        cy = self.PADDING + PILL_H / 2.0
        start_x = self.PADDING + 27.0
        self.btn_centers = [
            (start_x, cy),
            (start_x + 40.0, cy),
            (start_x + 80.0, cy),
            (start_x + 120.0, cy)
        ]
        self.hovered_idx = -1
        self.tip_alpha = 0.0

        # 提示文本定义
        self.tip_labels = ["立即刷新数据", "重置顶部居中", "切换最小微圆", "退出灵动岛"]

        # 字体 (优先微软雅黑，字重 Medium，小字极清晰)
        self.f_tip = QFont("Microsoft YaHei", 8)
        self.f_tip.setWeight(QFont.Weight.Medium)

        # -----------------------------
        # 阶梯落体弹跳动力学状态 (Staggered Drop-Bounce States: 4 按钮)
        # -----------------------------
        self.scales = [0.2, 0.2, 0.2, 0.2]
        self.alphas = [0.0, 0.0, 0.0, 0.0]
        self.dys = [-16.0, -16.0, -16.0, -16.0]
        self.vel_ys = [0.0, 0.0, 0.0, 0.0]
        self.vel_scales = [0.0, 0.0, 0.0, 0.0]

        self.container_scale = 0.88
        self.container_alpha = 0.0

        self.is_closing = False
        self.anim_start_time = 0.0
        self.last_tick_time = 0.0

        self.anim_timer = QTimer(self)
        self.anim_timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.anim_timer.setInterval(7)
        self.anim_timer.timeout.connect(self.on_anim_tick)

    def popup(self, center_x, top_y):
        """在灵动岛正下方弹出，启动 1->2->3 鲜明错位落体弹跳动效"""
        self.is_closing = False
        target_scr = QApplication.screenAt(QPoint(int(center_x), int(top_y)))
        if not target_scr:
            target_scr = QApplication.primaryScreen()
        avail = target_scr.availableGeometry()

        win_x = int(center_x - self.WIN_W / 2.0)
        win_y = int(top_y - self.PADDING)

        min_x = avail.left() + 10
        max_x = avail.left() + avail.width() - self.WIN_W - 10
        min_y = avail.top() + 10
        max_y = avail.top() + avail.height() - self.WIN_H - 10

        win_x = max(min_x, min(win_x, max_x))
        win_y = max(min_y, min(win_y, max_y))
        self.move(win_x, win_y)

        # 初始化动力学初态 (初始向上偏移 16px，缩放为 0.2)
        self.container_scale = 0.88
        self.container_alpha = 0.0
        self.scales = [0.2, 0.2, 0.2, 0.2]
        self.alphas = [0.0, 0.0, 0.0, 0.0]
        self.dys = [-16.0, -16.0, -16.0, -16.0]
        self.vel_ys = [0.0, 0.0, 0.0, 0.0]
        self.vel_scales = [0.0, 0.0, 0.0, 0.0]

        self.anim_start_time = time.perf_counter()
        self.last_tick_time = self.anim_start_time

        # 瞬时检测光标当前是否已落在某个按钮上
        global_pos = QCursor.pos()
        local_x = global_pos.x() - win_x
        local_y = global_pos.y() - win_y
        self.hovered_idx = self.get_btn_at(local_x, local_y)
        self.tip_alpha = 1.0 if self.hovered_idx != -1 else 0.0

        self.show()
        self.raise_()

        if not self.anim_timer.isActive():
            self.anim_timer.start(7)

    def dismiss(self):
        """触发 4->3->2->1 逆序阶梯吸回消失"""
        if self.is_closing or not self.isVisible():
            return
        self.is_closing = True
        self.tip_alpha = 0.0
        self.anim_start_time = time.perf_counter()
        self.last_tick_time = self.anim_start_time
        if not self.anim_timer.isActive():
            self.anim_timer.start(7)

    def on_anim_tick(self):
        now = time.perf_counter()
        dt = min(0.025, max(0.002, now - self.last_tick_time))
        self.last_tick_time = now
        elapsed = now - self.anim_start_time

        # 悬浮小字提示平滑淡入淡出插值
        if self.hovered_idx != -1 and not self.is_closing:
            self.tip_alpha = min(1.0, self.tip_alpha + dt * 12.0)
        else:
            self.tip_alpha = max(0.0, self.tip_alpha - dt * 14.0)

        if not self.is_closing:
            # =====================================================
            # 弹出阶段：1 -> 2 -> 3 -> 4 错位落体微弹跳 (55ms 黄金节拍)
            # =====================================================
            # 1. 容器平滑展开
            self.container_scale = min(1.0, self.container_scale + dt * 6.5)
            self.container_alpha = min(1.0, self.container_alpha + dt * 9.0)

            # 2. 4 个微圆落体弹簧参数 (omega=25.1, damping=0.58 呈现饱满触觉超调回弹)
            delays = [0.0, 0.055, 0.110, 0.165]
            omega0 = 6.283185 / 0.25
            k = omega0 * omega0
            c = 2.0 * 0.58 * omega0

            all_settled = (self.container_scale >= 0.99 and self.container_alpha >= 0.99)

            for i in range(4):
                if elapsed >= delays[i]:
                    # Y 轴落体弹簧
                    fy = -k * self.dys[i] - c * self.vel_ys[i]
                    self.vel_ys[i] += fy * dt
                    self.dys[i] += self.vel_ys[i] * dt

                    # 缩放弹簧
                    fs = -k * (self.scales[i] - 1.0) - c * self.vel_scales[i]
                    self.vel_scales[i] += fs * dt
                    self.scales[i] += self.vel_scales[i] * dt

                    # 透明度
                    self.alphas[i] = min(1.0, self.alphas[i] + dt * 12.0)

                    if abs(self.dys[i]) > 0.15 or abs(self.vel_ys[i]) > 0.4 or self.alphas[i] < 0.99:
                        all_settled = False
                else:
                    all_settled = False

            if all_settled:
                for i in range(4):
                    self.scales[i] = 1.0
                    self.alphas[i] = 1.0
                    self.dys[i] = 0.0
                    self.vel_ys[i] = 0.0
                    self.vel_scales[i] = 0.0
                self.container_scale = 1.0
                self.container_alpha = 1.0
                is_tip_animating = (self.hovered_idx != -1 and self.tip_alpha < 0.99) or (self.hovered_idx == -1 and self.tip_alpha > 0.01)
                if not is_tip_animating:
                    self.anim_timer.stop()

        else:
            # =====================================================
            # 消失阶段：4 -> 3 -> 2 -> 1 逆序阶梯吸回收缩 (30ms 紧凑节拍)
            # =====================================================
            delays = [0.090, 0.060, 0.030, 0.0]
            for i in range(4):
                if elapsed >= delays[i]:
                    self.dys[i] = max(-16.0, self.dys[i] - dt * 65.0)
                    self.scales[i] = max(0.0, self.scales[i] - dt * 14.0)
                    self.alphas[i] = max(0.0, self.alphas[i] - dt * 14.0)

            # 全部吸回后，外壳迅速淡出闭合
            if elapsed >= 0.090:
                self.container_scale = max(0.88, self.container_scale - dt * 4.0)
                self.container_alpha = max(0.0, self.container_alpha - dt * 12.0)

            if self.container_alpha <= 0.02 and all(a <= 0.02 for a in self.alphas):
                self.anim_timer.stop()
                self.hide()
                self.is_closing = False
                self.dismissed.emit()
                return

        self.update()

    def handle_pointer_move(self, x, y):
        old_h = self.hovered_idx
        self.hovered_idx = self.get_btn_at(x, y)
        if self.hovered_idx != old_h:
            if not self.anim_timer.isActive():
                self.anim_timer.start(7)
            self.update()

    def handle_pointer_leave(self):
        if self.hovered_idx != -1:
            self.hovered_idx = -1
            if not self.anim_timer.isActive():
                self.anim_timer.start(7)
            self.update()

    def mouseMoveEvent(self, event):
        pt = event.position()
        self.handle_pointer_move(pt.x(), pt.y())
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        self.handle_pointer_leave()
        super().leaveEvent(event)

    def event(self, ev):
        t = ev.type()
        if t in (QEvent.Type.HoverMove, QEvent.Type.MouseMove):
            pos = ev.position() if hasattr(ev, "position") else ev.pos()
            self.handle_pointer_move(pos.x(), pos.y())
        elif t in (QEvent.Type.HoverLeave, QEvent.Type.Leave):
            self.handle_pointer_leave()
        return super().event(ev)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            idx = self.get_btn_at(event.position().x(), event.position().y())
            if idx == 0:
                self.refresh_requested.emit()
            elif idx == 1:
                self.reset_requested.emit()
            elif idx == 2:
                self.minimal_mode_requested.emit()
            elif idx == 3:
                self.quit_requested.emit()
            self.dismiss()
            event.accept()
            return
        elif event.button() == Qt.MouseButton.RightButton:
            self.dismiss()
            event.accept()
            return
        super().mousePressEvent(event)

    def get_btn_at(self, x, y):
        # 命中检测：每个微按钮 36x24，容差充裕
        for i, (cx, cy) in enumerate(self.btn_centers):
            rect = QRectF(cx - 18.0, cy - 12.0, 36.0, 24.0)
            if rect.contains(x, y):
                return i
        return -1

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        win_cx = self.WIN_W / 2.0
        pill_cy = self.PADDING + PILL_H / 2.0

        # =========================================================
        # 1. 绘制横向迷你纯胶囊外壳
        # =========================================================
        painter.save()
        painter.translate(win_cx, pill_cy)
        painter.scale(self.container_scale, self.container_scale)
        painter.translate(-win_cx, -pill_cy)
        painter.setOpacity(self.container_alpha)

        pill_rect = QRectF(self.PADDING, self.PADDING, PILL_W, PILL_H)
        # 深炭黑磨砂底 + 精致高光微发丝边框
        painter.setBrush(QBrush(QColor(10, 10, 12, 248)))
        painter.setPen(QPen(QColor(255, 255, 255, 30), 1.0))
        painter.drawRoundedRect(pill_rect, 14.0, 14.0)
        painter.restore()

        # =========================================================
        # 2. 依次绘制 4 个阶梯落体弹跳微圆
        # =========================================================
        for i in range(4):
            sc = self.scales[i]
            al = self.alphas[i]
            dy = self.dys[i]
            if al <= 0.01 or sc <= 0.01:
                continue

            cx, cy = self.btn_centers[i]
            is_hover = (self.hovered_idx == i)
            is_danger = (i == 3)

            painter.save()
            # 复合变换：以中心为锚点缩放 + Y轴下落弹跳 + 悬停1.06x微浮起
            scale_hover = 1.06 if is_hover else 1.0
            painter.translate(cx, cy + dy)
            painter.scale(sc * scale_hover, sc * scale_hover)
            painter.translate(-cx, -cy)
            painter.setOpacity(al * self.container_alpha)

            btn_rect = QRectF(cx - 16.0, cy - 10.0, 32.0, 20.0)

            # 统一苹果灵动极简单色白透磨砂底条与发丝微高光
            if is_hover:
                painter.setBrush(QBrush(QColor(255, 255, 255, 28)))
                painter.setPen(QPen(QColor(255, 255, 255, 52), 0.8))
            else:
                painter.setBrush(QBrush(QColor(255, 255, 255, 8)))
                painter.setPen(QPen(QColor(255, 255, 255, 14), 0.6))

            painter.drawRoundedRect(btn_rect, 10.0, 10.0)

            # 纯矢量微图标 (1.2px 极细线条，0 Emoji)
            if i == 0:
                self.draw_vector_refresh(painter, cx, cy, is_hover)
            elif i == 1:
                self.draw_vector_crosshair(painter, cx, cy, is_hover)
            elif i == 2:
                self.draw_vector_minimal(painter, cx, cy, is_hover)
            elif i == 3:
                self.draw_vector_close(painter, cx, cy, is_hover)

            painter.restore()

        # =========================================================
        # 3. 悬浮小字智能提示徽章 (Hover Tooltip Badge: 统一深邃炭黑底)
        # =========================================================
        if self.tip_alpha > 0.01 and self.hovered_idx != -1 and not self.is_closing:
            idx = self.hovered_idx
            tip_str = self.tip_labels[idx]

            painter.save()
            painter.setOpacity(self.tip_alpha * self.container_alpha)

            tip_y = self.PADDING + PILL_H + 4.0
            badge_w = 78.0 if idx == 3 else 98.0
            badge_h = 19.0
            badge_x = win_cx - badge_w / 2.0
            badge_rect = QRectF(badge_x, tip_y, badge_w, badge_h)

            # 与主岛同款的深邃纯黑磨砂底 + 精致微发丝边框
            painter.setBrush(QBrush(QColor(9, 9, 11, 248)))
            painter.setPen(QPen(QColor(255, 255, 255, 38), 0.8))
            painter.drawRoundedRect(badge_rect, 5.0, 5.0)

            # 提示文字 (前三项统一高级米白，退出项柔和珊瑚红)
            painter.setFont(self.f_tip)
            if idx == 3:
                text_color = QColor(248, 113, 113)  # 柔和珊瑚红（警示）
            else:
                text_color = QColor(244, 244, 245)  # 高级温润米白

            painter.setPen(text_color)
            painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, tip_str)
            painter.restore()

    def draw_vector_minimal(self, painter, cx, cy, hovered):
        """100% 纯手绘矢量极简微圆环图标 (1.2px 极细线条)"""
        color = QColor(255, 255, 255) if hovered else QColor(161, 161, 170)
        pen = QPen(color, 1.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(cx, cy), 4.6, 4.6)
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(cx, cy), 1.6, 1.6)

    # -------------------------------------------------------------
    # 纯矢量微线条 (QPainterPath 1.2px，0 廉价 Emoji)
    # -------------------------------------------------------------
    def draw_vector_refresh(self, painter, cx, cy, hovered):
        color = QColor(255, 255, 255) if hovered else QColor(161, 161, 170)
        pen = QPen(color, 1.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        arc_rect = QRectF(cx - 4.2, cy - 4.2, 8.4, 8.4)
        painter.drawArc(arc_rect, 40 * 16, 275 * 16)

        arrow = QPainterPath()
        arrow.moveTo(cx + 4.2, cy - 2.8)
        arrow.lineTo(cx + 4.2, cy + 1.2)
        arrow.lineTo(cx + 0.8, cy + 0.8)
        painter.drawPath(arrow)

    def draw_vector_crosshair(self, painter, cx, cy, hovered):
        color = QColor(255, 255, 255) if hovered else QColor(161, 161, 170)
        pen = QPen(color, 1.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        painter.drawEllipse(QPointF(cx, cy), 3.8, 3.8)
        painter.drawLine(QPointF(cx - 5.8, cy), QPointF(cx - 3.8, cy))
        painter.drawLine(QPointF(cx + 3.8, cy), QPointF(cx + 5.8, cy))
        painter.drawLine(QPointF(cx, cy - 5.8), QPointF(cx, cy - 3.8))
        painter.drawLine(QPointF(cx, cy + 3.8), QPointF(cx, cy + 5.8))

    def draw_vector_close(self, painter, cx, cy, hovered):
        color = QColor(248, 113, 113) if hovered else QColor(161, 161, 170)
        pen = QPen(color, 1.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        d = 3.0
        painter.drawLine(QPointF(cx - d, cy - d), QPointF(cx + d, cy + d))
        painter.drawLine(QPointF(cx - d, cy + d), QPointF(cx + d, cy - d))


# =================================================================
# 水滴副岛二级微悬浮操作卡片 (ActionFlyoutCard)
# =================================================================
# =================================================================
# 水滴副岛二级微悬浮操作卡片 (ActionFlyoutCard)
# 一体化灵动落体大卡片：一步到位展开、选项高度全自动动态自适应、纯正苹果黑调质感
# =================================================================
class ActionFlyoutCard(QWidget):
    action_submitted = pyqtSignal(str, str)  # (action_type, choice)
    closing_started = pyqtSignal()
    dismissed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.SubWindow
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setMouseTracking(True)

        self.CARD_W = 320.0  # 拓宽至 320px，使 70+ 字长选项舒展为 3~4 行，阅读呼吸感极佳
        self.PADDING = 8.0
        self.SIDE_PAD = 14.0
        self.CONTENT_W = self.CARD_W - self.SIDE_PAD * 2  # 292.0px

        self.metrics_data = {}
        self.action_type = "plan_approval"

        # 字体规范 (纯正原生苹果排版风格)
        self.f_tit = QFont("Segoe UI", 9)
        self.f_tit.setBold(True)
        self.f_sub = QFont("Microsoft YaHei", 8)
        self.f_sub.setWeight(QFont.Weight.Medium)
        self.f_chip = QFont("Segoe UI", 8)
        self.f_chip.setBold(True)
        self.f_step = QFont("Microsoft YaHei", 8)
        self.f_btn = QFont("Microsoft YaHei", 8)
        self.f_btn.setBold(True)
        self.f_opt = QFont("Microsoft YaHei", 8)

        # 144Hz 苹果原生二阶流体动力学解算器 (高敏捷丝滑展开)
        self.spring_progress = 0.0
        self.spring_vel = 0.0
        self.container_alpha = 0.0
        
        # 进场弹簧物理参数：omega=24.0 (约 150ms 敏捷丝滑舒展周期), zeta=0.73 (克制果冻微回弹 1.9%)
        omega = 24.0
        zeta = 0.73
        self.spring_k = omega * omega
        self.spring_c = 2.0 * zeta * omega

        # 退场时间轴绝对控制状态 (120ms 敏捷磁吸收纳)
        self.dismiss_start_time = 0.0
        self.dismiss_duration = 0.12
        self.dismiss_start_p = 1.0
        self.dismiss_start_alpha = 1.0

        # 卡片自适应高度与 GPU 离屏高清显存纹理缓存 (单帧贴图仅需 0.06ms)
        self.current_card_h = 120.0
        self.cached_pixmap = None

        # 按键与选项悬停交互
        self.hovered_btn = -1  # 0: 立即批准, 1: 查阅/输入, 10+: 选项索引
        self.selected_opt_idx = 0

        self.is_closing = False
        self.fast_closing = False
        self.anim_start_time = 0.0
        self.last_tick_time = 0.0

        self.anim_timer = QTimer(self)
        self.anim_timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.anim_timer.setInterval(7)
        self.anim_timer.timeout.connect(self.on_anim_tick)

        # 移出自动收起定时器 (180ms 灵敏响应)
        self.auto_dismiss_timer = QTimer(self)
        self.auto_dismiss_timer.setSingleShot(True)
        self.auto_dismiss_timer.setInterval(180)
        self.auto_dismiss_timer.timeout.connect(self.dismiss)

    def draw_vector_file_icon(self, painter, cx, cy, color, alpha):
        """100% 纯手绘 1.0px 矢量极细折角文件微图标 (彻底杜绝廉价 Emoji)"""
        pen = QPen(QColor(color.red(), color.green(), color.blue(), int(alpha * 220)), 1.0)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        w, h = 9.0, 11.0
        x = cx - w / 2.0
        y = cy - h / 2.0
        path = QPainterPath()
        path.moveTo(x, y)
        path.lineTo(x + w - 3.0, y)
        path.lineTo(x + w, y + 3.0)
        path.lineTo(x + w, y + h)
        path.lineTo(x, y + h)
        path.closeSubpath()
        painter.drawPath(path)
        painter.drawLine(QPointF(x + w - 3.0, y), QPointF(x + w - 3.0, y + 3.0))
        painter.drawLine(QPointF(x + w - 3.0, y + 3.0), QPointF(x + w, y + 3.0))

    def compute_card_height(self, metrics=None):
        """计算包含所有完整自适应内容的卡片最终物理高度（一步到位，绝无死板抽屉）"""
        if metrics is not None:
            self.metrics_data = metrics or {}
            self.action_type = self.metrics_data.get("pending_action", "plan_approval")
        TOP_PAD = 12.0
        BOT_PAD = 12.0
        w = self.CONTENT_W

        if self.action_type == "plan_approval":
            # 顶部标题(16) + 间距(6) + 描述(18) + 间距(10) + 按钮(24) + 内边距(24)
            base_h = TOP_PAD + 16.0 + 6.0 + 18.0 + 10.0 + 24.0 + BOT_PAD
            files = self.metrics_data.get("pending_files") or []
            steps = self.metrics_data.get("pending_steps") or []
            if files:
                base_h += 24.0  # 芯片微徽章行 18 + 间距 6
            if steps:
                base_h += min(2, len(steps)) * 17.0 + 6.0
            return max(100.0, base_h)
        else:
            raw_options = self.metrics_data.get("pending_options") or ["确认继续", "需要调整方案"]
            options = raw_options[:3]
            full_q = self.metrics_data.get("pending_detail") or "请选择后续方案"

            # 题干长文字真实折行高度
            fm_sub = QFontMetrics(self.f_sub)
            br_q = fm_sub.boundingRect(QRect(0, 0, int(w), 10000), Qt.TextFlag.TextWordWrap, full_q)
            q_h = max(18.0, float(br_q.height() + 4.0))

            # 各选项自适应多行高度 (彻底移除死上限截断，文字有多高就给多高，留足上下各 8px 舒适边距)
            fm_opt = QFontMetrics(self.f_opt)
            total_opts_h = 0.0
            for opt in options:
                is_rec = "(Recommended)" in opt or "(推荐)" in opt
                clean_opt = opt.replace("(Recommended)", "").replace("(推荐)", "").strip()
                avail_w = w - 24.0 - (46.0 if is_rec else 8.0)
                br_opt = fm_opt.boundingRect(QRect(0, 0, int(avail_w), 10000), Qt.TextFlag.TextWordWrap, clean_opt)
                item_h = float(max(34.0, br_opt.height() + 16.0))
                total_opts_h += item_h

            total_opts_h += max(0, len(options) - 1) * 6.0

            # 顶部(16) + 间距(6) + 题干(q_h) + 间距(8) + 选项(total_opts_h) + 间距(8) + 底部链接(16) + 内边距(24)
            return TOP_PAD + 16.0 + 6.0 + q_h + 8.0 + total_opts_h + 8.0 + 16.0 + BOT_PAD

    def get_card_height(self):
        return self.current_card_h

    def bake_cache_pixmap(self):
        """一次性将完整的高清黑曜石底座、发丝微边与全部排版内容烘焙至离屏显存纹理中（支持 High-DPI 视网膜高清）"""
        self.compute_layout()
        w = float(self.CARD_W)
        h = float(self.current_card_h)
        if w <= 0 or h <= 0:
            return

        # 获取当前屏幕真实的设备像素比 (例如 1.25x / 1.5x / 2.0x 视网膜屏)，杜绝位图拉伸模糊！
        dpr = self.devicePixelRatioF() or (self.screen().devicePixelRatio() if self.screen() else 1.0)
        pw = int(math.ceil(w * dpr))
        ph = int(math.ceil(h * dpr))

        pix = QPixmap(pw, ph)
        pix.setDevicePixelRatio(dpr)
        pix.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pix)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        card_rect = QRectF(0, 0, w, h)

        # 1. 纯正黑曜石磨砂底座 + 发丝高光微边
        painter.setPen(QPen(QColor(255, 255, 255, 22), 1.0))
        painter.setBrush(QBrush(QColor(10, 10, 12, 250)))
        painter.drawRoundedRect(card_rect, 14.0, 14.0)

        # 顶部微光发丝反光线
        painter.setPen(QPen(QColor(255, 255, 255, 15), 1.0))
        painter.drawLine(
            QPointF(card_rect.left() + 16.0, card_rect.top() + 1.0),
            QPointF(card_rect.right() - 16.0, card_rect.top() + 1.0)
        )

        # 2. 绘制具体内容 (烘焙时以 100% 满血 alpha 呈现)
        if self.action_type == "plan_approval":
            self.draw_approval_content(painter, card_rect, 1.0)
        else:
            self.draw_question_content(painter, card_rect, 1.0)

        painter.end()
        self.cached_pixmap = pix

    def popup(self, center_x, top_y, metrics):
        self.metrics_data = metrics or {}
        self.action_type = self.metrics_data.get("pending_action", "plan_approval")
        self.is_closing = False
        self.fast_closing = False
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.auto_dismiss_timer.stop()

        # 动态计算最终一步到位高度
        self.current_card_h = self.compute_card_height()

        win_w = int(self.CARD_W + self.PADDING * 2)
        win_h = int(self.current_card_h + self.PADDING * 2)
        self.resize(win_w, win_h)

        target_scr = QApplication.screenAt(QPoint(int(center_x), int(top_y)))
        if not target_scr:
            target_scr = QApplication.primaryScreen()
        avail = target_scr.availableGeometry()

        win_x = int(center_x - win_w / 2.0)
        win_y = int(top_y - self.PADDING)

        min_x = avail.left() + 10
        max_x = avail.left() + avail.width() - win_w - 10
        min_y = avail.top() + 10
        max_y = avail.top() + avail.height() - win_h - 10

        win_x = max(min_x, min(win_x, max_x))
        win_y = max(min_y, min(win_y, max_y))
        self.move(win_x, win_y)

        # 在第 0ms 一次性烘焙离屏纹理，彻底粉碎单帧文本光栅化瓶颈！
        self.hovered_btn = -1
        self.selected_opt_idx = 0
        self.bake_cache_pixmap()

        # 144Hz 顶部锚点流体绽放初始化
        self.spring_progress = 0.0
        self.spring_vel = 0.0
        self.container_alpha = 0.0

        self.anim_start_time = time.perf_counter()
        self.last_tick_time = self.anim_start_time

        self.show()
        self.raise_()
        if not self.anim_timer.isActive():
            self.anim_timer.start(7)

    def dismiss(self, fast=False):
        if self.is_closing or not self.isVisible():
            return
        self.is_closing = True
        self.fast_closing = fast
        self.auto_dismiss_timer.stop()
        self.closing_started.emit()  # 第0毫秒通知主岛协同舒展复原！

        # 退场前将当前卡片视觉状态烘焙至 High-DPI 纹理
        self.bake_cache_pixmap()

        self.dismiss_start_time = time.perf_counter()
        # 退场时长绝对控制：普通移开 120ms，快速提交 90ms（敏捷磁吸吸入副岛）
        self.dismiss_duration = 0.09 if fast else 0.12
        self.dismiss_start_p = max(0.2, self.spring_progress)
        self.dismiss_start_alpha = max(0.2, self.container_alpha)

        if fast:
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.anim_start_time = self.dismiss_start_time
        self.last_tick_time = self.dismiss_start_time
        if not self.anim_timer.isActive():
            self.anim_timer.start(7)

    def on_anim_tick(self):
        now = time.perf_counter()
        dt = min(0.025, max(0.002, now - self.last_tick_time))
        self.last_tick_time = now

        if not self.is_closing:
            # 144Hz 苹果二阶欠阻尼流体弹簧解算器 (omega=24.0, zeta=0.73)
            target = 1.0
            f = -self.spring_k * (self.spring_progress - target) - self.spring_c * self.spring_vel
            self.spring_vel += f * dt
            self.spring_progress += self.spring_vel * dt

            # 透明度前 40ms 柔和升至 1.0 (提速至 25.0)
            self.container_alpha = min(1.0, self.container_alpha + dt * 25.0)

            # 进场平稳就位判定 (约 150~170ms 完成果冻微震并平稳锁定)
            scale_done = (abs(self.spring_progress - 1.0) < 0.010 and abs(self.spring_vel) < 0.30 and (now - self.anim_start_time) > 0.14)
            if scale_done:
                self.spring_progress = 1.0
                self.spring_vel = 0.0
                self.container_alpha = 1.0
                self.anim_timer.stop()
        else:
            # 120ms 时间轴绝对控制：流体向上聚合磁吸扑入副岛底部消融 (easeInCubic 加速吸入)
            elapsed = now - self.dismiss_start_time
            t_norm = min(1.0, max(0.0, elapsed / self.dismiss_duration))
            # easeInCubic 磁吸加速曲线
            ease = t_norm * t_norm * t_norm

            self.spring_progress = self.dismiss_start_p * (1.0 - ease)
            self.container_alpha = self.dismiss_start_alpha * (1.0 - ease)

            if t_norm >= 1.0 or self.container_alpha <= 0.01:
                self.anim_timer.stop()
                self.hide()
                self.is_closing = False
                self.fast_closing = False
                self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
                self.dismissed.emit()
                return

        self.update()

    def paintEvent(self, event):
        if self.container_alpha <= 0.01:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)

        # 稳态就位（展开就绪静止状态）：
        # 彻底跳过位图显存贴图，直接执行 100% 原生矢量绘制与 Windows ClearType 亚像素抗锯齿渲染！
        # 字体发丝级锋芒毕露，绝无任何模糊或色散！
        is_steady = (not self.is_closing and not self.anim_timer.isActive() and abs(self.spring_progress - 1.0) < 0.005)

        if is_steady:
            painter.save()
            painter.translate(self.PADDING, self.PADDING)
            card_rect = QRectF(0, 0, self.CARD_W, self.current_card_h)

            # 1. 纯正黑曜石磨砂底座 + 发丝高光微边
            painter.setPen(QPen(QColor(255, 255, 255, 22), 1.0))
            painter.setBrush(QBrush(QColor(10, 10, 12, 250)))
            painter.drawRoundedRect(card_rect, 14.0, 14.0)

            # 顶部微光发丝反光线
            painter.setPen(QPen(QColor(255, 255, 255, 15), 1.0))
            painter.drawLine(
                QPointF(card_rect.left() + 16.0, card_rect.top() + 1.0),
                QPointF(card_rect.right() - 16.0, card_rect.top() + 1.0)
            )

            # 2. 原生矢量内容输出
            if self.action_type == "plan_approval":
                self.draw_approval_content(painter, card_rect, 1.0)
            else:
                self.draw_question_content(painter, card_rect, 1.0)

            painter.restore()
            return

        # 动画执行期间 (进场约 150ms / 退场约 120ms)：使用 High-DPI 显存贴图 Blit，满血 144Hz 丝滑流体
        if not self.cached_pixmap or self.cached_pixmap.isNull():
            return

        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        alpha = max(0.0, min(1.0, self.container_alpha))

        if not self.is_closing:
            # 进场：从副岛下方以顶部为锚点等比例自然绽放舒展 (scale: 0.88 -> 1.0, dy: -14px -> 0px)
            p = self.spring_progress
            cur_scale = max(0.60, min(1.03, 0.88 + 0.12 * p))
            p_clamped = min(1.0, max(0.0, p))
            cur_dy = -14.0 * (1.0 - p_clamped)
        else:
            # 退场：向上拉丝磁吸扑入副岛底部消融 (120ms 绝对敏捷平滑)
            elapsed = time.perf_counter() - self.dismiss_start_time
            t_norm = min(1.0, max(0.0, elapsed / self.dismiss_duration))
            ease = t_norm * t_norm * t_norm
            cur_scale = max(0.40, self.dismiss_start_p * (1.0 - 0.15 * ease))
            cur_dy = -14.0 * ease

        # 核心：以卡片顶部中心为物理变换锚点！与上方水滴副岛视觉严丝合缝
        cx = self.PADDING + self.CARD_W / 2.0
        cy = self.PADDING

        painter.save()
        painter.translate(cx, cy + cur_dy)
        painter.scale(cur_scale, cur_scale)
        painter.translate(-cx, -cy)

        painter.setOpacity(alpha)
        # 纯显卡硬件加速 High-DPI Blit 贴图
        painter.drawPixmap(int(self.PADDING), int(self.PADDING), self.cached_pixmap)
        painter.restore()

    def compute_layout(self):
        TOP_PAD = 12.0
        BOT_PAD = 12.0
        left_x = self.SIDE_PAD
        w = self.CONTENT_W
        top_y = TOP_PAD
        card_bottom = self.current_card_h

        self.btn1_rect = QRectF(0, 0, 0, 0)
        self.btn2_rect = QRectF(0, 0, 0, 0)
        self.option_rects = []
        self.link_rect = QRectF(0, 0, 0, 0)

        if self.action_type == "plan_approval":
            btn_y = card_bottom - BOT_PAD - 24.0
            btn1_w = 170.0
            btn2_w = w - btn1_w - 8.0
            self.btn1_rect = QRectF(left_x, btn_y, btn1_w, 24.0)
            self.btn2_rect = QRectF(left_x + btn1_w + 8.0, btn_y, btn2_w, 24.0)
        else:
            raw_options = self.metrics_data.get("pending_options") or ["确认继续", "需要调整方案"]
            options = raw_options[:3]

            full_q = self.metrics_data.get("pending_detail") or "请选择后续方案"
            fm_sub = QFontMetrics(self.f_sub)
            br_q = fm_sub.boundingRect(QRect(0, 0, int(w), 10000), Qt.TextFlag.TextWordWrap, full_q)
            q_h = max(18.0, float(br_q.height() + 4.0))

            base_opt_y = top_y + 16.0 + 6.0 + q_h + 8.0

            fm_opt = QFontMetrics(self.f_opt)
            for i, opt in enumerate(options):
                is_rec = "(Recommended)" in opt or "(推荐)" in opt
                clean_opt = opt.replace("(Recommended)", "").replace("(推荐)", "").strip()
                avail_w = w - 24.0 - (46.0 if is_rec else 8.0)
                br_opt = fm_opt.boundingRect(QRect(0, 0, int(avail_w), 10000), Qt.TextFlag.TextWordWrap, clean_opt)
                opt_h = float(max(34.0, br_opt.height() + 16.0))

                self.option_rects.append(QRectF(left_x, base_opt_y, w, opt_h))
                base_opt_y += opt_h + 6.0

            # 底部微链接严格固定在卡片底部内侧 12px 处，绝不超出卡片边缘
            self.link_rect = QRectF(left_x + w - 105.0, card_bottom - BOT_PAD - 16.0, 105.0, 16.0)

    def draw_approval_content(self, painter, rect, alpha):
        TOP_PAD = 12.0
        left_x = self.SIDE_PAD
        top_y = TOP_PAD
        w = self.CONTENT_W

        # 1. 顶部：柔和翡翠绿呼吸点 + 标题 + 右侧状态
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(52, 211, 153, int(230 * alpha))))
        painter.drawEllipse(QPointF(left_x + 3.0, top_y + 8.0), 2.5, 2.5)

        painter.setFont(self.f_tit)
        painter.setPen(QColor(255, 255, 255, int(245 * alpha)))
        painter.drawText(QRectF(left_x + 12.0, top_y, w - 75.0, 16.0), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, "方案待审批")

        painter.setFont(self.f_sub)
        painter.setPen(QColor(161, 161, 170, int(200 * alpha)))
        painter.drawText(QRectF(left_x + w - 75.0, top_y, 75.0, 16.0), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, "等待确认")

        # 2. 方案核心目标/标题摘要
        plan_desc = self.metrics_data.get("pending_detail") or "架构重构与交互闭环已就绪"
        painter.setFont(self.f_sub)
        painter.setPen(QColor(228, 228, 231, int(235 * alpha)))
        fm = painter.fontMetrics()
        elided_desc = fm.elidedText(plan_desc, Qt.TextElideMode.ElideRight, int(w))
        painter.drawText(QRectF(left_x, top_y + 22.0, w, 18.0), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, elided_desc)

        # 3. 展开详情 (改动代码文件芯片微徽章 + 核心实施步骤)
        drawer_y = top_y + 44.0
        files = self.metrics_data.get("pending_files") or []
        if files:
            chip_x = left_x
            painter.setFont(self.f_chip)
            for f_name in files[:3]:
                f_name_w = painter.fontMetrics().horizontalAdvance(f_name)
                chip_w = f_name_w + 22.0
                if chip_x + chip_w > left_x + w:
                    break
                chip_rect = QRectF(chip_x, drawer_y, chip_w, 18.0)
                painter.setPen(QPen(QColor(59, 130, 246, int(alpha * 90)), 1.0))
                painter.setBrush(QBrush(QColor(59, 130, 246, int(alpha * 35))))
                painter.drawRoundedRect(chip_rect, 4.0, 4.0)

                # 手绘矢量极细折角文件微图标
                self.draw_vector_file_icon(painter, chip_x + 8.0, drawer_y + 9.0, QColor(96, 165, 250), alpha)

                painter.setPen(QColor(224, 242, 254, int(alpha * 240)))
                painter.drawText(QRectF(chip_x + 16.0, drawer_y, f_name_w + 4.0, 18.0), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, f_name)
                chip_x += chip_w + 6.0
            drawer_y += 24.0

        steps = self.metrics_data.get("pending_steps") or []
        if steps:
            painter.setFont(self.f_step)
            for idx, step_str in enumerate(steps[:2]):
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(QColor(59, 130, 246, int(alpha * 200))))
                painter.drawEllipse(QPointF(left_x + 3.0, drawer_y + 8.0), 2.0, 2.0)

                painter.setPen(QColor(212, 212, 216, int(alpha * 230)))
                fm_s = painter.fontMetrics()
                elided_s = fm_s.elidedText(f"{idx+1}. {step_str}", Qt.TextElideMode.ElideRight, int(w - 10.0))
                painter.drawText(QRectF(left_x + 10.0, drawer_y, w - 10.0, 16.0), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, elided_s)
                drawer_y += 17.0

        # 4. 底部操作栏 [✓ 立即批准开工] + [↗ 查阅]
        h1 = (self.hovered_btn == 0)
        bg1_a = int(alpha * (85 if h1 else 45))
        border1_a = int(alpha * (200 if h1 else 120))
        painter.setPen(QPen(QColor(16, 185, 129, border1_a), 1.0))
        painter.setBrush(QBrush(QColor(16, 185, 129, bg1_a)))
        painter.drawRoundedRect(self.btn1_rect, 6.0, 6.0)

        painter.setFont(self.f_btn)
        painter.setPen(QColor(255, 255, 255, int(alpha * (255 if h1 else 230))))
        painter.drawText(self.btn1_rect, Qt.AlignmentFlag.AlignCenter, "✓ 立即批准开工")

        h2 = (self.hovered_btn == 1)
        bg2_a = int(alpha * (32 if h2 else 16))
        border2_a = int(alpha * (80 if h2 else 35))
        painter.setPen(QPen(QColor(255, 255, 255, border2_a), 1.0))
        painter.setBrush(QBrush(QColor(255, 255, 255, bg2_a)))
        painter.drawRoundedRect(self.btn2_rect, 6.0, 6.0)

        painter.setFont(self.f_btn)
        painter.setPen(QColor(244, 244, 245, int(alpha * (255 if h2 else 180))))
        painter.drawText(self.btn2_rect, Qt.AlignmentFlag.AlignCenter, "↗ 查阅")

    def draw_question_content(self, painter, rect, alpha):
        TOP_PAD = 12.0
        left_x = self.SIDE_PAD
        top_y = TOP_PAD
        w = self.CONTENT_W

        # 1. 顶部：柔和天青微呼吸点 + 纯白标题 + 极简静谧灰状态
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(56, 189, 248, int(220 * alpha))))
        painter.drawEllipse(QPointF(left_x + 3.0, top_y + 8.0), 2.5, 2.5)

        painter.setFont(self.f_tit)
        painter.setPen(QColor(255, 255, 255, int(245 * alpha)))
        painter.drawText(QRectF(left_x + 12.0, top_y, w - 75.0, 16.0), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, "决策确认")

        painter.setFont(self.f_sub)
        painter.setPen(QColor(161, 161, 170, int(200 * alpha)))
        painter.drawText(QRectF(left_x + w - 75.0, top_y, 75.0, 16.0), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, "等待选择")

        # 2. 题干长文字（多行完整换行排版，自然向下延伸，零抖动）
        full_q = self.metrics_data.get("pending_detail") or "请选择后续方案"
        fm_sub = painter.fontMetrics()
        br_q = fm_sub.boundingRect(QRect(0, 0, int(w), 10000), Qt.TextFlag.TextWordWrap, full_q)
        q_h = max(18.0, float(br_q.height() + 4.0))

        painter.setFont(self.f_sub)
        painter.setPen(QColor(228, 228, 231, int(235 * alpha)))
        painter.drawText(QRectF(left_x, top_y + 22.0, w, q_h), Qt.TextFlag.TextWordWrap | Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft, full_q)

        # 3. 选项微胶囊列表 (全自动多行动态自适应，首行对齐，彻底消除削顶切底)
        raw_options = self.metrics_data.get("pending_options") or ["确认继续", "需要调整方案"]
        options = raw_options[:3]

        painter.setFont(self.f_opt)
        fm_opt = painter.fontMetrics()
        for i, opt_rect in enumerate(self.option_rects):
            if i >= len(options):
                break

            raw_text = options[i]
            is_rec = "(Recommended)" in raw_text or "(推荐)" in raw_text
            clean_text = raw_text.replace("(Recommended)", "").replace("(推荐)", "").strip()

            is_hover = (self.hovered_btn == (10 + i))
            is_sel = (self.selected_opt_idx == i)

            # 纯黑曜石微透底座与发丝高光边框
            if is_hover or is_sel:
                opt_pen = QPen(QColor(255, 255, 255, int(45 * alpha)), 1.0)
                opt_bg = QBrush(QColor(255, 255, 255, int(22 * alpha)))
                text_color = QColor(255, 255, 255, int(255 * alpha))
                dot_c = QColor(255, 255, 255, int(245 * alpha))
            else:
                opt_pen = QPen(QColor(255, 255, 255, int(18 * alpha)), 1.0)
                opt_bg = QBrush(QColor(255, 255, 255, int(10 * alpha)))
                text_color = QColor(212, 212, 216, int(225 * alpha))
                dot_c = QColor(140, 140, 148, int(140 * alpha))

            painter.setPen(opt_pen)
            painter.setBrush(opt_bg)
            painter.drawRoundedRect(opt_rect, 7.0, 7.0)

            # 单选指示圆点：严格对齐第一行文字垂直中心 (y + 8.0 + 8.0 = y + 16.0)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(dot_c))
            painter.drawEllipse(QPointF(opt_rect.x() + 12.0, opt_rect.y() + 16.0), 2.4, 2.4)

            # 推荐标记：对齐首行右侧
            text_avail_w = opt_rect.width() - 24.0 - 8.0
            if is_rec:
                rec_w = 38.0
                rec_rect = QRectF(opt_rect.right() - rec_w - 8.0, opt_rect.y() + 8.0 + 1.0, rec_w, 14.5)
                painter.setPen(QPen(QColor(16, 185, 129, int(80 * alpha)), 1.0))
                painter.setBrush(QBrush(QColor(16, 185, 129, int(30 * alpha))))
                painter.drawRoundedRect(rec_rect, 3.5, 3.5)
                painter.setFont(self.f_step)
                painter.setPen(QColor(110, 231, 183, int(235 * alpha)))
                painter.drawText(rec_rect, Qt.AlignmentFlag.AlignCenter, "推荐")
                text_avail_w -= (rec_w + 6.0)

            # 选项文字排版：采用 AlignTop | AlignLeft，从顶部自然展开，彻底杜绝削顶切底！
            painter.setFont(self.f_opt)
            painter.setPen(text_color)
            br_opt = fm_opt.boundingRect(QRect(0, 0, int(text_avail_w), 10000), Qt.TextFlag.TextWordWrap, clean_text)
            text_box = QRectF(opt_rect.x() + 24.0, opt_rect.y() + 8.0, text_avail_w, float(br_opt.height() + 2.0))
            painter.drawText(text_box, Qt.TextFlag.TextWordWrap | Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft, clean_text)

        # 4. 底部微链接：“↗ 在 IDE 中输入” (严格距离卡片下边缘 12px 留白，绝不超出)
        painter.setFont(self.f_sub)
        is_link_hover = (self.hovered_btn == 1)
        link_pen = QColor(255, 255, 255, int(240 * alpha)) if is_link_hover else QColor(140, 140, 148, int(170 * alpha))
        painter.setPen(link_pen)
        painter.drawText(self.link_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, "↗ 在 IDE 中输入")

    def mouseMoveEvent(self, event):
        pos = event.position()
        px = pos.x() - self.PADDING
        py = pos.y() - self.PADDING

        old_hover = self.hovered_btn
        self.hovered_btn = -1

        card_rect = QRectF(0, 0, self.CARD_W, self.current_card_h)
        if card_rect.contains(px, py):
            if self.action_type == "plan_approval":
                if self.btn1_rect.contains(px, py):
                    self.hovered_btn = 0
                elif self.btn2_rect.contains(px, py):
                    self.hovered_btn = 1
            else:
                for i, o_rect in enumerate(self.option_rects):
                    if o_rect.contains(px, py):
                        self.hovered_btn = 10 + i
                        break
                if self.hovered_btn == -1 and self.link_rect.contains(px, py):
                    self.hovered_btn = 1

        if self.hovered_btn != old_hover:
            self.bake_cache_pixmap()
            self.update()

        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position()
            px = pos.x() - self.PADDING
            py = pos.y() - self.PADDING

            card_rect = QRectF(0, 0, self.CARD_W, self.current_card_h)
            if not card_rect.contains(px, py):
                super().mousePressEvent(event)
                return

            if self.action_type == "plan_approval":
                if self.btn1_rect.contains(px, py):
                    send_decision_via_cdp("plan_approval", "approve")
                    self.action_submitted.emit("plan_approval", "approve")
                    self.dismiss(fast=True)
                    event.accept()
                    return
                elif self.btn2_rect.contains(px, py):
                    bring_antigravity_to_foreground()
                    self.dismiss(fast=True)
                    event.accept()
                    return
            else:
                for i, o_rect in enumerate(self.option_rects):
                    if o_rect.contains(px, py):
                        raw_options = self.metrics_data.get("pending_options") or ["确认继续", "需要调整方案"]
                        choice = raw_options[i] if i < len(raw_options) else ""
                        send_decision_via_cdp("ask_question", choice)
                        self.action_submitted.emit("ask_question", choice)
                        self.dismiss(fast=True)
                        event.accept()
                        return
                if self.link_rect.contains(px, py):
                    bring_antigravity_to_foreground()
                    self.dismiss(fast=True)
                    event.accept()
                    return

            event.accept()
            return

        super().mousePressEvent(event)

    def enterEvent(self, event):
        self.auto_dismiss_timer.stop()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.hovered_btn = -1
        self.bake_cache_pixmap()
        self.update()

        cur_pos = QCursor.pos()
        # 智能判定：若鼠标移出卡片时是向上方（即往主岛/副岛方向移），立即以快速折叠模式避让！
        if cur_pos.y() < self.y() + self.PADDING + 10:
            self.dismiss(fast=True)
        else:
            self.auto_dismiss_timer.start(280)
        super().leaveEvent(event)


# =================================================================
# 独立后台工作线程 (BackgroundMetricsWorker)
# =================================================================
class BackgroundMetricsWorker(QThread):
    metrics_signal = pyqtSignal(dict)
    running_signal = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self._running = True
        self.is_busy = False

    def run(self):
        while self._running:
            try:
                running = is_antigravity_running()
                self.running_signal.emit(running)

                if running:
                    m = get_context_metrics()
                    m["is_fg"] = is_antigravity_foreground()
                    self.is_busy = m.get("is_busy", False)
                    self.metrics_signal.emit(m)
            except Exception:
                pass

            sleep_time = 0.5 if self.is_busy else 1.2
            steps = int(sleep_time / 0.1)
            for _ in range(steps):
                if not self._running:
                    break
                time.sleep(0.1)

    def stop(self):
        self._running = False
        self.wait(800)


# =================================================================
# 灵动岛主悬浮窗 (SmoothDynamicIsland)
# =================================================================
class SmoothDynamicIsland(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.cfg = load_config()

        self.metrics = {
            "has_active": True,
            "project_name": "Antigravity",
            "percent": 0.0,
            "total_used": 0,
            "model_tokens": 0,
            "tool_tokens": 0,
            "system_tokens": 4000,
            "user_tokens": 0,
            "is_busy": False,
            "just_completed": False,
            "duration_str": ""
        }
        self.cached_used_str = "0.0k"
        self.cached_pct_str = "0.0%"
        self.cached_bar_widths = (1.0, 1.0, 1.0, 1.0)
        self.cached_items = []

        # 144Hz 弹簧动力学求解器参数
        self.current_w = float(COMPACT_W)
        self.current_h = float(COMPACT_H)
        self.target_w = float(COMPACT_W)
        self.target_h = float(COMPACT_H)
        self.vel_w = 0.0
        self.vel_h = 0.0
        self.spring_k = 500.0
        self.spring_c = 32.0
        self.last_spring_time = 0.0
        self.on_spring_finished_cb = None

        self.spring_timer = QTimer(self)
        self.spring_timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.spring_timer.setInterval(7)
        self.spring_timer.timeout.connect(self.on_spring_tick)

        # 灵动双联岛（多任务水滴副岛）动力学状态
        self.droplet_scale = 0.0
        self.droplet_target_scale = 0.0
        self.droplet_vel_scale = 0.0
        self.droplet_x_offset = -12.0
        self.droplet_vel_x = 0.0
        self.droplet_alpha = 0.0
        self.is_hovering_droplet = False

        # 流体水滴磁吸融合与主岛果冻冲击动力学参数
        self.is_absorbing = False
        self.absorb_t = 0.0
        self.droplet_squash_x = 1.0
        self.droplet_squash_y = 1.0
        self.impact_w = 0.0
        self.impact_vel_w = 0.0

        # 水滴副岛连通器避让膨胀动力学参数 (0.0 为微圆 30px，118.0 为膨胀胶囊 148px)
        self.droplet_expand_w = 0.0
        self.droplet_target_expand_w = 0.0
        self.droplet_vel_expand = 0.0

        # 紧凑态文字垂直平滑翻转动力学参数 (0.0 为原项目名，1.0 为待办提示)
        self.text_flip = 0.0
        self.target_text_flip = 0.0
        self.text_flip_vel = 0.0

        # 状态
        self.is_notifying = False
        self.notify_duration_str = ""
        self.is_mouse_inside = False
        self.is_manually_hidden = False
        self.last_running = None

        # 最小微圆状态 (Minimal Mode: 30px 屏幕顶部居中纯黑曜石微圆)
        self.is_minimal_mode = bool(self.cfg.get("minimal_mode", False))
        self.minimal_hover_alpha = 0.0

        # 边缘贴靠灵动收缩 (Edge Notch Auto-Tuck) 状态与物理动力学
        self.auto_tuck_enabled = bool(self.cfg.get("auto_tuck", True))
        self.tuck_delay_ms = int(self.cfg.get("tuck_delay_ms", 4000))
        self.is_tucked = False
        self.tuck_y_offset = 0.0          # 当前平移偏移量（0.0 展开态，-39.0 完全贴顶）
        self.tuck_target_y_offset = 0.0   # 目标平移偏移量
        self.tuck_vel = 0.0               # 物理二阶弹簧速度
        self.base_win_y = 0               # 展开态基准物理 Y 坐标
        self.last_tuck_tick_time = 0.0

        self.init_resources()
        self.update_cached_strings()
        self.setup_window()
        self.setup_timers()
        self.setup_pill_bar()
        self.setup_action_flyout()
        self.setup_worker()
        self.setup_tray_icon()
        self.setup_ipc_server()
        self.schedule_auto_tuck()

    def init_resources(self):
        # 瑞士现代排版：优先 Segoe UI Variable Text / Segoe UI，Medium 500 字重，优雅克制
        self.f_proj = QFont("Segoe UI Variable Text", 9)
        if not self.f_proj.exactMatch():
            self.f_proj = QFont("Segoe UI", 9)
        self.f_proj.setWeight(QFont.Weight.Medium)

        # 百分比数字与符号精细分离
        self.f_pct = QFont("Consolas", 9)
        self.f_pct.setBold(True)
        self.f_pct_sym = QFont("Segoe UI Variable Text", 7)
        if not self.f_pct_sym.exactMatch():
            self.f_pct_sym = QFont("Segoe UI", 7)
        self.f_pct_sym.setWeight(QFont.Weight.Medium)

        self.f_notify = QFont("Segoe UI", 9)
        self.f_notify.setBold(True)

        self.f_exp_proj = QFont("Segoe UI", 10)
        self.f_exp_proj.setBold(True)

        self.f_tag = QFont("Segoe UI", 7)
        self.f_tag.setBold(True)

        self.f_used = QFont("Consolas", 10)
        self.f_used.setBold(True)

        self.f_cap = QFont("Segoe UI", 8)

        self.f_big_pct = QFont("Consolas", 11)
        self.f_big_pct.setBold(True)

        self.f_tip = QFont("Microsoft YaHei", 8)
        self.f_tip.setWeight(QFont.Weight.Medium)

        self.f_lbl = QFont("Segoe UI", 8)

        self.f_val = QFont("Consolas", 8)
        self.f_val.setBold(True)

        self.c_model = QColor(16, 185, 129)
        self.c_tool = QColor(245, 158, 11)
        self.c_sys = QColor(168, 85, 247)
        self.c_user = QColor(56, 189, 248)

    def get_target_screen(self):
        """
        智能探测灵动岛目标停靠显示器：
        1. 优先探测 Antigravity IDE 宿主主窗口所在显示器；
        2. 若未探测到 IDE 窗口，则使用鼠标当前所在显示器；
        3. 兜底使用系统主显示器 (primaryScreen)。
        """
        # 1. 优先根据 Antigravity IDE 宿主窗口探测
        try:
            rect = get_antigravity_window_rect()
            if rect:
                cx = (rect[0] + rect[2]) // 2
                cy = (rect[1] + rect[3]) // 2
                scr = QApplication.screenAt(QPoint(cx, cy))
                if scr:
                    return scr
        except Exception:
            pass

        # 2. 探测鼠标光标所在屏幕
        try:
            scr = QApplication.screenAt(QCursor.pos())
            if scr:
                return scr
        except Exception:
            pass

        # 3. 兜底返回主屏幕
        return QApplication.primaryScreen()

    def on_screen_removed(self, screen):
        """显示器拔出或休眠断开：安全校验当前屏幕有效性，平滑回退主屏"""
        cur_center = self.geometry().center()
        still_valid = QApplication.screenAt(cur_center)
        if still_valid is None:
            self.reset_to_center(QApplication.primaryScreen())

    def on_screen_added(self, screen):
        """新显示器插入：若当前处于不可见盲区，重新校准"""
        cur_center = self.geometry().center()
        if QApplication.screenAt(cur_center) is None:
            self.reset_to_center(QApplication.primaryScreen())

    def on_window_screen_changed(self, new_screen):
        """窗口跨屏移动，DPI 或物理屏幕发生跃迁时自动刷新遮罩与矢量渲染"""
        if new_screen:
            self.update_mask()
            self.update()

    def showEvent(self, event):
        super().showEvent(event)
        wh = self.windowHandle()
        if wh and not hasattr(self, "_screen_changed_connected"):
            wh.screenChanged.connect(self.on_window_screen_changed)
            self._screen_changed_connected = True

    def setup_window(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

        # 智能跟随 + 手动记忆复合定位
        target_scr = None
        capsule_x = self.cfg.get("x")
        capsule_y = self.cfg.get("y", 12)

        if capsule_x is not None and isinstance(capsule_x, (int, float)):
            test_pt = QPoint(int(capsule_x + COMPACT_W / 2.0), int(capsule_y + COMPACT_H / 2.0))
            scr = QApplication.screenAt(test_pt)
            if scr:
                target_scr = scr

        if target_scr is None:
            target_scr = self.get_target_screen()
            avail = target_scr.availableGeometry()
            capsule_x = avail.left() + (avail.width() - COMPACT_W) // 2
            capsule_y = avail.top() + 12

        avail = target_scr.availableGeometry()
        min_cx = avail.left()
        max_cx = avail.left() + avail.width() - COMPACT_W
        capsule_x = max(min_cx, min(capsule_x, max_cx))

        min_cy = avail.top()
        max_cy = avail.top() + avail.height() - COMPACT_H
        capsule_y = max(min_cy, min(capsule_y, max_cy))

        if self.is_minimal_mode:
            self.current_w = 30.0
            self.current_h = 30.0
            self.target_w = 30.0
            self.target_h = 30.0
            self.droplet_scale = 0.0
            self.droplet_target_scale = 0.0

        win_x = int(capsule_x - (CANVAS_W - COMPACT_W) / 2.0)
        win_y = int(capsule_y - PADDING_TOP)
        self.base_win_y = win_y

        self.setGeometry(win_x, win_y, CANVAS_W, CANVAS_H)
        self.update_mask()
        self.make_topmost()

        # 监听多显示器热插拔事件
        app = QApplication.instance()
        if app:
            app.screenRemoved.connect(self.on_screen_removed)
            app.screenAdded.connect(self.on_screen_added)

    def make_topmost(self):
        """Win32 硬件级置顶 (HWND_TOPMOST)"""
        try:
            hwnd = int(self.winId())
            ctypes.windll.user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0040)
            ctypes.windll.user32.SetWindowTextW(hwnd, WINDOW_TITLE)
        except Exception:
            pass

    def get_capsule_rect(self):
        cx = CANVAS_W / 2.0

        # 最小微圆模式 (当未触发全宽通知时，保持 30x30 居中微圆)
        if self.is_minimal_mode and not self.is_notifying:
            w = max(30.0, self.current_w)
            h = max(30.0, self.current_h)
            x = cx - w / 2.0
            return QRectF(x, float(PADDING_TOP), w, h)

        # 大屏展开模式时（单岛居中）
        if self.current_w > 220.0:
            w = self.current_w + self.impact_w
            x = cx - w / 2.0
            return QRectF(x, float(PADDING_TOP), w, self.current_h)

        # 连通器流体避让模式（双联岛组合在画布居中平衡，恒定 8px 间隙）
        # 主岛从 182px 协同收缩为 30px 正圆微岛，水滴副岛向左展开为 160px 单行待办胶囊
        shrink_w = self.droplet_expand_w * (152.0 / 130.0)
        main_w = max(30.0, self.current_w - shrink_w) + self.impact_w
        drop_w = 30.0 + self.droplet_expand_w
        gap = 8.0

        total_combo_w = main_w + gap + drop_w
        combo_left = cx - total_combo_w / 2.0
        return QRectF(combo_left, float(PADDING_TOP), main_w, self.current_h)

    def get_droplet_rect(self):
        cx = CANVAS_W / 2.0
        if self.is_minimal_mode or self.current_w > 220.0:
            # 最小模式或大屏模式下水滴不外显
            return QRectF(cx + self.current_w / 2.0 - 30.0, float(PADDING_TOP), 30.0, 30.0)

        shrink_w = self.droplet_expand_w * (152.0 / 130.0)
        main_w = max(30.0, self.current_w - shrink_w) + self.impact_w
        drop_w = 30.0 + self.droplet_expand_w
        gap = 8.0

        total_combo_w = main_w + gap + drop_w
        combo_left = cx - total_combo_w / 2.0

        cur_x = combo_left + main_w + gap + self.droplet_x_offset
        return QRectF(cur_x, float(PADDING_TOP), drop_w, 30.0)

    def update_mask(self):
        rect = self.get_capsule_rect()
        x = int(rect.x())
        y = int(rect.y())
        w = int(rect.width())
        h = int(rect.height())
        mask = QRegion(QRect(x - 2, y - 2, w + 4, h + 4))

        # 最小微圆状态下若浮出悬停提示气泡，穿透遮罩动态联合该区域
        if self.is_minimal_mode and not self.is_notifying and self.minimal_hover_alpha > 0.05:
            cx = rect.center().x()
            badge_w = 140
            badge_h = 24
            bx = int(cx - badge_w / 2.0)
            by = int(rect.bottom() + 4.0)
            mask = mask.united(QRegion(QRect(bx - 2, by - 2, badge_w + 4, badge_h + 4)))

        # 若水滴副岛处于外显分离状态，根据实时药丸尺寸动态联合穿透遮罩
        if not self.is_minimal_mode and self.droplet_alpha > 0.05 and self.current_w < 240:
            d_rect = self.get_droplet_rect()
            dx = int(d_rect.x())
            dy = int(d_rect.y())
            dw = int(d_rect.width())
            dh = int(d_rect.height())
            droplet_region = QRegion(QRect(dx - 3, dy - 3, dw + 6, dh + 6))
            mask = mask.united(droplet_region)

        self.setMask(mask)

    def setup_timers(self):
        self.collapse_timer = QTimer(self)
        self.collapse_timer.setSingleShot(True)
        self.collapse_timer.timeout.connect(self.start_collapse)

        self.notify_collapse_timer = QTimer(self)
        self.notify_collapse_timer.setSingleShot(True)
        self.notify_collapse_timer.timeout.connect(self.collapse_notification)

        # 鼠标跨窗口桥接感应定时器 (Hover Bridge: 移出灵动岛与药丸栏瞬间自动收回)
        self.hover_bridge_timer = QTimer(self)
        self.hover_bridge_timer.setInterval(60)
        self.hover_bridge_timer.timeout.connect(self.check_hover_bridge)

        # 待办水滴呼吸光晕慢速定时器 (40ms, 0.0% CPU)
        self.halo_timer = QTimer(self)
        self.halo_timer.setInterval(40)
        self.halo_timer.timeout.connect(self.update)

        # 1. 水滴悬停意图防误触定时器 (60ms: 灵敏即刻响应，划过副岛不误触)
        self.droplet_hover_intent_timer = QTimer(self)
        self.droplet_hover_intent_timer.setSingleShot(True)
        self.droplet_hover_intent_timer.setInterval(60)
        self.droplet_hover_intent_timer.timeout.connect(self.on_droplet_hover_confirmed)

        # 2. 悬停展开后自动滑出二级操作卡片辅助定时器
        self.auto_flyout_timer = QTimer(self)
        self.auto_flyout_timer.setSingleShot(True)
        self.auto_flyout_timer.setInterval(20)
        self.auto_flyout_timer.timeout.connect(self.trigger_auto_flyout)

        # 3. 水滴移出滞后去抖定时器 (160ms: 敏捷收纳去抖)
        self.droplet_exit_debounce_timer = QTimer(self)
        self.droplet_exit_debounce_timer.setSingleShot(True)
        self.droplet_exit_debounce_timer.setInterval(160)
        self.droplet_exit_debounce_timer.timeout.connect(self.on_droplet_exit_confirmed)

        # 4. 边缘贴靠灵动收缩倒计时定时器 (4 秒闲置自动贴顶收缩)
        self.tuck_countdown_timer = QTimer(self)
        self.tuck_countdown_timer.setSingleShot(True)
        self.tuck_countdown_timer.setInterval(self.tuck_delay_ms)
        self.tuck_countdown_timer.timeout.connect(self.start_tuck)

        # 5. 贴边物理落体弹簧动效定时器 (7ms 高精度物理引擎，滑下带 1.2px 微弹性回弹)
        self.tuck_spring_timer = QTimer(self)
        self.tuck_spring_timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.tuck_spring_timer.setInterval(7)
        self.tuck_spring_timer.timeout.connect(self.on_tuck_spring_tick)

        # 6. 贴顶收缩态极顶光标感应时钟 (45ms 极低开销轮询，仅在 is_tucked 时启动)
        self.tuck_edge_sensor_timer = QTimer(self)
        self.tuck_edge_sensor_timer.setInterval(45)
        self.tuck_edge_sensor_timer.timeout.connect(self.check_tuck_edge_hover)

    def on_droplet_hover_confirmed(self):
        """鼠标在副岛停留满 120ms，确认为意图悬停：主岛平滑收缩为 30px 圆环，副岛展开为 160px 胶囊，顺势落体弹出大卡片"""
        if self.target_w > COMPACT_W + 5.0 or self.current_w > COMPACT_W + 15.0:
            self.start_collapse()
        if not self.is_absorbing and self.target_text_flip < 0.5:
            self.droplet_target_expand_w = 130.0
            self.clearMask()
            if not self.spring_timer.isActive():
                self.spring_timer.start(7)
            self.update()
        # 顺势一体化落体滑出二级卡片 (无需额外等待)
        self.trigger_auto_flyout()

    def trigger_auto_flyout(self):
        """水滴胶囊确认识别后，自动丝滑滑出二级微操作大卡片 (无需用户点击)"""
        if not hasattr(self, "action_flyout"):
            return
        if self.action_flyout.isVisible() and not self.action_flyout.is_closing:
            return
        if self.droplet_scale > 0.35:
            cx = CANVAS_W / 2.0
            total_combo_w = 30.0 + 8.0 + 160.0  # 稳态主岛 30 + 间隙 8 + 副岛 160
            combo_left = cx - total_combo_w / 2.0
            drop_stable_center_x = self.x() + combo_left + 30.0 + 8.0 + (160.0 / 2.0)
            drop_bottom_y = self.y() + float(PADDING_TOP) + 30.0
            self.action_flyout.popup(drop_stable_center_x, drop_bottom_y + 4.0, self.metrics)
            self.hover_bridge_timer.start(60)

    def on_droplet_exit_confirmed(self):
        """鼠标确实移开水滴副岛且未进入二级操作卡片，缓冲 240ms 确认后弹性收拢回 30px 小圆"""
        self.auto_flyout_timer.stop()
        if hasattr(self, "action_flyout") and self.action_flyout.isVisible() and not self.action_flyout.is_closing:
            return
        if self.droplet_target_expand_w > 10.0 and not self.is_absorbing:
            self.droplet_target_expand_w = 0.0
            self.clearMask()
            if not self.spring_timer.isActive():
                self.spring_timer.start(7)
            self.update()

    def setup_pill_bar(self):
        """构建横向迷你微药丸栏"""
        self.pill_bar = MiniPillBar()
        self.pill_bar.refresh_requested.connect(self.force_refresh)
        self.pill_bar.reset_requested.connect(self.reset_to_center)
        self.pill_bar.minimal_mode_requested.connect(self.enter_minimal_mode)
        self.pill_bar.quit_requested.connect(self.clean_exit)
        self.pill_bar.dismissed.connect(self.on_pill_bar_dismissed)

    def enter_minimal_mode(self):
        """进入最小状态：收缩为 30px 屏幕顶部居中微圆，并持久化到配置"""
        self.is_minimal_mode = True
        self.cfg["minimal_mode"] = True
        save_config(self.cfg)

        if getattr(self, "is_tucked", False):
            self.untuck(fast=True)
        if hasattr(self, "tuck_countdown_timer"):
            self.tuck_countdown_timer.stop()

        # 确保窗口居中到当前所在屏幕顶部
        cur_screen = QApplication.screenAt(self.geometry().center())
        if not cur_screen:
            cur_screen = QApplication.primaryScreen()
        avail = cur_screen.availableGeometry()
        default_win_x = avail.left() + (avail.width() - CANVAS_W) // 2
        cur_y = self.y()
        self.move(default_win_x, cur_y)

        # 隐藏二级子菜单与药丸栏
        if hasattr(self, "action_flyout") and self.action_flyout.isVisible():
            self.action_flyout.dismiss(fast=True)
        if hasattr(self, "pill_bar") and self.pill_bar.isVisible():
            self.pill_bar.dismiss()

        self.droplet_target_scale = 0.0
        self.droplet_target_expand_w = 0.0
        if self.metrics.get("is_busy", False):
            if not self.halo_timer.isActive():
                self.halo_timer.start(40)
        self.start_spring_animation(30.0, 30.0, response=0.20, damping_ratio=0.74, on_finished=self.update_mask)

    def exit_minimal_mode(self):
        """退出最小状态：平滑舒展展开回标准灵动岛，并持久化到配置"""
        self.is_minimal_mode = False
        self.cfg["minimal_mode"] = False
        save_config(self.cfg)

        self.clearMask()
        pending_act = self.metrics.get("pending_action")
        if pending_act and self.target_text_flip < 0.5:
            self.droplet_target_scale = 1.0
        elif self.halo_timer.isActive():
            self.halo_timer.stop()

        def on_exit_done():
            self.update_mask()
            self.schedule_auto_tuck()

        self.start_spring_animation(COMPACT_W, COMPACT_H, response=0.22, damping_ratio=0.72, on_finished=on_exit_done)

    def setup_action_flyout(self):
        self.action_flyout = ActionFlyoutCard()
        self.action_flyout.action_submitted.connect(self.on_flyout_action_submitted)
        self.action_flyout.closing_started.connect(self.on_flyout_closing_started)
        self.action_flyout.dismissed.connect(self.on_flyout_dismissed)

    def on_flyout_closing_started(self):
        """二级微操作卡片退场开始的第 0 毫秒：副岛立即收拢回 30px 小圆，主岛协同舒展复原，绝不卡死在 30px！"""
        self.is_hovering_droplet = False
        self.droplet_hover_intent_timer.stop()
        self.auto_flyout_timer.stop()
        self.droplet_exit_debounce_timer.stop()

        if self.droplet_target_expand_w > 5.0 and not self.is_absorbing:
            self.droplet_target_expand_w = 0.0
            self.clearMask()
            if not self.spring_timer.isActive():
                self.spring_timer.start(7)

        if not self.is_mouse_inside:
            self.start_collapse()

    def on_flyout_action_submitted(self, act_type, choice):
        """用户在二级微操作卡片上提交了动作（后台静默闭环，副岛如丝般扑入主岛融合消融）"""
        self.auto_flyout_timer.stop()
        self.droplet_hover_intent_timer.stop()
        self.droplet_exit_debounce_timer.stop()
        # 1. 触发副岛向左拉伸磁吸扑入主岛融合消融并引发果冻微震
        self.start_droplet_absorption()
        # 2. 注意：绝对不切屏唤醒 IDE，保证极致从容不被打扰！

    def on_flyout_dismissed(self):
        self.is_hovering_droplet = False
        if self.droplet_target_expand_w > 5.0 and not self.is_absorbing:
            self.droplet_target_expand_w = 0.0
            self.clearMask()
            if not self.spring_timer.isActive():
                self.spring_timer.start(7)
        if not self.is_mouse_inside:
            self.start_collapse()

    def on_pill_bar_dismissed(self):
        """当小药丸栏完全退场消失后，若鼠标不在主岛上，才触发主岛优雅收拢！保证小岛先消失、主岛后收回"""
        if not self.is_mouse_inside:
            self.start_collapse()

    def force_refresh(self):
        new_m = get_context_metrics(force=True)
        self.on_metrics_updated(new_m)

    # -------------------------------------------------------------
    # 系统托盘与常驻兜底 (System Tray Icon & Context Menu)
    # -------------------------------------------------------------
    def setup_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.update_tray_icon()

        self.tray_menu = QMenu()
        self.setup_tray_menu()
        self.tray_icon.setContextMenu(self.tray_menu)

        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()

    def setup_tray_menu(self):
        self.tray_menu.setStyleSheet("""
            QMenu {
                background-color: #121216;
                border: 1px solid rgba(255, 255, 255, 0.14);
                border-radius: 8px;
                padding: 6px;
                color: #f4f4f5;
                font-family: 'Segoe UI Variable Text', 'Segoe UI', 'Microsoft YaHei', sans-serif;
                font-size: 12px;
            }
            QMenu::item {
                padding: 6px 24px 6px 12px;
                border-radius: 5px;
            }
            QMenu::item:selected {
                background-color: rgba(255, 255, 255, 0.12);
                color: #ffffff;
            }
            QMenu::item:disabled {
                color: rgba(255, 255, 255, 0.35);
            }
            QMenu::separator {
                height: 1px;
                background-color: rgba(255, 255, 255, 0.08);
                margin: 4px 6px;
            }
        """)

        self.tray_menu.aboutToShow.connect(self.on_tray_menu_about_to_show)

        self.act_toggle_vis = QAction("隐藏灵动岛", self)
        self.act_toggle_vis.triggered.connect(self.toggle_visibility_from_tray)
        self.tray_menu.addAction(self.act_toggle_vis)

        self.act_toggle_mode = QAction("切换至 30px 极简微圆", self)
        self.act_toggle_mode.triggered.connect(self.toggle_minimal_mode_from_tray)
        self.tray_menu.addAction(self.act_toggle_mode)

        self.act_auto_tuck = QAction("贴边自动收缩", self)
        self.act_auto_tuck.setCheckable(True)
        self.act_auto_tuck.setChecked(self.auto_tuck_enabled)
        self.act_auto_tuck.triggered.connect(self.toggle_auto_tuck)
        self.tray_menu.addAction(self.act_auto_tuck)

        self.tray_menu.addSeparator()

        self.act_autostart = QAction("开机自启动", self)
        self.act_autostart.setCheckable(True)
        self.act_autostart.setChecked(is_autostart_enabled())
        self.act_autostart.triggered.connect(self.toggle_autostart)
        self.tray_menu.addAction(self.act_autostart)

        self.act_refresh = QAction("立即刷新数据", self)
        self.act_refresh.triggered.connect(self.force_refresh)
        self.tray_menu.addAction(self.act_refresh)

        self.act_reset_pos = QAction("重置顶部居中", self)
        self.act_reset_pos.triggered.connect(lambda: self.reset_to_center())
        self.tray_menu.addAction(self.act_reset_pos)

        # 二级子菜单：停靠至显示器 ▶
        self.menu_screens = QMenu("停靠至显示器", self.tray_menu)
        self.menu_screens.setStyleSheet(self.tray_menu.styleSheet())
        self.tray_menu.addMenu(self.menu_screens)

        self.tray_menu.addSeparator()

        self.act_quit = QAction("彻底退出灵动岛", self)
        self.act_quit.triggered.connect(self.clean_exit_app)
        self.tray_menu.addAction(self.act_quit)

    def on_tray_menu_about_to_show(self):
        if self.isVisible():
            self.act_toggle_vis.setText("隐藏灵动岛")
        else:
            self.act_toggle_vis.setText("显示灵动岛")

        if self.is_minimal_mode:
            self.act_toggle_mode.setText("恢复为标准岛")
        else:
            self.act_toggle_mode.setText("切换至 30px 极简微圆")

        self.act_autostart.setChecked(is_autostart_enabled())
        self.act_auto_tuck.setChecked(getattr(self, "auto_tuck_enabled", True))

        # 动态刷新所有显示器列表
        self.menu_screens.clear()
        screens = QApplication.screens()
        primary_screen = QApplication.primaryScreen()
        cur_center = self.geometry().center()
        current_screen = QApplication.screenAt(cur_center)

        for i, scr in enumerate(screens, 1):
            geo = scr.geometry()
            dpr = scr.devicePixelRatio()
            is_primary = (scr == primary_screen)
            is_current = (scr == current_screen)

            tag = " (主屏)" if is_primary else ""
            dpr_str = f" @ {int(round(dpr * 100))}%" if abs(dpr - 1.0) > 0.01 else ""
            label = f"显示器 {i}{tag} [{geo.width()}x{geo.height()}{dpr_str}]"

            act = QAction(label, self.menu_screens)
            act.setCheckable(True)
            act.setChecked(is_current)

            def make_dock_handler(s):
                return lambda: self.reset_to_center(target_screen=s)

            act.triggered.connect(make_dock_handler(scr))
            self.menu_screens.addAction(act)

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.toggle_visibility_from_tray()
        elif reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            bring_antigravity_to_foreground()
            self.is_manually_hidden = False
            if self.isHidden():
                self.show()
                self.make_topmost()
                self.raise_()
                self.activateWindow()

    def toggle_visibility_from_tray(self):
        if self.isVisible():
            self.is_manually_hidden = True
            self.hide()
        else:
            self.is_manually_hidden = False
            self.show()
            self.make_topmost()
            self.raise_()
            self.activateWindow()
            self.update_mask()

    def toggle_minimal_mode_from_tray(self):
        if self.is_minimal_mode:
            self.exit_minimal_mode()
        else:
            self.enter_minimal_mode()

    def toggle_autostart(self, checked):
        set_autostart_enabled(checked)
        self.act_autostart.setChecked(is_autostart_enabled())

    def clean_exit_app(self):
        if hasattr(self, "tray_icon") and self.tray_icon:
            self.tray_icon.hide()
        self.clean_exit()

    def update_tray_icon(self):
        if not hasattr(self, "tray_icon") or not self.tray_icon:
            return

        is_busy = bool(self.metrics.get("is_busy", False))
        pct_val = float(self.metrics.get("percent", 0.0))
        pending_act = self.metrics.get("pending_action")

        icon = generate_tray_icon(is_busy, pct_val, pending_act)
        self.tray_icon.setIcon(icon)

        status_desc = "思考中 ⚡" if is_busy else "待机"
        if pending_act == "ask_question":
            status_desc = "待回答 ❓"
        elif pending_act == "plan_approval":
            status_desc = "待审批 🛡️"

        total_used = self.metrics.get("total_used", 0)
        proj = self.metrics.get("project_name", "Antigravity")
        tip = f"Antigravity 灵动岛\n状态: {status_desc}\nToken: {pct_val:.1f}% ({total_used/1000:.1f}k / 1.0M)\n项目: {proj}"
        self.tray_icon.setToolTip(tip)

    # -------------------------------------------------------------
    # 单实例 IPC 服务端与跨进程唤醒 (Single-Instance IPC Wakeup)
    # -------------------------------------------------------------
    def setup_ipc_server(self):
        self.ipc_server = QLocalServer(self)
        QLocalServer.removeServer(IPC_PIPE_NAME)
        self.ipc_server.listen(IPC_PIPE_NAME)
        self.ipc_server.newConnection.connect(self.on_ipc_incoming_connection)

    def on_ipc_incoming_connection(self):
        client = self.ipc_server.nextPendingConnection()
        if not client:
            return
        client.readyRead.connect(lambda: self.handle_ipc_message(client))

    def handle_ipc_message(self, client):
        try:
            msg = bytes(client.readAll()).decode("utf-8", errors="ignore").strip()
            if "WAKE_UP" in msg:
                self.wake_up_island()
        except Exception:
            pass

    def wake_up_island(self):
        """无论当前处于隐藏到托盘还是极简微圆，安全唤醒并置顶显现"""
        self.is_manually_hidden = False
        if getattr(self, "is_tucked", False):
            self.untuck(fast=True)
        self.show()
        self.make_topmost()
        self.raise_()
        self.activateWindow()
        self.update_mask()
        self.update()

    # -------------------------------------------------------------
    # 边缘贴靠灵动收缩机制 (Edge Notch Auto-Tuck Engine)
    # -------------------------------------------------------------
    def schedule_auto_tuck(self):
        """检查并规划贴边收缩倒计时（智能状态豁免判定）"""
        if not getattr(self, "auto_tuck_enabled", True) or getattr(self, "is_minimal_mode", False):
            return

        # 强力状态豁免条件：若鼠标在岛内、药丸栏或卡片开启、忙碌思考中、阻断待办中或通知中，绝不收缩！
        pill_open = hasattr(self, "pill_bar") and self.pill_bar.isVisible() and not self.pill_bar.is_closing
        flyout_open = hasattr(self, "action_flyout") and self.action_flyout.isVisible() and not self.action_flyout.is_closing
        is_busy = bool(self.metrics.get("is_busy", False))
        has_pending = bool(self.metrics.get("pending_action"))

        if self.is_mouse_inside or pill_open or flyout_open or is_busy or has_pending or self.is_notifying:
            if hasattr(self, "tuck_countdown_timer"):
                self.tuck_countdown_timer.stop()
            if self.is_tucked:
                self.untuck()
            return

        if not self.is_tucked and hasattr(self, "tuck_countdown_timer") and not self.tuck_countdown_timer.isActive():
            self.tuck_countdown_timer.start(self.tuck_delay_ms)

    def start_tuck(self):
        """开始向上贴顶收缩为 3px 极简呼吸微刘海 (Notch Retract)"""
        if not getattr(self, "auto_tuck_enabled", True) or getattr(self, "is_minimal_mode", False) or self.is_tucked:
            return

        # 再次严格校验豁免条件
        pill_open = hasattr(self, "pill_bar") and self.pill_bar.isVisible() and not self.pill_bar.is_closing
        flyout_open = hasattr(self, "action_flyout") and self.action_flyout.isVisible() and not self.action_flyout.is_closing
        if self.is_mouse_inside or pill_open or flyout_open or self.metrics.get("is_busy") or self.metrics.get("pending_action") or self.is_notifying:
            return

        self.is_tucked = True
        self.tuck_target_y_offset = -39.0
        self.tuck_vel = 0.0
        self.last_tuck_tick_time = time.perf_counter()
        if hasattr(self, "tuck_spring_timer") and not self.tuck_spring_timer.isActive():
            self.tuck_spring_timer.start(7)
        if hasattr(self, "tuck_edge_sensor_timer") and not self.tuck_edge_sensor_timer.isActive():
            self.tuck_edge_sensor_timer.start(45)

    def untuck(self, fast=False):
        """从顶缘顺滑滑落展开回标准岛（带 1.2px 柔和微弹性回弹）"""
        if hasattr(self, "tuck_countdown_timer"):
            self.tuck_countdown_timer.stop()

        if not self.is_tucked and abs(self.tuck_y_offset) < 0.1:
            return

        self.is_tucked = False
        self.tuck_target_y_offset = 0.0

        if fast:
            self.tuck_y_offset = 0.0
            self.tuck_vel = 0.0
            self.move(self.x(), int(self.base_win_y))
            if hasattr(self, "tuck_spring_timer"):
                self.tuck_spring_timer.stop()
            if hasattr(self, "tuck_edge_sensor_timer"):
                self.tuck_edge_sensor_timer.stop()
            self.update_mask()
            self.update()
            return

        self.last_tuck_tick_time = time.perf_counter()
        if hasattr(self, "tuck_spring_timer") and not self.tuck_spring_timer.isActive():
            self.tuck_spring_timer.start(7)

    def on_tuck_spring_tick(self):
        """7ms 二阶物理弹簧落体动效驱动帧"""
        now = time.perf_counter()
        dt = getattr(self, "last_tuck_tick_time", now)
        dt = min(0.025, max(0.002, now - dt))
        self.last_tuck_tick_time = now

        # 动力学参数：滑落时带 1.2px 柔和微回弹 (response=0.22, zeta=0.76)，收回时平滑吸附 (response=0.20, zeta=0.88)
        if self.tuck_target_y_offset < -10.0:
            omega0 = 6.283185 / 0.20
            zeta = 0.88
        else:
            omega0 = 6.283185 / 0.22
            zeta = 0.76

        delta = self.tuck_y_offset - self.tuck_target_y_offset
        accel = -omega0 * omega0 * delta - 2.0 * zeta * omega0 * self.tuck_vel
        self.tuck_vel += accel * dt
        self.tuck_y_offset += self.tuck_vel * dt

        # 停机判定
        if abs(delta) < 0.25 and abs(self.tuck_vel) < 0.9:
            self.tuck_y_offset = self.tuck_target_y_offset
            self.tuck_vel = 0.0
            self.tuck_spring_timer.stop()
            if not self.is_tucked:
                self.tuck_edge_sensor_timer.stop()

        target_y = int(self.base_win_y + self.tuck_y_offset)
        self.move(self.x(), target_y)
        self.update_mask()
        self.update()

    def check_tuck_edge_hover(self):
        """贴顶收缩态下的极顶光标感应（触顶极速滑落）"""
        if not self.is_tucked:
            if hasattr(self, "tuck_edge_sensor_timer"):
                self.tuck_edge_sensor_timer.stop()
            return

        pos = QCursor.pos()
        target_scr = QApplication.screenAt(self.geometry().center()) or QApplication.screenAt(pos)
        if not target_scr:
            target_scr = QApplication.primaryScreen()
        avail = target_scr.availableGeometry()

        # 判定光标是否触碰屏幕极顶（avail.top() ~ avail.top() + 6px）且处于岛体水平感应范围
        c_left = self.x() + (CANVAS_W - COMPACT_W) / 2.0
        c_right = c_left + COMPACT_W
        if avail.top() <= pos.y() <= avail.top() + 8:
            if c_left - 20 <= pos.x() <= c_right + 20:
                self.untuck()

    def toggle_auto_tuck(self, checked):
        """托盘菜单切换贴边自动收缩开关"""
        self.auto_tuck_enabled = checked
        self.cfg["auto_tuck"] = checked
        save_config(self.cfg)
        if not checked and self.is_tucked:
            self.untuck(fast=False)
        elif checked:
            self.schedule_auto_tuck()

    # -------------------------------------------------------------
    # 移出自动收回多窗口联合感应桥 (Multi-Window Hover Bridge)
    # -------------------------------------------------------------
    def check_hover_bridge(self):
        pill_active = hasattr(self, "pill_bar") and self.pill_bar.isVisible() and not self.pill_bar.is_closing
        flyout_active = hasattr(self, "action_flyout") and self.action_flyout.isVisible() and not self.action_flyout.is_closing

        if not pill_active and not flyout_active:
            if hasattr(self, "hover_bridge_timer") and self.hover_bridge_timer.isActive():
                self.hover_bridge_timer.stop()
            return

        pos = QCursor.pos()
        rect = self.get_capsule_rect()
        d_rect = self.get_droplet_rect()

        # 1. 灵动主岛与水滴副岛视觉联合矩形
        island_rect = QRect(
            int(self.x() + rect.x()),
            int(self.y() + rect.y()),
            int(rect.width()),
            int(rect.height())
        )
        if self.droplet_scale > 0.3:
            droplet_rect = QRect(
                int(self.x() + d_rect.x()),
                int(self.y() + d_rect.y()),
                int(d_rect.width()),
                int(d_rect.height())
            )
            combined_rect = island_rect.united(droplet_rect)
        else:
            combined_rect = island_rect

        # 2. 控制药丸栏感应
        if pill_active:
            pill_rect = QRect(
                int(self.pill_bar.x() + self.pill_bar.PADDING),
                int(self.pill_bar.y() + self.pill_bar.PADDING),
                int(PILL_W),
                int(PILL_H + self.pill_bar.TIP_H + 4)
            )
            combined_rect = combined_rect.united(pill_rect)

        # 3. 二级微操作卡片感应
        if flyout_active:
            # 智能互斥退避：若二级微操作卡片正在显示，而鼠标已经悬停/移入了灵动主岛有效区域
            if island_rect.adjusted(-2, -6, 2, 6).contains(pos):
                self.action_flyout.dismiss(fast=True)
                self.raise_()
                flyout_active = False
            else:
                card_h = self.action_flyout.get_card_height()
                flyout_rect = QRect(
                    int(self.action_flyout.x() + self.action_flyout.PADDING),
                    int(self.action_flyout.y() + self.action_flyout.PADDING),
                    int(self.action_flyout.CARD_W),
                    int(card_h)
                )
                combined_rect = combined_rect.united(flyout_rect)

        # 4. 联合感应桥（带 10px 舒适容差，保证平滑滑动不中断）
        buffered_rect = combined_rect.adjusted(-10, -10, 10, 10)
        if not buffered_rect.contains(pos):
            if pill_active:
                self.pill_bar.dismiss()
            if flyout_active:
                self.action_flyout.dismiss()
            self.hover_bridge_timer.stop()

    # -------------------------------------------------------------
    # 满血 144Hz 弹簧动力学引擎
    # -------------------------------------------------------------
    def start_spring_animation(self, target_w, target_h, response=0.22, damping_ratio=0.72, on_finished=None):
        self.target_w = float(target_w)
        self.target_h = float(target_h)
        self.on_spring_finished_cb = on_finished

        omega0 = 6.283185 / max(0.05, response)
        self.spring_k = omega0 * omega0
        self.spring_c = 2.0 * damping_ratio * omega0

        self.last_spring_time = time.perf_counter()
        self.clearMask()
        if not self.spring_timer.isActive():
            self.spring_timer.start(7)

    def start_droplet_absorption(self):
        """触发水滴流体向左拉伸磁吸融合至主岛，并平滑翻转为常驻待办胶囊"""
        self.is_absorbing = True
        self.absorb_t = 0.0
        self.droplet_target_expand_w = 0.0
        self.droplet_expand_w = 0.0
        self.droplet_vel_expand = 0.0
        self.is_hovering_droplet = False
        self.target_text_flip = 1.0
        self.clearMask()
        if not self.spring_timer.isActive():
            self.spring_timer.start(7)

    def on_spring_tick(self):
        now = time.perf_counter()
        dt = now - self.last_spring_time
        self.last_spring_time = now

        dt = min(0.025, max(0.002, dt))

        # 1. 主岛基础尺寸弹簧动力学
        f_w = -self.spring_k * (self.current_w - self.target_w) - self.spring_c * self.vel_w
        self.vel_w += f_w * dt
        self.current_w += self.vel_w * dt

        f_h = -self.spring_k * (self.current_h - self.target_h) - self.spring_c * self.vel_h
        self.vel_h += f_h * dt
        self.current_h += self.vel_h * dt

        # 2. 主岛吸收水滴时的果冻冲击弹性振荡 (k=650.0, c=24.0)
        f_impact = -650.0 * self.impact_w - 24.0 * self.impact_vel_w
        self.impact_vel_w += f_impact * dt
        self.impact_w += self.impact_vel_w * dt
        if abs(self.impact_w) < 0.04 and abs(self.impact_vel_w) < 0.2:
            self.impact_w = 0.0
            self.impact_vel_w = 0.0

        # 3. 紧凑态文字垂直平滑翻转弹簧动力学 (response=0.20, damping=0.82)
        omega_flip = 6.283185 / 0.20
        k_flip = omega_flip * omega_flip
        c_flip = 2.0 * 0.82 * omega_flip
        f_flip = -k_flip * (self.text_flip - self.target_text_flip) - c_flip * self.text_flip_vel
        self.text_flip_vel += f_flip * dt
        self.text_flip += self.text_flip_vel * dt
        if abs(self.text_flip - self.target_text_flip) < 0.01 and abs(self.text_flip_vel) < 0.02:
            self.text_flip = self.target_text_flip
            self.text_flip_vel = 0.0

        # 4. 副岛水滴流体吸附融合动力学 vs 常规分离动力学
        if self.is_absorbing:
            self.absorb_t += dt
            # 阶段一：前 70ms 横向流体拉伸，纵向微压缩，高速向左磁吸扑向主岛
            if self.absorb_t < 0.07:
                p_t = self.absorb_t / 0.07
                self.droplet_squash_x = 1.0 + 0.35 * p_t
                self.droplet_squash_y = 1.0 - 0.25 * p_t
                self.droplet_x_offset = -12.0 * p_t
                self.droplet_scale = 1.0 - 0.15 * p_t
                self.droplet_alpha = self.droplet_scale
            # 阶段二：70ms ~ 110ms 触壁消融
            elif self.absorb_t < 0.11:
                p_t = (self.absorb_t - 0.07) / 0.04
                self.droplet_squash_x = 1.35 - 0.35 * p_t
                self.droplet_squash_y = 0.75 + 0.25 * p_t
                self.droplet_x_offset = -12.0 - 8.0 * p_t
                self.droplet_scale = max(0.0, 0.85 * (1.0 - p_t))
                self.droplet_alpha = self.droplet_scale
            else:
                # 触壁完成时刻：水滴完全消失，并赋予主岛右侧果冻溢出冲击！
                self.is_absorbing = False
                self.droplet_scale = 0.0
                self.droplet_target_scale = 0.0
                self.droplet_alpha = 0.0
                self.droplet_squash_x = 1.0
                self.droplet_squash_y = 1.0
                self.droplet_x_offset = -12.0
                self.impact_vel_w = 110.0   # 注入 +5~6px 果冻弹性冲击速度
                if hasattr(self, "halo_timer") and self.halo_timer.isActive():
                    self.halo_timer.stop()
                self.update_mask()
        else:
            # 常规副岛水滴分离动力学 (response=0.22, damping=0.68)
            omega_d = 6.283185 / 0.22
            k_d = omega_d * omega_d
            c_d = 2.0 * 0.68 * omega_d

            f_ds = -k_d * (self.droplet_scale - self.droplet_target_scale) - c_d * self.droplet_vel_scale
            self.droplet_vel_scale += f_ds * dt
            self.droplet_scale += self.droplet_vel_scale * dt

            target_dx = 0.0 if self.droplet_target_scale > 0.5 else -12.0
            f_dx = -k_d * (self.droplet_x_offset - target_dx) - c_d * self.droplet_vel_x
            self.droplet_vel_x += f_dx * dt
            self.droplet_x_offset += self.droplet_vel_x * dt

            self.droplet_alpha = max(0.0, min(1.0, self.droplet_scale))

            ds_diff = abs(self.droplet_scale - self.droplet_target_scale)
            vs_diff = abs(self.droplet_vel_scale)
            if ds_diff < 0.01 and vs_diff * dt < 0.01:
                self.droplet_scale = self.droplet_target_scale
                self.droplet_vel_scale = 0.0
                self.droplet_x_offset = target_dx
                self.droplet_vel_x = 0.0
                self.droplet_alpha = self.droplet_target_scale

        # 5. 水滴连通器药丸膨胀动力学求解器 (response=0.22, damping=0.72)
        omega_exp = 6.283185 / 0.22
        k_exp = omega_exp * omega_exp
        c_exp = 2.0 * 0.72 * omega_exp
        f_exp = -k_exp * (self.droplet_expand_w - self.droplet_target_expand_w) - c_exp * self.droplet_vel_expand
        self.droplet_vel_expand += f_exp * dt
        self.droplet_expand_w += self.droplet_vel_expand * dt
        if abs(self.droplet_expand_w - self.droplet_target_expand_w) < 0.2 and abs(self.droplet_vel_expand) < 0.5:
            self.droplet_expand_w = self.droplet_target_expand_w
            self.droplet_vel_expand = 0.0

        # 6. 沉寂与稳态检测
        dw = abs(self.current_w - self.target_w)
        dh = abs(self.current_h - self.target_h)
        vw = abs(self.vel_w)
        vh = abs(self.vel_h)
        island_settled = (dw < 0.2 and dh < 0.2 and vw < 0.6 and vh < 0.6)
        if island_settled:
            self.current_w = self.target_w
            self.current_h = self.target_h
            self.vel_w = 0.0
            self.vel_h = 0.0

        droplet_settled = (not self.is_absorbing and self.droplet_scale == self.droplet_target_scale and self.droplet_vel_scale == 0.0)
        impact_settled = (self.impact_w == 0.0 and self.impact_vel_w == 0.0)
        flip_settled = (self.text_flip == self.target_text_flip and self.text_flip_vel == 0.0)
        expand_settled = (self.droplet_expand_w == self.droplet_target_expand_w and self.droplet_vel_expand == 0.0)

        if island_settled and droplet_settled and impact_settled and flip_settled and expand_settled:
            self.spring_timer.stop()
            self.update_mask()
            self.update()
            if self.on_spring_finished_cb:
                cb = self.on_spring_finished_cb
                self.on_spring_finished_cb = None
                cb()
            if self.droplet_target_scale > 0.5 or (self.is_minimal_mode and self.metrics.get("is_busy", False)):
                if not self.halo_timer.isActive():
                    self.halo_timer.start(40)
            else:
                if self.halo_timer.isActive():
                    self.halo_timer.stop()
            return

        self.update()

    def setup_worker(self):
        self.worker = BackgroundMetricsWorker()
        self.worker.metrics_signal.connect(self.on_metrics_updated)
        self.worker.running_signal.connect(self.on_running_state_changed)
        self.worker.start()

    def on_running_state_changed(self, running):
        state_changed = (running != getattr(self, "last_running", None))
        self.last_running = running

        # 用户手动通过托盘或操作隐藏时，绝不自动弹窗打扰
        if getattr(self, "is_manually_hidden", False):
            return

        if self.cfg.get("auto_hide", True) and state_changed:
            if running and self.isHidden():
                self.show()
                self.make_topmost()
            elif not running and not self.isHidden():
                self.hide()

    def update_cached_strings(self):
        total_used = self.metrics.get("total_used", 0)
        pct = self.metrics.get("percent", 0.0)
        self.cached_used_str = f"{total_used / 1000:.1f}k"
        self.cached_pct_str = f"{pct:.1f}%"

        cap = TOTAL_CAPACITY
        bar_w = EXPANDED_W - 30.0
        m_w = max(1.0, bar_w * (self.metrics.get("model_tokens", 0) / cap))
        t_w = max(1.0, bar_w * (self.metrics.get("tool_tokens", 0) / cap))
        s_w = max(1.0, bar_w * (self.metrics.get("system_tokens", 0) / cap))
        u_w = max(1.0, bar_w * (self.metrics.get("user_tokens", 0) / cap))
        self.cached_bar_widths = (m_w, t_w, s_w, u_w)

        total = max(1, total_used)
        def fmt(tk):
            k = f"{tk / 1000:.1f}k"
            p_int = round((tk / total) * 100)
            return f"{k} ({p_int}%)"

        self.cached_items = [
            ("思考/回复", fmt(self.metrics.get("model_tokens", 0))),
            ("工具/网页", fmt(self.metrics.get("tool_tokens", 0))),
            ("系统/规范", fmt(self.metrics.get("system_tokens", 0))),
            ("用户提问", fmt(self.metrics.get("user_tokens", 0)))
        ]

    def on_metrics_updated(self, data):
        is_fg = data.get("is_fg", True)
        just_completed = data.get("just_completed", False)
        dur_str = data.get("duration_str", "")

        if not is_fg and just_completed and not self.is_notifying:
            self.trigger_notification(dur_str)

        old_m = self.metrics
        self.metrics = data
        self.update_cached_strings()

        pending_act = data.get("pending_action")
        old_act = old_m.get("pending_action")

        # 当待办在 IDE 中被处理完（old_act 存在且 pending_act 变为 None）
        if old_act and not pending_act:
            if self.target_text_flip > 0.5:
                self.target_text_flip = 0.0
                # 轻微果冻振颤反馈 (Jelly bounce)
                self.impact_vel_w = 60.0
                self.clearMask()
                if not self.spring_timer.isActive():
                    self.spring_timer.start(7)

        # 当检测到待办阻断且处于未展开紧凑态时，驱动副岛水滴分离滑出（前提是用户尚未点击收回常驻）
        p = max(0.0, min(1.0, (self.current_w - COMPACT_W) / float(EXPANDED_W - COMPACT_W)))
        if pending_act and p < 0.15:
            if not self.is_absorbing and self.target_text_flip < 0.5:
                if self.droplet_target_scale < 0.9:
                    self.droplet_target_scale = 1.0
                    self.clearMask()
                    if not self.spring_timer.isActive():
                        self.spring_timer.start(7)
                    if not self.halo_timer.isActive():
                        self.halo_timer.start(40)
        elif not pending_act:
            if self.droplet_target_scale > 0.1:
                self.droplet_target_scale = 0.0
                self.clearMask()
                if not self.spring_timer.isActive():
                    self.spring_timer.start(7)

        if self.is_minimal_mode:
            if data.get("is_busy", False):
                if not self.halo_timer.isActive():
                    self.halo_timer.start(40)
            else:
                if self.droplet_target_scale <= 0.5 and self.halo_timer.isActive():
                    self.halo_timer.stop()

        if (
            data.get("conv_id") != old_m.get("conv_id")
            or data.get("project_name") != old_m.get("project_name")
            or data.get("percent") != old_m.get("percent")
            or data.get("total_used") != old_m.get("total_used")
            or data.get("is_busy") != old_m.get("is_busy")
            or pending_act != old_act
        ):
            self.update_mask()
            self.update()
        self.update_tray_icon()

        # 边缘贴靠灵动收缩豁免判定：若忙碌或待办阻断，强制滑出置顶展示；若空闲，调度 4 秒贴顶收缩
        if data.get("is_busy") or pending_act:
            if getattr(self, "is_tucked", False):
                self.untuck()
            if hasattr(self, "tuck_countdown_timer"):
                self.tuck_countdown_timer.stop()
        else:
            self.schedule_auto_tuck()

    def trigger_notification(self, duration_str=""):
        if self.is_mouse_inside or self.current_w > 250:
            return

        self.is_notifying = True
        self.notify_duration_str = duration_str or ""
        self.collapse_timer.stop()
        self.notify_collapse_timer.stop()

        self.start_spring_animation(NOTIFY_W, COMPACT_H, response=0.22, damping_ratio=0.75)
        delay = 4000 if self.is_minimal_mode else 3200
        self.notify_collapse_timer.start(delay)

    def collapse_notification(self):
        if self.is_mouse_inside:
            return
        self.notify_collapse_timer.stop()

        def on_done():
            self.is_notifying = False
            self.update_mask()
            self.update()

        target_w = 30.0 if self.is_minimal_mode else COMPACT_W
        target_h = 30.0 if self.is_minimal_mode else COMPACT_H
        self.start_spring_animation(target_w, target_h, response=0.18, damping_ratio=0.92, on_finished=on_done)

    def enterEvent(self, event):
        self.is_mouse_inside = True
        self.notify_collapse_timer.stop()
        self.collapse_timer.stop()
        if hasattr(self, "tuck_countdown_timer"):
            self.tuck_countdown_timer.stop()
        if getattr(self, "is_tucked", False):
            self.untuck()

        if self.is_minimal_mode:
            super().enterEvent(event)
            return

        pos = self.mapFromGlobal(QCursor.pos())
        px, py = pos.x(), pos.y()
        d_rect = self.get_droplet_rect()
        c_rect = self.get_capsule_rect()

        in_droplet = bool(self.droplet_scale > 0.3 and d_rect.adjusted(-5, -5, 5, 5).contains(px, py))
        in_capsule = c_rect.contains(px, py) and not in_droplet

        if in_droplet:
            self.is_hovering_droplet = True
            self.droplet_exit_debounce_timer.stop()
            # 划过不立即形变！启动 60ms 意图防误触定时器
            if self.droplet_target_expand_w < 10.0 and not self.is_absorbing and self.target_text_flip < 0.5:
                self.droplet_hover_intent_timer.start(60)
            self.update()
        elif in_capsule:
            self.is_hovering_droplet = False
            self.droplet_hover_intent_timer.stop()
            self.auto_flyout_timer.stop()
            self.droplet_exit_debounce_timer.stop()
            if hasattr(self, "action_flyout") and self.action_flyout.isVisible() and not self.action_flyout.is_closing:
                self.action_flyout.dismiss(fast=True)
            self.raise_()
            self.droplet_target_expand_w = 0.0
            if self.droplet_target_scale > 0.1:
                self.droplet_target_scale = 0.0
                self.clearMask()
                if not self.spring_timer.isActive():
                    self.spring_timer.start(7)
            self.start_spring_animation(EXPANDED_W, EXPANDED_H, response=0.22, damping_ratio=0.72)

        super().enterEvent(event)

    def leaveEvent(self, event):
        self.is_mouse_inside = False
        self.is_notifying = False
        self.is_hovering_droplet = False
        self.droplet_hover_intent_timer.stop()

        if self.is_minimal_mode:
            self.minimal_hover_alpha = 0.0
            self.update_mask()
            self.update()
            super().leaveEvent(event)
            return

        flyout_open = hasattr(self, "action_flyout") and self.action_flyout.isVisible() and not self.action_flyout.is_closing
        if not flyout_open:
            if self.droplet_target_expand_w > 5.0 and not self.is_absorbing:
                self.droplet_exit_debounce_timer.start(160)
        else:
            # 二级操作卡片正在显示，不收拢副岛，保持展开
            pass

        pill_open = hasattr(self, "pill_bar") and self.pill_bar.isVisible()
        if not pill_open and not flyout_open:
            self.collapse_timer.start(90)
            self.schedule_auto_tuck()

        super().leaveEvent(event)

    def mouseMoveEvent(self, event):
        if self.is_minimal_mode and not self.is_notifying:
            pt = event.position()
            rect = self.get_capsule_rect()
            in_min = rect.adjusted(-4, -4, 4, 4).contains(pt.x(), pt.y())
            old_h = (self.minimal_hover_alpha > 0.5)
            self.minimal_hover_alpha = 1.0 if in_min else 0.0
            if in_min != old_h:
                self.update_mask()
                self.update()
            super().mouseMoveEvent(event)
            return

        pt = event.position()
        px, py = pt.x(), pt.y()
        c_rect = self.get_capsule_rect()
        d_rect = self.get_droplet_rect()

        # 水滴副岛检测范围（滞后防抖设计）：
        # 若已处于展开态，扩大水平与垂直容差，涵盖间隙与向下方二级卡片的过渡安全通道
        if self.droplet_target_expand_w > 50.0:
            in_droplet = bool(
                self.droplet_scale > 0.3 and
                (px >= min(d_rect.left() - 6.0, c_rect.right() - 2.0)) and
                (px <= max(d_rect.right() + 10.0, 290.0)) and
                (c_rect.top() - 6.0 <= py <= c_rect.bottom() + 10.0)
            )
        else:
            droplet_hover_rect = d_rect.adjusted(-5, -5, 5, 5)
            in_droplet = bool(self.droplet_scale > 0.3 and droplet_hover_rect.contains(px, py))

        in_capsule = c_rect.contains(px, py) and not in_droplet

        old_hover = self.is_hovering_droplet
        self.is_hovering_droplet = in_droplet

        # 提前感知移向主岛意图：
        # 如果卡片开着，而鼠标在向左移动（离开副岛主体并靠近主岛区域）：
        if hasattr(self, "action_flyout") and self.action_flyout.isVisible() and not self.action_flyout.is_closing:
            if px < d_rect.left() + 8.0:
                self.action_flyout.dismiss(fast=True)
                self.raise_()
                if self.droplet_target_expand_w > 5.0:
                    self.droplet_target_expand_w = 0.0

        if in_droplet:
            # 鼠标在水滴副岛：停止退出去抖
            self.droplet_exit_debounce_timer.stop()
            # 若尚未展开，启动意图防误触定时器 (60ms 停留后才展开)
            if self.droplet_target_expand_w < 10.0 and not self.is_absorbing and self.target_text_flip < 0.5:
                if not self.droplet_hover_intent_timer.isActive():
                    self.droplet_hover_intent_timer.start(60)
        else:
            # 鼠标不在水滴副岛：取消意图展开定时器
            self.droplet_hover_intent_timer.stop()
            # 若处于展开状态，启动 160ms 缓冲去抖，杜绝微小晃动弹来弹去
            if self.droplet_target_expand_w > 10.0 and not self.is_absorbing:
                flyout_open = hasattr(self, "action_flyout") and self.action_flyout.isVisible() and not self.action_flyout.is_closing
                if not flyout_open and not self.droplet_exit_debounce_timer.isActive():
                    self.droplet_exit_debounce_timer.start(160)

        if in_capsule:
            # 鼠标滑入主岛大屏区：取消副岛的所有未结定时器与展开，顺畅展开主岛指标大屏
            self.droplet_hover_intent_timer.stop()
            self.auto_flyout_timer.stop()
            self.droplet_exit_debounce_timer.stop()
            if hasattr(self, "action_flyout") and self.action_flyout.isVisible() and not self.action_flyout.is_closing:
                self.action_flyout.dismiss(fast=True)
            self.raise_()
            if self.droplet_target_expand_w > 5.0:
                self.droplet_target_expand_w = 0.0
            if self.target_w < EXPANDED_W - 5.0:
                if self.droplet_target_scale > 0.1:
                    self.droplet_target_scale = 0.0
                    if not self.spring_timer.isActive():
                        self.clearMask()
                        self.spring_timer.start(7)
                self.start_spring_animation(EXPANDED_W, EXPANDED_H, response=0.22, damping_ratio=0.72)

        if self.is_hovering_droplet != old_hover:
            self.update()

        super().mouseMoveEvent(event)

    def start_collapse(self):
        if self.is_mouse_inside:
            return
        if hasattr(self, "pill_bar") and self.pill_bar.isVisible():
            # 药丸栏仍在显示或退场动画中，主岛必须等待其彻底消失后才能收缩！
            return
        if self.is_minimal_mode:
            self.start_spring_animation(30.0, 30.0, response=0.18, damping_ratio=0.90)
            return
        # 折叠回紧凑态：若存在待办阻断且用户尚未点击收回常驻，副岛水滴平滑重新分离滑出
        if self.metrics.get("pending_action") and self.target_text_flip < 0.5:
            self.droplet_target_scale = 1.0
            self.clearMask()
            if not self.spring_timer.isActive():
                self.spring_timer.start(7)

        self.start_spring_animation(COMPACT_W, COMPACT_H, response=0.18, damping_ratio=0.90)

    # -------------------------------------------------------------
    # 交互：右键呼出 MiniPillBar (绝对沉稳无抖动)，左键唤醒/拖拽
    # -------------------------------------------------------------
    def mousePressEvent(self, event):
        rect = self.get_capsule_rect()

        # 若处于贴顶收缩微刘海态，任何点击立即瞬间滑落展开
        if getattr(self, "is_tucked", False):
            self.untuck(fast=True)
            rect = self.get_capsule_rect()
        # 最小微圆模式交互：左键或右键点击微圆，立即退出最小状态恢复为标准灵动岛
        if self.is_minimal_mode and not self.is_notifying:
            pt = event.position()
            if rect.adjusted(-4, -4, 4, 4).contains(pt.x(), pt.y()):
                self.exit_minimal_mode()
                event.accept()
                return

        # =========================================================
        # 右键：灵动岛主屏保持绝对沉稳（零抖动），呼出阶梯落体弹跳微药丸
        # =========================================================
        if event.button() == Qt.MouseButton.RightButton:
            if self.pill_bar.isVisible() and not self.pill_bar.is_closing:
                self.pill_bar.dismiss()
                self.hover_bridge_timer.stop()
                event.accept()
                return

            # 精确计算正下方弹出位置 (灵动岛本体完全不动，零形变抖动)
            screen_center_x = self.x() + CANVAS_W / 2.0
            screen_bottom_y = self.y() + PADDING_TOP + rect.height()

            # 呼出药丸栏并启动鼠标移出桥接监控
            self.pill_bar.popup(screen_center_x, screen_bottom_y + 5.0)
            self.hover_bridge_timer.start(60)
            event.accept()
            return

        # =========================================================
        # 左键：一键唤醒 IDE 或自由拖拽
        # =========================================================
        if event.button() == Qt.MouseButton.LeftButton:
            pt = event.position()
            d_rect = self.get_droplet_rect()

            if self.pill_bar.isVisible():
                self.pill_bar.dismiss()

            # 若点击主岛其它区域且二级操作卡片正在显示，则关闭卡片
            if hasattr(self, "action_flyout") and self.action_flyout.isVisible() and not d_rect.contains(pt.x(), pt.y()):
                self.action_flyout.dismiss()

            # 点击水滴副岛检测：平滑落体呼出/折叠二级微悬浮操作卡片 (ActionFlyoutCard)
            if self.droplet_scale > 0.4 and d_rect.contains(pt.x(), pt.y()):
                if hasattr(self, "action_flyout") and self.action_flyout.isVisible() and not self.action_flyout.is_closing:
                    self.action_flyout.dismiss()
                else:
                    drop_center_x = self.x() + d_rect.x() + d_rect.width() / 2.0
                    drop_bottom_y = self.y() + d_rect.bottom()
                    self.action_flyout.popup(drop_center_x, drop_bottom_y + 4.0, self.metrics)
                    self.hover_bridge_timer.start(60)
                event.accept()
                return

            orig_win_x = self.x()
            orig_win_y = self.y()

            self.clearMask()
            ctypes.windll.user32.ReleaseCapture()
            ctypes.windll.user32.SendMessageW(int(self.winId()), 0x00A1, 2, 0)

            rect_win = ctypes.wintypes.RECT()
            ctypes.windll.user32.GetWindowRect(int(self.winId()), ctypes.byref(rect_win))
            dpr = self.devicePixelRatioF() or 1.0
            cur_win_x = rect_win.left / dpr
            cur_win_y = rect_win.top / dpr

            dx = abs(cur_win_x - orig_win_x)
            dy = abs(cur_win_y - orig_win_y)

            if dx < 4 and dy < 4:
                bring_antigravity_to_foreground()
                if self.is_notifying:
                    self.collapse_notification()
                self.update_mask()
                event.accept()
                return

            # 获取拖拽后窗口中心点所在的显示器
            center_x = int(cur_win_x + CANVAS_W / 2.0)
            center_y = int(cur_win_y + CANVAS_H / 2.0)
            target_scr = QApplication.screenAt(QPoint(center_x, center_y))
            if not target_scr:
                target_scr = QApplication.screenAt(QCursor.pos())
            if not target_scr:
                target_scr = QApplication.primaryScreen()

            avail = target_scr.availableGeometry()

            capsule_x = cur_win_x + (CANVAS_W - COMPACT_W) / 2.0
            capsule_y = cur_win_y + PADDING_TOP

            # 顶部磁吸判定：如果距离当前显示器可用顶边在 [0, 28] 像素以内，自动磁吸到 top + 12px
            rel_y = capsule_y - avail.top()
            if 0 <= rel_y < 28:
                capsule_y = avail.top() + 12.0

            # 边界约束到该屏幕可用区域内，彻底支持副屏负坐标
            min_c_x = avail.left()
            max_c_x = avail.left() + avail.width() - COMPACT_W
            capsule_x = max(min_c_x, min(capsule_x, max_c_x))

            min_c_y = avail.top()
            max_c_y = avail.top() + avail.height() - COMPACT_H
            capsule_y = max(min_c_y, min(capsule_y, max_c_y))

            final_win_x = int(capsule_x - (CANVAS_W - COMPACT_W) / 2.0)
            final_win_y = int(capsule_y - PADDING_TOP)

            self.move(final_win_x, final_win_y)
            self.base_win_y = final_win_y
            self.tuck_y_offset = 0.0
            self.is_tucked = False

            self.cfg["x"] = int(capsule_x)
            self.cfg["y"] = int(capsule_y)
            save_config(self.cfg)
            self.update_mask()
            self.update()
            self.schedule_auto_tuck()
            event.accept()

    def reset_to_center(self, target_screen=None):
        if target_screen is None:
            target_screen = self.get_target_screen()
        if not target_screen:
            target_screen = QApplication.primaryScreen()

        avail = target_screen.availableGeometry()
        capsule_x = avail.left() + (avail.width() - COMPACT_W) // 2
        capsule_y = avail.top() + 12
        win_x = int(capsule_x - (CANVAS_W - COMPACT_W) / 2.0)
        win_y = int(capsule_y - PADDING_TOP)

        self.cfg["x"] = capsule_x
        self.cfg["y"] = capsule_y
        save_config(self.cfg)

        self.move(win_x, win_y)
        self.base_win_y = win_y
        self.tuck_y_offset = 0.0
        self.is_tucked = False
        self.make_topmost()
        self.update_mask()
        self.update()
        self.schedule_auto_tuck()

    def clean_exit(self):
        global _GLOBAL_MUTEX_HANDLE
        if _GLOBAL_MUTEX_HANDLE:
            try:
                ctypes.windll.kernel32.CloseHandle(_GLOBAL_MUTEX_HANDLE)
            except Exception:
                pass
            _GLOBAL_MUTEX_HANDLE = None
        if hasattr(self, "ipc_server") and self.ipc_server:
            try:
                self.ipc_server.close()
                QLocalServer.removeServer(IPC_PIPE_NAME)
            except Exception:
                pass
        if hasattr(self, "tray_icon") and self.tray_icon:
            self.tray_icon.hide()
        if hasattr(self, "halo_timer") and self.halo_timer.isActive():
            self.halo_timer.stop()
        if hasattr(self, "hover_bridge_timer") and self.hover_bridge_timer.isActive():
            self.hover_bridge_timer.stop()
        if hasattr(self, "pill_bar"):
            self.pill_bar.close()
        if hasattr(self, "action_flyout"):
            self.action_flyout.close()
        if hasattr(self, "spring_timer") and self.spring_timer.isActive():
            self.spring_timer.stop()
        if hasattr(self, "worker") and self.worker.isRunning():
            self.worker.stop()
        QApplication.quit()

    def closeEvent(self, event):
        self.clean_exit()
        super().closeEvent(event)

    # -------------------------------------------------------------
    # 灵动岛纯正渲染绘制管线
    # -------------------------------------------------------------
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        rect = self.get_capsule_rect()
        w = rect.width()
        h = rect.height()

        p = max(0.0, min(1.0, (w - COMPACT_W) / float(EXPANDED_W - COMPACT_W)))
        radius = 15.0 + 5.0 * p

        # 纯黑深邃背景
        painter.setBrush(QBrush(QColor(9, 9, 11, 255)))

        # 苹果级物理光影：定向发丝微渐变边框 (顶部微高光发丝，底部自然微隐，拒绝生硬平切)
        grad_pen = QLinearGradient(rect.left(), rect.top(), rect.left(), rect.bottom())
        top_alpha = int(78 + 32 * p)   # 顶部微白发丝光 (~30%-43% 透明度)
        mid_alpha = int(45 + 18 * p)   # 中腰自然过渡 (~18%-25% 透明度)
        bot_alpha = int(18 + 12 * p)   # 底部幽深微隐 (~7%-12% 透明度)
        grad_pen.setColorAt(0.0, QColor(255, 255, 255, top_alpha))
        grad_pen.setColorAt(0.45, QColor(255, 255, 255, mid_alpha))
        grad_pen.setColorAt(1.0, QColor(255, 255, 255, bot_alpha))
        painter.setPen(QPen(QBrush(grad_pen), 1.15))
        painter.drawRoundedRect(rect, radius, radius)

        # 边缘贴靠灵动收缩态：在底边露出 3px 区域正中央绘制 1.2px 发丝状态冷光纤芯 (Notch Optic Core)
        if getattr(self, "is_tucked", False) or self.tuck_y_offset < -5.0:
            is_busy = bool(self.metrics.get("is_busy", False))
            pending_act = self.metrics.get("pending_action")
            if pending_act == "ask_question":
                optic_color = QColor(245, 158, 11, 230)  # 琥珀橙
            elif pending_act == "plan_approval":
                optic_color = QColor(59, 130, 246, 230)   # 宝石蓝
            elif is_busy:
                optic_color = QColor(56, 189, 248, 230)   # 天空蓝
            else:
                optic_color = QColor(16, 185, 129, 220)   # 翡翠绿

            core_w = 48.0
            core_rect = QRectF(rect.center().x() - core_w / 2.0, rect.bottom() - 2.2, core_w, 1.2)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(optic_color))
            painter.drawRoundedRect(core_rect, 0.6, 0.6)

        top_left_x = rect.x()
        top_left_y = rect.y()

        # =========================================================
        # A. 离焦任务完成通知态 (is_notifying)
        # =========================================================
        if self.is_notifying and p < 0.4:
            badge_center = QPointF(top_left_x + 17.0, top_left_y + h / 2.0)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(16, 185, 129, 230)))
            painter.drawEllipse(badge_center, 6.5, 6.5)

            painter.setPen(QPen(QColor(255, 255, 255), 1.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            p1 = QPointF(badge_center.x() - 2.8, badge_center.y())
            p2 = QPointF(badge_center.x() - 0.8, badge_center.y() + 2.4)
            p3 = QPointF(badge_center.x() + 3.2, badge_center.y() - 2.2)
            painter.drawLine(p1, p2)
            painter.drawLine(p2, p3)

            painter.setFont(self.f_notify)
            painter.setPen(QColor(244, 244, 245, 255))
            notify_text = f"任务完成 · {self.notify_duration_str}" if self.notify_duration_str else "任务已完成"
            painter.drawText(QRectF(top_left_x + 30.0, top_left_y, w - 38.0, h), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, notify_text)
            return

        # =========================================================
        # 0. 最小状态 (极简微圆模式: 30px 居中微圆 + 环形进度圈 + 状态微点 + 悬停气泡)
        # =========================================================
        if self.is_minimal_mode and not self.is_notifying:
            pct_val = float(self.metrics.get("percent", 0.0))
            is_busy = bool(self.metrics.get("is_busy", False))
            cx = rect.center().x()
            cy = rect.center().y()

            # 1. 环形进度条 (底轨 + 前景动态弧)
            ring_r = 10.5
            ring_rect = QRectF(cx - ring_r, cy - ring_r, ring_r * 2.0, ring_r * 2.0)

            # 暗轨底环
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor(255, 255, 255, 32), 1.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawEllipse(ring_rect)

            # 进度颜色梯级
            if pct_val < 60.0:
                arc_color = QColor(16, 185, 129, 230)
            elif pct_val < 85.0:
                arc_color = QColor(245, 158, 11, 235)
            else:
                arc_color = QColor(239, 68, 68, 240)

            if pct_val > 0.5:
                painter.setPen(QPen(arc_color, 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                span_angle = -int((min(100.0, max(0.0, pct_val)) / 100.0) * 360.0 * 16.0)
                painter.drawArc(ring_rect, 90 * 16, span_angle)

            # 2. 中心状态微点
            if is_busy:
                # 忙碌运行中：围绕中心半径 4.2px 轨道旋转的高亮微点
                rot = (time.perf_counter() * 4.5) % (2.0 * math.pi)
                orbit_r = 4.2
                dot_x = cx + orbit_r * math.cos(rot)
                dot_y = cy + orbit_r * math.sin(rot)
                # 中心极微弱锚点
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(QColor(255, 255, 255, 90)))
                painter.drawEllipse(QPointF(cx, cy), 1.0, 1.0)
                # 轨道旋转微星
                painter.setBrush(QBrush(QColor(56, 189, 248, 240)))
                painter.drawEllipse(QPointF(dot_x, dot_y), 1.6, 1.6)
            else:
                # 空闲待机：中心精致微点
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(QColor(255, 255, 255, 130)))
                painter.drawEllipse(QPointF(cx, cy), 1.8, 1.8)

            # 3. 悬停浮动气泡徽章 (Hover Floating Badge)
            if self.minimal_hover_alpha > 0.01:
                badge_font = QFont("Segoe UI Variable Display", 8, QFont.Weight.Medium)
                if not badge_font.exactMatch():
                    badge_font = QFont("Segoe UI", 8, QFont.Weight.Medium)
                fm = QFontMetrics(badge_font)
                status_desc = "运行中" if is_busy else "待机"
                badge_text = f"{pct_val:.1f}% · {status_desc}"
                txt_w = fm.horizontalAdvance(badge_text)
                badge_w = txt_w + 16.0
                badge_h = 20.0
                badge_x = cx - badge_w / 2.0
                badge_y = rect.bottom() + 6.0
                badge_rect = QRectF(badge_x, badge_y, badge_w, badge_h)

                # 徽章半透明胶囊背景
                painter.setPen(QPen(QColor(255, 255, 255, 40), 1.0))
                painter.setBrush(QBrush(QColor(18, 18, 22, 235)))
                painter.drawRoundedRect(badge_rect, 10.0, 10.0)

                # 徽章文字
                painter.setFont(badge_font)
                painter.setPen(QColor(228, 228, 231, 240))
                painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, badge_text)

            return

        # =========================================================
        # B. 常规紧凑模式绘制 (p < 0.7)
        # =========================================================
        if p < 0.7:
            alpha = int(255 * (1.0 - p / 0.7))
            proj = self.metrics.get("project_name", "Antigravity")
            is_busy = self.metrics.get("is_busy", False)
            pct_val = float(self.metrics.get("percent", 0.0))

            # 1. 智能动态状态配色 (若处于待办翻转常驻中，平滑融合待办警示色)
            if pct_val < 60.0:
                base_color = QColor(16, 185, 129, alpha)
            elif pct_val < 85.0:
                base_color = QColor(245, 158, 11, alpha)
            else:
                base_color = QColor(239, 68, 68, alpha)

            pending_act = self.metrics.get("pending_action")
            tf = min(1.0, max(0.0, self.text_flip))
            if pending_act == "ask_question":
                pending_color = QColor(245, 158, 11)   # 琥珀橙
                tip_prefix = "待回答"
            elif pending_act == "plan_approval":
                pending_color = QColor(59, 130, 246)   # 宝石蓝
                tip_prefix = "待审批"
            else:
                pending_color = QColor(239, 68, 68)    # 珊瑚红
                tip_prefix = "待处理"

            if tf > 0.001 and pending_act:
                r_blend = int(base_color.red() * (1.0 - tf) + pending_color.red() * tf)
                g_blend = int(base_color.green() * (1.0 - tf) + pending_color.green() * tf)
                b_blend = int(base_color.blue() * (1.0 - tf) + pending_color.blue() * tf)
                color_theme = QColor(r_blend, g_blend, b_blend, alpha)
            else:
                color_theme = base_color

            # 2. 收缩变形比例与淡出系数 (主岛从 182px 收缩为 30px 正圆圆环微岛)
            # p_shrink: 0.0(未压缩 182px) -> 1.0(完全压缩 30px 正圆)
            p_shrink = max(0.0, min(1.0, (COMPACT_W - w) / (COMPACT_W - 30.0)))
            # text_fade: 当 w 从 160px 收缩至 75px 时平滑淡出，w <= 75px 完全隐去绝不绘制，根除白色断条
            text_fade = max(0.0, min(1.0, (w - 75.0) / 85.0))

            # 3. 左侧状态冷光宝石指示灯 (伴随 text_fade 淡出)
            if text_fade > 0.02:
                dot_alpha = int(alpha * text_fade)
                center_pt = QPointF(top_left_x + 15.0, top_left_y + h / 2.0)
                painter.setPen(Qt.PenStyle.NoPen)
                if is_busy:
                    painter.setBrush(QBrush(QColor(color_theme.red(), color_theme.green(), color_theme.blue(), int(dot_alpha * 0.35))))
                    painter.drawEllipse(center_pt, 5.5, 5.5)

                # 底座微凹槽发丝暗圈 (提升嵌入感与立体感)
                groove_alpha = int(dot_alpha * 0.55)
                painter.setBrush(QBrush(QColor(0, 0, 0, groove_alpha)))
                painter.drawEllipse(center_pt, 4.3, 4.3)

                # 宝石冷光主体核心 (3.4px)
                painter.setBrush(QBrush(QColor(color_theme.red(), color_theme.green(), color_theme.blue(), dot_alpha)))
                painter.drawEllipse(center_pt, 3.4, 3.4)

                # 内部偏上冷光透镜微反光 (1.1px 微白晶核)
                lens_pt = QPointF(center_pt.x() - 0.7, center_pt.y() - 0.8)
                lens_alpha = int(dot_alpha * 0.55)
                painter.setBrush(QBrush(QColor(255, 255, 255, lens_alpha)))
                painter.drawEllipse(lens_pt, 1.1, 1.1)

            # 4. 百分比圆环指示器 (Circular Ring Progress: 苹果腕表内嵌凹槽 + 流光游标端点)
            ring_cx_normal = top_left_x + w - 18.0
            ring_cx_centered = top_left_x + 15.0
            ring_cx = ring_cx_normal * (1.0 - p_shrink) + ring_cx_centered * p_shrink
            ring_cy = top_left_y + h / 2.0
            ring_r = 6.2 + 0.6 * p_shrink   # 30px 圆里为 6.8px 外半径，居中饱满精致
            ring_rect = QRectF(ring_cx - ring_r, ring_cy - ring_r, ring_r * 2.0, ring_r * 2.0)

            # 内嵌凹槽暗轨底层 (Groove Depth Track)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            groove_pen = QPen(QColor(0, 0, 0, int(alpha * 0.45)), 2.6)
            painter.setPen(groove_pen)
            painter.drawEllipse(QPointF(ring_cx, ring_cy), ring_r, ring_r)

            # 底环 (Track) - 半透明物理发丝微轨
            track_pen = QPen(QColor(255, 255, 255, int(alpha * 0.15)), 1.6)
            painter.setPen(track_pen)
            painter.drawEllipse(QPointF(ring_cx, ring_cy), ring_r, ring_r)

            # 进度弧 (Progress Arc) - 12点钟顺时针展开，圆润笔触 + 游标端点微高光
            if pct_val > 0.4:
                prog_pen = QPen(color_theme, 1.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
                painter.setPen(prog_pen)
                start_angle = 90 * 16
                clamped_pct = min(100.0, max(0.0, pct_val))
                span_angle = int(-clamped_pct / 100.0 * 360.0 * 16)
                painter.drawArc(ring_rect, start_angle, span_angle)

                # 游标端点微高光 (Cursor Highlight Bead)
                end_rad = (90.0 - (clamped_pct / 100.0 * 360.0)) * (math.pi / 180.0)
                bead_x = ring_cx + ring_r * math.cos(end_rad)
                bead_y = ring_cy - ring_r * math.sin(end_rad)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(QColor(255, 255, 255, int(alpha * 0.85))))
                painter.drawEllipse(QPointF(bead_x, bead_y), 0.9, 0.9)

            # 5. 百分比数值 (主数字清晰突出，% 符号微降 30% 明度并紧凑排列)
            if text_fade > 0.05:
                pct_alpha = int(alpha * text_fade)
                raw_pct = self.cached_pct_str or "0.0%"
                num_part = raw_pct[:-1] if raw_pct.endswith("%") else raw_pct
                has_sym = raw_pct.endswith("%")

                fm_num = QFontMetrics(self.f_pct)
                fm_sym = QFontMetrics(self.f_pct_sym) if hasattr(self, 'f_pct_sym') else fm_num
                w_num = fm_num.horizontalAdvance(num_part)
                w_sym = fm_sym.horizontalAdvance("%") if has_sym else 0
                total_w = w_num + (w_sym + 1 if has_sym else 0)

                area_right = ring_cx - ring_r - 6.0
                start_x = area_right - total_w

                # 绘制主数字
                painter.setFont(self.f_pct)
                painter.setPen(QColor(color_theme.red(), color_theme.green(), color_theme.blue(), pct_alpha))
                num_rect = QRectF(start_x, top_left_y, w_num, h)
                painter.drawText(num_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, num_part)

                # 绘制次级 % 符号 (微缩字号与降低明度)
                if has_sym:
                    sym_alpha = int(pct_alpha * 0.70)
                    painter.setFont(self.f_pct_sym)
                    painter.setPen(QColor(color_theme.red(), color_theme.green(), color_theme.blue(), sym_alpha))
                    sym_rect = QRectF(start_x + w_num + 1.0, top_left_y + 1.0, w_sym + 2.0, h)
                    painter.drawText(sym_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, "%")

            # 6. 中间文字双层垂直滑动翻转 (仅在 text_fade > 0.05 且有足够宽度时绘制，彻底杜绝白条与截断残影)
            if text_fade > 0.05:
                name_max_w = (ring_cx - ring_r - 47.0) - (top_left_x + 26.0)
                if name_max_w > 20:
                    name_rect = QRectF(top_left_x + 26.0, top_left_y, name_max_w, h)
                    painter.save()
                    painter.setClipRect(name_rect)

                    # 层1：原项目名 (向上滑出) - 瑞士柔和白银色排版
                    if tf < 0.99:
                        al_proj = int(alpha * (1.0 - tf) * text_fade)
                        dy_proj = -tf * 18.0
                        painter.setFont(self.f_proj)
                        silver_color = QColor(236, 236, 241, int(al_proj * 0.92))
                        painter.setPen(silver_color)
                        fm = painter.fontMetrics()
                        elided_proj = fm.elidedText(proj, Qt.TextElideMode.ElideRight, int(name_max_w))
                        p_rect = QRectF(name_rect.x(), name_rect.y() + dy_proj, name_rect.width(), name_rect.height())
                        painter.drawText(p_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, elided_proj)

                    # 层2：具体待办提示 (从下方滑入就位)
                    if tf > 0.01:
                        al_pend = int(alpha * tf * text_fade)
                        dy_pend = (1.0 - tf) * 18.0
                        act_tit = self.metrics.get("pending_title") or ""
                        act_det = self.metrics.get("pending_detail") or ""
                        display_str = f"{tip_prefix}: {act_det or act_tit or '请确认'}"
                        painter.setFont(self.f_proj)
                        painter.setPen(QColor(255, 255, 255, al_pend))
                        fm = painter.fontMetrics()
                        elided_pend = fm.elidedText(display_str, Qt.TextElideMode.ElideRight, int(name_max_w))
                        d_rect = QRectF(name_rect.x(), name_rect.y() + dy_pend, name_rect.width(), name_rect.height())
                        painter.drawText(d_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, elided_pend)

                    painter.restore()

        # =========================================================
        # C. 展开指标大屏模式绘制 (p > 0.3)
        # =========================================================
        if p > 0.3:
            alpha = int(255 * ((p - 0.3) / 0.7))
            proj = self.metrics.get("project_name", "Antigravity")
            pending_act = self.metrics.get("pending_action")

            # 顶部第一行标题与指示灯
            head_center = QPointF(top_left_x + 18.0, top_left_y + 18.0)
            painter.setPen(Qt.PenStyle.NoPen)
            if pending_act and self.target_text_flip > 0.5:
                if pending_act == "ask_question":
                    p_dot_c = QColor(245, 158, 11, alpha)
                    act_tit = self.metrics.get("pending_title") or ""
                    act_det = self.metrics.get("pending_detail") or ""
                    header_str = f"待回答 · {act_det or act_tit or '提问交互'}"
                elif pending_act == "plan_approval":
                    p_dot_c = QColor(59, 130, 246, alpha)
                    act_tit = self.metrics.get("pending_title") or ""
                    act_det = self.metrics.get("pending_detail") or ""
                    header_str = f"待审批 · {act_det or act_tit or '方案已就绪'}"
                else:
                    p_dot_c = QColor(239, 68, 68, alpha)
                    header_str = f"待处理 · 任务异常中断"
                painter.setBrush(QBrush(p_dot_c))
            else:
                painter.setBrush(QBrush(QColor(16, 185, 129, alpha)))
                header_str = proj

            painter.drawEllipse(head_center, 3.5, 3.5)

            painter.setFont(self.f_exp_proj)
            painter.setPen(QColor(255, 255, 255, alpha))
            title_max_w = w - 135.0
            fm = painter.fontMetrics()
            elided_header = fm.elidedText(header_str, Qt.TextElideMode.ElideRight, int(title_max_w))
            painter.drawText(QRectF(top_left_x + 28.0, top_left_y + 8.0, title_max_w, 20.0), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, elided_header)

            # 顶部右上角标签（智能根据待办阻断状态 pending_action 展现待办徽章或默认模型）
            tag_rect = QRectF(top_left_x + w - 105.0, top_left_y + 9.0, 92.0, 18.0)
            if pending_act:
                if pending_act == "ask_question":
                    t_bg = QColor(245, 158, 11, int(alpha * 0.22))
                    t_border = QColor(245, 158, 11, int(alpha * 0.7))
                    t_pen = QColor(251, 191, 36, alpha)
                    t_str = "等待回答提问"
                elif pending_act == "plan_approval":
                    t_bg = QColor(59, 130, 246, int(alpha * 0.22))
                    t_border = QColor(59, 130, 246, int(alpha * 0.7))
                    t_pen = QColor(96, 165, 250, alpha)
                    t_str = "等待审批确认"
                else:
                    t_bg = QColor(239, 68, 68, int(alpha * 0.22))
                    t_border = QColor(239, 68, 68, int(alpha * 0.7))
                    t_pen = QColor(248, 113, 113, alpha)
                    t_str = "任务异常中断"

                painter.setPen(QPen(t_border, 1.0))
                painter.setBrush(QBrush(t_bg))
                painter.drawRoundedRect(tag_rect, 9.0, 9.0)

                painter.setFont(self.f_tip)
                painter.setPen(t_pen)
                painter.drawText(tag_rect, Qt.AlignmentFlag.AlignCenter, t_str)
            else:
                painter.setPen(QPen(QColor(255, 255, 255, int(alpha * 0.1)), 1.0))
                painter.setBrush(QBrush(QColor(24, 24, 27, alpha)))
                painter.drawRoundedRect(tag_rect, 9.0, 9.0)

                painter.setFont(self.f_tag)
                painter.setPen(QColor(161, 161, 170, alpha))
                painter.drawText(tag_rect, Qt.AlignmentFlag.AlignCenter, "Gemini 3.8 Flash")

            painter.setFont(self.f_used)
            painter.setPen(QColor(244, 244, 245, alpha))
            used_k = f"{self.metrics.get('total_used', 0) / 1000:.1f}k"
            painter.drawText(QRectF(top_left_x + 15.0, top_left_y + 36.0, 65.0, 18.0), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, used_k)

            painter.setFont(self.f_cap)
            painter.setPen(QColor(113, 113, 122, alpha))
            painter.drawText(QRectF(top_left_x + 60.0, top_left_y + 37.0, 140.0, 18.0), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, "/ 1.05M Tokens")

            painter.setFont(self.f_big_pct)
            painter.setPen(QColor(16, 185, 129, alpha))
            painter.drawText(QRectF(top_left_x + w - 58.0, top_left_y + 35.0, 44.0, 18.0), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, self.cached_pct_str)

            bar_y = top_left_y + 60.0
            bar_h = 4.0
            bar_w = w - 30.0
            bar_bg = QRectF(top_left_x + 15.0, bar_y, bar_w, bar_h)

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(39, 39, 42, alpha)))
            painter.drawRoundedRect(bar_bg, 2.0, 2.0)

            m_w, t_w, s_w, u_w = self.cached_bar_widths
            cur_bx = top_left_x + 15.0
            painter.setBrush(QBrush(QColor(16, 185, 129, alpha)))
            painter.drawRoundedRect(QRectF(cur_bx, bar_y, m_w, bar_h), 2.0, 2.0)
            cur_bx += m_w

            painter.setBrush(QBrush(QColor(245, 158, 11, alpha)))
            painter.drawRoundedRect(QRectF(cur_bx, bar_y, t_w, bar_h), 2.0, 2.0)
            cur_bx += t_w

            painter.setBrush(QBrush(QColor(168, 85, 247, alpha)))
            painter.drawRoundedRect(QRectF(cur_bx, bar_y, s_w, bar_h), 2.0, 2.0)
            cur_bx += s_w

            painter.setBrush(QBrush(QColor(56, 189, 248, alpha)))
            painter.drawRoundedRect(QRectF(cur_bx, bar_y, u_w, bar_h), 2.0, 2.0)

            grid_y = top_left_y + 74.0
            col1_x = top_left_x + 15.0
            col2_x = top_left_x + w / 2.0 + 6.0
            row_h = 24.0

            colors = [self.c_model, self.c_tool, self.c_sys, self.c_user]
            coords = [
                (col1_x, grid_y),
                (col2_x, grid_y),
                (col1_x, grid_y + row_h),
                (col2_x, grid_y + row_h)
            ]

            for i, (name, val_str) in enumerate(self.cached_items):
                x_pos, y_pos = coords[i]
                color_obj = colors[i]

                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(color_obj))
                painter.drawEllipse(QPointF(x_pos + 4.0, y_pos + 8.0), 2.2, 2.2)

                painter.setFont(self.f_lbl)
                painter.setPen(QColor(161, 161, 170, alpha))
                painter.drawText(QRectF(x_pos + 12.0, y_pos, 52.0, 16.0), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, name)

                painter.setFont(self.f_val)
                painter.setPen(QColor(244, 244, 245, alpha))
                painter.drawText(QRectF(x_pos + 66.0, y_pos, 74.0, 16.0), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, val_str)

        # =========================================================
        # D. 灵动双联岛：多任务水滴分离形态绘制
        # =========================================================
        self.draw_droplet_sub_island(painter, p)

    # -------------------------------------------------------------
    # 灵动双联岛：副岛水滴渲染管线与纯矢量微图形 (0 Emoji)
    # -------------------------------------------------------------
    def draw_droplet_sub_island(self, painter, p):
        if self.droplet_alpha <= 0.01 or self.droplet_scale <= 0.01:
            return

        d_rect = self.get_droplet_rect()
        drop_w = d_rect.width()
        dx = d_rect.x()
        dy = d_rect.y()
        scale = max(0.0, min(1.2, self.droplet_scale))
        alpha = max(0.0, min(1.0, self.droplet_alpha))

        act = self.metrics.get("pending_action", "ask_question")
        if act == "ask_question":
            theme_color = QColor(245, 158, 11)   # 琥珀橙
            badge_prefix = "待回答"
        elif act == "plan_approval":
            theme_color = QColor(59, 130, 246)   # 宝石蓝
            badge_prefix = "待审批"
        else:
            theme_color = QColor(239, 68, 68)    # 珊瑚红
            badge_prefix = "待处理"

        painter.save()
        cx = dx + drop_w / 2.0
        cy = dy + 15.0
        painter.translate(cx, cy)
        painter.scale(scale * self.droplet_squash_x, scale * self.droplet_squash_y)
        painter.translate(-cx, -cy)

        # 1. 柔和呼吸脉冲光晕 (自适应水滴药丸圆角矩形，0.8Hz 纯视觉呼吸)
        t = time.time()
        halo = (math.sin(t * 5.0) + 1.0) * 0.5
        halo_alpha = int(alpha * (18 + 26 * halo))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(theme_color.red(), theme_color.green(), theme_color.blue(), halo_alpha)))
        painter.drawRoundedRect(d_rect.adjusted(-2, -2, 2, 2), 17.0, 17.0)

        # 2. 深炭黑磨砂副岛胶囊药丸 (高 30px，两端圆角 15px)
        painter.setBrush(QBrush(QColor(10, 10, 12, int(248 * alpha))))
        border_alpha = int(210 * alpha) if self.is_hovering_droplet else int(65 * alpha)
        painter.setPen(QPen(QColor(theme_color.red(), theme_color.green(), theme_color.blue(), border_alpha), 1.0))
        painter.drawRoundedRect(d_rect, 15.0, 15.0)

        # 3. 左侧纯矢量微图标绘制 (始终居中锚定在左端 15px 处)
        icon_cx = dx + 15.0
        icon_cy = dy + 15.0
        icon_alpha = int(255 * alpha)
        if act == "ask_question":
            self.draw_vector_bubble_question(painter, icon_cx, icon_cy, theme_color, icon_alpha)
        elif act == "plan_approval":
            self.draw_vector_shield(painter, icon_cx, icon_cy, theme_color, icon_alpha)
        else:
            self.draw_vector_alert(painter, icon_cx, icon_cy, theme_color, icon_alpha)

        # 4. 中间待办文本展开平滑淡入 (当膨胀宽度 > 15px 时激活)
        if self.droplet_expand_w > 15.0:
            p_exp = max(0.0, min(1.0, (self.droplet_expand_w - 15.0) / 95.0))
            text_alpha = int(255 * alpha * p_exp)
            if text_alpha > 5:
                act_tit = self.metrics.get("pending_title") or ""
                act_det = self.metrics.get("pending_detail") or ""
                tip_text = f"{badge_prefix}: {act_det or act_tit or '等待确认'}"

                text_rect = QRectF(dx + 30.0, dy, drop_w - 44.0, 30.0)
                painter.setFont(self.f_tip)
                painter.setPen(QColor(244, 244, 245, text_alpha))
                fm = painter.fontMetrics()
                elided_t = fm.elidedText(tip_text, Qt.TextElideMode.ElideRight, int(text_rect.width()))
                painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, elided_t)

                # 右端微光呼吸小圆点
                if p_exp > 0.7:
                    dot_a = int(alpha * (p_exp - 0.7) / 0.3 * 220)
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.setBrush(QBrush(QColor(theme_color.red(), theme_color.green(), theme_color.blue(), dot_a)))
                    painter.drawEllipse(QPointF(dx + drop_w - 10.0, dy + 15.0), 2.0, 2.0)

        painter.restore()

    def draw_vector_bubble_question(self, painter, cx, cy, color, alpha):
        """纯矢量问号 (精巧三阶贝塞尔曲线 + 底部微圆点)"""
        pen = QPen(QColor(color.red(), color.green(), color.blue(), alpha), 1.4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        path = QPainterPath()
        path.moveTo(cx - 2.8, cy - 3.2)
        path.cubicTo(cx - 2.8, cy - 6.2, cx + 2.8, cy - 6.2, cx + 2.8, cy - 3.2)
        path.cubicTo(cx + 2.8, cy - 1.2, cx, cy - 1.2, cx, cy + 0.8)
        painter.drawPath(path)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(color.red(), color.green(), color.blue(), alpha)))
        painter.drawEllipse(QPointF(cx, cy + 3.8), 0.9, 0.9)

    def draw_vector_shield(self, painter, cx, cy, color, alpha):
        """纯矢量微盾牌 + 内部审批勾 (Approval Checkmark)"""
        pen = QPen(QColor(color.red(), color.green(), color.blue(), alpha), 1.3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        shield = QPainterPath()
        shield.moveTo(cx - 4.2, cy - 4.5)
        shield.lineTo(cx + 4.2, cy - 4.5)
        shield.lineTo(cx + 4.2, cy - 0.5)
        shield.cubicTo(cx + 4.2, cy + 3.8, cx, cy + 5.2, cx, cy + 5.5)
        shield.cubicTo(cx, cy + 5.2, cx - 4.2, cy + 3.8, cx - 4.2, cy - 0.5)
        shield.closeSubpath()
        painter.drawPath(shield)

        check = QPainterPath()
        check.moveTo(cx - 2.0, cy - 0.2)
        check.lineTo(cx - 0.6, cy + 1.3)
        check.lineTo(cx + 2.2, cy - 1.5)
        painter.drawPath(check)

    def draw_vector_alert(self, painter, cx, cy, color, alpha):
        """纯矢量警报微圆 + 叹号线条"""
        pen = QPen(QColor(color.red(), color.green(), color.blue(), alpha), 1.3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        painter.drawEllipse(QPointF(cx, cy), 5.5, 5.5)
        painter.drawLine(QPointF(cx, cy - 2.6), QPointF(cx, cy + 0.8))

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(color.red(), color.green(), color.blue(), alpha)))
        painter.drawEllipse(QPointF(cx, cy + 2.8), 0.8, 0.8)


def main():
    def log_dbg(msg):
        with open(os.path.join(CURRENT_DIR, "capsule_debug.log"), "a", encoding="utf-8") as fp:
            fp.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")

    log_dbg(">>> MiniPillBar Cascade DropBounce main() started")

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    if not check_single_instance_or_wake():
        log_dbg("check_single_instance_or_wake returned False, exiting")
        sys.exit(0)
    log_dbg("Single instance check passed")

    island = SmoothDynamicIsland()
    island.show()
    island.make_topmost()
    log_dbg("Island shown, entering app.exec()")

    ret = app.exec()
    island.clean_exit()
    sys.exit(ret)


if __name__ == "__main__":
    try:
        main()
    except BaseException as e:
        if not isinstance(e, SystemExit) or e.code != 0:
            with open(os.path.join(CURRENT_DIR, "capsule_error.log"), "w", encoding="utf-8") as f:
                import traceback
                traceback.print_exc(file=f)
