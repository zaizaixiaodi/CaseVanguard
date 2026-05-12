---
name: preprocess
description: 证据文件预处理技能。扫描 raw/ 目录，识别文件格式，将 PDF/图片转为 Markdown，统一重命名，生成分组阅读方案建议。由 /preprocess 命令调用。
allowed-tools: Bash(ls *) Bash(wc *) Bash(python *) Glob Grep Write Edit
---

# Skill：预处理

## 1. 文件格式识别

根据文件扩展名判断格式和处理方式：

| 扩展名 | 格式 | 转换方式 |
|--------|------|----------|
| `.pdf` `.png` `.jpg` `.jpeg` | PDF/图片 | `python .claude/scripts/mineru_converter.py` 调用 MinerU 标准 API（OCR + 表格识别） |
| `.docx` `.doc` `.pptx` `.ppt` | Office 文档 | 同上 |
| `.xls` `.xlsx` `.csv` | 表格 | 同上（MinerU API 不支持，用 Read 工具读取后做基础转换） |
| `.txt` `.md` | 纯文本/Markdown | 直接复制到 processed/ |
| `.mp3` `.wav` `.m4a` `.mp4` `.mov` | 音视频 | v1 阶段由律师提供文字稿，放入 raw/ 作为 .txt 或 .md |

**转换工具说明：**
- `mineru_converter.py` 位于 `.claude/scripts/`，Token 从同目录 `api.txt` 读取
- 已有同名 `.md` 文件会自动跳过，不重复转换
- 超出 MinerU 支持范围的格式（xls/xlsx/csv），Agent 用 Read 工具处理

## 2. 证据类型分类

根据文件名和内容，将证据分为以下类型：

| 类型标签 | 关键词/特征 | 类别 |
|----------|------------|------|
| 合同类 | 合同、协议、契约、补充协议 | hard（硬证据） |
| 转账/付款类 | 转账、回单、流水、付款、收据、发票 | hard |
| 官方文书类 | 回执、决定书、通知、证明、鉴定 | hard |
| 工程/验收类 | 竣工、验收、移交、完工、质检 | hard |
| 沟通函件类 | 函、催告、律师函、通知函 | hard |
| 财务报表类 | 明细、报表、收支、账目、利润 | hard |
| 聊天记录类 | 聊天、微信、截图、对话 | soft（软证据） |
| 照片/图片类 | 照片、图片、现场 | soft |
| 录音文字稿 | 录音、转写、文字稿 | soft |

**判断规则：**
1. 优先从文件名关键词判断
2. 文件名无法判断时，快速扫读内容首段确认
3. 仍无法判断的标注为 `待分类`

## 3. 统一重命名规范

**格式：** `{序号}_{类型}_{日期}_{简述}.pdf`

**序号规则：** 按原始文件名的自然排序（如果文件名含数字前缀则按前缀排序，否则按文件名字母序），从 01 开始。

**日期规则：**
- 从文件名或内容中提取日期，格式 `YYYYMMDD`
- 有明确日期的优先使用
- 仅有年月的，补 01 日（如 `202412` → `20241201`）
- 有多个日期的，取最关键日期（签约日、发文日等）
- 无法提取日期的标注 `未知日期`

**简述规则：**
- 3-8 个字概括文件核心内容
- 去除"扫描全能王"等工具水印
- 去除冗余修饰词

**示例：**
- `01.武汉成丰学校-苏茂建设-建设工程施工合同-扫描全能王 2025-11-09 16.23.pdf` → `01_合同类_未知日期_建设工程施工合同.pdf`
- `02.2024.12.5 工作联系函14.56.pdf` → `02_函件类_20241205_工作联系函.pdf`

> **注意：** v1 阶段不实际重命名 raw/ 中的文件（保留原始文件名），仅在 file-manifest.json 中记录新文件名。

## 4. 分组算法

### 4.1 分组原则

1. **按证据类型和关联性分组**，通常 3-7 组
2. **硬证据组排在软证据组之前**
3. **同组内按日期排序**（早期在前）
4. **律师关注点驱动排序**：与 `case-context.json` 中 `focus_points` 关联度高的证据优先

### 4.2 分组步骤

1. 将所有证据按类型标签归类
2. 关联性强的类型合并为一组（如"合同类"和"验收类"都与合同履行相关）
3. 对每组内的证据按日期排序
4. 根据 `case-context.json` 的 `focus_points` 调整组间优先级：
   - 匹配方法：检查证据类型/简述是否包含 focus_points 中的关键词
   - 匹配到的组提升排序优先级
5. 输出每组含：组号、标签、包含的证据 ID 列表、分组理由

### 4.3 排序优先级

```
1. 合同及主体关系组（含协议、身份证明）
2. 工程完工验收组（含竣工、移交、验收）
3. 财务付款组（含转账、流水、收据）
4. 沟通函件组（含工作联系函、律师函、催告）
5. 聊天记录组（含微信截图、对话记录）
6. 其他组
```

以上为默认排序，律师关注点可调整。

## 5. 格式转换规范

### 5.1 PDF/图片/Office → Markdown

使用 `mineru_converter.py` 批量转换，直接输出到 `workspace/processed/`：

```bash
python .claude/scripts/mineru_converter.py <raw_dir>/ --output-dir workspace/processed/ --name-map <映射>
```

输出文件命名规则：`{证据编号}_{简述}.md`，例如 `E001_建设工程施工合同.md`。

转换完成后，在文件首部添加元信息注释：

```
> 来源：{原始文件名}
> 类型：{证据类型}
> 转换日期：{YYYY-MM-DD}
> 页数：{估计页数}
```

### 5.2 不支持的格式（Excel/CSV 等）

MinerU API 不支持 Excel/CSV，Agent 用 Read 工具直接读取：
- 保留表头 + 前 5 行样本
- 统计总行数和关键分组
- 超过 100 行生成压缩摘要

### 5.3 质量自检

转换完成后检查：
- MD 文件小于 100 bytes → 标注 `preprocess_status: "failed"`
- 内容大量乱码或空白 → 标注 `notes: "OCR 质量待确认"`
- 正常 → `preprocess_status: "done"`

## 6. file-manifest.json 条目格式

每份证据的条目：

```json
{
  "evidence_id": "E001",
  "original_filename": "原始文件名.pdf",
  "renamed": "01_合同类_YYYYMMDD_简述.pdf",
  "processed_path": "processed/E001_简述.md",
  "file_size_kb": 2048,
  "format": "pdf",
  "category": "hard",
  "type": "合同",
  "preprocess_status": "done",
  "reading_status": "unread",
  "brief_path": null,
  "token_estimate": null,
  "notes": null,
  "source_anchors_enabled": true
}
```

**字段说明：**
- `evidence_id`：格式 E + 三位序号，从 E001 开始
- `category`：`hard`（硬证据）或 `soft`（软证据）
- `type`：对应第 2 节的类型标签
- `preprocess_status`：`done` / `failed` / `skipped`
- `reading_status`：`unread` / `reading` / `read` / `pending_review` / `approved`
- `notes`：转换过程中的特殊说明
