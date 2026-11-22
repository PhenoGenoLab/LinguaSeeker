# libs — 本地共享库

> 只剩一个本地包。Rust 原生扩展已发布为独立 wheel，不再在本仓库维护源码。

## 目录

```
libs/
└── config-loader/    # acmg-config-loader:分层 YAML 配置加载器(pure Python)
```

## Rust 原生扩展

`rust_io`(含 `rust_io.net`、`rust_io.files`)通过 PyPI 安装:

```toml
# backend/pyproject.toml
"rust-io>=0.2,<0.3",
```

```bash
uv sync                                # 安装
uv run python -c "import rust_io.net, rust_io.files"
```

- 包主页:`https://pypi.org/project/rust-io/`
- 平台要求:`cp312`、Linux x86_64 且 glibc ≥ 2.38(当前发布只有这一个 wheel)
- 源码与发布流程在发布仓库(`github.com/lanshi17/LinguaSeeker`),不在本仓库
- 可用性探测与降级封装:`backend/src/utils/rust_io.py`

升级方式:改 `backend/pyproject.toml` 的版本约束 → `uv lock` → 跑
`uv run python -c "import rust_io.net, rust_io.files"` 冒烟。

## config-loader

```bash
cd backend/libs/config-loader
uv run pytest
```

`backend/src/core/config.py` 直接 `from acmg_config_loader import ...`。
