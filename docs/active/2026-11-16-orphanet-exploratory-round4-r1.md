# Orphadata 多语种探索批次 R4：西语来源审计

**Status:** in-progress  
**Created:** 2026-11-16  
**Completed:**  
**PR:** 未合并

R4 对固定种子抽取的 10 个 Orphadata 问题执行了 40 条 Europe PMC 探索查询。总命中 5,142 条，其中英文 5,105、西语 5、葡语 0、中文语言中性回退 32。该批次仍是探索性扫描，不进入 B2 的确认性分母。

## 西语肾-眼结肠综合征线索

ORPHA 1475 / PMID 29333833 的西语来源为 *Archivos Argentinos de Pediatria* 2018;116(1):e106-e109，DOI `10.5546/aap.2018.e106`。通过出版方 PDF 路线保存了 4 页原文并完成文本提取。原文报告一名 12 岁女孩：产前双侧肾发育不良，出生第 5 天出现慢性肾病，双侧 II 级膀胱输尿管反流，双侧视神经乳头缺损，以及随访中的蛋白尿和肾功能变化。外周血 PCR/测序报告 `PAX2 NM_003987.3:c.310C>T (p.Arg104Ter/p.R104X)` 杂合无义变异，并记录 `N21+10G>C (rs4472867)` 多态性；双亲未检出该变异，但不能排除生殖系嵌合。

同一 Europe PMC 记录的英文摘要已覆盖同一患者、`p.R104X`、de novo/杂合状态和主要临床表现。冻结的英文对应探针检出的是其他 PAX2 病例或综述，未建立该患者的独立英文来源对应；这不等于全球英文缺失。

两名独立 commandcode 审阅模型均确认原文身份和证据支持，但一名建议保留探索性候选、另一名建议排除。独立仲裁依据已选的 `2-1` 内容范围（英文臂可读取同一非英语全文）判定排除：PCR 方法、双亲检测限制、`rs4472867` 和纵向表格属于同源全文暴露，不是英文臂不可获得的语言独有事实。所有确认性端点均为 0。

机器可读工件：

- [候选审计](../../benchmark/experiments/acmg_multilingual/candidate_audits/orphanet_exploratory_round4_20261116/renal_coloboma_pmid29333833/candidate_audit.json)
- [原文访问收据](../../benchmark/experiments/acmg_multilingual/candidate_audits/orphanet_exploratory_round4_20261116/renal_coloboma_pmid29333833/source_acquisition_receipt.json)
- [英文对应探针](../../benchmark/experiments/acmg_multilingual/candidate_audits/orphanet_exploratory_round4_20261116/renal_coloboma_pmid29333833/english_correspondence.json)
- [双审与仲裁收据](../../benchmark/experiments/acmg_multilingual/candidate_audits/orphanet_exploratory_round4_20261116/renal_coloboma_pmid29333833/ai_review_r1.json)
- [R4 汇总](../../benchmark/experiments/acmg_multilingual/candidate_audits/orphanet_exploratory_round4_20261116/round4_summary_r1.json)

## 西语先天性角化不良线索

ORPHA 1775 / PMID 7940052 仅保留 Europe PMC 摘要：一名 25 岁男性有先天性角化不良和骨髓低增生。当前没有 PMCID、DOI 或可审阅开放全文路由；摘要也没有患者特异性基因或 HGVS 结果。因此该线索标记为 `abstract_only_access_unresolved`，没有启动全文双审，也没有计入任何端点。

## 当前边界

- R4 仍不授权主研究确认性多语种检索。
- `article/patient/family/variant/language_exclusive_fact` 的批次增量保持 `0/0/0/0/0`。
- 访问失败、摘要-only 和有限查询未命中均不编码为英文阴性。
- 中文 ORPHA/HPO 回退仍是语言中性检索，不作为中文术语证据。
