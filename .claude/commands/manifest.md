# /manifest — 查看证据文件清单

> 适用于预处理之后的任何阶段。以表格形式展示所有证据文件及其当前状态。

## 前置检查

1. 读取 `workspace/meta/file-manifest.json`。
   - 如果文件不存在 → 提示"尚未执行预处理，请先执行 /preprocess"。

## 无参数：展示全部

以表格形式展示所有证据文件：

```
━━━ 证据文件清单 ━━━

共 {N} 份证据

| 编号 | 文件名 | 类型 | 状态 | 组别 |
|------|--------|------|------|------|
| E001 | 建设工程施工合同 | 合同 | ✅ 已审批 | 第1组 |
| E003 | 工程联系函 | 函件 | ✅ 已审批 | 第2组 |
| ... | ... | ... | ... | ... |

统计：已审批 {n1} | 待审 {n2} | 未读 {n3} | 其他 {n4}
```

### 状态映射

| reading_status | 显示 |
|----------------|------|
| `unread` | 未读 |
| `reading` | 阅读中 |
| `re_reading` | 重新阅读中 |
| `pending_review` | 待审 |
| `revising` | 修改中 |
| `approved` | ✅ 已审批 |

### 组别映射

从 `workspace/meta/reading-plan.json` 读取每个证据所属的组。

## 带参数：按状态筛选

律师可以指定筛选条件：
- `/manifest 未读` — 只显示 reading_status 为 unread 的
- `/manifest 待审` — 只显示 pending_review 的
- `/manifest 已审批` — 只显示 approved 的

输出格式与全部展示相同，但仅包含匹配的条目。
