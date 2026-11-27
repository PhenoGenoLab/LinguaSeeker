"""Tests for parse_document exceptions."""

from __future__ import annotations

from src.core.tools.parsing.exceptions import (
    MinerUAPIError,
    MinerUTimeoutError,
    ParseDocumentError,
)


class TestParseDocumentError:
    def test_base_exception(self):
        err = ParseDocumentError("test error")
        assert str(err) == "test error"
        assert isinstance(err, Exception)


class TestMinerUAPIError:
    def test_with_status_code(self):
        err = MinerUAPIError("API failed", status_code=500)
        assert err.status_code == 500
        assert "API failed" in str(err)

    def test_without_status_code(self):
        err = MinerUAPIError("API failed")
        assert err.status_code is None


class TestMinerUTimeoutError:
    def test_timeout(self):
        err = MinerUTimeoutError(total_timeout=300)
        assert err.total_timeout == 300
        assert "300" in str(err)
