# 多语种 R13 审阅队列 R1

**Status:** in-progress  
**Created:** 2026-11-17  
**Completed:**  
**PR:** 未合并

为 R13 统一矩阵建立稳定审阅队列，绑定矩阵 SHA-256、来源语言、访问状态、观察单位、维度和确认性零端点。队列只准备审阅拓扑，不改变候选处置或确认性分母。

| 状态 | 数量 | 含义 |
|---|---:|---|
| `already_reviewed_adjudicated` | 3 | 既有双审/仲裁记录可回链 |
| `pending_ai_dual_review` | 9 | 有原始全文，但 AI 双审尚未完成 |
| `not_reviewable_access_unresolved` | 2 | 摘要-only/访问未决，不能启动正文审阅 |
| `pending_source_review` | 22 | 历史探索矩阵行需先回链来源审计，再决定审阅路径 |

机器可读工件：[R13 审阅队列](../../benchmark/experiments/acmg_multilingual/discovery_20261116/multilingual_r13_review_queue_r1.json)。当前 reasoning 服务对新增候选返回 401/429，因此队列仍保持 pending；所有行 `confirmatory_admission=false`。
