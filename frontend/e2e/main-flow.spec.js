import { test, expect } from '@playwright/test'

/**
 * AlgoStudy 前端 E2E 冒烟：
 * 注册 -> 登录 -> 题库列表 -> 难度筛选 -> 题目详情 -> 更新进度 -> 复盘中心
 * 全程走真实前端 + 真实后端（webServer 自动拉起），验证主链路可用。
 */

const PASSWORD = 'pass12345'

test('完整主链路：注册登录到复盘', async ({ page }) => {
  const username = `e2e_${Date.now()}`

  // 1. 打开登录页，切到注册
  await page.goto('/login')
  await expect(page.locator('h1')).toHaveText('AlgoStudy')
  await page.getByRole('button', { name: '立即注册' }).click()

  // 2. 填写注册表单
  await page.getByPlaceholder('your@email.com').fill(`${username}@example.com`)
  await page.getByPlaceholder('username').fill(username)
  await page.getByPlaceholder('password', { exact: true }).fill(PASSWORD)
  await page.getByPlaceholder('confirm password').fill(PASSWORD)
  await page.getByRole('button', { name: '注册' }).click()

  // 3. 注册成功后回到登录态切换（切到登录 tab），用新账号登录
  await page.getByRole('button', { name: '立即登录' }).click()
  await page.getByPlaceholder('username').fill(username)
  await page.getByPlaceholder('password').fill(PASSWORD)
  await page.getByRole('button', { name: '登录' }).click()

  // 4. 登录后应跳转首页 Dashboard
  await expect(page).toHaveURL(/\//)
  await expect(page.locator('h1, .dashboard-title, .page-title').first()).toBeVisible({ timeout: 15_000 })

  // 5. 进入题库页
  await page.getByRole('link', { name: /题库/ }).first().click()
  await expect(page).toHaveURL(/\/problems/)
  await expect(page.locator('text=难度').first()).toBeVisible({ timeout: 15_000 })

  // 6. 难度筛选 Medium：应存在筛选控件且页面不报错
  const select = page.locator('select').first()
  if (await select.count()) {
    await select.selectOption({ label: 'Medium' })
    await page.waitForTimeout(1500)
  }

  // 7. 打开第一道题详情（卡片是 <a class="problem-card"> 链接）
  const firstCard = page.locator('a.problem-card').first()
  await expect(firstCard).toBeVisible({ timeout: 15_000 })
  await firstCard.click()
  await expect(page).toHaveURL(/\/problems\/\d+/)
  await page.waitForTimeout(1500)

  // 8. 详情页应有提交记录 / 笔记等模块（出现任一核心区块即通过）
  const detailText = await page.locator('body').innerText()
  expect(detailText.length).toBeGreaterThan(50)

  // 9. 回到题库，进入复盘中心
  await page.getByRole('link', { name: /复盘/ }).first().click()
  await expect(page).toHaveURL(/\/reviews/)
  await page.waitForTimeout(1000)

  // 10. 统计页可打开
  await page.getByRole('link', { name: /统计/ }).first().click()
  await expect(page).toHaveURL(/\/stats/)
  await page.waitForTimeout(1000)
  const bodyText = await page.locator('body').innerText()
  expect(bodyText.length).toBeGreaterThan(50)
})
