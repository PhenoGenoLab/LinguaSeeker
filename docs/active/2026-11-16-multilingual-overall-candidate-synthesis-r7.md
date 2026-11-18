# 多语种遗传变异候选综合 R7

**Status:** in-progress  
**Created:** 2026-11-16  
**Completed:** —  
**PR:** N/A（探索性研究）

本轮从访问未决的中文候选中通过 NCBI PMC `?report=xml` 替代路线恢复两篇全文：复杂三向易位家系和青岛 FAOD 新生儿队列。机器可读汇总见 [discovery_summary_r4.json](../../benchmark/experiments/acmg_multilingual/discovery_20261116/discovery_summary_r4.json)。

## 新增来源

| 候选 | 多维证据 | 英文对应边界 | 仲裁结论 |
|---|---|---|---|
| `46,XX,t(1;6;14)` 中文病例 | 31 岁女性 8 年不孕、PCOS 与内分泌资料；高分辨核型三向易位；母亲同核型，父亲/妹妹正常；母亲有两次流产史；无 FISH/CMA 断点验证 | 同文英文摘要覆盖核心；精确英文易位查询命中无关 chordoma 文献；广义英文不孕/易位结果均为其他病例 | 1 个细胞遗传结构事件；文章/患者/家系/变异/语言独有事实增量均 0 |
| 青岛 FAOD 中文队列 | 562,225 名新生儿筛查、42 例 FAOD、6 亚型；37 例基因检测；SLC22A5 c.1400C>G 热点；ACADM/ACADVL/ACADS/ETFA/B/ETFDH 等分型；最长 9 年 4 个月随访，死亡、横纹肌溶解、发育倒退和代谢危象 | 同文英文摘要覆盖核心；英文 c.1400C>G 查询返回其他 SLC22A5 报告；ClinVar UID 25423 已知 | 42 名患者、1 个队列；不计语言独有患者/变异/事实增量 |

## 边界

- `?report=xml` 是访问路线，原文仍是中文；同一记录英文摘要不构成独立英文来源。
- FAOD 队列中的 42 名患者没有逐一独立英文身份，因此不把队列人数拆成英文缺失患者。
- 三向易位为细胞遗传结构事件，不补造断点级 HGVS；文章自己也说明尚未做 FISH/CMA 分子验证。
- 目前累计 13 条探索性候选；确认性文章、患者、家系、变异和语言独有事实增量仍为 0。

## 工件

- [discovery_summary_r4.json](../../benchmark/experiments/acmg_multilingual/discovery_20261116/discovery_summary_r4.json)
- [recovered case batch](../../benchmark/experiments/acmg_multilingual/discovery_20261116/source_packages/new_access_recovered_20261116_r1)

这些新增来源扩大了多维证据覆盖，但仍不能支持“多语种总体必然增加更多证据”的全称结论。
