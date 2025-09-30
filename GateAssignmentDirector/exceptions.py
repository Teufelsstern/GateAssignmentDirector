# exceptions.py
"""Custom exceptions for GSX Hook

This module defines all custom exceptions used throughout the GSX Hook system.
Having them in a separate file prevents circular imports and provides a clean
exception hierarchy.
"""


class GsxError(Exception):
    """Base exception for all GSX operations

    All GSX-specific exceptions inherit from this base class,
    making it easy to catch all GSX errors with a single except block.
    """

    pass


class GsxMenuError(GsxError):
    """Error related to GSX menu operations

    Raised when:
    - Menu file cannot be read
    - Menu doesn't change after a click
    - Expected menu option is not found
    - Navigation fails
    """

    pass


class GsxConnectionError(GsxError):
    """Error connecting to SimConnect or GSX

    Raised when:
    - SimConnect connection fails
    - Cannot establish connection to MSFS
    - GSX is not responding
    """

    pass


class GsxTimeoutError(GsxError):
    """Timeout waiting for an operation

    Raised when:
    - Waiting for aircraft to be on ground times out
    - Waiting for menu change times out
    - Any operation exceeds its timeout limit
    """

    pass


class GsxFileNotFoundError(GsxError):
    """GSX menu file not found

    Raised when:
    - The GSX menu file cannot be located in any of the configured paths
    - The menu file exists but cannot be accessed
    """

    pass


class GsxInvalidStateError(GsxError):
    """GSX is in an invalid or unexpected state

    Raised when:
    - Aircraft is not in a valid state for GSX operations
    - GSX state variables indicate an error condition
    - Operations are attempted when prerequisites are not met
    """

    pass
