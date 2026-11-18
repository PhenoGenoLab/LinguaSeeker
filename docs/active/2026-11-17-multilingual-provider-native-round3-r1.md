# 多语种 provider-native 探索批次 R3

**Status:** in-progress  
**Created:** 2026-11-17  
**Completed:**   
**PR:** 未合并

本轮复用本地/GitHub `lit-acquisition` 固定 commit `14e3dbfd07f1a5e7fbc1257c7f9fea37e29dca40`，从确认性计划中排除前两轮已用问题，抽取 8 个新问题。每题分别以西语和葡语注册标签调用 SciELO、Europe PMC、Crossref、DOAJ，保留 provider 原始 envelope。

机器可读工件：[provider-native round3](../../benchmark/experiments/acmg_multilingual/candidate_audits/multilingual_provider_native_round3_20261117/)。

| 阶段 | 结果 |
|---|---:|
| 新问题 | 8 |
| provider-language 记录 | 64 |
| 成功 provider 响应 | 48 |
| 元数据条目 | 356 |
| 去重候选池 | 243 |
| 冻结候选 | 20 |
| Europe PMC 原始 JATS 全文 | 4 |
| 新源文多维矩阵 | 3 |
| 原文事实引文 | 15 |

3 条新矩阵记录中，PMC11346508 和 PMC7141146 的原文含西语正文/摘要；PMC11195492 为英文正文，虽被西/葡查询触达，但不计作非英语正文。15/15 引文均在提取原文中可定位。观察患者单位为 146、变异事件为 2；家系未有可靠统一计数则保持 `null`。

DOI-only 候选多数无法由 Europe PMC 暴露 PMCID，保持 `unresolved_no_pmcid`，不把 provider 命中或访问失败当作患者级证据。所有确认性端点为 0。
