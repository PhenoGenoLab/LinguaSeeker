"""Document parse orchestrator backed only by the remote MinerU parser."""

from __future__ import annotations

from .base import ParserStrategy
from .contracts import MinerULocalBatchOptions, MinerULocalBatchParseResult, ParseResult


class DocumentParseOrchestrator(ParserStrategy):
    """Delegate parsing to the remote MinerU service.

    There is no local VLM fallback: a remote failure is surfaced to the
    pipeline so it can retry or fail the phase explicitly.
    """

    def __init__(self, remote: ParserStrategy):
        self._remote = remote

    @property
    def name(self) -> str:
        return "orchestrator"

    async def parse(self, pdf_path: str) -> ParseResult:
        """Parse a PDF through the remote MinerU parser."""
        return await self._remote.parse(pdf_path)

    async def parse_local_files(
        self,
        file_paths: list[str],
        *,
        options: MinerULocalBatchOptions,
    ) -> MinerULocalBatchParseResult:
        """Delegate batch local-file parsing to the remote MinerU parser."""
        parser = getattr(self._remote, "parse_local_files", None)
        if parser is None:
            raise AttributeError(f"Remote parser '{self._remote.name}' does not support parse_local_files")
        return await parser(file_paths, options=options)
