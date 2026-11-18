# SMPD1 p.Arg610del 英文对应探索

**Status:** in-progress  
**Created:** 2026-11-17  
**Completed:**  
**PR:** 未合并

对葡语病例 DOI `10.31365/issn.2595-1769.v21i4p223-229` 报告的 SMPD1 变异，使用 Europe PMC 检索编码和蛋白写法，保存了原始响应及哈希。三条查询分别返回 13、8、8 条索引记录；查询没有限定语言，命中不等于已核验病例。

其中英文索引论文 [PMID 37628828](https://europepmc.org/article/MED/37628828)、DOI `10.3390/ijms241612645` 的英文摘要明确描述一名携带 SMPD1 `p.Arg610del` 的患者及其来源肝类器官。因此，**该蛋白水平变异本身不能称为非英语独有**。

两篇论文是否涉及同一患者、葡语病例的临床细节是否已有独立英文来源，以及转录本和编码写法是否完全等价，均待核查。该探索不证明英文缺失，也不进入确认性分母。

进一步读取英文 JATS 全文后发现，该文明确报告患者纯合 `NM_000543.5:c.1829_1831delGCC`、`p.Arg610del`，并使用患者肝活检来源类器官；样本来自马德里 Hospital 12 de Octubre。葡语病例正文也写出纯合 `c.1829_1831delGCC (p.Arg610del)`，但该引文没有给出转录本。两个来源在展示的编码及蛋白写法上相同；两名患者是否为同一人仍未决，地点差异和等位基因相同均不足以单独判定。

全文对照：[english_fulltext_comparison_r1.json](../../benchmark/experiments/acmg_multilingual/candidate_audits/smpd1_arg610del_english_correspondence_20261117_r1/english_fulltext_comparison_r1.json)。

两篇原文的初步逐维对照还发现：两者都报告该变异的纯合状态和肝脾受累；均描述肺部情况，但具体表现不同。葡语病例 11 岁时的随访细节尚未在其他英文来源中系统核查。葡语表格与英文论文采用不同酶活表达，暂不能直接比较数值。这些比较均未完成独立审阅，也不能据此判定患者身份或语言独有事实。

逐维记录：[patient_dimension_comparison_r1.json](../../benchmark/experiments/acmg_multilingual/candidate_audits/smpd1_arg610del_english_correspondence_20261117_r1/patient_dimension_comparison_r1.json)。

对英文 JATS 的 64 条参考文献进行有界字面检索，未发现葡语论文 DOI、作者 Pagan/Lourenco 或期刊缩写 SOPERJ；这不排除间接引用或患者重叠。葡语原文说明患者为男性儿童，10 周龄时被收养；已检查的英文论文没有提供足以确认或排除同一人的标识。患者对应继续标为未决。

参考文献核查记录：[patient_correspondence_bibliography_r1.json](../../benchmark/experiments/acmg_multilingual/candidate_audits/smpd1_arg610del_english_correspondence_20261117_r1/patient_correspondence_bibliography_r1.json)。

机器可读证据：[检索收据](../../benchmark/experiments/acmg_multilingual/candidate_audits/smpd1_arg610del_english_correspondence_20261117_r1/manifest.json)；[英文摘要变异匹配](../../benchmark/experiments/acmg_multilingual/candidate_audits/smpd1_arg610del_english_correspondence_20261117_r1/english_allele_match_r1.json)。

对葡语原 PDF 第 223 页按文本块坐标分离双栏，并完整核查同篇英文摘要：摘要明确报告 3 岁男性、肝脾大、呼吸症状和影像提示肺部受累；没有报告患者具体 HGVS、纯合状态、精确酶活数值或 11 岁 2 个月的随访。葡语正文第 225 页报告了这些后续细节。这个比较仅涉及同一篇文章的英文摘要，并不能证明其他英文来源缺失；事实上，另一篇英文全文也报告了相同展示写法的变异及纯合状态。患者身份与独立审阅仍未决，不计入确认性增量。

分栏原文、页面坐标、PDF 哈希和事实可见性：[同篇英文摘要核查](../../benchmark/experiments/acmg_multilingual/candidate_audits/smpd1_arg610del_english_correspondence_20261117_r1/same_article_english_abstract_visibility_r1.json)。
