"""Stage adapters for the pipeline graph.

Each adapter owns one stage's assembly, error classification and state writes;
the underlying domain service stays outside the graph layer.

- ``acquisition.py``: literature and document acquisition
- ``parsing.py``: document parsing (MinerU)
- ``fact_chain.py``: extraction -> verification -> fact English
- ``standardization.py``: entity standardization and knowledge alignment
"""
