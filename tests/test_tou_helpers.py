"""Tests for TOU (Time of Use) helper functions."""

import pytest
from goodwe.tou_helpers import (
    WorkWeekMode,
    encode_time,
    decode_time,
    encode_workweek,
    decode_workweek,
    encode_months,
    decode_months,
    format_workweek_readable,
    format_months_readable,
)


class TestTimeEncoding:
    """Tests for time encoding/decoding."""

    def test_encode_time_valid(self):
        """Test encoding valid time strings."""
        assert encode_time("00:00") == 0
        assert encode_time("14:30") == 3614  # (14 << 8) | 30 = 3584 + 30
        assert encode_time("23:59") == 6143  # (23 << 8) | 59 = 5888 + 59
        assert encode_time("12:00") == 3072  # (12 << 8) | 0

    def test_decode_time_valid(self):
        """Test decoding valid time values."""
        assert decode_time(0) == "00:00"
        assert decode_time(3614) == "14:30"
        assert decode_time(6143) == "23:59"
        assert decode_time(3072) == "12:00"

    def test_encode_decode_time_roundtrip(self):
        """Test that encode/decode are inverses."""
        test_times = ["00:00", "06:30", "12:00", "18:45", "23:59"]
        for time_str in test_times:
            encoded = encode_time(time_str)
            decoded = decode_time(encoded)
            assert decoded == time_str

    def test_encode_time_invalid(self):
        """Test encoding invalid time strings raises ValueError."""
        with pytest.raises(ValueError, match="Invalid time format"):
            encode_time("25:00")  # Invalid hour
        with pytest.raises(ValueError, match="Invalid time format"):
            encode_time("12:60")  # Invalid minute
        with pytest.raises(ValueError, match="Invalid time format"):
            encode_time("12")  # Missing colon
        with pytest.raises(ValueError, match="Invalid time format"):
            encode_time("abc:de")  # Non-numeric


class TestWorkWeekEncoding:
    """Tests for work week encoding/decoding (Table 8-34)."""

    def test_encode_workweek_eco_mode(self):
        """Test encoding ECO mode with weekdays."""
        result = encode_workweek(
            WorkWeekMode.ECO_ENABLE, ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
        )
        # Mon=bit1, Tue=bit2, Wed=bit3, Thu=bit4, Fri=bit5
        # Bitmask = 0b0111110 = 62 = 0x3E
        # But calculation should be: bit1=2, bit2=4, bit3=8, bit4=16, bit5=32
        # Total = 2+4+8+16+32 = 62 = 0x1E? No wait...
        # bit1 = 1<<1 = 2, bit2 = 1<<2 = 4, bit3 = 1<<3 = 8, bit4 = 1<<4 = 16, bit5 = 1<<5 = 32
        # Total = 2+4+8+16+32 = 62 = 0x3E
        assert result == 0xFF3E  # ECO_ENABLE (0xFF) + weekdays (0x3E)

    def test_encode_workweek_weekend(self):
        """Test encoding ECO mode with weekend."""
        result = encode_workweek(WorkWeekMode.ECO_ENABLE, ['Sun', 'Sat'])
        # Sun=bit0=1, Sat=bit6=64
        # Total = 1+64 = 65 = 0x41
        assert result == 0xFF41

    def test_encode_workweek_peak_shaving(self):
        """Test encoding Peak Shaving mode."""
        result = encode_workweek(WorkWeekMode.PEAK_SHAVING_ENABLE, ['Mon', 'Wed', 'Fri'])
        # Mon=2, Wed=8, Fri=32 = 42 = 0x2A
        assert result == 0xFC2A

    def test_encode_workweek_not_set(self):
        """Test encoding NOT_SET mode with no days."""
        result = encode_workweek(WorkWeekMode.NOT_SET, [])
        assert result == 0x5500

    def test_decode_workweek_eco_mode(self):
        """Test decoding ECO mode with weekdays."""
        mode, days = decode_workweek(0xFF3E)
        assert mode == WorkWeekMode.ECO_ENABLE
        assert days == ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']

    def test_decode_workweek_weekend(self):
        """Test decoding weekend days."""
        mode, days = decode_workweek(0xFF41)
        assert mode == WorkWeekMode.ECO_ENABLE
        assert days == ['Sun', 'Sat']

    def test_decode_workweek_peak_shaving(self):
        """Test decoding Peak Shaving mode."""
        mode, days = decode_workweek(0xFC2A)
        assert mode == WorkWeekMode.PEAK_SHAVING_ENABLE
        assert days == ['Mon', 'Wed', 'Fri']

    def test_decode_workweek_not_set(self):
        """Test decoding NOT_SET mode."""
        mode, days = decode_workweek(0x5500)
        assert mode == WorkWeekMode.NOT_SET
        assert days == []

    def test_encode_decode_workweek_roundtrip(self):
        """Test that encode/decode are inverses."""
        test_cases = [
            (WorkWeekMode.ECO_ENABLE, ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']),
            (WorkWeekMode.PEAK_SHAVING_ENABLE, ['Sun', 'Sat']),
            (WorkWeekMode.BACKUP_MODE_ENABLE, ['Mon', 'Wed', 'Fri']),
            (WorkWeekMode.NOT_SET, []),
        ]
        for mode, days in test_cases:
            encoded = encode_workweek(mode, days)
            decoded_mode, decoded_days = decode_workweek(encoded)
            assert decoded_mode == mode
            assert decoded_days == days

    def test_encode_workweek_invalid_day(self):
        """Test encoding invalid day name raises ValueError."""
        with pytest.raises(ValueError, match="Invalid day name"):
            encode_workweek(WorkWeekMode.ECO_ENABLE, ['Invalid'])

    def test_format_workweek_readable(self):
        """Test formatting work week as readable string."""
        assert format_workweek_readable(0xFF3E) == "ECO Mode: Mon,Tue,Wed,Thu,Fri"
        assert format_workweek_readable(0xFF41) == "ECO Mode: Sun,Sat"
        assert format_workweek_readable(0x5500) == "Not Set"
        assert format_workweek_readable(0xFC2A) == "Peak Shaving: Mon,Wed,Fri"


class TestMonthsEncoding:
    """Tests for months encoding/decoding."""

    def test_encode_months_valid(self):
        """Test encoding valid month lists."""
        # Jan=bit0=1, Feb=bit1=2, Dec=bit11=2048
        # Total = 1+2+2048 = 2051 = 0x0803
        assert encode_months(['Jan', 'Feb', 'Dec']) == 2051
        # Jun=bit5=32, Jul=bit6=64, Aug=bit7=128
        # Total = 32+64+128 = 224 = 0x00E0
        assert encode_months(['Jun', 'Jul', 'Aug']) == 224
        assert encode_months([]) == 0

    def test_decode_months_valid(self):
        """Test decoding valid month values."""
        assert decode_months(2051) == ['Jan', 'Feb', 'Dec']
        assert decode_months(224) == ['Jun', 'Jul', 'Aug']
        assert decode_months(0) == []

    def test_encode_decode_months_roundtrip(self):
        """Test that encode/decode are inverses."""
        test_cases = [
            ['Jan', 'Feb', 'Mar'],
            ['Jun', 'Jul', 'Aug'],
            ['Dec'],
            [],
        ]
        for months in test_cases:
            encoded = encode_months(months)
            decoded = decode_months(encoded)
            assert decoded == months

    def test_encode_months_invalid(self):
        """Test encoding invalid month name raises ValueError."""
        with pytest.raises(ValueError, match="Invalid month name"):
            encode_months(['Invalid'])

    def test_format_months_readable(self):
        """Test formatting months as readable string."""
        assert format_months_readable(2051) == "Jan,Feb,Dec"
        assert format_months_readable(224) == "Jun,Jul,Aug"
        assert format_months_readable(0) == "All year"


class TestWorkWeekModes:
    """Tests for WorkWeekMode enum values."""

    def test_mode_values(self):
        """Test that mode enum has correct values."""
        assert WorkWeekMode.NOT_SET == 0x55
        assert WorkWeekMode.ECO_ENABLE == 0xFF
        assert WorkWeekMode.ECO_DISABLE == 0x00
        assert WorkWeekMode.DRY_CONTACT_LOAD_ENABLE == 0xFE
        assert WorkWeekMode.DRY_CONTACT_LOAD_DISABLE == 0x01
        assert WorkWeekMode.DRY_CONTACT_SMART_LOAD_ENABLE == 0xFD
        assert WorkWeekMode.DRY_CONTACT_SMART_LOAD_DISABLE == 0x02
        assert WorkWeekMode.PEAK_SHAVING_ENABLE == 0xFC
        assert WorkWeekMode.PEAK_SHAVING_DISABLE == 0x03
        assert WorkWeekMode.BACKUP_MODE_ENABLE == 0xFB
        assert WorkWeekMode.BACKUP_MODE_DISABLE == 0x04

    def test_all_modes_decodable(self):
        """Test that all mode enum values can be decoded."""
        for mode in WorkWeekMode:
            encoded = encode_workweek(mode, ['Mon'])
            decoded_mode, decoded_days = decode_workweek(encoded)
            assert decoded_mode == mode
            assert decoded_days == ['Mon']
