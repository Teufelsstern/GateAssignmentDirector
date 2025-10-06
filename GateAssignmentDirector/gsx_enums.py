# enums_own.py (or enums.py)
"""Enumerations and constants for GSX Hook

This module contains all enumerations and constant values used throughout
the GSX Hook system, providing type-safe constants for SimConnect variables,
search types, and GSX states.
"""

# Licensed under AGPL-3.0-or-later with additional terms
# See LICENSE file for full text and additional requirements

from enum import Enum, IntEnum


class SearchType(Enum):
    """Types of searches that can be performed in GSX menus"""

    GATE = "gate"
    TERMINAL = "terminal"
    AIRLINE = "airline"
    KEYWORD = "keyword"
    MENU_ACTION = "menu_action"


class GsxVariable(Enum):
    """GSX SimConnect L:Variables (Local Variables)

    These are the SimConnect variables used to interact with GSX.
    The values are byte strings as required by SimConnect.
    """

    # Menu control variables
    MENU_OPEN = b"L:FSDT_GSX_MENU_OPEN"  # Open/close GSX menu (1=open, 0=close)
    MENU_CHOICE = (
        b"L:FSDT_GSX_MENU_CHOICE"  # Select menu option (index number, -2=refresh)
    )

    # GSX state variables
    STATE = b"L:FSDT_GSX_STATE"  # Overall GSX state


class GsxState(Enum):
    """GSX overall state values

    These are the possible values for the GSX_STATE variable.
    Note: These are example values - you may need to verify the actual values GSX uses.
    """

    INACTIVE = 0
    MENU_OPEN = 1
    SERVICE_ACTIVE = 2
    BOARDING = 3
    DEBOARDING = 4
    PUSHBACK = 5
    REFUELING = 6


class GsxServiceState(Enum):
    """Common service state values

    Many GSX service variables use these standard states.
    """

    NOT_AVAILABLE = -1
    IDLE = 0
    REQUESTED = 1
    ARRIVING = 2
    IN_POSITION = 3
    ACTIVE = 4
    COMPLETE = 5
    DEPARTING = 6


class MenuAction(Enum):
    """Standard GSX menu actions"""

    OPEN = 1
    CLOSE = 0
    REFRESH = -2
    BACK = -1


class AircraftVariable(Enum):
    """Standard aircraft SimConnect variables

    These are not GSX-specific but are often used alongside GSX operations.
    """

    ON_GROUND = b"SIM ON GROUND"  # Is aircraft on ground (1=yes, 0=no)


class VariableType(Enum):
    """SimConnect variable types

    Types that can be used when creating SimConnect requests.
    """

    NUMBER = b"Number"
    BOOL = b"Bool"
    ENUM = b"Enum"
    FLAGS = b"Flags"
    STRING = b"String"
    PERCENT = b"Percent"


class GsxMenuKeywords(Enum):
    """Common keywords found in GSX menus

    These are standard words that appear in GSX menus across different airports.
    """

    # Navigation
    NEXT = "Next"
    PREVIOUS = "Previous"
    BACK = "Back"

    # Gate operations
    ACTIVATE = "activate"
    SELECT = "select"
    CONFIRM = "confirm"

    # Common options
    YES = "Yes"
    NO = "No"
    CANCEL = "Cancel"
    EXIT = "Exit"


class GsxErrorCode(Enum):
    """GSX error codes for better error handling

    Custom error codes to identify specific failure scenarios.
    """

    SUCCESS = 0
    CONNECTION_FAILED = 1
    MENU_NOT_FOUND = 2
    OPTION_NOT_FOUND = 3
    TIMEOUT = 4
    AIRCRAFT_NOT_READY = 5
    GSX_NOT_AVAILABLE = 6
    INVALID_GATE = 7
    INVALID_AIRLINE = 8

class GateGroups(IntEnum):
    T_NAME = 1
    T_NUMBER = 2
    G_WORD = 3
    G_PRE = 4
    G_NUMBER = 5
    G_LETTER = 6