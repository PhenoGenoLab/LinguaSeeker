# core/tools — 具体工具

> skills 交给 agent 的具体工具。全部是标准 AgentScope tool 对象，可直接进模型循环，也可被 skill 直接调用。

## 分层位置

```
pipeline/graph     编排（topology、phases、routing）
graph/agents       门户（薄节点，只委托给某个 skill）
pipeline/skills    agent 实现（prompt、模型调用、控制流）
core/tools         具体工具 ← 本目录
```

单向依赖：上层可 import 下层，本目录只向下依赖 `agentscope` 与标准库，**不得 import `src.pipeline`**。

## 目录

```
tools/
├── builtin/    # shell、文件、交互：Bash PowerShell Read Write Edit Glob Grep
│               #                       AskUser ResetTools LocalBackend/BackendBase
└── task/       # TaskCreate TaskGet TaskList TaskUpdate
```

分类镜像 AgentScope 的 `agentscope.tool` 布局，因此 `src.core.tools.builtin` 对应
`agentscope.tool._builtin`，`src.core.tools.task` 对应 `agentscope.tool._task`。

## 用法

注册给 agent：

```python
from src.core.tools.builtin import file_and_shell_tools
from src.pipeline.skills.runtime.agent import build_agent

agent = build_agent(
    name="reviewer",
    system_prompt="...",
    model=model,
    tools=file_and_shell_tools(cwd="/data/yangzs/work"),
)
```

直接调用（不需要模型）：

```python
from src.core.tools.builtin import Read

result = await Read().call({"file_path": "README.md"})
```

只需个别工具时直接实例化类即可；工厂函数只是常用组合，没有隐藏默认值。

## 边界

- 本包是 `src/core` 中**唯一**允许 import `agentscope` 的位置；`src/core/shared/tools`
  仍然禁止（那层是确定性领域能力，不携带 agent 决策）。
- 不得 import `src.pipeline`。由 `tests/pipeline/test_import_boundaries.py` 断言。
- `SkillViewer` 在锁定的 agentscope 2.0.12 wheel 中只存在于 `agentscope.tool._builtin`，
  未公开导出，因此本包不 re-export。
