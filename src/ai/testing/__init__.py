# -*- coding: utf-8 -*-
"""
Module: __init__.py
Project: TALOS v5.9.4
Description:
    Package initializer for the Autonomous System Tester (RL-Driven Chaos Engineering)
    subpackage. Provides the non-stationary multi-armed bandit testing daemon that
    stress-tests TALOS system components via subprocess execution with LLM-as-a-Judge
    diagnostics and Synapse event emission.

    Exports the run_autonomous_tester() entry point for import by talos.py menu
    launcher and the tester_routes.py API router.

Dependencies:
    - .autonomous_tester: Core testing daemon with MAB, rich TUI, and LLM diagnostics.
"""
from .autonomous_tester import run_autonomous_tester

__all__ = ["run_autonomous_tester"]
