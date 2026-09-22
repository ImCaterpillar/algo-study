# AlgoStudy 运行手册

本文档记录本项目的本地启动、配置、验证与常见问题处理方式。

## 1. 项目结构

```text
algo-study/
├── backend/              # FastAPI + SQLAlchemy + SQLite 后端
│   ├── app/              # API、模型、服务、启动迁移
│   ├── requirements.txt  # 运行依赖
│   ├── requirements-dev.txt
│   ├── smoke_test.py     # 后端冒烟测试
│   └── .env.example
├── frontend/             # Vite + React 前端
│   ├── src/
│   ├── package.json
│   └── .env.example
├── data/                 # 初始题库与模板数据
└── docs/                 # 数据库说明、运行手册、优化报告
```

## 2. 环境要求

推荐版本：

- Python 3.11+
- Node.js 20+
- npm 10+

代码运行功能还会调用本机解释器或编译器：

- Python：需要 `python`
- JavaScript：需要 `node`
- Java：需要 `javac` 和 `java`
- C++：需要 `g++`

## 3. 后端启动

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
# Windows 使用：.venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # 可选，但建议设置 SECRET_KEY
uvicorn app.main:app --reload
```

后端默认地址：

```text
http://localhost:8000
http://localhost:8000/docs
```

首次启动会自动创建 `backend/algo_study.db`，并从 `data/problems.json` 与 `data/templates.json` 导入初始数据。

默认演示账号：

```text
username: admin
password: admin123
```

生产或长期自用时请立即修改默认密码，并在 `.env` 中设置强随机 `SECRET_KEY`。

## 4. 前端启动

```bash
cd frontend
npm install
cp .env.example .env  # 可选
npm run dev
```

前端默认地址：

```text
http://localhost:5173
```

前端通过 `VITE_API_BASE_URL` 连接后端，默认是：

```text
http://localhost:8000/api
```

## 5. 构建与验证

后端语法检查：

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

冒烟测试会验证注册、登录、题库、题目详情、统计、复盘、模板、代码执行与沙箱执行等核心接口。

前端生产构建：

```bash
cd frontend
npm run build
```

前端依赖安全检查：

```bash
cd frontend
npm audit --omit=dev
```

## 6. 数据库与迁移说明

项目使用 SQLite，默认文件是：

```text
backend/algo_study.db
```

`app/migrations.py` 包含轻量启动迁移，用于兼容旧版单用户数据库。它会在启动时自动补齐 `progress`、`problem_notes`、`submissions`、`review_logs`、`ai_hints` 等表的 `user_id` 字段，补齐 `templates.owner_user_id` / `templates.is_system` 字段，并移除旧库中 `progress.problem_id` / `problem_notes.problem_id` 的单用户唯一约束。

如需重置本地数据：

```bash
rm backend/algo_study.db
uvicorn app.main:app --reload
```

Windows PowerShell：

```powershell
Remove-Item backend/algo_study.db
uvicorn app.main:app --reload
```

## 7. 代码执行安全提示

本项目的代码执行功能适合本地学习使用。虽然 `/api/sandbox/execute` 使用临时目录、超时和输出长度限制，并要求登录鉴权，但它仍然不是生产级容器隔离方案。不要把代码执行服务直接暴露到公网。

上线前建议：

1. 使用 Docker / Firecracker / gVisor 等隔离运行用户代码。
2. 为每次执行设置 CPU、内存、文件系统、进程数与网络限制。
3. 增加接口限流、审计日志与队列执行。
4. 禁止使用默认账号和默认 `SECRET_KEY`。

## 8. 常见问题

### 登录接口报 `python-multipart` 缺失

请确认已经安装最新 `backend/requirements.txt`：

```bash
pip install -r backend/requirements.txt
```

### `no such column: progress.user_id`

这是旧版数据库结构问题。新版启动时会自动迁移。若仍然异常，可以备份后删除 `backend/algo_study.db` 让项目重新生成。

### 前端构建提示 Rollup optional dependency 缺失

通常是不同系统拷贝 `node_modules` 导致。删除并重新安装即可：

```bash
cd frontend
rm -rf node_modules
npm install
npm run build
```

### 前端登录后页面空白

已修复登录后跳转路径问题。登录成功后会回到首页 `/`，刷新用户状态。

## 9. 四次优化新增配置

`.env.example` 现在额外支持：

```text
APP_ENV=development
CREATE_DEMO_USER=true
DEMO_USERNAME=admin
DEMO_EMAIL=admin@example.com
DEMO_PASSWORD=admin123
CODE_EXECUTION_ENABLED=true
MAX_CODE_EXECUTION_TIMEOUT=10
```

建议：

- 本地学习可保留 `CREATE_DEMO_USER=true`。
- 生产或共享环境设置 `APP_ENV=production`、`CREATE_DEMO_USER=false`，并必须设置强随机 `SECRET_KEY`。
- 需要彻底关闭代码执行能力时设置 `CODE_EXECUTION_ENABLED=false`。
- `MAX_CODE_EXECUTION_TIMEOUT` 最大会被服务端限制在 30 秒以内。

手动执行轻量迁移：

```bash
cd backend
source .venv/bin/activate
python -m app.migrations
```

---

# v5 运维补充

## 健康检查

部署或本地排查时可以先访问：

```bash
curl http://localhost:8000/health
```

正常返回示例：

```json
{"status":"ok","database":"ok","version":"0.3.0"}
```

如果该接口失败，优先检查后端进程、`.env`、`DATABASE_URL` 和数据库文件权限。

## 一键验证

项目根目录新增：

```bash
./scripts/verify.sh
```

该脚本会依次执行：

1. 后端 `python -m compileall -q app`
2. 后端 `python smoke_test.py`
3. 后端 `python regression_test.py`
4. 前端 `npm audit --omit=dev`
5. 前端 `npm run build`

首次使用前仍需分别安装后端和前端依赖。

## CI

GitHub Actions 配置位于：

```text
.github/workflows/ci.yml
```

推送代码或提交 PR 后会自动运行后端和前端验证。CI 中使用测试专用 `SECRET_KEY`，不会读取本地 `.env`。

## 分页接口注意事项

v5 起，以下接口不再返回裸数组，而是返回统一分页对象：

```text
GET /api/problems
GET /api/templates
GET /api/submissions/problem/{problem_id}
GET /api/reviews/due
GET /api/reviews/history
```

前端或脚本应从 `items` 读取数据，并使用 `has_more` 判断是否继续请求下一页。


## 一键部署

Docker Compose 部署：

```bash
./scripts/deploy.sh
```

本地一键运行：

```bash
./scripts/deploy-local.sh
```

查看完整部署参数和生产配置说明：`docs/DEPLOYMENT.md`。
