# 多语种相对英文探索库存对比 R1

**Status:** in-progress  
**Created:** 2026-11-17  
**Completed:**  
**PR:** 未合并

## 输入

- 多语种 R13：[统一矩阵](../../benchmark/experiments/acmg_multilingual/discovery_20261116/multilingual_multidimensional_case_matrix_r13_unified.json)，SHA-256 `49260eeaaea04d3ac7531c40a6ba73452104f2e73a33067447f9f5ba143e1dbc`
- 英文恢复 R3：[英文矩阵](../../benchmark/experiments/acmg_multilingual/overall_design/english_recovery_multidimensional_case_matrix_r3_unified.json)，SHA-256 `4185e82851a10ea6ac246a811710d9dce3cc061ae63857e36e0d63a7e301142b`
- 生成脚本：[build_multilingual_vs_english_inventory_comparison_r1.py](../../scripts/build_multilingual_vs_english_inventory_comparison_r1.py)
- 输出工件：[对比 JSON](../../benchmark/experiments/acmg_multilingual/discovery_20261116/multilingual_vs_english_inventory_comparison_r1.json)

## 描述性结果

| 探索库存 | 候选数 | 观察患者单位 | 观察家系单位 | 观察变异事件 | 临床覆盖 | 分子变异覆盖 | 遗传检测覆盖 | 实验室覆盖 | 治疗/随访覆盖 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 非英语多语种（中/西/葡） | 33 | 914 | 11 | 21 | 33/33 (100%) | 29/33 (87.9%) | 30/33 (90.9%) | 25/33 (75.8%) | 28/33 (84.8%) |
| 英文恢复 R3 | 19 | 13 | 11 | 44 | 19/19 (100%) | 19/19 (100%) | 19/19 (100%) | 8/19 (42.1%) | 9/19 (47.4%) |

非英语库存比本次英文恢复库存多 14 条候选和 901 个观察患者单位，并覆盖更多实验室、治疗/随访和生殖维度；但英文库存的观察变异事件更多（44 对 21），说明“证据更多”必须先定义证据单位，不能把候选数或患者数直接等同变异发现能力。

## 边界

两组是不同来源、不同访问恢复路径的便利探索库存，候选疾病、队列大小、全文可得性和历史矩阵契约不相同，候选 ID 没有重叠。该对比不是配对检索估计、总体优效检验或因果语言效应；所有确认性文章、患者、家系、变异和语言独有事实增量仍为 0。

要证明总体上多语种一定增加更多证据，必须在冻结的 A2/B2/C3/D1 确认性框架中预先定义证据单位和去重规则，并完成英文 readiness、全文访问、双审、独立仲裁及缺失机制处理。
