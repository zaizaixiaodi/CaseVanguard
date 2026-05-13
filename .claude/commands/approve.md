# /approve — 审批证据精要

## 前置检查

1. 读取 `workspace/meta/case-state.json`，确认 `first_pass_completed` 为 `true`。
   - 如果为 `true` → 继续。
   - 如果为 `false` → 提示"首次阅读尚未完成，无法执行审批。"。
2. 读取 `workspace/meta/file-manifest.json`，确认有 `reading_status = "pending_review"` 的证据。
   - 如果没有 → 提示"当前没有待审批的精要。"。

## 参数解析

律师输入可能有以下形式（本命令无显式参数，律师通过自然语言表达意图）：

- **无额外说明：** 审批当前组内所有 `pending_review` 状态的精要。
- **排除某份：** 如"approve，但 E005 需要修改"、"全部通过，E003 再看看"。将排除的证据 ID 收集到 `excluded_ids` 列表。
- **指定某几份：** 如"通过 E001 和 E007"。只审批指定的证据。

## 步骤一：确定审批范围

1. 读取 `workspace/meta/reading-plan.json`，找到当前包含 `pending_review` 证据的组。
2. 根据律师输入确定：
   - `to_approve`：本次要审批的证据 ID 列表。
   - `excluded_ids`：律师要求修改的证据 ID 列表（不审批，引导使用 /revise）。
3. 对 `excluded_ids` 中的每份证据，输出"已排除：{E编号}，请使用 /revise {E编号} [修改意见] 提交修改意见。"。

## 步骤二：逐份入库

对 `to_approve` 中的每份证据：

1. 读取 `workspace/briefs/E{NNN}_brief.md`。
2. 检查该证据是否已存在于 `workspace/精要大合集-evidence-collection.md` 中：
   - 搜索 `### E{NNN} —` 标题。
   - **如果存在**（re-read 场景）：替换该精要块。
     - 定位从 `### E{NNN} —` 到下一个 `### E` 或 `## 第` 或 `## 压缩比` 或文件尾之间的所有内容。
     - 用新精要内容替换该块。
   - **如果不存在**（首次审批或 add-evidence 场景）：追加到对应组。
     - 如果文件不存在，先按 `templates/精要大合集-evidence-collection.md` 模板创建。
     - 追加时按分组排列，每组前加 `## 第{n}组：{组标签}` 标题。
3. 更新 `file-manifest.json`：
   - `reading_status` → `"approved"`
4. 追加 `review-log.json`：
   - `action: "approved"`（首次审批）或 `action: "re_read_approved"`（重新阅读后审批）
   - `evidence_id: "{E编号}"`
   - `content: "精要已审批通过并入库"` 或 `"重新阅读审批通过，精要大合集已更新"`（re-read 场景）

**re-read 审批后的额外状态更新：**
- 更新 `case-state.json`：
  - `supplementary_rounds` += 1
  - `report_outdated` = true
- 向律师提示报告已过期，建议执行 `/generate-report` 重新生成。

## 步骤三：更新计数器

1. 更新 `case-state.json`：
   - `evidence_approved` += len(to_approve)
   - `evidence_pending_review` -= len(to_approve)

## 步骤四：检测完成状态

1. 读取 `file-manifest.json`，检查是否所有证据的 `reading_status` 都为 `"approved"`。
2. 如果全部 approved：
   - `case-state.json` 的 `first_pass_completed` → `true`
   - 追加 `review-log.json`：`action: "all_approved"`, `content: "全部{N}份证据精要已审批通过"`
   - 提示律师"全部精要已入库。下一步可执行 /cross-verify 进入全局交叉验证。"
3. 如果仍有未审批的：
   - 统计剩余 `pending_review` 和 `unread` 数量，向律师汇报进度。

## 步骤五：压缩比自检

全部入库完成后，执行压缩比自检：

1. 计算 `workspace/processed/` 下所有 MD 文件的总大小（字节）。
2. 计算 `workspace/精要大合集-evidence-collection.md` 的大小（字节）。
3. 计算压缩比 = 精要大合集大小 / 原始MD总大小。
4. 输出自检报告：
   ```
   📊 压缩比自检：原始 MD {X}KB → 精要大合集 {Y}KB（约 1/{ratio}）
   ```
5. 如果压缩比 > 1/4（即精要超过原文的25%）：
   - 输出 ⚠️ 提示："压缩比未达目标（≤1/4）。请自查精要中是否存在冗余或整段复制原文的情况。"
6. 如果压缩比 ≤ 1/4：
   - 输出 ✅ "压缩比达标"

## 步骤六：输出确认

向律师输出审批结果摘要：

```
✅ 已审批通过：{E001}, {E007}, ...（共{n}份）
📝 已排除待修改：{E005}（请使用 /revise E005 [修改意见]）
📊 进度：{已审批}/{总数}，剩余待审批 {pending} 份，未读 {unread} 份
```
