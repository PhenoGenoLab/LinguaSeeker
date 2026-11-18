# 英文恢复病例多维证据矩阵 R3（统一）

**Status:** in-progress  
**Created:** 2026-11-17  
**Completed:**  
**PR:** 未合并

R3 合并 R1 与 R2，形成 19 条去重的英文来源探索性病例/家系库存。候选覆盖：

- 单病例和多病例家系；
- SNV/indel、剪接变异、mosaic、CNV/全外显子缺失和结构变异；
- WES、trio-ES、Sanger、RNA-seq、超深度测序、MLPA 和功能验证；
- 临床、影像/病理、实验室、生殖/家系和治疗随访维度。

机器可读工件：[R3 统一矩阵](../../benchmark/experiments/acmg_multilingual/overall_design/english_recovery_multidimensional_case_matrix_r3_unified.json)。R3 绑定两个父矩阵 SHA-256，并重新验证每行原始 XML 哈希。确认性文章、患者、家系、变异和语言独有事实增量全部为 0：英文臂可以读取同一批来源，不能把这些英文案例解释成多语种优势。

R3 仍是探索性人工原文抽取；AI 双审/独立仲裁因 reasoning 服务 401/429 未完成，不能直接进入确认性分母。
