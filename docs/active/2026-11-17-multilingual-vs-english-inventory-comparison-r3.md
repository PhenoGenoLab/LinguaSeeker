# 多语种相对英文探索库存对比 R3

**Status:** in-progress  
**Created:** 2026-11-17  
**Completed:**  
**PR:** 未合并

R3 更新英文恢复矩阵到 R5，并继续使用显式 affected-patient/variant-event 字段映射。缺失字段保持未知。

机器可读工件：[inventory comparison R3](../../benchmark/experiments/acmg_multilingual/discovery_20261116/multilingual_vs_english_inventory_comparison_r3.json)。

| 组别 | 候选 | 观察患者单位 | 观察变异事件 | 确认性端点增量 |
|---|---:|---:|---:|---:|
| 非英语多语种 | 33 | 914 | 21 | 全部 0 |
| 英文恢复 | 29 | 70 | 73 | 全部 0 |

非英语库存候选和患者单位仍更多，英文库存观察变异事件更多。两组没有题级配对，R3 仍只是描述性库存比较，不是总体优效检验。
