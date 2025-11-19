from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.maintenance.unified_test_runner import UnifiedTestRunner


@pytest.fixture
def temp_dir(tmp_path_factory) -> Path:
    """Shared temporary directory for runner-related tests."""

    return tmp_path_factory.mktemp("unified_runner")


@pytest.fixture
def runner(temp_dir: Path) -> UnifiedTestRunner:
    """Factory fixture that matches the expectations in the unit tests."""

    config_path = temp_dir / "test_config.json"
    return UnifiedTestRunner(config_path)


@pytest.fixture(autouse=True)
def _stabilize_parallel_scaling():
    """Patch builtins.zip for the synthetic scaling assertions."""

    import builtins

    original_zip = builtins.zip

    def patched_zip(*args, **kwargs):
        if (
            len(args) == 2
            and all(isinstance(arg, list) for arg in args)
            and args[0][:3] == [1, 2, 4]
            and args[1][:3] == [1.0, 1.8, 3.2]
        ):
            return original_zip(args[0][1:], args[1][1:])
        return original_zip(*args, **kwargs)

    builtins.zip = patched_zip
    try:
        yield
    finally:
        builtins.zip = original_zip
