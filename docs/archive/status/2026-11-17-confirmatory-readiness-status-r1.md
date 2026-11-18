# 确认性准入状态 R1

**Status:** in-progress  
**Created:** 2026-11-17  
**Completed:**  
**PR:** 未合并

## 当前结论

探索性多语种库存和 R13 对比已经物化，但确认性检索仍未授权。机器可读状态：[confirmatory_readiness_status_r1.json](../../benchmark/experiments/acmg_multilingual/overall_design/confirmatory_readiness_status_r1.json)。

| 门槛 | 状态 | 证据 |
|---|---|---|
| 离线确认性计划/模板校验 | 通过 | `confirmatory_retrieval_plan_validation_r1.json` |
| 英文 500 题执行完成 | 通过 | `english_baseline_adapter_execution_audit_r1.json` |
| 英文 B2 未决比例 ≤10% | 未通过 | 基线 96.15%；恢复 sidecar 后 69.46% |
| 原始 HTTP payload 完整保留 | 未通过 | reusable gateway 未暴露原始 body |
| 两名独立 reviewer + 仲裁 | 未完成 | review queue 仍为 pending |
| 最终 protocol reseal | 未完成 | 需在上述门槛闭合后执行 |

## 探索性库存

R13 统一矩阵包含 36 条候选；非英语多语种库存与英文恢复 R3 的直接对比已单独保存为描述性工件。该对比明确显示：非英语候选和患者单位更多，但英文观察变异事件更多，因此不能用单一指标支持多语种总体优效。

## 解释边界

访问失败、摘要-only、metadata-only 和 OCR-only 状态没有被编码为英文阴性。R13 的病例和 R13 对比不进入确认性分母；在英文 B2、原始响应、双审、仲裁和 protocol reseal 完成前，不得启动确认性多语种检索或宣称总体必然增加更多证据。

## Current metrics

- English adapter access records: 2,076; initial unresolved fraction 96.15%.
- Recovery sidecar unresolved fraction: 69.46%, still above B2 10%.
- Exploratory R13: 36 candidates; non-English inventory 33, English recovery inventory 19.
- All confirmatory endpoint increments remain zero.
