#!/usr/bin/env python3
"""卷宗先锋 — 状态管理工具

统一的 JSON 状态文件读写工具，用于管理 workspace/meta/ 下的所有状态文件。
所有写入操作自动更新 updated_at 字段。
"""

import json
import os
import shutil
from datetime import datetime

META_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "workspace", "meta")


def _resolve_path(filename):
    """解析状态文件路径。如果传入绝对路径则直接使用，否则拼接 META_DIR。"""
    if os.path.isabs(filename):
        return filename
    return os.path.join(META_DIR, filename)


def read_state(filename):
    """读取状态文件，返回 dict。文件不存在时返回 None。"""
    path = _resolve_path(filename)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_state(filename, data):
    """写入状态文件（原子写入），自动更新 updated_at。"""
    path = _resolve_path(filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data["updated_at"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    shutil.move(tmp_path, path)
    return data


def update_phase(new_phase):
    """更新 case-state.json 的 phase 字段，自动追加 phase_history。"""
    state = read_state("case-state.json")
    if state is None:
        return None
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    if state.get("phase") and state["phase"] != new_phase:
        state.setdefault("phase_history", []).append({
            "phase": state["phase"],
            "completed_at": now
        })
    state["phase"] = new_phase
    return write_state("case-state.json", state)


def increment_counter(field, delta=1):
    """递增 case-state.json 中的计数字段。"""
    state = read_state("case-state.json")
    if state is None:
        return None
    state[field] = state.get(field, 0) + delta
    return write_state("case-state.json", state)


def append_review_log(action, evidence_id=None, content=None):
    """追加一条审批记录到 review-log.json。"""
    log = read_state("review-log.json")
    if log is None:
        log = {"reviews": []}
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "action": action
    }
    if evidence_id:
        entry["evidence_id"] = evidence_id
    if content:
        entry["content"] = content
    log["reviews"].append(entry)
    return write_state("review-log.json", log)


def append_context_update(source, content):
    """向 case-context.json 追加一条动态更新。"""
    ctx = read_state("case-context.json")
    if ctx is None:
        return None
    ctx.setdefault("updates", []).append({
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "source": source,
        "content": content
    })
    return write_state("case-context.json", ctx)


def update_evidence_status(evidence_id, status_field, new_value):
    """更新 file-manifest.json 中指定证据的某个状态字段。"""
    manifest = read_state("file-manifest.json")
    if manifest is None:
        return None
    for f in manifest.get("files", []):
        if f.get("evidence_id") == evidence_id:
            f[status_field] = new_value
            break
    return write_state("file-manifest.json", manifest)


def init_from_template(template_name, target_filename, overrides=None):
    """从 templates/meta/ 模板初始化一个状态文件。"""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    template_path = os.path.join(base_dir, "templates", "meta", template_name)
    target_path = _resolve_path(target_filename)

    os.makedirs(os.path.dirname(target_path), exist_ok=True)

    with open(template_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if overrides:
        data.update(overrides)

    return write_state(target_filename, data)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python state-manager.py <command> [args...]")
        print("Commands: read <file> | phase <new_phase> | init")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "read":
        result = read_state(sys.argv[2])
        print(json.dumps(result, ensure_ascii=False, indent=2) if result else "File not found")
    elif cmd == "phase":
        result = update_phase(sys.argv[2])
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif cmd == "init":
        for tmpl in ["case-state.json", "case-context.json", "file-manifest.json",
                      "reading-plan.json", "review-log.json"]:
            init_from_template(tmpl, tmpl)
        print("All state files initialized.")
