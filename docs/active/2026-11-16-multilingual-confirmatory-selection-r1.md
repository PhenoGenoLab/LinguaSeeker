# Nasu–Hakola 反向控制仲裁与确认性方案选择 R1

**Status:** in-progress  
**Created:** 2026-11-16  
**Completed:** —  
**PR:** N/A (research protocol)

用户输入 `1-1，2-1，3-1` 已按此前抽样/阈值三题记录，并在本轮范围门禁中按以下语义登记：

1. 采用 Orphadata 2026-06-23 的 1,933 个已评估胚系关联且有 HPO 注释的问题框；
2. 主要最小实际意义增量 δ = 0.25 个经核验的语言独有事实单位/问题；
3. 采用固定种子的简单随机无放回抽样，而不是比例分层或最小单元覆盖分层。

本轮范围选择也记录为：

1. `1-1`：多语种臂纳入英文、西文、葡文和中文；
2. `2-1`：英文查询命中的非英语全文可以读取，但作为同源暴露，不计入语言独有事实；
3. `3-1`：中文缺少已验证本地化疾病名时，使用预先登记的语言中性 ORPHA/HPO 标识符/语义槽回退，不把回退冒充中文术语覆盖。

回退契约已保存为 [chinese_query_fallback_contract_r1.json](../../benchmark/experiments/acmg_multilingual/overall_design/chinese_query_fallback_contract_r1.json)，SHA-256 为 `c5a0ba0aa1344e27f223fe62ef2a7b1ff6a6ad0e28d0c9c5d97696ebd8074d5a`。1,933 行无检索干跑已生成 [manifest](../../benchmark/experiments/acmg_multilingual/overall_design/chinese_query_fallback_dry_run_manifest_r1.json) 和 [receipt](../../benchmark/experiments/acmg_multilingual/overall_design/chinese_query_fallback_dry_run_receipt_r1.json)，1,933/1,933 行通过、未使用语言特定字段。契约只固定字段和禁止事后扩词，尚未固定每题查询预算、候选上限或日期截点。

已保存机器可读回执：[user_selected_confirmatory_inputs_r1.json](../../benchmark/experiments/acmg_multilingual/overall_design/user_selected_confirmatory_inputs_r1.json)。已生成对应的 δ=0.25 草案：[orphanet_simple_random_selected_delta025_20261116.json](../../benchmark/experiments/acmg_multilingual/overall_design/draft_manifests/orphanet_simple_random_selected_delta025_20261116.json)，但仍标记为未冻结、未检索。

## 反向控制仲裁

独立来源审阅已完成，记录见[独立审阅工件](../../benchmark/experiments/acmg_multilingual/candidate_audits/nasu_hakola_spanish_two_sibling_r1/independent_source_audit.json)。来源是 Molina-Monasterios 与 Molina-Abecia 的 2003 年玻利维亚 Nasu–Hakola 西语病例报告（PMID 12717671；DOI 10.33588/rn.3609.2002423）。正文为西语，出版物同时印有英语摘要以及西语、葡语摘要。

仲裁确认正文描述两名兄弟病例（30 岁与 33 岁），不是三名患者；较年长且患相似疾病的兄长就是正文病例 2。西语正文比英语摘要多出逐例病程、临床检查、影像、骨囊肿、手术和病理细节，但这些只是相对同文摘要的细节差异，不能据此声称全球英文文献没有相同信息。文章没有患者级分子检测、共分离结果或 HGVS 变异，因此不计新的变异或患者证据。英语同库查询返回同一篇文章，位列 854 条结果中的第 509 位；这只反映检索可达性。

原来源清单所写“西语查询 1/1”与留存精确查询收据的 `hitCount=0` 冲突。独立审阅无法从保留材料解释差异；西语排名因此记为未核实，不将它用作检索收益证据。该反向控制已加入探索性台账 R2，所有确认性增量端点仍为 0，并明确排除出确认性分母。

这些范围选择已记录，但不等于完整协议冻结。有限总体简单随机功效敏感性模拟采用 `N=1,933`、`δ=0.25`、单侧 `α=0.0125`、目标功效 80%，并用非经验估计的合成计数总体设定 `μ₁=0.50`、`σ=1/2/3`。首个达到约 80% 的网格样本量是 150/500/800；在 60 题下模拟功效约为 0.308/0.012/0.0004。10%/20% MCAR 未决膨胀后，联系量约为 167/188、556/625、889/1,000。该敏感性模拟未从探索案例估算方差，不能视为预注册样本量；MCAR 膨胀也不能消除 MNAR 偏差。60 题草案尚未冻结为最终样本量。语言中性中文回退的具体查询构造、来源库、查询预算、缺失上限/MNAR 界、α/多重性、设计忠实功效模拟、停止规则和英文基线仍是检索前门槛。本轮没有启动确认性查询。探索性材料（包括 Nasu–Hakola 反向控制）不进入确认性分母。
