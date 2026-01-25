"""Helper functions for Time of Use (TOU) register encoding and decoding.

This module provides utilities to convert between human-readable formats
and Modbus register values for TOU (Time of Use) scheduling settings.

Encoding patterns:
- Time (HH:MM): (hours << 8) | minutes
- Work Week (Table 8-34): H-byte = mode, L-byte = day bitmask (bit0-6 = Sun-Sat)
- Months: direct 12-bit bitmask (bits 0-11 = Jan-Dec)
"""

from enum import IntEnum
from typing import List, Tuple, Optional


class WorkWeekMode(IntEnum):
    """Work Week operation modes (H-byte values from Table 8-34)."""
    NOT_SET = 0x55
    ECO_ENABLE = 0xFF
    ECO_DISABLE = 0x00
    DRY_CONTACT_LOAD_ENABLE = 0xFE
    DRY_CONTACT_LOAD_DISABLE = 0x01
    DRY_CONTACT_SMART_LOAD_ENABLE = 0xFD
    DRY_CONTACT_SMART_LOAD_DISABLE = 0x02
    PEAK_SHAVING_ENABLE = 0xFC
    PEAK_SHAVING_DISABLE = 0x03
    BACKUP_MODE_ENABLE = 0xFB
    BACKUP_MODE_DISABLE = 0x04
    BATTERY_POWER_PERMILLAGE = 0xF9  # Battery power permillage mode (observed in practice)


# Day names mapping (0=Sunday, 1=Monday, ..., 6=Saturday)
DAY_NAMES = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
DAY_MAP = {name: idx for idx, name in enumerate(DAY_NAMES)}

# Month names mapping (0=January, 1=February, ..., 11=December)
MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
               'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
MONTH_MAP = {name: idx for idx, name in enumerate(MONTH_NAMES)}

# Mode name mapping for human-readable output
MODE_NAMES = {
    WorkWeekMode.NOT_SET: "Not Set",
    WorkWeekMode.ECO_ENABLE: "ECO Mode",
    WorkWeekMode.ECO_DISABLE: "ECO Disabled",
    WorkWeekMode.DRY_CONTACT_LOAD_ENABLE: "Dry Contact Load",
    WorkWeekMode.DRY_CONTACT_LOAD_DISABLE: "Dry Contact Load Disabled",
    WorkWeekMode.DRY_CONTACT_SMART_LOAD_ENABLE: "Dry Contact Smart Load",
    WorkWeekMode.DRY_CONTACT_SMART_LOAD_DISABLE: "Dry Contact Smart Load Disabled",
    WorkWeekMode.PEAK_SHAVING_ENABLE: "Peak Shaving",
    WorkWeekMode.PEAK_SHAVING_DISABLE: "Peak Shaving Disabled",
    WorkWeekMode.BACKUP_MODE_ENABLE: "Backup Mode",
    WorkWeekMode.BACKUP_MODE_DISABLE: "Backup Mode Disabled",
    WorkWeekMode.BATTERY_POWER_PERMILLAGE: "Battery Power Permillage",
}


def encode_time(time_str: str) -> int:
    """Encode time string to Modbus register value.

    Args:
        time_str: Time in HH:MM format (e.g., "14:30")

    Returns:
        Integer value: (hours << 8) | minutes

    Raises:
        ValueError: If time format is invalid

    Examples:
        >>> encode_time("14:30")
        3630  # 0x0E1E = (14 << 8) | 30
        >>> encode_time("00:00")
        0
        >>> encode_time("23:59")
        6143  # 0x173B = (23 << 8) | 59
    """
    if not time_str or ':' not in time_str:
        raise ValueError(f"Invalid time format: {time_str}. Expected HH:MM")

    try:
        parts = time_str.split(':')
        hours = int(parts[0])
        minutes = int(parts[1])

        if not (0 <= hours <= 23):
            raise ValueError(f"Hours must be 0-23, got {hours}")
        if not (0 <= minutes <= 59):
            raise ValueError(f"Minutes must be 0-59, got {minutes}")

        return (hours << 8) | minutes
    except (IndexError, ValueError) as e:
        raise ValueError(f"Invalid time format: {time_str}. Error: {e}")


def decode_time(value: int) -> str:
    """Decode Modbus register value to time string.

    Args:
        value: Integer register value

    Returns:
        Time string in HH:MM format

    Examples:
        >>> decode_time(3630)
        "14:30"
        >>> decode_time(0)
        "00:00"
        >>> decode_time(6143)
        "23:59"
    """
    hours = (value >> 8) & 0xFF
    minutes = value & 0xFF
    return f"{hours:02d}:{minutes:02d}"


def encode_workweek(mode: WorkWeekMode, days: List[str]) -> int:
    """Encode work week mode and days to Modbus register value (Table 8-34).

    Args:
        mode: Work week operation mode (from WorkWeekMode enum)
        days: List of day names (e.g., ['Mon', 'Tue', 'Wed'])
              Valid names: Sun, Mon, Tue, Wed, Thu, Fri, Sat
              Empty list is valid

    Returns:
        Integer value: (mode << 8) | day_bitmask
        H-byte = mode, L-byte bits 0-6 = Sunday-Saturday

    Raises:
        ValueError: If day name is invalid or mode is invalid

    Examples:
        >>> encode_workweek(WorkWeekMode.ECO_ENABLE, ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'])
        65502  # 0xFF1E = ECO_ENABLE + (Mon|Tue|Wed|Thu|Fri)
        >>> encode_workweek(WorkWeekMode.PEAK_SHAVING_ENABLE, ['Sun', 'Sat'])
        64577  # 0xFC41 = PEAK_SHAVING_ENABLE + (Sun|Sat)
        >>> encode_workweek(WorkWeekMode.NOT_SET, [])
        21760  # 0x5500 = NOT_SET + no days
    """
    if not isinstance(mode, WorkWeekMode):
        try:
            mode = WorkWeekMode(mode)
        except ValueError:
            raise ValueError(f"Invalid mode: {mode}. Must be a WorkWeekMode value")

    bitmask = 0
    for day in days:
        day = day.capitalize()
        if day not in DAY_MAP:
            raise ValueError(f"Invalid day name: {day}. Valid names: {', '.join(DAY_NAMES)}")
        bitmask |= (1 << DAY_MAP[day])

    # H-byte = mode, L-byte = day bitmask
    return (mode << 8) | bitmask


def decode_workweek(value: int) -> Tuple[WorkWeekMode, List[str]]:
    """Decode Modbus register value to work week mode and days (Table 8-34).

    Args:
        value: Integer register value

    Returns:
        Tuple of (mode: WorkWeekMode, days: List[str])

    Examples:
        >>> decode_workweek(65502)
        (WorkWeekMode.ECO_ENABLE, ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'])
        >>> decode_workweek(64577)
        (WorkWeekMode.PEAK_SHAVING_ENABLE, ['Sun', 'Sat'])
        >>> decode_workweek(21760)
        (WorkWeekMode.NOT_SET, [])
    """
    mode_byte = (value >> 8) & 0xFF
    try:
        mode = WorkWeekMode(mode_byte)
    except ValueError:
        # Unknown mode, return raw value
        mode = mode_byte

    bitmask = value & 0x7F  # Bits 0-6
    decoded_days = []
    for i in range(7):
        if bitmask & (1 << i):
            decoded_days.append(DAY_NAMES[i])

    return mode, decoded_days


def encode_months(months: List[str]) -> int:
    """Encode list of month names to Modbus register value.

    Args:
        months: List of month names (e.g., ['Jan', 'Feb', 'Mar'])
                Valid names: Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec
                Empty list means all year (returns 0)

    Returns:
        Integer value: direct 12-bit bitmask (bits 0-11 = Jan-Dec)

    Raises:
        ValueError: If month name is invalid

    Examples:
        >>> encode_months(['Jan', 'Feb', 'Dec'])
        2051  # 0x0803 = Jan|Feb|Dec
        >>> encode_months(['Jun', 'Jul', 'Aug'])
        224  # 0x00E0 = Jun|Jul|Aug
        >>> encode_months([])
        0  # 0x0000 = all year
    """
    bitmask = 0
    for month in months:
        month = month.capitalize()
        if month not in MONTH_MAP:
            raise ValueError(f"Invalid month name: {month}. Valid names: {', '.join(MONTH_NAMES)}")
        bitmask |= (1 << MONTH_MAP[month])

    return bitmask


def decode_months(value: int) -> List[str]:
    """Decode Modbus register value to month list.

    Args:
        value: Integer register value

    Returns:
        List of month names. Empty list means all year.

    Examples:
        >>> decode_months(2051)
        ['Jan', 'Feb', 'Dec']
        >>> decode_months(224)
        ['Jun', 'Jul', 'Aug']
        >>> decode_months(0)
        []
    """
    bitmask = value & 0xFFF  # Bits 0-11
    decoded_months = []
    for i in range(12):
        if bitmask & (1 << i):
            decoded_months.append(MONTH_NAMES[i])

    return decoded_months


def format_workweek_readable(value: int) -> str:
    """Format work week register value as human-readable string.

    Args:
        value: Integer register value

    Returns:
        Formatted string showing mode and days

    Examples:
        >>> format_workweek_readable(65502)
        "ECO Mode: Mon,Tue,Wed,Thu,Fri"
        >>> format_workweek_readable(21760)
        "Not Set"
    """
    mode, days = decode_workweek(value)

    if isinstance(mode, WorkWeekMode):
        mode_name = MODE_NAMES.get(mode, f"Unknown (0x{mode:02X})")
    else:
        mode_name = f"Unknown (0x{mode:02X})"

    if not days:
        return mode_name
    return f"{mode_name}: {','.join(days)}"


def format_months_readable(value: int) -> str:
    """Format months register value as human-readable string.

    Args:
        value: Integer register value

    Returns:
        Formatted string showing months or "All year" if empty

    Examples:
        >>> format_months_readable(2051)
        "Jan,Feb,Dec"
        >>> format_months_readable(0)
        "All year"
    """
    months = decode_months(value)
    if not months:
        return "All year"
    return ','.join(months)
