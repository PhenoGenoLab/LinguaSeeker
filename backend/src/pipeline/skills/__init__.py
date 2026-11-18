"""Bounded agents built on AgentScope.

Import boundary: skills must not import database drivers or ORM/session
modules (SQLAlchemy, Neo4j, asyncpg, psycopg, sqlite3, ``src.dao``).  All reads
and writes go through ``src.pipeline.tools`` or the outer service layer.
"""
