// 跨平台启动后端，供 Playwright 的 webServer 使用。
//
// 本地开发优先使用 backend/.venv 里的解释器（Windows 是 Scripts/python.exe，
// POSIX 是 bin/python）；CI（ubuntu-latest）没有 .venv，退回 runner 自带的
// python3 / python。此前这里写死 `cmd /c "... .venv\Scripts\python.exe ..."`，
// 在 Linux runner 上必然启动失败，E2E 步骤因此无法通过。
import { spawn } from 'node:child_process'
import { existsSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const backendDir = path.resolve(here, '..', '..', 'backend')
const isWindows = process.platform === 'win32'

const venvPython = path.join(
  backendDir,
  '.venv',
  isWindows ? 'Scripts' : 'bin',
  isWindows ? 'python.exe' : 'python',
)

// 绝对路径要求真实存在；裸命令名交给 PATH 解析。
// E2E_PYTHON 可显式指定解释器，便于本地用非默认的虚拟环境跑 E2E。
const candidates = [process.env.E2E_PYTHON, venvPython, 'python3', 'python'].filter(Boolean)
const python = candidates.find((candidate) =>
  path.isAbsolute(candidate) ? existsSync(candidate) : true,
)

const args = ['-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000']
console.log(`[e2e] backend: ${python} ${args.join(' ')} (cwd=${backendDir})`)

const child = spawn(python, args, { cwd: backendDir, stdio: 'inherit' })

child.on('error', (err) => {
  console.error(`[e2e] failed to start backend: ${err.message}`)
  process.exit(1)
})

child.on('exit', (code, signal) => {
  if (signal) {
    console.error(`[e2e] backend terminated by ${signal}`)
  }
  process.exit(code === null ? 1 : code)
})

for (const signal of ['SIGINT', 'SIGTERM']) {
  process.on(signal, () => child.kill(signal))
}
