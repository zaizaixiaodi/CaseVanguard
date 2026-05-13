# /clean-workspace — 清理工作区（归档案件）

> 适用场景：当前案件已完成（报告已定稿），律师需要清理工作区以便开始新案件。本命令会归档当前案件的所有文件，然后重建空的 workspace 目录结构。

## 前置检查

1. 读取 `workspace/meta/case-state.json`。
   - 如果文件不存在 → 提示"工作区已经是空的，无需清理。"。
2. 检查 `report_finalized` 状态：
   - 如果为 `false` → **警告**"当前案件报告尚未定稿（状态：{report_generated ? '已生成未定稿' : '未生成'}）。归档前请确认是否需要先定稿报告。确定要继续归档吗？"
   - 等待律师确认"是"或"确定"才继续。
   - 律师说"取消"或"不" → 终止，不执行归档。
3. 如果 `report_finalized` 为 `true` → 直接继续（仍需最终确认）。

## 步骤一：确认归档

向律师展示归档摘要并请求最终确认：

```
━━━ 工作区清理确认 ━━━

即将归档以下案件：
**案件：** {case_name}
**编号：** {case_id}
**证据数：** {evidence_count} 份
**报告版本：** v{report_version} ({report_finalized ? "已定稿" : "未定稿"})
**增量轮次：** {supplementary_rounds}

归档目标：workspace_archive/{case_id}/

归档内容：
- workspace/raw/（原始证据文件）
- workspace/processed/（转换后文件）
- workspace/briefs/（精要文件）
- workspace/meta/（状态文件）
- workspace/versions/（历史版本）
- workspace/ 下的所有 .md 文件（精要大合集、验证报告、时间线、案件初探精要等）

⚠️ 此操作不可逆。确认归档请回复"确认"。
```

等待律师回复"确认"才继续。其他回复 → 终止。

## 步骤二：执行归档

1. 创建归档目录 `workspace_archive/{case_id}/`（如果不存在）。
2. 将以下内容移动到归档目录：
   - `workspace/raw/` → `workspace_archive/{case_id}/raw/`
   - `workspace/processed/` → `workspace_archive/{case_id}/processed/`
   - `workspace/briefs/` → `workspace_archive/{case_id}/briefs/`
   - `workspace/meta/` → `workspace_archive/{case_id}/meta/`
   - `workspace/versions/` → `workspace_archive/{case_id}/versions/`
   - `workspace/*.md` → `workspace_archive/{case_id}/`
3. 使用 bash 命令执行移动：

```bash
mkdir -p workspace_archive/{case_id}
mv workspace/raw workspace_archive/{case_id}/raw
mv workspace/processed workspace_archive/{case_id}/processed
mv workspace/briefs workspace_archive/{case_id}/briefs
mv workspace/meta workspace_archive/{case_id}/meta
mv workspace/versions workspace_archive/{case_id}/versions
mv workspace/*.md workspace_archive/{case_id}/
```

## 步骤三：重建空 workspace

重建空的 workspace 目录结构：

```bash
mkdir -p workspace/raw
mkdir -p workspace/processed
mkdir -p workspace/briefs
mkdir -p workspace/meta
mkdir -p workspace/versions
```

## 步骤四：确认输出

```
✅ 工作区已清理完毕。

已归档案件：{case_name}（{case_id}）
归档位置：workspace_archive/{case_id}/

workspace/ 已恢复为空的初始目录结构。

下一步：执行 /init-case 初始化新案件。
```
