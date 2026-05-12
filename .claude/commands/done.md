# /done — 记录开发日志 + Git 推送

执行此命令时，按以下步骤操作：

## 步骤 1：检查变更

```bash
git status
git diff --stat
```

查看自上次提交以来的所有变更。

## 步骤 2：记录到 DEVLOG

在 `DEVLOG.md` 末尾追加本次变更的记录，格式如下：

```markdown
### v{版本号} — {一句话摘要} ({日期})

**变更内容：**
- {改动1}
- {改动2}
- ...

**决策与反馈：**
- {记录开发过程中发生的重要决策、用户反馈、方向调整}
```

读取 `git diff` 和 `git status` 的输出来自动生成变更内容。决策与反馈部分基于本次对话中的讨论内容提炼。

## 步骤 3：Git 提交与推送

调用 `.claude/skills/git-push.md` 中定义的流程：

1. 确认 `.gitignore` 规则正确
2. `git add -A`
3. `git commit` — 提交信息格式：`v{版本号} — {摘要}`
4. `git tag -a v{版本号} -m "{摘要}"`
5. `git push origin main --tags`

### 版本号规则

查看当前已有的 git tag（`git tag -l`），新版本号在上一个基础上递增。对应关系见 git-push skill 中的标签命名规范。

如果是里程碑之间的增量提交，使用三位版本号递增（如 v0.1.0 → v0.1.1）。

## 步骤 4：确认

向用户报告：
- DEVLOG 已更新
- 已提交到 Git，版本号 v{X.X.X}
- 已推送到 GitHub
