"""HCA EV charger support - GoodWe HCA/HCA G2 EV charger series"""
from __future__ import annotations

import logging
from typing import Any, Optional

from .const import GOODWE_TCP_PORT
from .exceptions import InverterError, RequestFailedException
from .inverter import Inverter, OperationMode, Sensor, SensorKind as Kind
from .protocol import ProtocolCommand, ProtocolResponse
from .sensor import (
    Current, Energy, Energy4, Enum2, Integer, Long, Power, Voltage,
    read_bytes4,
)

logger = logging.getLogger(__name__)


CP_STATUS_MODES: dict[int, str] = {
    0: "Disconnected",
    1: "Connected",
    2: "Charging",
    3: "Fault",
}

EV_CHARGER_STATUS_MODES: dict[int, str] = {
    0: "Initial",
    1: "Fault",
    2: "Standby",
    3: "Running",
    4: "Shutdown",
    5: "Reserved",
    6: "Self-testing",
    7: "Starting",
    8: "Ready",
}

CHARGING_MODES: dict[int, str] = {
    0: "Plug and Play",
    1: "Scheduled",
    2: "PV Only",
    3: "Plug and Play + Scheduled",
}


class Hours4(Sensor):
    """Sensor representing time [h] value encoded in 4 (unsigned) bytes, scale factor 10"""

    def __init__(self, id_: str, offset: int, name: str, kind: Optional[Kind] = None):
        super().__init__(id_, offset, name, 4, "h", kind)

    def read_value(self, data: ProtocolResponse) -> Any:
        value = read_bytes4(data)
        return float(value) / 10 if value is not None else None

    def encode_value(self, value: Any, register_value: bytes = None) -> bytes:
        raise NotImplementedError()


class HCA(Inverter):
    """Class representing GoodWe HCA/HCA G2 EV charger series.

    Communicates via standard Modbus TCP (port 502).
    Supported models: GW7K-HCA-20 (1-phase), GW11K-HCA-20 (3-phase), GW22K-HCA-20 (3-phase).
    Model tag in serial number: HPA (e.g. 5022KHPA257L2133).
    """

    # Modbus registers 10600-10621, count 22
    __all_sensors: tuple[Sensor, ...] = (
        Voltage("cp_voltage", 10600, "CP Voltage", Kind.AC),
        Integer("leak_current", 10601, "Leak Current", "mA", Kind.AC),
        Integer("cp_status", 10602, "CP Status code", "", Kind.AC),
        Enum2("cp_status_label", 10602, CP_STATUS_MODES, "CP Status", Kind.AC),
        Power("solar_power_for_charge", 10603, "Solar Power for Charge", Kind.PV),
        Power("battery_power_for_charge", 10604, "Battery Power for Charge", Kind.BAT),
        Power("grid_power_for_charge", 10605, "Grid Power for Charge", Kind.GRID),
        Energy("charge_energy", 10606, "Current Charge Energy", Kind.AC),
        Integer("charge_time", 10607, "Current Charge Time", "min", Kind.AC),
        Current("charge_current", 10608, "Charge Current", Kind.AC),
        Integer("charger_status", 10609, "EV Charger Status code", "", Kind.AC),
        Enum2("charger_status_label", 10609, EV_CHARGER_STATUS_MODES, "EV Charger Status", Kind.AC),
        Long("charger_error", 10610, "EV Charger Error Message"),
        Integer("charging_mode", 10612, "Charging Mode code", "", Kind.AC),
        Enum2("charging_mode_label", 10612, CHARGING_MODES, "Charging Mode", Kind.AC),
        Integer("max_charge_current", 10613, "Max Charge Current", "A", Kind.AC),
        Power("charge_power", 10614, "Charge Power", Kind.AC),
        Energy4("total_charge_energy", 10615, "Total Charge Energy", Kind.AC),
        Hours4("total_charge_time", 10617, "Total Charge Time"),
        Voltage("ev_output_voltage", 10619, "EV Output Voltage", Kind.AC),
        Voltage("ac_input_voltage", 10620, "AC Input Voltage", Kind.AC),
        Integer("ev_com_lost", 10621, "EV Communication Lost", "", Kind.AC),
    )

    __all_settings: tuple[Sensor, ...] = (
        Integer("charging_mode_set", 20320, "Charging Mode"),
        Integer("max_charge_current_set", 20323, "Max Charge Current", "A"),
        Integer("off_grid_charge_enable", 20332, "Off Grid Charge Enable"),
    )

    def __init__(self, host: str, port: int = GOODWE_TCP_PORT, comm_addr: int = 0,
                 timeout: int = 1, retries: int = 3):
        super().__init__(host, port, comm_addr, timeout, retries)
        # Device info registers: 10670 (SW ver) + 10671-10678 (SN 8 regs) + 10679-10694 (model 16 regs) = 25 regs
        self._READ_DEVICE_INFO: ProtocolCommand = self._read_command(10670, 25)
        # Runtime data: registers 10600-10621, count 22
        self._READ_RUNNING_DATA: ProtocolCommand = self._read_command(10600, 22)
        self._sensors: tuple[Sensor, ...] = self.__all_sensors
        self._sensors_map: dict[str, Sensor] | None = None
        self._settings_map: dict[str, Sensor] = {s.id_: s for s in self.__all_settings}

    async def read_device_info(self):
        response = await self._read_from_socket(self._READ_DEVICE_INFO)
        raw = response.response_data()
        # Register 10670: Software Version (2 bytes)
        self.dsp1_version = int.from_bytes(raw[0:2], byteorder='big', signed=False)
        self.firmware = str(self.dsp1_version)
        # Registers 10671-10678: EV Charger SN (8 registers = 16 bytes)
        self.serial_number = self._decode(raw[2:18])
        # Registers 10679-10694: EV Charger Model Name (16 registers = 32 bytes)
        self.model_name = self._decode(raw[18:50])
        logger.debug("HCA device: model=%s, S/N=%s, fw=%s", self.model_name, self.serial_number, self.firmware)

    async def read_runtime_data(self) -> dict[str, Any]:
        response = await self._read_from_socket(self._READ_RUNNING_DATA)
        data = self._map_response(response, self._sensors)
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
        return self._sensors

    def settings(self) -> tuple[Sensor, ...]:
        return tuple(self._settings_map.values())
