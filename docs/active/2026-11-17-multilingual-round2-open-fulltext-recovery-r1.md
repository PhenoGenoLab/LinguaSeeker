# 多语种 R2 开放全文恢复 R1

**Status:** in-progress  
**Created:** 2026-11-17  
**Completed:**  
**PR:** 未合并

从 provider-native R2 扩展的元数据筛选中抽取 4 条有遗传变异线索的候选，使用本地 `lit-acquisition` 的安全下载/SSRF 校验和原始哈希收据做有界恢复：

| 候选 | 访问结果 | 处理边界 |
|---|---|---|
| 西语 GLUT1 DOI `10.22517/25395203.25778` | 原始 PDF 恢复 | 已做人工原文抽取，进入西语 R2/统一 R9；确认性端点为0 |
| 西语 ASXL3 DOI `10.1016/j.nrl.2017.01.022` | Elsevier XML 仅返回 `coredata` 元数据 | 重新标记为 `metadata_only_not_fulltext`，不抽取病例证据 |
| 葡语听力学位论文 DOI `10.11606/d.41.2020.tde-05042021-154617` | 访问未决 | 不编码患者/变异证据，不作英文阴性 |
| 西语 BBS/ALMS 学位论文 DOI `10.35869/11093/746` | 访问未决（仓储 TLS 路线失败） | 不编码患者/变异证据，不作英文阴性 |

机器可读工件：[恢复汇总](../../benchmark/experiments/acmg_multilingual/candidate_audits/multilingual_round2_open_fulltexts_20261117/summary.json)。ASXL3 的 XML 原始字节仍保留用于审计，但只有元数据包，不满足全文证据门槛。所有确认性端点均为 0。
