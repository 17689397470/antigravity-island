# Antigravity Island 🏝️

<div align="center">

[![Version: v2.0.0](https://img.shields.io/badge/Version-v2.0.0-emerald.svg?style=flat-square)](https://github.com/17689397470/antigravity-island)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Platform: Windows](https://img.shields.io/badge/Platform-Windows%2010%20%2F%2011-0078D6?style=flat-square&logo=windows&logoColor=white)](https://github.com/17689397470/antigravity-island)
[![GUI: PyQt6](https://img.shields.io/badge/GUI-PyQt6-41CD52?style=flat-square&logo=qt&logoColor=white)](https://riverbankcomputing.com/software/pyqt/)

**A sleek, lightweight desktop dynamic island with authentic physics springs for Google Antigravity.**

[Features](#-key-features-v200) • [Controls](#-interactive-controls) • [Quick Start](#-quick-start) • [Architecture](#-architecture) • [Changelog](CHANGELOG.md) • [中文文档](README.md)

</div>

---

## 🎯 Why Antigravity Island?

When working with **Google Antigravity** (built on Gemini 1M Context Window), developers encounter two common challenges:
1. **Context Blind Box Anxiety**: When deep into long agentic workflows, it's hard to know how many tokens have been consumed and when the 1M limit is approaching.
2. **Delayed Pending Action Awareness**: When switching to another window, agent pauses (e.g. `ask_question` or `plan_approval`) or task completions often go unnoticed without constantly tabbing back.

**Antigravity Island** condenses these critical metrics into an elegant, non-intrusive floating island pinned to the top of your screen.

---

## ✨ Key Features (v2.0.0)

- 🍃 **Edge Notch Auto-Tuck**: Automatically retracts to an ultra-minimal **182x3px Obsidian Notch** after 4s of idle time. Touching the very top edge drops the island down smoothly with **1.2px elastic overshoot & settle**. Includes **Smart Immunity Rules** (automatically un-tucks when agent is busy or waiting for approval).
- 🖥️ **Multi-Monitor & Negative Coordinate Support**: Smart auto-following detects which monitor Antigravity IDE is on and docks to it. Fully supports Windows non-standard arrangements and negative coordinates ($X < 0$), plus hotplug failover safely returning to primary monitor. Includes a dynamic tray submenu `Dock to Monitor ▶`.
- 💎 **Swiss Micro-Typography & Optical Physics**: Directional Fresnel hairline border, optical jewel indicator light, Segoe UI Variable Text (500 Medium) typography, and recessed dark track with cursor specular highlight.
- 🔔 **System Tray & Persistent Daemon**: Hand-crafted 32x32 dynamic vector tray icon reflecting live token usage and agent state with breathing color. Complete with Windows 11 dark context menu and boot autostart (`HKCU\Run`) toggle.
- 🔒 **Industrial Single-Instance & Local IPC Wakeup**: Powered by Windows Named Mutex (`CreateMutexW`) and `QLocalServer`/`QLocalSocket` pipe. Prevents multiple instances while instantly waking the running instance to foreground upon duplicate launch.
- 💧 **Detachable Action Droplet**: Separates automatically when agent actions require your attention, enabling fast 1-click approvals.
- 🔘 **30px Minimal Mode**: Shrinks into an ultra-clean 30px micro circle centered at the top of your screen with progress arc and rotating orbit star.
- ⚡ **Ultra-Lightweight Footprint**: Combines Chrome DevTools Protocol (CDP) session sniffing and SQLite WAL reader. Consumes **0.0% CPU** on idle.

---

## 🎮 Interactive Controls

| Gesture / Action | Result |
| :--- | :--- |
| **Hover (Main Island)** | Expands to full dashboard displaying Input, Output, and agent state |
| **Hover (Droplet)** | Triggers drop flyout card for inline plan approval |
| **Idle for 4s** | Smoothly retracts to top edge as a 182x3px notch |
| **Touch Screen Top Edge** | Fluid drop-down spring animation reveals the island |
| **Right Click** | Pops up 4-button staggered mini pill bar |
| **Left Click** | Brings Antigravity IDE window immediately to the foreground |
| **Drag & Drop** | Repositions the island across any monitor (snaps to 12px at top) |
| **Tray Left Click** | Toggles show / hide |
| **Tray Double Click** | Wakes Antigravity IDE and island to topmost foreground |
| **Tray Right Click** | Opens modern dark context menu |

---

## 🚀 Quick Start

### Prerequisites
- Windows 10 or 11
- Python 3.10+
- Google Antigravity installed

### Installation & Run
```bash
git clone https://github.com/17689397470/antigravity-island.git
cd antigravity-island
pip install -r requirements.txt
python capsule_gui.py
```
Or simply double-click `start.bat` for silent background execution.

---

## 📄 License

Distributed under the [MIT License](LICENSE).
