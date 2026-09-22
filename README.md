# Antigravity Island (灵动岛) 🏝️

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Platform: Windows](https://img.shields.io/badge/Platform-Windows%2010%20%2F%2011-0078D6?style=flat-square&logo=windows&logoColor=white)](https://github.com/17689397470/antigravity-island)
[![GUI: PyQt6](https://img.shields.io/badge/GUI-PyQt6-41CD52?style=flat-square&logo=qt&logoColor=white)](https://riverbankcomputing.com/software/pyqt/)
[![Gitee](https://img.shields.io/badge/Gitee-Mirror-C71D23?style=flat-square&logo=gitee&logoColor=white)](https://gitee.com/yan-chaoyong/antigravity-island)

**专为 Google Antigravity 打造的高颜值、轻量级、原生物理流体动效桌面灵动岛**  
*A sleek, lightweight desktop dynamic island with authentic physics springs for Google Antigravity.*

[特性介绍](#-核心特性) • [交互指南](#-交互操作指南) • [快速开始](#-快速开始) • [核心架构](#-核心架构原理) • [English Docs](README_EN.md)

</div>

---

## 📸 效果演示 (Preview)

> 💡 *提示：录制一段 `preview.gif` 放置于根目录即可直观展示！*

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
```

---

## 🎯 为什么需要 Antigravity Island？

在使用 **Google Antigravity**（基于 Gemini 1M 上下文模型）进行智能编程与长链条 Agent 工作流时，开发者常常面临两个痛点：
1. **上下文盲盒焦虑**：任务进行到了第 30 步，不知道当前的 Token 消耗了多少、离 1M 窗口上限还有多远，何时需要主动开启新会话。
2. **待办与完成感知滞后**：当切到其他窗口工作时，Agent 触发了 `ask_question`（向你提问）或 `plan_approval`（等待审批），或者已经耗时 3 分钟完成了长任务，用户无法第一时间获知，频繁切回窗口确认打断心流。

**Antigravity Island** 将所有关键指标提炼为屏幕顶部常驻的一颗“灵动胶囊”，兼具极致美感与零打扰交互。

---

## ✨ 核心特性

- 🧠 **上下文深度透视**：精确跟踪 Gemini 1M 窗口容量，毫秒级解析输入 Token、输出 Token、使用率百分比，三阶智能着色（绿/橙/红）。
- 🌊 **满血物理流体弹簧动力学**：基于 Runge-Kutta 4阶 / 二阶欠阻尼物理弹簧振子计算，144Hz 满血硬件加速，呈现如同 iOS 灵动岛般的果冻微回弹与流体连通器避让。
- 💧 **待办阻断水滴副岛**：当 Agent 处于等待审批 (`plan_approval`) 或需要回答问题 (`ask_question`) 时，水滴副岛自动分离外滑，支持一键呼出二级悬浮卡片快速处理。
- 🔘 **30px 极简微圆最小状态**：随时收缩为屏幕正上方仅 30px 的黑曜石微圆，外围带彩色发丝进度环，内部随状态旋转灵动微星，悬停轻触浮出气泡徽章，纯粹无扰。
- 🔔 **离焦任务完成通知闭环**：任务完成时微圆向两侧平滑延展为 236px 横条通知，展示 4 秒后自动重新收缩回 30px，无需人工干预。
- ⚡ **极致克制的资源开销**：整合 Chrome DevTools Protocol (CDP) 极速前台 Tab 探测与 SQLite WAL 只读状态机，带 mtime 增量微秒级缓存，日常待机 **CPU 0.0%**。
- 🪟 **原生 Win32 硬件级优化**：采用 `SetWindowRgn` 穿透遮罩与物理层置顶，主岛外空白画布 100% 鼠标穿透，绝不阻挡任何正常窗口操作。

---

## 🎮 交互操作指南

| 手势 / 操作 | 交互效果 |
| :--- | :--- |
| **鼠标悬停（主岛区）** | 平滑展开大屏，展示详细 Token 分布（输入/输出/总计/当前运行状态） |
| **鼠标悬停（水滴副岛）** | 意图识别（60ms）后顺势落体滑出二级操作卡片，可直接审批计划 |
| **鼠标右键单击** | 唤出 4 按钮横向迷你药丸栏（刷新数据、重置居中、切换最小微圆、退出） |
| **鼠标左键单击** | 一键将正在运行的 Antigravity IDE 唤醒至前台 |
| **鼠标左键按住拖拽** | 自由将灵动岛拖动至屏幕任意位置（靠近顶部自动磁吸至 12px） |
| **最小模式下单机** | 无论左键还是右键点击 30px 微圆，瞬间液态舒展恢复为完整标准岛 |

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
- 在灵动岛上点击**鼠标右键**，点击药丸栏最右侧的**退出按钮**；
- 或双击运行 `stop.bat`。

---

## 🏛 核心架构原理

```mermaid
graph TD
    subgraph Antigravity IDE
        CDP[Chrome DevTools Protocol\n端口探测]
        DB[(conversation_summaries.db\nSQLite WAL)]
        LOGS[transcript.jsonl\n会话日志流]
    end

    subgraph Data Pipeline [后台指标嗅探引擎 (brain_monitor.py)]
        Detector[CDP 前台活跃会话探测器]
        Parser[SQLite/JSONL 增量微秒级解析器]
        Detector --> Parser
    end

    CDP --> Detector
    DB --> Parser
    LOGS --> Parser

    subgraph GUI Engine [灵动岛核心渲染引擎 (capsule_gui.py)]
        Spring[144Hz RK4 物理弹簧动力学系统]
        Renderer[PyQt6 + Win32 穿透遮罩管线]
        Pill[阶梯落体微药丸栏]
        Minimal[30px 极简微圆与通知闭环]
    end

    Parser -->|QThread 信号驱动| Spring
    Spring --> Renderer
    Renderer --> Pill
    Renderer --> Minimal
```

---

## ⚙️ 配置文件说明 (`config.json`)

程序首次运行会自动在当前目录生成 `config.json`，配置项支持自动热保存：

```json
{
  "x": 860,
  "y": 12,
  "minimal_mode": false
}
```
- `x`, `y`：灵动岛在屏幕上的物理坐标（留空或拖动后自动保存）；
- `minimal_mode`：是否开启极简微圆模式（`true` / `false`）。

---

## 🗺️ 路线图 (Roadmap)

- [x] 基于二阶欠阻尼物理弹簧算法重构动效系统
- [x] 待办阻断分离水滴副岛与二级卡片审批
- [x] 30px 屏幕居中极简微圆模式与 4 秒通知闭环
- [x] 4 按钮阶梯落体弹跳微药丸栏
- [ ] 基于 PyInstaller / Nuitka 打包发布单个免安装可执行文件 (`.exe`)
- [ ] 多显示器 DPI 动态热插拔自适应
- [ ] 支持自定义主题色（莫兰迪/黑金/赛博朋克）与音效反馈

---

## 🤝 贡献与支持 (Contributing)

欢迎提交 Issue 和 Pull Request！
如果你喜欢这个项目，欢迎点一个 ⭐️ **Star** 鼓励支持！

- GitHub: [17689397470/antigravity-island](https://github.com/17689397470/antigravity-island)
- Gitee: [yan-chaoyong/antigravity-island](https://gitee.com/yan-chaoyong/antigravity-island)

---

## 📄 开源协议 (License)

本项目遵循 [MIT License](LICENSE) 开源协议。
