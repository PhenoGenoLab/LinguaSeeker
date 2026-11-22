"""AgentScope builtin tools: shell, file and interaction.

Re-exported so skills import from a project module instead of reaching into
``agentscope.tool`` directly; behaviour is AgentScope's, unchanged.
"""

from agentscope.tool import (
    AskUser,
    BackendBase,
    Bash,
    DirEntry,
    Edit,
    ExecResult,
    Glob,
    Grep,
    LocalBackend,
    PowerShell,
    Read,
    ResetTools,
    ToolBase,
    Write,
)


def file_and_shell_tools(*, cwd: str | None = None) -> list[ToolBase]:
    """Instantiate the file/shell builtins for ``build_agent(tools=...)``.

    Args:
        cwd: Working directory for ``Bash``; defaults to the process cwd.

    Returns:
        Fresh instances of Bash, Read, Write, Edit, Glob and Grep.
    """
    return [
        Bash(cwd=cwd),
        Read(),
        Write(),
        Edit(),
        Glob(),
        Grep(),
    ]


__all__ = [
    "AskUser",
    "BackendBase",
    "Bash",
    "DirEntry",
    "Edit",
    "ExecResult",
    "Glob",
    "Grep",
    "LocalBackend",
    "PowerShell",
    "Read",
    "ResetTools",
    "ToolBase",
    "Write",
    "file_and_shell_tools",
]
