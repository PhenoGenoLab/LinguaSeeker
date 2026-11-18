# 葡语恢复病例矩阵 R3

**Status:** in-progress  
**Created:** 2026-11-17  
**Completed:**  
**PR:** 未合并

R3 将三条葡语原始全文候选统一到同一结构，并保留每个 `candidate_audit.json` 的 SHA-256 父哈希：

| 来源 | 候选数 | 主要观察单位 |
|---|---:|---|
| PYCR2 成人病例 | 1 | 1 名患者；WES、MRI、家族近亲、治疗随访 |
| ARSA juvenile MLD | 1 | 1 名患者；2 个源文 HGVS、WES/ENMG/MRI/酶活性、家系、纵向照护 |
| ROR2 Robinow 学位论文 | 1 | 11 名患者、4 个家系图上下文、13 个变异事件；Sanger/Ion Torrent/MLPA、影像和骨骼比较 |
| 合计 | **3** | 探索性观察单位，不是确认性分母 |

机器可读工件：[葡语 R3 恢复矩阵](../../benchmark/experiments/acmg_multilingual/discovery_20261116/portuguese_recovered_case_matrix_r3.json)。三条记录均保持 `confirmatory_admission=false`，文章、患者、家系、变异和语言独有事实确认性端点均为 0。ARSA 和 ROR2 的同记录英文摘要/元数据暴露不能替代独立英文病例对应；PYCR2 的精确 HGVS 在原文中缺失，未自行补全。

检索层可复用本地 `/data/yangzs/Projects/01_Platform/05_lit-acquisition` 或 GitHub `https://github.com/lanshi17/lit-acquisition` 的固定 commit `14e3dbfd07f1a5e7fbc1257c7f9fea37e29dca40`。该复用仅用于 provider 和访问路径，不解除全文、原始响应、双审和独立仲裁门禁。
