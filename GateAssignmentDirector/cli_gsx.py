"""Updated CLI with airport parameter"""

import argparse
import logging
from gsx_hook import GsxHook
from config import GsxConfig

logger = logging.getLogger(__name__)


def main():
    """Main CLI entry point with airport support"""
    parser = argparse.ArgumentParser(
        description="GSX Gate Assignment Automation for MSFS"
    )

    # Required airport parameter
    parser.add_argument("airport", type=str, help="Airport ICAO code (e.g., KLAX)")

    # Gate parameters
    parser.add_argument("--gate-letter", type=str, help="Gate letter (e.g., 'C')")
    parser.add_argument(
        "--gate-number", type=int, required=True, help="Gate number (e.g., 102)"
    )
    parser.add_argument("--terminal", type=str, default="", help="Terminal identifier")
    parser.add_argument(
        "--terminal-number", type=int, default=0, help="Terminal number"
    )
    parser.add_argument(
        "--airline", type=str, default="GSX", help="Airline code (e.g., 'United_2000')"
    )

    # Options
    parser.add_argument(
        "--no-wait-ground",
        action="store_true",
        help="Don't wait for aircraft to be on ground",
    )
    parser.add_argument(
        "--ground-timeout",
        type=int,
        default=300,
        help="Timeout in seconds when waiting for ground (default: 300)",
    )
    parser.add_argument(
        "--no-menu-logging", action="store_true", help="Disable menu state logging"
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Analyze existing logs for the airport instead of assigning",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
    )

    # Create and run GSX Hook
    try:
        config = GsxConfig()
        gsx = GsxHook(config, enable_menu_logging=not args.no_menu_logging)

        if not gsx.is_initialized:
            logger.error("Failed to initialize GSX Hook")
            return 1

        success = gsx.assign_gate_when_ready(
            airport=args.airport.upper(),
            terminal=args.terminal,
            terminal_number=args.terminal_number,
            gate_letter=args.gate_letter,
            gate_number=args.gate_number,
            airline=args.airline,
            wait_for_ground=not args.no_wait_ground,
            ground_timeout=args.ground_timeout,
        )

        gsx.close()
        return 0 if success else 1

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1
