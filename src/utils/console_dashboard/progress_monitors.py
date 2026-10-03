# -*- coding: utf-8 -*-
"""
Module: progress_monitors.py
Project: TALOS v5.22.0
Description:
    Unified multi-metric progress monitor for the TALOS Scientific Terminal
    Dashboard. Builds a Rich Progress instance whose columns expose a spinner,
    a styled task description, a 35-cell bar, the task progress fraction, the
    remaining time, a processing rate (papers/s), and the live GPU VRAM
    footprint. Tasks declare ``rate`` and ``vram`` in ``task.fields`` and call
    ``progress.update`` so the HMI reflects throughput and hardware pressure
    in-place (zero-flicker rendering).

Dependencies:
    - rich.progress: SpinnerColumn, BarColumn, TextColumn, TaskProgressColumn,
      TimeRemainingColumn, Progress.
"""

from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeRemainingColumn,
)


def create_scientific_progress() -> Progress:
    """Create the canonical multi-metric scientific Progress instance.

    Returns:
        Progress: A Progress configured with the full scientific column set.
    """
    return Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=35),
        TaskProgressColumn(),
        TimeRemainingColumn(),
        TextColumn("[green]{task.fields[rate]:.1f} papers/s[/green]"),
        TextColumn("[yellow]GPU: {task.fields[vram]} GB[/yellow]"),
    )


class MultiMetricProgress:
    """Convenience wrapper around the multi-metric scientific Progress.

    Attributes:
        progress (Progress): The underlying configured Progress instance.
    """

    def __init__(self, progress: Progress = None) -> None:
        """Initialise the wrapper, defaulting to the scientific progress.

        Args:
            progress (Progress): An optional pre-configured Progress instance.
        """
        self.progress = progress or create_scientific_progress()

    def add_metric_task(
        self,
        description: str,
        total: float = 100.0,
        rate: float = 0.0,
        vram: float = 0.0,
    ) -> int:
        """Register a metric task with throughput and VRAM fields.

        Args:
            description (str): Human-readable task label.
            total (float): Total work units. Defaults to 100.0.
            rate (float): Initial processing rate in papers/s. Defaults to 0.0.
            vram (float): Initial VRAM footprint in GB. Defaults to 0.0.

        Returns:
            int: The task identifier assigned by the Progress instance.
        """
        return self.progress.add_task(
            description,
            total=total,
            rate=rate,
            vram=vram,
        )
