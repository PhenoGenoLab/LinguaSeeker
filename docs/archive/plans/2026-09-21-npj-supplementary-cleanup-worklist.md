# npj 补充材料清理执行单

**Status:** completed
**Created:** 2026-09-21
**Completed:** 2026-09-22
**PR:** 未提交、未合并；保留主工作区供人工审阅。
**依据:** [`2026-09-21-paper-artifact-attribution.md`](../../active/2026-09-21-paper-artifact-attribution.md) §4.8 / §4.9，以及[原审计清单](../papers/2026-09-22-npj-review/superseded-notes/REMAINING_AUDIT_TASKS.md)。

> **归档说明（2026-09-22）**：本单已由[完整证据审阅与修订](2026-09-22-npj-paper-review.md)取代。主文、补充材料和全部当前图表已经同步修改；字段以真实 107 个标识符报告，资助按用户确认写无专项资助。离线复算进一步发现并修正错值漏计 FN，主结果由 0.6045 更正为 0.5220。因此下文的旧数值、行号、待批准事项和执行建议仅保留为历史记录，不是当前任务或验收标准。原生多语言等未完成研究见[修订稿状态](../papers/2026-09-22-npj-review/SUBMISSION_STATUS.md)。

> **原则**：本单只做「删除」与「改写为可溯源的表述」，**不重跑任何实验**。每项都给出当前原文锚点与建议替换文本，可直接落地。
> **行号基准**：`npj_paper/main.tex` = **212 行**；`npj_paper/supplementary.tex` = **244 行**（2026-09-21 核）。
> **未获批准前不要执行**——其中「18 vs 107 字段体系」等属作者决策（见 §四）。

## 一、为什么要动这些块

| 数据块 | 判定依据 |
|---|---|
| Table S2 / §Language-Stratified / Fig S2 | 冻结工件中**没有按语言的逐条评测数据**：150 条基准跑的是英文 `source.md`（81 条另带合成中文译文、8 条带另六种语言合成译文），Rett 子集仅 51 条 / 7 篇源文档 / 4 种语言，且真实语言方向与稿中声称相反 |
| Table S3（BLEU / 实体保持率） | 需要「参考译文」的 50 篇验证集，工件不存在 |
| Table S5 / Fig S3（接地召回 94.3 / 3.2 / 2.5%） | 100 篇验证集，工件不存在 |
| Figure 4（语言 ridge plot） | `assets/generate_advanced_figures.py:293-339` 用 `np.random.seed(42)` + 硬编码均值，纯模拟 |
| 补充相关热图 | `generate_supp_fig_correlation_heatmap`（同文件 L342-390）用 `0.3 + 0.4*random()`，纯随机，且未被稿件引用（孤儿资产） |
| 表型 F1（supp 0.489 / main 0.462） | 与工件不符：真实值 `B.clinical_phenotypes` = 0.3038、`B.hpo_terms` = 0.0000 |
| 82% 非英语占比 | 数字本身正确，但缺「配额抽样」限定语（6 处中 5 处未限定） |
| supplementary L222 的「100% precision」与 19 条观测分类 | 定性过高；且分类清单与 **npj 自己 main.tex L154** 和 GIM 台账 v1.2 都不一致 |

## 二、删除清单

### D1 Table S2 + 按语言分层小节 + Figure S2

- `supplementary.tex:218` 删除：`\input{assets/table_s2_language_stratified.tex}`
- `supplementary.tex:158-160` 用下列**弃权声明**替换整节（保留小节标题可避免编号断档）：
  ```latex
  \subsection{Language-Stratified Performance}

  We do not report per-language $F_1$. The unified benchmark is drawn from
  English-source documents (81 of 150 entries also carry a synthetic Chinese
  translation and 8 more carry synthetic translations in six further languages),
  so a per-language split would measure the translation condition rather than
  native-language extraction. The Rett/MECP2 subset (51 entries from 7 source
  documents in four languages) is too small and too unevenly distributed to
  support a language comparison, and we report it only as a single pilot.
  ```
- `supplementary.tex:235-240` 删除整段 `figure_s2_language_stratified.pdf` 图环境
- 资产与脚本：删除 `assets/table_s2_language_stratified.tex`、`assets/figure_s2_language_stratified.pdf`；删除 `assets/generate_supplementary.py` 的 `generate_figure_s2_language_bars`（约 L252-276）与 `generate_table_s2_language_stratified` 内的硬编码 `lang_data` 占位字典（约 L153-181）

### D2 Table S3（翻译质量）

- `supplementary.tex:162-169` 删除整个 `\subsection{Translation Quality Analysis}` 块（BLEU 42.3/38.7/45.1/51.2/40.8/49.3、实体保持 94.2%/87.6%、回译一致 76.4%/91.2%）
- `supplementary.tex:220` 删除 Table S3 段落
- 对应 `assets/table_s3_*.tex`（如存在）一并删除
- 说明：BLEU 必须有参考译文语料，是本单里**最不存在争议**的一项

### D3 Table S5 + Figure S3（接地召回）

- `supplementary.tex:175-177` 删除 `\subsection{Grounding Recall Analysis}` 块
- `supplementary.tex:224` 删除 Table S5 段落
- `supplementary.tex:242` 删除 Figure S3 文本段
- `assets/generate_advanced_figures.py:342-390` 删除 `generate_supp_fig_correlation_heatmap`

### D4 Figure 4（语言 ridge plot）

- `assets/generate_advanced_figures.py:293-339` 删除 `generate_fig4_ridge_plot`
- `assets/figure4_language_ridgeplot.pdf` 删除
- 前置确认：稿中无 `figure4` 的 `\includegraphics` / `\ref`（撰写本单时未见引用，执行前再过一遍）

### D5 编号连带（最易出错）

- 删除 S3、S5 后需重排：S4→S3，S1/S2 图号顺延；`supplementary.tex` 与 `main.tex` 中所有 `Table~S*`、`Supplementary Figure S*` 交叉引用同步
- 执行后统一 `grep -n "S[0-9]" npj_paper/*.tex npj_paper/assets/*.tex` 逐条核对，确认无断号、无指向已删对象

## 三、改写清单

### R1 表型 F1（两处统一）

- `supplementary.tex:156`：`... for all 18 evidence fields ...` 与 `free-text phenotype descriptions reach $F_1=0.489$`
- `main.tex:160`：`... while free-text phenotype descriptions reach $F_1=0.462$.`
- 建议替换为（两处同）：
  ```latex
  Gene symbols reach $F_1=0.983$, while phenotype-related fields are the weakest
  (\texttt{B.clinical\_phenotypes}: $F_1=0.304$; \texttt{B.hpo\_terms}: $F_1=0.000$).
  ```
- **需作者确认**：正文/补充说「18 个 ACMG 证据字段」，而工件 `by_field` 有 **107 个字段 id（A–J 族）**。建议二选一：① 改称「18 个聚合字段族」；② 在补充材料给出 18→107 的映射表（见 §四-1）

### R2 Table S4 的「100% 精确」与 19 条观测分类

- `supplementary.tex:222` 的 `209 layer-specific field anchors verified manually with 100\% precision` 改为：
  ```latex
  209 layer-specific anchor checks passed local content-hash, path, line-anchor and
  quote verification. This establishes consistency of the local ledger with the
  retained files; it does not establish original-publication provenance, field
  correctness, or clinical validity. No independent human language or
  clinical-genetics review was performed.
  ```
- 同段的 `19 ... across seven evidence categories: variant nomenclature (10), phenotype descriptions (4), inheritance mode (2), functional assays (1), population frequency (1), patient metadata (1)` **与本稿 main.tex L154 自相矛盾**：L154 说的是「seven distinct evidence fields across two categories (A: variant identification, C: inheritance/segregation)」，也就是字段 id **全属 A.\* 与 C.\***。GIM 台账 v1.2（GIM 补充表 S6）为更细的七类：cDNA 4 / 蛋白 6 / 变异类型 2 / de novo 2 / 母源 2 / 父源 2 / 功能域 1 = 19。
  → **建议以 GIM 台账版为准改写**（唯一可追溯到台账的版本），并与 main.tex L154 的「two categories」措辞对齐

### R3 82% 限定语（5 处）

照 GIM 的写法加「in our quota-sampled corpus」，并去掉升级表述：

| 位置 | 现值（节选） | 建议 |
|---|---|---|
| `main.tex:54` 摘要 Results | `The 1,602-document corpus revealed that 82\% of clinical genetics and rare disease literature (283 of 346 classified documents) originated from non-English sources` | `In our quota-sampled 1,602-document corpus, 82\% of documents classified post hoc as clinical genetics and rare disease (283 of 346) were non-English` |
| `main.tex:71` 引言 | `This quantifies, for the first time, the magnitude of clinical genetics evidence systematically excluded by monolingual curation.` | 删句，或改为 `The corpus is quota-sampled and cancer-query-driven, so it does not estimate the world prevalence of non-English clinical genetics literature.` |
| `main.tex:76` fig:gap caption | `... 283 (81.8\%) originated from non-English sources across six languages, quantifying the evidence gap ...` | 加 `in this corpus` 限定 |
| `main.tex:171` Discussion | `The 1,602-document corpus reveals that 82\% of clinical genetics literature originates outside English-language publications.` | 加 `in our quota-sampled corpus` 限定；**并删除同句的** `Source-grounded traceability, verified at 100\% precision`（改为本地哈希/行锚校验通过的定性表述） |
| `main.tex:187` Conclusion | `By quantifying the 82\% non-English literature contribution and achieving $F_1=0.6045$ ...` | 改为 `In this corpus, 82\% of ... ; \methodname{} achieved $F_1=0.6045$ ...` |

> **无需改动**：`main.tex:142`（`fig:benchmark` caption）已自行披露「synthetic language variants」且注明「per-dataset baseline stratification not available in frozen artifacts」；`main.tex:110`（合成译文披露）与 `main.tex:122`（配额抽样限定语）都已到位。此前清单曾把 L142 列为待改项，本次重读后**更正为已基本到位**。

## 四、需作者决定（不擅自改）

1. **18 vs 107 字段体系**：改称「聚合字段族」，还是补映射表？
2. **81 条合成中文译文的处置**：L110 已如实披露；若要支撑更强的「多语言」结论，需要真实多语言 gold——超出本轮范围
3. **Table S2 位置**：本单建议直接删除；若希望留一个「未来工作」占位，用 D1 的弃权声明替代即可
4. **`[Grant Numbers]`（`main.tex:200`）**：唯一剩余占位符，需作者填

## 五、执行后验证

1. `pdflatex` 四步编译（先 `rm` 掉 aux）：Overfull / Underfull / Warning 计数应为 0（这是当前基线）
2. grep 确认下列数字在 `npj_paper/` 内**全部消失**：
   - 按语言分层 F1：`0.641` `0.598` `0.612` `0.585` `0.623` `0.571` `0.604`
   - BLEU：`42.3` `38.7` `45.1` `51.2` `40.8` `49.3`；`94.2\%` `87.6\%` `76.4\%` `91.2\%`
   - 接地召回：`94.3\%` `3.2\%` `2.5\%`
3. grep 确认 `Table~S` / `Supplementary Figure S` 编号连续
4. `pdftotext` 抽查补充材料 PDF：已删小节标题不再出现

## 六、相关文件

| 用途 | 路径 |
|---|---|
| 审计依据 | `docs/active/2026-09-21-paper-artifact-attribution.md`（§4.7–4.9、§4.12） |
| 稿件 | `npj_paper/main.tex`、`npj_paper/supplementary.tex` |
| 待删资产/脚本 | `npj_paper/assets/generate_advanced_figures.py`、`npj_paper/assets/generate_supplementary.py`、`npj_paper/assets/table_s2_language_stratified.tex`、`figure4_language_ridgeplot.pdf`、`figure_s2_language_stratified.pdf` |
| 真实数据来源 | `npj_paper/assets/table1_corpus.tex`、`table3_rett.tex`（已逐值核过，保留） |
