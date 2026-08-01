# -*- coding: utf-8 -*-
"""
Module: __init__.py
Project: TALOS v5.9.0
Description:
    Package initializer for the Autonomous System Tester (RL-Driven Chaos Engineering)
    subpackage. Provides the non-stationary multi-armed bandit testing daemon that
    stress-tests TALOS system components via subprocess execution with LLM-as-a-Judge
    diagnostics and Synapse event emission.

    Exports the AutonomousTester class for import by talos.py menu launcher
    and the tester_routes.py API router.

Dependencies:
    - .autonomous_tester: Core testing daemon with MAB, rich TUI, and LLM diagnostics.
"""
from .autonomous_tester import AutonomousTester

__all__ = ["AutonomousTester"]