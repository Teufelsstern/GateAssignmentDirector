"""Tooltip file monitoring for GSX success detection"""

# Licensed under AGPL-3.0-or-later with additional terms
# See LICENSE file for full text and additional requirements

import os
import time
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)


class TooltipReader:
    """Monitors GSX tooltip file for success messages"""

    def __init__(self, config) -> None:
        """Initialize tooltip reader with config

        Args:
            config: GADConfig instance with tooltip_file_paths and tooltip_success_keyphrases
        """
        self.config = config
        self.tooltip_paths: List[str] = config.tooltip_file_paths or []
        self.success_keyphrases: List[str] = config.tooltip_success_keyphrases or []

    def get_file_timestamp(self) -> Optional[float]:
        """Get most recent modification time of tooltip files

        Returns:
            Most recent mtime as float, or None if no files exist
        """
        latest_mtime = None

        for path in self.tooltip_paths:
            try:
                if os.path.exists(path):
                    mtime = os.path.getmtime(path)
                    if latest_mtime is None or mtime > latest_mtime:
                        latest_mtime = mtime
            except (OSError, IOError) as e:
                logger.debug(f"Could not get timestamp for {path}: {e}")

        return latest_mtime

    def read_tooltip(self) -> str:
        """Read current tooltip content from first existing file

        Returns:
            Tooltip content as string, or empty string if no files exist or readable
        """
        for path in self.tooltip_paths:
            try:
                if os.path.exists(path):
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                        logger.debug(f"Read tooltip from {path}: {content[:100]}")
                        return content
            except (OSError, IOError) as e:
                logger.debug(f"Could not read {path}: {e}")

        return ""

    def check_for_success(
        self,
        baseline_timestamp: Optional[float],
        timeout: float = 2.0,
        check_interval: float = 0.2,
    ) -> bool:
        """Poll tooltip file for updates with success messages

        Args:
            baseline_timestamp: Original file timestamp before action (None if file didn't exist)
            timeout: Maximum seconds to poll before giving up
            check_interval: Seconds between polls

        Returns:
            True if file timestamp changed AND contains success keyphrase
        """
        if not self.tooltip_paths or not self.success_keyphrases:
            logger.debug("No tooltip paths or keyphrases configured, skipping check")
            return False

        start_time = time.time()
        elapsed = 0.0

        while elapsed < timeout:
            current_timestamp = self.get_file_timestamp()

            # Check if timestamp changed
            if current_timestamp is not None and current_timestamp != baseline_timestamp:
                # File was updated, check content
                tooltip_content = self.read_tooltip().lower()

                for keyphrase in self.success_keyphrases:
                    if keyphrase.lower() in tooltip_content:
                        logger.info(
                            f"GSX success confirmed via tooltip: '{keyphrase}' found"
                        )
                        return True

                logger.debug(
                    f"Tooltip updated but no success keyphrase found: {tooltip_content[:100]}"
                )

            time.sleep(check_interval)
            elapsed = time.time() - start_time

        logger.debug(
            f"Tooltip check timed out after {timeout}s (no timestamp change or keyphrase match)"
        )
        return False

    def clear_tooltips(self):
        for path in self.tooltip_paths:
            if os.path.exists(path):
                open(path, "w").close()