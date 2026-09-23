# Changelog (更新日志)

本项目遵循 [Semantic Versioning (语义化版本号 2.0.0)](https://semver.org/lang/zh-CN/) 规范。

---

## [2.0.0] - 2026-09-24

### 🌟 Added (重大新增)
- **边缘贴靠灵动收缩 (Edge Notch Auto-Tuck)**：
  - 闲置 4 秒自动贴顶收纳为 182x3px 极简黑曜石微刘海，内嵌 48x1.2px 发丝状态冷光晶条（Notch Optic Core）。
  - 采用二阶流体物理弹簧引擎（7ms 高精度时钟），触顶即刻落体展开，伴随 1.2px 柔和微弹性回弹（Overshoot & Settle）。
  - 智能状态豁免机制 (Smart Immunity Rules)：Agent 处于思考生成（`is_busy`）或收到待办阻断（`ask_question`/`plan_approval`）时强制展开并锁定，绝不错过核心决策。
  - 托盘右键菜单增加【贴边自动收缩】开关，配置持久化至 `config.json`。
- **多显示器与异形副屏全适配 (Multi-Monitor & Negative Coordinates)**：
  - 智能跟随 Antigravity IDE 所在屏幕，启动或居中时自动吸附至对应显示器顶部。
  - 彻底攻克 Windows 副屏负坐标截断缺陷，主岛、药丸栏与二级卡片均完全支持左侧/上方副屏（$X < 0$ / $Y < 0$）。
  - 监听显示器热插拔与分辨率事件，外接屏断开或休眠时秒级平滑回退至主屏居中。
  - 托盘右键菜单新增【停靠至显示器 ▶】二级动态子菜单，动态枚举系统全部屏幕并支持一键切换。
- **系统托盘与常驻兜底机制 (System Tray & Autostart)**：
  - 手绘 32x32 动态矢量托盘图标，带 Token 使用率动态圆环进度圈与 Agent 状态三色呼吸指示。
  - 沉浸式 Win11 暗黑托盘右键菜单，支持显隐切换、极简微圆切换、贴边收缩切换与开机静默自启动（注册表 `HKCU\Run`）。
- **工业级单实例互斥与本地 IPC 唤醒 (Single-Instance & Local IPC)**：
  - 引入 Windows 内核命名互斥体 `CreateMutexW("Local\\AntigravityIsland_SingleInstance_Mutex")`，100% 杜绝多开。
  - 基于 `QLocalServer`/`QLocalSocket` 本地命名管道，重复双击启动时自动向已有实例发送 `WAKE_UP` 指令，瞬间将其从后台/托盘唤出置顶前台。
  - 增加僵尸进程自动清理与接管机制，杜绝孤儿死锁。

### 🎨 Visual & Typographic Polish (视觉质感升级)
- **瑞士现代微排版**：采用 `Segoe UI Variable Text` Medium (500) 柔和白银字符，主数字与 `%` 符号专业分离。
- **物理光学发丝边框**：重构定向菲涅尔垂直线性渐变发丝边框（顶部 38% 高光，中腰 20%，底部 8% 幽深微隐）。
- **状态宝石指示灯**：0.9px 暗圈底座内嵌 1.1px 高纯度晶体微光核，色彩纯粹沉稳。
- **暗轨与微高光游标**：右侧 Token 环形进度圈采用凹槽暗轨与 0.9px 游标微高光。

### 🐛 Fixed (缺陷修复)
- 修复用户手动在托盘点击“隐藏”后，被指标工作线程周期性心跳在 1 秒内无脑自动重新弹出的 Bug。
- 修复 Windows `cmd.exe` 因 LF 换行导致多行括号批处理闪退的问题，`start.bat` 升级为秒级静默启动并自动脱离控制台。

---

## [1.0.0] - 2026-09-20

### Initial Release
- 首次开源发布 Antigravity Island 灵动岛。
- 深度透视 Gemini 1M 上下文 Token 分布（Model / Tool / System / User）。
- 二阶欠阻尼物理弹簧动画动力学系统。
- 待办阻断分离水滴副岛与二级计划审批卡片。
- 30px 极简微圆模式与离焦任务完成 4 秒通知闭环。
- 4 按钮阶梯落体弹跳微药丸栏。
