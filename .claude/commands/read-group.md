# /read-group [组号] — 按分组阅读证据

## 前置检查

1. 读取 `workspace/meta/case-state.json`，确认 `phase`。
   - 如果为 `phase_1_preprocess` → 首次进入 Phase 2，调用 `state-manager.py` 的 `update_phase("phase_2_reading")`。
   - 如果为 `phase_2_reading` → 继续。
   - 如果为 `phase_0_init` → 提示"尚未完成预处理，请先执行 /preprocess"。
   - 如果为 `phase_3_cross_verify` 或更后 → 提示"已进入 {phase}，如需重新阅读，请先联系开发者。"。
   - 如果状态文件不存在 → 提示"尚未初始化案件，请先执行 /init-case"。
2. 读取 `workspace/meta/reading-plan.json`，确认目标组。
   - 如果未指定组号 → 提示"请指定组号，如 /read-group 1。当前分组：{列出各组编号和标签}"。
   - 如果指定组号不存在 → 提示"组号 {n} 不存在，当前有 {M} 组"。
   - 如果目标组 status=`completed` → 提示"第 {n} 组已完成阅读。可用 /read-group {下一组号} 开始下一组。"。
   - 如果目标组 status=`in_progress` 且有 `paused_at` → 提示"第 {n} 组曾因 {pause_reason} 暂停于 E{xxx}，从暂停处继续。"。
   - 如果有其他组 status=`in_progress` → 提示"第 {other_n} 组正在阅读中，请先用 /read-next 完成当前组。"。

## 步骤一：初始化阅读上下文

1. 读取 `workspace/meta/case-context.json`，获取：
   - `focus_points`（律师关注点）
   - `legal_elements_checklist`（法律要件清单）
2. 读取 `workspace/meta/file-manifest.json`，获取目标组的证据文件信息。
3. 更新 `reading-plan.json` 中目标组的 `status` → `in_progress`（通过 `state-manager.py` 的 `update_group_status(group_id, "in_progress")`）。
4. 追加 `review-log.json`：`{action: "group_reading_started", content: "开始阅读第{n}组：{label}（{M}份证据）"}`。

## 步骤二：读取第一份证据

1. 取目标组 `evidence_ids` 列表中的第一份 `reading_status = "unread"` 的证据。
2. 调用 `state-manager.py` 的 `update_evidence_status(evidence_id, "reading_status", "reading")`。
3. 读取对应的 `workspace/processed/E{NNN}_*.md` 全文。

## 步骤三：生成证据精要

按照 `read-evidence` skill 的规则提取精要：

1. **七要素提取：** 逐项检查主体信息、意思表示、效力事项、权利义务条款、失衡事实、抗辩事由、金额相关。
2. **法庭试金石：** 对不确定的细节使用补充判断。
3. **原文锚点：** 每条摘录记录行号范围（格式：`E001.md#L45-L52`）。
4. **大表处理：** 如遇大型表格，按统计摘要规则处理。
5. **梗概撰写：** 3-5 句话，纯客观事实。
6. **关联性分析：** 对照 focus_points 和 legal_elements_checklist，标注关联。

## 步骤四：保存精要并更新状态

1. 按 `templates/evidence-brief.md` 模板格式生成精要，保存到 `workspace/briefs/E{NNN}_brief.md`。
2. 调用 `state-manager.py`：
   - `update_evidence_status(evidence_id, "reading_status", "pending_review")`
   - `update_evidence_status(evidence_id, "brief_path", "briefs/E{NNN}_brief.md")`
   - `increment_counter("evidence_read")`
   - `increment_counter("evidence_unread", -1)`
   - `append_review_log("brief_generated", evidence_id, "生成精要：E{NNN}")`

## 步骤五：输出精要并提示

向律师展示精要内容：

```
━━━ 第{n}组 · {label} ━━━

正在阅读 E{NNN}（{简述}）...

{精要全文}

📌 这是第{n}组的第 1 份证据（共{M}份）。
下一步：/read-next 继续阅读下一份，或先审阅本精要。
```
