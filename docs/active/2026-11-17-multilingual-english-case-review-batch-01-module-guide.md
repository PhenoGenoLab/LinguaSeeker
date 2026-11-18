# 首批多语种/英文病例 AI 审阅脚本指南

**Status:** in-progress  
**Created:** 2026-11-17  
**Completed:**   
**PR:** 未合并

目标脚本：[review_multilingual_english_case_batch_01_ai_r1.py](../../scripts/review_multilingual_english_case_batch_01_ai_r1.py)。它读取冻结的 `multilingual_english_case_review_batch_01_r1.json`，对绑定的原文提取文本执行两次独立 reviewer 调用；两次均得到可解析 JSON 后才调用独立仲裁者。

## 快速运行

```bash
uv run --project . python scripts/review_multilingual_english_case_batch_01_ai_r1.py \
  --max-candidates 10 --delay-seconds 5
```

凭证通过 `REASONING_LLM_API_KEY` 或已有 `LS_API_KEY` 注入。端点和模型可通过 `REASONING_LLM_BASE_URL`、`REASONING_LLM_MODEL`、`REVIEWER_MODEL_A`、`REVIEWER_MODEL_B`、`ARBITRATOR_MODEL` 覆盖；脚本不会把凭证写入工件。

## 数据流和边界

```text
冻结批次 JSON
    -> 读取唯一 .txt 原文提取物（与 XML 哈希绑定）
    -> reviewer_a / reviewer_b 顺序调用
    -> 两者均为 HTTP 200 + JSON 时调用独立仲裁者
    -> 每候选 ai_review_r1.json + batch_summary.json
```

脚本只把原文提取物放入 prompt，禁止网页搜索、数据库推断和翻译替代。所有失败响应保留 HTTP 状态、错误体和响应哈希；失败不会被写成阴性证据。每条输出的 `confirmed_increment` 固定为全零，`confirmatory_admission=false`。

## 输出与审计

输出目录为 `benchmark/experiments/acmg_multilingual/overall_design/candidate_audits/multilingual_english_case_review_batch_01_r1/`。`batch_summary.json` 记录批次 ID、模型、端点、成功/未完成数量；子目录收据记录源文件路径、源文哈希、prompt 哈希和原始 reviewer 响应。

当前批次的审计结果见 [AI 尝试 R1](2026-11-17-multilingual-english-case-review-batch-01-ai-attempt-r1.md)。

## 验证

```bash
uv run --project . ruff check scripts/review_multilingual_english_case_batch_01_ai_r1.py
uv run --project . pytest tests/overall_design
```

重新运行前应先确认凭证有效；401/429 只能产生新的失败收据，不能提升 readiness。检索器沿用本地 `lit-acquisition` 固定 commit `14e3dbfd07f1a5e7fbc1257c7f9fea37e29dca40`，本脚本本身不重新发起确认性检索。
