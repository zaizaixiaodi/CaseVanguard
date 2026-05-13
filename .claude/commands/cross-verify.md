# /cross-verify — 全局交叉验证

## 前置检查

1. 读取 `workspace/meta/case-state.json`，确认状态：
   - `first_pass_completed` 须为 `true` → 继续。
   - 如果为 `false` → 提示"尚有证据未完成首轮阅读，请先完成所有组的阅读和审批。"。
   - `cross_verify_completed` 为 `true` → 提示"已完成全局交叉验证。如需重新验证，请先确认。"。
2. 读取 `workspace/meta/file-manifest.json`，确认 `evidence_approved > 0`。
   - 如果为 0 → 提示"尚无已审批的证据精要，请先使用 /approve 审批精要。"。
3. 确认 `workspace/精要大合集-evidence-collection.md` 存在。
   - 不存在 → 提示"精要大合集尚未生成，请先使用 /approve 生成。"。

## 步骤一：初始化

1. 更新 `case-state.json`：`phase` → `"phase_3_cross_verify"`。
2. 读取 `workspace/meta/case-context.json`（重点关注 `legal_elements_checklist` 和 `focus_points`）。
3. 读取 `workspace/精要大合集-evidence-collection.md` 全文。

## 步骤二：时间线验证

按 `cross-verify` skill 维度一的方法论执行：

1. 从精要大合集中提取全部日期-事件对（如签约、开工、完工、交付、付款、催告、发函等）。
2. 按时间排序，构建案件时间线。
3. 检测矛盾：同一事件不同日期、逻辑倒置、关键节点缺失、日期模糊。
4. **生成副产品 `workspace/案件时间线-timeline.md`**：按时间排序的事件表，标注证据来源。

## 步骤三：金额校验

按 `cross-verify` skill 维度二的方法论执行：

1. 提取全部金额信息，按类别分组（合同约定/实际支付/欠付主张/关联金额）。
2. 验证算术关系：合同价 - 已付 ≈ 欠付（5%误差范围）。
3. 检查金额来源一致性、异常资金流向。
4. 输出金额校验表和不一致项。

## 步骤四：主体校验

按 `cross-verify` skill 维度三的方法论执行：

1. 提取全部主体及其角色（签约方/建设单位/施工单位/付款方/收款方/发函方等）。
2. 构建主体角色矩阵。
3. 检测身份链矛盾：签约方vs履行方vs付款方vs收款方是否一致。
4. 追踪新主体：标注未在合同中出现的主体的案件关系。
5. 输出主体角色矩阵和矛盾项。

## 步骤五：法律要件缺口分析

按 `cross-verify` skill 维度四的方法论执行：

1. 读取 `case-context.json` 的 `legal_elements_checklist`（11项要件）。
2. 逐一遍历每个要件，在精要大合集中查找支撑证据。
3. 评估充分性：
   - **✅ 充分支撑：** 有直接证据证明该要件成立，列出支撑证据编号。
   - **⚠️ 部分支撑：** 有间接证据但存在缺口，标注缺少什么。
   - **❌ 无证据：** 无任何证据触及该要件，建议补充方向。
4. 对照 `focus_points`（律师关注点），检查每个关注点对应的要件是否有足够证据。
5. **更新 `case-context.json`**：将 `legal_elements_checklist` 的每项从 `null` 更新为 `{status, supporting_evidence, gap_note}` 对象。

## 步骤六：生成验证报告

1. 汇总四维验证结果，按 `cross-verify` skill 第3节的报告格式生成。
2. 从四维结果中提取风险提示：
   - 🔴 **严重风险：** 时间线重大矛盾、金额核心不一致、主体身份链断裂、要件缺失
   - 🟡 **注意事项：** 次要矛盾、部分缺口、需确认事项
3. 基于风险提示和缺口分析，生成下一步行动建议。
4. 将验证报告保存到 `workspace/交叉验证报告-cross-verify-report.md`。
5. 更新 `case-state.json`：`cross_verify_completed` → `true`。
6. 追加 `review-log.json`：
   - `action: "cross_verify_completed"`
   - `content: "四维验证完成：时间线{N}项矛盾/金额{N}项异常/主体{N}项矛盾/要件{N}项缺口"`

## 步骤七：输出

```
━━━ 全局交叉验证报告 ━━━

**验证维度：** 时间线 / 金额 / 主体 / 法律要件
**证据总数：** 19 份

## 摘要

- 时间线：{N} 项矛盾（🔴{n} / 🟡{n}）
- 金额：{N} 项异常
- 主体：{N} 项矛盾
- 法律要件：✅{n} / ⚠️{n} / ❌{n}

## 🔴 严重风险
{严重风险列表}

## 🟡 注意事项
{注意事项列表}

## 📌 下一步行动建议
{行动建议列表}

完整报告已保存至 workspace/交叉验证报告-cross-verify-report.md
时间线已保存至 workspace/案件时间线-timeline.md

下一步：/generate-report 生成《案件初探精要》
```

向律师输出完整验证报告全文供审阅。
