# /preprocess — 证据文件预处理

## 前置检查

1. 读取 `workspace/meta/case-state.json`，确认 `phase` 为 `phase_0_init`。
   - 如果为 `phase_1_preprocess` 且 `lawyer_confirmed` 为 false → 继续未完成的预处理流程（跳到步骤五呈报分组）。
   - 如果为 `phase_2_reading` 或更后 → 提示"预处理已完成，当前处于 {phase}。如需重新预处理，请先联系开发者。"。
   - 如果状态文件不存在 → 提示"尚未初始化案件，请先执行 /init-case"。
2. 读取 `workspace/meta/case-context.json`，获取 `focus_points` 和 `legal_elements_checklist`，用于后续分组排序。
3. 扫描 `workspace/raw/` 目录，检查是否有文件。
   - 如果 `raw/` 为空 → 提示"raw/ 目录为空，请先将证据文件放入 workspace/raw/ 目录。"。

## 步骤一：文件扫描与编号

1. 列出 `workspace/raw/` 下所有文件（排除子目录）。
2. 按文件名自然排序（数字前缀优先）。
3. 为每个文件分配 evidence_id（E001、E002、...），记录：
   - `evidence_id`
   - `original_filename`
   - `format`（根据扩展名判断）
   - `file_size_kb`

向律师报告扫描结果：
```
扫描完成，共发现 {N} 份文件：

| 编号 | 文件名 | 格式 | 大小 |
|------|--------|------|------|
| E001 | xxx.pdf | PDF | xxx KB |
| ... | ... | ... | ... |

开始批量转换...
```

## 步骤二：批量格式转换

使用 `mineru_converter.py` 批量调用 MinerU 标准 API，直接输出到 `workspace/processed/`：

```bash
python .claude/scripts/mineru_converter.py workspace/raw/ --output-dir workspace/processed/ --name-map <映射>
```

**转换引擎：** MinerU 标准 API（OCR + 表格识别），支持 PDF/Word/图片。
**Token：** 从 `.claude/scripts/api.txt` 读取（已配置）。
**已转换跳过：** 同名 `.md` 已存在则自动跳过。

### 输出命名规则

`{证据编号}_{简述}.md`，例如 `E001_建设工程施工合同.md`。

简述从文件名/内容中提取，3-8 字概括核心内容（与步骤三重命名规范中的简述一致）。

转换完成后：
1. 在每份 processed MD 首部添加元信息注释：
   ```
   > 来源：{原始文件名}
   > 类型：{证据类型}
   > 转换日期：{YYYY-MM-DD}
   > 页数：{估计页数}
   ```
2. 对每个文件判断证据类型、提取日期和简述（参照 preprocess skill 第 2、3 节）
3. 质量自检：MD < 100 bytes → `preprocess_status: "failed"`；内容异常 → 标注 notes

### 进度汇报

```
✅ E001 已转换 → processed/E001_建设工程施工合同.md (合同类，2457字)
⚠️ E003 转换异常：转换后内容过少，已标注待确认
```

## 步骤三：统一重命名

根据 preprocess skill 第 3 节的命名规范，为每个文件生成新文件名：

`{序号}_{类型}_{日期}_{简述}.{ext}`

- 序号：两位序号（01, 02, ...）
- 类型：合同类 / 函件类 / 转账类 / 验收类 / 聊天类 / 财务类 / 照片类 / 待分类
- 日期：YYYYMMDD 或 "未知日期"
- 简述：3-8 字

将重命名结果记录到 file-manifest.json 的 `renamed` 字段。

> **注意：** v1 阶段不实际重命名 raw/ 中的文件（保留原始文件名），仅在 file-manifest.json 中记录新文件名。

## 步骤四：生成分组建议

根据 preprocess skill 第 4 节的分组算法，生成分组方案：

1. 将所有证据按类型归类
2. 关联性强的类型合并为一组
3. 硬证据组排在软证据组之前
4. 同组内按日期排序
5. 根据 `case-context.json` 的 `focus_points` 调整优先级

每组包含：
- `group_id`：组号（从 1 开始）
- `label`：组标签（如"合同及主体关系"）
- `mode`：`silent`（默认静默阅读模式）
- `evidence_ids`：该组包含的证据 ID 列表
- 分组理由（一句话说明为什么这样分组）

## 步骤五：呈报律师确认

向律师展示完整的预处理结果：

```
━━━ 预处理完成 ━━━

共处理 {N} 份文件：
- ✅ 成功转换：{M} 份
- ⚠️ 需注意：{X} 份

📄 重命名一览：
| 编号 | 原文件名 | 新文件名 |
|------|----------|----------|
| E001 | ... | 01_合同类_... |
| ... | ... | ... |

📂 建议分组方案：

【第 1 组】{标签}（{N} 份）
  理由：{理由}
  - E001 {简述}
  - E002 {简述}

...

💡 建议：{如果有关注点相关的特殊排序建议，在此说明}

请确认分组方案，或告诉我需要调整的地方（如"把 E010 提到第 1 组"）。
```

等待律师回复。律师可以：
- 直接确认（如"同意"、"OK"、"没问题"）
- 调整分组（如"把 E010 提到第 2 组"）
- 修改命名（如"E005 的日期应该是 2025 年不是 2024 年"）

## 步骤六：写入状态文件

律师确认后，执行以下写入操作：

### 6.1 更新 case-state.json

```python
# 使用 state-manager.py 或直接写入
phase = "phase_1_preprocess"
evidence_count = N  # 文件总数
evidence_unread = N  # 全部标记为未读
```

### 6.2 写入 file-manifest.json

```json
{
  "files": [
    {
      "evidence_id": "E001",
      "original_filename": "...",
      "renamed": "01_合同类_YYYYMMDD_简述.pdf",
      "processed_path": "processed/E001_简述.md",
      "file_size_kb": ...,
      "format": "pdf",
      "category": "hard",
      "type": "合同",
      "preprocess_status": "done",
      "reading_status": "unread",
      "brief_path": null,
      "token_estimate": null,
      "notes": null,
      "source_anchors_enabled": true
    },
    ...
  ]
}
```

### 6.3 写入 reading-plan.json

```json
{
  "groups": [
    {
      "group_id": 1,
      "label": "合同及主体关系",
      "mode": "silent",
      "evidence_ids": ["E001", "E002"],
      "status": "pending"
    },
    ...
  ],
  "reading_order_within_group": "by_date",
  "lawyer_confirmed": true
}
```

### 6.4 更新 review-log.json

追加一条记录：
```json
{
  "timestamp": "...",
  "action": "preprocess_completed",
  "content": "预处理完成，共 {N} 份文件，{M} 组"
}
```

## 步骤七：确认输出

向律师确认：

```
✅ 预处理完成并已保存。

共 {N} 份证据，分为 {M} 组。
转换后的 Markdown 文件在 workspace/processed/ 下。

下一步：执行 /read-group 1 开始阅读第 1 组证据。
```
