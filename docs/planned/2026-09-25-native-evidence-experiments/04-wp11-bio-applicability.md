# 04 WP11:BIO 对照适用性评估

**Status:** offline-preparation,未完成
**Created:** 2026-10-17
**Route:** `blocked_with_evidence`(尚未决定可行或不可行;见 §6)
**PR:** not created

[工作包表](00-decision-ledger.md) · [方法设计](01-design.md) · [执行与预算](03-execution-and-budget.md)

本文只记录离线可核验事实。未执行任何 BIO 工具、未付费调用、未读取 test 材料、未下载 99 GB 数据库。

## 1. 版本与许可清单

| 组件 | 固定版本 | 许可/条款证据 | 状态 |
|---|---|---|---|
| tmVar3 | commit `6c0c5770`(`ncbi/tmVar3`) | COPYING 为 NCBI 公共领域声明;依赖与资源条款未完全审计 | 代码包 368,594,869 字节,SHA256 `526d173c…73b63`,已缓存;运行未执行 |
| GNorm2 | commit `347515fa`(`ncbi/GNorm2`) | DISCLAIMER 为临床使用限制,不是软件再分发许可;LICENSE/COPYING 返回 404 | 未执行 |
| PubTator3 | 官方页面与 UI 资产 SHA256 `d74e5bcd…` | 官方页面含临床使用免责声明;服务与再分发条款未确立 | `run_status=not_executed`,`terms_status=unresolved` |
| Stanford tagger jar | 随 tmVar3 代码包提供 | 未找到许可文件 | unresolved |
| CRF++ | 随包 `CRF/` 提供 | 上游版本与许可文本未定位 | unresolved |

## 2. 语言与任务覆盖

- 当前无任何 BIO 工具在本项目八语言原生文本上的运行记录。覆盖情况**待验证**。
- tmVar3 的变异提及识别与归一化是否对非英语原文有效,无证据;不得据此推断适用。
- 任务层面只确认了输出类型:变异提及位置与归一化结果(由 tmVar3 源码与 README 说明)。原子事实映射未设计完成。

## 3. 运行依赖(仅源码与包内核查)

- 启动文件在输入读取前打开,缺失即中止(`tmVar.java`)。
- 六个静态 SQLite 文件在 `PostProcessing.Normalization` 中打开:`Merged`、`Expired`、`gene2rs`、`rs2gene`、`gene2tax`、`gene2humangene`。
- 动态 SQLite 路径由 `"Database/"+DB+".db"` 构造,包括 `var2rs_p/c/m/n/g.*`、`var2rs_clinvar_proteinchange.db`、`RS2CA_tmVarForm.db`。
- 数据库包 `tmVar3.Database.tar.gz` 约 99 GB,2024-03-19;拆分文件 2025-08-04。**未下载,与代码包兼容性未验证。**
- 模型文件存在:`CRF/MentionExtractionUB.Model`(232,501,476 字节)、`CRF/ComponentExtraction.Model`(882,512 字节)。哈希未记录。
- CRF 运行时:tar 内缺 `libcrfpp.so.0`,包装器 `CRF/.libs/lt-crf_test` 无法加载。**需要重建或另取 CRF++**。`crf_test` 是否为可执行 ELF 未验证。
- 基因预处理:README 要求先运行 GNormPlus,包内无 GNormPlus 组件;`BioCConverter.java:47` 将标注标为 GNormPlus 输出。**基因来源缺口未解决。**
- 已知源码缺陷:`tmVar.java:112` 将 `HideMultipleResult` 赋值自 `args[4]`(疑为 `args[5]`)。默认运行不受影响。
- `Test` 分支在 `tmVar.java:532` 无条件设置 `GeneMention = true`,归一化总是运行(`tmVar.java:539/543`)。

## 4. 原子事实映射方案

**状态:未设计完成,全部待验证。**

需要定义:tmVar3 输出的变异提及 → 原子事实字段的映射规则、偏移量契约(0 基/1 基、字符对齐)、无法映射项的处置。这些在 WP11-R1 的 `input-and-offset-contract.md` 中处理,尚未交付。

## 5. 成本估算

| 项 | 数值 | 证据 |
|---|---|---|
| 付费 API 调用 | 0 | 本轮未执行 |
| 磁盘 | `/data` 可用约 317 GB;数据库 99 GB 需额外空间 | 本地 `df` |
| 内存/交换 | RAM 31 GiB 总量,约 22–24 GiB 可用;交换 15 GiB 基本耗尽 | 本地检查,两次结果略有差异 |
| 数据库下载与解压耗时 | 未测 | 未执行 |
| 翻译(如用于非英语路径) | 未估算;设计文件要求计入 MT 成本 | 待定 |
| 人工处理 | 未估算 | 待定 |

## 6. 路线结论

**当前:`blocked_with_evidence`。** 阻塞项:

1. 数据库与代码包的兼容性证据缺失。
2. GNormPlus 或等效基因来源缺失。
3. CRF 运行时需重建,模型哈希未记录。
4. Stanford tagger、CRF++ 许可未核实。
5. PubTator3 服务条款未确立,不得作为默认对照。

可选路线(未选择,需要用户决定):
- 补齐数据库与基因来源后做有限运行;或
- 修改对照范围为无需 GNormPlus 的子路径(需用户批准);或
- 判定不可行并出具不可行报告。

在上述决定前,不启动 BIO 运行,也不计入对照成本。
