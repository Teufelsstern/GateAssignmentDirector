"""Sleek UI for Gate Assignment Director

This module provides a backward-compatible entry point.
The actual UI implementation has been refactored into the ui/ package.
"""

# Licensed under AGPL-3.0-or-later with additional terms
# See LICENSE file for full text and additional requirements

import logging

# Silence PIL debug spam
logging.getLogger("PIL").setLevel(logging.WARNING)

# Import from new structure
from GateAssignmentDirector.ui import DirectorUI, GateManagementWindow

__all__ = ["DirectorUI", "GateManagementWindow"]


if __name__ == "__main__":
    from GateAssignmentDirector.gad_config import GADConfig

    config = GADConfig()
    app = DirectorUI()
    app.run()
