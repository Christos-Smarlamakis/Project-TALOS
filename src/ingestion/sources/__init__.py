# -*- coding: utf-8 -*-
"""
Module: __init__.py
Project: TALOS v5.15.3
Description:
    Package root for the modular 18-source academic ingestion mesh. Exposes the
    unified ``SOURCE_REGISTRY`` mapping every source key (e.g., ``arxiv``) to its
    adapter class (e.g., ``ArxivSource``), plus the ordered ``ALL_SOURCE_NAMES``
    list. Downstream orchestrators (``daily_search.py``, ``historic_search.py``)
    and the DRL live agent import from this single canonical registry so that the
    18-adapter set is defined in exactly one place.

    Key design decisions:
    - One source module per provider under ``src/ingestion/sources/``.
    - ``SOURCE_REGISTRY`` preserves the canonical ordering used by the checkbox
      TUI, the ``--sources`` filter, and the visualizer source health map.
    - Importing this package performs no network I/O; adapters are constructed
      lazily by callers via ``cls(config)``.

Dependencies:
    - src.ingestion.sources.*_source: The 18 provider adapter modules.
"""
from src.ingestion.sources.arxiv_source import ArxivSource
from src.ingestion.sources.core_source import CORESource
from src.ingestion.sources.crossref_source import CrossrefSource
from src.ingestion.sources.dblp_source import DBLPSource
from src.ingestion.sources.elsevier_source import ElsevierSource
from src.ingestion.sources.hal_inria_source import HalInriaSource
from src.ingestion.sources.ieee_source import IEEEXploreSource
from src.ingestion.sources.nasa_ntrs_source import NasaNtrsSource
from src.ingestion.sources.openaire_source import OpenAIRESource
from src.ingestion.sources.openalex_source import OpenAlexSource
from src.ingestion.sources.openarchives_source import OpenArchivesSource
from src.ingestion.sources.openreview_source import OpenReviewSource
from src.ingestion.sources.osti_source import OSTISource
from src.ingestion.sources.plos_source import PLOSSource
from src.ingestion.sources.pubmed_source import PubMedSource
from src.ingestion.sources.scigov_source import ScienceGovSource
from src.ingestion.sources.semantic_scholar_source import SemanticScholarSource
from src.ingestion.sources.springer_source import SpringerNatureSource

# -- v5.15.0: Unified canonical 18-source registry. --
SOURCE_REGISTRY = [
    ("arxiv", ArxivSource),
    ("ieee", IEEEXploreSource),
    ("semantic_scholar", SemanticScholarSource),
    ("springer", SpringerNatureSource),
    ("openalex", OpenAlexSource),
    ("dblp", DBLPSource),
    ("elsevier", ElsevierSource),
    ("core", CORESource),
    ("crossref", CrossrefSource),
    ("openarchives", OpenArchivesSource),
    ("pubmed", PubMedSource),
    ("scigov", ScienceGovSource),
    ("osti", OSTISource),
    ("plos", PLOSSource),
    ("openreview", OpenReviewSource),
    ("openaire", OpenAIRESource),
    ("nasa_ntrs", NasaNtrsSource),
    ("hal_inria", HalInriaSource),
]

ALL_SOURCE_NAMES = [name for name, _ in SOURCE_REGISTRY]

__all__ = [
    "SOURCE_REGISTRY",
    "ALL_SOURCE_NAMES",
    "ArxivSource",
    "IEEEXploreSource",
    "SemanticScholarSource",
    "SpringerNatureSource",
    "OpenAlexSource",
    "DBLPSource",
    "ElsevierSource",
    "CORESource",
    "CrossrefSource",
    "OpenArchivesSource",
    "PubMedSource",
    "ScienceGovSource",
    "OSTISource",
    "PLOSSource",
    "OpenReviewSource",
    "OpenAIRESource",
    "NasaNtrsSource",
    "HalInriaSource",
]
