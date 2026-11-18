# 英文 Europe PMC 超时恢复 R1

**Status:** in-progress  
**Created:** 2026-11-17  
**Completed:**  
**PR:** 未合并

在不修改英文 500 题原始账本的前提下，对既有 Europe PMC XML 恢复中因超时/连接错误未决的 PMCID 做了低并发、30 秒超时重试。六批 sidecar 覆盖全部 509 个超时/连接错误候选，按 PMCID 去重后恢复 448 个 PMCID、581 个 occurrence；与先前恢复结果合并后，未决比例从 69.46% 降至 41.47%。

机器可读收据：

- [timeout retry R1](../../benchmark/experiments/acmg_multilingual/overall_design/executions/english_adapter_europepmc_timeout_retry_20261117_r1/receipt.json)
- [timeout retry R2](../../benchmark/experiments/acmg_multilingual/overall_design/executions/english_adapter_europepmc_timeout_retry_20261117_r2/receipt.json)
- [timeout retry R3](../../benchmark/experiments/acmg_multilingual/overall_design/executions/english_adapter_europepmc_timeout_retry_20261117_r3/receipt.json)
- [timeout retry R4](../../benchmark/experiments/acmg_multilingual/overall_design/executions/english_adapter_europepmc_timeout_retry_20261117_r4/receipt.json)
- [timeout retry R5](../../benchmark/experiments/acmg_multilingual/overall_design/executions/english_adapter_europepmc_timeout_retry_20261117_r5/receipt.json)
- [timeout retry R6](../../benchmark/experiments/acmg_multilingual/overall_design/executions/english_adapter_europepmc_timeout_retry_20261117_r6/receipt.json)
- [merged recovery audit R2](../../benchmark/experiments/acmg_multilingual/overall_design/english_adapter_recovery_audit_r2.json)

这只是访问与身份恢复结果。剩余 861 个 access occurrence 仍为未决，不得编码为英文阴性；恢复文本还需要文本抽取、两名独立 reviewer 和仲裁。
