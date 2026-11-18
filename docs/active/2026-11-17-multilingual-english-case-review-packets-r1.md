# 多语种/英文统一病例审阅包 R1

**Status:** in-progress  
**Created:** 2026-11-17  
**Completed:**  
**PR:** 未合并

为统一队列 70 条候选生成源绑定审阅包。每包保存源文件路径、字节数、SHA-256、先前观察单位和冻结审阅合同；56 条包当前能直接绑定源文件，5 条还带有历史审计文件。其余记录保留待来源审阅状态，不补猜为阴性。

机器可读工件：[review packets R1](../../benchmark/experiments/acmg_multilingual/discovery_20261116/multilingual_english_case_review_packets_r1.json)。审阅包不生成 reviewer 结论，不修改确认性端点。
