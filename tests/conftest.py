"""Test configuration for ensuring the project root is importable.

Test role: shared pytest configuration used by the full test suite.
"""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
