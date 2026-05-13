# /re-read — 重新阅读证据（增量回溯）

> 适用场景：首次阅读已完成（first_pass_completed），律师要求对某份证据以新的重点关注方向重新阅读。不同于 /revise（律师直接修改精要文字），/re-read 是重新从原文出发，按新方向深度提取。

## 前置检查

1. 读取 `workspace/meta/case-state.json`，确认 `first_pass_completed` 为 `true`。
   - 如果为 `false` → 提示"首次阅读尚未完成，请先完成 /read-next 流程。"。
2. 确认律师提供了目标证据编号和重点关注方向。如果缺少，提示用法：`/re-read {E编号} {重点关注方向}`。

## 参数解析

律师输入格式：`/re-read {E编号} {重点关注方向}`

- **E编号**（必需）：要重新阅读的证据编号（如 E003）。
- **重点关注方向**（必需）：律师希望 Agent 重新聚焦的分析方向。

## 步骤一：定位目标证据

1. 读取 `workspace/meta/file-manifest.json`，找到指定 `evidence_id` 的条目。
   - 如果不存在 → 提示"未找到证据 {E编号}。"。
   - 如果 `reading_status` 为 `"unread"` → 提示"证据 {E编号} 尚未首次阅读，请先使用 /read-next {E编号}。"。
2. 记录 `processed_path`（原文路径）和 `brief_path`（当前精要路径）。

## 步骤二：记录重新阅读

1. 更新 `file-manifest.json`：`reading_status` → `"re_reading"`。
2. 追加 `review-log.json`：
   - `action: "re_read_requested"`
   - `evidence_id: "{E编号}"`
   - `content: "律师要求重新阅读，重点：{重点关注方向}"`

## 步骤三：按新重点重新阅读原文

1. 读取 `workspace/processed/E{NNN}_*.md` 全文。
2. 读取当前精要 `workspace/briefs/E{NNN}_brief.md`。
3. 读取 `workspace/meta/case-context.json` 获取 `focus_points` 和 `legal_elements_checklist`。
4. 按 `read-evidence` skill 的七要素规则重新生成精要，但进行以下调整：
   - **优先提取**与重点关注方向相关的细节，深度展开。
   - **保留**现有精要中仍准确且与案件相关的摘录。
   - **扩展或修改**与重点方向相关的内容，在新增/修改处标注 `（依律师意见补充）`。
   - **保持**源锚点格式 `E{NNN}.md#L{行号}`。
   - **保持**精要模板格式（标题、七要素结构、总结、交叉验证）。

## 步骤四：增量交叉验证

1. 读取 `workspace/精要大合集-evidence-collection.md` 全部已审批精要。
2. 对重新生成的精要 vs 全部已有精要，执行四维增量验证：
   - **时间线**：新精要中的日期与已有精要是否产生新矛盾或解决已有矛盾。
   - **金额**：新提取的金额信息与已有金额是否一致。
   - **主体**：新精要中的主体/角色信息与已有主体是否一致。
   - **法律要件**：重新聚焦后是否改变了对 `legal_elements_checklist` 中某项要件的覆盖。
3. 生成交量验证摘要（不写入独立报告，嵌入输出中）。

## 步骤五：保存与更新状态

1. 将新精要写入 `workspace/briefs/E{NNN}_brief.md`（覆盖旧版）。
2. 更新 `file-manifest.json`：`reading_status` → `"pending_review"`。
3. 追加 `review-log.json`：
   - `action: "re_read_completed"`
   - `evidence_id: "{E编号}"`
   - `content: "证据 {E编号} 已按重点「{重点关注方向}」重新阅读，新精要待审批"`

## 步骤六：输出

向律师输出：

```
--- 证据 {E编号} 重新阅读完成 ---

**重新阅读重点：** {重点关注方向}
**原文：** {processed_path}
**新精要：** {brief_path}

{新精要全文}

--- 增量交叉验证 ---

**时间线：** {新矛盾或一致数量} 项
**金额：** {新异常或已解决数量} 项
**主体：** {新矛盾数量} 项
**法律要件：** {覆盖变化}

{任何新矛盾或发现的详细说明}

请审阅新精要。如满意，使用 /approve 通过；如需调整，再次使用 /re-read {E编号} {新重点方向}。
```

## 审批后处理（/approve 增强）

律师使用 `/approve` 通过后，Agent 需要执行以下额外操作：

1. **替换** `精要大合集-evidence-collection.md` 中的已有精要（而非追加）：
   - 定位 `### E{NNN} —` 标题行。
   - 选取从此标题到下一个 `### E` 或 `## 第` 或 `## 压缩比` 或文件尾之间的内容。
   - 用新精要替换该块。
2. 更新 `case-state.json`：
   - `supplementary_rounds` += 1
   - `report_outdated` = true
3. 追加 `review-log.json`：
   - `action: "re_read_approved"`
   - `evidence_id: "{E编号}"`
   - `content: "证据 {E编号} 重新阅读审批通过，精要大合集已更新"`
4. 向律师提示：
   ```
   证据 {E编号} 已通过审批，精要大合集已更新。

   supplementary_rounds: {新值}
   报告状态: 已过期（建议执行 /generate-report 重新生成）

   下一步：
   1. /generate-report — 生成更新后的案件初探精要
   2. /re-read {其他E编号} {重点} — 继续重新阅读其他证据
   3. /add-evidence — 追加新证据
   ```

## 状态流转

```
approved → re_reading → pending_review → approved
  (定位)    (记录)       (精要生成)      (律师审批，替换合集)
```
