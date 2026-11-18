# 多语种 R13 审阅队列 R2

**Status:** in-progress  
**Created:** 2026-11-17  
**Completed:**  
**PR:** 未合并

R2 将 R13 中 22 条 `pending_source_review` 历史行按 `candidate_id` 绑定到 R5 不可变矩阵快照。22/22 行匹配成功，并保存 R5 路径和 SHA-256；这一步只补来源可追溯性，不执行原文审阅、AI 双审、仲裁或确认性纳入。

机器可读工件：[R13 审阅队列 R2](../../benchmark/experiments/acmg_multilingual/discovery_20261116/multilingual_r13_review_queue_r2.json)。R5 SHA-256 为 `6445b16086b9fdaa6ca3c2f3647fb6db416b953e7905959e63301020cd1a5dcf`。

| 状态 | 数量 | 来源状态 |
|---|---:|---|
| `already_reviewed_adjudicated` | 3 | 已有双审/仲裁记录 |
| `pending_ai_dual_review` | 9 | 有全文，等待 AI 双审 |
| `not_reviewable_access_unresolved` | 2 | 访问未决，暂不能启动正文审阅 |
| `pending_source_review` | 22 | 已绑定 R5 快照，仍等待来源审阅 |

所有行仍为 `confirmatory_admission=false`。本次来源绑定不改变 R13 观察证据、确认性端点或准入门槛。
