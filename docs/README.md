# Documentation Index

> 项目文档，按生命周期状态组织。

## 概述

本目录是 Lingua Seeker 所有项目文档的索引和组织中心。文档按生命周期分类：活跃（active/）、计划中（planned/）、归档（archive/），以及模板和图表。

## 目录结构

```text
docs/
├── active/           # 进行中的计划和活跃参考文档
├── planned/          # 尚未开始的计划工作
├── codereview/       # 活跃代码审查（.gitkeep）
├── diagrams/         # Mermaid 流程图（phase1-phase4）
├── archive/
│   ├── plans/        # 已完成或被取代的计划
│   ├── codereview/   # 已完成的代码审查
│   └── deprecated-modules/  # 已移除模块的 README
└── templates/        # plan.md、codereview.md 模板
```

## 分类规则

- `active/` — 进行中的实施计划和活跃参考文档
- `planned/` — 尚未开始的计划工作（`YYYY-MM-DD-<topic>.md`）
- `codereview/` — 活跃代码审查报告
- `diagrams/` — 四个管线阶段的 Mermaid 流程图（`.mmd`）
- `archive/plans/` — 已完成或被取代的计划
- `archive/codereview/` — 已完成的代码审查
- `archive/deprecated-modules/` — 已移除模块保留的 README
- `templates/` — 可复用文档模板

### 文档迁移时机

| 触发条件 | 从 | 到 |
|---------|-----|-----|
| 开始实施计划 | `planned/` | `active/` |
| 计划完成/合并/被取代 | `active/`（或 `planned/`） | `archive/plans/` |
| 代码审查解决 | `codereview/` | `archive/codereview/` |

## 命名规范

新文档使用 `YYYY-MM-DD-<kebab-case-description>.md` 格式。

## 活跃计划和参考

- [2026-11-15 EIF2B5西语原文证据候选 R1](active/2026-11-15-eif2b5-spanish-fulltext-candidate-r1.md) — 无英文摘要；两位独立审阅确认来源及会议误命中；当前7条 RefSeq mRNA 的 c.338/c.713 参考碱基均不符原文 HGVS，变异级证据暂不可用。
- [2026-11-15 FZD2/omodisplasia西英摘要正文核查 R1](active/2026-11-15-fzd2-omodysplasia-spanish-abstract-audit-r1.md) — 双语单篇记录的西语正文/英文摘要对照；原文含更细病例史和测量，既往英文病例已有同一等位基因，患者与变异获取增量均为0；英文摘要 missense 用词经独立复核判为与 p.(Ser547*) 矛盾。
- [2026-11-15 GLA/TTR/PRKAG2葡英全文病例审计 R1](active/2026-11-15-gla-ttr-prkag2-portuguese-english-case-audit-r1.md) — 一个三变异、家系及酶学病例；出版方有完整英文译文，GLA p.Met290Ile 已见于英文队列；英译漏掉葡语 HCM 阈值的 `≥`，不计语言独占病例/变异。
- [2026-11-15 RPS6KA3中英摘要—正文事实筛查 R1](archive/papers/2026-11-15-rps6ka3-abstract-body-fact-screen-r1/README.md) — 盲态独立复核后登记19条有段落定位的原文候选/综述项，并对摘要覆盖差异作源文仲裁；全英文全文对应与患者去重未完成，主终点计数仍为0。
- [2026-11-15 多语种遗传病例候选初筛 R1](archive/papers/2026-11-15-multilingual-case-candidate-triage-r1/README.md) — 初筛7篇中/西/法/俄文全文；均有英文题名或摘要，不计来源/患者/变异增量；正文细节候选待英文对应仲裁。

- [2026-11-15 多语种遗传病例候选综合 R2](active/2026-11-15-multilingual-current-candidate-synthesis-r2.md) — 汇总 EIF2B5 转录本冲突、FZD2 正文/摘要信息差及葡语三变异双语控制；当前确认的语言独占患者/变异增量仍为0，不作总体推断。

### 基准测试与数据

| 日期 | 标题 | 状态 |
|------|------|------|
| 2026-07-04 | [Pipeline Path Exploration](active/2026-07-04-pipeline-path-exploration.md) | in-progress |
| 2026-11-17 | [Pipeline 阶段 0–1 迁移实施记录](active/2026-11-17-pipeline-stage-0-1-migration.md) | in-progress |
| 2026-11-18 | [Pipeline 阶段 2 迁移实施记录：AgentScope 运行时](active/2026-11-18-pipeline-stage-2-agentscope-runtime.md) | in-progress |
| 2026-06-29 | [Evidence DB Field Model Implementation Plan](active/2026-06-29-evidence-db-field-model-plan.md) | in-progress |
| 2026-06-15 | [ClinGen + ClinVar Fused Benchmark Dataset Plan](active/2026-06-15-clingen-clinvar-fused-benchmark-dataset-plan.md) | in-progress |
| 2026-06-14 | [Traceability Metrics Guide](active/2026-06-14-traceability-metrics-guide.md) | reference |

### 发布与运维

| 日期 | 标题 | 状态 |
|------|------|------|
| 2026-10-22 | [云上 PG 建库 / 全量引导 / 增量同步 SOP](active/2026-10-22-cloud-pg-sync-sop.md) | in-progress |
| 2026-08-01 | [dev → prod 数据库同步 Runbook](active/2026-08-01-dev-to-prod-sync-runbook.md) | superseded |
| 2026-06-25 | [Lingua Seeker v1.0.0 Release Checklist](active/2026-06-25-v1-release-checklist.md) | in-progress |
| 2026-06-27 | [Backend Host Deployment Guide](active/2026-06-27-backend-host-deployment-guide.md) | reference |
| 2026-06-23 | [Environment Consistency Standard](active/2026-06-23-environment-consistency.md) | reference |

### 架构参考

| 日期 | 标题 | 状态 |
|------|------|------|
| — | [APP_FLOW](active/APP_FLOW.md) | reference |
| — | [BACKEND_STRUCTURE](active/BACKEND_STRUCTURE.md) | reference |
| — | [FRONTEND_GUIDELINES](active/FRONTEND_GUIDELINES.md) | reference |
| — | [IMPLEMENTATION_PLAN](active/IMPLEMENTATION_PLAN.md) | reference |
| — | [Methods: Literature Filtering](active/methods_literature_filtering.md) | reference |
| — | [Phase Workflow Overview](active/phase_workflow_overview.md) | reference |
| — | [TECH_STACK](active/TECH_STACK.md) | reference |

### 用户指南

| 日期 | 标题 | 状态 |
|------|------|------|
| 2026-07-02 | [Evidence DB 与审核标注使用指南](active/2026-07-02-evidence-db-and-audit-user-guide.md) | reference |

完整列表见本目录源文件。

## 计划中工作

| 日期 | 标题 | 状态 |
|------|------|------|
| 2026-11-17 | [Pipeline 技术栈替换：LangGraph + AgentScope + ReMe](planned/2026-11-17-pipeline-agentscope-reme-migration.md) | planned（r2：含 skills/mcp/tools 领域层目录划分） |

## 归档计划

| 日期 | 标题 | 状态 |
|------|------|------|
| 2026-11-16 | [Pipeline Phase 3 切换为原文事实链](archive/plans/2026-11-16-source-fact-chain-pipeline-cutover.md) | completed |
| 2026-08-31 | [ACMG 多语种案例分析方法快照](archive/plans/2026-08-31-acmg-case-analysis-methodology-superseded.md) | superseded |
| 2026-08-28 | [GIM 模型面板诊断包概念](archive/plans/2026-08-28-gim-model-panel-diagnostic-archive.md) | completed |
| 2026-07-25 | [GraphRAG 集成方案](archive/plans/2026-07-25-graphrag-integration.md) | completed |
| 2026-07-01 | [Semantic Word Alignment Design](archive/plans/2026-07-01-semantic-word-alignment-design.md) | completed |
| 2026-07-01 | [Semantic Word Alignment Implementation Plan](archive/plans/2026-07-01-semantic-word-alignment-plan.md) | completed |
| 2026-06-20 | [Variant ID Guarantee Plan](archive/plans/2026-06-20-variant-id-guarantee-plan.md) | completed |
| — | [PRD — LinguaSeeker](archive/plans/PRD.md) | completed |

## 图表

| 文件 | 内容 |
|------|------|
| [phase1.mmd](diagrams/phase1.mmd) | Phase 1：文献获取、解析 |
| [phase2.mmd](diagrams/phase2.mmd) | Phase 3 原文事实链（分窗→抽取→核验→事实英译→双语行） |
| [phase3.mmd](diagrams/phase3.mmd) | Phase 3：实体标准化、知识对齐 |
| [phase4.mmd](diagrams/phase4.mmd) | Phase 4：证据可视化、专家反馈 |

## 模块 README 索引

每个 `backend/` 模块都有自己的 `README.md` 开发者指南。关键模块：

- **[backend/app/](../backend/app/README.md)** — FastAPI 应用入口
- **[backend/src/agents/](../backend/src/agents/README.md)** — 管线编排器（LangGraph）
- **[backend/src/api/](../backend/src/api/README.md)** — HTTP 边界、依赖注入
- **[backend/src/core/](../backend/src/core/README.md)** — 垂直功能切片
- **[backend/src/dao/](../backend/src/dao/README.md)** — 持久化层
- **[backend/libs/](../backend/libs/README.md)** — Rust 原生扩展
