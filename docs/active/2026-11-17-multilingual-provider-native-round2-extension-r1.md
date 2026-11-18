# 多语种 provider-native 探索 R2 扩展 R1

**Status:** in-progress  
**Created:** 2026-11-17  
**Completed:**  
**PR:** 未合并

在保留 R2 首批 8 个固定种子问题收据的基础上，复用本地 `lit-acquisition` 固定 commit `14e3dbfd07f1a5e7fbc1257c7f9fea37e29dca40`，按相同的显式 Europe PMC 语言分组和注册标签模板补充 4 个未用问题。扫描仍只使用西语/葡语，每题每 provider 的返回上限为 20，单请求超时为 20 秒，没有 follow-up 查询。

本轮共 12 个问题、72 条 provider-language 记录、494 条元数据候选。新增问题 ID 为 `q_0054`、`q_0102`、`q_0233` 和 `q_0469`。这些结果是筛选收据，未读取或仲裁全文，也没有建立独立患者对应；访问失败、摘要-only 和 no-match 均未被编码为英文阴性。

机器可读工件：

- [直接扫描收据](../../benchmark/experiments/acmg_multilingual/candidate_audits/multilingual_provider_native_round2_20261117/summary.json)
- [R2 扩展审计汇总](../../benchmark/experiments/acmg_multilingual/candidate_audits/multilingual_provider_native_round2_20261117/summary_r2.json)

`summary_r2.json` 保留父 R2 的筛选线索和未决访问线索，同时记录新增问题集合、按语言元数据计数和直接收据 SHA-256。文章、患者、家系、变异和语言独有事实确认性端点均为 0；扩展不进入确认性分母，也不解除英文 readiness 门禁。
