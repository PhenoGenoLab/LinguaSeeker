# Runs

> 一次 pipeline run 的运行时外壳——作业队列、后台执行、状态契约与持久化、两级缓存。LangGraph 拓扑与 phase 适配器在 `src/pipeline/graph/`；agent 能力实现在 `src/core/agents/`。
>
> 本目录 2026-11-19 由 `src/agents/` 改名而来：旧名暗示这里放 agent，实际放的是 run。

## Overview

`runs/` 实现 Lingua Seeker 管线的**外层运行时**：后台运行器、作业调度器、PostgreSQL 状态持久化和作业队列。4 阶段有向图（Phase 1 文献获取 → Phase 2 文档解析 → Phase 3 翻译+证据提取 → Phase 4 实体标准化）的拓扑与各 Phase 适配器已在阶段 1 目录迁移中移到 `src/pipeline/graph/`；本目录不再包含编排器实现。Phase 5 不是图节点——它是独立的请求-响应式交互服务（证据审核、对话、审计），通过 `Phase5ServiceFactory` 在 API 层创建。

## Structure

```
runs/
├── runner.py                # 后台管线运行器（asyncio task + DB fallback）
├── dispatcher.py            # 单任务作业调度器（轮询 pipeline_jobs 表）
├── contracts.py             # 状态模型、枚举、错误层次、状态转换守卫
├── state_persistence.py     # PostgreSQL 状态持久化（直接 + 会话绑定两种模式）
├── processing_cache.py      # 两级文档处理缓存（L1 Redis + L2 PostgreSQL）
├── content_hash.py          # 内容哈希计算（SHA-256 去重）
├── concurrency.py           # 并发控制（信号量 + 重试执行器）
├── phase_5_factory.py       # Phase 5 服务工厂（交互审核层，API 层边界）
└── __init__.py

# 编排器与 Phase 1-4 适配器：
src/pipeline/graph/topology.py
src/pipeline/graph/phases/phase_{1..4}.py
```

## Key Components

### `PipelineOrchestrator` (src/pipeline/graph/topology.py)

基于 LangGraph 的管线编排器，构建 4 节点有向图（实现位于 pipeline 领域层）：

```
Phase 1 (文献获取) → Phase 2 (文档解析) → Phase 3 (翻译+提取) → Phase 4 (标准化) → END
```

- 每个 Phase 完成后状态持久化到 PostgreSQL（崩溃恢复）
- 单阶段模式支持上游依赖验证（Phase 2 需要 Phase 1，Phase 3 需要 Phase 1+2，Phase 4 需要 Phase 1+2+3）
- 适配器抛出分类错误，编排器决定重试或终止
- 使用 `RetryablePhaseExecutor` 实现指数退避重试

### `PipelineRunner` (runner.py)

后台管线运行器，管理 asyncio 任务：

- `start()` — 启动后台任务并记录到 PostgreSQL
- `get_last_state()` — 获取运行状态（先查内存缓存，再查 DB）
- `recover_orphaned_runs()` — 服务器重启后恢复中断的运行
- `shutdown()` — 优雅关闭，等待活跃任务完成
- `check_processing_cache()` — 查询两级缓存
- LRU 内存缓存最近 100 个状态

### `SingleJobDispatcher` (dispatcher.py)

单任务作业调度器，后台轮询 `pipeline_jobs` 表：

- 使用 `SELECT FOR UPDATE SKIP LOCKED` 原子性认领任务
- 即使多个后端进程运行也保证只有一个 worker 处理给定任务
- 生命周期：`start()` 在应用启动时调用，`stop()` 在关闭时调用

### `PipelineGraphState` (contracts.py)

管线编排状态的核心 Pydantic 模型，包含：

- `pipeline_status` — 管线整体状态（PENDING → RUNNING → COMPLETED/FAILED）
- `phase_1` / `phase_2` / `phase_3` — 各阶段的 `PhaseStatusDetail`
- `pipeline_mode` — 运行模式（FULL / PHASE）
- `source_type` — 文档来源（LOCAL / ONLINE）
- 状态转换守卫（`validate_pipeline_status_transition`、`validate_phase_status_transition`）

### 错误层次 (contracts.py)

```
PhaseError
├── RetryablePhaseError    # 瞬态错误，可重试（网络超时、LLM 速率限制）
└── PermanentPhaseError    # 永久错误，不重试（文件不存在、验证失败）
```

`classify_phase_error()` 根据异常类型自动分类并重新抛出。

### `SessionBoundStatePersistence` (state_persistence.py)

PostgreSQL 状态持久化层：

- `save_state()` — 保存管线状态到 `pipeline_run_states` 表
- `load_state()` — 加载最新状态
- `list_runs()` — 列出运行摘要（分页）
- `has_active_source_key()` — 检查是否有活跃运行处理同一文档
- 处理 Phase 2 重跑时的旧数据清理
- 自动维护 `source_documents` 和 `literature_profiles` 表

### `DocumentProcessingCacheService` (processing_cache.py)

两级文档处理缓存：

- **L1 Redis** — 热缓存，TTL 1 小时，键 `docproc:{content_hash}`
- **L2 PostgreSQL** — 持久缓存，表 `document_processing_cache`
- 读路径：L1 → L2（回填 L1）→ miss
- 写路径：L2 upsert → L1 set

### `Phase5ServiceFactory` (phase_5_factory.py)

Phase 5 服务工厂（交互审核层），作为 API 层和核心服务之间的边界：

- 长生命周期依赖（config、providers）在构造时注入
- 短生命周期依赖（AsyncSession）每次方法调用传入
- 创建：`FeedbackService`、`ChatService`、`SourceLinker`

## Usage / Patterns

### 管线运行流程

```
API: POST /pipeline/run
  → JobQueueRepository.enqueue()
  → SingleJobDispatcher 轮询认领
  → PipelineRunner.start()
  → PipelineOrchestrator.invoke()
    → AcquisitionAdapter.run()
    → ParsingAdapter.run()
    → FactChainAdapter.run()
  → 状态持久化 + 缓存写入
```

### 单阶段运行

```python
state = PipelineGraphState(
    pipeline_mode=PipelineMode.PHASE,
    phase_to_run=2,
    source_document_id="...",
    # Phase 1 已完成的输出
)
task = await runner.start(state)
```

### 状态查询

```python
state = await runner.get_last_state(processing_run_id)
print(state.pipeline_status, state.phase_2.status)
```

## Dependencies

| 依赖 | 用途 |
|------|------|
| LangGraph | 有向图编排 |
| SQLAlchemy | 状态持久化 |
| Redis (asyncio) | L1 缓存 |
| loguru | 结构化日志 |
| `src.pipeline.graph.*` | LangGraph 拓扑与 Phase 1-4 适配器 |
| `src.core.*` | Phase 1-4 业务逻辑服务 |
| `src.dao.postgresql.*` | 数据库模型和仓储 |
