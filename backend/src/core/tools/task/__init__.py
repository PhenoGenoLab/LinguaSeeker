"""AgentScope task tools: create, get, list and update tasks.

Re-exported so skills import from a project module instead of reaching into
``agentscope.tool`` directly; behaviour is AgentScope's, unchanged.
"""

from agentscope.tool import TaskCreate, TaskGet, TaskList, TaskUpdate, ToolBase


def task_tools() -> list[ToolBase]:
    """Instantiate the task tools for ``build_agent(tools=...)``.

    Returns:
        Fresh instances of TaskCreate, TaskGet, TaskList and TaskUpdate.
    """
    return [TaskCreate(), TaskGet(), TaskList(), TaskUpdate()]


__all__ = [
    "TaskCreate",
    "TaskGet",
    "TaskList",
    "TaskUpdate",
    "ToolBase",
    "task_tools",
]
