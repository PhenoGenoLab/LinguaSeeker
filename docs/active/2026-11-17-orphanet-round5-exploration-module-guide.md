# Orphadata R5 探索脚本指南

**Status:** in-progress  
**Created:** 2026-11-17  
**Completed:**   
**PR:** 未合并

本轮由四个脚本组成：

- `run_orphanet_exploratory_multilingual_round5_r1.py`：排除历史题目并保存 40 条 Europe PMC 原始响应。
- `rank_orphanet_round5_case_candidates_r1.py`：按标题病例信号、开放全文和 PMCID 可得性生成 20 条有界候选。
- `recover_orphanet_round5_fulltexts_r1.py`：回收最多 20 条 `fullTextXML`，将 PMID-only 失败保留为未决。
- `extract_orphanet_round5_fulltext_r1.py` 与 `triage_orphanet_round5_fulltext_r1.py`：从原始 JATS 提取文本并做规则 triage。
- `build_orphanet_round5_multidimensional_matrix_r1.py`：为 14 条高价值全文写入原文引文、观察单位和维度；不产生确认性增量。

运行示例：

```bash
uv run --project . python scripts/run_orphanet_exploratory_multilingual_round5_r1.py --seed 20261120 --count 10
uv run --project . python scripts/rank_orphanet_round5_case_candidates_r1.py --limit 20
uv run --project . python scripts/recover_orphanet_round5_fulltexts_r1.py --limit 20
uv run --project . python scripts/extract_orphanet_round5_fulltext_r1.py
uv run --project . python scripts/triage_orphanet_round5_fulltext_r1.py
uv run --project . python scripts/build_orphanet_round5_multidimensional_matrix_r1.py
```

脚本固定 `trust_env=False` 并使用 `LIT_PROXY`（默认 `http://127.0.0.1:7890`），避免根环境把 SOCKS 代理误传给未安装 `socksio` 的 `httpx`。所有外部响应保留路径、HTTP 状态和 SHA-256；访问错误不编码为证据阴性。

验证：

```bash
uv run --project . ruff check scripts/run_orphanet_exploratory_multilingual_round5_r1.py scripts/rank_orphanet_round5_case_candidates_r1.py scripts/recover_orphanet_round5_fulltexts_r1.py scripts/extract_orphanet_round5_fulltext_r1.py scripts/triage_orphanet_round5_fulltext_r1.py scripts/build_orphanet_round5_multidimensional_matrix_r1.py
```
