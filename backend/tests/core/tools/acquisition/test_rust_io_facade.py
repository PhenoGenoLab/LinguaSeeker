"""Regression tests for the rust_io Python facade."""

import hashlib

import pytest

import rust_io.files as files
import rust_io.net as net_io


def test_net_io_facade_exports_provider_functions():
    for name in (
        "fetch_one",
        "fetch_multi",
        "scrape_web",
        "scrape_html",
        "extract_pdf_links",
        "mineru_create_task",
        "mineru_get_result",
        "mineru_batch_submit",
        "mineru_batch_result",
        "mineru_create_upload_url",
        "mineru_create_batch_upload_urls",
        "mineru_upload_local_file",
        "mineru_upload_local_files",
    ):
        assert hasattr(net_io, name)


def test_files_facade_preserves_legacy_helpers(tmp_path):
    path = tmp_path / "sample.bin"

    files.write_file(str(path), b"abc")

    assert path.read_bytes() == b"abc"
    assert files.compute_sha256(str(path)) == hashlib.sha256(b"abc").hexdigest()
    assert files.validate_pdf_magic(b"%PDF-1.7") is True
    assert files.validate_pdf_magic(b"not a pdf") is False


def test_files_facade_exports_files_io_functions():
    for name in (
        "File",
        "batch_copy",
        "batch_compress",
        "batch_copy_async",
        "check_duplicate",
        "batch_hash",
    ):
        assert hasattr(files, name)


def test_submodule_names_are_fully_qualified():
    assert net_io.__name__ == "rust_io.net"
    assert files.__name__ == "rust_io.files"


def test_file_write_accepts_str_and_buffer_types(tmp_path):
    path = tmp_path / "nested" / "sample.txt"
    handle = files.File(str(path))

    assert handle.path == str(path)
    assert "sample.txt" in repr(handle)

    handle.write("hello")
    assert path.read_bytes() == b"hello"
    assert handle.read(as_text=True) == "hello"

    handle.write(bytearray(b"world"))
    assert path.read_bytes() == b"world"
    assert handle.content_hash() == hashlib.sha256(b"world").hexdigest()


def test_batch_hash_reports_hashes_and_missing_files(tmp_path):
    present = tmp_path / "present.bin"
    present.write_bytes(b"abc")
    missing = tmp_path / "missing.bin"

    result = files.batch_hash([str(present), str(missing)])

    assert result["hashes"][str(present)] == hashlib.sha256(b"abc").hexdigest()
    assert str(missing) in result["errors"]


@pytest.mark.asyncio
async def test_net_io_fetch_multi_returns_failure_per_unknown_provider():
    results = await net_io.fetch_multi(["missing_a", "missing_b"], "search", {})

    assert [result["provider"] for result in results] == ["missing_a", "missing_b"]
    assert [result["success"] for result in results] == [False, False]
    assert all(result["warnings"] for result in results)


@pytest.mark.asyncio
async def test_unpaywall_requires_configured_email(monkeypatch):
    monkeypatch.delenv("UNPAYWALL_EMAIL", raising=False)

    result = await net_io.fetch_one(
        "unpaywall",
        "search",
        {"identifiers": {"doi": "10.1234/example"}},
        timeout_ms=100,
        max_retries=0,
        proxy="http://127.0.0.1:1",
    )

    assert result["success"] is False
    assert result["warnings"] == ["unpaywall_requires_email"]
