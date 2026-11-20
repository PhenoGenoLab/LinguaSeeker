# Agents — 业务能力实现层

> 本层按 **agent 能力**划分，不表示阶段。阶段（谁先谁后、何时重试、何时跳过）由
> `src/pipeline/graph/` 的 LangGraph 拓扑决定；这里只回答"这个 agent 能做什么"。

## 结构

```
agents/
├── acquisition/        # 文献采集：本地上传、在线获取（委托 lit-acquisition SDK）
├── parsing/            # 文档解析：MinerU remote/local、产物落盘
├── translation/        # 翻译：术语映射、句级对齐、语言校验
├── extraction/         # 证据抽取：ACMG 字段目录、双轨证据、分组规则
├── standardization/    # 实体标准化：精确/语义匹配、术语持久化、ACMG 投影
├── review/             # 专家审核：证据检索、反馈、问答
└── graph_retrieval/    # 图谱：证据图构建与检索问答
```

## 依赖规则

- `agents/*` 可以互相引用（同级），可以依赖 `src.core.foundation`、`src.core.shared`。
- `agents/*` **不得** import `src.pipeline`：是图调用 agent，不是 agent 反向驱动图。
- `src.core.shared.tools`（纯规则）被 agent 调用，反之不成立。
- 断言位置：`tests/core/test_layer_boundaries.py`。

## 常用入口

| agent | 入口 |
|-------|------|
| acquisition | `acquisition.service.DocumentAcquisitionService` |
| parsing | `parsing.service.create_parse_service` / `ParseDocumentService` |
| translation | `translation.api.TranslationService` |
| extraction | `extraction.api.EvidenceExtractionService` |
| standardization | `standardization.api.EntityStandardizationService` |
| review | `review.search_service.SearchService`、`review.feedback_service.FeedbackService` |
| graph_retrieval | `graph_retrieval.api.GraphRagService` |

各 agent 内部的调用约定（契约、阶段编排、重试语义）见对应目录的 `README.md`。

## 使用

```python
from src.core.agents.acquisition import (
    DocumentAcquisitionService,
    DocumentAcquisitionRequest,
    AcquisitionSource,
)
from src.core.agents.parsing import create_parse_service

svc = DocumentAcquisitionService()
result = await svc.acquire(
    DocumentAcquisitionRequest(
        source=AcquisitionSource.ONLINE,
        query="ACMG variant classification",
        limit=10,
    )
)

parse_svc = create_parse_service()
parsed = await parse_svc.parse(result.downloads[0].file_path)
```

> 线上流程不直接调用本层：`src/pipeline/graph/phases/*.py` 才负责把它们接到图上。
