# Antigravity Island (灵动岛) 🏝️

<div align="center">

[![Version: v2.0.0](https://img.shields.io/badge/Version-v2.0.0-emerald.svg?style=flat-square)](https://github.com/17689397470/antigravity-island)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Platform: Windows](https://img.shields.io/badge/Platform-Windows%2010%20%2F%2011-0078D6?style=flat-square&logo=windows&logoColor=white)](https://github.com/17689397470/antigravity-island)
[![GUI: PyQt6](https://img.shields.io/badge/GUI-PyQt6-41CD52?style=flat-square&logo=qt&logoColor=white)](https://riverbankcomputing.com/software/pyqt/)
[![Gitee](https://img.shields.io/badge/Gitee-Mirror-C71D23?style=flat-square&logo=gitee&logoColor=white)](https://gitee.com/yan-chaoyong/antigravity-island)

**专为 Google Antigravity 打造的高颜值、轻量级、原生物理流体动效桌面灵动岛**  
*A sleek, lightweight desktop dynamic island with authentic physics springs for Google Antigravity.*

[特性介绍](#-核心特性) • [交互指南](#-交互操作指南) • [快速开始](#-快速开始) • [核心架构](#-核心架构原理) • [English Docs](README_EN.md) • [更新日志](CHANGELOG.md)

</div>

---

## 📸 效果演示 (Preview)

```
   ┌──────────────────────────────────────────────────────────┐
   │  ● Context: 42.8% [▓▓▓▓▓▓▓▓░░░░░░░░]  Antigravity   💧1  │  <-- 标准灵动岛状态
   └──────────────────────────────────────────────────────────┘
                              │
                    (鼠标悬停在主岛指标区)
                              ▼
   ┌──────────────────────────────────────────────────────────┐
   │ 448.2k / 1.0M (42.8%)  •  Antigravity (Coding Agent)      │
   │ Input: 380.1k  Output: 68.1k  •  状态: 思考中 ⚡          │  <-- 展开大屏指标
   └──────────────────────────────────────────────────────────┘
                              │
                  (闲置 4 秒且无交互，自动贴顶)
                              ▼
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━[  182x3px 微刘海晶条  ]━━━━━━━━━━━━━━━━━━━━━━━━━━━  <-- 边缘贴靠收缩
```

---

## 🎯 为什么需要 Antigravity Island？

在使用 **Google Antigravity**（基于 Gemini 1M 上下文模型）进行智能编程与长链条 Agent 工作流时，开发者常常面临两个痛点：
1. **上下文盲盒焦虑**：任务进行到了第 30 步，不知道当前的 Token 消耗了多少、离 1M 窗口上限还有多远，何时需要主动开启新会话。
2. **待办与完成感知滞后**：当切到其他窗口工作时，Agent 触发了 `ask_question`（向你提问）或 `plan_approval`（等待审批），或者已经耗时 3 分钟完成了长任务，用户无法第一时间获知，频繁切回窗口确认打断心流。

**Antigravity Island** 将所有关键指标提炼为屏幕顶部常驻的一颗“灵动胶囊”，兼具极致美感与零打扰交互。

---

## ✨ 核心特性 (v2.0.0)

### 🍃 边缘贴靠灵动收缩 (Edge Notch Auto-Tuck)
- **4 秒闲置微刘海收纳**：无交互满 4 秒后，以 200ms 平滑临界阻尼向上吸附收缩至屏幕顶缘，仅露出 **182x3px 黑曜石微刘海**，彻底消灭全屏浏览器或无边框 IDE 的顶栏遮挡。
- **触顶落体与物理弹性展开**：鼠标触碰屏幕极顶瞬间触发水滴滑落展出，伴随 **1.2px 柔和微弹性回弹（Overshoot & Settle）**，手感浑厚自然。
- **智能状态豁免 (Immunity Rules)**：Agent 思考中（`is_busy`）或出现提问/审批阻断（`pending_action`）时**强制锁定展出**；若已收缩，毫秒级自动从顶缘滑出置顶提醒，绝不遗漏核心决策。
- **冷光纤芯呼吸指示**：收缩态正中央呈现 48x1.2px 的微光状态冷光纤芯（Notch Optic Core），提供极低视觉负荷的健康指示。

### 🖥️ 多显示器与副屏负坐标全兼容 (Multi-Monitor Adaptive)
- **智能跟随宿主显示器**：优先探测 Antigravity IDE 所在屏幕并自动吸附至对应屏幕顶部；无 IDE 窗口时自动回退到鼠标当前所在屏幕或主屏。
- **攻克副屏负坐标陷阱**：彻底重构窗口几何计算，主岛、药丸栏与二级卡片全面支持 Windows 异形排列及负坐标（$X < 0$ / $Y < 0$），在左侧/上方副屏绝不被强行截断在 X=0。
- **屏幕热插拔容灾**：监听外接显示器断开与分辨率变动，一旦检测到停靠屏幕失效，秒级安全平滑回退至主屏幕顶部居中。
- **托盘动态切换**：托盘右键菜单提供【停靠至显示器 ▶】二级子菜单，动态展示当前系统全部屏幕（如 `显示器 1 (主屏) [2048x1152 @ 125%]`），一键瞬移停靠。

### 💎 瑞士现代排版与物理光学美学 (Swiss Micro-Typography)
- **定向菲涅尔发丝光边框**：顶部微白发丝高光（~38% 透明度），中腰自然过渡，底部幽深微隐（~8% 透明度），拒绝廉价平切边框。
- **左侧冷光状态晶石**：0.9px 暗圈底座内嵌 1.1px 高纯度晶体微光核，待机翡翠绿、思考天空蓝、待办琥珀橙/宝石蓝，色彩纯粹沉稳。
- **精细白银字符排版**：采用 `Segoe UI Variable Text` Medium (500) 柔和白银色，百分比主数字与 `%` 符号专业分离排版，层次分明。

### 🔔 系统托盘与常驻兜底机制 (System Tray & Autostart)
- **手绘 32x32 动态矢量托盘图标**：纯内存矢量绘制，外围带根据 Token 百分比实时展开的动态环形进度圈，中央指示灯三色呼吸。
- **Win11 暗黑现代右键菜单**：支持开机静默自启动（注册表 `HKCU\Run`）、显隐切换、极简微圆切换、贴边自动收缩切换。
- **防误触隐藏守卫**：手动在托盘点击“隐藏”后锁定状态，杜绝指标心跳脉冲导致的误弹出。

### 🔒 工业级单实例互斥与 IPC 唤醒 (Single-Instance & Local IPC)
- **Windows 内核命名互斥体**：基于 `CreateMutexW`，无论主岛处于显示、隐藏、极简还是托盘，100% 绝对杜绝多开。
- **本地管道跨进程唤醒**：重复启动时新实例自动通过 `QLocalSocket` 向旧实例发送唤醒指令，瞬间将其从后台/托盘呼出置顶前台，新实例安全退出。
- **孤儿僵尸进程自动接管**：若检测到冲突但 IPC 无响应（旧进程异常僵死），新进程自动强制清理残留并接管启动。

---

## 🎮 交互操作指南

| 手势 / 操作 | 交互效果 |
| :--- | :--- |
| **鼠标悬停（主岛区）** | 平滑展开大屏，展示详细 Token 分布（输入/输出/系统/用户占比及运行状态） |
| **鼠标悬停（水滴副岛）** | 意图识别（60ms）后顺势落体滑出二级操作卡片，可直接审批计划或选择答复 |
| **鼠标离开 4 秒（空闲态）** | 岛体以 200ms 临界阻尼平滑吸附收缩至屏幕顶缘，变为 182x3px 微刘海 |
| **鼠标触碰屏幕极顶** | 毫秒级从顶缘顺滑滑落展开，伴随 1.2px 柔和微弹性回弹 |
| **鼠标右键单击** | 唤出 4 按钮横向迷你药丸栏（刷新数据、重置居中、切换最小微圆、退出） |
| **鼠标左键单击** | 一键将正在运行的 Antigravity IDE 唤醒至前台（处于收缩态时先滑落展开） |
| **鼠标左键按住拖拽** | 自由将灵动岛拖动至任意显示器（靠近顶部 28px 自动磁吸至 12px） |
| **系统托盘单击** | 一键切换灵动岛在前台的显示与收起 |
| **系统托盘双击** | 瞬间穿透置顶唤醒 Antigravity IDE 窗口并呼出灵动岛 |
| **系统托盘右键** | 打开沉浸式暗黑菜单（开机自启、贴边收缩开关、停靠显示器切换等） |

---

## 🚀 快速开始

### 环境依赖
- **操作系统**：Windows 10 / Windows 11
- **Python 版本**：Python 3.10+
- **Google Antigravity**：已安装并运行

### 1. 克隆仓库
```bash
# 从 GitHub 克隆
git clone https://github.com/17689397470/antigravity-island.git
cd antigravity-island

# 或从 Gitee 镜像克隆
git clone https://gitee.com/yan-chaoyong/antigravity-island.git
cd antigravity-island
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 启动灵动岛
- **方式一（无控制台静默启动，推荐）**：双击 `start.bat`。
- **方式二（调试运行）**：
  ```bash
  python capsule_gui.py
  ```

### 4. 安全退出
- 在系统托盘图标上右键，点击【彻底退出灵动岛】；
- 或在灵动岛上点击**鼠标右键**，点击药丸栏最右侧的**退出按钮**；
- 或双击运行 `stop.bat`。

---

## ⚙️ 配置文件说明 (`config.json`)

程序首次运行会自动在当前目录生成 `config.json`，配置项支持自动热保存：

```json
{
  "x": 860,
  "y": 12,
  "on_top": true,
  "auto_hide": true,
  "auto_tuck": true,
  "tuck_delay_ms": 4000,
  "minimal_mode": false
}
```
- `x`, `y`：灵动岛在屏幕上的物理坐标（留空或拖动后自动保存，支持负坐标）；
- `auto_tuck`：是否启用 4 秒闲置贴边收缩微刘海模式（`true` / `false`）；
- `tuck_delay_ms`：闲置收缩延迟时间，默认 4000ms；
- `minimal_mode`：是否开启 30px 极简微圆模式（`true` / `false`）。

---

## 🗺️ 路线图 (Roadmap)

- [x] 基于二阶欠阻尼物理弹簧算法重构动效系统
- [x] 待办阻断分离水滴副岛与二级卡片审批
- [x] 30px 屏幕居中极简微圆模式与 4 秒通知闭环
- [x] 4 按钮阶梯落体弹跳微药丸栏
- [x] 瑞士现代排版与物理光学质感升级
- [x] 系统托盘动态图标与开机静默自启机制
- [x] 工业级 Win32 Named Mutex 单实例互斥与本地 IPC 唤醒
- [x] 多显示器 DPI 追踪、智能跟随与副屏负坐标全兼容
- [x] 边缘贴靠灵动收缩（Edge Notch Auto-Tuck）与智能状态豁免
- [ ] 基于 PyInstaller / Nuitka 打包发布单个免安装可执行文件 (`.exe`)
- [ ] 类似 iOS 灵动岛的多模态轻量水滴音效与流体呼吸光波

---

## 🤝 贡献与支持 (Contributing)

欢迎提交 Issue 和 Pull Request！
如果你喜欢这个项目，欢迎点一个 ⭐️ **Star** 鼓励支持！

- GitHub: [17689397470/antigravity-island](https://github.com/17689397470/antigravity-island)
- Gitee: [yan-chaoyong/antigravity-island](https://gitee.com/yan-chaoyong/antigravity-island)

---

## 📄 开源协议 (License)

本项目遵循 [MIT License](LICENSE) 开源协议。
