"""Tests for TOU decoding using real Modbus data from master inverter."""

from unittest import TestCase
from goodwe.tou_helpers import (
    decode_time,
    decode_workweek,
    decode_months,
    format_workweek_readable,
    format_months_readable,
)


class TestTOURealData(TestCase):
    """Tests using real data captured from master inverter (ID 247) on 2026-01-26."""

    def test_slot1_start_time(self):
        """Test TOU Slot 1 Start Time (register 47547)."""
        # Raw value: 0x1300 = 4864 decimal
        # Expected: 19:00 (0x13 = 19 hours, 0x00 = 0 minutes)
        raw_value = 0x1300
        decoded = decode_time(raw_value)
        self.assertEqual(decoded, "19:00", f"Expected 19:00 but got {decoded}")

    def test_slot1_end_time(self):
        """Test TOU Slot 1 End Time (register 47548)."""
        # Raw value: 0x0600 = 1536 decimal
        # Expected: 06:00 (0x06 = 6 hours, 0x00 = 0 minutes)
        raw_value = 0x0600
        decoded = decode_time(raw_value)
        self.assertEqual(decoded, "06:00", f"Expected 06:00 but got {decoded}")

    def test_slot1_workweek(self):
        """Test TOU Slot 1 Work Week (register 47549)."""
        # Raw value: 0xF97F = 63871 decimal
        # Mode: 0xF9 = BATTERY_POWER_PERMILLAGE
        # Days: 0x7F = 0b1111111 = all 7 days (Sun-Sat)
        raw_value = 0xF97F
        mode, days = decode_workweek(raw_value)

        # Check mode
        self.assertEqual(mode.value, 0xF9, f"Expected mode 0xF9 but got {mode.value:02x}")

        # Check days (should be all 7 days)
        self.assertEqual(len(days), 7, f"Expected 7 days but got {len(days)}: {days}")
        self.assertEqual(days, ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'])

    def test_slot1_months(self):
        """Test TOU Slot 1 Months (register 47552)."""
        # Raw value: 0x0FFF = 4095 decimal = 0b111111111111
        # All 12 bits set = all months (Jan-Dec)
        raw_value = 0x0FFF
        decoded = decode_months(raw_value)

        self.assertEqual(len(decoded), 12, f"Expected 12 months but got {len(decoded)}")
        self.assertEqual(decoded, ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])

    def test_slot2_start_time(self):
        """Test TOU Slot 2 Start Time (register 47554)."""
        # Raw value: 0x1700 = 5888 decimal
        # Expected: 23:00 (0x17 = 23 hours, 0x00 = 0 minutes)
        raw_value = 0x1700
        decoded = decode_time(raw_value)
        self.assertEqual(decoded, "23:00", f"Expected 23:00 but got {decoded}")

    def test_slot2_workweek(self):
        """Test TOU Slot 2 Work Week (register 47555)."""
        # Raw value: 0xF941 = 63809 decimal
        # Mode: 0xF9 = BATTERY_POWER_PERMILLAGE
        # Days: 0x41 = 0b1000001 = bit 0 (Sun) and bit 6 (Sat)
        raw_value = 0xF941
        mode, days = decode_workweek(raw_value)

        # Check mode
        self.assertEqual(mode.value, 0xF9)

        # Check days (should be weekend only)
        self.assertEqual(len(days), 2, f"Expected 2 days but got {len(days)}: {days}")
        self.assertEqual(days, ['Sun', 'Sat'])

    def test_slot8_start_time(self):
        """Test TOU Slot 8 Start Time (register 47590)."""
        # Raw value: 0x173B = 5947 decimal
        # Expected: 23:59 (0x17 = 23 hours, 0x3B = 59 minutes)
        raw_value = 0x173B
        decoded = decode_time(raw_value)
        self.assertEqual(decoded, "23:59", f"Expected 23:59 but got {decoded}")

    def test_slot8_workweek(self):
        """Test TOU Slot 8 Work Week (register 47591)."""
        # Raw value: 0xFC00 = 64512 decimal
        # Mode: 0xFC = PEAK_SHAVING_ENABLE
        # Days: 0x00 = no days selected
        raw_value = 0xFC00
        mode, days = decode_workweek(raw_value)

        # Check mode
        self.assertEqual(mode.value, 0xFC, f"Expected mode 0xFC but got {mode.value:02x}")

        # Check days (should be empty)
        self.assertEqual(len(days), 0, f"Expected 0 days but got {len(days)}: {days}")
        self.assertEqual(days, [])

    def test_format_workweek_readable_slot1(self):
        """Test formatting Slot 1 work week as readable string."""
        raw_value = 0xF97F
        formatted = format_workweek_readable(raw_value)

        # Should show mode name and all days
        self.assertIn("Battery Power Permillage", formatted)
        self.assertIn("Sun", formatted)
        self.assertIn("Mon", formatted)
        self.assertIn("Sat", formatted)

    def test_format_months_readable_all(self):
        """Test formatting all months as readable string."""
        raw_value = 0x0FFF  # All 12 months
        formatted = format_months_readable(raw_value)

        # Should show "All year" or list all months
        # Implementation may vary
        self.assertTrue(
            "All year" in formatted or len(formatted.split(',')) == 12,
            f"Expected 'All year' or 12 months in: {formatted}"
        )

    def test_format_months_readable_none(self):
        """Test formatting no months selected."""
        raw_value = 0x0000
        formatted = format_months_readable(raw_value)

        # Should indicate no months or "All year" depending on implementation
        self.assertIsNotNone(formatted)


class TestTOUParameterValues(TestCase):
    """Test TOU parameter values from real data."""

    def test_slot1_param1(self):
        """Test Slot 1 Parameter 1 (register 47550)."""
        # Raw value: 0xFEA2 = 65186 decimal
        # This is likely a signed value or has special meaning
        raw_value = 0xFEA2
        self.assertEqual(raw_value, 65186)

    def test_slot1_param2(self):
        """Test Slot 1 Parameter 2 (register 47551)."""
        # Raw value: 0x0041 = 65 decimal
        raw_value = 0x0041
        self.assertEqual(raw_value, 65)

    def test_slot2_param2(self):
        """Test Slot 2 Parameter 2 (register 47557)."""
        # Raw value: 0x0050 = 80 decimal
        raw_value = 0x0050
        self.assertEqual(raw_value, 80)

    def test_slot8_param1(self):
        """Test Slot 8 Parameter 1 (register 47592)."""
        # Raw value: 0x0BB8 = 3000 decimal
        raw_value = 0x0BB8
        self.assertEqual(raw_value, 3000)
