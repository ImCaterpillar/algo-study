# 安全说明（Security Notes）

本文记录 AlgoStudy 当前的安全边界、已修复的问题，以及**尚未**解决的问题。
它同时是以下变更的记录文档：沙箱加固、依赖升级（python-jose / passlib）。

---

## 1. 代码执行沙箱的安全边界

代码执行相关的模块：

| 文件 | 职责 |
| --- | --- |
| `backend/app/services/sandbox_runner.py` | 共享的加固子进程层（环境白名单、临时目录、进程树超时击杀、输出截断） |
| `backend/app/services/sandbox_service.py` | 多语言执行（`/api/sandbox/execute`） |
| `backend/app/services/execution_service.py` | 单语言快速执行（`/api/execute`） |

### 1.1 这是什么

**本地、单用户的演示用沙箱。** 它的作用是缩小提交代码的影响范围，**不是隔离边界**。
子进程仍然以服务器相同的操作系统用户身份运行，拥有相同的文件系统和网络访问权限。

### 1.2 已强制执行的措施

1. **环境变量白名单。** 子进程只继承 `_ENV_ALLOWLIST` 中列出的变量，外加模块内显式构造的覆盖项。
   服务器持有的 `SECRET_KEY`（JWT 签名密钥）、`DATABASE_URL`、各类 `*_API_KEY`、OAuth token、
   代理凭据等一律不会被继承。此外还有 `_ENV_DENY_PATTERN` 正则做二次兜底：即便将来误把某个
   凭据类变量加进白名单，也会在此被丢弃。
   > 修复前：原实现直接透传完整 `os.environ`，任何提交的代码片段都可以读到服务器密钥。
2. **显式工作目录。** 子进程在一次性临时目录中运行，且 `HOME` / `USERPROFILE` / `TEMP` / `TMP` /
   `TMPDIR` 均被指向该目录，因此 `~/.aws/credentials`、`~/.npmrc`、`~/.git-credentials` 这类
   基于用户主目录的查找不会命中真实配置。
3. **整棵进程树的超时击杀。** 子进程被放在独立的会话 / 进程组中启动（POSIX 用
   `start_new_session=True`，Windows 用 `CREATE_NEW_PROCESS_GROUP`），超时后按**进程组**击杀：
   POSIX 走 `os.killpg(os.getpgid(pid), SIGKILL)`，Windows 走 `taskkill /F /T /PID`，
   最后 `wait()` 回收。提交代码再派生出的辅助进程不会比请求活得更久。
4. **输出长度受限。** stdout / stderr 在返回前统一截断到 `MAX_OUTPUT_SIZE`。
5. **写入前拒绝符号链接。** 写入用户代码前检查目标是否为符号链接（`_checked_write`），
   避免被诱导写出临时目录。

### 1.3 未覆盖的风险（重要）

- **没有内存限制。** 原先声明的 `MAX_MEMORY_MB = 256` 是死代码：仓库内无任何引用，
  也从未真正调用 `resource.setrlimit`，即该上限历史上从未生效。**本次没有重新引入该限制**，
  原因是常见实现方式不成立：`RLIMIT_AS` 限制的是虚拟地址空间，而 V8（node）与 JVM 在启动时
  就会保留数 GB 地址空间，256MB 的 `RLIMIT_AS` 会让这两个运行时直接启动失败，而不是限制
  用户代码；`RLIMIT_DATA` 在现代分配器上同样有此缺陷。真正的内存限制需要容器内的 cgroup。
  **因此请不要把本沙箱描述为"有内存限制"。** 现已移除死代码，并在
  `sandbox_runner.py` 与两个服务的数据类注释中写明该字段恒为 `0.0`（既不测量也不限制）。
- **没有网络隔离**，没有 seccomp / 系统调用过滤，没有文件系统 jail，也没有只读根目录。
  提交代码仍可读取服务器用户有权读取的任何文件，包括服务器自身源码与数据库。
- **解释器可能就是服务器自身的虚拟环境解释器**，因此提交的 Python 仍可 `import` 服务器已装的包。
- **没有 CPU 配额、没有并发限流、没有审计日志。**

### 1.4 生产环境要求

任何面向共享、多用户或公网的部署，都必须把本模块替换为真正的隔离边界：

- gVisor，或
- Firecracker / 其它 microVM，或
- 每次执行使用一个一次性容器（cgroup 资源限制、只读根文件系统、禁用网络），

并补充限流、资源配额与审计日志。**不要**把调用本模块的接口暴露到公网。
`CODE_EXECUTION_ENABLED=false` 可一键关闭代码执行，Docker 部署默认即为关闭状态。

---

## 2. 依赖安全变更记录

### 2.1 python-jose：`3.3.0` → `3.5.0`（修复 CVE）

`backend/requirements.txt` 原固定 `python-jose[cryptography]==3.3.0`，该版本受以下漏洞影响：

| CVE | 类型 | 影响 |
| --- | --- | --- |
| CVE-2024-33663 | 算法混淆（algorithm confusion） | `jwt.decode` / `jws.verify` 在特定密钥形态下可被绕过签名校验 |
| CVE-2024-33664 | JWE 解压缩炸弹 | 畸形 JWE 触发资源耗尽（拒绝服务） |

两个漏洞均在 **3.4.0** 中修复。本次升级到 **3.5.0**（高于 3.4.0 的最低要求）。

**选择升级而非替换为 PyJWT 的原因：** `app/routes/auth.py` 与 `app/services/auth_service.py`
依赖 `jose` 的 `jwt` / `JWTError` 接口，升级即可消除漏洞且改动面最小；替换为 PyJWT 属于
更大的重构，收益不明确。

**兼容性验证：** 升级后 `smoke_test.py`、`regression_test.py`、`test_api_extended.py`
全部通过，JWT 签发与校验链路正常。

### 2.2 passlib：移除，改为直接使用 bcrypt

原依赖为 `passlib[bcrypt]==1.7.4` + `bcrypt==4.0.1`。

- passlib 1.7.4 发布于 2020 年，**已停止维护**；
- 它对 bcrypt 后端做了私有属性探测（`bcrypt.__about__`），在 bcrypt ≥ 4.1 上会直接报错——
  这正是仓库此前把 `bcrypt` 固定在 `4.0.1` 的原因，即**用锁死一个库来绕开一个废弃库的兼容问题**。

本次改为在 `app/services/auth_service.py` 中直接调用 `bcrypt`，并升级 `bcrypt` 到 `4.2.1`。
净效果：去掉一个停止维护的依赖，同时解除对 bcrypt 的版本封锁。

**哈希格式与行为兼容性（已实测验证）：**

- passlib 1.7.4 使用 bcrypt scheme，输出 `$2b$12$...`、长度 60；直接 `bcrypt.checkpw`
  **可以**校验这类哈希，无需迁移或重刷密码。
- passlib 对超过 72 字节的密码**静默截断**；新实现显式按 72 字节截断，语义完全一致。
- 已用真实数据验证：仓库自带演示库 `backend/algo_study.db` 中的 `admin` 账户哈希由 passlib 生成，
  换用新实现后 `POST /api/auth/login`（`admin` / `admin123`）返回 **200** 并正常签发 token，
  错误密码返回 **401**，`GET /api/auth/me` 返回 **200**。

### 2.3 直接使用 bcrypt 时发现的额外问题（已修复）

升级到 `bcrypt==4.2.1` 后，畸形哈希的处理方式发生了变化，**这是一个真实的健壮性缺陷**：

对 bcrypt 4.2.1 实测（每种输入单独子进程，20 秒硬超时）：

| 传入 `checkpw` 的哈希 | 结果 |
| --- | --- |
| `x`、`not-a-hash`、`$1$md5$...` | 抛出 `ValueError` |
| `$2b$12$tooshort`、`$2a$10$short` | 抛出 **`pyo3_runtime.PanicException`** |
| `$2b$99$<53 chars>`（非法 cost） | 抛出 `ValueError` |

关键在于 `PanicException` 由 Rust 侧 panic 产生：

- 它**继承自 `BaseException`**，因此 `except Exception` 与 `except ValueError` 都捕获不到；
- `pyo3_runtime` **不是可导入模块**（`import pyo3_runtime` 会 `ImportError`），
  所以也无法在 `except` 子句里写这个类名。

也就是说，一条格式损坏的哈希记录（更糟：可被外部影响的哈希）会让登录路径抛出
`except Exception` 拦不住的异常。修复方式是**在调用扩展之前先做格式校验**：
`auth_service.verify_password` 现在用正则
`^\$2[abxy]\$(?:0[4-9]|[12]\d|3[01])\$[./A-Za-z0-9]{53}$` 先确认这是格式合法、cost 处于
bcrypt 合法区间 04–31 的 bcrypt 哈希，不合法直接返回 `False`。
这一层格式校验才是真正的防线，`try/except ValueError` 只用于兼容 bcrypt ≤ 4.0 的 C 扩展行为。

对应的回归测试见 `backend/test_password_hashing.py`（含上述全部畸形用例）。

> 说明：本次还观察到一次**未能稳定复现**的现象——早期一个在同进程内连续调用
> `checkpw` 的探针脚本没有正常退出。在隔离实验中（每个用例独立子进程）全部用例都能正常
> 结束，未复现该现象，故此处仅作为观察记录，不据此声称存在死锁。无论该现象成因如何，
> 上述格式校验都使其无法被触发。

---

## 3. 仍待处理事项

以下问题本次**未**修复，如实记录：

1. **无内存 / CPU 配额**：见 1.3。需要容器化 cgroup 才能正确实现。
2. **无网络隔离**：提交代码可发起外连。
3. **无执行限流与审计日志**：接口有登录鉴权，但没有按用户的频率限制。
4. **`datetime.utcnow()` 已弃用**：仓库多处使用 `datetime.utcnow()`，在 Python 3.12+ 会触发
   `DeprecationWarning`，未来版本将移除。经确认当前 Python 3.12 / 3.14 上仍可用，故本次未改动
   （涉及面广且与本次目标无关），后续建议统一迁移到 `datetime.now(timezone.utc)`。
5. **演示数据库含历史测试账号**：`backend/algo_study.db` 中存在大量 `smoke_*` / `reg_*` / `e2e_*`
   等测试遗留账号。该文件被 `.gitignore` 忽略且未被 git 跟踪，因此不会进入仓库，本次保持原样未改动。
