# SLC46A1 西语病例候选审计 R1

**Status:** in-progress  
**Created:** 2026-11-16  
**Completed:**  2026-11-16  
**PR:** n/a（探索性证据包）

## 范围

本记录审计 PMID 42809880 / PMCID PMC13700926 的西语全文。它属于探索性候选，不进入确认性分母，也不用于证明多语种检索总体优效。原文 XML 的 `xml:lang` 为 `es`；欧洲 PMC 元数据同时提供同一记录的英文摘要。

## 来源和可复现收据

- 题名：*Malabsorción hereditaria de folato por mutación en SLC46A1 con deficiencia cerebral de folato y epilepsia refractaria: primer caso reportado en Argentina*。
- DOI：`10.31053/1853.0605.v83.n3.50324`；PMID：`42809880`；PMCID：`PMC13700926`。
- 原文 XML：[PMC13700926.xml](../../../benchmark/experiments/acmg_multilingual/discovery_20261116/round4_broad/PMC13700926.xml)，SHA-256 `bbf803d6b62a0ea4776aa5060d5a82ea3d07ef2869d89e39ffca3fcad73834a4`。
- 提取文本：[PMC13700926.txt](../../../benchmark/experiments/acmg_multilingual/discovery_20261116/round4_broad/PMC13700926.txt)，SHA-256 `a96ae39f544cdca02d86de8b42f77a83f39c4934b26fa8f8a2df9cffcb1d8557`。
- 候选包：[source_packages/slc46a1_spanish_pmc13700926](../../../benchmark/experiments/acmg_multilingual/discovery_20261116/source_packages/slc46a1_spanish_pmc13700926)。

## 原文提取

原文报告 1 名阿根廷男婴、1 个家系和 1 个同源变异事件：`NM_080669.6:c.981_982del (p.Tyr327_Cys328delinsTer)`。英文摘要使用较短的蛋白写法 `p.Tyr327Ter`；两种原文写法均保留，不擅自改写。

全文提供多维病例事实：早期胃肠症状和微血管病性贫血，IgA/IgM 与多糖抗原反应异常，发育迟缓和难治性癫痫，低肉碱和高同型半胱氨酸，MRI/CT/EEG 变化，父母携带验证，以及 17–54 月龄的 CSF 5-MTHF、治疗和随访表。这里的事实均来自原文；正文相对同文英文摘要的细节暂只作候选事实单位，不等同于英语全局缺失。

## 英文对应和数据库边界

- 无过滤精确查询 `SLC46A1 "c.981_982del"` 命中 1 条，且为同一西语记录。
- `LANG:eng AND SLC46A1 AND "c.981_982del"` 命中 0 条；蛋白写法的英文精确查询也命中 0 条。该结果是有界检索收据，不是全球无匹配证明。
- ClinVar UID `801406` 收录同一等位基因，分类为 `Pathogenic/Likely pathogenic`，多提交者、无冲突。ClinVar 只证明数据库已有等位基因，不能证明患者、文章或事实已被英文来源报告。
- 同一记录带有英文摘要，不视为独立英文病例全文；尚未建立独立英文患者身份对应。

## 双审与仲裁

- [primary_review.json](../../../benchmark/experiments/acmg_multilingual/discovery_20261116/source_packages/slc46a1_spanish_pmc13700926/primary_review.json)：源文主审。
- [independent_review.json](../../../benchmark/experiments/acmg_multilingual/discovery_20261116/source_packages/slc46a1_spanish_pmc13700926/independent_review.json)：隔离复读，未读取主审结论。
- [adjudication.json](../../../benchmark/experiments/acmg_multilingual/discovery_20261116/source_packages/slc46a1_spanish_pmc13700926/adjudication.json)：独立仲裁。

三份记录对文章、患者、家系和变异单位达成一致；均判定当前没有可确认的文章、患者、家系、变异或语言独有事实增量。正文细节保留为 `candidate_only_unpooled`。

## 当前协议状态

用户已选择 Orphadata 1,933 题问题框、每题 `δ=0.25` 个语言独有事实单位和固定种子简单随机无放回抽样；60 题 manifest 仍为草案，尚未确认性检索。非英语语言范围和英文臂是否读取英文查询命中的非英语全文，仍需按选择题冻结后才能进入确认性阶段。
