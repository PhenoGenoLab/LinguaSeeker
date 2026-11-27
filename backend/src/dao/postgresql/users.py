"""PostgreSQL adapter for the user directory."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.dao.postgresql.models import User
from src.ports.users import UserAlreadyExistsError, UserRecord


def _record(user: User | None) -> UserRecord | None:
    if user is None:
        return None
    return UserRecord(
        user_id=user.user_id,
        username=user.username,
        password_hash=user.password_hash,
        display_name=user.display_name,
        status=user.status,
    )


class PostgresUserStore:
    """One session per operation; writes commit inside the adapter."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_by_username(self, username: str) -> UserRecord | None:
        async with self._session_factory() as session:
            result = await session.execute(select(User).where(User.username == username))
            return _record(result.scalar_one_or_none())

    async def get_by_id(self, user_id: UUID) -> UserRecord | None:
        async with self._session_factory() as session:
            result = await session.execute(select(User).where(User.user_id == user_id))
            return _record(result.scalar_one_or_none())

    async def create(
        self,
        *,
        username: str,
        password_hash: str,
        display_name: str | None,
        status: str = "active",
    ) -> UserRecord:
        user = User(
            username=username,
            password_hash=password_hash,
            display_name=display_name,
            status=status,
        )
        async with self._session_factory() as session:
            session.add(user)
            try:
                await session.flush()
                await session.commit()
            except IntegrityError as exc:
                await session.rollback()
                raise UserAlreadyExistsError(username) from exc
        return UserRecord(
            user_id=user.user_id,
            username=user.username,
            password_hash=user.password_hash,
            display_name=user.display_name,
            status=user.status,
        )
