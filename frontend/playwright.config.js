import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  timeout: 60_000,
  retries: 0,
  use: {
    baseURL: 'http://127.0.0.1:5173',
    headless: true,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  webServer: [
    {
      // 跨平台启动后端，见 e2e/start-backend.js。
      // 这里以前写死 `cmd /c "... .venv\Scripts\python.exe ..."`：Windows 专有写法，
      // 在 CI 的 ubuntu-latest 上无法执行，E2E 步骤必然失败。
      command: 'node e2e/start-backend.js',
      url: 'http://127.0.0.1:8000/health',
      reuseExistingServer: true,
      timeout: 60_000,
    },
    {
      command: 'npm run dev -- --host 127.0.0.1 --port 5173',
      url: 'http://127.0.0.1:5173',
      reuseExistingServer: true,
      timeout: 60_000,
    },
  ],
})
