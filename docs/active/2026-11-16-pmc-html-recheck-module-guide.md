# PMC HTML 复取与可审计文本提取脚本

> 从 PMC HTML 的首个 `<article>` 元素提取可读正文块，并为来源和提取文本保存 SHA-256 收据；用于探索性多语种候选复核，不负责确认性计数。

## 快速开始

在项目根目录运行：

```bash
uv run python scripts/extract_pmc_html_recheck_r1.py
```

脚本读取四个预置候选目录的 `recheck_20261116_retry1/pmc.html`，写出 `source_html_recheck.txt`、`source_manifest_recheck.json`，并检查可用的出版方英文译文路由。

## 数据流

```text
PMC HTML
  └─ first <article lang="zh">
       ├─ block extraction (h1–h6, p, table cells, captions, list items)
       ├─ source_html_recheck.txt + SHA-256
       └─ source_manifest_recheck.json

Publisher translation HTML
  └─ embedded data= JSON
       ├─ expected DOI comparison
       └─ publisher_translation_manifest.json (+ English text when DOI matches)
```

## 公开函数

| 函数 | 签名 | 作用 |
|---|---|---|
| `extract` | `extract(candidate_dir: Path) -> dict[str, Any]` | 提取 PMC HTML 正文块并写入来源清单。 |
| `extract_publisher_translation` | `extract_publisher_translation(candidate_dir: Path) -> dict[str, Any] \| None` | 按候选的预期 DOI 核对出版方英文译文路由。 |
| `main` | `main() -> None` | 处理四个固定探索候选并打印 JSON 汇总。 |

脚本使用标准库 `html.parser`、`json`、`hashlib` 和 `pathlib`，不发起网络请求；网络响应由外部收据步骤保存后再处理。

## 关键边界

- HTML 中存在 `<article>` 才能作为正文来源；挑战页或错误页不会被当作正文。
- 出版方英文译文只有在嵌入 DOI 与候选预期 DOI 完全一致时才标为 `verified_same_record_english_full_text`。
- 同文英文摘要/译文不是独立英文来源，不能自动形成语言独有增量。
- 脚本只产生来源和提取工件，不修改确认性分母或终点台账。

## 测试与校验

```bash
uv run ruff check --no-cache scripts/extract_pmc_html_recheck_r1.py
uv run python scripts/extract_pmc_html_recheck_r1.py
uv run python scripts/validate_question_frame_contract_r1.py
```

下游校验应同时断言 JSON 可解析、SHA-256 为 64 位十六进制且与实际文件匹配。完整总体设计测试使用：

```bash
uv run pytest tests/overall_design
```
