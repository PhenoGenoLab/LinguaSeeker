# Agents — 门户层

> 每个 `agents/<A>/` 只有 `__init__.py`：把图（phase 适配器、phase 5 工厂）需要的名字
> 从下层转出来。**不含实现**。

## 分层

```
pipeline/graph/                编排：topology、phases、routing
pipeline/graph/agents/<A>/     门户：只导出图用到的入口（本目录）
pipeline/skills/<A>/           专业 agent：prompt、模型调用、工具编排、Skill 类
core/tools/<A>/                具体工具：确定性能力（解析、匹配、导入、检索、投影、契约）
```

单向依赖：`graph → agents → skills → core/tools`。`core` 不 import `src.pipeline`；
`skills` 可以 import `src.dao`（它们承担持久化），但不得 import `topology/phases`。
断言位置：`tests/pipeline/test_import_boundaries.py`、`tests/core/test_layer_boundaries.py`。

## 门户清单

| agent | 门户导出的名字 | 实现位置 |
|-------|----------------|----------|
| acquisition | `AcquisitionSource`, `DocumentAcquisitionRequest` | `core/tools/acquisition` + `skills/acquisition` |
| parsing | `ParsingSkill` | `core/tools/parsing` + `skills/parsing` |
| translation | `TranslationService`, `detect_language` | `core/tools/translation` + `skills/translation` |
| extraction | `DualEvidenceExtractionResult`, `SourceFactChainService`, `project_dual_result` | `core/tools/extraction` + `skills/extraction` |
| standardization | `StandardizationSkill` | `core/tools/standardization` + `skills/standardization` |
| review | `ChatService`, `ChatLLMProvider`, `DeltaAuditService`, `FeedbackService`, `SourceLinker` | `core/tools/review` + `skills/review` |
| graph_retrieval | `GraphRagService` | `core/tools/graph_retrieval` + `skills/graph_retrieval` |

图以外的调用方（`src/api`、`src/runs`、scripts、tests）直接 import 实现所在路径，
不绕门户——门户不是兼容层。

## 使用

```python
from src.pipeline.graph.agents.acquisition import (
    AcquisitionSource,
    DocumentAcquisitionRequest,
)
from src.core.tools.acquisition import DocumentAcquisitionService

svc = DocumentAcquisitionService()
```
