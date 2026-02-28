"""
Pipeline — sequential processor chain.

Each step is a ``ProcessorFn``: a callable that takes a ``Path`` and
returns a ``Path``. Steps run in list order; each receives the output
of the previous step.

Usage:

    from domain.pipeline import build_pipeline

    pipeline = build_pipeline([trim_step, codec_step, resize_step])
    output_path = pipeline(input_path)
"""

from collections.abc import Callable
from pathlib import Path

ProcessorFn = Callable[[Path], Path]


def build_pipeline(steps: list[ProcessorFn]) -> ProcessorFn:
    """Return a single callable that applies each step in order.

    If *steps* is empty the returned function is the identity: it
    returns its input unchanged.

    Args:
        steps: Ordered list of processing functions. Each receives the
            ``Path`` returned by the previous step.

    Returns:
        A single ``ProcessorFn`` that applies every step sequentially.
    """

    def handler(path: Path) -> Path:
        for step in steps:
            path = step(path)
        return path

    return handler
