"""Tests for the startup advisory lock connection lifecycle."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture(autouse=True)
def reset_lock_global():
    """Reset module-level global between tests to prevent stale state."""
    import src.api.wiring as wiring

    wiring._startup_lock_raw_conn = None
    yield
    wiring._startup_lock_raw_conn = None


@pytest.mark.asyncio
async def test_startup_lock_closes_connection_on_sql_error():
    """raw_conn must be closed even when SQL execution fails."""
    from src.api.wiring import acquire_startup_lock

    mock_engine = MagicMock()
    mock_conn = MagicMock()
    mock_conn.exec_driver_sql = AsyncMock(side_effect=RuntimeError("SQL failed"))
    mock_conn.close = AsyncMock()
    mock_engine.raw_connection = AsyncMock(return_value=mock_conn)

    with patch("src.api.wiring.get_engine", return_value=mock_engine):
        result = await acquire_startup_lock()

    assert result is True
    mock_conn.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_startup_lock_closes_connection_when_not_acquired():
    """raw_conn must be closed when advisory lock is not acquired."""
    from src.api.wiring import acquire_startup_lock

    mock_engine = MagicMock()
    mock_conn = MagicMock()
    mock_result = MagicMock()
    mock_result.fetchone.return_value = (False,)
    mock_conn.exec_driver_sql = AsyncMock(return_value=mock_result)
    mock_conn.close = AsyncMock()
    mock_engine.raw_connection = AsyncMock(return_value=mock_conn)

    with patch("src.api.wiring.get_engine", return_value=mock_engine):
        result = await acquire_startup_lock()

    assert result is False
    mock_conn.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_startup_lock_keeps_connection_when_acquired():
    """raw_conn must NOT be closed when advisory lock is acquired."""
    from src.api.wiring import acquire_startup_lock

    mock_engine = MagicMock()
    mock_conn = MagicMock()
    mock_result = MagicMock()
    mock_result.fetchone.return_value = (True,)
    mock_conn.exec_driver_sql = AsyncMock(return_value=mock_result)
    mock_conn.close = AsyncMock()
    mock_engine.raw_connection = AsyncMock(return_value=mock_conn)

    with patch("src.api.wiring.get_engine", return_value=mock_engine):
        result = await acquire_startup_lock()

    assert result is True
    mock_conn.close.assert_not_awaited()
