# 西语 GLUT1 全文病例审计 R1

**Status:** in-progress  
**Created:** 2026-11-17  
**Completed:**  
**PR:** 未合并

## 来源与检索复用

候选来自 provider-native R2 扩展的 `q_0233` 西语筛选，Crossref DOI 为 `10.22517/25395203.25778`。出版方提供原始 PDF；通过本地 `lit-acquisition` 固定 commit `14e3dbfd07f1a5e7fbc1257c7f9fea37e29dca40` 的安全下载入口恢复，保存 PDF、`pdftotext` 文本和访问收据。相同检索器可从 GitHub `https://github.com/lanshi17/lit-acquisition` 取得。

## 原文多维证据

- 1 名 25 岁男性；7 个月起出现癫痫，伴发育倒退、运动障碍和多次骨科手术，原文报告随访中的神经系统和骨骼表现。
- 三人外显子组发现 `SLC2A1 c.972+1G>T` 杂合 de novo 致病变异；父母均未携带该变异。原文另记载 `ATP7B c.4301C>T (p.Thr1434Met)`，临床意义冲突，不能和 GLUT1 致病变异混为一谈。
- 检测包括三人外显子组、核型、氨基酸色谱、ATP7B 缺失/重复分析和代谢筛查；MRI 描述岛叶后部、额部体积和小脑蚓部异常。
- 治疗/照护包括丙戊酸、左乙拉西坦和神经发育治疗；文章讨论并强调生酮饮食作为 GLUT1-DS 的治疗方向，但本病例原文中不应把讨论段落误写成已实施治疗。

## 英文对应与确认性边界

PDF同篇含英文摘要，因此存在同记录英文暴露；没有建立独立英文全文或同一患者身份对应。变异保留源文 HGVS，未独立补充转录本标准化。该条记录是探索性人工抽取，尚未完成两名独立 AI reviewer 与独立仲裁；确认性文章、患者、家系、变异和语言独有事实增量均为 0，不把该西语病例写成已证实的多语种相对英文增量。

工件：

- [候选审计包](../../benchmark/experiments/acmg_multilingual/candidate_audits/multilingual_round2_open_fulltexts_20261117/glut1_spanish_doi_10.22517_25395203.25778/)
- [西语 R2 矩阵](../../benchmark/experiments/acmg_multilingual/discovery_20261116/spanish_recovered_case_matrix_r2.json)
