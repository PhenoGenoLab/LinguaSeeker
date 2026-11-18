# Orphadata 多语种探索批次 R3

**Status:** in-progress  
**Created:** 2026-11-16  
**Completed:**  
**PR:** 未合并

## 扫描范围

从 1,933 题 Orphadata 问题框排除既有探索样本后，以固定种子抽取 10 个新问题，使用 Europe PMC 对英文、西文、葡文和中文语言中性 ORPHA 回退各发送一条查询，共 40 条。所有原始 JSON 响应、查询 URL 和 SHA-256 均保存在：

[round3 scan manifest](../../benchmark/experiments/acmg_multilingual/candidate_audits/orphanet_exploratory_round3_20261116/scan_manifest.json)

命中数为英文 2,120、西文 11、葡文 4、中文回退 1,250。中文回退命中不代表中文术语或中文正文覆盖；这些数字只用于筛选。

## 高信息量候选

西语 PMCID `PMC11469105` 报告哥伦比亚神经肌肉中心 12 名遗传性远端肌病患者，正文表格包含 12 个 HGVS 事件，涉及 CAV3、ANO5、DES、DYSF、HNRNPA1、MYH7 和 TTN，并提供临床表现、家族史、CK、肌电图和遗传检测信息。

[候选审计包](../../benchmark/experiments/acmg_multilingual/candidate_audits/orphanet_exploratory_round3_20261116/spanish_distal_myopathy_pmc11469105/candidate_audit.json) 已绑定 Europe PMC XML、BioC JSON、抽取文本和 12 个英文精确变异查询。该记录的同一索引条目带英文摘要，摘要已覆盖 12 患者和基因列表；目前没有建立独立英文全文患者对应。因此文章、患者、家系、变异和语言独有事实确认增量均为 0。

当前状态为 `reviewed_with_arbitration`，尚未进入确认性分母。两个独立 commandcode 模型和一个独立仲裁模型均同意保留该来源：协议端点计数为文章 0、患者 0、家系 0、独立变异 0、语言独有事实簇 1。模型识别的 12 个 HGVS 表格事件保留为一个语言独有正文事实簇，因为精确等位基因已有英文/数据库边界命中，不能当作 12 个新的独立变异。
