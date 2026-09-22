# AlgoStudy

AlgoStudy 是一个个人算法学习与刷题复盘系统，包含题库路线、题目详情、代码编辑与执行、提交记录、笔记、掌握度、间隔复习、弱项分析、个性化推荐、周报、模板库、AI 辅助提示和轻量沙箱执行。

## 功能概览

- 用户注册、登录、JWT 鉴权
- 题库列表、难度 / 标签 / 阶段 / 状态筛选
- 题目详情、starter code、多语言编辑
- Python / JavaScript / Java / C++ 本地执行
- 提交记录、最佳提交、错误原因记录
- 学习笔记与掌握度更新
- D+1 / D+3 / D+7 / D+14 / D+30 间隔复盘
- 弱项标签分析、每日推荐、周报
- 算法模板库、系统模板只读保护、个人模板、自定义模板、模板练习模式
- AI 难度预测、解题提示、代码审查、知识点讲解
- SQLite 本地数据存储、旧库自动迁移、迁移版本标记、外键约束、进度 / 笔记唯一性保护
- 统一分页响应、健康检查接口、GitHub Actions CI 验证

## 技术栈

- 后端：FastAPI、SQLAlchemy、Pydantic、SQLite、JWT
- 前端：React、Vite、React Router、Axios、Recharts、Monaco Editor
- 数据：`data/problems.json`、`data/templates.json`

## 快速开始

#
## 一键启动

Windows 推荐直接双击项目根目录的：

```text
一键启动.cmd
```

或在 PowerShell / CMD 中运行：

```powershell
.\start-windows.cmd
```

默认使用国内 npm 镜像 `https://registry.npmmirror.com/`，会自动修复 npm 源、安装后端/前端依赖、启动服务并打开浏览器。启动后访问：

```text
http://127.0.0.1:5173
```

如需指定 npm 源：

```powershell
.\start-windows.cmd https://registry.npmjs.org/
```

macOS / Linux 可运行：

```bash
./start.sh
```

停止服务：在启动窗口按 `Ctrl+C`，然后按提示确认。

## 1. 启动后端

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # 可选，建议设置 SECRET_KEY；生产环境必须设置
uvicorn app.main:app --reload
```

后端地址：

```text
http://localhost:8000
http://localhost:8000/docs
http://localhost:8000/health
```

默认演示账号：

```text
username: admin
password: admin123
```

> 长期使用时请修改默认密码，并在 `.env` 里设置强随机 `SECRET_KEY`。生产或共享环境建议设置 `APP_ENV=production`、`CREATE_DEMO_USER=false`。

### 2. 启动前端

```bash
cd frontend
npm install
cp .env.example .env  # 可选
npm run dev
```

如果 `npm install` 很慢、超时，或 PowerShell 启动时 Anaconda profile 报错，推荐使用不加载 profile 的 `.cmd` 包装脚本修复 npm 源：

```powershell
.\scripts\fix-npm-registry.cmd https://registry.npmmirror.com/
```

也可以直接运行 PowerShell 脚本，但建议加 `-NoProfile`：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\fix-npm-registry.ps1 -Registry https://registry.npmmirror.com/
```

前端地址：

```text
http://localhost:5173
```

### 3. 构建与检查

后端编译检查：

```bash
cd backend
python -m compileall -q app
```

后端冒烟测试：

```bash
cd backend
pip install -r requirements-dev.txt
python smoke_test.py
python regression_test.py
```

扩展接口回归测试（覆盖笔记 CRUD、模板全权限矩阵、题目筛选、统计与执行接口）：

```bash
cd backend
python -m pytest test_api_extended.py -q
```

后端覆盖率统计（smoke + regression + extended 合并）：

```bash
cd backend
python -m coverage run --source=app smoke_test.py
python -m coverage run --append --source=app regression_test.py
python -m coverage run --append --source=app -m pytest test_api_extended.py -q
python -m coverage report --fail-under=65
# 当前实测：核心路由 84%~100%，总计约 71%（HTML 报告：coverage_html/index.html）
```

前端安全检查与生产构建：

```bash
cd frontend
npm audit --omit=dev
npm run build
```

前端 E2E（Playwright，自动拉起后端 + 前端，走真实浏览器验证注册→登录→题库→详情→复盘→统计主链路）：

```bash
cd frontend
npx playwright install chromium   # 首次
npx playwright test
```

也可以从项目根目录一键执行：

```bash
./scripts/verify.sh
```

项目已内置 `.github/workflows/ci.yml`，推送或发起 PR 时会自动执行后端编译 / 冒烟 / 回归 / 覆盖率门槛测试和前端 audit / build / Playwright E2E。


## 一键部署

### Docker Compose 部署

项目已内置一键部署脚本：

```bash
./scripts/deploy.sh
```

默认访问：

```text
http://127.0.0.1:8080
http://127.0.0.1:8080/health
http://127.0.0.1:8080/docs
```

常用命令：

```bash
./scripts/deploy.sh --port 8088      # 指定端口
./scripts/deploy.sh --build          # 强制重新构建
./scripts/deploy.sh --status         # 查看状态
./scripts/deploy.sh --logs           # 查看日志
./scripts/deploy.sh --down           # 停止服务
```

Docker 部署默认关闭代码执行；可信本机/内网需要代码执行时可运行：

```bash
./scripts/deploy.sh --enable-code-exec --build
```

### 本地一键运行

不依赖 Docker 的本地启动方式：

macOS / Linux / Git Bash：

```bash
./scripts/deploy-local.sh
```

Windows 推荐方式：

```powershell
.\scripts\deploy-local.cmd https://registry.npmmirror.com/
```

如果要直接运行 PowerShell 脚本，请加 `-NoProfile`，避免 Anaconda / Conda profile 报错影响脚本：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\deploy-local.ps1 -NpmRegistry https://registry.npmmirror.com/
```

默认访问：

```text
http://127.0.0.1:5173
```

详细说明见 `docs/DEPLOYMENT.md`。

## 配置说明

后端配置见 `backend/.env.example`：

```text
APP_ENV=development
SECRET_KEY=replace-with-a-long-random-secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
CREATE_DEMO_USER=true
DEMO_USERNAME=admin
DEMO_EMAIL=admin@example.com
DEMO_PASSWORD=admin123
CODE_EXECUTION_ENABLED=true
MAX_CODE_EXECUTION_TIMEOUT=10
```

前端配置见 `frontend/.env.example`：

```text
VITE_API_BASE_URL=http://localhost:8000/api
```

Docker 构建前端镜像时可在项目根目录 `.env` 设置：

```text
NPM_REGISTRY=https://registry.npmjs.org/
# 国内网络可改为：https://registry.npmmirror.com/
```

## 数据库说明

默认数据库文件：

```text
backend/algo_study.db
```

首次启动后端时会自动创建数据库，并导入：

- `data/problems.json`
- `data/templates.json`

项目包含轻量启动迁移 `backend/app/migrations.py`，用于兼容早期单用户数据库，自动补齐多用户字段、模板所有权字段，移除旧约束，并在 `schema_migrations` 表中记录迁移标记。题库和系统模板 seed 现在是幂等 upsert，后续更新 JSON 文件后会自动同步系统数据，不覆盖个人学习数据。

如需清空本地数据重新开始：

```bash
rm backend/algo_study.db
uvicorn app.main:app --reload
```

## 文档

- `docs/RUNBOOK.md`：运行、配置、验证、常见问题
- `docs/OPTIMIZATION_REPORT.md`：代码检查、问题修复、二次优化与后续建议
- `docs/DATABASE_SCHEMA.md`：数据库表结构说明
- `docs/API_CONTRACT.md`：主要 API 返回结构与分页约定
- `docs/DEPLOYMENT.md`：Docker Compose、Windows `.cmd` / PowerShell 与本地一键部署说明
- `PROJECT_PLANNING.md` / `docs/PROJECT_PLAN.md`：完整项目规划、版本路线图、功能蓝图与验收标准

## 安全提示

代码执行功能适合本地学习场景。`/api/sandbox/execute` 已加入登录鉴权、临时目录、超时限制和输出长度限制，并可通过 `CODE_EXECUTION_ENABLED=false` 一键关闭，但仍不是生产级容器隔离。不要直接暴露到公网；如需线上使用，应改造成容器 / 微虚拟机隔离执行，并增加限流、审计和资源配额。

## 当前验证状态

本次已验证：

- 后端应用可导入并启动
- 后端核心 API 冒烟通过
- 后端回归检查通过：鉴权、校验、快速复盘日志、旧库迁移、系统模板只读、个人模板隔离
- JavaScript 与 Python 执行接口通过
- 匿名访问沙箱接口返回 401
- 前端 `npm audit --omit=dev` 结果为 0 vulnerabilities
- 前端 `npm run build` 通过，并完成 chunk 拆分优化
- 第四轮新增验证：dashboard 薄弱标签明细、AI 请求长度校验、提交分页、迁移版本标记、题库 / 模板库加载更多
- 第五轮新增验证：统一分页响应结构、健康检查接口、用户名大小写无关登录 / 防重复、CI 配置和一键验证脚本
- 第六轮新增验证：Docker Compose 部署文件、一键部署脚本、本地启动脚本和部署文档
