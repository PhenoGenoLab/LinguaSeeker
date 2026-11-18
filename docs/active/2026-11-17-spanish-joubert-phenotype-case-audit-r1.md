# 西语 Joubert 谱系表型病例审计 R1

**Status:** in-progress  
**Created:** 2026-11-17  
**Completed:**  
**PR:** 未合并

## 来源与访问

候选来自 `q_0488` 西语 provider-native 收据，DOI 为 `10.66827/ucmb.2026.v3.n1.015`。通过出版方 PDF 直链恢复原始西语全文，并保存 PDF、文本提取、访问收据和 Crossref provider 响应的哈希。检索与下载继续复用本地/GitHub `lit-acquisition` 固定 commit `14e3dbfd07f1a5e7fbc1257c7f9fea37e29dca40`。

## 原文证据与分子边界

- 1 名新生儿，出生后出现全身发绀、明显低张力、枕部脑脊膜膨出/出血；影像记录胼胝体缺如、小脑蚓部缺失、脑回异常和复杂中线畸形。
- 家族信息包括父母二级近亲婚配、6 名既往存活子女中 2 名有相似严重畸形且分别在 1 个月和 6 个月死亡；这是家系/遗传风险上下文，不是患者级变异结果。
- 眼部、心血管、肝胆和神经系统均有异常，患者经历新生儿重症监护、机械通气、血流动力学支持和后续慢性照护。
- 文章明确写出未能进行遗传研究，父母因意识形态原因拒绝检测；文中提出 `CEP290`、`TMEM67`、`CC2D2A`、`AHI1`、`KIAA0586` 等候选基因和可能的双等位变异只是推测/检测建议，不能编码为已观察变异。

因此本记录的 `variant_event=0`、`molecular_variant=false`、`genetic_testing=false`。它用于展示多维临床和家系证据的访问边界，不作为“多语种发现了新变异”的证据。

## 英文对应与确认性边界

文章含英文摘要，但没有独立英文全文或患者身份对应。AI 双审和独立仲裁尚未完成，确认性文章、患者、家系、变异和语言独有事实增量均为 0；访问到原文不等于通过确认性准入。

工件：

- [候选审计包](../../benchmark/experiments/acmg_multilingual/candidate_audits/multilingual_round2_open_fulltexts_20261117/joubert_spanish_doi_10.66827_ucmb.2026.v3.n1.015/)
- [西语 R3 矩阵](../../benchmark/experiments/acmg_multilingual/discovery_20261116/spanish_recovered_case_matrix_r3.json)
