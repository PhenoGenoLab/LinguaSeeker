# 多语种相对英文单位敏感性分析 R1

**Status:** in-progress  
**Created:** 2026-11-17  
**Completed:**  
**PR:** 未合并

对 R13 非英语库存与英文 R6 库存，按候选数、患者单位、家系单位、变异事件和多维覆盖做方向敏感性分析。

机器可读工件：[sensitivity R1](../../benchmark/experiments/acmg_multilingual/discovery_20261116/multilingual_vs_english_sensitivity_r1.json)。

结果显示方向不一致：

- 非英语更高：观察患者单位、影像/病理、实验室、家系、生殖、治疗/随访覆盖。
- 英文更高：候选数、观察变异事件，以及临床/分子/遗传检测覆盖计数。

因此当前库存不存在单方向总体支配，不能证明“多语种总体一定比英文增加更多证据”。这是便利探索库存的敏感性描述，不是确认性效应估计。
