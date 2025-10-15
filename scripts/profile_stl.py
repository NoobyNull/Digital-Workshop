import sys
import os
import glob
import time
import gc

try:
    import psutil  # optional
except Exception:
    psutil = None

# Ensure src is on sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from core.logging_config import setup_logging  # noqa: E402
from parsers.stl_parser import STLParser, ProgressCallback  # noqa: E402
from core.hardware_acceleration import get_acceleration_manager  # noqa: E402


class PC(ProgressCallback):
    pass


def main():
    setup_logging()
    if len(sys.argv) < 2:
        print("Usage: python scripts/profile_stl.py <folder_with_stl_files>")
        sys.exit(2)

    folder = sys.argv[1]
    files = sorted(glob.glob(os.path.join(folder, "*.stl")))
    print(f"Found {len(files)} STL files in: {folder}")

    accel_info = get_acceleration_manager().get_acceleration_info()
    print("Acceleration:", accel_info)

    parser = STLParser()

    for f in files:
        print("\n--- Loading:", f)
        t0 = time.time()
        model = parser.parse_file(f, progress_callback=PC())
        t1 = time.time()
        rss_mb = None
        if psutil:
            try:
                rss_mb = int(psutil.Process().memory_info().rss / (1024 * 1024))
            except Exception:
                pass
        print("Result:", {
            "file": f,
            "secs": round(t1 - t0, 2),
            "tris": model.stats.triangle_count,
            "rss_mb": rss_mb
        })
        gc.collect()


if __name__ == "__main__":
    main()