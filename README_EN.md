# Antigravity Island 🏝️

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Platform: Windows](https://img.shields.io/badge/Platform-Windows%2010%20%2F%2011-0078D6?style=flat-square&logo=windows&logoColor=white)](https://github.com/17689397470/antigravity-island)
[![GUI: PyQt6](https://img.shields.io/badge/GUI-PyQt6-41CD52?style=flat-square&logo=qt&logoColor=white)](https://riverbankcomputing.com/software/pyqt/)

**A sleek, lightweight desktop dynamic island with authentic physics springs for Google Antigravity.**

[Features](#-key-features) • [Controls](#-interactive-controls) • [Quick Start](#-quick-start) • [Architecture](#-architecture) • [中文文档](README.md)

</div>

---

## 🎯 Why Antigravity Island?

When working with **Google Antigravity** (built on Gemini 1M Context Window), developers encounter two common challenges:
1. **Context Blind Box Anxiety**: When deep into long agentic workflows, it's hard to know how many tokens have been consumed and when the 1M limit is approaching.
2. **Delayed Pending Action Awareness**: When switching to another window, agent pauses (e.g. `ask_question` or `plan_approval`) or task completions often go unnoticed without constantly tabbing back.

**Antigravity Island** condenses these critical metrics into an elegant, non-intrusive floating island pinned to the top of your screen.

---

## ✨ Key Features

- 🧠 **Deep Context Visibility**: Tracks Gemini 1M context in real time, showing Input, Output, and Usage Percentage with 3-tier smart coloring.
- 🌊 **Authentic Physics Springs**: Powered by second-order underdamped spring dynamics at 144Hz hardware-accelerated rendering.
- 💧 **Detachable Action Droplet**: Separates automatically when agent actions (approval/question) require your attention, enabling fast 1-click approvals.
- 🔘 **30px Minimal Mode**: Shrinks into an ultra-clean 30px micro circle centered at the top of your screen with progress arc and rotating orbit star.
- 🔔 **Unfocused Notification Loop**: Auto-expands into a 236px banner when a background task finishes, auto-collapsing after 4 seconds.
- ⚡ **Ultra-Lightweight Footprint**: Combines Chrome DevTools Protocol (CDP) session sniffing and SQLite WAL reader. Consumes **0.0% CPU** on idle.
- 🪟 **Native Win32 Optimization**: Hardware-level topmost priority with `SetWindowRgn` transparent click-through outside the island.

---

## 🎮 Interactive Controls

| Gesture / Action | Result |
| :--- | :--- |
| **Hover (Main Island)** | Expands to full dashboard displaying Input, Output, and agent state |
| **Hover (Droplet)** | Triggers drop flyout card for inline plan approval |
| **Right Click** | Pops up 4-button staggered mini pill bar (Refresh, Center, Minimal Mode, Exit) |
| **Left Click** | Brings Antigravity IDE window immediately to the foreground |
| **Drag & Drop** | Freely repositions the island (snaps to 12px at screen top) |
| **Click in Minimal Mode** | Restores the island to standard full-size smoothly |

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
