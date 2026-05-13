# /generate-report — 生成案件初探精要

## 前置检查

1. 读取 `workspace/meta/case-state.json`，确认状态：
   - `cross_verify_completed` 须为 `true` → 继续。
   - 如果为 `false` → 提示"尚未完成全局交叉验证，请先执行 /cross-verify"。
   - `report_finalized` 为 `true` → 提示"报告已定稿（v{version}）。如需修改，请直接编辑文件后告知。"。
2. 确认以下文件存在：
   - `workspace/evidence-collection.md`
   - `workspace/cross-verify-report.md`
   - `workspace/meta/case-context.json`

## 步骤一：判断案件复杂度

按 `generate-deliverable` skill 第1节的规则判断：

1. 读取 `file-manifest.json`，统计证据数量和类型（硬/软）。
2. 读取 `case-context.json`，统计涉及主体数量和争点数量。
3. 综合判断复杂度（简单/中等/复杂）。
4. 确定字数目标和是否需要 Executive Summary。

## 步骤二：读取输入

1. 读取 `workspace/evidence-collection.md` 全文（精要大合集）。
2. 读取 `workspace/cross-verify-report.md` 全文（验证报告）。
3. 读取 `workspace/timeline.md`（时间线）。
4. 读取 `workspace/meta/case-context.json`（案件背景、法律要件、律师关注点）。
5. 读取 `workspace/meta/case-state.json`（session_id 等元数据）。

## 步骤三：生成报告

按 `generate-deliverable` skill 的撰写规范和字数分配，逐章节撰写：

1. **页眉元数据：** 填写案件名称、案由、日期、证据数量、版本号、复杂度、session_id。
2. **Executive Summary：** 仅复杂案件。≤200字，纯事实摘要。
3. **一、案件概况（~300字）：** 基于精要大合集和案件背景，概述案件基本事实。
4. **二、案件大事记（~400字）：** 基于 timeline.md 提炼关键事件，以表格呈现。
5. **三、初步证据目录（~500字）：** 按组展示精要大合集内容，每组概述+关键发现+警告。
6. **四、风险提示与证据链断裂点（~400字）：** 基于验证报告的风险提示和缺口分析。
7. **五、下一步行动计划（~400字）：** 基于验证报告的行动建议+律师关注点。
8. **附：关键细节速查表：** 从精要大合集和验证报告中提取决定性细节，每条含原文锚点。

## 步骤四：自检

按 `generate-deliverable` skill 第5节的自检规则：

1. **字数自检：** 统计正文字数（一至五章），确认在目标范围内。
2. **锚点自检：** 速查表每条是否包含原文锚点。
3. **事实来源自检：** 正文中的关键事实是否可追溯到证据编号。
4. **不做法律判断自检：** 确认无法律结论性表述。

如果自检不通过，调整报告内容后重新自检。

## 步骤五：版本管理与保存

1. 如果 `workspace/case-probe-report.md` 已存在：
   - 读取当前版本号
   - 将当前文件复制到 `workspace/versions/case-probe-report_v{old_version}.md`
   - 新版本号 = 旧版本号 + 0.1
2. 如果不存在（首次生成）：
   - 版本号 = "1.0"
3. 将报告写入 `workspace/case-probe-report.md`（头部标注版本号）。
4. 更新 `case-state.json`：
   - `report_generated` → `true`
   - `report_version` → "{version}"
5. 追加 `review-log.json`：
   - `action: "report_generated"`
   - `content: "生成案件初探精要 v{version}，复杂度{级别}，正文{n}字"`

## 步骤六：输出

```
━━━ 案件初探精要 ━━━

**版本：** v{version}
**复杂度：** {级别}
**正文字数：** {n} 字（目标 {range}）
**速查表条目：** {n} 条

报告已保存至 workspace/case-probe-report.md

请审阅报告。您可以：
1. 直接编辑文件（修改后告知我更新版本）
2. 对话告诉我修改意见（我将修改并生成新版本）
3. 确认定稿（回复"定稿"，我将标记报告为最终版）
```

向律师输出报告全文供审阅。

## 定稿流程（律师确认后触发）

当律师说"定稿"或"确认"时：

1. 更新 `case-state.json`：
   - `report_finalized` → `true`
2. 将当前版本标记为 `final`：
   - 复制到 `workspace/versions/case-probe-report_v{version}_final.md`
3. 追加 `review-log.json`：
   - `action: "report_finalized"`
   - `content: "案件初探精要 v{version} 已定稿"`
4. 向律师确认定稿完成。
