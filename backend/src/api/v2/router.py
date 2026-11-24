"""Router for the v2 API (directory runs + standalone agent jobs)."""

from __future__ import annotations

from fastapi import APIRouter

from src.api.v2.agents import router as agents_router
from src.api.v2.runs import router as runs_router

router = APIRouter()
router.include_router(runs_router)
router.include_router(agents_router)
