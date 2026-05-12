---
name: pdf-to-md
description: 调用 MinerU 云端 API 将 `workspace/input/` 目录下的 PDF 批量转换为 Markdown（_converted.md 后缀），支持 OCR + 表格识别。阶段 0 文件预处理时由 PM 调用，已转换的 PDF 自动跳过支持断点续转。底层实现 `.claude/skills/pdf-to-md/scripts/pdf_to_md.py`。
---

# Skill：PDF 转 Markdown（MinerU API）

## 基本信息

| 字段 | 值 |
|------|----|
| 当前状态 | 🟢 可用 |
| 调用者 | PM Agent（阶段 0 文件预处理步骤） |
| 底层实现 | `.claude/skills/pdf-to-md/scripts/pdf_to_md.py` |
| 外部依赖 | MinerU 云端 API（mineru.net） |

---

## 触发条件

满足以下所有条件时调用：
- `workspace/input/` 目录下存在 `.pdf` 文件
- 对应的 `_converted.md` 文件尚不存在（脚本自动跳过已转换的文件）
- 当前正在进入阶段 0（接案与初始化）的文件预处理步骤

---

## 前置条件

1. **API Key**：项目根目录的 `.env` 文件中必须包含 `MINERU_API_KEY=...`
2. **Python 环境**：Python 3.10+ 已安装，`requests` 库可用
3. **网络连通**：能访问 `mineru.net` 和阿里云 OSS

---

## 入参

```
输入目录：workspace/input/（含 .pdf 文件）
输出目录：workspace/input/（产出 _converted.md 文件）
API Key：从 .env 的 MINERU_API_KEY 读取
```

---

## 调用方式

```bash
python .claude/skills/pdf-to-md/scripts/pdf_to_md.py --input-dir workspace/input/ --output-dir workspace/input/
```

**可选参数：**
- `--api-key <key>`：直接传入 API Key（优先于 .env）
- `--poll-interval <秒>`：轮询间隔，默认 10 秒
- `--timeout <秒>`：单文件超时，默认 300 秒

**PM Agent 调用时的标准命令：**
```bash
python .claude/skills/pdf-to-md/scripts/pdf_to_md.py --input-dir workspace/input/ --output-dir workspace/input/
```

---

## 处理流程

脚本对 `workspace/input/` 下每个 PDF 自动执行三步：

1. **提交任务** → `POST /api/v4/file-urls/batch`，获取 batch_id 和 OSS 上传 URL
2. **上传文件** → `PUT {OSS URL}`，将 PDF 二进制直传阿里云 OSS（不经过 MinerU 服务器）
3. **轮询取结果** → 每 10 秒 `GET /api/v4/extract-results/batch/{batch_id}`，直到状态为 `done`，下载 ZIP → 解压 → 提取 .md 文件

关键参数（硬编码在脚本中）：
- `is_ocr: true` — 启用 OCR（扫描件必需）
- `enable_table: true` — 启用表格识别
- `language: "ch"` — 中文文档
- `model_version: "pipeline"` — 使用 pipeline 模型

---

## 出参格式

每个 PDF 产出 `workspace/input/[文件名]_converted.md`，格式如下：

```markdown
# [原文件名]

> 来源：workspace/input/[原文件名].pdf
> 转换时间：YYYY-MM-DD HH:MM:SS
> 转换方式：MinerU API (OCR + 表格识别)

## 文档内容

[MinerU 返回的结构化 Markdown，保留标题层级、表格、列表]
```

---

## 退出码

| 退出码 | 含义 |
|--------|------|
| 0 | 全部成功（或无 PDF 需转换） |
| 1 | 部分文件失败 |
| 2 | 全部失败或配置错误 |

---

## 质量检查

转换完成后，PM Agent 应检查：
- `_converted.md` 文件是否成功创建
- 内容是否可读（无乱码、非空白）
- 若失败，报告 PDF 文件名和错误信息，**不重试**，等待律师手动处理

---

## 错误处理

| 错误 | 原因 | PM Agent 动作 |
|------|------|--------------|
| `No API key found` | .env 缺失或未配置 | 告知律师检查 .env 文件 |
| `Polling timed out` | 文件过大或 API 繁忙 | 告知律师稍后重试 |
| `No .md file found in ZIP` | MinerU 解析异常 | 告知律师该 PDF 可能需要手动处理 |
| `Connection error` | 网络不通 | 告知律师检查网络连接 |
