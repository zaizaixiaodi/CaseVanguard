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

### M3：预处理能力 + /preprocess ✅

**交付物：**
- `.claude/skills/preprocess/SKILL.md` — 预处理技能（文件识别、分类、重命名、分组算法）
- `.claude/commands/preprocess.md` — 预处理命令（7步标准流程）
- `.claude/scripts/mineru_converter.py` — 从 pdf2md 移植的 MinerU 标准 API 转换器
- `.claude/scripts/api.txt` — MinerU API Token（已加入 .gitignore）

**技术决策：**
- PDF → MD 转换方案从"Read 工具 + mineru-ocr skill"改为"mineru_converter.py（Python + MinerU 标准 API）"。原因：
  - pdftoppm 未安装在 Windows 环境，Read 工具无法读取 PDF
  - mineru-ocr skill 的 convert.js 使用 JXA（macOS-only），Windows 不可用
  - 用户提供了 pdf2md 工具（`项目需求和一些输入/pdf2md/`），基于 Python + requests + MinerU API，跨平台可用
- mineru_converter.py 放在 `.claude/scripts/`，Token 从同目录 `api.txt` 读取，不提交到 Git

### M3 Walkthrough 验收：✅ 全部通过 (2026-05-12)

| 测试项 | 结果 | 备注 |
|--------|------|------|
| T3.1 文件扫描 | ✅ | 19 份 PDF 文件全部记录，编号 E001-E019（跳过 E008，原始排序中 08 空缺） |
| T3.2 格式转换 | ✅ | 19/19 全部转换成功，MinerU 标准 API（OCR+表格识别），总计 161.5KB MD |
| T3.3 processed/ 目录 | ✅ | 19 份 E{NNN}.md 文件，均含元信息注释头（来源/格式/转换日期） |
| T3.4 重命名 | ✅ | file-manifest.json 中 `renamed` 字段符合 `{序号}_{类型}_{日期}_{简述}` 规范 |
| T3.5 分组建议 | ✅ | 5 组，硬证据优先，含分组理由，覆盖律师关注点"多主体债务关联" |
| T3.6 律师确认分组 | ✅ | 律师确认"没问题"，reading-plan.json 更新 lawyer_confirmed = true |

**转换质量抽查：**
- E001（建设工程施工合同）：11KB，主体/价款/工期/计价条款完整，少量 OCR 错字
- E007（付款协议书）：7KB，欠款金额 62,000,019.54 元、多主体清单、付款节点清晰

**环境依赖记录：**
- pdftoppm：未安装（Windows 缺少 poppler-utils），Read 工具 PDF 读取不可用
- mineru-ocr JXA 脚本：macOS 专有，Windows 不可用
- Python requests 库：已安装（v2.32.5），mineru_converter.py 正常工作
- MinerU Token：有效，api.txt 已加入 .gitignore 防止泄漏

**session_id：** session_20260512_151730

### v0.1.3 — M3预处理能力 + MinerU转换器移植 + Walkthrough验收通过 (2026-05-12)

**变更内容：**
- 新增 `.claude/skills/preprocess/SKILL.md` — 预处理技能（格式识别、证据分类、重命名规范、分组算法）
- 新增 `.claude/commands/preprocess.md` — `/preprocess` 命令（7步标准流程：扫描→转换→重命名→分组→确认→写入→输出）
- 移植 `.claude/scripts/mineru_converter.py` — 从用户 pdf2md 工具移植，Python + MinerU 标准 API，跨平台 PDF→MD
- 更新 `.gitignore` — 排除 api.txt、__pycache__/、converted/、项目需求和一些输入/
- 更新 `DEVLOG.md` — M3 开发记录与 Walkthrough 验收（T3.1-T3.6 全部通过）

**决策与反馈：**
- 原方案（Read 工具 / mineru-ocr JXA）在 Windows 不可用，用户提供 pdf2md 参考工具后直接移植，大幅简化预处理管道
- 19 份真实案件证据 PDF 全部转换成功（161.5KB MD），分为 5 组，律师确认通过

### v0.1.4 — 预处理管道优化：消除中转目录 + 语义化文件命名 (2026-05-12)

**变更内容：**
- `mineru_converter.py`：`convert_and_save()` 新增 `output_dir` 和 `output_name` 参数，`convert_folder()` 新增 `name_map` 映射，不再硬编码输出到 `scripts/converted/`
- `preprocess.md`：步骤二改为直接输出到 `workspace/processed/E{NNN}_简述.md`，去掉 `scripts/converted/` 中转流程
- `preprocess/SKILL.md`：第 5 节同步更新输出路径和命名规则
- `processed/` 下 19 份文件从 `E001.md` 重命名为 `E001_建设工程施工合同.md` 等语义化名称
- `file-manifest.json` 的 `processed_path` 全部同步更新
- 删除 `.claude/scripts/converted/`（19 份冗余副本）
- 删除 `workspace/processed/_mapping.json`（不再需要映射桥接）

**决策与反馈：**
- 用户指出预处理阶段产生两处冗余：`scripts/converted/` 存放案件数据污染代码目录，`processed/E001.md` 纯序号命名缺乏辨识度
- 用户接受序号但要求加原始名简述，最终确定 `{E编号}_{简述关键词}.md` 命名规则
- 映射关系直接记在 `file-manifest.json` 中，`_mapping.json` 成为冗余层，一并清理

### v0.1.5 — M4分组阅读实现 + 19份证据精要全部生成 + 审批模拟 (2026-05-12)

**变更内容：**
- 新增 `.claude/skills/read-evidence/SKILL.md` — 阅读技能（七要素摘录规则、法庭试金石判断法、大表精要处理、梗概规范、原文锚点格式、即时交叉验证）
- 新增 `templates/evidence-brief.md` — 证据精要模板（元信息/梗概/摘录表/关联性/发现疑问/交叉验证）
- 新增 `.claude/commands/read-group.md` — `/read-group [组号]` 命令（前置检查→初始化→读取→精要→保存→输出）
- 新增 `.claude/commands/read-next.md` — `/read-next [E编号]` 命令（支持跨组、即时交叉验证、中断恢复）
- 更新 `.claude/scripts/state-manager.py` — 新增 `update_group_status()` 函数，修复 BOM 编码问题（`utf-8` → `utf-8-sig`）
- 生成 `workspace/briefs/` 下 19 份证据精要（E001-E019），覆盖全部 5 组
- 更新 `workspace/meta/` 下所有状态文件：`first_pass_completed = true`, `evidence_read = 19`, `evidence_approved = 19`

**关键发现（跨组交叉验证）：**
- 资金混同证据链完整：E016/E017/E018/E019 四份银行流水构建了"两校收入→成丰实业集团"的资金转移模式
- 成臣/成倩个人从学校对公账户取现/消费（E017），构成人格混同证据
- 中信银行5,000万融资已到账但未用于支付工程款（E008/E010），构成恶意拖欠
- 新发现主体网络：武汉长征集团、荆州市武强塑料制品、厚泽后勤、成丰磁材科技、武汉市新展教育后勤
- 成廷虎发送"九真仙境度假区项目宣传册"（E008），疑似资金挪用去向
- 成臣提及"蔡甸校区出售在积极推进中"（E009），存在财产转移风险

**决策与反馈：**
- 用户要求"假装在做案子，把所有内容都做全"，因此直接跑完全部 5 组 19 份证据，而非仅做 T4 Walkthrough
- M5（审批流程 `/approve`、`/revise`）尚未开发，审批环节通过手动修改 JSON 状态文件模拟通过
- 用户指出不应在更新状态文件时使用 Python（因 Windows 环境下 `python` 命令 exit 49），应直接用 Edit 工具修改 JSON 文件

### v0.1.6 — M5审批流程 + 精要大合集 + Walkthrough验收通过 (2026-05-13)

**变更内容：**
- 新增 `.claude/commands/approve.md` — `/approve` 命令（批量审批、入库精要大合集、压缩比自检、支持排除和指定证据）
- 新增 `.claude/commands/revise.md` — `/revise` 命令（律师修改意见→重读原文→重新生成精要→批注标记→待复审）
- 新增 `templates/evidence-collection.md` — 精要大合集模板（5组分区 + 压缩比自检报告）
- 生成 `workspace/evidence-collection.md` — 19份精要压缩合集（17.3KB，压缩比 1/9.5，接近理想值 1/10）
- 更新 `workspace/meta/file-manifest.json` — 19份证据 reading_status → approved
- 更新 `workspace/meta/case-state.json` — evidence_approved = 19
- 更新 `workspace/meta/review-log.json` — 追加审批和修改记录
- 测试 `/revise E004` — 补充面积差异分析，含批注标记（依律师意见补充）

**M5 Walkthrough 验收：**

| 验收项 | 结果 |
|--------|------|
| /approve 命令文件 | ✅ |
| /revise 命令文件 | ✅ |
| 精要大合集模板 | ✅ |
| 精要大合集已生成 | ✅ |
| 压缩比达标（≤1/4） | ✅ 1/9.5 |
| 压缩比自检报告 | ✅ 数值完整 |
| 批量审批状态更新 | ✅ 19份 → approved |
| /revise 测试 | ✅ E004 含批注标记 |
| review-log 完整 | ✅ 含审批+修改记录 |

**决策与反馈：**
- 用户评价"质量非常高，已经接近想要的东西了"
- M5 完成后，Phase 2（分组阅读+审批）的全部核心能力已就绪，可进入 Phase 3（全局交叉验证 /cross-verify）

### v0.1.7 — M6即时交叉验证 + 三维比对矩阵 + 中断恢复机制 (2026-05-13)

**变更内容：**
- 增强 `.claude/skills/read-evidence/SKILL.md` 第8节 — 从简单3项检查扩展为完整的三维比对矩阵：
  - 时间线维度（阈值>1天）、金额维度（阈值差异>5%）、主体维度（任何不一致即标记）
  - 矛盾严重性三级分类：🔴严重（必须中断）、🟡注意（标注不中断）、⚪信息（静默）
  - 结构化比对流程：提取事实卡→读取已入库精要→逐一比对→分级输出
  - 比对范围从同组扩展到跨组所有已入库精要
  - 精要交叉验证区标准输出格式（印证/矛盾/新发现分区）
- 增强 `.claude/commands/read-next.md` — 步骤四交叉验证逻辑升级 + 恢复机制：
  - 前置检查新增恢复机制：检测 paused_at → 展示暂停原因 → 律师确认"继续" → 清除暂停继续阅读
  - 步骤四按三维比对矩阵执行系统化检查，按严重性分级决策
  - 步骤七暂停输出模板增加严重性标记和 /revise 引导

**T6 Walkthrough 验收：**

| 验收项 | 结果 |
|--------|------|
| 三维比对矩阵（时间线/金额/主体） | ✅ E001 vs E007 完整比对 |
| 矛盾阈值生效 | ✅ 合同总价0.0018%通过，付款期限差43天标记🟡 |
| 🔴严重矛盾触发中断 | ✅ 模拟55%金额差异，正确触发中断 |
| reading-plan 记录 paused_at + pause_reason | ✅ 正确写入和读取 |
| 恢复机制 | ✅ 模拟"继续"→清除暂停标记 |
| 🟡注意级矛盾不中断 | ✅ 标注后继续阅读 |
| 比对范围扩展到跨组 | ✅ 已入库精要不限同组 |

**决策与反馈：**
- 利用现有案件已知矛盾（E001 vs E007 付款期限差异、E001 vs E004 面积差异）作为测试数据，无需创建合成测试文件
- 比对范围从同组扩展到跨组：避免遗漏组间矛盾（如合同组 vs 验收组的面积/日期差异）
- 恢复机制设计为"律师确认后清除暂停"，而非自动恢复，保持律师控制权

### v0.1.8 — M7全局交叉验证 + 四维验证报告 + 时间线生成 (2026-05-13)

**变更内容：**
- 新增 `.claude/skills/cross-verify/SKILL.md` — 四维验证技能（时间线矛盾检测、金额一致性校验、主体一致性校验、法律要件缺口检测），含验证报告输出格式模板和矛盾严重性分级
- 新增 `.claude/commands/cross-verify.md` — `/cross-verify` 命令（7步流程：初始化→时间线→金额→主体→法律要件→报告→输出）
- T7 Walkthrough：对真实案件19份证据执行完整四维验证
- 生成 `workspace/timeline.md` — 24个事件的案件时间线（合同签约→施工→完工→催款全链路）
- 生成 `workspace/cross-verify-report.md` — 完整验证报告（6章节：时间线/金额/主体/法律要件/风险提示/行动建议）
- 更新 `workspace/meta/case-state.json` — phase→phase_3_cross_verify, cross_verify_completed=true
- 更新 `workspace/meta/case-context.json` — legal_elements_checklist 11项全部从null→{status, supporting_evidence, gap_note}
- 更新 `workspace/meta/review-log.json` — 追加cross_verify_completed记录

**T7 验收结果：**

| 验收项 | 结果 |
|--------|------|
| 四维验证全部执行 | ✅ 时间线3矛盾/金额6异常/主体4矛盾/要件5✅+5⚠️+1❌ |
| timeline.md 生成 | ✅ 24事件按时间排序 |
| cross-verify-report.md | ✅ 6章节完整报告 |
| case-state 更新 | ✅ phase_3_cross_verify |
| legal_elements_checklist | ✅ 11项全部填充 |
| review-log | ✅ 追加记录 |

**四维验证关键发现：**
- 🔴 严重风险：中信银行5,000万融资挪用（E008/E010）、人格混同证据链（E016/E017/E018/E019）、付款协议多主体未盖章（E007）、无工程结算文件
- ✅ 充分支撑：主体适格、合同效力、工期、工程价款、加速到期
- ❌ 唯一缺口：工程结算（无正式结算文件）
- 📌 5条优先补充证据 + 4条诉讼策略建议

**决策与反馈：**
- v1保守策略：不自动修改已审批精要，仅在验证报告中标注矛盾和缺口，律师根据报告手动 /revise
- timeline.md 作为 /cross-verify 的副产品生成，不单独创建 /timeline 命令（属于 M10）
- 法律要件分析直接更新 case-context.json，使后续 /generate-report 可直接读取覆盖状态

### v0.1.9 — M8报告生成 + 案件初探精要v1.0定稿 (2026-05-13)

**变更内容：**
- 新建 `.claude/skills/generate-deliverable/SKILL.md`：案件复杂度判断规则（简单/中等/复杂）、字数分配、Executive Summary 撰写规范、各章节撰写标准、自检规则
- 新建 `templates/case-probe-report.md`：案件初探精要完整模板，含元数据头、Executive Summary、五章正文、关键细节速查表
- 新建 `.claude/commands/generate-report.md`：6步流程（复杂度判断→读取输入→生成报告→自检→版本管理→输出）+ 定稿流程
- T8 Walkthrough 执行完成：生成案件初探精要 v1.0，复杂度"复杂"，正文2563字，15条速查表
- 律师确认定稿，归档至 workspace/versions/case-probe-report_v1.0_final.md

**T8 验收结果：**
| 检查项 | 结果 |
|--------|------|
| 报告生成 | ✅ workspace/case-probe-report.md |
| 复杂度判断 | ✅ 复杂（19证据/>10主体/多争点） |
| Executive Summary | ✅ ~190字，纯事实 |
| 正文字数 | ✅ 2563字（目标2000-3000） |
| 速查表锚点 | ✅ 15条，每条含原文锚点 |
| 无法律判断 | ✅ 自检通过 |
| 定稿归档 | ✅ v1.0 final |

**决策与反馈：**
- 律师直接确认定稿，无修改意见
- 版本管理策略：v1.0起步，每次修改递增0.1，定稿时归档带_final后缀

