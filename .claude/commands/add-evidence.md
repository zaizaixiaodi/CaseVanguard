# /add-evidence — 追加新证据（增量更新）

> 适用场景：首次阅读已完成（first_pass_completed），律师获得了新的证据文件，需要追加到现有案件中。本命令整合了预处理（转换+编号+分组）、阅读（精要生成+即时交叉验证）、审批入库和增量全局验证的完整流程。

## 前置检查

1. 读取 `workspace/meta/case-state.json`，确认 `first_pass_completed` 为 `true`。
   - 如果为 `false` → 提示"首次阅读尚未完成，请先完成 /read-next 流程。"。
2. 扫描 `workspace/raw/` 目录，列出所有文件名。
3. 读取 `workspace/meta/file-manifest.json`，获取所有已有证据的 `original_filename`。
4. 比对确定**新文件**（raw/ 中存在但 manifest 中未记录的文件）。
   - 如果没有新文件 → 提示"未发现新文件。请将新证据文件放入 workspace/raw/ 目录后再执行 /add-evidence。"。

## 步骤一：新文件扫描与编号

1. 对新文件按文件名自然排序。
2. 确定起始编号：`next_number = case-state.json 的 evidence_count + 1`。
3. 为每个新文件分配顺序的 `evidence_id`（如当前 19 份，新文件从 E020 开始）。
4. 根据文件扩展名判断格式，记录文件大小。

向律师报告扫描结果：

```
--- 新证据扫描 ---

发现 {N} 份新文件：

| 编号 | 文件名 | 格式 | 大小 |
|------|--------|------|------|
| E020 | xxx.pdf | PDF | xxx KB |
| ... | ... | ... | ... |

开始批量转换...
```

## 步骤二：批量格式转换

使用 `mineru_converter.py` 对新文件进行批量转换（复用 preprocess 流程）：

```bash
python .claude/scripts/mineru_converter.py workspace/raw/ --output-dir workspace/processed/ --name-map <新文件映射>
```

- 输出命名：`E{NNN}_{简述}.md`。
- 已转换文件自动跳过（幂等）。
- 每份转换后添加元信息注释。
- 质量自检：MD < 100 bytes → `preprocess_status: "failed"`。
- 根据文件内容判断证据类型（复用 preprocess skill 第 2 节逻辑）。

## 步骤三：分组建议

1. 读取 `workspace/meta/reading-plan.json` 现有组。
2. 对每份新证据，根据其类型和内容确定组分配：
   - **匹配现有组**：类型与某现有组一致 → 分入该组。
   - **创建新组**：不匹配任何现有组 → 建议创建新组（group_id = max + 1）。
3. 向律师展示分组建议：

```
--- 新证据分组建议 ---

- E020 → 第{N}组：{组标签}（新增）
- E021 → 新组：{新组标签}

请确认分组，或告诉我需要调整的地方。
```

等待律师确认。律师可以：
- 直接确认
- 调整分组（如"E021 也放到第 3 组"）

## 步骤四：写入状态文件

律师确认分组后，更新以下文件：

### 4.1 追加 file-manifest.json

在 `files` 数组末尾追加新证据条目：

```json
{
  "evidence_id": "E020",
  "original_filename": "新文件名.pdf",
  "renamed": "20_{类型}_{日期}_{简述}.pdf",
  "processed_path": "processed/E020_{简述}.md",
  "file_size_kb": ...,
  "format": "pdf",
  "category": "hard/soft",
  "type": "{类型}",
  "preprocess_status": "done",
  "reading_status": "unread",
  "brief_path": null,
  "token_estimate": null,
  "notes": null,
  "source_anchors_enabled": true
}
```

### 4.2 更新 reading-plan.json

- 将新证据 ID 追加到对应组的 `evidence_ids` 数组。
- 如果是新组，追加完整组对象。
- 将相关组 `status` 改为 `"in_progress"`（如果有新证据加入）。

### 4.3 更新 case-state.json

- `evidence_count` += N（新文件数量）
- `evidence_unread` += N

### 4.4 追加 review-log.json

- `action: "add_evidence_scanned"`
- `content: "扫描到{N}份新证据（E020-E021），等待分组确认"`

## 步骤五：逐份阅读生成精要

对每份新证据（按组排序，组内按日期排序）：

### 5.1 阅读原文

1. 更新 `file-manifest.json`：`reading_status` → `"reading"`。
2. 读取 `workspace/processed/E{NNN}_*.md` 全文。
3. 读取 `workspace/meta/case-context.json` 获取 `focus_points` 和 `legal_elements_checklist`。

### 5.2 生成精要

按 `read-evidence` skill 的七要素规则生成精要：
- 兜底七要素提取。
- 法庭试金石判断。
- 大表统计摘要。
- 源锚点标注（`E{NNN}.md#L{行号}`）。
- 3-5 句总结。
- 关联性分析（映射到 focus_points 和 legal_elements_checklist）。

### 5.3 即时交叉验证

读取 `workspace/精要大合集-evidence-collection.md` 全部已有精要，执行即时交叉验证（复用 read-next 步骤四逻辑）：
- 提取事实卡片（日期、金额、主体）。
- 与全部已有 approved 精要进行三维比对。
- 严重性分级：🔴 严重 / 🟡 注意 / ⚪ 一致。

### 5.4 保存精要

1. 写入 `workspace/briefs/E{NNN}_brief.md`。
2. 更新 `file-manifest.json`：`reading_status` → `"pending_review"`，`brief_path` → `"briefs/E{NNN}_brief.md"`。
3. 追加 `review-log.json`：
   - `action: "brief_generated"`
   - `evidence_id: "{E编号}"`
   - `content: "新增证据 {E编号} 精要已生成（增量阅读）"`

### 5.5 展示精要

向律师展示精要全文和即时交叉验证结果，等待律师确认后再阅读下一份，或批量审阅后统一审批。

## 步骤六：审批入库

律师使用 `/approve` 审批新精要后：

1. 在 `workspace/精要大合集-evidence-collection.md` 对应组中**追加**新精要：
   - 定位目标组的 `## 第{n}组：{标签}` 部分。
   - 在该组已有精要之后、下一个 `## 第` 标题之前插入新精要。
   - 如果是新组，在最后一个已有组之后添加新组标题和精要。
2. 更新 `file-manifest.json`：`reading_status` → `"approved"`。
3. 更新 `case-state.json`：
   - `evidence_approved` += 1
   - `evidence_read` += 1
   - `evidence_unread` -= 1
4. 追加 `review-log.json`：
   - `action: "add_evidence_approved"`
   - `evidence_id: "{E编号}"`
   - `content: "新增证据 {E编号} 审批通过，已追加到精要大合集"`

## 步骤七：增量交叉验证（全部审批后）

所有新证据审批完成后，自动执行增量交叉验证：

1. 读取更新后的 `workspace/精要大合集-evidence-collection.md`（包含新精要）。
2. 对每份新证据精要 vs 全部已有精要，执行四维增量验证：
   - **时间线**：新日期是否与已有日期产生新矛盾？是否填补了时间线空白？
   - **金额**：新金额与已有金额是否一致？是否有新的算术关系需要验证？
   - **主体**：新主体/角色是否与已有信息一致？是否揭示了新的关系？
   - **法律要件**：新证据是否改变了对 `case-context.json` 中 `legal_elements_checklist` 某项要件的覆盖？
3. 生成增量验证报告，保存到 `workspace/增量验证报告-incremental-verify-report.md`：

```markdown
# 增量交叉验证报告

**案件：** {case_name}
**验证时间：** {timestamp}
**触发原因：** 新增证据（/add-evidence）
**变更证据：** {新 E IDs}
**比对范围：** 变更证据 vs 全部{N}份已有精要

## 一、新增/变更发现

### 时间线
{新矛盾或确认}

### 金额
{新异常或确认}

### 主体
{新矛盾或确认}

### 法律要件
{覆盖变化}

## 二、缺口变化

| 要件 | 变更前 | 变更后 | 说明 |
|------|--------|--------|------|

## 三、建议

- {是否需要重新生成报告}
- {其他建议}
```

4. 更新 `workspace/案件时间线-timeline.md`：从新精要中提取新事件，插入到时间顺序正确位置。
5. 更新 `workspace/meta/case-context.json`：如果 `legal_elements_checklist` 项目发生变化，更新对应条目。
6. 更新 `case-state.json`：
   - `supplementary_rounds` += 1
   - `report_outdated` = true
7. 追加 `review-log.json`：
   - `action: "incremental_verify_completed"`
   - `content: "增量验证完成：新增{N}份证据，发现{M}项新矛盾/异常"`

## 步骤八：最终输出

向律师展示：

```
--- 新增证据处理完成 ---

新增：{E020}, {E021}（共{N}份）
审批通过：{N} 份
增量交叉验证：{发现数量} 项新发现

**增量验证报告：** workspace/增量验证报告-incremental-verify-report.md
**时间线已更新：** workspace/案件时间线-timeline.md

supplementary_rounds: {新值}
报告状态: 已过期（建议执行 /generate-report 重新生成）

下一步：
1. /generate-report — 生成更新后的案件初探精要
2. /re-read {E编号} {重点} — 重新阅读某份证据
3. /add-evidence — 继续追加更多证据
```
