# 英文恢复病例多维证据矩阵 R1

**Status:** in-progress  
**Created:** 2026-11-17  
**Completed:**  
**PR:** 未合并

## 范围

从英文适配器恢复的 439 份原始 JATS 全文中，按文章类型、查询标签、HGVS/结构变异、患者/家系、遗传检测、临床、影像/病理、实验室和治疗/随访维度筛出 11 条病例或家系候选：PLEC、GAN、POMGNT1、HSD11B2、RMRP、SACS、NPHS2、OTC 两条、ADAR1 和 TTPA。

这是英文来源的探索性证据目录，不是多语种优效证据。英文臂可以读取同一批英文全文，因此所有确认性文章、患者、家系、变异和语言独有事实增量均登记为 0。SACS 的 6 个既有波兰病例作为文章内部上下文保留，不与索引病例混写；OTC 晚发病例的 `c.830>A` 按原文保留，未自行补全转录本或核苷酸。

## 机器可读工件

- [病例矩阵](../../benchmark/experiments/acmg_multilingual/overall_design/english_recovery_multidimensional_case_matrix_r1.json)
- [病例排序清单](../../benchmark/experiments/acmg_multilingual/overall_design/english_adapter_recovery_case_rank_r1.json)
- [原始 XML 提取清单](../../benchmark/experiments/acmg_multilingual/overall_design/english_adapter_recovery_text_manifest_r1.json)
- [矩阵生成脚本](../../scripts/build_english_recovery_case_matrix_r1.py)

矩阵每行包含原始 XML SHA-256、提取文本 SHA-256、观察单位、维度布尔值、原文定位/摘录和确认性端点字段。所有行标记 `exploratory_manual_extraction_not_ai_adjudicated`，不得直接进入确认性分母；若后续要作确认性端点判断，必须补齐两名独立 reviewer 和独立仲裁。

## 代表性证据宽度

- **PLEC**：1 名患者、1 个近亲家系、PLEC `c.7159G>T (p.Glu2387*)`、Sanger、皮肤/肌肉/脱发和家系信息。
- **GAN**：1 名墨西哥儿童、双亲携带、GAN `c.851+1G>A`、WES/Sanger、MRI 和神经发育表型。
- **POMGNT1**：1 名患者、2 个复合杂合变异、NGS、MRI/EEG 和长期抗癫痫治疗。
- **HSD11B2**：1 名儿童、2 个检测到的变异（其中 1 个为临床偶发 UBE3B 变异）、WES、低钾/高血压、影像和螺内酯随访。
- **RMRP**：1 名儿童、家系 WES、2 个 `n.` 变异、骨骼影像和未治疗随访边界。
- **SACS/NPHS2/OTC/ADAR1/TTPA**：分别补充结构变异、肾活检、氨代谢/移植、三家系分离和维生素 E 可治疗性等维度。

## 解释边界

观察证据丰富度不能代替语言增量。英文来源可能与多语种检索共享同一记录，也可能在英文臂中直接可见；因此本矩阵只扩展探索性病例库存，不证明多语种总体上增加更多证据。
