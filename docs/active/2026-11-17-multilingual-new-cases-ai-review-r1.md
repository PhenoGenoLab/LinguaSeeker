# 新增多语种病例 AI 双审与仲裁 R1

**Status:** in-progress  
**Created:** 2026-11-17  
**Completed:**  
**PR:** 未合并

对 R13 最近新增的 3 条原始全文候选执行有界、串行的两名 reviewer + 独立仲裁调用：西语 p47-phox CGD、葡语 MLD 双兄弟和葡语 Krabbe。

| 候选 | Reviewer A | Reviewer B | 仲裁 | 状态 |
|---|---:|---:|---:|---|
| p47-phox CGD | HTTP 401 | HTTP 401 | 未启动 | `review_incomplete` |
| 葡语 MLD 双兄弟 | HTTP 401 | HTTP 401 | 未启动 | `review_incomplete` |
| 葡语 Krabbe | HTTP 401 | HTTP 429 | 未启动 | `review_incomplete` |

每条候选的 prompt 哈希、模型、HTTP 状态、空响应哈希和 `confirmatory_admission=false` 已保存于候选包的 `ai_review_r1.json`；批次汇总位于 [batch_summary.json](../../benchmark/experiments/acmg_multilingual/candidate_audits/multilingual_round2_open_fulltexts_20261117/multilingual_new_cases_ai_review_r1/batch_summary.json)。HTTP 401/429 只表示审阅服务不可用，不能作为证据阴性；三条记录仍是人工探索性抽取，确认性端点均为 0。
