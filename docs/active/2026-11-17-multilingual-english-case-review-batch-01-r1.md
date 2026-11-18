# 多语种/英文统一病例审阅批次 01

**Status:** in-progress  
**Created:** 2026-11-17  
**Completed:**   
**PR:** 未合并

从 70 条统一病例审阅包中按冻结的维度覆盖和候选 ID 规则选取首批 10 条审阅输入。批次只安排审阅顺序，不产生 reviewer 结论、独立仲裁、证据增量或确认性分母。

机器可读批次：[multilingual_english_case_review_batch_01_r1.json](../../benchmark/experiments/acmg_multilingual/discovery_20261116/multilingual_english_case_review_batch_01_r1.json)。父审阅包哈希在批次中绑定，避免来源漂移。

批次候选 ID：

`PMC7667337`、`PMC5775598`、`PMC13741775`、`PMC13719475`、`PMC13634090`、`PMC13562385`、`PMC13451836`、`PMC13434505`、`PMC13351653`、`PMC13300342`。

每条记录的 `reviewer_a`、`reviewer_b` 和 `arbitrator` 均为空，`confirmed_increment` 为零，`confirmatory_admission=false`。审阅仍须仅依据绑定的原文源文件；翻译文本不能作为 primary extraction。

该批次沿用本地可复用的 `lit-acquisition` 获取/来源工件方案：本地路径为 `/data/yangzs/Projects/01_Platform/05_lit-acquisition`，固定 commit 为 `14e3dbfd07f1a5e7fbc1257c7f9fea37e29dca40`，GitHub 远端为 `lanshi17/lit-acquisition`。本轮只引用已生成的原文工件，不重新发起确认性检索，`retrieval_authorized=false` 保持不变。
