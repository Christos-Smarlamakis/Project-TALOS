# -*- coding: utf-8 -*-
"""
Module: ui_theme.py
Project: TALOS v5.10.9
Description:
    Canonical single source of truth for the unified questionary prompt style
    used across the entire TALOS TUI. The palette implements the Enterprise
    TUI Overhaul "Cyan/Teal & Bright White" academic aesthetic: category
    separators render in bright white, the question mark and question text in
    IEEE blue and light gray respectively, and all selection/highlight/answer
    accents in cyan/teal (#00ced1) with no background inversion (noinherit).

    Key design decisions:
    - Defined once and imported everywhere so every questionary.select,
      questionary.checkbox, and questionary.text prompt shares identical
      typography for IEEE publication-ready screenshots.
    - noinherit is applied to highlighted and selected tokens so the chosen
      item is drawn in cyan/teal on the terminal's normal background rather
      than a block-inverted selection, which reads poorly in captured frames.
    - The text and disabled keys are retained with harmonized neutral colors
      so multi-line input and inactive choices remain legible.

Dependencies:
    - questionary.Style: The questionary prompt style container.
"""
from questionary import Style


TALOS_QUESTIONARY_STYLE = Style([
    ('separator',   'bold fg:#ffffff'),           # Category Headers: Bright White
    ('qmark',       'bold fg:#4a9eff'),           # Question mark: IEEE Blue
    ('question',    'bold fg:#e4e7ee'),           # Question text: Light gray/white
    ('pointer',     'bold fg:#00ced1'),           # Arrow pointer: Cyan/Teal
    ('highlighted', 'bold fg:#00ced1 noinherit'), # Selected text: Cyan/Teal (no bg inversion)
    ('selected',    'bold fg:#00ced1 noinherit'), # Selected checkbox item: Cyan/Teal
    ('instruction', 'fg:#6b7280 italic'),         # Helper text: Dim gray
    ('answer',      'bold fg:#00ced1'),           # Final answered text: Cyan/Teal
    ('text',        'fg:#e4e7ee'),                # Typed input text: Light gray/white
    ('disabled',    'fg:#6b7280 italic'),         # Inactive choices: Dim gray
])
