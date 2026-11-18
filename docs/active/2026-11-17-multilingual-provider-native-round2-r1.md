# 多语种 provider-native 探索 R2

**Status:** in-progress  
**Created:** 2026-11-17  
**Completed:**  
**PR:** 未合并

首轮 provider-native 探索发现 Europe PMC 查询的 Boolean 优先级问题：`LANG AND label OR ORPHA` 可能让 ORPHA 分支绕过语言过滤。R2 保留 R1 原始收据，改用显式括号的 `LANG:(label OR ORPHA)` 形式，仅扫描注册的西语/葡语标签；中文标识符回退不送入本轮 Crossref 诊断。

R2 对 8 个固定种子问题执行 48 条查询，获得 328 条元数据：西语 186 条、葡语 142 条。元数据命中不计患者、家系或变异端点。西语 sitosterolemia PMID 25074708 仍只有元数据/摘要访问未决，未启动全文审阅。

另保存西语 PMID 30350845 的 TUBB4A 低髓鞘白质营养不良摘要级线索：一名 8 岁儿童，含运动/小脑/基底节影像和致病 TUBB4A 变异描述；全文不可得，摘要没有精确 HGVS，因此标记为访问未决，不进入双审或确认性分母。

机器可读工件：[R2 汇总](../../benchmark/experiments/acmg_multilingual/candidate_audits/multilingual_provider_native_round2_20261117/round2_summary_r1.json)。

确认性端点增量保持：文章 0、患者 0、家系 0、变异 0、语言独有事实 0。R2 仍不进入确认性分母，也不解除英文 readiness 门禁。
