"""
Pytest configuration file for 3D-MM test suite.

This module sets up the Python path to allow tests to import
from the src package while also allowing src modules to use
their normal relative imports.
"""

import sys
import os

# Add the parent directory (project root) to Python path
# This allows tests to use 'from src.module import ...'
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Also add the src directory to allow modules inside src to use relative imports
src_dir = os.path.join(project_root, 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)