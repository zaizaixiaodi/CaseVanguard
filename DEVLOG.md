# DEVLOG — 卷宗先锋（CaseVanguard）

## 2026-05-12

### M1：项目脚手架搭建 ✅

**交付物：**
- 完整目录结构（.claude/skills、scripts、commands、templates、workspace）
- `claude.md` — Agent 主指令文件
- `templates/meta/` 下 5 个 JSON 状态文件模板（case-state、case-context、file-manifest、reading-plan、review-log）
- `.claude/scripts/state-manager.py` — 状态管理工具（init、read、write、update_phase、increment_counter 等）

**决策与反馈：**
- claude.md 初始版本包含详细的阶段守卫表格，用户反馈"希望在全面的同时保持精简"。调整策略：阶段守卫的详细逻辑下沉到各命令文件，claude.md 只保留原则性的一句话交互规则。最终 claude.md 约 90 行，7 个章节，后续不再变动。

### M2：/init-case 命令 ✅

**交付物：**
- `.claude/commands/init-case.md` — 完整的初始化流程（前置检查、结构化引导、法律要件拆解、状态文件写入、目录创建、确认输出）
- 内置 7 种常见案由的法律构成要件拆解 + 通用推导方法

### 开发计划调整

**决策记录：**
- M3 预处理：PDF/图片转 MD 复用已有 `mineru-ocr` skill，不写独立转换脚本
- M3 预处理：大表压缩（csv-summarize.py）推迟到 v2，v1 只做基础转换
- 新增 git-push skill（`.claude/skills/git-push.md`），仓库：https://github.com/zaizaixiaodi/CaseVanguard.git
- 新增 `.gitignore`，排除 workspace 下所有案件数据

### v0.1.1 — 修正 git-push skill 注册 + PRD 规范对齐 (2026-05-12)

**变更内容：**
- `.claude/skills/git-push.md`（扁平文件）→ `.claude/skills/git-push/SKILL.md`（目录式结构），补充 YAML frontmatter（name、description、allowed-tools）
- PRD 3.1 目录结构：skills 条目从错误的扁平文件格式修正为 Claude Code 官方规范 `<name>/SKILL.md`
- PRD 3.1：新增 `git-push` skill 和 `done`/`git-push` command 目录条目，新增 Claude Code 目录规范说明块
- PRD 九、命令速查表：补充缺失的 `/done` 和 `/git-push` 命令
- `.claude/commands/done.md`：引用路径从 `.claude/skills/git-push.md` 更新为 `.claude/skills/git-push/SKILL.md`

**决策与反馈：**
- 用户反馈"无法唤起 git-push skill"，经查 Claude Code 官方文档确认根因：skills 必须使用目录式结构（`<name>/SKILL.md`），扁平文件不会被系统识别。commands 则使用扁平 `.md` 文件
- 用户要求"PRD 中与 Claude Code 官方不一致的地方也要改"，已逐项审查并修正

### M1 Walkthrough 验收：✅ 全部通过 (2026-05-12)

| 测试项 | 结果 | 备注 |
|--------|------|------|
| T1.1 claude.md 自动加载 | ✅ | Agent 自我介绍为"卷宗先锋"，红线生效 |
| T1.2 目录结构完整 | ✅ | 与 PRD 3.1 一致，skills 为目录式结构 |
| T1.3 JSON 模板 Schema | ✅ | 5 个文件字段齐全 |
| T1.4 state-manager.py | ✅ | init/read/write 正常。附注：Windows 下 `python` 命令指向 WindowsApps 重定向器（exit 49），需用绝对路径 `C:\Users\Administrator\AppData\Local\Python\bin\python.exe` |
| T1.5 claude.md 内容覆盖 | ✅ | 6 个章节全覆盖 |
| T1.6 git-push skill 注册 | ✅ | skill 列表中可见 |

**环境备注：**
- settings.local.json 已改为 `Bash(*)` 通配符，减少权限弹窗
- 测试数据已放入 `workspace/raw/`：20 份 PDF（建设工程施工合同纠纷相关）

### M2 Walkthrough 验收：✅ 全部通过 (2026-05-12)

**测试案件：** 苏茂公司 诉 武汉成丰学校等 建设工程施工合同纠纷

| 测试项 | 结果 | 备注 |
|--------|------|------|
| T2.1 引导表展示 | ✅ | 7 个字段，不强制填满 |
| T2.2 输入解析 | ✅ | 正确提取案由、当事人、案情 |
| T2.3 假设与关注点补充 | ✅ | 4 条假设、5 条关注点 |
| T2.4 法律要件拆解 | ✅ | 11 项要件，含 3 项重点标注（优先受偿权、多主体效力、加速到期） |
| T2.5 case-state.json | ✅ | 18 字段，phase = phase_0_init |
| T2.6 case-context.json | ✅ | 9 字段，与律师输入一致 |
| T2.7 file-manifest.json | ✅ | `{"files": []}` |
| T2.8 reading-plan.json | ✅ | groups 为空 |
| T2.9 review-log.json | ✅ | `{"reviews": []}` |
| T2.10 workspace 子目录 | ✅ | 5 个子目录全部存在 |
| T2.11 确认输出 | ✅ | 含 session_id、要件拆解、下一步提示 |
| T2.12 二次执行冲突检测 | ✅ | 检测到已有未完成案件并提示 |

**session_id：** session_20260512_151730

