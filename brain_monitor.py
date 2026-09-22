#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Brain Monitor: 极速实时解析 Antigravity 活动会话与上下文 Token 指标
优化版：
1. 增加 Chrome DevTools Protocol (CDP) 极速前台探测，100% 实时响应用户在界面上的会话 Tab 切换。
2. 增加 SQLite conversation_summaries.db 只读第二级兜底。
3. 增加 mtime + size 智能微秒级缓存，会话未变且无写入时 0 CPU 消耗。
"""

import os
import glob
import json
import re
import urllib.request
import sqlite3
import time

PORT_FILE = os.path.expanduser(r"~\AppData\Roaming\Antigravity\DevToolsActivePort")
DB_PATH = os.path.expanduser(r"~\.gemini\antigravity\conversation_summaries.db")
BRAIN_DIR = os.path.expanduser(r"~\.gemini\antigravity\brain")
TOTAL_CAPACITY = 1_048_576  # Gemini 1M 窗口
# 全局内存缓存
_CACHE_METRICS = None
_CACHE_KEY = None  # (conv_id, mtime, file_size)


class SessionActivityTracker:
    def __init__(self):
        self.last_conv_id = None
        self.is_busy = False
        self.busy_start_time = 0
        self.has_notified = False

    def check_db_status(self, conv_id):
        """读取 SQLite 数据库权威运行状态 (耗时 < 1ms)"""
        if not os.path.exists(DB_PATH) or not conv_id:
            return None, None
        try:
            conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
            cur = conn.cursor()
            cur.execute("SELECT not_fully_idle, status FROM conversation_summaries WHERE conversation_id = ?", (conv_id,))
            row = cur.fetchone()
            conn.close()
            if row:
                return row[0], row[1]
        except Exception:
            pass
        return None, None

    def update(self, conv_id, step_count, mtime, last_source):
        now = time.time()
        just_completed = False
        duration_str = ""

        # 切换会话时重置
        if conv_id != self.last_conv_id:
            self.last_conv_id = conv_id
            self.is_busy = False
            self.busy_start_time = 0
            self.has_notified = False
            return False, False, ""

        not_idle, run_status = self.check_db_status(conv_id)

        # 权威判断：只要处于 RUNNING 或 not_fully_idle == 1，说明 Agent 正在思考/执行工具！
        if not_idle == 1 or run_status == "CASCADE_RUN_STATUS_RUNNING":
            if not self.is_busy:
                self.is_busy = True
                self.busy_start_time = now
                self.has_notified = False  # 新任务开始，重置通知锁
        else:
            # 当前处于就绪空闲态
            if self.is_busy and not self.has_notified:
                # 由忙碌状态首次转移为空闲：整轮交互彻底完成！
                self.is_busy = False
                self.has_notified = True  # 加锁，单次触发，绝不重复打断动画
                elapsed = max(1, int(now - self.busy_start_time))
                if elapsed < 60:
                    duration_str = f"{elapsed}s"
                else:
                    m_cnt = elapsed // 60
                    s_cnt = elapsed % 60
                    duration_str = f"{m_cnt}m {s_cnt}s"
                just_completed = True
            else:
                self.is_busy = False

        return self.is_busy, just_completed, duration_str


_TRACKER = SessionActivityTracker()


def get_active_conversation_info():
    """
    极速解析当前前台真正活动的会话信息
    返回: (conv_id, project_name, source)
    """
    # 1. 优先级一：DevTools CDP 极速查询 (感知用户在 UI 上点击 Tab 的瞬间)
    if os.path.exists(PORT_FILE):
        try:
            with open(PORT_FILE, "r", encoding="utf-8") as f:
                port = f.readline().strip()
            if port.isdigit():
                url = f"http://127.0.0.1:{port}/json"
                with urllib.request.urlopen(url, timeout=0.25) as resp:
                    targets = json.loads(resp.read().decode("utf-8", errors="ignore"))

                for t in targets:
                    if t.get("type") == "page":
                        page_url = t.get("url", "")
                        # 匹配 /c/<conversation_id>
                        m = re.search(r"/c/([0-9a-fA-F\-]{36})", page_url)
                        if m:
                            conv_id = m.group(1)
                            title = t.get("title", "")
                            proj = None
                            if " - " in title:
                                parts = [p.strip() for p in title.split(" - ")]
                                if len(parts) >= 3 and parts[-1].lower() == "antigravity":
                                    proj = parts[-2]
                                elif len(parts) == 2 and parts[-1].lower() == "antigravity":
                                    proj = parts[0]
                            return conv_id, proj, "devtools"
        except Exception:
            pass

    # 2. 优先级二：SQLite 数据库只读查询最近记录
    if os.path.exists(DB_PATH):
        try:
            conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
            cur = conn.cursor()
            cur.execute("SELECT conversation_id, workspace_uris FROM conversation_summaries ORDER BY last_modified_time DESC LIMIT 1;")
            row = cur.fetchone()
            conn.close()
            if row:
                conv_id = row[0]
                uris_str = row[1]
                proj = None
                try:
                    uris = json.loads(uris_str) if uris_str else []
                    if uris:
                        raw_uri = uris[0]
                        parts = [p for p in raw_uri.rstrip("/").split("/") if p and not p.endswith(":")]
                        if parts:
                            proj = parts[-1]
                except Exception:
                    pass
                return conv_id, proj, "database"
        except Exception:
            pass

    # 3. 优先级三：扫描 brain 目录中 transcript.jsonl 的最后修改时间
    if os.path.exists(BRAIN_DIR):
        valid = []
        try:
            for d in os.listdir(BRAIN_DIR):
                full_d = os.path.join(BRAIN_DIR, d)
                if os.path.isdir(full_d):
                    lp = os.path.join(full_d, ".system_generated", "logs", "transcript.jsonl")
                    if os.path.exists(lp):
                        valid.append((d, os.path.getmtime(lp)))
            if valid:
                valid.sort(key=lambda x: x[1], reverse=True)
                return valid[0][0], None, "disk_scan"
        except Exception:
            pass

    return None, None, "none"


def extract_project_name(steps):
    """从会话步骤的工具调用参数中提取当前活动工程名称"""
    for step in steps:
        tc_list = step.get("tool_calls", [])
        for tc in tc_list:
            args = tc.get("args", {})
            for key in ["DirectoryPath", "Cwd", "TargetFile", "AbsolutePath", "SearchDirectory"]:
                if key in args:
                    val = str(args[key]).replace('"', '').replace('\\', '/')
                    parts = [p for p in val.split('/') if p and not p.endswith(':')]
                    if parts:
                        name = parts[-1]
                        if '.' in name and len(parts) > 1:
                            name = parts[-2]
                        if name not in ['logs', 'scratch', '.gemini', 'antigravity', 'tmp']:
                            return name
    return "Antigravity"


def detect_pending_action(steps, is_busy):
    """
    探测当前会话是否处于需要用户介入的阻断状态：
    1. 'ask_question': 正在等待用户回答问答交互；
    2. 'plan_approval': implementation_plan 计划已生成且 Agent 进入空闲等待审批；
    3. 'error': 任务执行报错中断。

    返回: (action_type, title, detail, options, extra)
    """
    if not steps:
        return None, "", "", [], {}

    last_step = steps[-1]

    # 1. 正在等待用户回答 ask_question
    for tc in last_step.get("tool_calls", []):
        if tc.get("name") == "ask_question":
            args = tc.get("args", {})
            q_text = "等待回答提问"
            options = []
            is_multi = False
            rec_option = ""
            try:
                q_json = args.get("questions")
                if isinstance(q_json, str):
                    q_json = json.loads(q_json)
                if q_json and isinstance(q_json, list):
                    q_item = q_json[0]
                    q_text = q_item.get("question", q_text)
                    raw_opts = q_item.get("options", [])
                    is_multi = q_item.get("is_multi_select", False)
                    for opt in raw_opts:
                        opt_str = str(opt).strip()
                        options.append(opt_str)
                        if opt_str.startswith("(Recommended)") or opt_str.startswith("(推荐)"):
                            rec_option = opt_str
            except Exception:
                pass
            extra = {
                "is_multi": is_multi,
                "full_question": q_text,
                "recommended": rec_option
            }
            return "ask_question", "等待回答", q_text, options, extra

    # 2. 检查是否有待审批的 implementation_plan (且当前 Agent 已空闲等待用户确认)
    if not is_busy:
        for idx in range(len(steps) - 1, max(-1, len(steps) - 15), -1):
            s = steps[idx]
            if s.get("source") == "USER_EXPLICIT" or s.get("type") == "USER_INPUT":
                break
            for tc in s.get("tool_calls", []):
                if tc.get("name") == "write_to_file":
                    args = tc.get("args", {})
                    tgt = str(args.get("TargetFile", "")).lower()
                    meta = args.get("ArtifactMetadata", {})
                    if isinstance(meta, str):
                        try:
                            meta = json.loads(meta)
                        except Exception:
                            meta = {}
                    if ("implementation_plan.md" in tgt) or (meta.get("RequestFeedback") is True):
                        summary = meta.get("Summary", "")
                        code = args.get("CodeContent", "")
                        plan_title = "实施方案已就绪"
                        files = []
                        steps_list = []

                        # 若未直接带 code，尝试读取本地文件
                        real_target = args.get("TargetFile", "")
                        if not code and real_target and os.path.exists(real_target):
                            try:
                                with open(real_target, "r", encoding="utf-8") as f:
                                    code = f.read()
                            except Exception:
                                pass

                        if code:
                            import re
                            for c_line in code.splitlines():
                                c_line = c_line.strip()
                                if c_line.startswith("# ") and plan_title == "实施方案已就绪":
                                    plan_title = c_line.lstrip("# ").strip()
                                    break

                            # 提取修改/新建/删除的文件名 (#### [MODIFY] [xxx] 等)
                            file_matches = re.findall(r'####\s*\[(?:MODIFY|NEW|DELETE)\]\s*\[?([^\]\n]+)\]?', code)
                            for fm in file_matches:
                                clean_f = os.path.basename(fm.replace('`', '').strip('[]() '))
                                if clean_f and clean_f not in files and not clean_f.startswith("file"):
                                    files.append(clean_f)

                            # 提取核心步骤 (## Proposed Changes 下的子模块或要点)
                            step_matches = re.findall(r'###\s+(?:\[?\d+[\.\、]?\s*)?([^\n#\[\]]+)', code)
                            for sm in step_matches:
                                clean_s = sm.replace('`', '').strip('[]() ')
                                upper_s = clean_s.upper()
                                if any(k in upper_s for k in ["MODIFY", "NEW", "DELETE", "COMPONENT", "PROPOSED"]):
                                    continue
                                if clean_s and clean_s not in steps_list:
                                    steps_list.append(clean_s)

                        elif summary:
                            plan_title = summary.splitlines()[0][:35]

                        extra = {
                            "summary": summary,
                            "files": files[:3],
                            "steps": steps_list[:3],
                        }
                        return "plan_approval", "等待审批", plan_title, ["立即批准", "在IDE中查阅"], extra

    # 3. 检查是否有执行异常报错
    if last_step.get("status") == "ERROR":
        return "error", "任务报错", str(last_step.get("content", ""))[:30], [], {}

    return None, "", "", [], {}


def get_context_metrics(force=False):
    """
    计算当前活动会话的完整上下文指标
    带微秒级智能缓存，极大降低后台轮询开销
    """
    global _CACHE_METRICS, _CACHE_KEY

    conv_id, dev_proj, src = get_active_conversation_info()
    if not conv_id:
        return {
            "has_active": False,
            "project_name": "未检测到工程",
            "total_used": 0,
            "total_limit": TOTAL_CAPACITY,
            "percent": 0.0,
            "model_tokens": 0,
            "tool_tokens": 0,
            "system_tokens": 0,
            "user_tokens": 0,
            "steps_count": 0,
            "file_size_kb": 0.0,
            "conv_id": "none",
            "pending_action": None,
            "pending_title": "",
            "pending_detail": ""
        }

    conv_dir = os.path.join(BRAIN_DIR, conv_id)
    log_path = os.path.join(conv_dir, ".system_generated", "logs", "transcript.jsonl")

    # 会话刚建立尚未生成 transcript.jsonl 时
    if not os.path.exists(log_path):
        proj_name = dev_proj or "Antigravity"
        return {
            "has_active": True,
            "project_name": proj_name,
            "total_used": 4000,
            "total_limit": TOTAL_CAPACITY,
            "percent": 0.38,
            "model_tokens": 0,
            "tool_tokens": 0,
            "system_tokens": 4000,
            "user_tokens": 0,
            "steps_count": 0,
            "file_size_kb": 0.0,
            "conv_id": conv_id,
            "pending_action": None,
            "pending_title": "",
            "pending_detail": ""
        }

    try:
        mtime = os.path.getmtime(log_path)
        fsize = os.path.getsize(log_path)
    except Exception:
        mtime = 0
        fsize = 0

    cache_key = (conv_id, mtime, fsize)
    if not force and _CACHE_METRICS is not None and _CACHE_KEY == cache_key:
        last_src = _CACHE_METRICS.get("last_source", "")
        steps_cnt = _CACHE_METRICS.get("steps_count", 0)
        is_busy, just_comp, dur_str = _TRACKER.update(conv_id, steps_cnt, mtime, last_src)
        _CACHE_METRICS["is_busy"] = is_busy
        _CACHE_METRICS["just_completed"] = just_comp
        _CACHE_METRICS["duration_str"] = dur_str
        if _CACHE_METRICS.get("_has_plan") and not is_busy:
            _CACHE_METRICS["pending_action"] = "plan_approval"
            _CACHE_METRICS["pending_title"] = "等待审批"
            _CACHE_METRICS["pending_detail"] = _CACHE_METRICS.get("pending_detail") or "方案已就绪，等待确认"
            if not _CACHE_METRICS.get("pending_options"):
                _CACHE_METRICS["pending_options"] = ["立即批准", "在IDE中查阅"]
        return _CACHE_METRICS

    # 缓存未命中或文件更新，执行极速解析 (1MB 约 10ms)
    file_size_kb = fsize / 1024.0
    steps = []
    user_chars = 0
    model_chars = 0
    tool_chars = 0

    try:
        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    steps.append(data)
                    s = data.get("source", "")
                    content = str(data.get("content", ""))
                    tc = data.get("tool_calls", [])

                    if s == "USER_EXPLICIT":
                        user_chars += len(content)
                    elif s == "MODEL":
                        model_chars += len(content)
                    elif s == "SYSTEM":
                        tool_chars += len(content)

                    if tc:
                        tool_chars += len(json.dumps(tc, ensure_ascii=False))
                except Exception:
                    continue
    except Exception:
        pass

    last_source = steps[-1].get("source", "") if steps else ""
    is_busy, just_completed, duration_str = _TRACKER.update(conv_id, len(steps), mtime, last_source)

    # 工程名优先采用 DevTools 提取的权威项目名，其次从步骤参数中提取
    project_name = dev_proj or extract_project_name(steps)

    # Token 估算：中英混排约 3.5 字符/Token
    est_user = int(user_chars / 3.5)
    est_model = int(model_chars / 3.5)
    est_tool = int(tool_chars / 3.5)
    est_system = 4000  # 基础 Prompt 与工程规范
    total_used = est_user + est_model + est_tool + est_system

    pct = round((total_used / TOTAL_CAPACITY) * 100, 2)

    pending_act, pending_tit, pending_det, pending_options, pending_extra = detect_pending_action(steps, is_busy)
    has_plan = False
    for idx in range(len(steps) - 1, max(-1, len(steps) - 15), -1):
        s = steps[idx]
        if s.get("source") == "USER_EXPLICIT" or s.get("type") == "USER_INPUT":
            break
        for tc in s.get("tool_calls", []):
            if tc.get("name") == "write_to_file" and "implementation_plan.md" in str(tc.get("args", {})).lower():
                has_plan = True
                break

    result = {
        "has_active": True,
        "project_name": project_name,
        "total_used": total_used,
        "total_limit": TOTAL_CAPACITY,
        "percent": pct,
        "model_tokens": est_model,
        "tool_tokens": est_tool,
        "system_tokens": est_system,
        "user_tokens": est_user,
        "steps_count": len(steps),
        "file_size_kb": round(file_size_kb, 1),
        "conv_id": conv_id,
        "last_source": last_source,
        "is_busy": is_busy,
        "just_completed": just_completed,
        "duration_str": duration_str,
        "pending_action": pending_act,
        "pending_title": pending_tit,
        "pending_detail": pending_det,
        "pending_options": pending_options,
        "pending_files": pending_extra.get("files", []),
        "pending_steps": pending_extra.get("steps", []),
        "pending_extra": pending_extra,
        "_has_plan": has_plan
    }

    _CACHE_KEY = cache_key
    _CACHE_METRICS = result
    return result


if __name__ == "__main__":
    m = get_context_metrics()
    print(json.dumps(m, ensure_ascii=False, indent=2))
