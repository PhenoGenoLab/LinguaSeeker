# 多语种 R2 访问边界探针 R1

**Status:** in-progress  
**Created:** 2026-11-17  
**Completed:**  
**PR:** 未合并

对两个仍有遗传病例线索但未进入正文矩阵的候选执行有界替代路线：

- 西语 MORC2 DOI `10.1016/s2667-0496(26)00746-5`：Elsevier XML 只返回 `coredata` 元数据；text/plain 路线返回 400，ScienceDirect/PDF 路线返回 403；不编码病例或变异。
- 西语 RARS2 DOI `10.5546/aap.2022.e39`：Europe PMC 仅返回订阅状态元数据，出版方 PDF/HTML 及参数变体均返回 403；不编码患者或变异，不作英文阴性。

这些探针延续本地 `lit-acquisition` 的 SSRF-safe 访问边界。失败路线与 metadata-only 路线不进入确认性分母，也不改变 R11 矩阵。

- OpenAlex 对 LAMA2、葡语 CGD 和听力学论文标记为 green OA，并提供 content PDF/GROBID URL；这些端点当前均返回 429。SLC26A4 的 Americanae 替代入口超时，仍不构成正文证据。
