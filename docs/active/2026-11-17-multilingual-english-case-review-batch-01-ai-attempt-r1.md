# 多语种/英文统一病例审阅批次 01：AI 尝试 R1

**Status:** in-progress  
**Created:** 2026-11-17  
**Completed:**   
**PR:** 未合并

对冻结的 10 条审阅输入执行顺序双审。每条先调用 reviewer A/B；只有两者都返回 HTTP 200 且 JSON 可解析时才调用独立仲裁者。原始响应、HTTP 状态、错误体和哈希均保存在审阅收据中。

机器可读汇总：[batch_summary.json](../../benchmark/experiments/acmg_multilingual/overall_design/candidate_audits/multilingual_english_case_review_batch_01_r1/batch_summary.json)。逐条收据位于同目录下各候选子目录的 `ai_review_r1.json`。

| 指标 | 结果 |
|---|---:|
| 尝试候选 | 10 |
| 两名 reviewer 均成功 | 0 |
| 成功仲裁 | 0 |
| `review_incomplete` | 10 |
| 确认性增量 | 全部保持 0 |

失败响应以 401 `Invalid token` 为主，并出现 429（无效 token 重试过多）和连接断开。它们只说明审阅服务没有提供可用结果，不能编码成英文阴性、病例排除或确认性无增量。`retrieval_authorized=false` 和 `confirmatory_admission=false` 保持不变。
