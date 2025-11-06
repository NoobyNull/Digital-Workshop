"""
Pipeline workers package.

Contains async worker implementations for pipeline stages.
Currently, stages execute synchronously, but this package is ready
for future async worker implementations.
"""

from src.core.import_pipeline.workers.base_worker import BaseWorker


__all__ = [
    "BaseWorker",
]

