# /status — 查看案件当前状态

> 适用于任何阶段。律师随时可查看案件进度和下一步建议。

## 执行步骤

### 步骤一：读取状态文件

1. 读取 `workspace/meta/case-state.json`。
2. 如果文件不存在 → 提示"尚未初始化案件，请先执行 /init-case"。

### 步骤二：计算进度

从 `case-state.json` 提取以下信息：

- **案件名称：** `case_name`
- **案件编号：** `case_id`
- **当前阶段：** `phase`（映射为中文标签）
- **证据进度：** 已读/已审批/待审/未读/总数
- **增量轮次：** `supplementary_rounds`
- **交叉验证：** 是否完成
- **报告状态：** 是否生成/是否定稿/版本号/是否过期

### 阶段映射

| phase 值 | 中文标签 |
|----------|----------|
| `phase_0_init` | 案件初始化 |
| `phase_1_preprocess` | 预处理 |
| `phase_2_reading` | 分组阅读 |
| `phase_3_cross_verify` | 全局交叉验证 |

### 步骤三：输出状态面板

```
━━━ 案件状态 ━━━

**案件：** {case_name}
**编号：** {case_id}
**创建时间：** {created_at}
**当前阶段：** {阶段中文标签}

--- 证据进度 ---
已审批：{evidence_approved} 份 | 已阅读：{evidence_read} 份 | 待审：{evidence_pending_review} 份 | 未读：{evidence_unread} 份
总证据数：{evidence_count} 份
首次阅读完成：{first_pass_completed ? "是" : "否"}
增量轮次：{supplementary_rounds}

--- 验证与报告 ---
全局交叉验证：{cross_verify_completed ? "已完成" : "未完成"}
报告生成：{report_generated ? "已生成 v" + report_version : "未生成"}
报告定稿：{report_finalized ? "已定稿" : "未定稿"}
报告状态：{report_outdated ? "已过期（精要大合集有更新，建议重新生成）" : "当前"}

--- 下一步建议 ---
{根据当前阶段和进度，给出 1-2 条建议}
```

### 下一步建议规则

| 当前状态 | 建议 |
|----------|------|
| phase_0_init | 执行 /init-case 初始化案件 |
| phase_1_preprocess, lawyer_confirmed=false | 确认分组方案 |
| phase_1_preprocess, lawyer_confirmed=true | 执行 /read-group 1 开始阅读 |
| phase_2_reading, evidence_pending_review > 0 | 执行 /approve 审批待审精要 |
| phase_2_reading, evidence_unread > 0 | 执行 /read-next 继续阅读 |
| phase_2_reading, first_pass_completed=false | 继续阅读剩余证据 |
| first_pass_completed=true, cross_verify_completed=false | 执行 /cross-verify 全局交叉验证 |
| cross_verify_completed=true, report_generated=false | 执行 /generate-report 生成案件初探精要 |
| report_generated=true, report_finalized=false | 审阅报告后回复"定稿" |
| report_finalized=true, report_outdated=true | 执行 /generate-report 重新生成报告 |
| report_finalized=true, report_outdated=false | 案件初探精要已定稿。可使用 /re-read 重新阅读证据或 /add-evidence 追加新证据 |
