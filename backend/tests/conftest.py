"""Test bootstrap: make backend modules importable and provide a dummy API key.

The Settings object requires ANTHROPIC_API_KEY at import time. Tests never make
real API calls, so we set a placeholder before any backend module is imported.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-not-used")
