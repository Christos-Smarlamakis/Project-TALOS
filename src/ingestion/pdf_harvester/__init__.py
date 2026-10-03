# -*- coding: utf-8 -*-
"""
Module: __init__.py (src/ingestion/pdf_harvester)
Project: TALOS v5.18.4
Description:
    Package marker for the Ethical Academic PDF Harvester subsystem. This package
    houses the three modular layers of legal, air-gapped full-text acquisition:

    1. ``resolvers.py``  -- the cascading Open Access and preprint URL resolver.
    2. ``harvester.py``  -- the download pipeline with magic-bytes validation,
       atomic writes, SHA-256 integrity hashing, polite rate limiting, and the
       per-candidate SQLite persistence of ``local_pdf_path`` / ``pdf_sha256`` /
       ``pdf_status``.
    3. ``section_extractor.py`` -- local PDF text extraction and smart section
       slicing that caches Methodology, Experiments, Code Availability, and
       Limitations text windows for the Tier-2 Quality Swarm.

    Key design decisions:
    - Operates strictly under EU Directive 2019/790 (Text and Data Mining)
      Articles 3 and 4: only legally accessible Open Access and preprint
      material is resolved and downloaded, with a polite academic User-Agent
      and a 1.5 second inter-request delay.
    - All downloaded artefacts are confined to the gitignored
      ``data/fulltext_cache/`` directory and never leave the local machine.
    - No telemetry, no analytics, and no phoning home.

Dependencies:
    - src.ingestion.pdf_harvester.resolvers: Open Access URL cascade.
    - src.ingestion.pdf_harvester.harvester: fault-tolerant download pipeline.
    - src.ingestion.pdf_harvester.section_extractor: local text extraction.
"""
from src.ingestion.pdf_harvester.resolvers import resolve_oa_url
from src.ingestion.pdf_harvester.harvester import AcademicPDFHarvester
from src.ingestion.pdf_harvester.section_extractor import PDFSectionExtractor

__all__ = [
    "resolve_oa_url",
    "AcademicPDFHarvester",
    "PDFSectionExtractor",
]
