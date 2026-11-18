# 多语种相对英文探索库存对比 R2

**Status:** in-progress  
**Created:** 2026-11-17  
**Completed:**  
**PR:** 未合并

R2 将英文恢复库存更新为 24 条 R4 候选，并扩展了明确暴露的 `patient_affected`、`diagnosed_patient`、`variant_event_index` 和 `variant_event_context` 字段映射；缺失字段仍保持未知。

机器可读工件：[inventory comparison R2](../../benchmark/experiments/acmg_multilingual/discovery_20261116/multilingual_vs_english_inventory_comparison_r2.json)。

| 组别 | 候选 | 观察患者单位 | 观察变异事件 | 确认性端点增量 |
|---|---:|---:|---:|---:|
| 非英语多语种 | 33 | 914 | 21 | 全部 0 |
| 英文恢复 | 24 | 65 | 61 | 全部 0 |

非英语库存候选和观察患者单位较多，英文库存观察变异事件较多。两组来自不同恢复路径、没有题级配对，因此 R2 仍是描述性探索，不是总体优效检验。
