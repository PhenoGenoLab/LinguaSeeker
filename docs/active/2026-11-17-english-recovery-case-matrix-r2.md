# 英文恢复病例多维证据矩阵 R2

**Status:** in-progress  
**Created:** 2026-11-17  
**Completed:**  
**PR:** 未合并

## 新增范围

R2 从同一批恢复英文 JATS 全文中补充 8 条与查询标签相符的独立候选：GAN、KRT2、COL3A1 两条、ADAR1、TTN、PRKCI 和日本 PUCD 新生儿筛查。候选覆盖 mosaic 变异、全外显子缺失、三代家系、RNA/功能验证、结构变异检测和人群筛查等证据维度。

## 代表性证据

- **GAN**：沙特 7 岁男孩，WES 检出 `NM_022041.3:c.1456G>A`，神经电生理显示弥漫性轴索性多神经病。
- **KRT2**：5 岁中国男孩，病灶组织 NGS 与超深度测序确认 `p.Glu487Lys` mosaic 变异及组织间 VAF 差异，同时有病理和免疫荧光证据。
- **COL3A1**：一例脑动脉夹层相关 vEDS 和一例轻微外伤后双侧胫前动脉假性动脉瘤；后者在测序阴性后由 MLPA 检出全外显子缺失。
- **ADAR1**：三代中国家系中先证者及 5 名受累亲属共享 `c.763C>T (p.Q255X)`。
- **TTN**：爱沙尼亚家系中两名同胞和父亲具有不同遗传剂量的 FINmaj/剪接变异组合，含 trio-ES、Sanger、RNA-seq、肌活检和 MRI。
- **PRKCI**：17 名有综合征性口面裂/周皮病表型的个体，包含 de novo 和稀有变异，并有斑马鱼功能验证。
- **PUCD 筛查**：日本 4 年前瞻性新生儿筛查发现 CPS1 复合杂合病例和 OTCD 病例，结合氨基酸/有机酸和遗传检测评估假阳性控制。

## 工件与边界

- [R2 机器可读矩阵](../../benchmark/experiments/acmg_multilingual/overall_design/english_recovery_multidimensional_case_matrix_r2.json)
- [R2 生成脚本](../../scripts/build_english_recovery_case_matrix_r2.py)

每行均绑定原始 XML 和提取文本哈希，`confirmed_increment` 全部为 0，`confirmatory_admission=false`。这些来源可被英文臂读取，因此不能支持“多语种必然增加更多证据”的结论；AI 双审/仲裁仍未因 reasoning 服务 401/429 而完成。
