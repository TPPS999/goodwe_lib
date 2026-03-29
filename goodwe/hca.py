"""HCA G2 EV charger support - GoodWe HCA G2 EV charger series"""
from __future__ import annotations

import logging
from typing import Any, Optional

from .const import GOODWE_TCP_PORT
from .exceptions import InverterError, RequestFailedException
from .inverter import Inverter, OperationMode, Sensor, SensorKind as Kind
from .protocol import ProtocolCommand, ProtocolResponse
from .sensor import (
    Current, Decimal, Energy4, Enum2, Integer, Long, SwitchValue, Voltage,
    read_bytes2,
)

logger = logging.getLogger(__name__)


CHARGER_STATUS_MODES: dict[int, str] = {
    0: "Idle",
    1: "Idle (plugged)",
    2: "Handshaking",
    3: "Charging",
    4: "Charging complete",
    5: "Alarm",
    6: "Scheduled",
    7: "Maintenance",
    8: "Start failed",
    9: "Upgrading",
    10: "Interrupted (low PV/bat)",
}

CAR_CONNECTION_MODES: dict[int, str] = {
    0: "Disconnected",
    1: "Half-connected",
    2: "Connected",
}

CHARGING_MODE_MODES: dict[int, str] = {
    0: "Fast charge",
    1: "PV only",
    2: "PV + battery",
}

CHARGE_START_MODES: dict[int, str] = {
    0: "RFID card",
    1: "Remote",
    2: "Local admin",
    3: "VIN",
    4: "Wallet card",
    5: "Plug & Play",
    6: "Scheduled",
    7: "Bluetooth app",
}

CHARGING_STRATEGY_MODES: dict[int, str] = {
    0: "Auto (full)",
    1: "By time",
    2: "By amount",
    3: "By energy",
}


class PowerSourceSensor(Sensor):
    """Sensor representing charging power source as human-readable text.

    Register 10108 is a bitmask: bit0=grid, bit1=PV, bit2=battery.
    Returns comma-separated list of active sources, e.g. 'Grid, PV'.
    """

    def __init__(self, id_: str, offset: int, name: str, kind: Optional[Kind] = None):
        super().__init__(id_, offset, name, 2, "", kind)

    def read_value(self, data: ProtocolResponse) -> str:
        raw = read_bytes2(data)
        sources = []
        if raw & 0x01:
            sources.append("Grid")
        if raw & 0x02:
            sources.append("PV")
        if raw & 0x04:
            sources.append("Battery")
        return ", ".join(sources) if sources else "None"


class HCA(Inverter):
    """Class representing GoodWe HCA G2 EV charger series.

    Communicates via standard Modbus TCP (port 502).
    Supported models: GW7K-HCA-20 (1-phase), GW11K-HCA-20 (3-phase), GW22K-HCA-20 (3-phase).
    Model tag in serial number: HPA (e.g. 5022KHPA257L2133).
    """

    # Runtime block 1 sensors - 3-phase (registers 10000-10018)
    __sensors_block1_3phase: tuple[Sensor, ...] = (
        # Fault/alarm status registers (bitmasks - non-zero means fault active)
        Integer("ac_fault_01", 10001, "EV Charger AC Fault 1", "", Kind.AC),
        Integer("ac_fault_02", 10002, "EV Charger AC Fault 2", "", Kind.AC),
        Integer("ac_fault_03", 10003, "EV Charger AC Fault 3", "", Kind.AC),
        Integer("ac_fault_04", 10004, "EV Charger AC Fault 4", "", Kind.AC),
        Integer("ac_alarm_05", 10005, "EV Charger AC Alarm 1", "", Kind.AC),
        Integer("ac_alarm_06", 10006, "EV Charger AC Alarm 2", "", Kind.AC),
        Integer("hw_fault_07", 10007, "EV Charger HW Fault 1", "", Kind.AC),
        Integer("hw_fault_08", 10008, "EV Charger HW Fault 2", "", Kind.AC),
        # AC measurements
        Voltage("voltage_a", 10009, "Charge Voltage L1", Kind.AC),
        Voltage("voltage_b", 10010, "Charge Voltage L2", Kind.AC),
        Voltage("voltage_c", 10011, "Charge Voltage L3", Kind.AC),
        Current("current_a", 10012, "Charge Current L1", Kind.AC),
        Current("current_b", 10013, "Charge Current L2", Kind.AC),
        Current("current_c", 10014, "Charge Current L3", Kind.AC),
        # Power and energy
        Decimal("charging_power", 10015, 10, "EV Charge Power", "kW", Kind.AC),
        Decimal("session_energy", 10016, 10, "Session Energy", "kWh", Kind.AC),
        # Status
        Enum2("charger_status", 10017, CHARGER_STATUS_MODES, "Charger Status", Kind.AC),
        Integer("charger_status_code", 10017, "Charger Status Code", "", Kind.AC),
        Integer("comm_status", 10018, "Connection Status Bits", "", Kind.AC),
    )

    # Runtime block 1 sensors - single-phase (B/C phase sensors excluded)
    __sensors_block1_1phase: tuple[Sensor, ...] = (
        Integer("ac_fault_01", 10001, "EV Charger AC Fault 1", "", Kind.AC),
        Integer("ac_fault_02", 10002, "EV Charger AC Fault 2", "", Kind.AC),
        Integer("ac_fault_03", 10003, "EV Charger AC Fault 3", "", Kind.AC),
        Integer("ac_fault_04", 10004, "EV Charger AC Fault 4", "", Kind.AC),
        Integer("ac_alarm_05", 10005, "EV Charger AC Alarm 1", "", Kind.AC),
        Integer("ac_alarm_06", 10006, "EV Charger AC Alarm 2", "", Kind.AC),
        Integer("hw_fault_07", 10007, "EV Charger HW Fault 1", "", Kind.AC),
        Integer("hw_fault_08", 10008, "EV Charger HW Fault 2", "", Kind.AC),
        Voltage("voltage_a", 10009, "Charge Voltage", Kind.AC),
        Current("current_a", 10012, "Charge Current", Kind.AC),
        Decimal("charging_power", 10015, 10, "EV Charge Power", "kW", Kind.AC),
        Decimal("session_energy", 10016, 10, "Session Energy", "kWh", Kind.AC),
        Enum2("charger_status", 10017, CHARGER_STATUS_MODES, "Charger Status", Kind.AC),
        Integer("charger_status_code", 10017, "Charger Status Code", "", Kind.AC),
        Integer("comm_status", 10018, "Connection Status Bits", "", Kind.AC),
    )

    # Runtime block 2 sensors (registers 10060-10108, same for all phase types)
    __sensors_block2: tuple[Sensor, ...] = (
        Integer("charge_on_off", 10060, "Charge State", "", Kind.AC),
        Long("charge_duration", 10063, "Session Duration", "s", Kind.AC),
        Energy4("total_energy", 10065, "Total Charged Energy", Kind.AC),
        Enum2("car_connection", 10075, CAR_CONNECTION_MODES, "EV Connection", Kind.AC),
        Enum2("charge_start_mode", 10076, CHARGE_START_MODES, "Session Start Method", Kind.AC),
        Enum2("charging_strategy", 10077, CHARGING_STRATEGY_MODES, "Charging Strategy", Kind.AC),
        Energy4("green_energy", 10103, "Session Green Energy", Kind.AC),
        Energy4("grid_energy", 10105, "Session Grid Energy", Kind.AC),
        # Power source bitmask: bit0=grid, bit1=PV, bit2=battery
        Integer("power_source_code", 10108, "Charge Power Source Code", "", Kind.AC),
        PowerSourceSensor("power_source", 10108, "Charge Power Source", Kind.AC),
    )

    __all_settings: tuple[Sensor, ...] = (
        Integer("ems_dispatch", 10000, "EMS Energy Dispatch"),
        Integer("plug_and_charge", 10019, "Plug and Charge Enable"),
        Integer("dynamic_load_mgmt", 10025, "Dynamic Load Management Enable"),
        Decimal("max_charging_power", 10029, 10, "Max Charging Power", "kW"),
        # 0=fast charge, 1=PV only, 2=PV+battery
        Integer("advanced_charging_mode", 10032, "Advanced Charging Mode"),
        Decimal("grid_power_limit", 10039, 10, "Grid Power Limit", "kW"),
        # Register 10060: 1=off, 2=on (non-standard values)
        SwitchValue("charge_enabled", 10060, "Charge Enabled", on_value=2, off_value=1),
    )

    def __init__(self, host: str, port: int = GOODWE_TCP_PORT, comm_addr: int = 0xF7,
                 timeout: int = 1, retries: int = 3):
        super().__init__(host, port, comm_addr, timeout, retries)
        # Device info: register 10040, count 20 (registers 10040-10059)
        self._READ_DEVICE_INFO: ProtocolCommand = self._read_command(10040, 20)
        # Runtime block 1: register 10000, count 19 (registers 10000-10018)
        self._READ_RUNNING_DATA: ProtocolCommand = self._read_command(10000, 19)
        # Runtime block 2: register 10060, count 49 (registers 10060-10108)
        self._READ_RUNNING_DATA2: ProtocolCommand = self._read_command(10060, 49)
        self._is_single_phase: bool = False
        self._sensors_block1: tuple[Sensor, ...] = self.__sensors_block1_3phase
        self._sensors_map: dict[str, Sensor] | None = None
        self._settings_map: dict[str, Sensor] = {s.id_: s for s in self.__all_settings}

    async def read_device_info(self):
        response = await self._read_from_socket(self._READ_DEVICE_INFO)
        raw = response.response_data()
        # Registers 10040-10047 (8 regs = 16 bytes): SN Number
        self.serial_number = self._decode(raw[0:16])
        # Registers 10048-10049 (2 regs = 4 bytes): Software version external
        self.firmware = self._decode(raw[16:20])
        # Register 10050 (1 reg = 2 bytes): SVN version (offset 20-21)
        # Registers 10056-10057 (2 regs = 4 bytes): Hardware Version (offset 32-35)
        self.model_name = self._decode(raw[32:36])
        # Register 10058 (1 reg = 2 bytes): Power Spec (offset 36-37)
        power_spec = int.from_bytes(raw[36:38], byteorder='big', signed=False)
        # Register 10059 (1 reg = 2 bytes): Phase type (offset 38-39)
        phase_type = int.from_bytes(raw[38:40], byteorder='big', signed=False)
        self._is_single_phase = (phase_type == 1)
        if self._is_single_phase:
            self._sensors_block1 = self.__sensors_block1_1phase
        else:
            self._sensors_block1 = self.__sensors_block1_3phase
        self._sensors_map = None
        power_spec_names = {0: "7kW", 1: "11kW", 2: "22kW"}
        power_spec_str = power_spec_names.get(power_spec, str(power_spec))
        phase_str = "single-phase" if self._is_single_phase else "3-phase"
        logger.debug(
            "HCA device: S/N=%s, fw=%s, hw=%s, power=%s, phase=%s",
            self.serial_number, self.firmware, self.model_name, power_spec_str, phase_str,
        )

    @property
    def is_single_phase(self) -> bool:
        """Return True if device is a single-phase charger."""
        return self._is_single_phase

    async def read_runtime_data(self) -> dict[str, Any]:
        response1 = await self._read_from_socket(self._READ_RUNNING_DATA)
        response2 = await self._read_from_socket(self._READ_RUNNING_DATA2)
        data = self._map_response(response1, self._sensors_block1)
        data.update(self._map_response(response2, self.__sensors_block2))
        data["serial_number"] = self.serial_number
        return data

    def _get_sensor(self, sensor_id: str) -> Sensor | None:
        if self._sensors_map is None:
            self._sensors_map = {s.id_: s for s in self.sensors()}
        return self._sensors_map.get(sensor_id)

    async def read_sensor(self, sensor_id: str) -> Any:
        sensor = self._get_sensor(sensor_id)
        if sensor:
            count = (sensor.size_ + (sensor.size_ % 2)) // 2
            response = await self._read_from_socket(self._read_command(sensor.offset, count))
            return sensor.read_value(response)
        if sensor_id.startswith("modbus"):
            response = await self._read_from_socket(self._read_command(int(sensor_id[7:]), 1))
            return int.from_bytes(response.read(2), byteorder="big", signed=True)
        raise ValueError(f'Unknown sensor "{sensor_id}"')

    async def read_setting(self, setting_id: str) -> Any:
        setting = self._settings_map.get(setting_id)
        if setting:
            count = (setting.size_ + (setting.size_ % 2)) // 2
            response = await self._read_from_socket(self._read_command(setting.offset, count))
            return setting.read_value(response)
        if setting_id.startswith("modbus"):
            response = await self._read_from_socket(self._read_command(int(setting_id[7:]), 1))
            return int.from_bytes(response.read(2), byteorder="big", signed=True)
        raise ValueError(f'Unknown setting "{setting_id}"')

    async def write_setting(self, setting_id: str, value: Any):
        setting = self._settings_map.get(setting_id)
        if setting:
            raw_value = setting.encode_value(value)
            int_value = int.from_bytes(raw_value, byteorder="big", signed=False)
            await self._read_from_socket(self._write_command(setting.offset, int_value))
        elif setting_id.startswith("modbus"):
            await self._read_from_socket(self._write_command(int(setting_id[7:]), int(value)))
        else:
            raise ValueError(f'Unknown setting "{setting_id}"')

    async def read_settings_data(self) -> dict[str, Any]:
        data = {}
        for setting in self.__all_settings:
            try:
                data[setting.id_] = await self.read_setting(setting.id_)
            except (ValueError, RequestFailedException):
                logger.exception("Error reading setting %s.", setting.id_)
                data[setting.id_] = None
        return data

    async def get_grid_export_limit(self) -> int:
        raise InverterError("Not supported by HCA EV charger")

    async def set_grid_export_limit(self, export_limit: int) -> None:
        raise InverterError("Not supported by HCA EV charger")

    async def get_operation_modes(self, include_emulated: bool) -> tuple[OperationMode, ...]:
        return ()

    async def get_operation_mode(self) -> OperationMode:
        raise InverterError("Not supported by HCA EV charger")

    async def set_operation_mode(self, operation_mode: OperationMode, eco_mode_power: int = 100,
                                 eco_mode_soc: int = 100) -> None:
        raise InverterError("Not supported by HCA EV charger")

    async def get_ongrid_battery_dod(self) -> int:
        raise InverterError("Not supported by HCA EV charger")

    async def set_ongrid_battery_dod(self, dod: int) -> None:
        raise InverterError("Not supported by HCA EV charger")

    @property
    def sensor_name_prefix(self) -> str:
        """Generate entity ID prefix based on last 4 characters of serial number."""
        if self.serial_number and len(self.serial_number) >= 4:
            return f"GW{self.serial_number[-4:]}_"
        return ""

    def sensors(self) -> tuple[Sensor, ...]:
        return self._sensors_block1 + self.__sensors_block2

    def settings(self) -> tuple[Sensor, ...]:
        return tuple(self._settings_map.values())
