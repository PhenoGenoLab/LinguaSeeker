# 英文适配器恢复 sidecar 模块指南

> 为英文 provider-native readiness 提供可审计的全文恢复、ID 转换、原始 JATS 提取和探索性排序；不覆盖主 ledger，也不授予确认性准入。

**Status:** in-progress  
**Created:** 2026-11-17  
**Completed:**  
**PR:** 未合并

## 快速开始

所有 Python 命令通过 `uv` 执行；网络 sidecar 使用本地 `lit-acquisition` 的 SSRF 校验和代理配置。

```bash
export PYTHONPATH=/data/yangzs/Projects/01_Platform/05_lit-acquisition/src
uv run python scripts/recover_english_adapter_europepmc_xml_r1.py --concurrency 8 --timeout 8
uv run python scripts/resolve_english_adapter_identifier_routes_r1.py
uv run python scripts/recover_english_adapter_resolved_pmcids_r1.py
uv run python scripts/extract_english_recovery_xml_text_r1.py
uv run python scripts/triage_english_recovery_fulltext_r1.py
uv run python scripts/audit_english_adapter_recovery_r1.py
```

## 架构与数据流

```text
sealed English adapter ledger
        │
        ├── PMCID ── Europe PMC fullTextXML ── JATS + PMCID identity check
        │                                      │
        ├── PMID/DOI ── NCBI ID conversion ────┘
        │
        └── independent sidecar records/raw bodies
                         │
                  original JATS extraction
                         │
                  regex triage (仅排序)
                         │
                  occurrence-level recovery audit
```

每条恢复响应保存 HTTP 状态、最终 URL、内容哈希、原始 XML/错误 body 和身份校验结果。恢复脚本只增加 sidecar 文件，不修改 `english_baseline_adapter_20261116_r1` 下的 receipt、ledger 或 query identity。

## 脚本接口

| 脚本 | 入口参数 | 作用 |
|---|---|---|
| `recover_english_adapter_europepmc_xml_r1.py` | `--output-dir`, `--max-candidates`, `--concurrency`, `--timeout` | 对主 ledger 中未决 PMCID 请求 Europe PMC XML；要求 JATS `article` 根节点和匹配 PMCID。 |
| `resolve_english_adapter_identifier_routes_r1.py` | `--output-dir`, `--timeout` | 用 NCBI PMC ID 转换接口分批解析 PMID/DOI，保存原始 JSON 和哈希。 |
| `recover_english_adapter_resolved_pmcids_r1.py` | `--resolution-manifest`, `--output-dir`, `--concurrency`, `--timeout` | 对转换得到的 PMCID 复用 XML 恢复器。 |
| `extract_english_recovery_xml_text_r1.py` | `--output`, `--sidecar` | 从身份核验过的原始 JATS XML 提取文本；跳过 `ref`/`ref-list`。 |
| `triage_english_recovery_fulltext_r1.py` | 无 | 用正则统计 HGVS、患者、家系、检测、表型、影像和随访词项，仅生成排序队列。 |
| `audit_english_adapter_recovery_r1.py` | 无 | 按 `query_id + baseline_candidate_id` 将 sidecar 状态回映射到原始访问记录，计算未决比例。 |

## 关键安全与证据边界

- 请求前和每次重定向后调用 `lit_acquisition.net.security.validate_url_safe`；客户端关闭环境变量代理，使用 SDK 的显式代理解析。
- 只接受 HTTP 200、可解析 JATS `article` 和匹配的 PMCID；超时、HTTP 500、解析失败和 ID 缺失均保留为未决。
- `english_negative_claim_allowed=false` 和 `confirmatory_admission=false` 是每个 sidecar 的固定不变量。
- 文本来自原始 XML；不读取翻译、不用摘要替代正文。正则 triage 不等于患者级事实提取。
- 只有通过全文访问、原文身份、两名独立 reviewer 和独立仲裁后，才可讨论候选证据；本模块不执行自动准入。

## 性能与扩展

恢复器使用有界并发和单请求超时，记录文件按 PMCID 缓存，重启时可复用已写入记录。增加新来源时应新建 sidecar，而不是覆盖既有响应；新 HTTP 路线必须复用 SSRF 校验并登记身份验证规则。大量 JATS 文本提取在本地磁盘完成，避免把全文 body 长时间保存在内存中。

## 依赖与测试

- `uv`：项目 Python 运行入口。
- 本地 `lit-acquisition` commit `14e3dbfd07f1a5e7fbc1257c7f9fea37e29dca40`：HTTP 配置、代理解析和 SSRF 校验。
- `httpx`、标准库 `ElementTree`：网络访问和 JATS 解析。

验证命令：

```bash
uv run ruff check scripts/recover_english_adapter_europepmc_xml_r1.py \
  scripts/resolve_english_adapter_identifier_routes_r1.py \
  scripts/recover_english_adapter_resolved_pmcids_r1.py \
  scripts/audit_english_adapter_recovery_r1.py \
  scripts/extract_english_recovery_xml_text_r1.py \
  scripts/triage_english_recovery_fulltext_r1.py
uv run pytest tests/overall_design
```

当前恢复审计的 2,076 条访问中，sidecar 恢复 554 条，剩余未决比例 69.46%，所以该模块尚未使英文 readiness 达到 B2 的 10% 门槛。
