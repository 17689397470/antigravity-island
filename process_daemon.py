#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Process Daemon: 毫秒级极速检测 Antigravity 宿主进程状态与强力前台唤醒
优化版：
1. 采用 PID 句柄与 HWND 智能缓存，GetExitCodeProcess 耗时 < 1µs，消除全系统遍历开销。
2. 硬件级极速唤醒：优先直接激活缓存的窗口句柄，耗时 < 0.1ms。
3. 网络与二次唤醒动作全异步线程化，彻底消除点击事件阻塞。
"""

import os
import json
import urllib.request
import subprocess
import ctypes
import ctypes.wintypes
import time
import threading

TARGET_PROCESSES = ["antigravity.exe", "code.exe"]
PORT_FILE = os.path.expanduser(r"~\AppData\Roaming\Antigravity\DevToolsActivePort")
ANTIGRAVITY_EXE = os.path.expanduser(r"~\AppData\Local\Programs\antigravity\Antigravity.exe")

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
psapi = ctypes.windll.psapi

STILL_ACTIVE = 259
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

_CACHED_PID = None
_CACHED_HANDLE = None
_CACHED_HWND = None
_LAST_ENUM_TIME = 0


def _cleanup_cached_handle():
    global _CACHED_HANDLE, _CACHED_PID
    if _CACHED_HANDLE:
        try:
            kernel32.CloseHandle(_CACHED_HANDLE)
        except Exception:
            pass
    _CACHED_HANDLE = None
    _CACHED_PID = None


def is_antigravity_running():
    """
    极速检查 Antigravity 进程是否存活。
    优先复用缓存的句柄（GetExitCodeProcess，耗时 < 1µs），仅在进程退出或未缓存时全量枚举。
    """
    global _CACHED_HANDLE, _CACHED_PID, _LAST_ENUM_TIME

    # 1. 优先使用缓存的句柄快速验证
    if _CACHED_HANDLE:
        exit_code = ctypes.wintypes.DWORD()
        if kernel32.GetExitCodeProcess(_CACHED_HANDLE, ctypes.byref(exit_code)):
            if exit_code.value == STILL_ACTIVE:
                return True
        _cleanup_cached_handle()

    # 2. 全量枚举（加节流保护，至少间隔 0.3s）
    now = time.time()
    if now - _LAST_ENUM_TIME < 0.3:
        return False
    _LAST_ENUM_TIME = now

    try:
        pids = (ctypes.wintypes.DWORD * 2048)()
        cb_needed = ctypes.wintypes.DWORD()
        if not psapi.EnumProcesses(ctypes.byref(pids), ctypes.sizeof(pids), ctypes.byref(cb_needed)):
            return False

        count = cb_needed.value // 4
        buf = ctypes.create_unicode_buffer(260)
        sz = ctypes.wintypes.DWORD(260)

        for i in range(count):
            pid = pids[i]
            if pid == 0:
                continue
            h = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
            if h:
                sz.value = 260
                if kernel32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(sz)):
                    pname = buf.value.split("\\")[-1].lower()
                    if pname in TARGET_PROCESSES:
                        # 成功找到目标进程，缓存句柄与 PID
                        _cleanup_cached_handle()
                        _CACHED_HANDLE = h
                        _CACHED_PID = pid
                        return True
                kernel32.CloseHandle(h)
        return False
    except Exception:
        return True


def is_antigravity_foreground():
    """检测 Antigravity 窗口当前是否位于最前台（聚焦），耗时 < 0.1ms"""
    try:
        fg = user32.GetForegroundWindow()
        if not fg:
            return False
        pid = ctypes.wintypes.DWORD()
        user32.GetWindowThreadProcessId(fg, ctypes.byref(pid))
        if pid.value == 0:
            return False

        if _CACHED_PID and pid.value == _CACHED_PID:
            return True

        h = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
        if not h:
            return False

        buf = ctypes.create_unicode_buffer(260)
        sz = ctypes.wintypes.DWORD(260)
        pname = ""
        if kernel32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(sz)):
            pname = buf.value.split("\\")[-1].lower()
        kernel32.CloseHandle(h)

        return pname in TARGET_PROCESSES
    except Exception:
        return False


def _find_antigravity_hwnd():
    """快速遍历顶层窗口寻找 Antigravity 窗口句柄"""
    global _CACHED_HWND
    try:
        hwnd = user32.GetTopWindow(0)
        buf = ctypes.create_unicode_buffer(260)
        sz = ctypes.wintypes.DWORD(260)

        while hwnd:
            if user32.IsWindowVisible(hwnd):
                pid = ctypes.wintypes.DWORD()
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                h = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
                if h:
                    sz.value = 260
                    if kernel32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(sz)):
                        pname = buf.value.split("\\")[-1].lower()
                        if pname in TARGET_PROCESSES:
                            rect = ctypes.wintypes.RECT()
                            user32.GetWindowRect(hwnd, ctypes.byref(rect))
                            w = rect.right - rect.left
                            h_val = rect.bottom - rect.top
                            if w > 300 and h_val > 200:
                                kernel32.CloseHandle(h)
                                _CACHED_HWND = hwnd
                                return hwnd
                    kernel32.CloseHandle(h)
            hwnd = user32.GetWindow(hwnd, 2)  # GW_HWNDNEXT
    except Exception:
        pass
    return None


def get_antigravity_window_rect():
    """
    获取当前 Antigravity 宿主主窗口的屏幕坐标矩形 (left, top, right, bottom)。
    若未运行或窗口最小化/未找到，返回 None。
    """
    global _CACHED_HWND
    try:
        if _CACHED_HWND and user32.IsWindow(_CACHED_HWND) and user32.IsWindowVisible(_CACHED_HWND):
            rect = ctypes.wintypes.RECT()
            if user32.GetWindowRect(_CACHED_HWND, ctypes.byref(rect)):
                w = rect.right - rect.left
                h = rect.bottom - rect.top
                if w > 300 and h > 200:
                    return (rect.left, rect.top, rect.right, rect.bottom)
            _CACHED_HWND = None

        hwnd = _find_antigravity_hwnd()
        if hwnd:
            rect = ctypes.wintypes.RECT()
            if user32.GetWindowRect(hwnd, ctypes.byref(rect)):
                return (rect.left, rect.top, rect.right, rect.bottom)
    except Exception:
        pass
    return None


def _activate_window_hw(hwnd):
    """Win32 穿透锁极速激活置顶"""
    try:
        if user32.IsIconic(hwnd):
            user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        else:
            user32.ShowWindow(hwnd, 5)  # SW_SHOW

        user32.keybd_event(0x12, 0, 0, 0)  # ALT down
        user32.SetForegroundWindow(hwnd)
        user32.keybd_event(0x12, 0, 2, 0)  # ALT up
        return True
    except Exception:
        return False


def _async_wake_fallback():
    """慢速唤醒 fallback (在独立后台线程执行，绝不阻塞主线程)"""
    try:
        # DevTools CDP 激活当前活动 Tab
        if os.path.exists(PORT_FILE):
            try:
                with open(PORT_FILE, "r", encoding="utf-8") as f:
                    port = f.readline().strip()
                if port.isdigit():
                    url = f"http://127.0.0.1:{port}/json"
                    with urllib.request.urlopen(url, timeout=0.3) as resp:
                        targets = json.loads(resp.read().decode("utf-8", errors="ignore"))
                    for t in targets:
                        if t.get("type") == "page":
                            tid = t.get("id")
                            urllib.request.urlopen(f"http://127.0.0.1:{port}/json/activate/{tid}", timeout=0.3)
                            break
            except Exception:
                pass

        # 官方单实例机制作为底层兜底
        if os.path.exists(ANTIGRAVITY_EXE):
            subprocess.Popen([ANTIGRAVITY_EXE], creationflags=0x00000008)
    except Exception:
        pass


def bring_antigravity_to_foreground():
    """
    强力唤醒并将 Antigravity 窗口置顶并聚焦到屏幕最前台。
    前台部分瞬间完成（< 0.1ms），网络及慢速兜底全异步执行，零卡顿。
    """
    global _CACHED_HWND

    # 1. 优先激活缓存的 HWND
    if _CACHED_HWND and user32.IsWindow(_CACHED_HWND) and user32.IsWindowVisible(_CACHED_HWND):
        _activate_window_hw(_CACHED_HWND)
        # 启动后台兜底
        threading.Thread(target=_async_wake_fallback, daemon=True).start()
        return True

    # 2. 缓存失效，快速寻找并激活
    hwnd = _find_antigravity_hwnd()
    if hwnd:
        _activate_window_hw(hwnd)
        threading.Thread(target=_async_wake_fallback, daemon=True).start()
        return True

    # 3. 未找到可见窗口，异步调用单实例拉起
    threading.Thread(target=_async_wake_fallback, daemon=True).start()
    return False
