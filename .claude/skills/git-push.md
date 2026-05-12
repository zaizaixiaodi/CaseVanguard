# Skill：Git 推送

## 基本信息

| 字段 | 值 |
|------|----|
| 状态 | 可用 |
| 调用者 | 律师直接指示 |
| 远程仓库 | https://github.com/zaizaixiaodi/CaseVanguard.git |

---

## 触发条件

- 律师说"推送""提交""上传到 GitHub"
- 里程碑开发完成后需要保存版本

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
- `claude.md`、`.claude/skills/`、`.claude/commands/`、`.claude/scripts/`、`templates/`

确认以下内容**已排除**（不应提交）：
- `workspace/raw/`（原始证据文件）
- `workspace/processed/`（转换后文件）
- `workspace/briefs/`（精要文件）
- `workspace/meta/`（案件状态）
- `workspace/*.md`（案件交付物）
- `workspace/versions/`（历史版本）
- `workspace_archive/`（归档案件）
- `.env`（含 API Key）

### 步骤 3：暂存并提交

```bash
git status
git diff --stat

git add -A

git commit -m "$(cat <<'EOF'
v[版本号] — [一句话摘要]

包含：
- [改动1]
- [改动2]

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

### 步骤 4：打标签

```bash
git tag -a v[版本号] -m "[里程碑摘要]"
git tag -l
```

**标签命名规范：**

| 标签 | 对应 |
|------|------|
| `v0.1.0` | M1：项目脚手架 + 状态管理 |
| `v0.2.0` | M2：/init-case 案件初始化 |
| `v0.3.0` | M3：/preprocess 预处理 |
| `v0.4.0` | M4：/read-group + /read-next 精要生成 |
| `v0.5.0` | M5：/approve + /revise + 精要大合集 |
| `v0.6.0` | M6：即时交叉验证 |
| `v0.7.0` | M7：/cross-verify 全局交叉验证 |
| `v0.8.0` | M8：/generate-report 案件初探精要 |
| `v0.9.0` | M9：回溯与增量命令 |
| `v1.0.0` | M10：辅助命令 + 脚手架管理，完整可用 |

### 步骤 5：推送

```bash
# 首次推送
git remote add origin https://github.com/zaizaixiaodi/CaseVanguard.git
"/c/Program Files/GitHub CLI/gh.exe" auth setup-git
git push -u origin main --tags

# 后续推送
git push origin main --tags
```

> **关键：** 推送前必须运行 `gh auth setup-git`，否则 git push 会报 403。

### 步骤 6：验证

```bash
"/c/Program Files/GitHub CLI/gh.exe" repo view zaizaixiaodi/CaseVanguard --web
```

---

## 认证排障

### gh 未登录

**方案 A — Token 认证（推荐）：**

1. 在 https://github.com/settings/tokens?type=beta 生成 Token
2. 权限必勾：**Contents** (Read and write) + **Metadata** (Read-only)
3. 执行：
```bash
echo "TOKEN" | "/c/Program Files/GitHub CLI/gh.exe" auth login --with-token
"/c/Program Files/GitHub CLI/gh.exe" auth setup-git
```

**方案 B — 浏览器登录：**

律师在终端运行：`"C:\Program Files\GitHub CLI\gh.exe" auth login`
- 选 GitHub.com → HTTPS → Login with a web browser

### git push 报 403

重新生成 Token，确保勾选 **Contents (Read and write)**。

### git push 报 Password authentication not supported

```bash
"/c/Program Files/GitHub CLI/gh.exe" auth setup-git
```

### gh 命令找不到

用绝对路径 `"/c/Program Files/GitHub CLI/gh.exe"` 调用。
