# 多语种 R2 开放全文恢复 R3

**Status:** in-progress  
**Created:** 2026-11-17  
**Completed:**  
**PR:** 未合并

继续复用 `lit-acquisition` 对 `q_0067` 葡语候选执行两条有界机构仓储路线：

| 候选 | 访问结果 | 处理边界 |
|---|---|---|
| `LAMA2` 肌营养不良学位论文 `10.11606/t.5.2023.tde-26052023-153344` | 访问未决 | 不编码患者/变异，不作英文阴性 |
| 慢性肉芽肿病学位论文 `10.11606/d.42.2014.tde-11072014-130927` | 访问未决 | 不编码患者/变异，不作英文阴性 |

当前恢复汇总包含 9 条路线：2 条原始全文、1 条 metadata-only、6 条访问未决。新增两条均为 USP 机构 PDF 路线；不能因为 Crossref 提供直链就推断正文可读。机器可读工件：[恢复汇总](../../benchmark/experiments/acmg_multilingual/candidate_audits/multilingual_round2_open_fulltexts_20261117/summary.json)。
