"""In-memory persistence adapters.

They let the API and the pipeline run without a database service. Data lives
for the process lifetime and is not shared across workers; use them for
development, tests, and DB-less deployments.
"""

from src.dao.memory.agent_jobs import InMemoryAgentJobStore
from src.dao.memory.job_queue import InMemoryRunJobQueue
from src.dao.memory.processing_cache import InMemoryProcessingCache
from src.dao.memory.run_state_store import InMemoryRunStateStore

__all__ = [
    "InMemoryAgentJobStore",
    "InMemoryProcessingCache",
    "InMemoryRunJobQueue",
    "InMemoryRunStateStore",
]
