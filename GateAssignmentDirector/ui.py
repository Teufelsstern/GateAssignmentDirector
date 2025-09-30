"""Sleek UI for Gate Assignment Director

This module provides a backward-compatible entry point.
The actual UI implementation has been refactored into the ui/ package.
"""

import logging

# Silence PIL debug spam
logging.getLogger("PIL").setLevel(logging.WARNING)

# Import from new structure
from GateAssignmentDirector.ui import DirectorUI, GateManagementWindow

__all__ = ['DirectorUI', 'GateManagementWindow']


if __name__ == "__main__":
    from GateAssignmentDirector.config import GsxConfig
    config = GsxConfig()
    app = DirectorUI()
    app.run()