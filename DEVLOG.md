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
