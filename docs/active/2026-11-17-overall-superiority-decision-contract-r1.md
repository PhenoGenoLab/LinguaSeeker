# 多语种总体优效判定合同 R1

**Status:** in-progress  
**Created:** 2026-11-17  
**Completed:**  
**PR:** 未合并

将“证明多语种总体增加更多证据”写成逐项可验收合同。主张定义为：在冻结的 500 个问题上，多语种臂相对于英文臂，每个问题产生的独立、去重、源文锚定的非英语独有事实单位均值超过 δ=0.25。

机器可读合同：[overall superiority decision contract R1](../../benchmark/experiments/acmg_multilingual/overall_design/overall_superiority_decision_contract_r1.json)。

必须同时满足：

1. 题框、同一 A2 来源宇宙、D1 预算和时间截点在检索前冻结。
2. 每个事实单位都绑定原文、引文、问题、去重身份，并通过两名独立 reviewer 和仲裁。
3. 英文对应检索完整；未决访问不得编码为英文阴性。
4. 未决比例满足 B2，并执行预注册 MNAR 敏感性界限。
5. C3 序贯分析中，主估计量的单侧调整置信下限超过 δ=0.25。
6. 患者、家系、变异和维度等次级指标不能替代主估计量。

当前合同结论：`overall_superiority_proven=false`。当前探索库存的指标方向相反，且英文恢复未决比例、双审/仲裁和最终 reseal 均未通过。
