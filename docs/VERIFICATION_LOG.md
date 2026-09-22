# 验证日志

验证日期：2026-05-17

## 后端

执行命令：

```bash
rm -f backend/algo_study.db
python -m compileall -q backend/app
cd backend
python smoke_test.py
```

结果：

```text
OK me
OK problems
OK problem-detail
OK summary
OK reviews
OK templates
OK template-detail
OK execute-js
OK sandbox-python
Smoke test passed.
```

说明：使用全新 SQLite 数据库验证，启动时能够自动建表、导入题库与模板，并完成核心接口冒烟测试。

## 前端

执行命令：

```bash
cd frontend
npm audit --omit=dev
npm run build
```

结果：

```text
found 0 vulnerabilities
✓ built
```

构建产物拆分结果：

```text
index.css
editor-*.js
http-*.js
index-*.js
react-*.js
charts-*.js
```

说明：前端生产构建通过，且已通过 manualChunks 拆分主 bundle。

---

# 二次验证日志

验证日期：2026-05-17

## 后端

执行命令：

```bash
cd backend
source .venv/bin/activate
python -m compileall -q app
python smoke_test.py
```

结果：

```text
OK me
OK problems
OK problem-detail
OK summary
OK reviews
OK templates
OK template-detail
OK execute-js
OK sandbox-python
Smoke test passed.
```

## 后端回归检查

覆盖项：

- 匿名访问模板列表返回 401。
- 登录后模板列表正常返回。
- 不存在的题目进度更新返回 404，避免孤儿进度。
- 空模板语言返回 422。
- 快速复盘会写入复盘历史。
- 复习效果统计会包含快速复盘记录。

结果：

```text
regression checks passed
```

## 旧库迁移检查

覆盖项：

- 旧 `progress` / `problem_notes` 单用户表补齐 `user_id`。
- 旧 `submissions` 表补齐 `user_id`。
- 创建 `ux_progress_user_problem` 与 `ux_problem_notes_user_problem` 唯一索引。
- NULL 默认字段回填为安全默认值。

结果：

```text
legacy migration check passed
```

## 前端

执行命令：

```bash
cd frontend
npm audit --omit=dev
npm run build
```

结果：

```text
found 0 vulnerabilities
✓ built
```


---

# 三次验证日志

验证日期：2026-05-17

## 后端

执行命令：

```bash
cd backend
source .venv/bin/activate
python -m compileall -q app
python smoke_test.py
python regression_test.py
```

结果：

```text
OK me
OK problems
OK problem-detail
OK summary
OK reviews
OK templates
OK template-detail
OK execute-js
OK sandbox-python
Smoke test passed.
OK api-regressions
OK legacy-migration
Regression checks passed.
```

新增覆盖项：

- 系统模板只读，更新返回 403。
- 复制系统模板生成个人模板，个人模板可编辑。
- 个人模板跨用户不可见。
- 非法快速复盘结果返回 422。
- 旧模板表自动补齐 `owner_user_id` 和 `is_system`。

## 前端

执行命令：

```bash
cd frontend
npm audit --omit=dev
npm run build
```

结果：

```text
found 0 vulnerabilities
✓ built
```

---

# 四次验证日志

验证日期：2026-05-18

## 后端

执行命令：

```bash
cd backend
source .venv/bin/activate
python -m compileall -q app
python smoke_test.py
python regression_test.py
```

结果：

```text
OK me
OK problems
OK problem-detail
OK summary
OK reviews
OK templates
OK template-detail
OK execute-js
OK sandbox-python
Smoke test passed.
OK api-regressions
OK legacy-migration
Regression checks passed.
```

新增覆盖项：

- `/api/stats/dashboard` 返回 `weakness_analysis.by_tag`。
- AI 超长 description 请求返回 422。
- 单题提交记录 `limit/offset` 生效。
- 旧库迁移后会写入 `schema_migrations` 标记。

## 前端

执行命令：

```bash
cd frontend
npm audit --omit=dev
npm run build
```

结果：

```text
found 0 vulnerabilities
✓ built in 4.50s
```

构建产物继续拆分为：

```text
editor-*.js
http-*.js
index-*.js
react-*.js
charts-*.js
```

补充覆盖项：

- 新用户按 `status=Not Started` 筛选时，能返回尚未创建 progress 的题目。

---

# 五次验证日志

验证日期：2026-05-18

## 后端

执行命令：

```bash
cd backend
source .venv/bin/activate
python -m compileall -q app
python smoke_test.py
python regression_test.py
```

结果：

```text
OK health
OK me
OK problems
OK problem-detail
OK summary
OK reviews
OK templates
OK template-detail
OK execute-js
OK sandbox-python
Smoke test passed.
OK api-regressions
OK legacy-migration
Regression checks passed.
```

新增覆盖项：

- `/health` 返回服务、数据库和版本状态。
- `GET /api/problems` 返回统一分页结构并包含 `total/has_more`。
- `GET /api/templates` 返回统一分页结构并保持系统模板只读。
- `GET /api/reviews/history` 返回统一分页结构。
- `GET /api/submissions/problem/{problem_id}` 返回统一分页结构，`limit=1` 时 `has_more=true`。
- 用户名大小写无关登录和重复注册拦截。

## 前端

执行命令：

```bash
cd frontend
npm audit --omit=dev
npm run build
```

结果：

```text
found 0 vulnerabilities
✓ built in 4.48s
```

补充覆盖项：

- 题库页适配 `items/total/has_more`，可展示总数和已加载数量。
- 模板库适配统一分页结构。
- 模板练习页、复盘中心、提交历史适配分页响应。

## 一键验证与 CI

新增：

```bash
./scripts/verify.sh
```

新增 GitHub Actions：

```text
.github/workflows/ci.yml
```


## 第六轮验证

新增部署能力后的检查：

```text
bash -n scripts/deploy.sh
bash -n scripts/deploy-local.sh
./scripts/deploy.sh --help
./scripts/deploy-local.sh --help
./scripts/verify.sh
```

验证目标：

- 部署脚本语法正确。
- 帮助输出可正常展示。
- 新增 Docker / Nginx / Compose 文件不影响现有后端测试和前端构建。
- 现有后端冒烟、回归、前端 audit 和生产构建继续通过。

---

## 第七轮验证

新增依赖源与 Windows 体验修复后的检查：

```text
grep -R "applied-caas\|internal.api.openai\|artifactory" frontend/package-lock.json frontend/.npmrc .npmrc
bash -n scripts/deploy.sh
bash -n scripts/deploy-local.sh
bash -n scripts/fix-npm-registry.sh
./scripts/deploy.sh --help
./scripts/deploy-local.sh --help
./scripts/verify.sh
```

验证目标：

- 项目中不再包含内部 npm registry 地址。
- 一键部署 / 本地启动 / npm 源修复脚本语法正确。
- Docker 构建可通过 `NPM_REGISTRY` 指定公开源或镜像源。
- Windows PowerShell 用户可使用 `deploy-local.ps1` 和 `fix-npm-registry.ps1`。
- 后端冒烟、回归、前端 audit 和生产构建继续通过。


---

## 第八轮验证

本轮新增 Windows 脚本修复后的检查：

```text
bash -n scripts/deploy.sh scripts/deploy-local.sh scripts/fix-npm-registry.sh scripts/verify.sh
grep -R "applied-caas\|internal.api.openai\|artifactory" frontend/package-lock.json frontend/.npmrc .npmrc
python -m compileall -q app
python smoke_test.py
python regression_test.py
```

验证目标：

- Bash 脚本语法仍正确。
- 前端依赖文件不包含内部 npm registry。
- 后端编译、冒烟测试、回归测试仍通过。
- Windows 入口改为 `.cmd` + `powershell -NoProfile`，绕开用户本机 Conda profile 解析错误。

说明：当前打包环境不是 Windows，无法真实执行 Windows PowerShell 5.1；因此本轮对 `.ps1` 进行了人工兼容性审查和脚本重写，实际 Windows 启动请优先使用 `.cmd` 入口。

## v9 一键启动脚本验证

- 新增 `一键启动.cmd` 和 `start-windows.cmd`，支持 Windows 双击启动。
- 新增 `start.sh`，支持 macOS/Linux 根目录一键启动。
- `deploy-local.ps1` 新增 `-OpenBrowser` 参数。
- `.cmd` 入口使用 `powershell.exe -NoProfile`，避免 Anaconda PowerShell profile 干扰。

## v10 Windows one-click script hotfix

- Rewrote `scripts/fix-npm-registry.ps1` and `scripts/deploy-local.ps1` as ASCII-only files to avoid Windows PowerShell 5.1 UTF-8-without-BOM parsing problems.
- Rewrote `.cmd` wrappers to launch PowerShell with `-NoProfile` and bypass Conda profile initialization issues.
- Confirmed no internal npm registry residue remains in frontend lock/config files.
