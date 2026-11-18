# 葡语 ROR2 Robinow 综合征学位论文病例审计 R1

**Status:** in-progress  
**Created:** 2026-11-17  
**Completed:**  
**PR:** 未合并

## 来源与可复用检索入口

来源是巴西利亚大学机构仓储中的葡语学位论文 `Pesquisa de Mutações no Gene ROR2 em Pacientes com a Forma Recessiva da Síndrome de Robinow`，DOI/仓储标识为 `10.26512/2015.07.D.20074`。原始 PDF、仓储页面、响应 headers 和本地文本提取均已保存；PDF SHA-256 为 `b5c15ecbc66ae79d8ae61a496de215417293d5314427ea1570153cb7ec11fd42`。

病例检索方案沿用本地 `lit-acquisition` checkout `/data/yangzs/Projects/01_Platform/05_lit-acquisition`，对应 GitHub `https://github.com/lanshi17/lit-acquisition`，固定 commit `14e3dbfd07f1a5e7fbc1257c7f9fea37e29dca40`。本地/GitHub 复用只说明检索器、provider 路由、缓存和 SSRF 边界可复用，不改变本候选的原文审计状态，也不将仓储题名或开放标记当作病例证据。

## 原文多维证据

- 摘要称纳入来自巴西、美国、印度和土耳其的 11 名患者，均具有隐性 Robinow 综合征的临床特征；舌裂在 11 名患者中均出现。
- 论文报告 13 个不同的 `ROR2` 变异，其中 10 个此前未描述；患者 10 有第 4、5 外显子整段缺失。
- 检测层包括 5 名患者的 Sanger 测序、6 名患者编码区 Ion Torrent PGM 测序，以及 1 名患者的 MLPA；这些计数属于检测流程，不自动等同于 13 个独立确认性变异端点。
- 论文包含患者 4、6、7、8、9 的家系图，并描述患者 7 有一名受累姐妹；同时包含放射影像和骨骼表现比较。
- 现有文本提取未编码为治疗或纵向随访证据；实验室维度也保持为 false。

## 英文对应与确认性边界

论文页面和摘要存在英文元数据/摘要暴露，但未建立独立英文全文或同一患者身份对应。`ROR2` 变异表的转录本上下文尚未逐项独立标准化，因此保留源文变异表，不自行补全 HGVS。AI 双审和独立仲裁尚未完成，所有确认性文章、患者、家系、变异和语言独有事实增量均为 0；不得把 11 名患者或 13 个变异直接写成多语种相对英文的确认性增量。

工件：

- [候选审计包](../../benchmark/experiments/acmg_multilingual/candidate_audits/ror2_portuguese_unb_thesis_doi_10.26512_2015.07.d.20074_r1/)
- [葡语 R3 恢复矩阵](../../benchmark/experiments/acmg_multilingual/discovery_20261116/portuguese_recovered_case_matrix_r3.json)
