# AlgoStudy 项目完整规划与完善路线图

> 文档版本：v1.0  
> 基于项目版本：v10 Windows 一键启动修复版  
> 更新时间：2026-05-18  
> 文档目标：在继续编码前，先明确产品定位、功能边界、技术路线、版本优先级、验收标准和长期完善方向，避免后续开发变成零散补丁。

---

## 1. 项目定位

AlgoStudy 的目标不是简单复制 LeetCode，而是打造一个面向个人和小团队的算法学习工作台：

- 刷题：题库、题目详情、代码编辑、运行、提交、记录。
- 判题：自动测试、隐藏用例、运行结果、错误定位、性能反馈。
- 复盘：间隔复习、错因记录、掌握度变化、弱项分析。
- 沉淀：题解、模板、笔记、相似题、知识点地图。
- 辅助：AI 提示、代码审查、错误解释、学习路线建议。
- 数据：学习报告、导入导出、跨设备同步、长期成长曲线。
- 部署：本地一键启动、Docker 部署、生产环境安全配置。

一句话定位：

> AlgoStudy 是一个“个人算法学习操作系统”，核心差异化是把刷题、复盘、模板沉淀、弱项追踪和 AI 反馈整合到一个本地可控的工作台里。

---

## 2. 当前项目状态基线

### 2.1 已具备能力

当前版本已经具备 MVP+ 能力：

| 模块 | 当前状态 | 说明 |
|---|---|---|
| 用户系统 | 已完成 | 注册、登录、JWT、用户数据隔离 |
| 题库 | 已完成 | 列表、详情、筛选、分页、seed upsert |
| 代码编辑 | 已完成 | Monaco Editor，多语言代码编辑 |
| 代码运行 | 已完成 | Python、JavaScript、Java、C++ 本地执行 |
| 提交记录 | 已完成 | 保存提交、状态、语言、错误原因 |
| 笔记 | 已完成 | 题目笔记、复杂度、易错点、总结 |
| 复盘 | 已完成 | D+1 / D+3 / D+7 / D+14 / D+30 复盘 |
| 统计 | 已完成 | 弱项分析、周报、推荐题、掌握度统计 |
| 模板库 | 已完成 | 系统模板只读、个人模板 CRUD、模板练习 |
| AI 辅助 | 初步完成 | 规则型提示、难度预测、代码审查、知识点解释 |
| 部署 | 已完成基础版 | Windows 一键启动、macOS/Linux start.sh、Docker Compose |
| 文档 | 已完成基础版 | README、运行手册、部署说明、API 契约、数据库文档 |
| CI / 验证 | 已完成基础版 | verify.sh、GitHub Actions、后端回归、前端构建 |

### 2.2 当前关键不足

当前版本仍然偏向个人工具，距离完整产品还有以下差距：

1. **自动判题体系不足**  
   目前有代码运行和提交记录，但还没有真正的测试用例集合、隐藏用例、逐用例结果、AC / WA / TLE / RE / CE 判定。

2. **代码执行安全不足**  
   现在适合本地学习，不适合公网开放任意代码执行。需要 Docker 隔离、资源限制、网络禁用、临时文件系统和审计日志。

3. **题库内容体系不足**  
   当前题量适合 MVP，不足以支撑长期系统训练。每题也缺少结构化题解、复杂度、相似题、考点、标准测试用例。

4. **学习路径不够完整**  
   有推荐和复盘，但还没有明确的学习计划、每日任务、日历、阶段目标、连续打卡和成就体系。

5. **AI 能力仍偏静态**  
   当前 AI 更像规则助手，还没有真正接入可配置 LLM Provider，也没有结合用户代码、错误用例和历史表现生成个性化反馈。

6. **前端产品体验有提升空间**  
   页面能用，但工作台、判题结果、测试用例面板、快捷键、暗色模式、响应式布局、空状态和错误状态还需要产品化打磨。

7. **工程化仍需加强**  
   目前用轻量手写迁移和 SQLite，适合本地。若面向多人或长期部署，需要 Alembic、PostgreSQL、日志、监控、备份、限流和权限治理。

---

## 3. 产品完善目标

### 3.1 短期目标：从 MVP+ 到可持续个人学习工具

时间范围：1～3 个版本。

目标：

- 自动判题可用。
- 每道题有结构化测试用例。
- 提交后可以看到清晰结果。
- 学习计划和复盘闭环更完整。
- 文档和一键启动稳定。

衡量标准：

- 新用户下载后 10 分钟内可以启动并开始刷题。
- 用户能完成“选题 → 写代码 → 运行样例 → 提交判题 → 查看失败用例 → 记录笔记 → 加入复盘”的完整流程。
- 主要流程有回归测试覆盖。

### 3.2 中期目标：成为个人算法学习工作台

时间范围：3～6 个版本。

目标：

- 题库扩展到 300～500 题。
- 每题有题解、复杂度、易错点、相似题。
- AI 能根据错误用例和历史记录给出个性化建议。
- 支持学习计划、打卡、日历、成就和阶段报告。
- 支持数据导出 / 导入和备份。

衡量标准：

- 用户可以按“数组、链表、二分、DP、图论”等路线持续学习。
- 用户可以查看过去 7 天、30 天、90 天的学习趋势。
- 用户可以从弱项自动生成练习计划。

### 3.3 长期目标：成为可部署的小团队算法训练平台

时间范围：6 个版本以上。

目标：

- 后端支持 PostgreSQL。
- 使用 Alembic 正式管理迁移。
- 代码执行使用容器 / 沙箱隔离。
- 支持团队、班级、任务、排行榜和题单分享。
- 支持更完善的权限、审计、监控和备份。

衡量标准：

- 可以安全部署到内网服务器供多人使用。
- 管理员可以维护题库、题单和测试用例。
- 用户之间数据隔离清晰，关键操作可追踪。

---

## 4. 功能蓝图

### 4.1 判题系统

这是下一阶段最重要的模块。

#### 4.1.1 要实现的能力

- 每道题维护多组测试用例。
- 测试用例分为：
  - 示例用例：前端可见。
  - 基础用例：提交时执行，可见失败详情。
  - 隐藏用例：提交时执行，但失败时只展示摘要。
- 支持 Run：只运行用户当前自定义输入或示例用例。
- 支持 Submit：运行该题全部测试用例并生成最终状态。
- 支持状态：
  - `Accepted`
  - `Wrong Answer`
  - `Time Limit Exceeded`
  - `Memory Limit Exceeded`
  - `Runtime Error`
  - `Compile Error`
  - `System Error`
- 记录每个测试点的：
  - 输入
  - 期望输出
  - 实际输出
  - 是否通过
  - 耗时
  - stderr
  - 错误类型
- 支持输出标准化：去除尾部空白、换行兼容、JSON 数组比较。
- 支持每题独立时间限制和内存限制。

#### 4.1.2 数据库新增表建议

##### `test_cases`

| 字段 | 类型 | 说明 |
|---|---|---|
| id | integer | 主键 |
| problem_id | integer | 所属题目 |
| name | string | 测试点名称 |
| input_data | text | 标准输入或结构化输入 |
| expected_output | text | 期望输出 |
| case_type | string | sample / public / hidden |
| weight | integer | 权重 |
| time_limit_ms | integer | 单用例时间限制 |
| memory_limit_mb | integer | 单用例内存限制 |
| is_active | boolean | 是否启用 |
| order_index | integer | 排序 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

##### `judge_runs`

| 字段 | 类型 | 说明 |
|---|---|---|
| id | integer | 主键 |
| user_id | integer | 用户 |
| problem_id | integer | 题目 |
| submission_id | integer | 关联提交，可为空 |
| language | string | 语言 |
| code | text | 提交代码快照 |
| mode | string | run / submit |
| status | string | 总体状态 |
| passed_count | integer | 通过数 |
| total_count | integer | 总用例数 |
| runtime_ms | integer | 总耗时 |
| memory_mb | float | 峰值内存 |
| error_message | text | 汇总错误 |
| created_at | datetime | 创建时间 |

##### `judge_case_results`

| 字段 | 类型 | 说明 |
|---|---|---|
| id | integer | 主键 |
| judge_run_id | integer | 所属判题运行 |
| test_case_id | integer | 关联测试用例 |
| status | string | 当前用例状态 |
| input_preview | text | 输入预览 |
| expected_preview | text | 期望输出预览 |
| actual_preview | text | 实际输出预览 |
| stderr_preview | text | 错误输出预览 |
| runtime_ms | integer | 当前用例耗时 |
| memory_mb | float | 当前用例内存 |
| is_hidden | boolean | 是否隐藏 |
| order_index | integer | 排序 |

#### 4.1.3 后端接口建议

| 接口 | 方法 | 说明 |
|---|---|---|
| `/api/problems/{id}/test-cases` | GET | 获取样例 / 可见测试用例 |
| `/api/problems/{id}/test-cases` | POST | 管理员新增测试用例，后续再做 |
| `/api/judge/run` | POST | 运行样例或自定义输入 |
| `/api/judge/submit` | POST | 提交并跑全部测试用例 |
| `/api/judge/runs/{id}` | GET | 查看判题详情 |
| `/api/submissions/{id}/judge-result` | GET | 查看提交对应判题结果 |

#### 4.1.4 前端页面建议

题目详情页重构为三栏：

```text
左侧：题目描述 / 示例 / 约束 / 题解 / 笔记
中间：代码编辑器
右侧：测试用例 / 运行结果 / 提交记录 / AI 建议
```

第一版不一定要做复杂布局，但至少要实现：

- 测试用例 Tab。
- 运行结果 Tab。
- 提交结果详情。
- 失败用例清晰展示。
- 一键复制失败输入。
- 隐藏用例失败时只显示摘要。

#### 4.1.5 验收标准

- 至少 10 道题具备 3～5 组测试用例。
- Python 和 JavaScript 提交可以自动判定 Accepted / Wrong Answer / Runtime Error / Time Limit Exceeded。
- 提交记录能关联判题结果。
- 前端能展示逐用例结果。
- 后端回归测试覆盖 Accepted、Wrong Answer、Runtime Error、超时场景。

---

### 4.2 题库与内容系统

#### 4.2.1 要实现的能力

- 题库从当前规模扩展到 300～500 题。
- 每题补齐：
  - 中文标题
  - 英文标题
  - 难度
  - 标签
  - 阶段
  - 来源
  - 题目描述
  - 示例
  - 约束
  - Starter Code
  - 测试用例
  - 官方题解
  - 复杂度
  - 易错点
  - 相似题
  - 推荐模板
- 支持题单：
  - 入门题单
  - 数据结构题单
  - 高频面试题单
  - 动态规划题单
  - 图论题单
  - 二分 / 双指针 / 滑动窗口题单

#### 4.2.2 数据库新增表建议

##### `problem_solutions`

| 字段 | 类型 | 说明 |
|---|---|---|
| id | integer | 主键 |
| problem_id | integer | 题目 |
| title | string | 题解标题 |
| language | string | 语言 |
| approach | text | 思路 |
| code | text | 标准代码 |
| time_complexity | string | 时间复杂度 |
| space_complexity | string | 空间复杂度 |
| pitfalls | text | 易错点 |
| is_official | boolean | 是否官方题解 |
| created_at | datetime | 创建时间 |

##### `problem_relations`

| 字段 | 类型 | 说明 |
|---|---|---|
| id | integer | 主键 |
| source_problem_id | integer | 当前题目 |
| target_problem_id | integer | 相关题目 |
| relation_type | string | similar / prerequisite / followup |
| note | text | 关系说明 |

##### `study_lists`

| 字段 | 类型 | 说明 |
|---|---|---|
| id | integer | 主键 |
| name | string | 题单名称 |
| description | text | 题单说明 |
| difficulty_range | string | 难度范围 |
| is_system | boolean | 系统题单 |
| owner_user_id | integer | 用户私有题单 |

##### `study_list_items`

| 字段 | 类型 | 说明 |
|---|---|---|
| id | integer | 主键 |
| study_list_id | integer | 题单 |
| problem_id | integer | 题目 |
| order_index | integer | 排序 |
| note | text | 题单内说明 |

#### 4.2.3 验收标准

- 至少新增 100 道题并保证 JSON seed 可重复执行。
- 至少 50 道题有官方题解。
- 至少 30 道题有测试用例。
- 至少 5 个系统题单可用。
- 用户可以按题单学习并看到题单进度。

---

### 4.3 学习计划与复盘闭环

#### 4.3.1 要实现的能力

- 用户可以创建学习计划：
  - 每日题量
  - 目标日期
  - 目标标签
  - 难度比例
  - 是否包含复盘任务
- 系统自动生成每日任务：
  - 新题
  - 复盘题
  - 弱项强化题
  - 模板练习
- 学习日历：
  - 每日完成情况
  - 连续学习天数
  - 提交次数
  - 通过题数
  - 复盘次数
- 阶段报告：
  - 本周 / 本月完成情况
  - 弱项变化
  - 掌握度变化
  - 推荐下一阶段学习内容

#### 4.3.2 数据库新增表建议

##### `study_plans`

| 字段 | 类型 | 说明 |
|---|---|---|
| id | integer | 主键 |
| user_id | integer | 用户 |
| name | string | 计划名称 |
| description | text | 计划说明 |
| start_date | date | 开始日期 |
| end_date | date | 结束日期 |
| daily_new_problem_count | integer | 每日新题数 |
| daily_review_count | integer | 每日复盘数 |
| target_tags | text | 目标标签 JSON |
| target_difficulties | text | 目标难度 JSON |
| status | string | active / paused / completed |
| created_at | datetime | 创建时间 |

##### `study_tasks`

| 字段 | 类型 | 说明 |
|---|---|---|
| id | integer | 主键 |
| user_id | integer | 用户 |
| plan_id | integer | 计划 |
| problem_id | integer | 题目，可为空 |
| task_type | string | new_problem / review / template / note |
| scheduled_date | date | 计划日期 |
| status | string | pending / done / skipped |
| completed_at | datetime | 完成时间 |
| note | text | 备注 |

##### `learning_streaks`

| 字段 | 类型 | 说明 |
|---|---|---|
| id | integer | 主键 |
| user_id | integer | 用户 |
| date | date | 日期 |
| solved_count | integer | 通过题数 |
| submission_count | integer | 提交数 |
| review_count | integer | 复盘数 |
| task_done_count | integer | 完成任务数 |
| active_minutes | integer | 活跃分钟数，可后续实现 |

#### 4.3.3 前端页面建议

- 学习计划页：创建计划、查看计划进度。
- 今日任务页：展示当天新题、复盘、模板练习。
- 学习日历：热力图 + 每日详情。
- 阶段报告页：周报 / 月报 / 阶段报告。

#### 4.3.4 验收标准

- 用户可以创建一个 30 天学习计划。
- 系统每天生成任务。
- 用户完成题目后任务状态自动更新。
- Dashboard 展示今日任务和连续学习天数。
- 复盘任务与已有 ReviewLog 打通。

---

### 4.4 AI 学习助手升级

#### 4.4.1 要实现的能力

当前 AI 是规则型提示，下一步要改造成可配置 Provider：

- `.env` 支持配置：
  - `AI_PROVIDER`
  - `AI_API_KEY`
  - `AI_BASE_URL`
  - `AI_MODEL`
  - `AI_ENABLED`
- 支持 OpenAI 兼容接口。
- 支持本地关闭 AI，不影响其他功能。
- 统一 AI 调用服务层。
- 给用户提供以下 AI 功能：
  - 基于题目给出分层提示。
  - 基于失败用例解释错误。
  - 基于用户代码做代码审查。
  - 基于历史薄弱标签推荐题目。
  - 自动生成题解草稿。
  - 自动提炼错题笔记。

#### 4.4.2 数据库增强建议

扩展 `ai_hints` 或新增 `ai_requests`：

| 字段 | 类型 | 说明 |
|---|---|---|
| id | integer | 主键 |
| user_id | integer | 用户 |
| problem_id | integer | 题目，可为空 |
| submission_id | integer | 提交，可为空 |
| request_type | string | hint / review / explain_error / plan |
| provider | string | Provider 名称 |
| model | string | 模型名称 |
| prompt | text | 请求内容 |
| response | text | 响应内容 |
| tokens_input | integer | 输入 token，可选 |
| tokens_output | integer | 输出 token，可选 |
| latency_ms | integer | 延迟 |
| status | string | success / failed |
| error_message | text | 错误信息 |
| created_at | datetime | 创建时间 |

#### 4.4.3 安全与成本控制

- 限制 prompt 长度。
- 限制每个用户每日调用次数。
- 对失败请求做降级返回。
- 不把用户敏感配置返回给前端。
- 默认关闭云端 AI，需要用户手动配置。

#### 4.4.4 验收标准

- 没有 API Key 时系统正常运行。
- 配置 API Key 后 AI 接口可以调用。
- AI 错误不会导致页面崩溃。
- AI 请求被记录，方便排错。
- 至少一个接口能结合失败用例给出具体修改建议。

---

### 4.5 执行器与安全沙箱

#### 4.5.1 当前风险

当前执行器适合本地可信环境，不适合公网开放。风险包括：

- 恶意代码消耗 CPU。
- 恶意代码写文件。
- 恶意代码访问网络。
- 恶意代码读取环境变量。
- 编译器 / 解释器漏洞。

#### 4.5.2 完善方向

##### 阶段 A：本地加强

- 每次执行创建独立临时目录。
- 清理危险环境变量。
- 禁止读取项目根目录。
- 加强 timeout。
- 限制 stdout / stderr。
- 记录执行日志。

##### 阶段 B：Docker 隔离

- 为每种语言准备执行镜像。
- 禁用网络：`--network none`。
- 限制 CPU：`--cpus`。
- 限制内存：`--memory`。
- 限制进程数：`--pids-limit`。
- 使用只读文件系统。
- 使用临时挂载目录。
- 每次执行结束删除容器。

##### 阶段 C：更强隔离

后续可评估：

- gVisor
- Firecracker
- nsjail
- isolate
- Kubernetes Job / Worker Queue

#### 4.5.3 验收标准

- Docker 部署默认关闭代码执行。
- 开启后每次执行在容器中运行。
- 恶意死循环能被终止。
- 超大输出会被截断。
- 代码无法访问外网。
- 代码无法读取宿主项目文件。

---

### 4.6 前端体验升级

#### 4.6.1 工作台重构

题目页应该成为核心工作台：

- 顶部：题目标题、难度、标签、状态、收藏。
- 左侧：题目描述、示例、约束、题解、笔记。
- 中间：代码编辑器、语言选择、快捷键。
- 右侧：测试用例、运行结果、提交记录、AI 助手。
- 底部：运行、提交、保存草稿、加入复盘。

#### 4.6.2 体验细节

- 暗色模式。
- 代码字体大小设置。
- 快捷键：
  - Ctrl / Cmd + Enter：运行。
  - Ctrl / Cmd + Shift + Enter：提交。
  - Ctrl / Cmd + S：保存草稿。
- 自动保存代码草稿。
- 失败用例一键复制。
- 页面加载骨架屏。
- 空状态文案。
- 错误提示统一 toast。
- 移动端基础适配。

#### 4.6.3 验收标准

- 用户能在题目页完成完整刷题流程，不需要频繁跳转。
- 运行和提交状态有明确 loading。
- 网络错误和后端错误有可读提示。
- 代码草稿刷新后不丢失。
- 首页、题库、题目页、模板页支持暗色模式。

---

### 4.7 数据导入导出与同步

#### 4.7.1 本地导入导出

要支持用户迁移和备份：

- 导出所有个人数据为 JSON / ZIP。
- 导入个人数据并合并。
- 导出范围：
  - 进度
  - 提交
  - 笔记
  - 复盘日志
  - 个人模板
  - 学习计划
- 导入冲突策略：
  - 保留较新记录。
  - 同题笔记可选择覆盖或合并。

#### 4.7.2 云端同步预留

后续支持：

- PostgreSQL 数据库。
- 用户账号云端登录。
- 多设备同步。
- 定期备份。
- 数据恢复。

#### 4.7.3 验收标准

- 用户可以导出完整备份。
- 删除数据库后可以导入恢复。
- 导入不会破坏系统题库和系统模板。

---

### 4.8 后台管理与内容维护

#### 4.8.1 管理端能力

后续需要区分普通用户和管理员：

- 管理题目。
- 管理测试用例。
- 管理官方题解。
- 管理系统模板。
- 管理系统题单。
- 查看系统健康状态。
- 查看执行器错误日志。

#### 4.8.2 权限模型

新增字段建议：

- `users.role`：`user / admin`。
- 管理接口必须校验 admin。
- 系统内容只能管理员修改。
- 普通用户只能管理自己的模板、笔记、计划。

#### 4.8.3 验收标准

- 普通用户无法新增 / 修改系统题库。
- 管理员可以导入题库 JSON。
- 管理员可以新增测试用例并立即用于判题。

---

### 4.9 工程化与可维护性

#### 4.9.1 数据库迁移

当前是轻量手写迁移。建议正式引入 Alembic：

- 初始化 Alembic。
- 把当前模型生成 baseline migration。
- 后续所有表结构变化通过 migration 管理。
- 启动时不再隐式大改表结构，只做必要检查。

验收标准：

- 新库可从 migration 创建。
- 旧库可升级。
- CI 中跑迁移测试。

#### 4.9.2 测试体系

后端测试：

- API 鉴权测试。
- 判题测试。
- 复盘测试。
- 模板权限测试。
- 迁移测试。
- 导入导出测试。

前端测试：

- 构建测试。
- 核心页面渲染测试。
- API 错误状态测试。
- 判题结果组件测试。

建议工具：

- 后端：pytest。
- 前端：Vitest + React Testing Library。
- E2E：Playwright。

#### 4.9.3 日志与监控

- 后端结构化日志。
- 请求 ID。
- 错误日志。
- 判题执行日志。
- AI 调用日志。
- 健康检查增强。

#### 4.9.4 验收标准

- `scripts/verify.sh` 一键跑完所有关键检查。
- CI 覆盖后端测试、前端构建、内部源残留检查。
- 核心接口测试覆盖率逐步提高。

---

## 5. 版本路线图

### v11：项目规划与自动判题 MVP

#### 目标

把项目从“代码运行工具”升级为“可自动判题的刷题工具”。

#### 范围

后端：

- 新增 `test_cases` 表。
- 新增 `judge_runs` 表。
- 新增 `judge_case_results` 表。
- 新增 `/api/judge/run`。
- 新增 `/api/judge/submit`。
- 新增判题服务层。
- 给 10 道题补充测试用例。
- 提交记录关联判题结果。

前端：

- 题目页新增测试用例面板。
- 题目页新增运行结果面板。
- Submit 后展示总体结果。
- 展示逐用例结果。

测试：

- Accepted 测试。
- Wrong Answer 测试。
- Runtime Error 测试。
- Time Limit Exceeded 测试。

不做：

- 暂不做管理员测试用例管理页面。
- 暂不做内存精确限制。
- 暂不做全题库测试用例。

#### 验收标准

- 至少 Python 和 JavaScript 可自动判题。
- 至少 10 道题可提交判题。
- 前端能清楚展示通过数和失败详情。
- `scripts/verify.sh` 通过。

---

### v12：题解系统与内容增强

#### 目标

让用户不仅能刷题，还能系统复盘和学习解法。

#### 范围

- 新增 `problem_solutions` 表。
- 题目详情页新增“题解”Tab。
- 至少 30 道题补齐官方题解。
- 每题题解包含：思路、代码、复杂度、易错点。
- 相似题推荐初版。
- data seed 支持题解导入。

#### 验收标准

- 题解可以被 seed 导入。
- 题目页可查看题解。
- 用户可以从失败提交跳转到题解和相关模板。

---

### v13：学习计划与日历

#### 目标

形成“每日任务 + 复盘 + 弱项强化”的学习闭环。

#### 范围

- 新增学习计划表。
- 新增每日任务表。
- Dashboard 展示今日任务。
- 学习日历热力图。
- 连续学习天数。
- 计划完成率。

#### 验收标准

- 用户可以创建 7 天 / 30 天计划。
- 今日任务可完成、跳过。
- 题目完成后自动更新任务状态。
- 复盘任务与 ReviewLog 打通。

---

### v14：AI Provider 与智能反馈

#### 目标

把规则型 AI 升级为真正可配置的智能学习助手。

#### 范围

- 新增 AI Provider 配置。
- 支持 OpenAI 兼容接口。
- AI 错误解释：结合失败用例 + 用户代码。
- AI 代码审查：给出复杂度、边界条件、优化建议。
- AI 错题笔记：自动生成总结草稿。
- AI 请求日志。

#### 验收标准

- 未配置 API Key 时功能降级且不报错。
- 配置 API Key 后至少 3 个 AI 功能可用。
- AI 调用失败时页面显示友好错误。

---

### v15：安全执行器与 Docker 判题

#### 目标

让代码执行更安全，支持内网多人使用。

#### 范围

- Docker 隔离执行。
- 禁止网络。
- 限制 CPU / 内存 / 进程数。
- 只读文件系统。
- 执行日志。
- Docker 部署可配置执行器开关。

#### 验收标准

- 恶意死循环能被终止。
- 无法访问外网。
- 无法读取项目文件。
- 执行错误有日志可查。

---

### v16：题库规模化与题单系统

#### 目标

让项目具备长期学习价值。

#### 范围

- 扩充到 300+ 题。
- 新增系统题单。
- 新增用户自定义题单。
- 标签规范化。
- 题单进度统计。

#### 验收标准

- 至少 5 个系统题单。
- 题单详情页可查看进度。
- 用户可以收藏 / 创建题单。

---

### v17：数据导入导出与备份

#### 目标

解决长期使用的数据安全问题。

#### 范围

- 导出个人数据。
- 导入个人数据。
- 备份说明。
- 冲突处理。

#### 验收标准

- 可以导出 ZIP。
- 新数据库可以导入恢复。
- 导入后统计和复盘正常。

---

### v18：多人模式与管理后台

#### 目标

从个人工具升级为小团队训练平台。

#### 范围

- 用户角色。
- 管理员页面。
- 题目管理。
- 测试用例管理。
- 题解管理。
- 团队 / 班级。
- 任务发布。
- 排行榜。

#### 验收标准

- 管理员和普通用户权限隔离。
- 管理员可以维护题库和测试用例。
- 普通用户只能查看和学习。

---

## 6. 推荐开发顺序

接下来不要一次性做全部功能，推荐按以下顺序推进：

1. **先做 v11 自动判题 MVP**  
   这是项目从“记录型工具”升级为“刷题产品”的关键。

2. **再做 v12 题解系统**  
   判题能发现问题，题解帮助用户解决问题。

3. **再做 v13 学习计划**  
   把刷题、复盘、弱项强化串成闭环。

4. **再做 v14 AI Provider**  
   AI 要建立在题目、提交、失败用例、题解这些数据基础之上，否则反馈不够精准。

5. **再做 v15 安全沙箱**  
   如果要多人使用或部署到服务器，这一步必须提前。

6. **最后扩内容、做同步和管理端**  
   内容规模和多人功能需要更稳的底层支撑。

---

## 7. v11 详细实施计划

v11 是下一步最推荐实现的版本。

### 7.1 后端任务拆分

#### 任务 1：新增模型

新增模型：

- `TestCase`
- `JudgeRun`
- `JudgeCaseResult`

注意事项：

- `TestCase.problem_id` 必须关联 `Problem.id`。
- `case_type` 只能是 `sample / public / hidden`。
- `JudgeRun.mode` 只能是 `run / submit`。
- `JudgeRun.status` 必须使用统一枚举。
- 隐藏测试用例不能把完整输入输出返回给普通用户。

#### 任务 2：新增 schema

新增 Pydantic schema：

- `TestCaseOut`
- `JudgeRunRequest`
- `JudgeSubmitRequest`
- `JudgeCaseResultOut`
- `JudgeRunOut`

字段校验：

- 语言只允许项目支持的语言。
- 代码长度限制。
- 自定义输入长度限制。
- problem_id 必须存在。

#### 任务 3：新增判题服务

新增 `backend/app/services/judge_service.py`。

核心函数：

- `run_single_case(language, code, input_data, time_limit_ms)`
- `compare_output(expected, actual, mode="text")`
- `judge_problem(user, problem, language, code, mode)`
- `save_judge_result(...)`

第一版比较规则：

- 默认文本比较。
- 去除两端空白。
- 统一换行。
- 后续再扩展 JSON / 浮点误差比较。

#### 任务 4：新增接口

新增 `backend/app/routes/judge.py`。

接口：

- `POST /api/judge/run`
- `POST /api/judge/submit`
- `GET /api/judge/runs/{id}`

#### 任务 5：数据 seed

新增文件：

- `data/test_cases.json`

格式建议：

```json
[
  {
    "problem_id": 1,
    "cases": [
      {
        "name": "sample 1",
        "case_type": "sample",
        "input_data": "...",
        "expected_output": "...",
        "time_limit_ms": 2000,
        "memory_limit_mb": 128,
        "order_index": 1
      }
    ]
  }
]
```

seed 要求：

- 幂等 upsert。
- 不重复创建同一 problem + name + case_type。
- 支持更新 expected_output。

#### 任务 6：提交记录联动

提交判题时：

- 创建 `Submission`。
- 创建 `JudgeRun`。
- 创建 `JudgeCaseResult`。
- 根据最终状态更新 `Progress`。
- Accepted 时更新 solved_count、first_solved_at、mastery_level。
- Wrong Answer / Runtime Error 时增加 attempts 和 last_attempt_at。

### 7.2 前端任务拆分

#### 任务 1：API 客户端

新增：

- `judgeApi.run(payload)`
- `judgeApi.submit(payload)`
- `judgeApi.getRun(id)`

#### 任务 2：题目页增加测试用例面板

能力：

- 展示示例用例。
- 支持用户自定义输入。
- 支持运行当前代码。

#### 任务 3：题目页增加判题结果面板

能力：

- 总体状态 Badge。
- 通过数 / 总数。
- 每个测试点状态。
- 失败输入、期望输出、实际输出。
- 隐藏用例只展示摘要。

#### 任务 4：提交按钮联动

- Run：不保存正式提交或保存为 `mode=run`。
- Submit：保存正式提交并更新进度。
- 按钮 loading 状态。
- 错误 toast。

### 7.3 测试任务

后端新增：

- `backend/judge_test.py` 或并入 `regression_test.py`。

覆盖：

- 正确代码 Accepted。
- 错误代码 Wrong Answer。
- 死循环 Time Limit Exceeded。
- 抛异常 Runtime Error。
- 未登录返回 401。
- 访问别人的 JudgeRun 返回 404 / 403。
- 隐藏用例不泄露完整输入输出。

前端验证：

- `npm run build` 通过。
- 题目页没有运行时错误。

---

## 8. 数据质量规划

### 8.1 标签体系规范

建议统一标签命名：

- Array
- String
- Hash Table
- Two Pointers
- Sliding Window
- Binary Search
- Stack
- Queue
- Linked List
- Tree
- Binary Tree
- Graph
- BFS
- DFS
- Dynamic Programming
- Greedy
- Backtracking
- Heap
- Trie
- Union Find
- Prefix Sum
- Difference Array
- Monotonic Stack
- Monotonic Queue
- Bit Manipulation
- Math

### 8.2 难度体系

保留：

- Easy
- Medium
- Hard

后续可新增内部字段：

- `difficulty_score`：1～10。
- `interview_frequency`：1～5。
- `importance_score`：1～5。

### 8.3 题目阶段

建议阶段：

1. 入门基础
2. 数组与字符串
3. 链表与栈队列
4. 哈希与前缀和
5. 双指针与滑动窗口
6. 二分查找
7. 树与递归
8. 回溯
9. 动态规划基础
10. 动态规划进阶
11. 图论
12. 贪心
13. 高频面试综合

---

## 9. 非功能性要求

### 9.1 性能要求

- 题库列表 500 题以内响应 < 300ms。
- Dashboard 响应 < 500ms。
- 提交判题结果在合理时间内返回。
- 前端首屏加载保持可接受，必要时继续拆包。

### 9.2 安全要求

- 生产环境必须配置强 `SECRET_KEY`。
- 生产环境默认关闭 demo 用户。
- 生产环境默认关闭或隔离代码执行。
- 所有用户数据接口必须鉴权。
- 用户只能访问自己的提交、笔记、复盘、计划、模板。
- 管理接口必须校验 admin。

### 9.3 可维护性要求

- 新增功能必须更新文档。
- 新增接口必须更新 `docs/API_CONTRACT.md`。
- 新增表必须更新 `docs/DATABASE_SCHEMA.md`。
- 新增启动方式必须更新 README。
- 每个版本必须更新 `docs/OPTIMIZATION_REPORT.md` 和 `docs/VERIFICATION_LOG.md`。

### 9.4 可测试性要求

- 核心接口必须有回归测试。
- 迁移必须有旧库兼容测试。
- 判题必须覆盖成功、失败、异常、超时。
- 前端至少保证生产构建通过。

---

## 10. Definition of Done

每个版本完成前必须满足：

1. 功能实现符合本规划的版本范围。
2. 后端编译通过。
3. 后端冒烟测试通过。
4. 后端回归测试通过。
5. 前端依赖安装正常。
6. 前端生产构建通过。
7. 没有内部 npm 源残留。
8. Windows 一键启动脚本不破坏。
9. README 与相关 docs 更新。
10. 生成新的 zip 包。
11. 明确记录本版本解决的问题和遗留问题。

---

## 11. 风险与应对

| 风险 | 影响 | 应对 |
|---|---|---|
| 判题标准输入格式不统一 | 用户代码难以适配 | 第一版先使用 stdin 文本协议，后续再做函数签名执行 |
| 代码执行安全风险 | 不能公网部署 | 默认关闭公网执行，Docker 隔离后再开放 |
| 题库扩展耗时 | 产品内容不足 | 先覆盖高频 100 题，再逐步扩展 |
| AI 成本不可控 | API 消耗过高 | 默认关闭，增加调用限制和日志 |
| SQLite 多人场景瓶颈 | 并发不足 | 个人版继续 SQLite，多人版迁移 PostgreSQL |
| 迁移脚本复杂 | 旧数据损坏风险 | 引入 Alembic，迁移前备份 |
| Windows 环境差异 | 启动失败 | 保留 `.cmd`，使用 `PowerShell -NoProfile`，脚本保持 ASCII-only |

---

## 12. 当前不优先做的事情

为了避免范围失控，以下内容暂不优先：

- 公开社区讨论区。
- 在线竞赛系统。
- 复杂排行榜。
- 付费系统。
- 第三方账号登录。
- 手机 App。
- 大规模分布式判题集群。
- 完整后台 CMS。

这些功能可以等自动判题、题解、学习计划和安全执行器稳定后再考虑。

---

## 13. 下一步执行建议

建议下一步从 v11 开始，顺序如下：

1. 新增判题相关数据库模型。
2. 新增测试用例 seed 文件。
3. 先给 10 道题补测试用例。
4. 实现后端判题服务。
5. 实现 `/api/judge/run` 和 `/api/judge/submit`。
6. 提交记录关联判题结果。
7. 题目页增加测试用例和判题结果面板。
8. 写回归测试。
9. 更新文档。
10. 打包 v11。

v11 完成后，项目的产品价值会明显提升，因为用户不再只是“手动记录刷题状态”，而是可以得到系统自动判定和可复盘的失败详情。

---

## 14. 文档维护规则

本文件是项目路线图主文档，后续每次大版本都应该更新：

- 当前版本状态。
- 已完成内容。
- 下个版本范围。
- 调整后的优先级。
- 新增风险和决策。

建议把本文件作为后续开发前的检查清单，避免每次只做局部修补，而是持续朝完整产品推进。
