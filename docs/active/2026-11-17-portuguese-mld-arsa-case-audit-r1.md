# 葡语 ARSA juvenile MLD 全文病例审计 R1

**Status:** in-progress  
**Created:** 2026-11-17  
**Completed:**  
**PR:** 未合并

## 来源

葡语原文标题为 `Leucodistrofia metacromática: Estudo de caso em paciente infanto-juvenil`，DOI `10.33448/rsd-v14i9.49562`。出版方 RSD Journal 提供 PDF；原始 PDF、出版方页面、响应 headers 和文本提取均已保存并哈希。

## 多维原文证据

- 1 名 juvenile MLD 患者，8 岁起出现步态不稳、跌倒、左侧无力、行为/学习下降，随后失去行走、吞咽和语言功能。
- ARSA 两个杂合变异：`c.1283C>T`（`ENST00000216124`）和 `c.465+1G>A`；原文说明无法由该检测确定 cis/trans。
- WES、ENMG、脑 MRI 和 ARSA 酶活性检测共同支持诊断；白细胞 ARSA 活性为 `0.36 nmol/h/mg protein`，显著降低。
- MRI 显示深部/脑室周围白质异常、胼胝体和内囊后肢受累；家系信息包括非近亲父母和健康哥哥。
- 2022–2025 纵向记录显示进行性神经退化、管饲、康复、营养/语言治疗和家庭姑息照护；未进入疾病修饰治疗。

## 对应边界

PDF同时包含葡语原文和英文摘要，属于同记录英文层；没有独立英文全文对应。Europe PMC DOI 查询返回 0 条，两个精确变异查询返回的是 token 化噪声记录，未验证为同一患者或同一 ARSA 病例，因此不作为对应证据，也不作为全球英文阴性证明。AI 双审/独立仲裁尚未完成，所有确认性端点保持 0。

工件：

- [候选审计包](../../benchmark/experiments/acmg_multilingual/candidate_audits/mld_portuguese_arsA_doi_10.33448_rsd49562_r1/)
- [葡语 R2 矩阵](../../benchmark/experiments/acmg_multilingual/discovery_20261116/portuguese_recovered_case_matrix_r2.json)
