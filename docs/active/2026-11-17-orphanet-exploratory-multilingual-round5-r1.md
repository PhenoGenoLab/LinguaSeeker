# Orphadata 多语种探索批次 R5

**Status:** in-progress  
**Created:** 2026-11-17  
**Completed:**   
**PR:** 未合并

本轮从 Orphadata 帧中排除 R3/R4 已用题目，固定种子抽取 10 个新问题，按英文、西语、葡语和中文回退模板向 Europe PMC 发出 40 条筛选查询。所有响应原字节保存，筛选结果不进入确认性分母。

机器可读工件位于：[round5 candidate audit](../../benchmark/experiments/acmg_multilingual/candidate_audits/orphanet_exploratory_round5_20261117/)。

| 阶段 | 结果 |
|---|---:|
| 新问题 | 10 |
| 多语种查询 | 40 |
| HTTP 200 响应 | 35 |
| 命中查询 | 13 |
| 去重候选元数据 | 177 |
| 标题筛选池 | 146 |
| 冻结全文候选 | 20 |
| 原始 JATS 全文 | 16 |
| PMID-only 未决 | 4 |
| 原文锚定多维矩阵 | 14 条、72 条事实引文 |

14 条全文探索矩阵的观察单位为患者 58、家系 24、变异事件 28；这些是原文抽取的探索性观察，不是确认性端点。所有 72/72 引文可在提取原文中定位，未知语言、英文对应和未审阅字段保持 `null`。

4 条 PMID-only 路线返回 500，保留为访问未决；不能据此写成英文阴性。查询语言也不等同于论文正文语言，因此矩阵的 `source_language` 暂保持未知。

检索模板沿用本地/GitHub `lit-acquisition` 方案的 provider 覆盖和来源留痕原则；本轮仍不授权确认性检索，`retrieval_authorized=false`。
