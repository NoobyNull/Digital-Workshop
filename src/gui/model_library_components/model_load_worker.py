"""
Compatibility wrapper for model loading worker.

Re-exports the worker from ``src.gui.model_library.model_load_worker`` to avoid
duplicated implementations.
"""

from src.gui.model_library.model_load_worker import ModelLoadWorker

__all__ = ["ModelLoadWorker"]
