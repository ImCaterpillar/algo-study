# AlgoStudy 项目检查与优化报告

检查日期：2026-05-17

## 1. 已执行的检查

- 解压并审查项目结构。
- 编译检查后端 Python 代码：`python -m compileall -q backend/app`。
- 安装后端运行依赖并导入 FastAPI 应用。
- 使用 FastAPI TestClient 验证核心接口。
- 重新安装前端依赖，执行 `npm audit --omit=dev`。
- 执行前端生产构建：`npm run build`。

## 2. 发现并修复的问题

### 2.1 后端依赖缺失

问题：后端鉴权代码使用了 `python-jose`、`passlib`、`bcrypt`、`python-multipart`，但 `requirements.txt` 未声明这些依赖，导致应用无法导入或登录接口不可用。

修复：补齐依赖，并将 `bcrypt` 固定为 `4.0.1`，避免 `passlib==1.7.4` 与新版 bcrypt 的兼容问题。

### 2.2 旧 SQLite 数据库结构不兼容多用户模型

问题：随包数据库是早期单用户结构，`progress`、`problem_notes`、`submissions`、`review_logs`、`ai_hints` 缺少 `user_id` 字段，登录后访问题库会报 `no such column: progress.user_id`。此外，旧库中 `progress.problem_id` 和 `problem_notes.problem_id` 存在单用户唯一约束，会阻止新用户保存进度或笔记。

修复：新增 `backend/app/migrations.py`，启动时自动补齐 `user_id`，回填旧数据，并在需要时重建旧表以移除单用户唯一约束。

### 2.3 SQLAlchemy 关系不完整

问题：`Problem` 与 `Progress` 等模型缺少双向关系，题目序列化依赖 `problem.progress` 时存在潜在异常。

修复：补齐 `Problem`、`Progress`、`ProblemNote`、`Submission`、`ReviewLog`、`AiHint` 之间的关系映射。

### 2.4 新建 Progress 默认值为 None

问题：SQLAlchemy 的 `Column(default=...)` 在 flush 前不会自动写入 Python 对象字段，新建进度后执行 `progress.attempts += 1` 会出现 `NoneType` 运算错误。

修复：新增 `new_progress()` 工具函数，在创建进度记录时显式初始化状态、次数、掌握度、信心值和布尔字段。

### 2.5 JavaScript 提交记录校验不一致

问题：前端支持 `javascript`，后端执行服务也支持 `javascript`，但 `SubmissionCreate.language` 只允许 `python|java|cpp`，导致 JS 代码运行成功后无法保存提交记录。

修复：提交语言校验已扩展为 `python|javascript|java|cpp`。

### 2.6 模板标签写入格式不规范

问题：模板创建和更新使用 `str(list)` 存储标签，生成的是 Python 字符串表示，不是合法 JSON。

修复：改用 `json.dumps(..., ensure_ascii=False)` 写入；读取函数兼容旧的 Python list repr，避免历史数据损坏。

### 2.7 模板不存在时返回 None

问题：`GET/PUT /templates/{id}` 返回 `None` 会触发 response_model 校验异常。

修复：改为标准 `404 Template not found`。

### 2.8 沙箱接口未鉴权

问题：`/api/sandbox/execute` 可以匿名调用，风险较高。

修复：接口现在要求 Bearer Token，并限制代码长度、stdin 长度和 timeout 范围。

### 2.9 普通执行接口缺少输入限制和输出截断

问题：`/api/execute` 缺少请求大小限制，执行输出也未截断。

修复：为请求模型添加代码长度、stdin 长度、timeout 限制，并将 stdout/stderr 截断为最多 1MB。

### 2.10 CORS 与 JWT 配置硬编码

问题：CORS 允许所有来源，JWT Secret 写死在代码中。

修复：新增 `.env.example`，后端通过环境变量配置 `SECRET_KEY`、`ACCESS_TOKEN_EXPIRE_MINUTES`、`CORS_ORIGINS` 等参数。

### 2.11 前端登录跳转路径错误

问题：登录成功后跳转到 `/dashboard`，但路由中没有该路径，导致页面空白。

修复：登录成功后跳转到 `/` 并刷新页面，使用户状态从 localStorage 正确加载。

### 2.12 前端构建包过大警告

问题：初次构建产物主 chunk 超过 500KB。

修复：在 Vite 中配置 `manualChunks`，将 React、图表、Monaco Editor、Axios 拆分到独立 chunk。构建后不再出现大 chunk 警告。

### 2.13 npm audit 漏洞告警

问题：`monaco-editor` 间接依赖的 `dompurify` 版本触发 moderate 漏洞告警。

修复：在 `package.json` 中添加 `overrides.dompurify`，重新安装后 `npm audit --omit=dev` 显示 `found 0 vulnerabilities`。

## 3. 当前验证结果

后端核心接口验证结果：

- 注册：通过
- 登录：通过
- 当前用户：通过
- 题库列表：通过
- 题目详情：通过
- 统计摘要：通过
- 待复盘列表：通过
- 模板列表：通过
- 模板详情：通过
- JavaScript 代码执行：通过
- Python 沙箱执行：通过
- 匿名访问沙箱接口：正确返回 401

前端验证结果：

- `npm audit --omit=dev`：0 vulnerabilities
- `npm run build`：通过
- 构建产物已拆分为 `react`、`charts`、`editor`、`http` 等 chunk

## 4. 后续建议

- 引入 Alembic 管理正式数据库迁移。
- 为核心服务增加 pytest 单元测试和 API 集成测试。
- 代码执行功能使用容器或微虚拟机进行强隔离。
- 为登录接口增加密码复杂度校验、账号锁定、刷新令牌和限流。
- 为题库和模板接口增加分页，避免数据规模扩大后响应过大。
- 增加 CI 流程：后端编译/测试、前端 audit/build、制品打包。

---

# 二次检查与优化补充报告

检查日期：2026-05-17

## 1. 二次检查发现的问题

### 1.1 复盘统计不完整

问题：前端“快速复盘”调用 `/api/reviews/quick-review` 后只更新 `progress`，没有写入 `review_logs`。这会导致复盘历史、复习效果统计、周报复习次数长期为空或偏低。

修复：`quick-review` 现在复用 `create_review_log()`，会同步记录复盘日志、更新掌握度、写入下次复盘时间，并返回标准 `ReviewLogOut`。

### 1.2 模板练习页题目详情缺失

问题：模板练习页用题目列表接口的数据直接展示详情，但列表接口不返回 `description/examples`，因此练习页会出现题面和示例为空。

修复：选中练习题后自动调用题目详情接口，展示完整题目描述、示例和跳转入口。

### 1.3 JavaScript 编辑器语言映射错误

问题：前端 Monaco Editor 未配置 `javascript` 映射，切换到 JavaScript 时仍按 Python 高亮。

修复：补齐 `javascript -> javascript` 映射。

### 1.4 API 客户端存在循环依赖

问题：`client.js` 引入 `authApi`，而 `authApi.js` 又引入 `api`，属于隐式循环依赖。当前构建能过，但后续扩展时容易出现初始化顺序问题。

修复：`client.js` 改为直接读取 / 清理 localStorage 中的 token 和 user，解除循环依赖。

### 1.5 题库列表存在潜在 N+1 查询

问题：题库列表通过 join 查询进度，但序列化时仍访问 `problem.progress` 关系，可能触发每道题额外查询，并且会加载该题所有用户的进度。

修复：列表接口改为查询 `(Problem, Progress)` 元组，直接传入当前用户进度进行序列化，避免额外关系加载。

### 1.6 进度接口可创建孤儿记录

问题：`PATCH /problems/{problem_id}/progress` 未先确认题目是否存在，可能对不存在的题目创建进度记录。

修复：更新进度前先验证题目存在，不存在时返回 `404 Problem not found`。

### 1.7 数据库唯一性约束不足

问题：多用户模型中，`progress` 与 `problem_notes` 缺少 `(user_id, problem_id)` 唯一约束，异常重复请求可能生成同一用户同一题的多条进度 / 笔记记录。

修复：模型中新增 `UniqueConstraint`，迁移脚本会为旧库创建 `ux_progress_user_problem` 与 `ux_problem_notes_user_problem` 唯一索引，并在创建索引前去重。

### 1.8 SQLite 迁移路径不尊重 DATABASE_URL

问题：旧迁移逻辑固定检查 `backend/algo_study.db`，如果通过 `DATABASE_URL` 指定了其他 SQLite 文件，迁移不会生效。

修复：迁移逻辑现在会解析 `DATABASE_URL`，对实际 SQLite 文件执行兼容迁移；非 SQLite 或内存库会自动跳过。

### 1.9 请求模型校验偏松

问题：用户注册、提交、模板、笔记、执行接口的长度和枚举校验不完整，容易写入空模板语言、超长文本或非预期状态。

修复：补齐 Pydantic 字段约束：用户名、邮箱、密码长度，提交语言 / 状态枚举，代码 / 笔记 / 模板文本长度，执行语言白名单等。

### 1.10 FastAPI startup 事件写法即将过时

问题：使用 `@app.on_event("startup")`，新版本 FastAPI 推荐改为 lifespan。

修复：改为 `asynccontextmanager` lifespan 初始化数据库、迁移和 seed。

### 1.11 模板接口鉴权不一致

问题：模板写接口需要登录，但列表、分类、语言、详情和推荐接口不需要登录，和前端受保护路由的设计不一致。

修复：模板相关接口统一要求 Bearer Token，减少匿名访问面。

## 2. 新增验证

- 后端冒烟测试：通过。
- 前端 `npm audit --omit=dev`：0 vulnerabilities。
- 前端 `npm run build`：通过。
- 新增回归检查：模板匿名访问返回 401、非法模板语言返回 422、非法题目进度更新返回 404、快速复盘写入历史和复习效果统计。
- 新增旧 SQLite 迁移检查：旧单用户表可补齐 `user_id`，可移除旧 `problem_id` 唯一约束，并创建新的 `(user_id, problem_id)` 唯一索引。

## 3. 二次优化后仍建议后续投入的方向

- 引入 Alembic 替代轻量手写迁移，适合多人协作和生产部署。
- 代码执行器仍是本地进程运行，不是生产级隔离；公网部署前应切换为容器 / 微虚拟机沙箱，并加限流与审计。
- 题库和模板仍未分页；数据量扩大后建议增加分页、搜索索引和服务端排序。
- AI 辅助当前是规则引擎式提示，不调用外部大模型；如需更强能力，应增加可配置 LLM Provider 与调用日志。


---

# 三次检查与优化补充报告

检查日期：2026-05-17

## 1. 三次检查发现的问题

### 1.1 系统模板可被任意登录用户修改

问题：模板库虽然要求登录，但模板数据本身是全局共享的。任意登录用户都可以编辑或删除内置模板，容易破坏其他用户的学习环境。

修复：为 `templates` 增加 `owner_user_id` 与 `is_system` 字段。系统 seed 模板标记为 `is_system=True` 且只读；用户新建模板或复制系统模板时创建个人模板，只对本人可见、可编辑、可删除。

### 1.2 模板旧库缺少所有权字段

问题：已有 SQLite 数据库中的 `templates` 表没有 `owner_user_id` 和 `is_system` 字段，升级后直接访问会报错。

修复：启动迁移会自动为旧 `templates` 表补齐字段，并将历史模板标记为系统模板，避免旧数据被普通用户误删。

### 1.3 SQLite 外键未显式开启

问题：SQLite 默认不强制执行外键约束，开发环境可能无法及时发现孤儿数据问题。

修复：在 SQLAlchemy engine connect 事件中执行 `PRAGMA foreign_keys=ON`，让本地 SQLite 行为更接近生产数据库。

### 1.4 快速复盘参数仍使用 query string 且结果未枚举校验

问题：`quick-review` 用 query 参数提交，且 `result` 可传任意字符串，长期会污染复盘统计。

修复：改为 JSON 请求体，并通过 `QuickReviewCreate` 限制为 `掌握 / 部分遗忘 / 完全遗忘`。前端调用同步更新。

### 1.5 统计与推荐直接解析 JSON，容错不足

问题：统计和推荐服务直接 `json.loads(problem.tags)`，一旦旧数据或手工修改导致标签不是合法 JSON，会使统计页整体失败。

修复：统一使用 `safe_json_loads()`，继续兼容旧的 Python list repr，并在异常时回退为空列表。

### 1.6 标签筛选为字符串 contains，可能误匹配

问题：题库和模板按标签筛选时使用数据库 `contains`，对 JSON 文本做模糊匹配可能误命中相似标签。

修复：改为读取标签 JSON 后做精确匹配，并为列表接口补充 `limit/offset` 防止未来数据量扩大后响应过大。

### 1.7 注册邮箱大小写未规范化

问题：`User@Example.com` 与 `user@example.com` 在部分数据库配置下可能被视为不同邮箱。

修复：注册和查询时统一 trim 并小写邮箱，注册重复检查使用 `lower(email)`。登录和当前用户校验会拒绝已停用账号。

## 2. 新增验证

- 系统模板更新返回 403。
- 复制系统模板后生成个人模板，并可编辑。
- 其他用户无法读取该个人模板。
- 非法快速复盘结果返回 422。
- 旧 `templates` 表可迁移出 `owner_user_id` 与 `is_system`。
- 后端冒烟测试、回归测试、前端 audit 与生产构建均通过。

## 3. 当前仍建议后续投入的方向

- 引入 Alembic 替代轻量手写迁移，适合多人协作和生产部署。
- 代码执行器仍是本地进程运行，不是生产级隔离；公网部署前应切换为容器 / 微虚拟机沙箱，并加限流与审计。
- 模板和题库已有基础分页参数，但前端仍是一次性加载；数据量继续增长后建议增加服务端搜索、总数返回和前端分页控件。
- AI 辅助当前是规则引擎式提示，不调用外部大模型；如需更强能力，应增加可配置 LLM Provider、调用日志和费用限制。
- 建议增加 CI：后端 compile/smoke/regression，前端 audit/build，自动生成 zip 制品。

---

# 四次检查与优化跟进报告

检查日期：2026-05-18

## 1. 四次检查发现的问题

### 1.1 Dashboard 薄弱标签详情为空

问题：首页的“薄弱标签详情”组件读取 `weakness_analysis.by_tag`，但后端 dashboard 接口只返回了 weakest / strongest 标签列表，没有返回 `by_tag` 明细，导致该区块长期为空。

修复：`/api/stats/dashboard` 现在返回完整 `by_tag` 明细，前端首页可以正确展示标签掌握度与待复习题数。

### 1.2 系统种子数据无法增量更新

问题：旧逻辑只要 `problems` 或 `templates` 表已有任意数据，就跳过整个 seed。后续更新 `data/problems.json` / `data/templates.json` 时，已有数据库不会得到新增题目、修正文案或新增系统模板。

修复：题库和系统模板改为幂等 upsert。启动时会按种子文件更新系统数据，但不会覆盖用户进度、提交、笔记或个人模板。

### 1.3 演示账号与生产配置边界不清晰

问题：默认 admin 账号固定创建，长期部署或误暴露服务时风险较高。

修复：新增 `APP_ENV`、`CREATE_DEMO_USER`、`DEMO_USERNAME`、`DEMO_EMAIL`、`DEMO_PASSWORD` 配置。生产环境默认不创建演示账号；当 `APP_ENV=production` 但仍使用默认 `SECRET_KEY` 时会直接拒绝启动。

### 1.4 代码执行缺少总开关

问题：虽然执行接口已有登录、长度和 timeout 限制，但没有服务端一键关闭开关，不方便部署时禁用高风险能力。

修复：新增 `CODE_EXECUTION_ENABLED` 与 `MAX_CODE_EXECUTION_TIMEOUT`。禁用后 `/api/execute` 和 `/api/sandbox/execute` 会返回 403；timeout 上限由服务端配置统一约束。

### 1.5 AI 辅助接口请求体缺少长度限制

问题：AI 分析、提示、代码审查、解释接口未限制描述、代码、标签数量等字段，异常请求可能导致内存或响应时间不可控。

修复：为 AI 请求模型增加 `min_length` / `max_length` / list 长度限制，并复用统一语言枚举。

### 1.6 提交记录和复盘历史未分页

问题：单题提交记录和复盘历史会一次性返回全部数据，长期使用后页面和接口响应会变慢。

修复：`GET /submissions/problem/{problem_id}`、`GET /reviews/history`、`GET /reviews/due` 增加 `limit/offset`，并设置最大返回上限。

### 1.7 迁移无显式记录

问题：轻量迁移只做幂等修改，没有记录当前已应用版本，不利于排查用户环境中的升级状态。

修复：新增 `schema_migrations` 表，记录本轮硬化迁移标记 `2026-05-18-v4-hardening`；`python -m app.migrations` 可手动触发迁移。

### 1.8 前端题库和模板库没有分页入口、错误提示不足

问题：后端已有 `limit/offset`，但前端仍默认一次加载；接口失败时多数页面只写 console，用户界面没有明显反馈。

修复：题库和模板库新增“加载更多”，并增加可见错误提示和重试按钮；题库新增状态筛选，模板库分类 / 语言选项改为从后端独立接口加载。

### 1.9 未匹配路由显示空页面

问题：访问不存在的前端路径时保护路由内没有 404 页面，容易误以为应用白屏。

修复：新增 `NotFound` 页面，未知路径会显示明确提示并可返回首页。

## 2. 四次优化新增验证

- 后端冒烟测试继续覆盖注册、登录、题库、题目详情、统计、复盘、模板、JS 执行、Python 沙箱执行。
- 回归测试新增覆盖：dashboard 返回 `by_tag`、AI 超大请求返回 422、提交记录分页返回正确数量、迁移版本表记录存在。
- 前端生产构建通过；`npm audit --omit=dev` 仍为 0 vulnerabilities。

## 3. 当前仍建议后续投入的方向

- 正式引入 Alembic，在多人协作和生产部署时替代轻量手写迁移。
- 将代码执行从本地进程升级为容器 / 微虚拟机隔离，并增加限流、审计、配额和队列。
- AI 辅助当前仍是规则式服务，可后续接入可配置 LLM Provider、缓存与调用日志。

### 1.10 状态筛选对新用户的“未开始”题目不准确

问题：题库状态筛选直接按 `Progress.status` 过滤。新用户尚未产生 `progress` 行时，逻辑上应属于 `Not Started`，但旧过滤会把这些题目排除。

修复：`status=Not Started` 现在同时包含没有进度记录的题目；回归测试已覆盖新用户未开始筛选。

---

# 五次优化跟进（v5）

验证日期：2026-05-18

## 1. 统一分页响应落地

问题：v4 已在部分接口加上 `limit/offset`，但返回仍是裸数组，前端只能用 `items.length === PAGE_SIZE` 猜测是否还有下一页，无法准确展示总数，也不利于后续分页控件、无限滚动和 API 文档维护。

修复：以下接口统一返回 `items/total/limit/offset/has_more`：

- `GET /api/problems`
- `GET /api/templates`
- `GET /api/submissions/problem/{problem_id}`
- `GET /api/reviews/due`
- `GET /api/reviews/history`

前端题库和模板库已改为使用 `has_more` 控制“加载更多”，并显示当前筛选总数和已加载数量。提交历史、模板练习、复盘中心也同步适配新的分页响应。

## 2. 健康检查接口

问题：项目没有轻量健康检查入口，部署或 CI 中只能访问业务接口间接判断服务状态。

修复：新增：

```http
GET /health
```

返回服务状态、数据库连通性和 API 版本号。冒烟测试已覆盖该接口。

## 3. 用户名大小写一致性

问题：邮箱已做小写规范化和大小写无关重复检查，但用户名此前按原始大小写查询，可能出现 `alice` 与 `Alice` 这样的重复认知冲突。

修复：注册时用户名统一保存为小写；登录和重复检查按大小写无关方式处理。回归测试已覆盖：同一用户名不同大小写不能重复注册，但可以用不同大小写登录。

## 4. CI 和一键验证脚本

问题：本地已有多条验证命令，但没有一键入口和 CI 配置，后续改动容易漏跑某一类检查。

修复：新增：

- `scripts/verify.sh`：从项目根目录一键执行后端编译、冒烟、回归、前端 audit/build。
- `.github/workflows/ci.yml`：GitHub Actions 自动执行后端和前端验证。

## 5. API 契约文档

问题：前端依赖的接口结构分散在代码里，后续继续迭代时容易破坏返回格式。

修复：新增 `docs/API_CONTRACT.md`，记录鉴权、健康检查、分页响应、题库 / 模板 / 提交 / 复盘接口约定和常见错误码。

## 6. 五次验证新增覆盖

- 冒烟测试新增 `/health` 检查。
- 回归测试新增统一分页结构、`has_more`、`total`、用户名大小写无关登录与防重复。
- 前端构建验证新版分页响应适配。
- 生产依赖 audit 仍为 0 vulnerabilities。

## 7. 当前仍建议后续投入的方向

- 正式引入 Alembic，在多人协作和生产部署时替代轻量手写迁移。
- 将代码执行从本地进程升级为容器 / 微虚拟机隔离，并增加限流、审计、配额和队列。
- 将题库标签 / 模板标签筛选进一步下推到数据库或增加规范化标签表，避免数据量变大后在 Python 中过滤。
- 为前端增加真正的分页控件、URL 查询参数同步和端到端测试。
- AI 辅助当前仍是规则式服务，可后续接入可配置 LLM Provider、缓存与调用日志。


## 第六轮：一键部署能力

本轮新增 Docker Compose 生产式部署和本地一键运行能力：

- 新增 `docker-compose.yml`，通过 Nginx 统一承载前端静态资源并反向代理 `/api`、`/health`、`/docs`。
- 新增 `backend/Dockerfile` 和 `frontend/Dockerfile`，支持独立构建后端 API 与前端 Nginx 镜像。
- 新增 `.env.deploy.example`，部署脚本会自动生成 `.env` 并替换默认 `SECRET_KEY`。
- 新增 `scripts/deploy.sh`，支持启动、停止、状态、日志、指定端口、强制构建和可选启用代码执行运行时。
- 新增 `scripts/deploy-local.sh`，用于无 Docker 的开发/演示环境，一键安装依赖并同时启动前后端。
- Docker 部署默认关闭代码执行，避免公网部署时暴露高风险执行接口；可信环境可通过 `--enable-code-exec` 显式开启。

---

# 第七轮：依赖源与 Windows 体验修复

本轮针对用户在 Windows PowerShell 执行 `npm install` 时出现的 `ETIMEDOUT` 做专项修复，并补齐跨平台启动体验。

## 1. 清理 npm 内部源残留

问题：`frontend/package-lock.json` 中部分依赖的 `resolved` 字段残留了构建环境内部 npm registry，用户本机无法访问，导致 `npm install` 超时。

修复：

- 将 `package-lock.json` 中内部 registry 地址替换为 `https://registry.npmjs.org/`。
- 新增 `frontend/.npmrc`，默认使用公开 npm 源。
- `scripts/verify.sh` 和 GitHub Actions 新增内部 registry 残留检查，防止再次打包出类似问题。
- Docker 前端构建显式使用 `NPM_REGISTRY`，默认公开源，国内网络可改为 npmmirror。

## 2. 新增 npm 源修复脚本

新增：

- `scripts/fix-npm-registry.ps1`
- `scripts/fix-npm-registry.sh`

用于一键修复 npm registry、项目级 `.npmrc` 和 `package-lock.json`。Windows 用户可执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\fix-npm-registry.ps1
```

网络较慢时可指定镜像源：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\fix-npm-registry.ps1 -Registry https://registry.npmmirror.com/
```

## 3. 新增 Windows PowerShell 本地一键运行

问题：v6 只有 Bash 版本 `deploy-local.sh`，Windows 用户需要手动执行多个命令。

修复：新增：

```text
scripts/deploy-local.ps1
```

它会自动完成：

- 创建 / 更新后端 `.env`。
- 创建 / 更新前端 `.env`。
- 创建 Python 虚拟环境。
- 安装后端依赖。
- 使用指定 npm registry 安装前端依赖。
- 启动后端并等待 `/health`。
- 启动前端 Vite 开发服务器。

## 4. 部署脚本 registry 参数

`deploy.sh` 新增：

```bash
./scripts/deploy.sh --npm-registry https://registry.npmmirror.com/ --build
```

适用于 Docker 构建阶段 npm 官方源较慢或不可达的环境。


---

# 第八轮：Windows PowerShell 脚本修复与运行入口加固

本轮针对用户实际运行 v7 时出现的两个问题做专项修复：

1. 打开 / 嵌套启动 PowerShell 时，Anaconda 的 `Conda.psm1` 通过 `Invoke-Expression` 解析 PATH 报错。
2. `fix-npm-registry.ps1` 和 `deploy-local.ps1` 在 Windows PowerShell 中存在解析兼容性问题。

## 1. PowerShell 脚本语法兼容修复

修复内容：

- 重写 `scripts/fix-npm-registry.ps1`，避免使用 Windows PowerShell 5.1 不兼容或容易误解析的双引号转义写法。
- 重写 `scripts/deploy-local.ps1`，减少复杂正则替换和内嵌表达式，增强 Windows PowerShell 5.1 兼容性。
- `SECRET_KEY` 生成改为 `RandomNumberGenerator.Create().GetBytes()`，兼容旧版 Windows PowerShell/.NET Framework。
- npm registry 自动补全尾部 `/`，减少 `package-lock.json` 替换后的地址拼接问题。

## 2. 新增 `.cmd` 包装入口

新增：

```text
scripts/fix-npm-registry.cmd
scripts/deploy-local.cmd
```

`.cmd` 包装脚本内部使用：

```text
powershell.exe -NoProfile -ExecutionPolicy Bypass
```

这样即使用户机器上的 Anaconda / Conda PowerShell profile 有问题，也不会影响项目脚本执行。

Windows 用户现在推荐使用：

```powershell
.\scripts\fix-npm-registry.cmd https://registry.npmmirror.com/
.\scripts\deploy-local.cmd https://registry.npmmirror.com/
```

## 3. 文档更新

已更新：

- `README.md`
- `docs/DEPLOYMENT.md`

文档现在明确说明：

- Windows 推荐使用 `.cmd` 入口。
- 直接运行 `.ps1` 时建议加 `-NoProfile`。
- Anaconda profile 报错属于本机 PowerShell 初始化问题，不是项目代码问题。

## v10 Windows one-click script hotfix

Fixed a Windows PowerShell parser failure caused by non-ASCII text in `.ps1` scripts being decoded incorrectly on some Windows PowerShell 5.1 installations. The Windows startup scripts now use ASCII-only output and `.cmd` wrappers continue to launch PowerShell with `-NoProfile`.
