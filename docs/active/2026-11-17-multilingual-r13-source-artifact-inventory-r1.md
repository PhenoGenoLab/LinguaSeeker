# 多语种 R13 历史源包清单 R1

**Status:** in-progress  
**Created:** 2026-11-17  
**Completed:**  
**PR:** 未合并

对 R13 队列中 22 条 `pending_source_review` 历史记录，按 PMCID 后缀扫描本地 `source_packages/`，并跟随既有审计文件中的 `source_artifact`、`source_html_path` 和 `extracted_text_path` 指针。22/22 条记录均能绑定到已保存的源字节；其中 7 条还带有历史 review/audit 文件。

机器可读清单：[source artifact inventory R1](../../benchmark/experiments/acmg_multilingual/discovery_20261116/multilingual_r13_source_artifact_inventory_r1.json)。清单保存每个源文件的相对路径、字节数和 SHA-256。

| 状态 | 数量 |
|---|---:|
| `source_bytes_present` | 22 |
| 历史 review/audit 文件存在 | 7 |

源包存在只证明后续可做原文级审阅，不代表已完成 AI 双审、独立仲裁或确认性纳入。访问错误文件与成功源字节同时存在时，两者均保留，不将失败记录改写成阴性。
