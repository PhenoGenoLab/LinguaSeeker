# 英文未决 PMID Europe PMC 元数据探针 R1

**Status:** in-progress  
**Created:** 2026-11-17  
**Completed:**  
**PR:** 未合并

对未决 PMID 做了有界 Europe PMC core metadata 探针。去重后检查 10 条 PMID：10 条返回元数据，0 条暴露 PMCID；观察到的全文链接均为 subscription-labeled 或缺失。该结果只说明当前样本中的路线可达性，不能推出全体 PMID 没有全文。

机器可读工件：[PMID probe summary R1](../../benchmark/experiments/acmg_multilingual/overall_design/english_unresolved_pmid_probe_summary_r1.json)。原始响应和每条记录收据保存在对应 executions 目录。
