# /read-next [E编号] — 阅读下一份或指定证据

## 前置检查

1. 读取 `workspace/meta/case-state.json`，确认 `phase`。
   - 如果为 `phase_2_reading` → 继续。
   - 如果为 `phase_1_preprocess` → 提示"尚未开始阅读，请先执行 /read-group {n}"。
   - 如果为 `phase_0_init` → 提示"尚未完成预处理，请先执行 /preprocess"。
   - 如果为 `phase_3_cross_verify` 或更后 → 提示"已进入 {phase}，如需重新阅读，请先联系开发者。"。
2. 读取 `workspace/meta/reading-plan.json`，找到 status=`in_progress` 的组。
   - 如果没有 in_progress 的组 → 提示"当前没有正在阅读的组。请执行 /read-group {n} 开始新组。"。
   - 如果组有 `paused_at` 字段 → 从暂停的证据继续。
3. 读取 `workspace/meta/file-manifest.json`，确认有 `reading_status = "unread"` 的证据。
   - 如果当前组内全部已读但未 approved → 提示"当前组已全部阅读，等待审阅。可执行 /approve 审批本组。"。

## 参数处理

- **无参数：** 在当前 in_progress 组中，按 `evidence_ids` 顺序取下一份 `reading_status = "unread"` 的证据。
- **指定 E编号：** 读取指定证据（可在当前组内或跨组）。如果该证据已读，提示"证据 {E编号} 已生成精要，如需修改请使用 /revise"。

## 步骤一：定位证据

1. 确定目标证据 ID。
2. 从 `file-manifest.json` 获取证据信息（`processed_path`、`type`、`category` 等）。
3. 调用 `state-manager.py` 的 `update_evidence_status(evidence_id, "reading_status", "reading")`。

## 步骤二：读取原文

1. 读取 `workspace/processed/E{NNN}_*.md` 全文。
2. 记录行号信息，为后续原文锚点做准备。

## 步骤三：生成证据精要

按照 `read-evidence` skill 的规则提取精要（同 /read-group 步骤三）：

1. **七要素提取：** 逐项检查主体信息、意思表示、效力事项、权利义务条款、失衡事实、抗辩事由、金额相关。
2. **法庭试金石：** 对不确定的细节使用补充判断。
3. **原文锚点：** 每条摘录记录行号范围（格式：`E001.md#L45-L52`）。
4. **大表处理：** 如遇大型表格，按统计摘要规则处理。
5. **梗概撰写：** 3-5 句话，纯客观事实。
6. **关联性分析：** 对照 focus_points 和 legal_elements_checklist，标注关联。

## 步骤四：即时交叉验证

1. 从 `file-manifest.json` 找到当前组内所有 `reading_status` 为 `pending_review` 或 `approved` 的证据。
2. 读取这些证据的精要文件（`workspace/briefs/E{NNN}_brief.md`）。
3. 执行轻量级增量比对：
   - **时间线冲突：** 本证据中的日期/事件是否与已读证据矛盾
   - **金额不一致：** 本证据中的金额是否与已读证据冲突
   - **主体矛盾：** 本证据中的主体信息是否与已读证据不一致
4. **处理结果：**
   - **发现矛盾：** 在精要"交叉验证"区标注 `⚠️ 交叉验证警告`，描述矛盾内容和涉及证据。调用 `state-manager.py` 的 `update_group_status(group_id, "in_progress", paused_at=evidence_id, pause_reason="发现 {evidence_id} 与 E{xxx} 存在{矛盾类型}：{描述}")`。中断并向律师汇报。
   - **未发现矛盾：** 在精要"交叉验证"区记录印证关系和发现的关联。静默继续。

## 步骤五：保存精要并更新状态

1. 按 `templates/evidence-brief.md` 模板格式生成精要（含交叉验证区），保存到 `workspace/briefs/E{NNN}_brief.md`。
2. 调用 `state-manager.py`：
   - `update_evidence_status(evidence_id, "reading_status", "pending_review")`
   - `update_evidence_status(evidence_id, "brief_path", "briefs/E{NNN}_brief.md")`
   - `increment_counter("evidence_read")`
   - `increment_counter("evidence_unread", -1)`
   - `append_review_log("brief_generated", evidence_id, "生成精要：E{NNN}" + (交叉验证结果摘要))`
3. 如果步骤四触发了暂停（发现矛盾），跳到步骤七输出暂停汇报。

## 步骤六：检查组/全局完成状态

1. 检查当前组的所有 `evidence_ids` 是否都已非 `unread`：
   - **组内全部读完 →** 调用 `update_group_status(group_id, "completed")`，追加 review-log（action: `group_reading_completed`）。
   - 检查是否所有组都是 `completed`：
     - **全部组完成 →** 更新 `case-state.json`：`first_pass_completed = true`。提示"所有证据已完成首轮阅读！下一步：/cross-verify 全局交叉验证"。
     - **还有未完成组 →** 提示"第{n}组已完成。下一步：/read-group {下一组号} 开始下一组"。
   - **组内还有未读 →** 提示继续 `/read-next`。

## 步骤七：输出精要

**正常输出：**

```
━━━ 第{n}组 · {label} ━━━

正在阅读 E{NNN}（{简述}）...

{精要全文}

📌 第{n}组进度：{已读}/{总数}
{下一步提示：/read-next 继续 | 组完成提示 | 全部完成提示}
```

**暂停输出（发现矛盾时）：**

```
━━━ 第{n}组 · {label} ━━━

正在阅读 E{NNN}（{简述}）...

{精要全文}

⚠️ 交叉验证警告：发现 E{NNN} 与 E{xxx} 存在{矛盾类型}：
- {矛盾描述}

已暂停阅读。请律师确认后回复"继续"，我将从 E{NNN} 后继续阅读。
```
