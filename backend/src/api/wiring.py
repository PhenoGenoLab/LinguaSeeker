"""Application dependency wiring — single source of truth for engine & session factory."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from redis.asyncio import Redis as AsyncRedis

from loguru import logger

from src.core.config import Settings, get_config
from src.dao.neo4j.connection import build_neo4j_driver
from src.dao.neo4j.graph_provider import Neo4jGraphProvider
from src.dao.neo4j.repository import Neo4jRepository
from src.dao.postgresql.connection import async_session_factory, build_async_engine
from src.dao.postgresql.job_queue import JobQueueRepository
from src.dao.postgresql.review.annotation_store import PostgresAnnotationStore
from src.dao.postgresql.review.audit_store import PostgresAuditStore
from src.dao.postgresql.review.evidence_store import PostgresEvidenceStore
from src.dao.postgresql.review.feedback_store import PostgresFeedbackStore
from src.dao.postgresql.review.literature_store import PostgresLiteratureStore
from src.dao.postgresql.run_state_store import PostgresRunStateStore
from src.dao.postgresql.standardization.runner import PostgresStandardizationRunner
from src.dao.postgresql.users import PostgresUserStore
from src.dao.redis.connection import build_redis_client

if TYPE_CHECKING:
    from neo4j import AsyncDriver
    from src.runs import AgentJobStore, RunJobQueue, SingleJobDispatcher
    from src.core.tools.parsing.local.parser import (
        MinerULocalParser,
    )


class _UnavailableSessionFactory:
    """Session factory for DB-less runs: any use returns a 503-mapped error."""

    def __call__(self, *args: object, **kwargs: object) -> object:
        del args, kwargs
        from src.utils.exceptions import PersistenceUnavailableError

        raise PersistenceUnavailableError("database-backed feature")


_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None
_redis_client: AsyncRedis | None = None
_local_parser: MinerULocalParser | None = None
_dispatcher: SingleJobDispatcher | None = None
_neo4j_driver: AsyncDriver | None = None
_neo4j_repository: Neo4jRepository | None = None
_agent_job_store: "AgentJobStore | None" = None
_startup_lock_raw_conn: Any = None


def set_agent_job_store(store: "AgentJobStore") -> None:
    """Register the process-wide agent job store."""
    global _agent_job_store
    _agent_job_store = store


def get_agent_job_store() -> "AgentJobStore":
    """Return the agent job store (raises if wiring has not run)."""
    if _agent_job_store is None:
        raise RuntimeError("Agent job store not initialized — call wire_dependencies() first")
    return _agent_job_store


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return the singleton session factory (set by wire_dependencies)."""
    if _session_factory is None:
        raise RuntimeError("Session factory not initialized — call wire_dependencies() first")
    return _session_factory


def get_engine() -> AsyncEngine | None:
    """Return the singleton engine (or None if not yet initialized).

    Prefer ``get_session_factory()`` for normal DB access; this accessor
    exists for health-check and shutdown paths that need the raw engine.
    """
    return _engine


async def dispose_engine() -> None:
    """Teardown the engine (called from lifespan shutdown)."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None


def get_redis_client() -> AsyncRedis | None:
    """Return the singleton async Redis client (or None if not yet initialized)."""
    return _redis_client


async def dispose_redis() -> None:
    """Teardown the Redis client (called from lifespan shutdown)."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None


def get_neo4j_driver() -> AsyncDriver | None:
    """Return the singleton Neo4j driver (or None if not yet initialized)."""
    return _neo4j_driver


def get_neo4j_repository() -> Neo4jRepository | None:
    """Return the singleton Neo4j repository (or None if not yet initialized)."""
    return _neo4j_repository


async def dispose_neo4j() -> None:
    """Teardown the Neo4j driver (called from lifespan shutdown)."""
    global _neo4j_driver, _neo4j_repository
    if _neo4j_repository is not None:
        _neo4j_repository = None
    if _neo4j_driver is not None:
        await _neo4j_driver.close()
        _neo4j_driver = None


async def create_search_index_tables() -> None:
    """Create standalone search-index tables that Alembic does not manage."""
    from src.dao.postgresql.search_index_repo import search_index_metadata

    engine = get_engine()
    if engine is None:
        return
    async with engine.begin() as conn:
        await conn.run_sync(search_index_metadata.create_all)


def has_database() -> bool:
    """Return True when a PostgreSQL engine is configured."""
    return get_engine() is not None


def make_user_store() -> PostgresUserStore:
    """Build a user store bound to the configured session factory."""
    return PostgresUserStore(get_session_factory())


def make_evidence_store() -> PostgresEvidenceStore:
    """Build a read-only evidence query store."""
    return PostgresEvidenceStore(get_session_factory())


def make_feedback_store() -> PostgresFeedbackStore:
    """Build a feedback store that owns the patch transaction."""
    return PostgresFeedbackStore(get_session_factory())


def make_audit_store() -> PostgresAuditStore:
    """Build a read-only audit store."""
    return PostgresAuditStore(get_session_factory())


def make_literature_store() -> PostgresLiteratureStore:
    """Build a literature profile store."""
    return PostgresLiteratureStore(get_session_factory())


def make_annotation_store() -> PostgresAnnotationStore:
    """Build an annotation store."""
    return PostgresAnnotationStore(get_session_factory())


def make_run_state_store() -> PostgresRunStateStore:
    """Build a run state store."""
    return PostgresRunStateStore(get_session_factory())


def make_standardization_runner() -> PostgresStandardizationRunner:
    """Build the PostgreSQL-backed standardization runner."""
    return PostgresStandardizationRunner(
        cfg=get_config(),
        session_factory=get_session_factory(),
    )


def build_rate_limit_storage():
    """Build the slowapi storage backend, falling back to memory.

    Only transport failures degrade. A malformed URL or bad config must fail
    startup instead of silently downgrading a security control.
    """
    import redis as redis_lib
    from limits.storage import MemoryStorage, RedisStorage

    cfg = get_config()
    pwd = cfg.redis.password or None
    auth = f":{pwd}@" if pwd else ""
    redis_url = f"redis://{auth}{cfg.redis.host}:{cfg.redis.port}/{cfg.redis.db}"
    try:
        client = redis_lib.Redis(
            host=cfg.redis.host,
            port=cfg.redis.port,
            db=cfg.redis.db,
            password=pwd,
            socket_connect_timeout=1,
        )
        client.ping()
        client.close()
        logger.info("Rate limiter using Redis storage")
        return RedisStorage(redis_url)
    except (redis_lib.RedisError, OSError) as exc:
        logger.warning("Redis unavailable ({}), rate limiter using in-memory storage", exc)
        return MemoryStorage()


async def check_postgres() -> bool:
    """Ping PostgreSQL using the singleton engine."""
    try:
        from src.dao.postgresql.health import ping_postgres

        engine = get_engine()
        if engine is None:
            logger.warning("PostgreSQL health check skipped: engine not initialized")
            return False
        return await ping_postgres(engine)
    except Exception as exc:
        logger.warning("PostgreSQL health check failed: {}", exc)
        return False


async def check_redis() -> bool:
    """Ping Redis using the singleton client."""
    try:
        client = get_redis_client()
        if client is None:
            logger.debug("Redis health check skipped: client not initialized")
            return False
        return bool(await client.ping())
    except Exception as exc:
        logger.debug("Redis health check failed: {}", exc)
        return False


def register_health_checks() -> None:
    """Register connectivity probes used during startup."""
    from src.utils.health import register_health_check

    register_health_check("postgres", check_postgres)
    register_health_check("redis", check_redis)


async def initialize_neo4j() -> None:
    """Ensure graph indexes and lowercase search fields exist."""
    repository = _neo4j_repository
    if repository is None:
        return
    try:
        await repository.ensure_indexes()
        logger.info("Neo4j indexes and lowercase fields ready")
    except Exception as exc:
        logger.warning("Neo4j index initialization failed: {}", exc)


async def acquire_startup_lock() -> bool:
    """Acquire a PostgreSQL advisory lock for startup initialization.

    Uses a raw connection (not returned to pool) so the lock persists for the
    duration of the startup phase. Advisory locks are session-scoped and are
    released automatically when the connection closes.

    Returns True when this worker should run recovery, False when another
    worker holds the lock, and True for engines without advisory locks.
    """
    global _startup_lock_raw_conn
    engine = get_engine()
    if engine is None:
        return False
    try:
        raw_conn = await engine.raw_connection()
        try:
            result = await raw_conn.exec_driver_sql(
                "SELECT pg_try_advisory_lock(hashtext('lingua_seeker_backend_startup'))"
            )
            row = result.fetchone()
            acquired = bool(row[0]) if row else False
        except Exception:
            await raw_conn.close()
            return True

        if acquired:
            _startup_lock_raw_conn = raw_conn
        else:
            await raw_conn.close()
        return acquired
    except Exception:
        return True


async def release_startup_lock() -> None:
    """Release the startup advisory lock by closing its raw connection."""
    global _startup_lock_raw_conn
    if _startup_lock_raw_conn is not None:
        try:
            await _startup_lock_raw_conn.close()
        except Exception:
            pass
        _startup_lock_raw_conn = None


def get_local_parser() -> MinerULocalParser | None:
    """Return the singleton MinerU local parser (or None if not yet initialized)."""
    return _local_parser


def get_dispatcher() -> SingleJobDispatcher | None:
    """Return the singleton job dispatcher (or None if not yet initialized)."""
    return _dispatcher


def _configure_lit_acquisition(cfg: Settings) -> None:
    """Bridge backend configuration into the lit-acquisition SDK.

    The SDK keeps its own process-wide config (LLM keys for the relevance
    gate and query translation, web-search adapter keys, outbound proxy)
    which it otherwise loads from ``LIT_*`` environment variables.  The
    backend YAML config is the single source of truth, so mirror the
    relevant domains into the SDK once at startup.
    """
    from lit_acquisition import configure as configure_lit_acquisition

    configure_lit_acquisition(
        llm_base_url=cfg.llm.base_url,
        llm_model=cfg.llm.model,
        llm_api_key=cfg.llm.api_key,
        llm_api_keys=list(cfg.llm.api_keys),
        llm_max_tokens=cfg.llm.max_tokens,
        translation_base_url=cfg.translation.base_url,
        translation_model=cfg.translation.model,
        translation_api_key=cfg.translation.api_key,
        translation_api_keys=list(cfg.translation.api_keys),
        firecrawl_api_key=cfg.web_search.firecrawl_api_key,
        tavily_api_key=cfg.web_search.tavily_api_key,
        serpapi_api_key=cfg.web_search.serpapi_api_key,
        proxy=cfg.network.proxy,
        no_proxy=cfg.network.no_proxy,
    )


def wire_dependencies() -> None:
    """Assemble and inject all application dependencies.

    Called once from lifespan startup.  Creates the full service graph:
    engine → session_factory → adapters → orchestrator → runner → factory.
    """
    from src.runs import (
        PipelineRunner,
        PipelineSemaphore,
        RetryablePhaseExecutor,
        SingleJobDispatcher,
    )
    from src.dao.postgresql.review.store_factory import PostgresReviewStoreFactory
    from src.pipeline.skills.review.factory import ReviewServiceFactory
    from src.dao.postgresql.run_state_store import PostgresRunStateStore
    from src.api.deps import set_review_factory
    from src.api.v1.pipeline import set_pipeline_runner
    from src.pipeline.skills.graph_retrieval.api import GraphRagService
    from src.core.tools.parsing.local.parser import (
        MinerULocalParser,
    )
    from src.core.tools.parsing.orchestrator import (
        DocumentParseOrchestrator,
    )
    from src.core.tools.parsing.remote.parser import (
        MinerURemoteParser,
    )
    from src.core.tools.parsing.service import (
        ParseDocumentService,
    )
    from src.dao.postgresql.standardization.runner import PostgresStandardizationRunner
    from src.pipeline.graph.phases.acquisition import AcquisitionAdapter
    from src.pipeline.graph.phases.parsing import ParsingAdapter
    from src.pipeline.graph.phases.fact_chain import FactChainAdapter
    from src.pipeline.graph.phases.standardization import StandardizationAdapter
    from src.pipeline.graph.topology import PipelineOrchestrator
    from src.pipeline.skills.acquisition.service import AcquisitionSkill
    from src.pipeline.skills.extraction.service import SourceFactChainService
    from src.pipeline.skills.parsing.service import ParsingSkill
    from src.pipeline.skills.standardization.service import StandardizationSkill

    global _engine, _session_factory, _redis_client, _local_parser, _dispatcher, _neo4j_driver, _neo4j_repository

    cfg = get_config()

    # ── lit-acquisition SDK (online literature acquisition) ──────────
    _configure_lit_acquisition(cfg)

    # ── Redis client singleton ───────────────────────────────────────
    _redis_client = build_redis_client(cfg)

    # ── Persistence backend ──────────────────────────────────────────
    backend = cfg.persistence_backend
    if backend == "memory":
        from src.dao.memory import InMemoryProcessingCache, InMemoryRunStateStore

        _engine = None
        _session_factory = cast("async_sessionmaker[AsyncSession]", _UnavailableSessionFactory())
        persistence = InMemoryRunStateStore()
        processing_cache = InMemoryProcessingCache()
        logger.warning(
            "Persistence backend=memory: run state/cache are process-local; "
            "DB-backed features return 503"
        )
    else:
        if _engine is None:
            _engine = build_async_engine(cfg)
        if _session_factory is None:
            _session_factory = async_session_factory(_engine)
        from src.dao.postgresql.processing_cache import PostgresProcessingCache

        session_factory = get_session_factory()
        persistence = PostgresRunStateStore(session_factory)
        processing_cache = PostgresProcessingCache(
            redis_client=_redis_client,
            session_factory=session_factory,
        )

    session_factory = get_session_factory()

    # ── Neo4j driver/repository singleton (optional) ──────────────────
    if _neo4j_driver is None:
        try:
            _neo4j_driver = build_neo4j_driver(cfg)
            _neo4j_repository = Neo4jRepository(
                _neo4j_driver,
                database=cfg.neo4j.database,
            )
        except Exception as exc:
            logger.warning("Neo4j unavailable ({}); graph features are disabled", exc)
            _neo4j_driver = None
            _neo4j_repository = None

    # ── Document processing cache is built with the persistence backend above.

    session_factory = get_session_factory()

    # ── Phase 1-4 services (long-lived, no session in constructor) ──

    acquisition_skill = AcquisitionSkill(cfg=cfg)
    pd_cfg = cfg.parse_document
    remote_parser = MinerURemoteParser(
        api_token=cfg.mineru_api_token,
        poll_interval=pd_cfg.mineru_remote_poll_interval,
        max_poll_attempts=pd_cfg.mineru_remote_max_poll_attempts,
    )
    _local_parser = MinerULocalParser(
        parse_url=pd_cfg.mineru_local_parse_url,
        model_id=pd_cfg.mineru_local_model_id,
        timeout=pd_cfg.mineru_local_timeout,
        dpi=pd_cfg.mineru_local_dpi,
        api_key=cfg.inference_api_key,
    )
    parse_orchestrator = DocumentParseOrchestrator(remote=remote_parser, local=_local_parser)
    parse_service = ParseDocumentService(parse_orchestrator)
    parsing_skill = ParsingSkill(cfg=cfg, service=parse_service)
    graph_rag_service = (
        GraphRagService(
            _neo4j_repository,
            writer=Neo4jGraphProvider(_neo4j_repository),
        )
        if _neo4j_repository is not None
        else None
    )
    source_fact_chain = SourceFactChainService(cfg=cfg)
    standardization_service = PostgresStandardizationRunner(
        cfg=cfg,
        session_factory=session_factory,
        graph_rag_service=graph_rag_service,
    )

    standardization_skill = StandardizationSkill(cfg=cfg, runner=standardization_service)

    # ── Phase adapters ──

    phase_adapters = {
        "acquisition": AcquisitionAdapter(acquisition_skill),
        "parsing": ParsingAdapter(parsing_skill),
        "fact_chain": FactChainAdapter(source_fact_chain),
        "standardization": StandardizationAdapter(standardization_skill),
    }

    # ── Orchestrator + Runner ──

    retry_executor = RetryablePhaseExecutor(max_retries=2, backoff_base=30.0)

    orchestrator = PipelineOrchestrator(
        phase_adapters=phase_adapters,
        state_persistence=persistence,
        retry_executor=retry_executor,
    )

    semaphore = PipelineSemaphore(max_concurrent=2)
    runner = PipelineRunner(
        orchestrator=orchestrator,
        semaphore=semaphore,
        state_persistence=persistence,
        processing_cache=processing_cache,
        processing_cache_enabled=cfg.pipeline.cache_enabled,
        duplicate_run_prevention_enabled=cfg.pipeline.dedup_enabled,
        heartbeat_interval_seconds=cfg.pipeline_heartbeat_interval,
    )
    # Let the orchestrator push intermediate state updates to the runner's
    # in-memory cache so the status endpoint reflects phase progress in
    # real time (not just after the entire pipeline completes).
    orchestrator.on_state_change = runner.remember_state

    # ── Phase 5 factory (interactive review layer) ──

    review_factory = ReviewServiceFactory(stores=PostgresReviewStoreFactory(session_factory))

    # ── Job queue + dispatcher ──

    from src.api.v1.pipeline import set_job_queue

    job_queue: RunJobQueue
    if backend == "memory":
        from src.dao.memory import InMemoryAgentJobStore, InMemoryRunJobQueue

        job_queue = InMemoryRunJobQueue()
        set_agent_job_store(InMemoryAgentJobStore())
    else:
        from src.dao.postgresql.agent_jobs import AgentJobRepository

        job_queue = JobQueueRepository(session_factory)
        set_agent_job_store(AgentJobRepository(session_factory))
    _dispatcher = SingleJobDispatcher(
        runner=runner,
        job_queue=job_queue,
        poll_interval=cfg.dispatcher_poll_interval,
        idle_max_interval=cfg.dispatcher_idle_max_interval,
    )

    # ── Inject into global registries (consumed by API routes) ──

    set_pipeline_runner(runner)
    set_review_factory(review_factory)
    set_job_queue(job_queue)
