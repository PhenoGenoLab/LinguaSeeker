# 多语种遗传变异案例发现 R1

**Status:** in-progress  
**Created:** 2026-11-16  
**Completed:** —  
**PR:** N/A (exploratory research)

本轮针对中文、西语和葡语全文索引做了有界探索性检索，重点寻找同时包含 HGVS、检测方法、患者/家系、表型、影像、实验室或治疗结局的病例。检索结果和候选字段见[机器可读发现总结](../../benchmark/experiments/acmg_multilingual/discovery_20261116/discovery_summary_r1.json)。

完成独立审阅的两个西语案例是：

- **GNAO1（PMID 41074486）**：一名患儿、三联体外显子组、`c.545C>T/p.Thr182Ile`、纵向运动障碍、治疗反应与死亡。该变异已出现在英文全文队列；患者身份未能与英文队列合并，因此不计新患者或语言独有变异。
- **Coffin–Lowry（PMID 42096245）**：一名患儿、RPS6KA3 panel 检测、`c.1762G>A/p.Glu588Lys`、详细发育/面容/影像和实验室信息。ClinVar 已有同一等位基因并标为单提交者 VUS；独立英文全文患者对应仍未完成，不计语言独有增量。

另外发现六条中文候选：MUSK、CHD7、SSUH2、SLC25A20、USP53 和 TNFAIP3/A20 家系。其中 TNFAIP3/A20 和 USP53 已取得全文并完成独立审阅：A20 报告先证者与父亲的外显子 2–9 杂合缺失、WES 未检出 SNV/小 indel、CNV/qPCR 验证；USP53 报告婴儿与哥哥的复合杂合变异、父母分相和 Sanger 验证。两者的同文英文摘要均已覆盖核心家系/变异事实；A20 的独立英文家系对应未决，USP53 的 `c.829dup` 在当前 bounded exact 查询中未命中 ClinVar/其他 EPMC 记录。两条已审阅案例均不计确认增量。其余四条候选的 PMC HTML 正文现已取得：MUSK 出版方英文链接返回404，CHD7链接误指Turner综合征文章，SSUH2有不同英文DD-I家系报道，SLC25A20有同文英文全文；四条均仍待独立英文对应审查。所有 bounded no-match 都不能解释为英文总体缺失。

本轮终点仍为：确认文章、患者、家系、变异和语言独有事实增量均为 0。A20 家系已完成独立来源审阅，但其英文对应仍是有界未决；所有候选均不进入确认性分母，也不能用于证明多语种在总体上必然增加更多证据。

**2026-11-16 原文复取补记：** 后续经 PMC HTML 再取回 MUSK、CHD7、SSUH2 和 SLC25A20 四篇全文，并保存原文哈希及提取文本。四篇同文英文摘要均覆盖核心病例/变异；SLC25A20 还取得 DOI 匹配的同文英文全文译本；MUSK 出版方翻译链接返回 404，CHD7 链接误指不相关 Turner 综合征文，SSUH2 有 2017 年英文文献报告同一等位基因且与 2025 家系身份未决。以上不改变确认文章/患者/家系/变异/语言独有事实增量为 0；四条的独立对应审查已完成，仍排除于确认性分母。详见[原文复取机器记录](../../benchmark/experiments/acmg_multilingual/discovery_20261116/recheck_20261116/recheck_summary_r1.json)。


后续批次的逐候选主审、独立复核与仲裁见[四条全文候选复核与仲裁 R1](2026-11-16-multilingual-recheck-adjudication-r1.md)。机器可读汇总见 `discovery_summary_r2.json`。
