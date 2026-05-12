# /revise — 修改证据精要

## 前置检查

1. 读取 `workspace/meta/case-state.json`，确认 `phase`。
   - 如果为 `phase_2_reading` → 继续。
   - 其他阶段 → 提示"当前不在阅读阶段，无法修改精要。"。
2. 确认律师提供了目标证据编号和修改意见。如果缺少，提示"/revise {E编号} {修改意见}"。

## 参数解析

律师输入格式：`/revise {E编号} {修改意见}`

- **E编号**（必需）：要修改的证据编号（如 E005）。
- **修改意见**（必需）：律师的具体修改要求。

## 步骤一：定位目标证据

1. 读取 `workspace/meta/file-manifest.json`，找到指定 `evidence_id` 的条目。
   - 如果不存在 → 提示"未找到证据 {E编号}。"。
   - 如果 `reading_status` 为 `"unread"` → 提示"证据 {E编号} 尚未阅读，请先使用 /read-next {E编号}。"。
2. 记录证据的 `processed_path`（原文路径）和 `brief_path`（当前精要路径）。

## 步骤二：更新状态为"修改中"

1. 更新 `file-manifest.json`：`reading_status` → `"revising"`。
2. 追加 `review-log.json`：
   - `action: "revision_requested"`
   - `evidence_id: "{E编号}"`
   - `content: "律师修改意见：{修改意见}"`

## 步骤三：重读原文 + 结合修改意见重新生成精要

1. 读取 `workspace/processed/E{NNN}_*.md` 全文。
2. 读取当前精要 `workspace/briefs/E{NNN}_brief.md`。
3. 对照律师的修改意见，按 `read-evidence` skill 的规则重新生成精要：
   - 保留原有正确的摘录不变。
   - 针对律师修改意见补充或修正对应内容。
   - 在修正处添加批注标记（如"（依律师意见补充）"）。
   - 保持原文锚点格式不变。
4. 将新精要写入 `workspace/briefs/E{NNN}_brief.md`（覆盖旧版）。

## 步骤四：更新状态为待复审

1. 更新 `file-manifest.json`：`reading_status` → `"pending_review"`。
2. 追加 `review-log.json`：
   - `action: "brief_revised"`
   - `evidence_id: "{E编号}"`
   - `content: "精要已按律师意见修改，待复审"`

## 步骤五：输出修改结果

向律师输出：

```
📝 证据 {E编号} 精要已按您的意见修改：

**修改意见：** {律师的修改意见}
**修改内容：**
- {列出具体修改的条目}

请审阅修改后的精要。如满意，使用 /approve 通过；如需进一步修改，再次使用 /revise。
```

同时输出修改后精要的完整内容供律师审阅。
