# 确认性文献检索复用审计 R1

**Status:** in-progress  
**Created:** 2026-11-16  
**Completed:**  
**PR:** 未合并

## 目的

将已冻结的 A2/B2/C3/D1 确认性设计接到可复用的本地文献获取项目，同时保持英文基线门禁、来源可追溯性和访问失败边界。本文档只记录离线计划与适配约束，不代表已启动 n=500 检索。

## 复用来源

- 本地路径：`/data/yangzs/Projects/01_Platform/05_lit-acquisition`
- GitHub：<https://github.com/lanshi17/lit-acquisition>
- 记录提交：`14e3dbfd07f1a5e7fbc1257c7f9fea37e29dca40`
- 包版本：`0.5.1`
- 审计工件：[retrieval_reuse_audit_r1.json](../../benchmark/experiments/acmg_multilingual/overall_design/retrieval_reuse_audit_r1.json)

该 checkout 的相关 provider、gateway、编排、下载和网络安全源码均已保存 SHA-256。工作树存在未跟踪的 `scripts/bulk_fulltext.py`，因此复现时应使用记录提交并核对源码哈希。

## A2 映射与适配

确认性两臂使用同一个来源宇宙和相同顺序：Europe PMC → PMC → Crossref → OpenAlex → DOAJ。Europe PMC 和 PMC 提供全文入口；Crossref、OpenAlex、DOAJ 提供元数据、DOI 或开放获取路径发现。语言相关的默认 provider 矩阵不直接使用，因为它会改变各语言的来源覆盖。

复用项目已经提供：

- `OnlineAcquisitionSourceTraceEntry`：provider、尝试次数、成功状态、候选数、下载数、警告和错误；
- 单 provider deadline、phase deadline 与仅对瞬时错误重试；
- `CONFIG_MISSING`、`PROVIDER_UNAVAILABLE`、`TIMEOUT`、`NETWORK_ERROR`、`PROVIDER_HTTP_<status>` 错误分类；
- 请求前、重定向逐跳 SSRF 检查，安全下载时固定已验证 IP，并对日志做 secret redaction。

适配器仍必须自行执行 D1：每个语言一个固定模板，每个查询最多保留 20 个去重候选，最多尝试 20 篇全文，不追加查询；所有候选（包括预算外、摘要-only、不可访问和未决记录）都进入 disposition ledger。访问失败不能编码为英文阴性。

## 离线计划

- [confirmatory_query_plan_r1.json](../../benchmark/experiments/acmg_multilingual/overall_design/confirmatory_query_plan_r1.json)：500 题 × 4 语言，共 2,000 条哈希查询定义；英文投影 500 条；中文仅使用 ORPHA/HPO 语言中性槽位。
- [english_baseline_query_plan_r1.json](../../benchmark/experiments/acmg_multilingual/overall_design/english_baseline_query_plan_r1.json)：英文基线的固定查询身份和 provider 计划。
- [confirmatory_retrieval_ledger_schema_r1.json](../../benchmark/experiments/acmg_multilingual/overall_design/confirmatory_retrieval_ledger_schema_r1.json)：查询、候选处置、全文访问和双审字段契约。
- [confirmatory_retrieval_ledger_stub_r1.json](../../benchmark/experiments/acmg_multilingual/overall_design/confirmatory_retrieval_ledger_stub_r1.json)：2,000 行 `not_run` 空台账，防止查询遗漏。
- [english_baseline_readiness_r1.json](../../benchmark/experiments/acmg_multilingual/overall_design/english_baseline_readiness_r1.json)：离线 readiness 结果。
- [confirmatory_retrieval_plan_validation_r1.json](../../benchmark/experiments/acmg_multilingual/overall_design/confirmatory_retrieval_plan_validation_r1.json)：计划哈希、模板绑定、ledger schema 和无网络状态的回放收据。

重放命令：

```bash
uv run python scripts/build_confirmatory_retrieval_plan_r1.py
uv run python scripts/validate_confirmatory_retrieval_plan_r1.py
```

当前离线验证通过，且 `retrieval_authorized=false`、`network_accessed=false`。剩余门禁是：执行英文基线并保存访问/摘要-only ledger、完成候选处置守恒、绑定两名 AI reviewer 与独立仲裁者、最后重新封存 protocol snapshot。通过这些门禁前，不应调用外部 provider。

## 英文基线执行结果

已运行冻结的 500 条英文查询，生成 500 个查询 ledger 和 2,500 个 provider response receipt。共保留 220 个候选出现记录，220 个候选处置记录与其一一守恒；访问失败均保留 `access_failure_is_negative=false`。由于 PMC、Crossref、OpenAlex 触发限流并进入 circuit-open，剩余 DOI-only 候选没有直接全文路径，本轮全文数为 0。复用项目 v0.5.1 只返回规范化 gateway envelope，未提供原始 HTTP body，因此这一限制已写入收据。

- [英文执行收据](../../benchmark/experiments/acmg_multilingual/overall_design/executions/english_baseline_20261116_r1/receipt.json)
- [英文执行审计](../../benchmark/experiments/acmg_multilingual/overall_design/english_baseline_execution_audit_r1.json)
- [双审/仲裁队列](../../benchmark/experiments/acmg_multilingual/overall_design/english_baseline_review_queue_r1.json)
- [Europe PMC DOI 路径探针](../../benchmark/experiments/acmg_multilingual/overall_design/english_baseline_doi_resolution_probe_r1.json) / [DOAJ DOI 路径探针](../../benchmark/experiments/acmg_multilingual/overall_design/english_baseline_doi_doaj_resolution_probe_r1.json)：25 个唯一 DOI 均未返回全文路径；这不是全球英文缺失结论。

### 新增：英文候选语义质量审计

对 220 条英文候选的 Crossref 原始元数据做了离线质量检查。220 条全部来自 Crossref；其中 102 条为 `book-chapter`、53 条为 `dataset`、22 条为 `component`、11 条为 `book`、11 条为 `report`、10 条为 `proceedings-article`，只有 11 条为 `journal-article`。候选标题与对应疾病标签的完整短语匹配为 0，保守词元重叠也为 0；220 条访问状态仍全部是 `no_access`。

这说明冻结的“疾病名 + ORPHA + 全部 HPO 号”序列化直接交给 Crossref 后，至少在当前网关路径上产生了明显的 provider 查询语义错配。它是英文基线 readiness 的新增阻塞证据，不能被解释为英文文献缺失。

- [候选质量审计](../../benchmark/experiments/acmg_multilingual/overall_design/english_baseline_candidate_quality_audit_r1.json)
- [门禁审计](../../benchmark/experiments/acmg_multilingual/overall_design/confirmatory_gate_audit_r1.json)：新增 `provider_query_semantic_mismatch_in_crossref_candidate_set` 阻塞项。

为判断问题是否可由 provider 适配修复，另做了一个 5 题、Europe PMC/Crossref/DOAJ 的诊断侧车。它只使用疾病标签的 provider-native 形式，不写入冻结台账：Crossref 100 条返回项中 70 条标题包含完整疾病标签，Europe PMC 为 31/100，DOAJ 为 33/70；这与冻结序列的 0/220 完整短语匹配形成对照。该侧车支持“适配器语义错配”解释，但不授权主检索，也不改变 D1 查询身份。

- [provider-adapter 质量探针](../../benchmark/experiments/acmg_multilingual/overall_design/provider_adapter_quality_probe_r1/summary.json)
- [provider-adapter 修订提案](../../benchmark/experiments/acmg_multilingual/overall_design/provider_adapter_amendment_proposal_r1.json)：推荐保留 D1 预算和 A2 来源宇宙，仅为 provider 固定疾病标签查询序列化；用户选择前不修改冻结协议。

提案 A 的离线回放已完成：2,000 个冻结问题映射到 10,000 条 provider 调用定义，A2 provider 顺序、20 候选/20 全文上限、零 follow-up、访问失败不作英文阴性等不变量均通过。该回放只生成并列的 proposal manifest，尚未替换冻结 query plan。

- [provider-adapter dry-run manifest](../../benchmark/experiments/acmg_multilingual/overall_design/provider_adapter_dry_run_manifest_r1.json)
- [provider-adapter dry-run receipt](../../benchmark/experiments/acmg_multilingual/overall_design/provider_adapter_dry_run_receipt_r1.json)

当前审计状态为 `not_ready`。220 条候选仍等待两名独立 AI reviewer 和独立仲裁者；因全文访问、原始响应和 provider 覆盖均未满足门禁，不能将这次运行作为英文阴性或确认性分母。

### Provider-native 适配器 readiness 重跑

采用并列的 `a2-provider-native-label-v1` 适配器后，500/500 英文查询完成，2,500 个 provider receipt 和 3,936 条候选处置记录生成；80 篇全文成功提取，较旧基线的 0 篇有所改善。适配器绑定和 provider query 哈希全部通过，但 1,996 条访问记录仍为 `no_access`，未决比例为 96.15%，超过 B2 登记的 10% 上限。原始 HTTP body 仍不可用，双 reviewer/独立仲裁也尚未完成，因此 readiness 继续为 `not_ready`。

- [适配器协议快照](../../benchmark/experiments/acmg_multilingual/overall_design/protocol_snapshot_adapter_r1.json)
- [适配器英文执行收据](../../benchmark/experiments/acmg_multilingual/overall_design/executions/english_baseline_adapter_20261116_r1/receipt.json)
- [适配器执行审计](../../benchmark/experiments/acmg_multilingual/overall_design/english_baseline_adapter_execution_audit_r1.json)

对 80 篇可读全文完成了探索性多维 triage，并对一篇高信息量来源进行双审/仲裁：PMC10968410 报告 4 个 RUNX2 先证者、2 个墨西哥家系、4 个变异、Sanger、家系分离、临床/影像和生信证据。该来源为英文，观察单位保留但所有确认性增量置零，不进入主研究分母。

- [全文 triage](../../benchmark/experiments/acmg_multilingual/overall_design/english_adapter_fulltext_triage_r1.json)
- [探索性 RUNX2 审计汇总](../../benchmark/experiments/acmg_multilingual/candidate_audits/english_adapter_fulltext_20261117/summary_r1.json)

随后进行的 A2 provider recovery probe 显示 Europe PMC、PMC、Crossref、DOAJ 可短暂返回，但 OpenAlex 仍为 429；Crossref recovery 在 4/490 个目标查询后再次限流，得到 60 条重复候选、0 个新的唯一候选。该结果作为访问状态记录，不改变原始基线 ledger。

进一步的无代理直连探针显示 Crossref/OpenAlex/PMC/Europe PMC/DOAJ 均可建立请求；直连恢复仍未产生新的候选（OpenAlex/PMC/DOAJ/Europe PMC 为 0 条，Crossref 4 条查询后再次限流）。因此“共享代理限流”已被识别，但英文基线仍没有可审阅全文，也不能解除 readiness 门。
