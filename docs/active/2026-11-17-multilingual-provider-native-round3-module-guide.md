# provider-native Round3 脚本指南

**Status:** in-progress  
**Created:** 2026-11-17  
**Completed:**   
**PR:** 未合并

脚本链：

- `run_multilingual_provider_native_exploratory_round3_r1.py`：通过 pinned `lit-acquisition` provider 调用生成 64 条原始响应。
- `rank_multilingual_provider_native_round3_case_candidates_r1.py`：按病例/家系/遗传标题信号和 DOI/PMCID 可得性冻结 20 条候选。
- `recover_multilingual_provider_native_round3_fulltexts_r1.py`：以 DOI/PMCID 做 Europe PMC 标识符解析并回收 JATS；无 PMCID 保持未决。
- `extract_multilingual_provider_native_round3_fulltext_r1.py`：只从原始 JATS 提取文本。
- `build_multilingual_provider_native_round3_matrix_r1.py`：人工原文锚定 3 条新矩阵记录，保存语言验证状态和引文。

运行示例：

```bash
PYTHONPATH=/data/yangzs/Projects/01_Platform/05_lit-acquisition/src \
uv run --project /data/yangzs/Projects/01_Platform/05_lit-acquisition \
python scripts/run_multilingual_provider_native_exploratory_round3_r1.py --seed 20261121 --count 8

uv run --project . python scripts/rank_multilingual_provider_native_round3_case_candidates_r1.py --limit 20
uv run --project . python scripts/recover_multilingual_provider_native_round3_fulltexts_r1.py --limit 20
uv run --project . python scripts/extract_multilingual_provider_native_round3_fulltext_r1.py
uv run --project . python scripts/build_multilingual_provider_native_round3_matrix_r1.py
```

provider 查询语言只代表检索输入；来源语言必须由原文核验。SciELO 连接失败、DOI 无 PMCID 和元数据-only 结果都保留访问状态，不转成英文阴性或语言独有事实。
