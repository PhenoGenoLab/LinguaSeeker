# 英文恢复病例 AI 双审与仲裁 R1

**Status:** in-progress  
**Created:** 2026-11-17  
**Completed:**  
**PR:** 未合并

## 审阅范围

对英文恢复病例矩阵中的 11 条候选尝试执行两名独立 reasoning reviewer 和独立仲裁者。审阅提示只包含已哈希的原始 XML/提取文本事实，不允许外部检索或把数据库命中当作患者对应。

## 访问结果

- 初始配置 `gpt-5` 返回 HTTP 401；
- 按项目既有 endpoint/模型组合重试：`gpt-5-mini`、`deepseek-v3.1`，仲裁 `Qwen/Qwen3-32B`；
- 该组合全部返回 HTTP 429，即使改为串行调用并进行有限退避，仍没有形成有效 reviewer JSON；
- 11/11 候选状态为 `review_incomplete`，仲裁调用数为 0。

机器可读收据位于：

- [AI 审阅批次摘要](../../benchmark/experiments/acmg_multilingual/overall_design/candidate_audits/english_recovery_cases_r1/batch_summary.json)
- [AI 审阅脚本](../../scripts/review_english_recovery_cases_ai_r1.py)

每个候选目录保留模型、HTTP 状态、提示哈希和空响应哈希；所有 `confirmed_increment` 仍为 0，`confirmatory_admission=false`。HTTP 401/429 只说明审阅服务不可用，不能作为病例证据阴性或英文阴性。

## 当前解释

11 条病例的原文人工抽取矩阵仍可作为探索性多维证据库存；它们尚未通过 AI 双审和独立仲裁，不进入确认性分母。待 reasoning 服务恢复后，应从同一 source hash 重新运行，不修改原文提取或病例事实。
