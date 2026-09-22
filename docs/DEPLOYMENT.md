# 一键部署说明

项目新增两种一键启动/部署方式：

- `scripts/deploy.sh`：Docker Compose 部署，适合服务器、长期运行或生产式演示。
- `scripts/deploy-local.sh`：本地一键运行，不依赖 Docker，适合开发、调试和课堂演示。

## 方式一：Docker Compose 一键部署

### 前置条件

需要安装：

- Docker Engine / Docker Desktop
- Docker Compose v2，也就是支持 `docker compose` 命令

### 首次部署

在项目根目录执行：

```bash
./scripts/deploy.sh
```

脚本会自动完成：

1. 复制 `.env.deploy.example` 为 `.env`。
2. 自动生成安全的 `SECRET_KEY`。
3. 构建后端镜像和前端 Nginx 镜像。
4. 启动后端、前端和 SQLite 数据卷。
5. 等待 `/health` 健康检查通过。

默认访问地址：

```text
http://127.0.0.1:8080
http://127.0.0.1:8080/health
http://127.0.0.1:8080/docs
```

### 指定端口

```bash
./scripts/deploy.sh --port 8088
```

访问：

```text
http://127.0.0.1:8088
```

### 强制重新构建

```bash
./scripts/deploy.sh --build
```

### 指定 npm 源

Docker 构建前端镜像时默认使用公开 npm 源。如果网络较慢，可以指定镜像源：

```bash
./scripts/deploy.sh --npm-registry https://registry.npmmirror.com/ --build
```

### 查看状态

```bash
./scripts/deploy.sh --status
```

### 查看日志

```bash
./scripts/deploy.sh --logs
```

### 停止服务

```bash
./scripts/deploy.sh --down
```

停止服务不会删除数据。SQLite 数据保存在 Docker volume：

```text
algo-study_algo_study_data
```

如果需要彻底清空数据，可以执行：

```bash
docker volume rm algo-study_algo_study_data
```

> 执行前请确认不再需要旧学习记录。

## 代码执行功能

Docker 部署默认关闭代码执行：

```env
CODE_EXECUTION_ENABLED=false
INSTALL_CODE_RUNNERS=false
```

这是为了避免把代码执行服务直接暴露到公网。如果只在可信内网或本机使用，并且确实需要在线运行 Python / JavaScript / Java / C++，可以执行：

```bash
./scripts/deploy.sh --enable-code-exec --build
```

脚本会修改 `.env`：

```env
CODE_EXECUTION_ENABLED=true
INSTALL_CODE_RUNNERS=true
```

并在后端镜像中安装 Node.js、g++ 和 JDK。

> 即使开启后，当前执行器仍不是生产级强隔离。公网部署建议继续保持关闭，或改造成容器 / 微虚拟机隔离执行。

## 生产配置建议

部署前建议检查项目根目录 `.env`：

```env
APP_ENV=production
SECRET_KEY=自动生成或手动设置的长随机字符串
CREATE_DEMO_USER=false
CODE_EXECUTION_ENABLED=false
```

如果要保留演示账号，可以临时设置：

```env
CREATE_DEMO_USER=true
DEMO_USERNAME=admin
DEMO_EMAIL=admin@example.com
DEMO_PASSWORD=请改成强密码
```

## 方式二：本地一键运行

不想安装 Docker 时，可以执行：

macOS / Linux / Git Bash：

```bash
./scripts/deploy-local.sh
```

Windows 推荐方式：

```powershell
.\scripts\deploy-local.cmd https://registry.npmmirror.com/
```

该 `.cmd` 包装脚本会用 `powershell -NoProfile` 调用真正的 PowerShell 脚本，可以绕开 Anaconda / Conda profile 启动时报错的问题。

如果要直接运行 PowerShell 脚本，请加 `-NoProfile`：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\deploy-local.ps1 -NpmRegistry https://registry.npmmirror.com/
```

脚本会自动完成：

1. 创建 `backend/.env` 和 `frontend/.env`。
2. 自动生成后端 `SECRET_KEY`。
3. 创建 Python 虚拟环境并安装后端依赖。
4. 安装前端 npm 依赖。
5. 同时启动后端和前端开发服务器。

默认访问地址：

```text
http://127.0.0.1:5173
http://127.0.0.1:8000/health
http://127.0.0.1:8000/docs
```

按 `Ctrl+C` 可同时停止前后端。

### 指定本地端口

```bash
BACKEND_PORT=8010 FRONTEND_PORT=5180 ./scripts/deploy-local.sh
```

## 文件清单

本轮新增部署相关文件：

```text
.env.deploy.example
docker-compose.yml
backend/Dockerfile
frontend/Dockerfile
frontend/nginx.conf
scripts/deploy.sh
scripts/deploy-local.sh
scripts/deploy-local.ps1
scripts/deploy-local.cmd
scripts/fix-npm-registry.sh
scripts/fix-npm-registry.ps1
scripts/fix-npm-registry.cmd
docs/DEPLOYMENT.md
```

## 常见问题

### 1. `docker compose` 不存在

说明 Docker Compose v2 未安装或 Docker 版本较旧。升级 Docker Desktop / Docker Engine 后重试。

### 2. 端口 8080 被占用

使用其他端口：

```bash
./scripts/deploy.sh --port 8088
```

### 3. 部署后前端能打开但接口报错

查看服务状态和日志：

```bash
./scripts/deploy.sh --status
./scripts/deploy.sh --logs
```

也可以直接检查：

```text
http://127.0.0.1:8080/health
```

### 4. 修改前端 API 地址后不生效

前端的 `VITE_API_BASE_URL` 是构建时变量。修改 `.env` 后需要重新构建：

```bash
./scripts/deploy.sh --build
```


### 5. `npm install` 访问内部地址或超时

如果报错里出现类似：

```text
packages.applied-caas-gateway1.internal.api.openai.org
```

请在项目根目录执行修复脚本，Windows 推荐使用 `.cmd` 入口：

```powershell
.\scripts\fix-npm-registry.cmd https://registry.npmmirror.com/
```

也可以直接运行 PowerShell 脚本，但建议加 `-NoProfile`：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\fix-npm-registry.ps1 -Registry https://registry.npmmirror.com/
```

然后重新安装：

```powershell
cd frontend
npm install
```


### 6. 打开 PowerShell 就出现 Anaconda / Conda `Invoke-Expression` 报错

这是本机 PowerShell profile 中 Conda 初始化脚本解析 PATH 时出错，和 AlgoStudy 项目代码无关。项目脚本已经提供 `.cmd` 包装入口，并强制使用 `powershell -NoProfile`，可以绕开该问题：

```powershell
.\scripts\fix-npm-registry.cmd https://registry.npmmirror.com/
.\scripts\deploy-local.cmd https://registry.npmmirror.com/
```

如果仍想直接运行 `.ps1`，请使用：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\deploy-local.ps1 -NpmRegistry https://registry.npmmirror.com/
```

## Windows 一键启动

解压项目后，进入项目根目录，双击：

```text
一键启动.cmd
```

或者在命令行运行：

```powershell
.\start-windows.cmd
```

脚本会自动执行：

1. 使用 `-NoProfile` 启动 PowerShell，绕过本机 Anaconda profile 报错。
2. 修复 npm registry 和 `.npmrc`。
3. 创建/更新后端 `.env` 和前端 `.env`。
4. 创建 Python 虚拟环境并安装后端依赖。
5. 安装前端依赖。
6. 启动 FastAPI 后端和 Vite 前端。
7. 自动打开浏览器到 `http://127.0.0.1:5173`。

默认 npm 源为：

```text
https://registry.npmmirror.com/
```

如需使用官方源：

```powershell
.\start-windows.cmd https://registry.npmjs.org/
```

端口默认：

```text
后端：http://127.0.0.1:8000
前端：http://127.0.0.1:5173
```
