"""Tests for wiring config propagation to parsers."""

from __future__ import annotations

from contextlib import ExitStack
from unittest.mock import MagicMock, patch

from src.core.config import ParseDocumentConfig

# Source module paths for classes imported inside wire_dependencies()
_REMOTE_PARSER_MOD = "src.core.tools.parsing.remote.parser.MinerURemoteParser"
_LOCAL_PARSER_MOD = "src.core.tools.parsing.local.parser.MinerULocalParser"


def _patch_wire_deps(stack: ExitStack):
    """Patch all dependencies wired inside wire_dependencies()."""
    for mod_path in [
        "src.core.tools.acquisition.service.DocumentAcquisitionService",
        "src.core.tools.parsing.orchestrator.DocumentParseOrchestrator",
        "src.core.tools.parsing.service.ParseDocumentService",
        "src.pipeline.skills.extraction.service.SourceFactChainService",
        "src.pipeline.skills.standardization.api.EntityStandardizationService",
        "src.pipeline.graph.topology.PipelineOrchestrator",
        "src.runs.PipelineSemaphore",
        "src.runs.RetryablePhaseExecutor",
        "src.runs.PipelineRunner",
        "src.dao.postgresql.run_state_store.PostgresRunStateStore",
        "src.pipeline.graph.phases.acquisition.AcquisitionAdapter",
        "src.pipeline.graph.phases.parsing.ParsingAdapter",
        "src.pipeline.graph.phases.fact_chain.FactChainAdapter",
        "src.pipeline.graph.phases.standardization.StandardizationAdapter",
        "src.pipeline.skills.review.factory.ReviewServiceFactory",
        "src.api.v1.pipeline.set_pipeline_runner",
        "src.api.deps.set_review_factory",
        "src.api.wiring.get_session_factory",
        "src.api.wiring.build_async_engine",
        "src.api.wiring.async_session_factory",
        "src.api.wiring._configure_lit_acquisition",
        "src.api.wiring.build_redis_client",
        "src.api.wiring.build_neo4j_driver",
        "src.api.wiring.Neo4jRepository",
    ]:
        stack.enter_context(patch(mod_path))


def test_remote_parser_receives_all_config():
    """MinerURemoteParser should receive poll_interval and max_poll_attempts."""
    from src.core.config import get_config

    get_config.cache_clear()

    pd = ParseDocumentConfig(
        mineru_remote_poll_interval=3.0,
        mineru_remote_max_poll_attempts=200,
        mineru_local_parse_url="http://localhost:8002",
        mineru_local_model_id="test-model",
        mineru_local_timeout=60.0,
        mineru_local_dpi=300,
    )

    with ExitStack() as stack:
        _patch_wire_deps(stack)
        mock_remote = stack.enter_context(patch(_REMOTE_PARSER_MOD))
        stack.enter_context(patch(_LOCAL_PARSER_MOD))
        mock_cfg = stack.enter_context(patch("src.api.wiring.get_config"))

        cfg = MagicMock()
        cfg.parse_document = pd
        cfg.mineru_api_token = "test-token"
        mock_cfg.return_value = cfg

        from src.api.wiring import wire_dependencies

        wire_dependencies()

        _, kwargs = mock_remote.call_args
        assert kwargs.get("api_token") == "test-token"
        assert kwargs.get("poll_interval") == 3.0
        assert kwargs.get("max_poll_attempts") == 200


def test_local_parser_receives_all_config():
    """MinerULocalParser should receive parse_url, model_id, timeout, dpi."""
    from src.core.config import get_config

    get_config.cache_clear()

    pd = ParseDocumentConfig(
        mineru_remote_poll_interval=2.0,
        mineru_remote_max_poll_attempts=150,
        mineru_local_parse_url="http://localhost:8002",
        mineru_local_model_id="test-model-id",
        mineru_local_timeout=60.0,
        mineru_local_dpi=300,
    )

    with ExitStack() as stack:
        _patch_wire_deps(stack)
        stack.enter_context(patch(_REMOTE_PARSER_MOD))
        mock_local = stack.enter_context(patch(_LOCAL_PARSER_MOD))
        mock_cfg = stack.enter_context(patch("src.api.wiring.get_config"))

        cfg = MagicMock()
        cfg.parse_document = pd
        cfg.mineru_api_token = ""
        mock_cfg.return_value = cfg

        from src.api.wiring import wire_dependencies

        wire_dependencies()

        _, kwargs = mock_local.call_args
        assert kwargs.get("parse_url") == "http://localhost:8002"
        assert kwargs.get("model_id") == "test-model-id"
        assert kwargs.get("timeout") == 60.0
        assert kwargs.get("dpi") == 300


def test_wire_dependencies_initializes_session_factory_before_use():
    """wire_dependencies should create the DB session factory during startup."""
    from src.core.config import get_config

    get_config.cache_clear()

    pd = ParseDocumentConfig(
        mineru_remote_poll_interval=2.0,
        mineru_remote_max_poll_attempts=150,
        mineru_local_parse_url="http://localhost:8002",
        mineru_local_model_id="test-model-id",
        mineru_local_timeout=60.0,
        mineru_local_dpi=300,
    )

    import src.api.wiring as wiring

    wiring._engine = None
    wiring._session_factory = None
    fake_engine = MagicMock(name="fake_engine")
    fake_session_factory = MagicMock(name="fake_session_factory")

    with ExitStack() as stack:
        for mod_path in [
            "src.core.tools.acquisition.service.DocumentAcquisitionService",
            "src.core.tools.parsing.orchestrator.DocumentParseOrchestrator",
            "src.core.tools.parsing.service.ParseDocumentService",
            "src.pipeline.skills.translation.api.TranslationService",
            "src.pipeline.skills.extraction.api.EvidenceExtractionService",
            "src.pipeline.skills.standardization.api.EntityStandardizationService",
            "src.pipeline.graph.topology.PipelineOrchestrator",
            "src.runs.PipelineSemaphore",
            "src.runs.RetryablePhaseExecutor",
            "src.runs.PipelineRunner",
            "src.dao.postgresql.run_state_store.PostgresRunStateStore",
            "src.pipeline.graph.phases.acquisition.AcquisitionAdapter",
            "src.pipeline.graph.phases.parsing.ParsingAdapter",
            "src.pipeline.graph.phases.fact_chain.FactChainAdapter",
            "src.pipeline.graph.phases.standardization.StandardizationAdapter",
            "src.pipeline.skills.review.factory.ReviewServiceFactory",
            "src.dao.postgresql.processing_cache.PostgresProcessingCache",
            "src.dao.postgresql.job_queue.JobQueueRepository",
            "src.runs.SingleJobDispatcher",
            "src.api.v1.pipeline.set_pipeline_runner",
            "src.api.v1.pipeline.set_job_queue",
            "src.api.deps.set_review_factory",
            "src.api.wiring._configure_lit_acquisition",
            "src.api.wiring.build_redis_client",
            "src.api.wiring.build_neo4j_driver",
            "src.api.wiring.Neo4jRepository",
        ]:
            stack.enter_context(patch(mod_path))
        stack.enter_context(patch(_REMOTE_PARSER_MOD))
        stack.enter_context(patch(_LOCAL_PARSER_MOD))
        mock_cfg = stack.enter_context(patch("src.api.wiring.get_config"))
        mock_engine = stack.enter_context(
            patch("src.api.wiring.build_async_engine", return_value=fake_engine, create=True)
        )
        mock_session_factory = stack.enter_context(
            patch("src.api.wiring.async_session_factory", return_value=fake_session_factory, create=True)
        )

        cfg = MagicMock()
        cfg.parse_document = pd
        cfg.mineru_api_token = ""
        cfg.inference_api_key = ""
        mock_cfg.return_value = cfg

        wiring.wire_dependencies()

    mock_engine.assert_called_once_with(cfg)
    mock_session_factory.assert_called_once_with(fake_engine)
    assert wiring.get_session_factory() is fake_session_factory
