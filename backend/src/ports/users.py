"""User directory port (auth and review ownership)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True)
class UserRecord:
    """A user row without persistence dependencies."""

    user_id: UUID
    username: str
    password_hash: str
    display_name: str | None
    status: str


class UserAlreadyExistsError(Exception):
    """Raised when a username is taken."""


class UserStore(Protocol):
    """Read and create users."""

    async def get_by_username(self, username: str) -> UserRecord | None: ...

    async def get_by_id(self, user_id: UUID) -> UserRecord | None: ...

    async def create(
        self,
        *,
        username: str,
        password_hash: str,
        display_name: str | None,
        status: str = "active",
    ) -> UserRecord: ...
