"""Neo4j data access layer."""

from src.dao.neo4j.connection import build_neo4j_driver
from src.dao.neo4j.repository import Neo4jRepository

__all__ = [
    "build_neo4j_driver",
    "Neo4jRepository",
]
