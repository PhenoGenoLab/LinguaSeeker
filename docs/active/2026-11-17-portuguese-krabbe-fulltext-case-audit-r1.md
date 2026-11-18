# 葡语 Krabbe 历史全文病例审计 R1

**Status:** in-progress  
**Created:** 2026-11-17  
**Completed:**  
**PR:** 未合并

## 来源与访问

来源为葡语/葡法摘要的历史 SciELO 文章 `Doença de Krabbe (Leucodistrofia de células globóides)`，DOI `10.1590/S0074-02761972000300006`。旧 PDF 路线在 SciELO 返回 502；改用当前 SciELO 文章格式 PDF `https://www.scielo.br/j/mioc/a/ByHtvcFBCR5Fy94qRJ5jDrv/?format=pdf&lang=pt`，通过 `lit-acquisition` 安全抓取恢复原始 PDF。PDF 为扫描文，使用本地 OCR，并保留 OCR 文本哈希。

## 原文证据与分子边界

- 1 名 3 岁女童，2 岁半起出现冷漠、易怒和进行性言语困难，随后四肢瘫痪、失明、反射亢进并在数月后死亡。
- 家族史记载 1 名兄弟在相近年龄出现相似疾病并死亡，另有 4 名兄弟幼年死亡；这是家系上下文，不是患者级变异。
- 尸检病理显示脑白质完全脱髓鞘、皮质萎缩、PAS 阳性球状细胞、Sudan 染色和银染等多维病理证据。
- 文章讨论半乳糖脑苷脂酶缺陷这一疾病机制，但没有患者级遗传检测、变异、HGVS 或测序结果，因此 `variant_event=0`、`molecular_variant=false`。

## 英文对应与确认性边界

未建立独立英文全文或患者身份对应；原始文章不是同记录英文摘要暴露层。OCR 人工抽取尚未完成 AI 双审和独立仲裁，所有确认性端点均为 0。

工件：

- [候选审计包](../../benchmark/experiments/acmg_multilingual/candidate_audits/multilingual_round2_open_fulltexts_20261117/krabbe_portuguese_doi_10.1590_s0074_02761972000300006/)
- [葡语 R5 矩阵](../../benchmark/experiments/acmg_multilingual/discovery_20261116/portuguese_recovered_case_matrix_r5.json)
