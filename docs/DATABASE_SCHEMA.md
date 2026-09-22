# 数据库模型说明

项目使用 SQLite + SQLAlchemy。数据库文件默认生成在：

```text
backend/algo_study.db
```

启动后端时会自动建表并导入 `data/problems.json` 与 `data/templates.json`。旧版单用户数据库会在启动时由 `backend/app/migrations.py` 自动迁移为多用户结构。

## users

保存用户账号。

| 字段 | 说明 |
|---|---|
| id | 用户 ID |
| username | 用户名，唯一 |
| email | 邮箱，唯一 |
| hashed_password | bcrypt 密码哈希 |
| is_active | 是否启用 |
| created_at | 创建时间 |
| updated_at | 更新时间 |

## problems

保存精选题库。

| 字段 | 说明 |
|---|---|
| id | 本项目题目 ID |
| leetcode_id | LeetCode 原编号 |
| title | 英文标题 |
| title_cn | 中文标题 |
| slug | LeetCode URL slug |
| difficulty | Easy / Medium / Hard |
| description | 学习用简述，不复制完整题面 |
| examples | JSON 字符串，少量示例 |
| constraints_text | 约束说明，占位提示 |
| tags | JSON 字符串，知识点标签 |
| stage | beginner / core / advanced |
| source | 来源说明 |
| source_url | 原题链接 |
| key_pattern | 关键解题模式 |
| starter_code | 多语言初始代码 JSON |
| recommended_order | 推荐学习顺序 |
| created_at | 创建时间 |
| updated_at | 更新时间 |

## progress

保存每个用户在每道题上的进度与复盘状态。`(user_id, problem_id)` 具有唯一约束。

| 字段 | 说明 |
|---|---|
| id | 进度记录 ID |
| user_id | 用户 ID |
| problem_id | 题目 ID |
| status | Not Started / Attempted / Accepted / Need Review |
| attempts | 尝试次数 |
| solved_count | 通过次数 |
| first_solved_at | 第一次通过时间 |
| last_attempt_at | 最近提交时间 |
| last_review_at | 最近复盘时间 |
| next_review_at | 下次复盘时间 |
| mastery_level | 掌握度 0-5 |
| confidence | 信心 0-5 |
| is_favorite | 是否收藏 |
| is_archived | 是否归档 |

## submissions

保存每个用户的提交记录。

| 字段 | 说明 |
|---|---|
| id | 提交 ID |
| user_id | 用户 ID |
| problem_id | 题目 ID |
| language | python / javascript / java / cpp |
| code | 用户代码 |
| status | Accepted / Wrong Answer / Runtime Error / Compile Error / Timeout / Need Review |
| runtime_ms | 运行时间，单位毫秒 |
| memory_mb | 预留内存字段 |
| error_message | 错误信息 |
| fail_reason | 错因分类 |
| is_best | 是否最佳提交 |
| created_at | 创建时间 |

## problem_notes

保存每个用户的每题学习笔记。`(user_id, problem_id)` 具有唯一约束。

| 字段 | 说明 |
|---|---|
| id | 笔记 ID |
| user_id | 用户 ID |
| problem_id | 题目 ID |
| idea | 解题思路 |
| key_points | 关键点 |
| complexity | 时间 / 空间复杂度 |
| pitfalls | 易错点 |
| summary | 复盘总结 |
| created_at | 创建时间 |
| updated_at | 更新时间 |

## templates

保存算法模板库。系统内置模板为只读，用户新建或复制后的模板归属于个人。

| 字段 | 说明 |
|---|---|
| id | 模板 ID |
| owner_user_id | 模板所有者；系统模板为空 |
| is_system | 是否系统内置模板；系统模板只读 |
| name | 模板名称 |
| category | 模板分类 |
| language | python / javascript / java / cpp |
| code | 模板代码 |
| explanation | 模板解释 |
| tags | 关联标签 JSON 字符串 |
| usage_scenario | 适用场景 |
| created_at | 创建时间 |
| updated_at | 更新时间 |

## review_logs

保存每个用户的复盘历史。

| 字段 | 说明 |
|---|---|
| id | 复盘记录 ID |
| user_id | 用户 ID |
| problem_id | 题目 ID |
| review_type | Manual / Quick / D+1 / D+3 / D+7 / D+14 / D+30 |
| result | 复盘结果：掌握 / 部分遗忘 / 完全遗忘 |
| notes | 复盘备注 |
| prev_mastery_level | 复习前掌握度 |
| new_mastery_level | 复习后掌握度 |
| review_interval_days | 距上次复习天数 |
| created_at | 创建时间 |

## ai_hints

保存 AI 辅助提示记录。

| 字段 | 说明 |
|---|---|
| id | AI 记录 ID |
| user_id | 用户 ID |
| problem_id | 题目 ID |
| submission_id | 关联提交，可为空 |
| hint_type | 思路提示 / 错因分析 / 复杂度优化等 |
| prompt | 提示词 |
| response | AI 返回内容 |
| created_at | 创建时间 |

## schema_migrations

保存轻量迁移的应用标记，便于排查本地数据库是否已经跑过兼容迁移。

| 字段 | 说明 |
|---|---|
| name | 迁移标记名称，例如 `2026-05-18-v4-hardening` |
| applied_at | 应用时间 |

## Seed 行为

`data/problems.json` 与 `data/templates.json` 采用幂等 upsert：

- 题库系统字段会随 seed 文件更新。
- 系统模板会随 seed 文件更新。
- 用户个人模板、提交、进度、笔记、复盘记录不会被 seed 覆盖。
