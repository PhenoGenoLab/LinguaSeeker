# ReMe 外部知识服务 HTTP 契约

> 适用：pipeline 阶段 4a 的 `src/pipeline/mcp/reme/client.py` 与独立部署的 ReMe 服务。
> 版本：v1（2026-11-18）。客户端只依赖以下字段；服务端可追加字段，客户端必须忽略未知字段。
> **Status:** active

## 1. 通用约定

| 项 | 约定 |
|---|---|
| 传输 | HTTP/1.1，JSON body（`Content-Type: application/json`） |
| 鉴权 | `X-API-Key: <key>`（与 `PIPELINE_MEMORY_API_KEY` 一致）；缺失/错误返回 401 |
| 超时 | 客户端读超时 `PIPELINE_MEMORY_TIMEOUT`（默认 0.8s）；服务端应在 0.5s 内返回 |
| 网络 | 仅内网/容器网络；不得暴露公网 |
| 故障语义 | 客户端对所有传输/解析错误降级：召回返回空、写入返回 `accepted=false`，不抛出 |
| 版本 | 路径不带版本号；字段演进向后兼容，破坏性变更需新端点 |

## 2. `POST /search`

请求：

```json
{"query": "BRCA1 pathogenic variant severe hypotonia", "top_k": 5}
```

响应 200：

```json
{"cards": [{"text": "Markdown card body", "path": "digest/wiki/gene/brca1.md", "score": 0.87}]}
```

- `text` 必填，字符串；客户端截断到 2000 字符并做 XML 转义后注入 prompt。
- `path`、`score` 可选。
- `top_k` 由客户端配置（默认 5）；服务端可返回少于 `top_k` 条。
- 客户端从不把卡片内容当作证据或 quote；只作为参考上下文。

## 3. `POST /auto_memory`

请求：

```json
{"session_id": "<document_id>", "text": "{\"facts\":3,\"verifications\":{\"supported\":2},\"field_ids\":[\"A.gene_symbol\"]}"}
```

响应 200：

```json
{"accepted": true, "detail": ""}
```

- `text` 是客户端生成的 counts-only 摘要，**不含原文、quote、用户信息**。
- 服务端按 `session_id` 归档；重复写入不要求幂等（允许追加）。

## 4. `POST /auto_resource`

请求：

```json
{"path": "documents/<document_id>/output.md", "content": "# ..."}
```

响应 200：

```json
{"accepted": true, "detail": ""}
```

- `path` 为相对 workspace 的逻辑路径，禁止 `..` 穿越；服务端负责校验。
- 同一 `path` 重复写入按覆盖处理（幂等）。
- 客户端仅在显式启用时调用；Phase 2 产物接入待部署后开启。

## 5. `GET /health`

- 200 表示 workspace 可读写；非 200 视为不可用。
- 客户端只用于诊断，不参与主流程判定。

## 6. 错误码

| 状态 | 客户端行为 |
|---|---|
| 400/422 | 记录 warning，降级（视为调用失败） |
| 401/403 | 记录 warning，降级；不重试 |
| 5xx / 超时 / 连接失败 | 记录 warning，降级 |
| 200 但 JSON 结构不符 | 记录 warning，降级 |

## 7. 数据边界

- ReMe 不是权威存储：不得写入事实权威副本、术语表、逐条审计字段。
- workspace 只存公共文献知识与运行计数摘要；不存用户私有内容。
- 单 workspace 单写者：多 backend worker 只发请求，不各自启动 ReMe 运行时。

## 8. 契约测试

- 客户端单测：`tests/pipeline/test_reme_memory.py`（`httpx.MockTransport` 覆盖成功、500、连接失败、鉴权头）。
- 服务端接入后：用 `curl` 验证 §2–§5 的四种调用，再执行 runbook 的故障注入与召回评测。
