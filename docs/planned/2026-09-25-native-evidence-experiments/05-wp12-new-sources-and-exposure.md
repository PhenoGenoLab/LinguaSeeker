# 05 WP12:新来源与暴露检查

**Status:** offline-preparation,未完成(候选核验阶段)
**Created:** 2026-10-17
**PR:** not created

[工作包表](00-decision-ledger.md) · [数据与统计](02-data-and-analysis.md) · [执行与预算](03-execution-and-budget.md)

本文记录 WP12-R1 的核验结果与口径。候选来源均为 `not_admitted`、`frozen=false`,不标为已冻结盲测集。

## 1. 交付位置与校验

- 目录:`docs/archive/papers/2026-10-17-native-v3-task-release-01/wp12-r1-delivery/`
- 文件:`candidate-adjudication.csv`(30 行)、`publication-links.csv`(35 行)、`candidate-shortlist.csv`(9 行)、`historical-identity-register.json`、`evidence-manifest.json`(62 条)、`README.md`、`SHA256SUMS`、`build-wp12-r1.py`
- 校验:`sha256sum -c SHA256SUMS` 全部 OK;30 行候选 ID 唯一。
- 原始受保护文件 66 份与 8 份输入哈希无不一致。
- 付费调用 0;外部 HTTP 请求 0;候选全文或摘要读取 0。

## 2. 候选处置(30 行)

| 处置 | 行数 |
|---|---|
| `scope_ruling_pending_document_type` | 14 |
| `continue_verification` | 9 |
| `pending_russian_pair_review` | 2 |
| `unresolved_reference_list_hit_only` | 2 |
| `excluded_same_document_as_historical_exposed`(MED/24750837 = rett_006) | 1 |
| `attestation_recorded_not_admitted`(MED/31095231,Aron 更正自述) | 1 |
| `scope_ruling_pending_boundary` | 1 |

- Aron 更正后的自述已记录,未进入开发集或冻结集。
- 候选来自 143 条命中的第一页,**不穷尽**。

## 3. 历史身份与 publication group

- `historical-identity-register.json`:55 个规范组,80 条原始行,60 个原始 ID;53 个 ID 有本地文本,7 个仅由登记表引用核对。5 组别名;1 条变更事件(CE-2026-10-17-01),未修改任何合并。
- **rett_036 → rett_035:** 字节相同,Stage-1 manifest 支持别名。但两份暴露台账不一致(rett_036 为 `unmapped`、`in_dev_v3_20=0`;rett_035 为 `pub_rett_035`、`in_dev_v3_20=1`)。别名保留,组归属待核验,原始出版物未核查。
- **rett_088:** 无本地文本且无登记引用,身份不可评估。
- **登记表冲突:** 登记表将 rett_006 引为 "Zou M et al., 16(4):374-378";本地题头为 Zhao PW et al., 16(4):393-396,且与 MED/24750837 一致。已记录冲突,未改登记表。

## 4. 疑似关联(publication-links.csv)

- MED/29213044 与 MED/29359720:均为俄语,题名与作者列表相同,DOI 与页码不同。记为 `possible_link`,未合并,不作共享病例结论。
- MED/41782542 亦为俄语,不与该对匹配,单独处理。
- 单词短题名(如 "[Rett syndrome]")使候选间重叠虚高,此类重叠仅记为低信息量。

## 5. 身份与暴露口径

- **显式患者词不自动确定身份。** "患者""先证者"等须结合病例段落、家庭成员关系和文档命名空间核验,方可提出具体 scope_id。当前无已确定的 scope_id。
- **历史缺证先记为"本地未留存"。** 云侧日志或计费记录的可恢复性未核查前,不得写为"不可恢复";现有预算估算不能证明覆盖全部缺失尝试费用。
- **敏感性修订的区间重算(WP13 适用):** 须保存逐事实修改映射,并对修订结果重新执行相同的 19 组 bootstrap。仅凭点估计接近零,不能称其落在"噪声区间"。本轮未执行该分析。
- 权利状态:30 行均为 `unresolved`,未读取许可页面。

## 6. 未决与边界

- 文献类型范围裁定:14 行;FOXG1/EEF1A2/Rett 样边界裁定:3 行。
- 权利声明与许可:全部未核验。
- 本交付仅为证据核验,**不是 WP12 完成,不是 Test-v3 冻结**。WP12 完成需要来源清单、组映射、暴露账本与纳入排除理由全部经验收。
- 验收文件 `acceptance.md` 尚未写入,由主协调者负责。
