# 西语慢性肉芽肿病 p47-phox 全文家系审计 R1

**Status:** in-progress  
**Created:** 2026-11-17  
**Completed:**  
**PR:** 未合并

## 来源与访问

候选来自 `q_0488` 西语 provider-native 收据，DOI 为 `10.4067/S0034-98872000000500006`。Crossref 的 SciELO 主页路线 `www.scielo.cl` 返回 403，但同一 DOI 的历史 SciELO 域名 `scielo.conicyt.cl` 返回完整 HTML 正文。通过本地 `lit-acquisition` 的 SSRF-safe `secure_fetch` 保存原始 HTML、去除参考文献后的正文文本、访问收据和 provider 响应哈希。

## 原文多维证据

- 同一家族 2 名男性患者：15 岁病例有反复脓肿、肺炎和肝脓肿；21 岁兄弟晚发皮肤/颈部脓肿，临床严重程度不同。
- NBT、超氧阴离子生成和 Western blot 共同显示吞噬细胞氧化爆发缺陷及 p47-phox 缺失。
- PCR/酶法测序显示两名患者均有 p47-phox 基因第 2 外显子起始处的纯合 GT 二核苷酸缺失。原文没有现代 HGVS 或 NCF1 转录本坐标，因此保留源文写法，不自行标准化。
- 家系图显示两名受累兄弟；母亲和 4 名健康兄弟 NBT 正常。病例 1 接受磺胺甲噁唑-甲氧苄啶预防，病例 2 接受脓肿引流和抗菌治疗。

## 英文对应与确认性边界

同一 SciELO 记录含英文摘要，但没有独立英文全文或患者身份对应。AI 双审和独立仲裁尚未完成，文章、患者、家系、变异和语言独有事实确认性增量均为 0；该记录只进入探索性西语矩阵。

工件：

- [候选审计包](../../benchmark/experiments/acmg_multilingual/candidate_audits/multilingual_round2_open_fulltexts_20261117/cgd_spanish_doi_10.4067_s0034_98872000000500006/)
- [西语 R4 矩阵](../../benchmark/experiments/acmg_multilingual/discovery_20261116/spanish_recovered_case_matrix_r4.json)
