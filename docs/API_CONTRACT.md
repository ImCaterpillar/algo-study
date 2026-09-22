# API Contract

本文档记录前端依赖的主要后端返回结构，便于后续继续迭代时避免接口破坏。

## 认证

除 `/`、`/health`、`/api/auth/login`、`/api/auth/register` 外，业务接口默认需要 Bearer Token：

```http
Authorization: Bearer <access_token>
```

用户名注册时会统一保存为小写，登录和重复检查按大小写无关方式处理。

## 健康检查

```http
GET /health
```

返回：

```json
{
  "status": "ok",
  "database": "ok",
  "version": "0.3.0"
}
```

## 统一分页响应

以下列表接口使用统一分页结构：

- `GET /api/problems`
- `GET /api/templates`
- `GET /api/submissions/problem/{problem_id}`
- `GET /api/reviews/due`
- `GET /api/reviews/history`

通用返回：

```json
{
  "items": [],
  "total": 0,
  "limit": 60,
  "offset": 0,
  "has_more": false
}
```

字段说明：

| 字段 | 说明 |
| --- | --- |
| `items` | 当前页数据。 |
| `total` | 当前筛选条件下的总数量。 |
| `limit` | 本次请求最大返回数量。 |
| `offset` | 本次请求起始偏移量。 |
| `has_more` | 是否还有下一页。 |

前端加载更多时应使用：

```text
next_offset = current_offset + items.length
```

并以 `has_more` 决定是否展示“加载更多”。

## 题库列表

```http
GET /api/problems?difficulty=Medium&tag=dp&status=Not%20Started&limit=60&offset=0
```

特别约定：

- `status=Not Started` 包含尚未创建 `progress` 记录的新用户题目。
- 标签筛选按 JSON 标签精确匹配，不再做字符串模糊匹配。

## 模板列表

```http
GET /api/templates?language=python&category=graph&limit=60&offset=0
```

特别约定：

- 返回系统模板和当前登录用户的个人模板。
- 系统模板 `is_system=true`，只读，不允许更新或删除。
- 个人模板 `is_system=false`，只对 owner 可见。

## 提交与复盘列表

提交历史：

```http
GET /api/submissions/problem/1?limit=20&offset=0
```

复盘历史：

```http
GET /api/reviews/history?problem_id=1&limit=20&offset=0
```

待复盘列表：

```http
GET /api/reviews/due?limit=60&offset=0
```

## 错误处理约定

- 未登录或 Token 失效：`401`。
- 访问他人的个人模板：`404`，避免泄露资源存在性。
- 尝试更新 / 删除系统模板：`403`。
- 请求字段不合法：`422`。
- 题目不存在：`404`。
