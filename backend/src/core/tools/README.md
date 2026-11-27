# core/tools — 具体工具

> skills 调用的确定性工具：契约、规则、匹配、解析、持久化。**不含 AgentScope 对象**。

## 分层位置

```
pipeline/graph     编排（topology、phases、routing）
pipeline/skills    agent 实现（AgentScope agent、prompt、模型调用、toolkit 注册）
core/tools         具体工具 ← 本目录
```

单向依赖：上层可 import 下层；本目录**不得 import `agentscope`**，也不得 import `src.pipeline`。

AgentScope 的框架约束由 skills 侧承担：agent 构造、`Toolkit`/`FunctionTool` 注册、工具实例化
都在 `src/pipeline/skills/runtime/` 与各 skill 内完成，本目录只提供被调用的纯逻辑与契约。

## 目录

```
tools/
├── acquisition/       # 文献采集：DocumentAcquisitionService、契约、local_upload
├── parsing/           # MinerU remote 编排、显式 local parser、契约
├── extraction/        # 证据抽取确定性部分：契约、core、domain、reconcile、verify、projection
├── standardization/   # 匹配、导入、投影、hgvs、similarity_match 等
├── translation/       # 契约、artifact 持久化、语言检测
├── review/            # 检索、反馈、delta audit、source link、variant 聚合
└── graph_retrieval/   # 图契约、builder、retrieval、Neo4j provider
```

各子包按需导入；`import src.core.tools` 本身不加载任何阶段 SDK。

## 边界

- 不 import `agentscope`（框架对象属于 skills）。
- 不 import `src.pipeline`（core 是依赖叶子）。
- 由 `tests/pipeline/test_import_boundaries.py` 断言。
