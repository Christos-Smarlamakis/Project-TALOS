# -*- coding: utf-8 -*-
"""
Module: live_agent_sources.py (v1.1)
Project: TALOS v5.10.1
Description:
    Source discovery and management for the TALOS Live DRL Agent.
    Handles auto-detection of configured API sources from config.json,
    dynamic import of source classes, and building a dense action mapping.

    Extracted from talos_live_agent.py v2.1 to enable reuse across
    the live agent, the 24/7 daemon (talos_service.py), and tests.

    Key design decisions:
    - Sources are auto-detected from config.json keys ending in "_query".
    - Class names are found by scanning the module for any class ending
      in "Source" (handles mixed naming: DBLP→DBLPSource, IEEE→IEEEXploreSource).
    - Dense mapping: only successfully imported sources get indices (0,1,2,...).
      No gaps = agent never picks an invalid action.
"""


def import_source_class(source_name):
    """
    Dynamically import a source class from the ingestion package.

    The 16 source modules follow two naming conventions: 14 use a `_source`
    suffix (e.g. `arxiv_source.py`) while the v5.10.0 additions (`openaire.py`,
    `openreview.py`) do not. This function first tries the suffixed module and
    falls back to the unsuffixed name when the suffixed module does not exist,
    so all 16 sources resolve and the DRL agent's state space keeps its full
    dimensionality.

    Args:
        source_name (str): Source key (e.g., "arxiv", "openaire", "openreview").

    Returns:
        class or None: The source class, or None if import fails.
    """
    suffixed_name = f"src.ingestion.{source_name}_source"
    try:
        module = __import__(suffixed_name, fromlist=["*"])
    except ModuleNotFoundError:
        # -- Fallback: v5.10.0 sources (openaire, openreview) have no suffix --
        fallback_name = f"src.ingestion.{source_name}"
        try:
            module = __import__(fallback_name, fromlist=["*"])
        except ImportError as e:
            print(f"  [WARN] Could not import module {fallback_name}: {e}")
            return None
    except ImportError as e:
        print(f"  [WARN] Could not import module {suffixed_name}: {e}")
        return None

    # -- Find any class in the module that ends with "Source" --
    for attr_name in dir(module):
        if attr_name.endswith("Source") and not attr_name.startswith("_"):
            cls = getattr(module, attr_name, None)
            if isinstance(cls, type):
                return cls

    # -- Fallback: try the naive .capitalize() guessing --
    class_parts = [part.capitalize() for part in source_name.split("_")]
    class_name = "".join(class_parts) + "Source"
    cls = getattr(module, class_name, None)
    if cls is not None:
        return cls

    print(f"  [WARN] No *Source class found for source '{source_name}'")
    return None


def build_source_map(source_names):
    """
    Build a DENSE action→(name, class) mapping for all WORKING sources only.

    Only sources that can be successfully imported get an action index.
    Indices are contiguous starting from 0 (no gaps), so the DRL agent
    never picks an action that maps to nothing.

    Args:
        source_names (list of str): Ordered source names from config.

    Returns:
        tuple: (dense_action_map, working_source_names)
            dense_action_map (dict): {0: (name, cls), 1: (name, cls), ...}
            working_source_names (list of str): Only the source names that
                could be imported, in order.
    """
    dense_map = {}
    working_names = []
    for name in source_names:
        cls = import_source_class(name)
        if cls is not None:
            dense_map[len(working_names)] = (name, cls)
            working_names.append(name)
    return dense_map, working_names