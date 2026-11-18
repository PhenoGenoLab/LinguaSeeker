# C04 展示规范化实施

**Status:** completed
**Completed:** 2026-11-12
**Created:** 2026-11-12
**PR:** not created

用户已确认实施 C04。依据已接受 DISPLAY-NORM-DESIGN-R1 选项 B，仅生成瞬态 DisplayTextView；不持久化显示文本，不改 facts/EnglishView/坐标/身份/评价/队列/role。工作树 `.worktrees/native-display-norm-impl-r1`，种子为已接受 R5（源代码继承 EVIDENCE-ROLE-IMPL-R1）。

1. 建立隔离工作树与输入快照 → 验证种子文件hash及原封包。
2. 实施类型化显示投影 → 验证五字段、状态边界与已确认规则。
3. 完整离线回归、静态检查与输出字节比较 → 交付新封包及模块指南。

用户已确认：保留单次实体解码；同一原始 EnglishView 重复投影一致，不承诺任意文本幂等。实现已交付：45新增/531完整离线测试通过、0网络、Ruff/AST通过。交付位于 docs/archive/papers/2026-11-12-native-display-norm-impl-delivery/display-norm-impl-r1。代码待人工审查，不自动合并。G-02/BASE保持开放。
