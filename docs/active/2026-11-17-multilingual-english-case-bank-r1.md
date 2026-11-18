# 多语种/英文统一病例库 R1

**Status:** in-progress  
**Created:** 2026-11-17  
**Completed:**  
**PR:** 未合并

将多语种 R13 与英文 R6 探索矩阵合并为统一病例库，保留来源臂、语言、原始矩阵路径、观察单位、维度、事实摘录和哈希。共 70 条候选：非英语 36 条、英语 34 条。

机器可读工件：[unified case bank R1](../../benchmark/experiments/acmg_multilingual/discovery_20261116/multilingual_english_case_bank_r1.json)。

观察单位汇总：患者 1,003、家系 39、变异事件 114。缺失字段保留为 `null`，所有确认性端点增量和确认性纳入均为 0。

这是审阅工作台，不是合并确认性分母，也不支持多语种总体优效推断。
