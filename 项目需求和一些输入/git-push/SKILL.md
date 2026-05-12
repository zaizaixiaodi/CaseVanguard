---
name: git-push
description: 版本推送 Skill。将当前项目状态 commit + tag + push 到 GitHub，供律师或 AI 在模块开发完成后调用。含前置检查、认证排障、标签管理。
---

# Skill：Git 推送

## 基本信息

| 字段 | 值 |
|------|----|
| 状态 | 🟢 可用 |
| 调用者 | PM Agent / 律师直接指示 |
| 远程仓库 | https://github.com/zaizaixiaodi/agent1.git |

---

## 触发条件

- 律师说"推送""提交""上传到 GitHub"
- 模块开发完成后需要保存版本

---

## 前置环境

| 依赖 | 检查命令 | 期望结果 |
|------|---------|---------|
| Git | `git --version` | git version 2.x |
| GitHub CLI | `"/c/Program Files/GitHub CLI/gh.exe" --version` | gh version 2.x |
| 认证 | `"/c/Program Files/GitHub CLI/gh.exe" auth status` | Logged in to github.com |

> **注意：** Windows 上 `gh` 安装后不在 bash 的 PATH 里，必须用绝对路径 `"/c/Program Files/GitHub CLI/gh.exe"` 调用。PowerShell 中可直接用 `gh`。

---

## 执行流程

### 步骤 1：前置检查

```bash
# 检查是否在 git 仓库内
git rev-parse --is-inside-work-tree

# 若返回错误 → 需要先 git init（仅首次）
```

检查认证状态：

```bash
"/c/Program Files/GitHub CLI/gh.exe" auth status
```

- 若显示 `Logged in to github.com` → 继续
- 若显示 `not logged in` → 进入**认证排障**（见下方）

### 步骤 2：确认 .gitignore

读取 `.gitignore`，确认以下内容**未被排除**（应该被跟踪）：
- `.claude/agents/`、`.claude/skills/`、`templates/`、`CLAUDE.md`、`DEVLOG.md`、`README.md`

确认以下内容**已排除**（不应提交）：
- `.env`（含 API Key）
- `workspace/input/*.pdf`、`workspace/input/*_converted.md`（真实案件数据）
- `workspace/dossier/`、`workspace/memory/`、`workspace/docs/`（案件隐私）
- `workspace/Context_Status.md`、`workspace/.agent-state.json`（运行状态）

### 步骤 3：暂存并提交

```bash
# 查看变更
git status
git diff --stat

# 暂存（不要 git add -A，逐文件确认更安全）
git add -A

# 提交（HEREDOC 格式，支持中文和特殊字符）
git commit -m "$(cat <<'EOF'
v[版本号] — [一句话摘要]

包含：
- [改动1]
- [改动2]

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

### 步骤 4：打标签

```bash
# 创建带注释的标签
git tag -a v[版本号] -m "[模块名称摘要]"

# 查看已有标签
git tag -l
```

**标签命名规范：**

| 标签 | 对应 |
|------|------|
| `v0.1.0` | 模块0：项目脚手架 |
| `v0.2.0` | 模块2：调查员Agent |
| `v0.3.0` | 模块3：战略家Agent |
| `v0.4.0` | 模块4：搜索Agent |
| `v0.9.0` | 模块0.9：Skills/Subagents 规范化 + Workspace 解耦 |
| `v0.5.0` | 模块5：总攻+红蓝对抗 |
| ... | 每个模块完成打一个 |

### 步骤 5：推送

```bash
# 首次推送（添加远程 + 推送）
git remote add origin https://github.com/zaizaixiaodi/agent1.git
"/c/Program Files/GitHub CLI/gh.exe" auth setup-git
git push -u origin main --tags

# 后续推送（远程已配置）
git push origin main --tags
```

> **关键：** 推送前必须运行 `gh auth setup-git`，否则 git push 会报 403（Token 认证不生效于 git 操作）。

### 步骤 6：验证

```bash
"/c/Program Files/GitHub CLI/gh.exe" repo view zaizaixiaodi/agent1 --web
# 或直接访问 https://github.com/zaizaixiaodi/agent1
```

---

## 认证排障

### 场景：gh 未登录

**症状：** `gh auth status` 显示 `not logged in`

**解决方案（二选一）：**

**方案 A — Token 认证（推荐，可自动化）：**

1. 让律师在 https://github.com/settings/tokens?type=beta 生成 Token
2. 权限必勾：**Contents** (Read and write) + **Metadata** (Read-only)
3. 执行：
```bash
echo "TOKEN" | "/c/Program Files/GitHub CLI/gh.exe" auth login --with-token
"/c/Program Files/GitHub CLI/gh.exe" auth setup-git
```

**方案 B — 浏览器登录（需律师操作）：**

律师在终端运行：`"C:\Program Files\GitHub CLI\gh.exe" auth login`
- 选 GitHub.com → HTTPS → Login with a web browser

### 场景：git push 报 403

**症状：** `remote: Write access to repository not granted`

**原因：** Token 权限不足（只有 read 没有 write）

**解决：** 重新生成 Token，确保勾选 **Contents (Read and write)**

### 场景：git push 报 Password authentication not supported

**症状：** `Password authentication is not supported for Git operations`

**原因：** git 没有配置使用 gh 的凭证助手

**解决：**
```bash
"/c/Program Files/GitHub CLI/gh.exe" auth setup-git
```

### 场景：gh 命令找不到

**症状：** `gh: command not found`

**原因：** winget 安装后 PATH 未生效

**解决：** 用绝对路径 `"/c/Program Files/GitHub CLI/gh.exe"` 调用

---

## 一键推送模板（AI 可直接执行）

```
给律师的提示词模板：
"模块X已开发完成。请允许我执行 git 推送，将本次改动保存到 GitHub。"

执行命令序列：
1. git status && git diff --stat        # 检查变更
2. git add -A                           # 暂存
3. git commit -m "v0.X.0 — [摘要] ..."  # 提交
4. git tag -a v0.X.0 -m "[摘要]"        # 打标签
5. git push origin main --tags          # 推送
6. 向律师报告：推送成功，标签 v0.X.0 已创建
```
