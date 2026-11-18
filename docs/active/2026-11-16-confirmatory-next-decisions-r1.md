# 确认性实验下一步决策 R1

**Status:** in-progress  
**Created:** 2026-11-16  
**Completed:** —  
**PR:** N/A（检索前协议）

当前探索性证据已扩展到 25 条中文、西语和葡语全文候选，并完成四语种查询模板干跑。用户已选择 `A2，B2，C3`；确认性检索仍未授权，因为日期截点、缺失/MNAR 边界和中期分析边界尚未填写。

已收到选择：`A2，B2，C3`，并确认最后的预算选项 `D1`。

仍需填写：

- A2 日期截点：`____ UTC`
- B2 最大未决/仅摘要比例：`____%`
- B2 MNAR 敏感性范围：`____`
- C3 alpha-spending 方法：`O'Brien–Fleming / Pocock / 其他 ____`
- C3 中期分析时点：`信息量 ____% / ____%`
- C3 优效边界：`____`
- C3 无效边界：`____`

预算已冻结为：每语言 1 个固定模板；每查询最多 20 个候选；每查询最多获取 20 篇全文；不追加后续查询。

| 选择 | 推荐方案 | 主要影响 |
|---|---|---|
| A | `A1`：Europe PMC + PMC/Europe PMC，截止 2026-11-16 23:59:59 UTC | 与现有收据同源，覆盖较窄但最易复核 |
| B | `B1`：先冻结未决上限、MNAR 界和方差保护情景，再定样本量 | 先解决解释有效性，再确定工作量 |
| C | `C1`：单侧 α=0.0125，一次最终分析 | 与当前规划敏感性一致，不做中期适应 |

机器可读版本见 [pending_protocol_decisions_r1.json](../../benchmark/experiments/acmg_multilingual/overall_design/pending_protocol_decisions_r1.json)。在上述空白填写前，不会生成确认性 manifest 或启动检索。
