"""Entry point for BrainWorkshop desktop application.

This module serves as the main entry point when running the application
as a Python module (python -m brainworkshop).

For now, this delegates to the original monolithic implementation while
we progressively refactor to the hexagonal architecture.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add parent directory to path to import the original module
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import and run the original implementation
# TODO: Replace this with the new hexagonal architecture
import brainworkshop_original

if __name__ == '__main__':
    # The original module runs on import, so we just need to import it
    pass
