"""Hybrid inverter support aka platform 205, 745, 753"""
from __future__ import annotations

import logging
from typing import Any

from .const import *
from .exceptions import RequestFailedException, RequestRejectedException
from .inverter import Inverter, OperationMode, SensorKind as Kind
from .modbus import ILLEGAL_DATA_ADDRESS
from .model import is_1_battery, is_2_battery, is_3_mppt, is_4_mppt, is_745_platform, is_single_phase
from .protocol import ProtocolCommand
from .sensor import *

logger = logging.getLogger(__name__)


class ET(Inverter):
    """Class representing inverter of ET/EH/BT/BH or GE's GEH families AKA platform 205 or 745"""

    # Modbus registers from offset 0x891c (35100), count 0x7d (125)
    __all_sensors: tuple[Sensor, ...] = (
        Timestamp("timestamp", 35100, "Timestamp"),
        Voltage("vpv1", 35103, "PV1 Voltage", Kind.PV),
        Current("ipv1", 35104, "PV1 Current", Kind.PV),
        Power4("ppv1", 35105, "PV1 Power", Kind.PV),
        Voltage("vpv2", 35107, "PV2 Voltage", Kind.PV),
        Current("ipv2", 35108, "PV2 Current", Kind.PV),
        Power4("ppv2", 35109, "PV2 Power", Kind.PV),
        Voltage("vpv3", 35111, "PV3 Voltage", Kind.PV),
        Current("ipv3", 35112, "PV3 Current", Kind.PV),
        Power4("ppv3", 35113, "PV3 Power", Kind.PV),
        Voltage("vpv4", 35115, "PV4 Voltage", Kind.PV),
        Current("ipv4", 35116, "PV4 Current", Kind.PV),
        Power4("ppv4", 35117, "PV4 Power", Kind.PV),
        # ppv1 + ppv2 + ppv3 + ppv4
        Calculated("ppv",
                   lambda data:
                   max(0, read_bytes4(data, 35105, 0)) +
                   max(0, read_bytes4(data, 35109, 0)) +
                   max(0, read_bytes4(data, 35113, 0)) +
                   max(0, read_bytes4(data, 35117, 0)),
                   "PV Power", "W", Kind.PV),
        ByteH("pv4_mode", 35119, "PV4 Mode code", "", Kind.PV),
        EnumH("pv4_mode_label", 35119, PV_MODES, "PV4 Mode", Kind.PV),
        ByteL("pv3_mode", 35119, "PV3 Mode code", "", Kind.PV),
        EnumL("pv3_mode_label", 35119, PV_MODES, "PV3 Mode", Kind.PV),
        ByteH("pv2_mode", 35120, "PV2 Mode code", "", Kind.PV),
        EnumH("pv2_mode_label", 35120, PV_MODES, "PV2 Mode", Kind.PV),
        ByteL("pv1_mode", 35120, "PV1 Mode code", "", Kind.PV),
        EnumL("pv1_mode_label", 35120, PV_MODES, "PV1 Mode", Kind.PV),
        Voltage("vgrid", 35121, "On-grid L1 Voltage", Kind.AC),
        Current("igrid", 35122, "On-grid L1 Current", Kind.AC),
        Frequency("fgrid", 35123, "On-grid L1 Frequency", Kind.AC),
        # 35124 reserved
        PowerS("pgrid", 35125, "On-grid L1 Power", Kind.AC),
        Voltage("vgrid2", 35126, "On-grid L2 Voltage", Kind.AC),
        Current("igrid2", 35127, "On-grid L2 Current", Kind.AC),
        Frequency("fgrid2", 35128, "On-grid L2 Frequency", Kind.AC),
        # 35129 reserved
        PowerS("pgrid2", 35130, "On-grid L2 Power", Kind.AC),
        Voltage("vgrid3", 35131, "On-grid L3 Voltage", Kind.AC),
        Current("igrid3", 35132, "On-grid L3 Current", Kind.AC),
        Frequency("fgrid3", 35133, "On-grid L3 Frequency", Kind.AC),
        # 35134 reserved
        PowerS("pgrid3", 35135, "On-grid L3 Power", Kind.AC),
        Integer("grid_mode", 35136, "Grid Mode code", "", Kind.PV),
        Enum2("grid_mode_label", 35136, GRID_MODES, "Grid Mode", Kind.PV),
        # 35137 reserved
        PowerS("total_inverter_power", 35138, "Total Power", Kind.AC),
        # 35139 reserved
        PowerS("active_power", 35140, "Active Power", Kind.GRID),
        Calculated("grid_in_out",
                   lambda data: read_grid_mode(data, 35140),
                   "On-grid Mode code", "", Kind.GRID),
        EnumCalculated("grid_in_out_label",
                       lambda data: read_grid_mode(data, 35140), GRID_IN_OUT_MODES,
                       "On-grid Mode", Kind.GRID),
        # 35141 reserved
        Reactive("reactive_power", 35142, "Reactive Power", Kind.GRID),
        # 35143 reserved
        Apparent("apparent_power", 35144, "Apparent Power", Kind.GRID),
        Voltage("backup_v1", 35145, "Back-up L1 Voltage", Kind.UPS),
        Current("backup_i1", 35146, "Back-up L1 Current", Kind.UPS),
        Frequency("backup_f1", 35147, "Back-up L1 Frequency", Kind.UPS),
        Integer("load_mode1", 35148, "Load Mode L1"),
        # 35149 reserved
        PowerS("backup_p1", 35150, "Back-up L1 Power", Kind.UPS),
        Voltage("backup_v2", 35151, "Back-up L2 Voltage", Kind.UPS),
        Current("backup_i2", 35152, "Back-up L2 Current", Kind.UPS),
        Frequency("backup_f2", 35153, "Back-up L2 Frequency", Kind.UPS),
        Integer("load_mode2", 35154, "Load Mode L2"),
        # 35155 reserved
        PowerS("backup_p2", 35156, "Back-up L2 Power", Kind.UPS),
        Voltage("backup_v3", 35157, "Back-up L3 Voltage", Kind.UPS),
        Current("backup_i3", 35158, "Back-up L3 Current", Kind.UPS),
        Frequency("backup_f3", 35159, "Back-up L3 Frequency", Kind.UPS),
        Integer("load_mode3", 35160, "Load Mode L3"),
        # 35161 reserved
        PowerS("backup_p3", 35162, "Back-up L3 Power", Kind.UPS),
        # 35163 reserved
        PowerS("load_p1", 35164, "Load L1", Kind.AC),
        # 35165 reserved
        PowerS("load_p2", 35166, "Load L2", Kind.AC),
        # 35167 reserved
        PowerS("load_p3", 35168, "Load L3", Kind.AC),
        # 35169 reserved
        PowerS("backup_ptotal", 35170, "Back-up Load", Kind.UPS),
        # 35171 reserved
        PowerS("load_ptotal", 35172, "Load", Kind.AC),
        Integer("ups_load", 35173, "Ups Load", "%", Kind.UPS),
        Temp("temperature_air", 35174, "Inverter Temperature (Air)", Kind.AC),
        Temp("temperature_module", 35175, "Inverter Temperature (Module)"),
        Temp("temperature", 35176, "Inverter Temperature (Radiator)", Kind.AC),
        Integer("function_bit", 35177, "Function Bit"),
        Voltage("bus_voltage", 35178, "Bus Voltage", None),
        Voltage("nbus_voltage", 35179, "NBus Voltage", None),
        Voltage("vbattery1", 35180, "Battery Voltage", Kind.BAT),
        CurrentS("ibattery1", 35181, "Battery Current", Kind.BAT),
        Power4S("pbattery1", 35182, "Battery Power", Kind.BAT),
        Integer("battery_mode", 35184, "Battery Mode code", "", Kind.BAT),
        Enum2("battery_mode_label", 35184, BATTERY_MODES, "Battery Mode", Kind.BAT),
        Integer("warning_code", 35185, "Warning code"),
        Integer("safety_country", 35186, "Safety Country code", "", Kind.AC),
        Enum2("safety_country_label", 35186, SAFETY_COUNTRIES, "Safety Country", Kind.AC),
        Integer("work_mode", 35187, "Work Mode code"),
        Enum2("work_mode_label", 35187, WORK_MODES_ET, "Work Mode"),
        Integer("operation_mode", 35188, "Operation Mode code"),
        Long("error_codes", 35189, "Error Codes"),
        EnumBitmap4("errors", 35189, ERROR_CODES, "Errors"),
        Energy4("e_total", 35191, "Total PV Generation", Kind.PV),
        Energy4("e_day", 35193, "Today's PV Generation", Kind.PV),
        Energy4("e_total_exp", 35195, "Total Energy (export)", Kind.AC),
        Long("h_total", 35197, "Hours Total", "h", Kind.PV),
        Energy("e_day_exp", 35199, "Today Energy (export)", Kind.AC),
        Energy4("e_total_imp", 35200, "Total Energy (import)", Kind.AC),
        Energy("e_day_imp", 35202, "Today Energy (import)", Kind.AC),
        Energy4("e_load_total", 35203, "Total Load", Kind.AC),
        Energy("e_load_day", 35205, "Today Load", Kind.AC),
        Energy4("e_bat_charge_total", 35206, "Total Battery Charge", Kind.BAT),
        Energy("e_bat_charge_day", 35208, "Today Battery Charge", Kind.BAT),
        Energy4("e_bat_discharge_total", 35209, "Total Battery Discharge", Kind.BAT),
        Energy("e_bat_discharge_day", 35211, "Today Battery Discharge", Kind.BAT),
        Long("diagnose_result", 35220, "Diag Status Code"),
        EnumBitmap4("diagnose_result_label", 35220, DIAG_STATUS_CODES, "Diag Status"),
        # ppv1 + ppv2 + ppv3 + ppv4 + pbattery1 - active_power
        Calculated("house_consumption",
                   lambda data:
                   read_bytes4(data, 35105, 0) +
                   read_bytes4(data, 35109, 0) +
                   read_bytes4(data, 35113, 0) +
                   read_bytes4(data, 35117, 0) +
                   read_bytes4_signed(data, 35182) -
                   read_bytes2_signed(data, 35140),
                   "House Consumption", "W", Kind.AC),

        # TOU (Time of Use) Slots 1-8
        # Writable settings exposed as sensors for visibility in HA
        # Slots 1-4 require ARM firmware 19+, slots 5-8 require firmware 22+
        TimeOfDay("tou_slot1_start_time", 47547, "TOU Slot 1 Start Time", Kind.BAT),
        TimeOfDay("tou_slot1_end_time", 47548, "TOU Slot 1 End Time", Kind.BAT),
        WorkWeekV2("tou_slot1_work_week", 47549, "TOU Slot 1 Work Week", Kind.BAT),
        Integer("tou_slot1_param1", 47550, "TOU Slot 1 Parameter 1", "", Kind.BAT),
        Integer("tou_slot1_param2", 47551, "TOU Slot 1 Parameter 2", "", Kind.BAT),
        MonthMask("tou_slot1_months", 47552, "TOU Slot 1 Months", Kind.BAT),
        TimeOfDay("tou_slot2_start_time", 47553, "TOU Slot 2 Start Time", Kind.BAT),
        TimeOfDay("tou_slot2_end_time", 47554, "TOU Slot 2 End Time", Kind.BAT),
        WorkWeekV2("tou_slot2_work_week", 47555, "TOU Slot 2 Work Week", Kind.BAT),
        Integer("tou_slot2_param1", 47556, "TOU Slot 2 Parameter 1", "", Kind.BAT),
        Integer("tou_slot2_param2", 47557, "TOU Slot 2 Parameter 2", "", Kind.BAT),
        MonthMask("tou_slot2_months", 47558, "TOU Slot 2 Months", Kind.BAT),
        TimeOfDay("tou_slot3_start_time", 47559, "TOU Slot 3 Start Time", Kind.BAT),
        TimeOfDay("tou_slot3_end_time", 47560, "TOU Slot 3 End Time", Kind.BAT),
        WorkWeekV2("tou_slot3_work_week", 47561, "TOU Slot 3 Work Week", Kind.BAT),
        Integer("tou_slot3_param1", 47562, "TOU Slot 3 Parameter 1", "", Kind.BAT),
        Integer("tou_slot3_param2", 47563, "TOU Slot 3 Parameter 2", "", Kind.BAT),
        MonthMask("tou_slot3_months", 47564, "TOU Slot 3 Months", Kind.BAT),
        TimeOfDay("tou_slot4_start_time", 47565, "TOU Slot 4 Start Time", Kind.BAT),
        TimeOfDay("tou_slot4_end_time", 47566, "TOU Slot 4 End Time", Kind.BAT),
        WorkWeekV2("tou_slot4_work_week", 47567, "TOU Slot 4 Work Week", Kind.BAT),
        Integer("tou_slot4_param1", 47568, "TOU Slot 4 Parameter 1", "", Kind.BAT),
        Integer("tou_slot4_param2", 47569, "TOU Slot 4 Parameter 2", "", Kind.BAT),
        MonthMask("tou_slot4_months", 47570, "TOU Slot 4 Months", Kind.BAT),
        TimeOfDay("tou_slot5_start_time", 47571, "TOU Slot 5 Start Time", Kind.BAT),
        TimeOfDay("tou_slot5_end_time", 47572, "TOU Slot 5 End Time", Kind.BAT),
        WorkWeekV2("tou_slot5_work_week", 47573, "TOU Slot 5 Work Week", Kind.BAT),
        Integer("tou_slot5_param1", 47574, "TOU Slot 5 Parameter 1", "", Kind.BAT),
        Integer("tou_slot5_param2", 47575, "TOU Slot 5 Parameter 2", "", Kind.BAT),
        MonthMask("tou_slot5_months", 47576, "TOU Slot 5 Months", Kind.BAT),
        TimeOfDay("tou_slot6_start_time", 47577, "TOU Slot 6 Start Time", Kind.BAT),
        TimeOfDay("tou_slot6_end_time", 47578, "TOU Slot 6 End Time", Kind.BAT),
        WorkWeekV2("tou_slot6_work_week", 47579, "TOU Slot 6 Work Week", Kind.BAT),
        Integer("tou_slot6_param1", 47580, "TOU Slot 6 Parameter 1", "", Kind.BAT),
        Integer("tou_slot6_param2", 47581, "TOU Slot 6 Parameter 2", "", Kind.BAT),
        MonthMask("tou_slot6_months", 47582, "TOU Slot 6 Months", Kind.BAT),
        TimeOfDay("tou_slot7_start_time", 47583, "TOU Slot 7 Start Time", Kind.BAT),
        TimeOfDay("tou_slot7_end_time", 47584, "TOU Slot 7 End Time", Kind.BAT),
        WorkWeekV2("tou_slot7_work_week", 47585, "TOU Slot 7 Work Week", Kind.BAT),
        Integer("tou_slot7_param1", 47586, "TOU Slot 7 Parameter 1", "", Kind.BAT),
        Integer("tou_slot7_param2", 47587, "TOU Slot 7 Parameter 2", "", Kind.BAT),
        MonthMask("tou_slot7_months", 47588, "TOU Slot 7 Months", Kind.BAT),
        TimeOfDay("tou_slot8_start_time", 47589, "TOU Slot 8 Start Time", Kind.BAT),
        TimeOfDay("tou_slot8_end_time", 47590, "TOU Slot 8 End Time", Kind.BAT),
        WorkWeekV2("tou_slot8_work_week", 47591, "TOU Slot 8 Work Week", Kind.BAT),
        Integer("tou_slot8_param1", 47592, "TOU Slot 8 Parameter 1", "", Kind.BAT),
        Integer("tou_slot8_param2", 47593, "TOU Slot 8 Parameter 2", "", Kind.BAT),
        MonthMask("tou_slot8_months", 47594, "TOU Slot 8 Months", Kind.BAT),

        # Serial Number is added manually in read_runtime_data() at line 892
        # It's already available in device info, no need to expose as sensor

        # Power4S("pbattery2", 35264, "Battery2 Power", Kind.BAT),
        # Integer("battery2_mode", 35266, "Battery2 Mode code", "", Kind.BAT),
        # Enum2("battery2_mode_label", 35184, BATTERY_MODES, "Battery2 Mode", Kind.BAT),
    )

    # Modbus registers from offset 0x9088 (37000)
    __all_sensors_battery: tuple[Sensor, ...] = (
        Integer("battery_bms", 37000, "Battery BMS", "", Kind.BAT),
        Integer("battery_index", 37001, "Battery Index", "", Kind.BAT),
        Integer("battery_status", 37002, "Battery Status", "", Kind.BAT),
        Temp("battery_temperature", 37003, "Battery Temperature", Kind.BAT),
        Integer("battery_charge_limit", 37004, "Battery Charge Limit", "A", Kind.BAT),
        Integer("battery_discharge_limit", 37005, "Battery Discharge Limit", "A", Kind.BAT),
        Integer("battery_error_l", 37006, "Battery Error L", "", Kind.BAT),
        Integer("battery_soc", 37007, "Battery State of Charge", "%", Kind.BAT),
        Integer("battery_soh", 37008, "Battery State of Health", "%", Kind.BAT),
        Integer("battery_modules", 37009, "Battery Modules", "", Kind.BAT),
        Integer("battery_warning_l", 37010, "Battery Warning L", "", Kind.BAT),
        Integer("battery_protocol", 37011, "Battery Protocol", "", Kind.BAT),
        Integer("battery_error_h", 37012, "Battery Error H", "", Kind.BAT),
        EnumBitmap22("battery_error", 37012, 37006, BMS_ALARM_CODES, "Battery Error", Kind.BAT),
        Integer("battery_warning_h", 37013, "Battery Warning H", "", Kind.BAT),
        EnumBitmap22("battery_warning", 37013, 37010, BMS_WARNING_CODES, "Battery Warning", Kind.BAT),
        Integer("battery_sw_version", 37014, "Battery Software Version", "", Kind.BAT),
        Integer("battery_hw_version", 37015, "Battery Hardware Version", "", Kind.BAT),
        Integer("battery_max_cell_temp_id", 37016, "Battery Max Cell Temperature ID", "", Kind.BAT),
        Integer("battery_min_cell_temp_id", 37017, "Battery Min Cell Temperature ID", "", Kind.BAT),
        Integer("battery_max_cell_voltage_id", 37018, "Battery Max Cell Voltage ID", "", Kind.BAT),
        Integer("battery_min_cell_voltage_id", 37019, "Battery Min Cell Voltage ID", "", Kind.BAT),
        Temp("battery_max_cell_temp", 37020, "Battery Max Cell Temperature", Kind.BAT),
        Temp("battery_min_cell_temp", 37021, "Battery Min Cell Temperature", Kind.BAT),
        CellVoltage("battery_max_cell_voltage", 37022, "Battery Max Cell Voltage", Kind.BAT),
        CellVoltage("battery_min_cell_voltage", 37023, "Battery Min Cell Voltage", Kind.BAT),
        # Energy4("battery_total_charge", 37056, "Total Battery 1 Charge", Kind.BAT),
        # Energy4("battery_total_discharge", 37058, "Total Battery 1 Discharge", Kind.BAT),
        # String8("battery_sn", 37060, "Battery S/N", Kind.BAT),
    )

    # Modbus registers from offset 0x9858 (39000)
    __all_sensors_battery2: tuple[Sensor, ...] = (
        Integer("battery2_status", 39000, "Battery 2 Status", "", Kind.BAT),
        Temp("battery2_temperature", 39001, "Battery 2 Temperature", Kind.BAT),
        Integer("battery2_charge_limit", 39002, "Battery 2 Charge Limit", "A", Kind.BAT),
        Integer("battery2_discharge_limit", 39003, "Battery 2 Discharge Limit", "A", Kind.BAT),
        Integer("battery2_error_l", 39004, "Battery 2 rror L", "", Kind.BAT),
        Integer("battery2_soc", 39005, "Battery 2 State of Charge", "%", Kind.BAT),
        Integer("battery2_soh", 39006, "Battery 2 State of Health", "%", Kind.BAT),
        Integer("battery2_modules", 39007, "Battery 2 Modules", "", Kind.BAT),
        Integer("battery2_warning_l", 39008, "Battery 2 Warning L", "", Kind.BAT),
        Integer("battery2_protocol", 39009, "Battery 2 Protocol", "", Kind.BAT),
        Integer("battery2_error_h", 39010, "Battery 2 Error H", "", Kind.BAT),
        EnumBitmap22("battery2_error", 39010, 39004, BMS_ALARM_CODES, "Battery 2 Error", Kind.BAT),
        Integer("battery2_warning_h", 39011, "Battery 2 Warning H", "", Kind.BAT),
        EnumBitmap22("battery2_warning", 39011, 39008, BMS_WARNING_CODES, "Battery 2 Warning", Kind.BAT),
        Integer("battery2_sw_version", 39012, "Battery 2 Software Version", "", Kind.BAT),
        Integer("battery2_hw_version", 39013, "Battery 2 Hardware Version", "", Kind.BAT),
        Integer("battery2_max_cell_temp_id", 39014, "Battery 2 Max Cell Temperature ID", "", Kind.BAT),
        Integer("battery2_min_cell_temp_id", 39015, "Battery 2 Min Cell Temperature ID", "", Kind.BAT),
        Integer("battery2_max_cell_voltage_id", 39016, "Battery 2 Max Cell Voltage ID", "", Kind.BAT),
        Integer("battery2_min_cell_voltage_id", 39017, "Battery 2 Min Cell Voltage ID", "", Kind.BAT),
        Temp("battery2_max_cell_temp", 39018, "Battery 2 Max Cell Temperature", Kind.BAT),
        Temp("battery2_min_cell_temp", 39019, "Battery 2 Min Cell Temperature", Kind.BAT),
        CellVoltage("battery2_max_cell_voltage", 39020, "Battery 2 Max Cell Voltage", Kind.BAT),
        CellVoltage("battery2_min_cell_voltage", 39021, "Battery 2 Min Cell Voltage", Kind.BAT),
        # Energy4("battery2_total_charge", 39054, "Total Battery 2 Charge", Kind.BAT),
        # Energy4("battery2_total_discharge", 39056, "Total Battery 2 Discharge", Kind.BAT),
        # String8("battery2_sn", 39058, "Battery 2 S/N", Kind.BAT),
    )

    # Inverter's meter data
    # Modbus registers from offset 0x8ca0 (36000)
    __all_sensors_meter: tuple[Sensor, ...] = (
        Integer("commode", 36000, "Commode"),
        Integer("rssi", 36001, "RSSI"),
        Integer("manufacture_code", 36002, "Manufacture Code"),
        Integer("meter_test_status", 36003, "Meter Test Status"),  # 1: correct，2: reverse，3: incorrect，0: not checked
        Integer("meter_comm_status", 36004, "Meter Communication Status"),  # 1 OK, 0 NotOK
        PowerS("active_power1", 36005, "Active Power L1", Kind.GRID),
        PowerS("active_power2", 36006, "Active Power L2", Kind.GRID),
        PowerS("active_power3", 36007, "Active Power L3", Kind.GRID),
        PowerS("active_power_total", 36008, "Active Power Total", Kind.GRID),
        Reactive("reactive_power_total", 36009, "Reactive Power Total", Kind.GRID),
        Decimal("meter_power_factor1", 36010, 1000, "Meter Power Factor L1", "", Kind.GRID),
        Decimal("meter_power_factor2", 36011, 1000, "Meter Power Factor L2", "", Kind.GRID),
        Decimal("meter_power_factor3", 36012, 1000, "Meter Power Factor L3", "", Kind.GRID),
        Decimal("meter_power_factor", 36013, 1000, "Meter Power Factor", "", Kind.GRID),
        Frequency("meter_freq", 36014, "Meter Frequency", Kind.GRID),
        Float("meter_e_total_exp", 36015, 1000, "Meter Total Energy (export)", "kWh", Kind.GRID),
        Float("meter_e_total_imp", 36017, 1000, "Meter Total Energy (import)", "kWh", Kind.GRID),
        Power4S("meter_active_power1", 36019, "Meter Active Power L1", Kind.GRID),
        Power4S("meter_active_power2", 36021, "Meter Active Power L2", Kind.GRID),
        Power4S("meter_active_power3", 36023, "Meter Active Power L3", Kind.GRID),
        Power4S("meter_active_power_total", 36025, "Meter Active Power Total", Kind.GRID),
        Reactive4("meter_reactive_power1", 36027, "Meter Reactive Power L1", Kind.GRID),
        Reactive4("meter_reactive_power2", 36029, "Meter Reactive Power L2", Kind.GRID),
        Reactive4("meter_reactive_power3", 36031, "Meter Reactive Power L3", Kind.GRID),
        Reactive4("meter_reactive_power_total", 36033, "Meter Reactive Power Total", Kind.GRID),
        Apparent4("meter_apparent_power1", 36035, "Meter Apparent Power L1", Kind.GRID),
        Apparent4("meter_apparent_power2", 36037, "Meter Apparent Power L2", Kind.GRID),
        Apparent4("meter_apparent_power3", 36039, "Meter Apparent Power L3", Kind.GRID),
        Apparent4("meter_apparent_power_total", 36041, "Meter Apparent Power Total", Kind.GRID),
        Integer("meter_type", 36043, "Meter Type", "", Kind.GRID),  # (0: Single phase, 1: 3P3W, 2: 3P4W, 3: HomeKit)
        Integer("meter_sw_version", 36044, "Meter Software Version", "", Kind.GRID),

        # Sensors added in some ARM fw update (or platform 745/753), read when flag _has_meter_extended is on
        Power4S("meter2_active_power", 36045, "Meter 2 Active Power", Kind.GRID),
        Float("meter2_e_total_exp", 36047, 1000, "Meter 2 Total Energy (export)", "kWh", Kind.GRID),
        Float("meter2_e_total_imp", 36049, 1000, "Meter 2 Total Energy (import)", "kWh", Kind.GRID),
        Integer("meter2_comm_status", 36051, "Meter 2 Communication Status"),
        Voltage("meter_voltage1", 36052, "Meter L1 Voltage", Kind.GRID),
        Voltage("meter_voltage2", 36053, "Meter L2 Voltage", Kind.GRID),
        Voltage("meter_voltage3", 36054, "Meter L3 Voltage", Kind.GRID),
        Current("meter_current1", 36055, "Meter L1 Current", Kind.GRID),
        Current("meter_current2", 36056, "Meter L2 Current", Kind.GRID),
        Current("meter_current3", 36057, "Meter L3 Current", Kind.GRID),

        Energy8("meter_e_total_exp_l1", 36092, "Meter Total Energy (export) L1", Kind.GRID),
        Energy8("meter_e_total_exp_l2", 36096, "Meter Total Energy (export) L2", Kind.GRID),
        Energy8("meter_e_total_exp_l3", 36100, "Meter Total Energy (export) L3", Kind.GRID),
        Energy8("meter_e_total_exp_sum", 36104, "Meter Total Energy (export) Sum", Kind.GRID),
        Energy8("meter_e_total_imp_l1", 36108, "Meter Total Energy (import) L1", Kind.GRID),
        Energy8("meter_e_total_imp_l2", 36112, "Meter Total Energy (import) L2", Kind.GRID),
        Energy8("meter_e_total_imp_l3", 36116, "Meter Total Energy (import) L3", Kind.GRID),
        Energy8("meter_e_total_imp_sum", 36120, "Meter Total Energy (import) Sum", Kind.GRID),
    )

    # Inverter's MPPT data
    # Modbus registers from offset 0x89e5 (35301)
    __all_sensors_mppt: tuple[Sensor, ...] = (
        Power4("ppv_total", 35301, "PV Power Total", Kind.PV),
        Integer("pv_channel", 35303, "PV Channel", "", Kind.PV),
        Voltage("vpv5", 35304, "PV5 Voltage", Kind.PV),
        Current("ipv5", 35305, "PV5 Current", Kind.PV),
        Voltage("vpv6", 35306, "PV6 Voltage", Kind.PV),
        Current("ipv6", 35307, "PV6 Current", Kind.PV),
        Voltage("vpv7", 35308, "PV7 Voltage", Kind.PV),
        Current("ipv7", 35309, "PV7 Current", Kind.PV),
        Voltage("vpv8", 35310, "PV8 Voltage", Kind.PV),
        Current("ipv8", 35311, "PV8 Current", Kind.PV),
        Voltage("vpv9", 35312, "PV9 Voltage", Kind.PV),
        Current("ipv9", 35313, "PV9 Current", Kind.PV),
        Voltage("vpv10", 35314, "PV10 Voltage", Kind.PV),
        Current("ipv10", 35315, "PV10 Current", Kind.PV),
        Voltage("vpv11", 35316, "PV11 Voltage", Kind.PV),
        Current("ipv11", 35317, "PV11 Current", Kind.PV),
        Voltage("vpv12", 35318, "PV12 Voltage", Kind.PV),
        Current("ipv12", 35319, "PV12 Current", Kind.PV),
        Voltage("vpv13", 35320, "PV13 Voltage", Kind.PV),
        Current("ipv13", 35321, "PV13 Current", Kind.PV),
        Voltage("vpv14", 35322, "PV14 Voltage", Kind.PV),
        Current("ipv14", 35323, "PV14 Current", Kind.PV),
        Voltage("vpv15", 35324, "PV15 Voltage", Kind.PV),
        Current("ipv15", 35325, "PV15 Current", Kind.PV),
        Voltage("vpv16", 35326, "PV16 Voltage", Kind.PV),
        Current("ipv16", 35327, "PV16 Current", Kind.PV),
        # 35328 Warning Message
        # 35330 Grid10minAvgVoltR
        # 35331 Grid10minAvgVoltS
        # 35332 Grid10minAvgVoltT
        # 35333 Error Message Extend
        # 35335 Warning Message Extend
        Power("pmppt1", 35337, "MPPT1 Power", Kind.PV),
        Power("pmppt2", 35338, "MPPT2 Power", Kind.PV),
        Power("pmppt3", 35339, "MPPT3 Power", Kind.PV),
        Power("pmppt4", 35340, "MPPT4 Power", Kind.PV),
        Power("pmppt5", 35341, "MPPT5 Power", Kind.PV),
        Power("pmppt6", 35342, "MPPT6 Power", Kind.PV),
        Power("pmppt7", 35343, "MPPT7 Power", Kind.PV),
        Power("pmppt8", 35344, "MPPT8 Power", Kind.PV),
        Current("imppt1", 35345, "MPPT1 Current", Kind.PV),
        Current("imppt2", 35346, "MPPT2 Current", Kind.PV),
        Current("imppt3", 35347, "MPPT3 Current", Kind.PV),
        Current("imppt4", 35348, "MPPT4 Current", Kind.PV),
        Current("imppt5", 35349, "MPPT5 Current", Kind.PV),
        Current("imppt6", 35350, "MPPT6 Current", Kind.PV),
        Current("imppt7", 35351, "MPPT7 Current", Kind.PV),
        Current("imppt8", 35352, "MPPT8 Current", Kind.PV),
        Reactive4("reactive_power1", 35353, "Reactive Power L1", Kind.GRID),
        Reactive4("reactive_power2", 35355, "Reactive Power L2", Kind.GRID),
        Reactive4("reactive_power3", 35357, "Reactive Power L3", Kind.GRID),
        Apparent4("apparent_power1", 35359, "Apparent Power L1", Kind.GRID),
        Apparent4("apparent_power2", 35361, "Apparent Power L2", Kind.GRID),
        Apparent4("apparent_power3", 35363, "Apparent Power L3", Kind.GRID),
    )

    # Parallel inverter system data
    # Modbus registers from offset 0x28a0 (10400)
    __all_sensors_parallel: tuple[Sensor, ...] = (
        Integer("parallel_inverter_quantity", 10400, "Master Inverter Quantity", "", Kind.AC),
        Integer("parallel_firmware_version_arm", 10401, "Master Firmware Version ARM", "", Kind.AC),
        Integer("parallel_firmware_version_dsp_master", 10402, "Master Firmware Version DSP Master", "", Kind.AC),
        Integer("parallel_firmware_version_dsp_slave", 10403, "Master Firmware Version DSP Slave", "", Kind.AC),
        Integer("parallel_online_quantity", 10404, "Master Online Quantity", "", Kind.AC),
        Integer("parallel_app_mode", 10405, "Master APP Mode", "", Kind.AC),
        Integer("parallel_safety_country", 10406, "Master Safety Country", "", Kind.AC),
        Integer("parallel_work_mode", 10407, "Master Work Mode", "", Kind.AC),
        Integer("parallel_meter_comm_status", 10408, "Master Meter Comm Status", "", Kind.GRID),
        Integer("parallel_backup_enable", 10409, "Master BackUp Enable", "", Kind.UPS),
        Integer("parallel_controller_status_code", 10410, "Master Controller Status Code", "", Kind.AC),
        # 10411 reserved
        Power4("parallel_pv_total_power", 10412, "Master PV Total Power", Kind.PV),
        Power4S("parallel_battery_total_power", 10414, "Master Battery Total Power", Kind.BAT),
        Power4S("parallel_total_backup_load_power", 10416, "Master Total Back-Up Load Power", Kind.UPS),
        Power4S("parallel_meter_power", 10418, "Master Meter Power", Kind.GRID),
        Power4S("parallel_total_inverter_power", 10420, "Master Total Inverter Power", Kind.AC),
        Power4S("parallel_l1_inverter_power", 10422, "Master L1 Inverter Power", Kind.AC),
        Power4S("parallel_l2_inverter_power", 10424, "Master L2 Inverter Power", Kind.AC),
        Power4S("parallel_l3_inverter_power", 10426, "Master L3 Inverter Power", Kind.AC),
        Power4S("parallel_backup_active_power_r", 10428, "Master Back-Up Active Power R", Kind.UPS),
        Power4S("parallel_backup_active_power_s", 10430, "Master Back-Up Active Power S", Kind.UPS),
        Power4S("parallel_backup_active_power_t", 10432, "Master Back-Up Active Power T", Kind.UPS),
        Decimal("parallel_meter_frequency", 10434, 100, "Master Meter Frequency", "Hz", Kind.GRID),
        Integer("parallel_battery_mode", 10435, "Master Battery Mode", "", Kind.BAT),
        Decimal("parallel_battery_voltage_1", 10436, 10, "Master Battery Voltage 1", "V", Kind.BAT),
        Decimal("parallel_battery_voltage_2", 10437, 10, "Master Battery Voltage 2", "V", Kind.BAT),
        Power4("parallel_total_inverter_power_rated", 10438, "Master Total Inverter Power (rated)", Kind.AC),
        # 10439-10469 reserved
        Integer("parallel_meter_check_value", 10470, "Master Meter Check Value", "", Kind.GRID),
        Integer("parallel_meter_connect_check_flag", 10471, "Master Meter Connect Check Flag", "", Kind.GRID),
        Integer("parallel_soc", 10472, "Master SOC", "%", Kind.BAT),
        Integer("parallel_battery_capacity", 10473, "Master Battery Capacity", "Ah", Kind.BAT),
        Integer("parallel_battery_communication", 10474, "Master Battery Communication Status", "", Kind.BAT),
        # 10475 reserved
        Energy4W("parallel_battery_charge_allow_kwh", 10476, "Master Battery Charge Allow kWh", Kind.BAT),
        Energy4W("parallel_battery_discharge_allow_kwh", 10478, "Master Battery Discharge Allow kWh", Kind.BAT),
        Integer("parallel_able_balance_flag", 10480, "Master Able Balance Flag", "", Kind.BAT),
        Power4S("parallel_meter_active_power_r", 10481, "Master Meter Active Power L1", Kind.GRID),
        Power4S("parallel_meter_active_power_s", 10483, "Master Meter Active Power L2", Kind.GRID),
        Power4S("parallel_meter_active_power_t", 10485, "Master Meter Active Power L3", Kind.GRID),
        # NOTE: Calculated current sensors (I = P / V) are computed in read_runtime_data()
        # and added directly to data dict, not read from Modbus registers
        # Undocumented parallel registers 10486-10499 (observed with data)
        Integer("parallel_unknown_10486", 10486, "Parallel Unknown 10486", "", Kind.AC),
        Integer("parallel_unknown_10487", 10487, "Parallel Unknown 10487", "", Kind.AC),
        Integer("parallel_unknown_10488", 10488, "Parallel Unknown 10488", "", Kind.AC),
        Integer("parallel_unknown_10489", 10489, "Parallel Unknown 10489", "", Kind.AC),
        Integer("parallel_unknown_10490", 10490, "Parallel Unknown 10490", "", Kind.AC),
        Integer("parallel_unknown_10491", 10491, "Parallel Unknown 10491", "", Kind.AC),
        Integer("parallel_unknown_10492", 10492, "Parallel Unknown 10492", "", Kind.AC),
        Integer("parallel_unknown_10493", 10493, "Parallel Unknown 10493", "", Kind.AC),
        Integer("parallel_unknown_10494", 10494, "Parallel Unknown 10494", "", Kind.AC),
        Integer("parallel_unknown_10495", 10495, "Parallel Unknown 10495", "", Kind.AC),
        Integer("parallel_unknown_10496", 10496, "Parallel Unknown 10496", "", Kind.AC),
        Integer("parallel_unknown_10497", 10497, "Parallel Unknown 10497", "", Kind.AC),
        Integer("parallel_unknown_10498", 10498, "Parallel Unknown 10498", "", Kind.AC),
        Integer("parallel_unknown_10499", 10499, "Parallel Unknown 10499", "", Kind.AC),
    )

    # Undocumented sensors for observation - 48xxx block (Slave-specific battery data)
    # These registers contain battery information readable from slave inverters
    # Key registers: 48011=discharge limit, 48012=charge limit, 48013=SOC
    __observation_sensors_48xxx: tuple[Sensor, ...] = (
        Long("obs_48000", 48000, "Obs 48000 (Battery Info)", "", Kind.BAT),
        Long("obs_48002", 48002, "Obs 48002 (Battery Energy?)", "", Kind.BAT),
        Integer("obs_48004", 48004, "Obs 48004 (Unknown)", "", Kind.BAT),
        Long("obs_48005", 48005, "Obs 48005 (Capacity?)", "", Kind.BAT),
        Integer("obs_48007", 48007, "Obs 48007 (Unknown)", "", Kind.BAT),
        Long("obs_48008", 48008, "Obs 48008 (Energy?)", "", Kind.BAT),
        Long("obs_48010", 48010, "Obs 48010 (Energy?)", "", Kind.BAT),
        Integer("obs_battery_discharge_limit", 48011, "Obs Battery Discharge Current Limit", "A", Kind.BAT),
        Integer("obs_battery_charge_limit", 48012, "Obs Battery Charge Current Limit", "A", Kind.BAT),
        Integer("obs_battery_soc_48013", 48013, "Obs Battery SOC (Slave)", "%", Kind.BAT),
        Integer("obs_48014", 48014, "Obs 48014 (Voltage?)", "", Kind.BAT),
        Integer("obs_48015", 48015, "Obs 48015 (Voltage?)", "", Kind.BAT),
        Integer("obs_48016", 48016, "Obs 48016 (Voltage?)", "", Kind.BAT),
        Integer("obs_48017", 48017, "Obs 48017 (Status?)", "", Kind.BAT),
        Long("obs_48018", 48018, "Obs 48018 (Power?)", "", Kind.BAT),
        Long("obs_48020", 48020, "Obs 48020 (Power?)", "", Kind.BAT),
        Integer("obs_48022", 48022, "Obs 48022 (Voltage?)", "", Kind.BAT),
        Integer("obs_48023", 48023, "Obs 48023 (Voltage?)", "", Kind.BAT),
        Integer("obs_48024", 48024, "Obs 48024 (Voltage?)", "", Kind.BAT),
        Integer("obs_48025", 48025, "Obs 48025 (Unknown)", "", Kind.BAT),
        Integer("obs_48026", 48026, "Obs 48026 (Unknown)", "", Kind.BAT),
        # 48046-48076 contain additional battery data (voltages, powers)
        Long("obs_48046", 48046, "Obs 48046 (Power?)", "", Kind.BAT),
        Long("obs_48048", 48048, "Obs 48048 (Power?)", "", Kind.BAT),
        Long("obs_48050", 48050, "Obs 48050 (Power?)", "", Kind.BAT),
        Long("obs_48052", 48052, "Obs 48052 (Power?)", "", Kind.BAT),
        Long("obs_48054", 48054, "Obs 48054 (Energy?)", "", Kind.BAT),
        Long("obs_48056", 48056, "Obs 48056 (Energy?)", "", Kind.BAT),
        Long("obs_48058", 48058, "Obs 48058 (Energy?)", "", Kind.BAT),
        Long("obs_48060", 48060, "Obs 48060 (Energy?)", "", Kind.BAT),
        Integer("obs_48064", 48064, "Obs 48064 (Status?)", "", Kind.BAT),
        Integer("obs_48065", 48065, "Obs 48065 (Unknown)", "", Kind.BAT),
        Integer("obs_48066", 48066, "Obs 48066 (Capacity?)", "", Kind.BAT),
        # New sensors from full scan
        Integer("obs_48001", 48001, "Obs 48001", "", Kind.BAT),
        Integer("obs_48003", 48003, "Obs 48003", "", Kind.BAT),
        Integer("obs_48006", 48006, "Obs 48006", "", Kind.BAT),
        Integer("obs_48009", 48009, "Obs 48009", "", Kind.BAT),
        Integer("obs_48019", 48019, "Obs 48019", "", Kind.BAT),
        Integer("obs_48021", 48021, "Obs 48021", "", Kind.BAT),
        Integer("obs_48027", 48027, "Obs 48027", "", Kind.BAT),
        Integer("obs_48028", 48028, "Obs 48028", "", Kind.BAT),
        Integer("obs_48029", 48029, "Obs 48029", "", Kind.BAT),
        Integer("obs_48030", 48030, "Obs 48030", "", Kind.BAT),
        Integer("obs_48031", 48031, "Obs 48031", "", Kind.BAT),
        Integer("obs_48032", 48032, "Obs 48032", "", Kind.BAT),
        Integer("obs_48033", 48033, "Obs 48033", "", Kind.BAT),
        Integer("obs_48034", 48034, "Obs 48034", "", Kind.BAT),
        Integer("obs_48035", 48035, "Obs 48035", "", Kind.BAT),
        Integer("obs_48036", 48036, "Obs 48036", "", Kind.BAT),
        Integer("obs_48037", 48037, "Obs 48037", "", Kind.BAT),
        Integer("obs_48038", 48038, "Obs 48038", "", Kind.BAT),
        Integer("obs_48039", 48039, "Obs 48039", "", Kind.BAT),
        Integer("obs_48040", 48040, "Obs 48040", "", Kind.BAT),
        Integer("obs_48041", 48041, "Obs 48041", "", Kind.BAT),
        Integer("obs_48042", 48042, "Obs 48042", "", Kind.BAT),
        Integer("obs_48043", 48043, "Obs 48043", "", Kind.BAT),
        Integer("obs_48044", 48044, "Obs 48044", "", Kind.BAT),
        Integer("obs_48045", 48045, "Obs 48045", "", Kind.BAT),
        Integer("obs_48047", 48047, "Obs 48047", "", Kind.BAT),
        Integer("obs_48049", 48049, "Obs 48049", "", Kind.BAT),
        Integer("obs_48051", 48051, "Obs 48051", "", Kind.BAT),
        Integer("obs_48053", 48053, "Obs 48053", "", Kind.BAT),
        Integer("obs_48055", 48055, "Obs 48055", "", Kind.BAT),
        Integer("obs_48057", 48057, "Obs 48057", "", Kind.BAT),
        Integer("obs_48059", 48059, "Obs 48059", "", Kind.BAT),
        Integer("obs_48061", 48061, "Obs 48061", "", Kind.BAT),
        Integer("obs_48062", 48062, "Obs 48062", "", Kind.BAT),
        Integer("obs_48063", 48063, "Obs 48063", "", Kind.BAT),
        Integer("obs_48067", 48067, "Obs 48067", "", Kind.BAT),
        Integer("obs_48068", 48068, "Obs 48068", "", Kind.BAT),
        Integer("obs_48069", 48069, "Obs 48069", "", Kind.BAT),
        Integer("obs_48070", 48070, "Obs 48070", "", Kind.BAT),
        Integer("obs_48071", 48071, "Obs 48071", "", Kind.BAT),
        Integer("obs_48072", 48072, "Obs 48072", "", Kind.BAT),
        Integer("obs_48073", 48073, "Obs 48073", "", Kind.BAT),
        Integer("obs_48074", 48074, "Obs 48074", "", Kind.BAT),
        Integer("obs_48075", 48075, "Obs 48075", "", Kind.BAT),
        Integer("obs_48076", 48076, "Obs 48076", "", Kind.BAT),
        Integer("obs_48077", 48077, "Obs 48077", "", Kind.BAT),
        Integer("obs_48078", 48078, "Obs 48078", "", Kind.BAT),
        Integer("obs_48079", 48079, "Obs 48079", "", Kind.BAT),
        Integer("obs_48080", 48080, "Obs 48080", "", Kind.BAT),
        Integer("obs_48081", 48081, "Obs 48081", "", Kind.BAT),
        Integer("obs_48082", 48082, "Obs 48082", "", Kind.BAT),
        Integer("obs_48083", 48083, "Obs 48083", "", Kind.BAT),
        Integer("obs_48084", 48084, "Obs 48084", "", Kind.BAT),
        Integer("obs_48085", 48085, "Obs 48085", "", Kind.BAT),
        Integer("obs_48086", 48086, "Obs 48086", "", Kind.BAT),
        Integer("obs_48087", 48087, "Obs 48087", "", Kind.BAT),
        Integer("obs_48088", 48088, "Obs 48088", "", Kind.BAT),
        Integer("obs_48089", 48089, "Obs 48089", "", Kind.BAT),
        Integer("obs_48090", 48090, "Obs 48090", "", Kind.BAT),
        Integer("obs_48091", 48091, "Obs 48091", "", Kind.BAT),
        Integer("obs_48092", 48092, "Obs 48092", "", Kind.BAT),
        Integer("obs_48093", 48093, "Obs 48093", "", Kind.BAT),
        Integer("obs_48094", 48094, "Obs 48094", "", Kind.BAT),
        Integer("obs_48095", 48095, "Obs 48095", "", Kind.BAT),
        Integer("obs_48096", 48096, "Obs 48096", "", Kind.BAT),
        Integer("obs_48097", 48097, "Obs 48097", "", Kind.BAT),
        Integer("obs_48098", 48098, "Obs 48098", "", Kind.BAT),
        Integer("obs_48099", 48099, "Obs 48099", "", Kind.BAT),
        Integer("obs_48131", 48131, "Obs 48131", "", Kind.BAT),
        Integer("obs_48132", 48132, "Obs 48132", "", Kind.BAT),
        Integer("obs_48133", 48133, "Obs 48133", "", Kind.BAT),
        Integer("obs_48134", 48134, "Obs 48134", "", Kind.BAT),
        Integer("obs_48135", 48135, "Obs 48135", "", Kind.BAT),
        Integer("obs_48136", 48136, "Obs 48136", "", Kind.BAT),
        Integer("obs_48140", 48140, "Obs 48140", "", Kind.BAT),
        Integer("obs_48141", 48141, "Obs 48141", "", Kind.BAT),
        Integer("obs_48142", 48142, "Obs 48142", "", Kind.BAT),
        Integer("obs_48143", 48143, "Obs 48143", "", Kind.BAT),
        Integer("obs_48144", 48144, "Obs 48144", "", Kind.BAT),
        Integer("obs_48145", 48145, "Obs 48145", "", Kind.BAT),
        Integer("obs_48146", 48146, "Obs 48146", "", Kind.BAT),
        Integer("obs_48147", 48147, "Obs 48147", "", Kind.BAT),
        Integer("obs_48148", 48148, "Obs 48148", "", Kind.BAT),
        Integer("obs_48149", 48149, "Obs 48149", "", Kind.BAT),
        Integer("obs_48150", 48150, "Obs 48150", "", Kind.BAT),
        Integer("obs_48151", 48151, "Obs 48151", "", Kind.BAT),
        Integer("obs_48152", 48152, "Obs 48152", "", Kind.BAT),
        Integer("obs_48153", 48153, "Obs 48153", "", Kind.BAT),
        Integer("obs_48154", 48154, "Obs 48154", "", Kind.BAT),
        Integer("obs_48155", 48155, "Obs 48155", "", Kind.BAT),
        Integer("obs_48156", 48156, "Obs 48156", "", Kind.BAT),
        Integer("obs_48157", 48157, "Obs 48157", "", Kind.BAT),
        Integer("obs_48158", 48158, "Obs 48158", "", Kind.BAT),
        Integer("obs_48159", 48159, "Obs 48159", "", Kind.BAT),
        Integer("obs_48160", 48160, "Obs 48160", "", Kind.BAT),
        Integer("obs_48161", 48161, "Obs 48161", "", Kind.BAT),
        Integer("obs_48162", 48162, "Obs 48162", "", Kind.BAT),
        Integer("obs_48163", 48163, "Obs 48163", "", Kind.BAT),
        Integer("obs_48164", 48164, "Obs 48164", "", Kind.BAT),
        Integer("obs_48165", 48165, "Obs 48165", "", Kind.BAT),
        Integer("obs_48166", 48166, "Obs 48166", "", Kind.BAT),
        Integer("obs_48167", 48167, "Obs 48167", "", Kind.BAT),
        Integer("obs_48168", 48168, "Obs 48168", "", Kind.BAT),
        Integer("obs_48169", 48169, "Obs 48169", "", Kind.BAT),
        Integer("obs_48170", 48170, "Obs 48170", "", Kind.BAT),
        Integer("obs_48171", 48171, "Obs 48171", "", Kind.BAT),
        Integer("obs_48172", 48172, "Obs 48172", "", Kind.BAT),
        Integer("obs_48173", 48173, "Obs 48173", "", Kind.BAT),
        Integer("obs_48174", 48174, "Obs 48174", "", Kind.BAT),
        Integer("obs_48175", 48175, "Obs 48175", "", Kind.BAT),
        Integer("obs_48176", 48176, "Obs 48176", "", Kind.BAT),
        Integer("obs_48177", 48177, "Obs 48177", "", Kind.BAT),
        Integer("obs_48178", 48178, "Obs 48178", "", Kind.BAT),
        Integer("obs_48179", 48179, "Obs 48179", "", Kind.BAT),
        Integer("obs_48180", 48180, "Obs 48180", "", Kind.BAT),
        Integer("obs_48181", 48181, "Obs 48181", "", Kind.BAT),
        Integer("obs_48182", 48182, "Obs 48182", "", Kind.BAT),
        Integer("obs_48183", 48183, "Obs 48183", "", Kind.BAT),
        Integer("obs_48184", 48184, "Obs 48184", "", Kind.BAT),
        Integer("obs_48185", 48185, "Obs 48185", "", Kind.BAT),
        Integer("obs_48186", 48186, "Obs 48186", "", Kind.BAT),
        Integer("obs_48187", 48187, "Obs 48187", "", Kind.BAT),
        Integer("obs_48188", 48188, "Obs 48188", "", Kind.BAT),
        Integer("obs_48189", 48189, "Obs 48189", "", Kind.BAT),
        Integer("obs_48190", 48190, "Obs 48190", "", Kind.BAT),
        Integer("obs_48191", 48191, "Obs 48191", "", Kind.BAT),
        Integer("obs_48192", 48192, "Obs 48192", "", Kind.BAT),
        Integer("obs_48193", 48193, "Obs 48193", "", Kind.BAT),
        Integer("obs_48194", 48194, "Obs 48194", "", Kind.BAT),
        Integer("obs_48195", 48195, "Obs 48195", "", Kind.BAT),
        Integer("obs_48196", 48196, "Obs 48196", "", Kind.BAT),
        Integer("obs_48197", 48197, "Obs 48197", "", Kind.BAT),
        Integer("obs_48198", 48198, "Obs 48198", "", Kind.BAT),
        Integer("obs_48199", 48199, "Obs 48199", "", Kind.BAT),
        Integer("obs_48200", 48200, "Obs 48200", "", Kind.BAT),
        Integer("obs_48201", 48201, "Obs 48201", "", Kind.BAT),
        Integer("obs_48202", 48202, "Obs 48202", "", Kind.BAT),
        Integer("obs_48203", 48203, "Obs 48203", "", Kind.BAT),
        Integer("obs_48204", 48204, "Obs 48204", "", Kind.BAT),
        Integer("obs_48205", 48205, "Obs 48205", "", Kind.BAT),
        Integer("obs_48206", 48206, "Obs 48206", "", Kind.BAT),
        Integer("obs_48207", 48207, "Obs 48207", "", Kind.BAT),
        Integer("obs_48208", 48208, "Obs 48208", "", Kind.BAT),
        Integer("obs_48209", 48209, "Obs 48209", "", Kind.BAT),
        Integer("obs_48210", 48210, "Obs 48210", "", Kind.BAT),
        Integer("obs_48211", 48211, "Obs 48211", "", Kind.BAT),
        Integer("obs_48212", 48212, "Obs 48212", "", Kind.BAT),
        Integer("obs_48213", 48213, "Obs 48213", "", Kind.BAT),
        Integer("obs_48214", 48214, "Obs 48214", "", Kind.BAT),
        Integer("obs_48215", 48215, "Obs 48215", "", Kind.BAT),
        Integer("obs_48216", 48216, "Obs 48216", "", Kind.BAT),
        Integer("obs_48217", 48217, "Obs 48217", "", Kind.BAT),
        Integer("obs_48218", 48218, "Obs 48218", "", Kind.BAT),
        Integer("obs_48219", 48219, "Obs 48219", "", Kind.BAT),
        Integer("obs_48220", 48220, "Obs 48220", "", Kind.BAT),
        Integer("obs_48221", 48221, "Obs 48221", "", Kind.BAT),
        Integer("obs_48222", 48222, "Obs 48222", "", Kind.BAT),
        Integer("obs_48223", 48223, "Obs 48223", "", Kind.BAT),
        Integer("obs_48224", 48224, "Obs 48224", "", Kind.BAT),
        Integer("obs_48225", 48225, "Obs 48225", "", Kind.BAT),
        Integer("obs_48226", 48226, "Obs 48226", "", Kind.BAT),
        Integer("obs_48227", 48227, "Obs 48227", "", Kind.BAT),
        Integer("obs_48228", 48228, "Obs 48228", "", Kind.BAT),
        Integer("obs_48229", 48229, "Obs 48229", "", Kind.BAT),
        Integer("obs_48230", 48230, "Obs 48230", "", Kind.BAT),
        Integer("obs_48231", 48231, "Obs 48231", "", Kind.BAT),
        Integer("obs_48232", 48232, "Obs 48232", "", Kind.BAT),
        Integer("obs_48233", 48233, "Obs 48233", "", Kind.BAT),
        Integer("obs_48234", 48234, "Obs 48234", "", Kind.BAT),
        Integer("obs_48235", 48235, "Obs 48235", "", Kind.BAT),
        Integer("obs_48236", 48236, "Obs 48236", "", Kind.BAT),
        Integer("obs_48237", 48237, "Obs 48237", "", Kind.BAT),
        Integer("obs_48238", 48238, "Obs 48238", "", Kind.BAT),
        Integer("obs_48239", 48239, "Obs 48239", "", Kind.BAT),
        Integer("obs_48240", 48240, "Obs 48240", "", Kind.BAT),
        Integer("obs_48241", 48241, "Obs 48241", "", Kind.BAT),
        Integer("obs_48242", 48242, "Obs 48242", "", Kind.BAT),
        Integer("obs_48243", 48243, "Obs 48243", "", Kind.BAT),
        Integer("obs_48244", 48244, "Obs 48244", "", Kind.BAT),
        Integer("obs_48245", 48245, "Obs 48245", "", Kind.BAT),
        Integer("obs_48246", 48246, "Obs 48246", "", Kind.BAT),
        Integer("obs_48247", 48247, "Obs 48247", "", Kind.BAT),
        Integer("obs_48248", 48248, "Obs 48248", "", Kind.BAT),
        Integer("obs_48249", 48249, "Obs 48249", "", Kind.BAT),
        Integer("obs_48250", 48250, "Obs 48250", "", Kind.BAT),
        Integer("obs_48251", 48251, "Obs 48251", "", Kind.BAT),
        Integer("obs_48252", 48252, "Obs 48252", "", Kind.BAT),
        Integer("obs_48253", 48253, "Obs 48253", "", Kind.BAT),
        Integer("obs_48254", 48254, "Obs 48254", "", Kind.BAT),
        Integer("obs_48255", 48255, "Obs 48255", "", Kind.BAT),
        Integer("obs_48256", 48256, "Obs 48256", "", Kind.BAT),
        Integer("obs_48257", 48257, "Obs 48257", "", Kind.BAT),
        Integer("obs_48258", 48258, "Obs 48258", "", Kind.BAT),
        Integer("obs_48259", 48259, "Obs 48259", "", Kind.BAT),
        Integer("obs_48260", 48260, "Obs 48260", "", Kind.BAT),
        Integer("obs_48261", 48261, "Obs 48261", "", Kind.BAT),
        Integer("obs_48262", 48262, "Obs 48262", "", Kind.BAT),
        Integer("obs_48263", 48263, "Obs 48263", "", Kind.BAT),
        Integer("obs_48264", 48264, "Obs 48264", "", Kind.BAT),
        Integer("obs_48265", 48265, "Obs 48265", "", Kind.BAT),
        Integer("obs_48266", 48266, "Obs 48266", "", Kind.BAT),
        Integer("obs_48267", 48267, "Obs 48267", "", Kind.BAT),
        Integer("obs_48268", 48268, "Obs 48268", "", Kind.BAT),
        Integer("obs_48269", 48269, "Obs 48269", "", Kind.BAT),
        Integer("obs_48270", 48270, "Obs 48270", "", Kind.BAT),
        Integer("obs_48271", 48271, "Obs 48271", "", Kind.BAT),
        Integer("obs_48272", 48272, "Obs 48272", "", Kind.BAT),
        Integer("obs_48273", 48273, "Obs 48273", "", Kind.BAT),
        Integer("obs_48274", 48274, "Obs 48274", "", Kind.BAT),
        Integer("obs_48275", 48275, "Obs 48275", "", Kind.BAT),
        Integer("obs_48276", 48276, "Obs 48276", "", Kind.BAT),
        Integer("obs_48277", 48277, "Obs 48277", "", Kind.BAT),
        Integer("obs_48278", 48278, "Obs 48278", "", Kind.BAT),
        Integer("obs_48279", 48279, "Obs 48279", "", Kind.BAT),
        Integer("obs_48280", 48280, "Obs 48280", "", Kind.BAT),
        Integer("obs_48281", 48281, "Obs 48281", "", Kind.BAT),
        Integer("obs_48282", 48282, "Obs 48282", "", Kind.BAT),
        Integer("obs_48283", 48283, "Obs 48283", "", Kind.BAT),
        Integer("obs_48284", 48284, "Obs 48284", "", Kind.BAT),
        Integer("obs_48285", 48285, "Obs 48285", "", Kind.BAT),
        Integer("obs_48286", 48286, "Obs 48286", "", Kind.BAT),
        Integer("obs_48287", 48287, "Obs 48287", "", Kind.BAT),
        Integer("obs_48288", 48288, "Obs 48288", "", Kind.BAT),
        Integer("obs_48289", 48289, "Obs 48289", "", Kind.BAT),
        Integer("obs_48290", 48290, "Obs 48290", "", Kind.BAT),
        Integer("obs_48291", 48291, "Obs 48291", "", Kind.BAT),
        Integer("obs_48292", 48292, "Obs 48292", "", Kind.BAT),
        Integer("obs_48293", 48293, "Obs 48293", "", Kind.BAT),
        Integer("obs_48294", 48294, "Obs 48294", "", Kind.BAT),
        Integer("obs_48295", 48295, "Obs 48295", "", Kind.BAT),
        Integer("obs_48296", 48296, "Obs 48296", "", Kind.BAT),
        Integer("obs_48297", 48297, "Obs 48297", "", Kind.BAT),
        Integer("obs_48298", 48298, "Obs 48298", "", Kind.BAT),
        Integer("obs_48299", 48299, "Obs 48299", "", Kind.BAT),
        Integer("obs_48500", 48500, "Obs 48500", "", Kind.BAT),
        Integer("obs_48501", 48501, "Obs 48501", "", Kind.BAT),
        Integer("obs_48502", 48502, "Obs 48502", "", Kind.BAT),
        Integer("obs_48503", 48503, "Obs 48503", "", Kind.BAT),
        Integer("obs_48504", 48504, "Obs 48504", "", Kind.BAT),
        Integer("obs_48505", 48505, "Obs 48505", "", Kind.BAT),
        Integer("obs_48506", 48506, "Obs 48506", "", Kind.BAT),
        Integer("obs_48507", 48507, "Obs 48507", "", Kind.BAT),
        Integer("obs_48508", 48508, "Obs 48508", "", Kind.BAT),
        Integer("obs_48509", 48509, "Obs 48509", "", Kind.BAT),
        Integer("obs_48510", 48510, "Obs 48510", "", Kind.BAT),
        Integer("obs_48511", 48511, "Obs 48511", "", Kind.BAT),
        Integer("obs_48512", 48512, "Obs 48512", "", Kind.BAT),
        Integer("obs_48513", 48513, "Obs 48513", "", Kind.BAT),
        Integer("obs_48514", 48514, "Obs 48514", "", Kind.BAT),
        Integer("obs_48515", 48515, "Obs 48515", "", Kind.BAT),
        Integer("obs_48516", 48516, "Obs 48516", "", Kind.BAT),
        Integer("obs_48517", 48517, "Obs 48517", "", Kind.BAT),
        Integer("obs_48518", 48518, "Obs 48518", "", Kind.BAT),
        Integer("obs_48519", 48519, "Obs 48519", "", Kind.BAT),
        Integer("obs_48520", 48520, "Obs 48520", "", Kind.BAT),
        Integer("obs_48521", 48521, "Obs 48521", "", Kind.BAT),
        Integer("obs_48522", 48522, "Obs 48522", "", Kind.BAT),
        Integer("obs_48800", 48800, "Obs 48800", "", Kind.BAT),
        Integer("obs_48801", 48801, "Obs 48801", "", Kind.BAT),
        Integer("obs_48802", 48802, "Obs 48802", "", Kind.BAT),
        Integer("obs_48803", 48803, "Obs 48803", "", Kind.BAT),
        Integer("obs_48804", 48804, "Obs 48804", "", Kind.BAT),
        Integer("obs_48805", 48805, "Obs 48805", "", Kind.BAT),
        Integer("obs_48806", 48806, "Obs 48806", "", Kind.BAT),
    )

    # Undocumented sensors - 33xxx block (Grid configuration/limits?)
    __observation_sensors_33xxx: tuple[Sensor, ...] = (
        Integer("obs_33002", 33002, "Obs 33002 (Limit?)", "", Kind.GRID),
        Integer("obs_33005", 33005, "Obs 33005 (Limit?)", "", Kind.GRID),
        Integer("obs_33007", 33007, "Obs 33007 (Limit?)", "", Kind.GRID),
        Integer("obs_33010", 33010, "Obs 33010 (Power?)", "", Kind.GRID),
        Integer("obs_33012", 33012, "Obs 33012 (Power?)", "", Kind.GRID),
        Integer("obs_33015", 33015, "Obs 33015 (Unknown)", "", Kind.GRID),
        Integer("obs_33017", 33017, "Obs 33017 (Limit?)", "", Kind.GRID),
        Integer("obs_33050", 33050, "Obs 33050 (Power?)", "", Kind.GRID),
        Integer("obs_33052", 33052, "Obs 33052 (Power?)", "", Kind.GRID),
        Integer("obs_33054", 33054, "Obs 33054 (Power?)", "", Kind.GRID),
        Integer("obs_33071", 33071, "Obs 33071 (Unknown)", "", Kind.GRID),
        Integer("obs_33072", 33072, "Obs 33072 (Unknown)", "", Kind.GRID),
        Integer("obs_33073", 33073, "Obs 33073 (Unknown)", "", Kind.GRID),
        Integer("obs_33074", 33074, "Obs 33074 (Unknown)", "", Kind.GRID),
        Integer("obs_33079", 33079, "Obs 33079 (Unknown)", "", Kind.GRID),
        # New sensors from full scan
        Integer("obs_33000", 33000, "Obs 33000", "", Kind.GRID),
        Integer("obs_33001", 33001, "Obs 33001", "", Kind.GRID),
        Integer("obs_33003", 33003, "Obs 33003", "", Kind.GRID),
        Integer("obs_33004", 33004, "Obs 33004", "", Kind.GRID),
        Integer("obs_33006", 33006, "Obs 33006", "", Kind.GRID),
        Integer("obs_33008", 33008, "Obs 33008", "", Kind.GRID),
        Integer("obs_33009", 33009, "Obs 33009", "", Kind.GRID),
        Integer("obs_33011", 33011, "Obs 33011", "", Kind.GRID),
        Integer("obs_33013", 33013, "Obs 33013", "", Kind.GRID),
        Integer("obs_33014", 33014, "Obs 33014", "", Kind.GRID),
        Integer("obs_33016", 33016, "Obs 33016", "", Kind.GRID),
        Integer("obs_33018", 33018, "Obs 33018", "", Kind.GRID),
        Integer("obs_33019", 33019, "Obs 33019", "", Kind.GRID),
        Integer("obs_33020", 33020, "Obs 33020", "", Kind.GRID),
        Integer("obs_33021", 33021, "Obs 33021", "", Kind.GRID),
        Integer("obs_33022", 33022, "Obs 33022", "", Kind.GRID),
        Integer("obs_33023", 33023, "Obs 33023", "", Kind.GRID),
        Integer("obs_33024", 33024, "Obs 33024", "", Kind.GRID),
        Integer("obs_33025", 33025, "Obs 33025", "", Kind.GRID),
        Integer("obs_33026", 33026, "Obs 33026", "", Kind.GRID),
        Integer("obs_33027", 33027, "Obs 33027", "", Kind.GRID),
        Integer("obs_33028", 33028, "Obs 33028", "", Kind.GRID),
        Integer("obs_33029", 33029, "Obs 33029", "", Kind.GRID),
        Integer("obs_33030", 33030, "Obs 33030", "", Kind.GRID),
        Integer("obs_33031", 33031, "Obs 33031", "", Kind.GRID),
        Integer("obs_33032", 33032, "Obs 33032", "", Kind.GRID),
        Integer("obs_33033", 33033, "Obs 33033", "", Kind.GRID),
        Integer("obs_33034", 33034, "Obs 33034", "", Kind.GRID),
        Integer("obs_33035", 33035, "Obs 33035", "", Kind.GRID),
        Integer("obs_33036", 33036, "Obs 33036", "", Kind.GRID),
        Integer("obs_33037", 33037, "Obs 33037", "", Kind.GRID),
        Integer("obs_33038", 33038, "Obs 33038", "", Kind.GRID),
        Integer("obs_33039", 33039, "Obs 33039", "", Kind.GRID),
        Integer("obs_33040", 33040, "Obs 33040", "", Kind.GRID),
        Integer("obs_33041", 33041, "Obs 33041", "", Kind.GRID),
        Integer("obs_33042", 33042, "Obs 33042", "", Kind.GRID),
        Integer("obs_33043", 33043, "Obs 33043", "", Kind.GRID),
        Integer("obs_33044", 33044, "Obs 33044", "", Kind.GRID),
        Integer("obs_33045", 33045, "Obs 33045", "", Kind.GRID),
        Integer("obs_33046", 33046, "Obs 33046", "", Kind.GRID),
        Integer("obs_33047", 33047, "Obs 33047", "", Kind.GRID),
        Integer("obs_33048", 33048, "Obs 33048", "", Kind.GRID),
        Integer("obs_33049", 33049, "Obs 33049", "", Kind.GRID),
        Integer("obs_33051", 33051, "Obs 33051", "", Kind.GRID),
        Integer("obs_33053", 33053, "Obs 33053", "", Kind.GRID),
        Integer("obs_33055", 33055, "Obs 33055", "", Kind.GRID),
        Integer("obs_33056", 33056, "Obs 33056", "", Kind.GRID),
        Integer("obs_33057", 33057, "Obs 33057", "", Kind.GRID),
        Integer("obs_33058", 33058, "Obs 33058", "", Kind.GRID),
        Integer("obs_33059", 33059, "Obs 33059", "", Kind.GRID),
        Integer("obs_33060", 33060, "Obs 33060", "", Kind.GRID),
        Integer("obs_33061", 33061, "Obs 33061", "", Kind.GRID),
        Integer("obs_33062", 33062, "Obs 33062", "", Kind.GRID),
        Integer("obs_33063", 33063, "Obs 33063", "", Kind.GRID),
        Integer("obs_33064", 33064, "Obs 33064", "", Kind.GRID),
        Integer("obs_33065", 33065, "Obs 33065", "", Kind.GRID),
        Integer("obs_33066", 33066, "Obs 33066", "", Kind.GRID),
        Integer("obs_33067", 33067, "Obs 33067", "", Kind.GRID),
        Integer("obs_33068", 33068, "Obs 33068", "", Kind.GRID),
        Integer("obs_33069", 33069, "Obs 33069", "", Kind.GRID),
        Integer("obs_33070", 33070, "Obs 33070", "", Kind.GRID),
        Integer("obs_33075", 33075, "Obs 33075 (Unknown)", "", Kind.GRID),
        Integer("obs_33076", 33076, "Obs 33076 (Unknown)", "", Kind.GRID),
        Integer("obs_33077", 33077, "Obs 33077 (Unknown)", "", Kind.GRID),
        Integer("obs_33078", 33078, "Obs 33078 (Unknown)", "", Kind.GRID),
        Integer("obs_33080", 33080, "Obs 33080", "", Kind.GRID),
        Integer("obs_33081", 33081, "Obs 33081", "", Kind.GRID),
        Integer("obs_33082", 33082, "Obs 33082", "", Kind.GRID),
        Integer("obs_33083", 33083, "Obs 33083", "", Kind.GRID),
        Integer("obs_33084", 33084, "Obs 33084", "", Kind.GRID),
        Integer("obs_33085", 33085, "Obs 33085", "", Kind.GRID),
        Integer("obs_33086", 33086, "Obs 33086", "", Kind.GRID),
        Integer("obs_33087", 33087, "Obs 33087", "", Kind.GRID),
        Integer("obs_33088", 33088, "Obs 33088", "", Kind.GRID),
        Integer("obs_33089", 33089, "Obs 33089", "", Kind.GRID),
        Integer("obs_33090", 33090, "Obs 33090", "", Kind.GRID),
        Integer("obs_33091", 33091, "Obs 33091", "", Kind.GRID),
        Integer("obs_33092", 33092, "Obs 33092", "", Kind.GRID),
        Integer("obs_33093", 33093, "Obs 33093", "", Kind.GRID),
        Integer("obs_33094", 33094, "Obs 33094", "", Kind.GRID),
        Integer("obs_33095", 33095, "Obs 33095", "", Kind.GRID),
        Integer("obs_33096", 33096, "Obs 33096", "", Kind.GRID),
        Integer("obs_33097", 33097, "Obs 33097", "", Kind.GRID),
        Integer("obs_33098", 33098, "Obs 33098", "", Kind.GRID),
        Integer("obs_33099", 33099, "Obs 33099", "", Kind.GRID),
        Integer("obs_33288", 33288, "Obs 33288", "", Kind.GRID),
        Integer("obs_33289", 33289, "Obs 33289", "", Kind.GRID),
        Integer("obs_33290", 33290, "Obs 33290", "", Kind.GRID),
        Integer("obs_33291", 33291, "Obs 33291", "", Kind.GRID),
        Integer("obs_33292", 33292, "Obs 33292", "", Kind.GRID),
        Integer("obs_33293", 33293, "Obs 33293", "", Kind.GRID),
        Integer("obs_33294", 33294, "Obs 33294", "", Kind.GRID),
        Integer("obs_33295", 33295, "Obs 33295", "", Kind.GRID),
        Integer("obs_33500", 33500, "Obs 33500", "", Kind.GRID),
        Integer("obs_33501", 33501, "Obs 33501", "", Kind.GRID),
    )

    # Undocumented sensors - 38xxx block (Grid phase settings?)
    __observation_sensors_38xxx: tuple[Sensor, ...] = (
        Integer("obs_38001", 38001, "Obs 38001 (Unknown)", "", Kind.GRID),
        Integer("obs_38002", 38002, "Obs 38002 (Unknown)", "", Kind.GRID),
        Integer("obs_38009", 38009, "Obs 38009 (Voltage?)", "", Kind.GRID),
        Integer("obs_38029", 38029, "Obs 38029 (Voltage?)", "", Kind.GRID),
        Integer("obs_38049", 38049, "Obs 38049 (Voltage?)", "", Kind.GRID),
        Integer("obs_38051", 38051, "Obs 38051 (Unknown)", "", Kind.GRID),
        Integer("obs_38451", 38451, "Obs 38451 (Unknown)", "", Kind.GRID),
        Integer("obs_38452", 38452, "Obs 38452 (Unknown)", "", Kind.GRID),
        Integer("obs_38453", 38453, "Obs 38453 (Unknown)", "", Kind.GRID),
        Integer("obs_38458", 38458, "Obs 38458 (Unknown)", "", Kind.GRID),
        # New sensors from full scan
        Integer("obs_38000", 38000, "Obs 38000", "", Kind.GRID),
        Integer("obs_38003", 38003, "Obs 38003", "", Kind.GRID),
        Integer("obs_38004", 38004, "Obs 38004", "", Kind.GRID),
        Integer("obs_38005", 38005, "Obs 38005", "", Kind.GRID),
        Integer("obs_38006", 38006, "Obs 38006", "", Kind.GRID),
        Integer("obs_38007", 38007, "Obs 38007", "", Kind.GRID),
        Integer("obs_38008", 38008, "Obs 38008", "", Kind.GRID),
        Integer("obs_38010", 38010, "Obs 38010", "", Kind.GRID),
        Integer("obs_38011", 38011, "Obs 38011", "", Kind.GRID),
        Integer("obs_38012", 38012, "Obs 38012", "", Kind.GRID),
        Integer("obs_38013", 38013, "Obs 38013", "", Kind.GRID),
        Integer("obs_38014", 38014, "Obs 38014", "", Kind.GRID),
        Integer("obs_38015", 38015, "Obs 38015", "", Kind.GRID),
        Integer("obs_38016", 38016, "Obs 38016", "", Kind.GRID),
        Integer("obs_38017", 38017, "Obs 38017", "", Kind.GRID),
        Integer("obs_38018", 38018, "Obs 38018", "", Kind.GRID),
        Integer("obs_38019", 38019, "Obs 38019", "", Kind.GRID),
        Integer("obs_38020", 38020, "Obs 38020", "", Kind.GRID),
        Integer("obs_38021", 38021, "Obs 38021", "", Kind.GRID),
        Integer("obs_38022", 38022, "Obs 38022", "", Kind.GRID),
        Integer("obs_38023", 38023, "Obs 38023", "", Kind.GRID),
        Integer("obs_38024", 38024, "Obs 38024", "", Kind.GRID),
        Integer("obs_38025", 38025, "Obs 38025", "", Kind.GRID),
        Integer("obs_38026", 38026, "Obs 38026", "", Kind.GRID),
        Integer("obs_38027", 38027, "Obs 38027", "", Kind.GRID),
        Integer("obs_38028", 38028, "Obs 38028", "", Kind.GRID),
        Integer("obs_38030", 38030, "Obs 38030", "", Kind.GRID),
        Integer("obs_38031", 38031, "Obs 38031", "", Kind.GRID),
        Integer("obs_38032", 38032, "Obs 38032", "", Kind.GRID),
        Integer("obs_38033", 38033, "Obs 38033", "", Kind.GRID),
        Integer("obs_38034", 38034, "Obs 38034", "", Kind.GRID),
        Integer("obs_38035", 38035, "Obs 38035", "", Kind.GRID),
        Integer("obs_38036", 38036, "Obs 38036", "", Kind.GRID),
        Integer("obs_38037", 38037, "Obs 38037", "", Kind.GRID),
        Integer("obs_38038", 38038, "Obs 38038", "", Kind.GRID),
        Integer("obs_38039", 38039, "Obs 38039", "", Kind.GRID),
        Integer("obs_38040", 38040, "Obs 38040", "", Kind.GRID),
        Integer("obs_38041", 38041, "Obs 38041", "", Kind.GRID),
        Integer("obs_38042", 38042, "Obs 38042", "", Kind.GRID),
        Integer("obs_38043", 38043, "Obs 38043", "", Kind.GRID),
        Integer("obs_38044", 38044, "Obs 38044", "", Kind.GRID),
        Integer("obs_38045", 38045, "Obs 38045", "", Kind.GRID),
        Integer("obs_38046", 38046, "Obs 38046", "", Kind.GRID),
        Integer("obs_38047", 38047, "Obs 38047", "", Kind.GRID),
        Integer("obs_38048", 38048, "Obs 38048", "", Kind.GRID),
        Integer("obs_38050", 38050, "Obs 38050", "", Kind.GRID),
        Integer("obs_38052", 38052, "Obs 38052", "", Kind.GRID),
        Integer("obs_38053", 38053, "Obs 38053", "", Kind.GRID),
        Integer("obs_38054", 38054, "Obs 38054", "", Kind.GRID),
        Integer("obs_38055", 38055, "Obs 38055", "", Kind.GRID),
        Integer("obs_38056", 38056, "Obs 38056", "", Kind.GRID),
        Integer("obs_38057", 38057, "Obs 38057", "", Kind.GRID),
        Integer("obs_38058", 38058, "Obs 38058", "", Kind.GRID),
        Integer("obs_38059", 38059, "Obs 38059", "", Kind.GRID),
        Integer("obs_38060", 38060, "Obs 38060", "", Kind.GRID),
        Integer("obs_38061", 38061, "Obs 38061", "", Kind.GRID),
        Integer("obs_38062", 38062, "Obs 38062", "", Kind.GRID),
        Integer("obs_38063", 38063, "Obs 38063", "", Kind.GRID),
        Integer("obs_38064", 38064, "Obs 38064", "", Kind.GRID),
        Integer("obs_38065", 38065, "Obs 38065", "", Kind.GRID),
        Integer("obs_38066", 38066, "Obs 38066", "", Kind.GRID),
        Integer("obs_38067", 38067, "Obs 38067", "", Kind.GRID),
        Integer("obs_38068", 38068, "Obs 38068", "", Kind.GRID),
        Integer("obs_38069", 38069, "Obs 38069", "", Kind.GRID),
        Integer("obs_38070", 38070, "Obs 38070", "", Kind.GRID),
        Integer("obs_38071", 38071, "Obs 38071", "", Kind.GRID),
        Integer("obs_38072", 38072, "Obs 38072", "", Kind.GRID),
        Integer("obs_38073", 38073, "Obs 38073", "", Kind.GRID),
        Integer("obs_38074", 38074, "Obs 38074", "", Kind.GRID),
        Integer("obs_38075", 38075, "Obs 38075", "", Kind.GRID),
        Integer("obs_38076", 38076, "Obs 38076", "", Kind.GRID),
        Integer("obs_38077", 38077, "Obs 38077", "", Kind.GRID),
        Integer("obs_38078", 38078, "Obs 38078", "", Kind.GRID),
        Integer("obs_38079", 38079, "Obs 38079", "", Kind.GRID),
        Integer("obs_38080", 38080, "Obs 38080", "", Kind.GRID),
        Integer("obs_38081", 38081, "Obs 38081", "", Kind.GRID),
        Integer("obs_38082", 38082, "Obs 38082", "", Kind.GRID),
        Integer("obs_38083", 38083, "Obs 38083", "", Kind.GRID),
        Integer("obs_38084", 38084, "Obs 38084", "", Kind.GRID),
        Integer("obs_38085", 38085, "Obs 38085", "", Kind.GRID),
        Integer("obs_38086", 38086, "Obs 38086", "", Kind.GRID),
        Integer("obs_38087", 38087, "Obs 38087", "", Kind.GRID),
        Integer("obs_38088", 38088, "Obs 38088", "", Kind.GRID),
        Integer("obs_38089", 38089, "Obs 38089", "", Kind.GRID),
        Integer("obs_38090", 38090, "Obs 38090", "", Kind.GRID),
        Integer("obs_38091", 38091, "Obs 38091", "", Kind.GRID),
        Integer("obs_38092", 38092, "Obs 38092", "", Kind.GRID),
        Integer("obs_38093", 38093, "Obs 38093", "", Kind.GRID),
        Integer("obs_38094", 38094, "Obs 38094", "", Kind.GRID),
        Integer("obs_38095", 38095, "Obs 38095", "", Kind.GRID),
        Integer("obs_38096", 38096, "Obs 38096", "", Kind.GRID),
        Integer("obs_38097", 38097, "Obs 38097", "", Kind.GRID),
        Integer("obs_38098", 38098, "Obs 38098", "", Kind.GRID),
        Integer("obs_38099", 38099, "Obs 38099", "", Kind.GRID),
        Integer("obs_38450", 38450, "Obs 38450", "", Kind.GRID),
        Integer("obs_38454", 38454, "Obs 38454", "", Kind.GRID),
        Integer("obs_38455", 38455, "Obs 38455", "", Kind.GRID),
        Integer("obs_38456", 38456, "Obs 38456", "", Kind.GRID),
        Integer("obs_38457", 38457, "Obs 38457", "", Kind.GRID),
        Integer("obs_38459", 38459, "Obs 38459", "", Kind.GRID),
        Integer("obs_38460", 38460, "Obs 38460", "", Kind.GRID),
        Integer("obs_38461", 38461, "Obs 38461", "", Kind.GRID),
        Integer("obs_38462", 38462, "Obs 38462", "", Kind.GRID),
        Integer("obs_38463", 38463, "Obs 38463", "", Kind.GRID),
    )

    # Undocumented sensors - 55xxx block (Energy counters?)
    __observation_sensors_55xxx: tuple[Sensor, ...] = (
        Long("obs_55252", 55252, "Obs 55252 (Energy?)", "", Kind.AC),
        Long("obs_55256", 55256, "Obs 55256 (Energy?)", "", Kind.AC),
        Long("obs_55260", 55260, "Obs 55260 (Energy?)", "", Kind.AC),
        Long("obs_55264", 55264, "Obs 55264 (Energy?)", "", Kind.AC),
        Long("obs_55268", 55268, "Obs 55268 (Energy?)", "", Kind.AC),
        Long("obs_55272", 55272, "Obs 55272 (Energy?)", "", Kind.AC),
        Long("obs_55276", 55276, "Obs 55276 (Energy?)", "", Kind.AC),
        Long("obs_55280", 55280, "Obs 55280 (Energy?)", "", Kind.AC),
        # New sensors from full scan
        Integer("obs_55000", 55000, "Obs 55000", "", Kind.AC),
        Integer("obs_55250", 55250, "Obs 55250", "", Kind.AC),
        Integer("obs_55251", 55251, "Obs 55251", "", Kind.AC),
        Integer("obs_55253", 55253, "Obs 55253", "", Kind.AC),
        Integer("obs_55254", 55254, "Obs 55254", "", Kind.AC),
        Integer("obs_55255", 55255, "Obs 55255", "", Kind.AC),
        Integer("obs_55257", 55257, "Obs 55257", "", Kind.AC),
        Integer("obs_55258", 55258, "Obs 55258", "", Kind.AC),
        Integer("obs_55259", 55259, "Obs 55259", "", Kind.AC),
        Integer("obs_55261", 55261, "Obs 55261", "", Kind.AC),
        Integer("obs_55262", 55262, "Obs 55262", "", Kind.AC),
        Integer("obs_55263", 55263, "Obs 55263", "", Kind.AC),
        Integer("obs_55265", 55265, "Obs 55265", "", Kind.AC),
        Integer("obs_55266", 55266, "Obs 55266", "", Kind.AC),
        Integer("obs_55267", 55267, "Obs 55267", "", Kind.AC),
        Integer("obs_55269", 55269, "Obs 55269", "", Kind.AC),
        Integer("obs_55270", 55270, "Obs 55270", "", Kind.AC),
        Integer("obs_55271", 55271, "Obs 55271", "", Kind.AC),
        Integer("obs_55273", 55273, "Obs 55273", "", Kind.AC),
        Integer("obs_55274", 55274, "Obs 55274", "", Kind.AC),
        Integer("obs_55275", 55275, "Obs 55275", "", Kind.AC),
        Integer("obs_55277", 55277, "Obs 55277", "", Kind.AC),
        Integer("obs_55278", 55278, "Obs 55278", "", Kind.AC),
        Integer("obs_55279", 55279, "Obs 55279", "", Kind.AC),
        Integer("obs_55281", 55281, "Obs 55281", "", Kind.AC),
        Integer("obs_55282", 55282, "Obs 55282", "", Kind.AC),
        Integer("obs_55283", 55283, "Obs 55283", "", Kind.AC),
        Integer("obs_55284", 55284, "Obs 55284", "", Kind.AC),
        Integer("obs_55285", 55285, "Obs 55285", "", Kind.AC),
        Integer("obs_55286", 55286, "Obs 55286", "", Kind.AC),
        Integer("obs_55287", 55287, "Obs 55287", "", Kind.AC),
        Integer("obs_55288", 55288, "Obs 55288", "", Kind.AC),
        Integer("obs_55289", 55289, "Obs 55289", "", Kind.AC),
        Integer("obs_55290", 55290, "Obs 55290", "", Kind.AC),
        Integer("obs_55291", 55291, "Obs 55291", "", Kind.AC),
        Integer("obs_55292", 55292, "Obs 55292", "", Kind.AC),
        Integer("obs_55293", 55293, "Obs 55293", "", Kind.AC),
        Integer("obs_55294", 55294, "Obs 55294", "", Kind.AC),
        Integer("obs_55295", 55295, "Obs 55295", "", Kind.AC),
        Integer("obs_55296", 55296, "Obs 55296", "", Kind.AC),
        Integer("obs_55297", 55297, "Obs 55297", "", Kind.AC),
        Integer("obs_55298", 55298, "Obs 55298", "", Kind.AC),
        Integer("obs_55299", 55299, "Obs 55299", "", Kind.AC),
        Integer("obs_55300", 55300, "Obs 55300", "", Kind.AC),
        Integer("obs_55301", 55301, "Obs 55301", "", Kind.AC),
        Integer("obs_55302", 55302, "Obs 55302", "", Kind.AC),
        Integer("obs_55303", 55303, "Obs 55303", "", Kind.AC),
        Integer("obs_55304", 55304, "Obs 55304", "", Kind.AC),
        Integer("obs_55305", 55305, "Obs 55305", "", Kind.AC),
        Integer("obs_55306", 55306, "Obs 55306", "", Kind.AC),
        Integer("obs_55307", 55307, "Obs 55307", "", Kind.AC),
        Integer("obs_55308", 55308, "Obs 55308", "", Kind.AC),
        Integer("obs_55309", 55309, "Obs 55309", "", Kind.AC),
        Integer("obs_55310", 55310, "Obs 55310", "", Kind.AC),
        Integer("obs_55311", 55311, "Obs 55311", "", Kind.AC),
        Integer("obs_55312", 55312, "Obs 55312", "", Kind.AC),
        Integer("obs_55313", 55313, "Obs 55313", "", Kind.AC),
        Integer("obs_55314", 55314, "Obs 55314", "", Kind.AC),
        Integer("obs_55315", 55315, "Obs 55315", "", Kind.AC),
        Integer("obs_55316", 55316, "Obs 55316", "", Kind.AC),
        Integer("obs_55400", 55400, "Obs 55400", "", Kind.AC),
        Integer("obs_55401", 55401, "Obs 55401", "", Kind.AC),
        Integer("obs_55402", 55402, "Obs 55402", "", Kind.AC),
    )

    # Modbus registers of inverter settings, offsets are modbus register addresses
    __all_settings: tuple[Sensor, ...] = (
        Integer("comm_address", 45127, "Communication Address", ""),
        Long("modbus_baud_rate", 45132, "Modbus Baud rate", ""),
        Timestamp("time", 45200, "Inverter time"),

        Integer("sensitivity_check", 45246, "Sensitivity Check Mode", "", Kind.AC),
        Integer("cold_start", 45248, "Cold Start", "", Kind.AC),
        Integer("shadow_scan", 45251, "Shadow Scan", "", Kind.PV),
        Integer("backup_supply", 45252, "Backup Supply", "", Kind.UPS),
        Integer("unbalanced_output", 45264, "Unbalanced Output", "", Kind.AC),
        Integer("pen_relay", 45288, "PE-N Relay", "", Kind.AC),

        Integer("battery_capacity", 45350, "Battery Capacity", "Ah", Kind.BAT),
        Integer("battery_modules", 45351, "Battery Modules", "", Kind.BAT),
        Voltage("battery_charge_voltage", 45352, "Battery Charge Voltage", Kind.BAT),
        Current("battery_charge_current", 45353, "Battery Charge Current", Kind.BAT),
        Voltage("battery_discharge_voltage", 45354, "Battery Discharge Voltage", Kind.BAT),
        Current("battery_discharge_current", 45355, "Battery Discharge Current", Kind.BAT),
        Integer("battery_discharge_depth", 45356, "Battery Discharge Depth", "%", Kind.BAT),
        Voltage("battery_discharge_voltage_offline", 45357, "Battery Discharge Voltage (off-line)", Kind.BAT),
        Integer("battery_discharge_depth_offline", 45358, "Battery Discharge Depth (off-line)", "%", Kind.BAT),

        Decimal("power_factor", 45482, 100, "Power Factor"),
        IntegerS("fixed_reactive_power", 45483, "Fixed Reactive Power", "‰", Kind.GRID),
        Integer("fixed_power_factor_enable", 45539, "Fixed Power Factor Enable", "", Kind.GRID),
        Integer("fixed_q_power_flag", 45542, "Fixed Q Power Flag", "", Kind.GRID),

        Integer("work_mode", 47000, "Work Mode", "", Kind.AC),
        Integer("dred", 47010, "DRED/Remote Shutdown", "", Kind.AC),

        Integer("meter_target_power_offset", 47120, "Meter Target Power Offset", "W", Kind.AC),

        Integer("battery_soc_protection", 47500, "Battery SoC Protection", "", Kind.BAT),

        Integer("grid_export", 47509, "Grid Export Limit Enabled", "", Kind.GRID),
        Integer("grid_export_limit", 47510, "Grid Export Limit", "W", Kind.GRID),
        Integer("ems_power_mode", 47511, "EMS Power Mode", "", Kind.BAT),
        Integer("ems_power", 47512, "EMS Power", "W", Kind.BAT),

        Integer("battery_protocol_code", 47514, "Battery Protocol Code", "", Kind.BAT),

        EcoModeV1("eco_mode_1", 47515, "Eco Mode Group 1"),
        ByteH("eco_mode_1_switch", 47518, "Eco Mode Group 1 Switch"),
        EcoModeV1("eco_mode_2", 47519, "Eco Mode Group 2"),
        ByteH("eco_mode_2_switch", 47522, "Eco Mode Group 2 Switch"),
        EcoModeV1("eco_mode_3", 47523, "Eco Mode Group 3"),
        ByteH("eco_mode_3_switch", 47526, "Eco Mode Group 3 Switch"),
        EcoModeV1("eco_mode_4", 47527, "Eco Mode Group 4"),
        ByteH("eco_mode_4_switch", 47530, "Eco Mode Group 4 Switch"),

        Integer("force_charge_soc_start", 47531, "Force Charge Start SoC", "%", Kind.BAT),
        Integer("force_charge_soc_stop", 47532, "Force Charge Stop SoC", "%", Kind.BAT),
        Integer("clear_eco_time", 47533, "Clear ECO Time Settings", "", Kind.BAT),

        Integer("wifi_reset", 47539, "WiFi Reset", "", Kind.AC),
        Integer("wifi_reload", 47541, "WiFi Reload", "", Kind.AC),

        # Direct BMS communication for EMS Control
        Integer("bms_version", 47900, "BMS Version"),
        Integer("bms_bat_modules", 47901, "BMS Battery Modules"),
        # Real time read from BMS
        Voltage("bms_bat_charge_v_max", 47902, "BMS Battery Charge Voltage (max)", Kind.BMS),
        Current("bms_bat_charge_i_max", 47903, "BMS Battery Charge Current (max)", Kind.BMS),
        Voltage("bms_bat_discharge_v_min", 47904, "BMS min. Battery Discharge Voltage (min)", Kind.BMS),
        Current("bms_bat_discharge_i_max", 47905, "BMS max. Battery Discharge Current (max)", Kind.BMS),
        Voltage("bms_bat_voltage", 47906, "BMS Battery Voltage", Kind.BMS),
        Current("bms_bat_current", 47907, "BMS Battery Current", Kind.BMS),
        #
        Integer("bms_bat_soc", 47908, "BMS Battery State of Charge", "%", Kind.BMS),
        Integer("bms_bat_soh", 47909, "BMS Battery State of Health", "%", Kind.BMS),
        Temp("bms_bat_temperature", 47910, "BMS Battery Temperature", Kind.BMS),
        Long("bms_bat_warning-code", 47911, "BMS Battery Warning Code"),
        # Reserved
        Long("bms_bat_alarm-code", 47913, "BMS Battery Alarm Code"),
        Integer("bms_status", 47915, "BMS Status"),
        Integer("bms_comm_loss_disable", 47916, "BMS Communication Loss Disable"),
        # RW settings of BMS voltage rate
        Integer("bms_battery_string_rate_v", 47917, "BMS Battery String Rate Voltage"),

        # Direct BMS communication for EMS Control
        Integer("bms2_version", 47918, "BMS2 Version"),
        Integer("bms2_bat_modules", 47919, "BMS2 Battery Modules"),
        # Real time read from BMS
        Voltage("bms2_bat_charge_v_max", 47920, "BMS2 Battery Charge Voltage (max)", Kind.BMS),
        Current("bms2_bat_charge_i_max", 47921, "BMS2 Battery Charge Current (max)", Kind.BMS),
        Voltage("bms2_bat_discharge_v_min", 47922, "BMS2 min. Battery Discharge Voltage (min)", Kind.BMS),
        Current("bms2_bat_discharge_i_max", 47923, "BMS2 max. Battery Discharge Current (max)", Kind.BMS),
        Voltage("bms2_bat_voltage", 47924, "BMS2 Battery Voltage", Kind.BMS),
        Current("bms2_bat_current", 47925, "BMS2 Battery Current", Kind.BMS),
        #
        Integer("bms2_bat_soc", 47926, "BMS2 Battery State of Charge", "%", Kind.BMS),
        Integer("bms2_bat_soh", 47927, "BMS2 Battery State of Health", "%", Kind.BMS),
        Temp("bms2_bat_temperature", 47928, "BMS2 Battery Temperature", Kind.BMS),
        Long("bms2_bat_warning-code", 47929, "BMS2 Battery Warning Code"),
        # Reserved
        Long("bms2_bat_alarm-code", 47931, "BMS2 Battery Alarm Code"),
        Integer("bms2_status", 47933, "BMS2 Status"),
        Integer("bms2_comm_loss_disable", 47934, "BMS2 Communication Loss Disable"),
        # RW settings of BMS voltage rate
        Integer("bms2_battery_string_rate_v", 47935, "BMS2 Battery String Rate Voltage"),

    )

    # Settings added in ARM firmware 19
    # Note: TOU sensors are ALSO in __all_sensors for visibility in HA (intentional duplication)
    __settings_arm_fw_19: tuple[Sensor, ...] = (
        Integer("fast_charging", 47545, "Fast Charging Enabled", "", Kind.BAT),
        Integer("fast_charging_soc", 47546, "Fast Charging SoC", "%", Kind.BAT),
        # TOU Slots 1-4 (also in __all_sensors for sensor visibility)
        TimeOfDay("tou_slot1_start_time", 47547, "TOU Slot 1 Start Time", Kind.BAT),
        TimeOfDay("tou_slot1_end_time", 47548, "TOU Slot 1 End Time", Kind.BAT),
        WorkWeekV2("tou_slot1_work_week", 47549, "TOU Slot 1 Work Week", Kind.BAT),
        Integer("tou_slot1_param1", 47550, "TOU Slot 1 Parameter 1", "", Kind.BAT),
        Integer("tou_slot1_param2", 47551, "TOU Slot 1 Parameter 2", "", Kind.BAT),
        MonthMask("tou_slot1_months", 47552, "TOU Slot 1 Months", Kind.BAT),
        TimeOfDay("tou_slot2_start_time", 47553, "TOU Slot 2 Start Time", Kind.BAT),
        TimeOfDay("tou_slot2_end_time", 47554, "TOU Slot 2 End Time", Kind.BAT),
        WorkWeekV2("tou_slot2_work_week", 47555, "TOU Slot 2 Work Week", Kind.BAT),
        Integer("tou_slot2_param1", 47556, "TOU Slot 2 Parameter 1", "", Kind.BAT),
        Integer("tou_slot2_param2", 47557, "TOU Slot 2 Parameter 2", "", Kind.BAT),
        MonthMask("tou_slot2_months", 47558, "TOU Slot 2 Months", Kind.BAT),
        TimeOfDay("tou_slot3_start_time", 47559, "TOU Slot 3 Start Time", Kind.BAT),
        TimeOfDay("tou_slot3_end_time", 47560, "TOU Slot 3 End Time", Kind.BAT),
        WorkWeekV2("tou_slot3_work_week", 47561, "TOU Slot 3 Work Week", Kind.BAT),
        Integer("tou_slot3_param1", 47562, "TOU Slot 3 Parameter 1", "", Kind.BAT),
        Integer("tou_slot3_param2", 47563, "TOU Slot 3 Parameter 2", "", Kind.BAT),
        MonthMask("tou_slot3_months", 47564, "TOU Slot 3 Months", Kind.BAT),
        TimeOfDay("tou_slot4_start_time", 47565, "TOU Slot 4 Start Time", Kind.BAT),
        TimeOfDay("tou_slot4_end_time", 47566, "TOU Slot 4 End Time", Kind.BAT),
        WorkWeekV2("tou_slot4_work_week", 47567, "TOU Slot 4 Work Week", Kind.BAT),
        Integer("tou_slot4_param1", 47568, "TOU Slot 4 Parameter 1", "", Kind.BAT),
        Integer("tou_slot4_param2", 47569, "TOU Slot 4 Parameter 2", "", Kind.BAT),
        MonthMask("tou_slot4_months", 47570, "TOU Slot 4 Months", Kind.BAT),
        Integer("load_control_mode", 47595, "Load Control Mode", "", Kind.AC),
        Integer("load_control_switch", 47596, "Load Control Switch", "", Kind.AC),
        Integer("load_control_soc", 47597, "Load Control SoC", "", Kind.AC),
        Integer("hardware_feed_power", 47599, "Hardware Feed Power"),
        Integer("pcs_powersave_mode", 47600, "PCS Powersave Mode", "", Kind.BAT),
        Integer("old_meter_protocol", 47601, "Old Meter Protocol", "", Kind.GRID),

        Integer("fast_charging_power", 47603, "Fast Charging Power", "%", Kind.BAT),
        Integer("load_regulation_generator_flag", 47604, "Load Regulation or Generator Flag", "", Kind.AC),

        Integer("pv_sell_first", 47613, "PV Sell First", "", Kind.PV),
        Integer("bat_feedpower_offset", 47614, "Battery FeedPower Offset", "W", Kind.BAT),
        Integer("battery_current_coff", 47615, "Battery Current Coefficient", "%", Kind.BAT),
        Integer("parallel_strong_charge_power", 47616, "Master Strong Charge Power", "‰", Kind.BAT),

        Integer("battery2_protocol_code", 47618, "Battery2 Protocol Code", "", Kind.BAT),

        # Feed Power Schedule - 24 time slots for export power limitation
        Long("feed_power_start_time_1", 47619, "Feed Power Start Time 1", "s", Kind.GRID),
        LongS("feed_power_limit_1", 47621, "Feed Power Limit 1", "W", Kind.GRID),
        Integer("feed_power_period_1", 47623, "Feed Power Period 1", "s", Kind.GRID),
        Long("feed_power_start_time_2", 47624, "Feed Power Start Time 2", "s", Kind.GRID),
        LongS("feed_power_limit_2", 47626, "Feed Power Limit 2", "W", Kind.GRID),
        Integer("feed_power_period_2", 47628, "Feed Power Period 2", "s", Kind.GRID),
        Long("feed_power_start_time_3", 47629, "Feed Power Start Time 3", "s", Kind.GRID),
        LongS("feed_power_limit_3", 47631, "Feed Power Limit 3", "W", Kind.GRID),
        Integer("feed_power_period_3", 47633, "Feed Power Period 3", "s", Kind.GRID),
        Long("feed_power_start_time_4", 47634, "Feed Power Start Time 4", "s", Kind.GRID),
        LongS("feed_power_limit_4", 47636, "Feed Power Limit 4", "W", Kind.GRID),
        Integer("feed_power_period_4", 47638, "Feed Power Period 4", "s", Kind.GRID),
        Long("feed_power_start_time_5", 47639, "Feed Power Start Time 5", "s", Kind.GRID),
        LongS("feed_power_limit_5", 47641, "Feed Power Limit 5", "W", Kind.GRID),
        Integer("feed_power_period_5", 47643, "Feed Power Period 5", "s", Kind.GRID),
        Long("feed_power_start_time_6", 47644, "Feed Power Start Time 6", "s", Kind.GRID),
        LongS("feed_power_limit_6", 47646, "Feed Power Limit 6", "W", Kind.GRID),
        Integer("feed_power_period_6", 47648, "Feed Power Period 6", "s", Kind.GRID),
        Long("feed_power_start_time_7", 47649, "Feed Power Start Time 7", "s", Kind.GRID),
        LongS("feed_power_limit_7", 47651, "Feed Power Limit 7", "W", Kind.GRID),
        Integer("feed_power_period_7", 47653, "Feed Power Period 7", "s", Kind.GRID),
        Long("feed_power_start_time_8", 47654, "Feed Power Start Time 8", "s", Kind.GRID),
        LongS("feed_power_limit_8", 47656, "Feed Power Limit 8", "W", Kind.GRID),
        Integer("feed_power_period_8", 47658, "Feed Power Period 8", "s", Kind.GRID),
        Long("feed_power_start_time_9", 47659, "Feed Power Start Time 9", "s", Kind.GRID),
        LongS("feed_power_limit_9", 47661, "Feed Power Limit 9", "W", Kind.GRID),
        Integer("feed_power_period_9", 47663, "Feed Power Period 9", "s", Kind.GRID),
        Long("feed_power_start_time_10", 47664, "Feed Power Start Time 10", "s", Kind.GRID),
        LongS("feed_power_limit_10", 47666, "Feed Power Limit 10", "W", Kind.GRID),
        Integer("feed_power_period_10", 47668, "Feed Power Period 10", "s", Kind.GRID),
        Long("feed_power_start_time_11", 47669, "Feed Power Start Time 11", "s", Kind.GRID),
        LongS("feed_power_limit_11", 47671, "Feed Power Limit 11", "W", Kind.GRID),
        Integer("feed_power_period_11", 47673, "Feed Power Period 11", "s", Kind.GRID),
        Long("feed_power_start_time_12", 47674, "Feed Power Start Time 12", "s", Kind.GRID),
        LongS("feed_power_limit_12", 47676, "Feed Power Limit 12", "W", Kind.GRID),
        Integer("feed_power_period_12", 47678, "Feed Power Period 12", "s", Kind.GRID),
        Long("feed_power_start_time_13", 47679, "Feed Power Start Time 13", "s", Kind.GRID),
        LongS("feed_power_limit_13", 47681, "Feed Power Limit 13", "W", Kind.GRID),
        Integer("feed_power_period_13", 47683, "Feed Power Period 13", "s", Kind.GRID),
        Long("feed_power_start_time_14", 47684, "Feed Power Start Time 14", "s", Kind.GRID),
        LongS("feed_power_limit_14", 47686, "Feed Power Limit 14", "W", Kind.GRID),
        Integer("feed_power_period_14", 47688, "Feed Power Period 14", "s", Kind.GRID),
        Long("feed_power_start_time_15", 47689, "Feed Power Start Time 15", "s", Kind.GRID),
        LongS("feed_power_limit_15", 47691, "Feed Power Limit 15", "W", Kind.GRID),
        Integer("feed_power_period_15", 47693, "Feed Power Period 15", "s", Kind.GRID),
        Long("feed_power_start_time_16", 47694, "Feed Power Start Time 16", "s", Kind.GRID),
        LongS("feed_power_limit_16", 47696, "Feed Power Limit 16", "W", Kind.GRID),
        Integer("feed_power_period_16", 47698, "Feed Power Period 16", "s", Kind.GRID),
        Long("feed_power_start_time_17", 47699, "Feed Power Start Time 17", "s", Kind.GRID),
        LongS("feed_power_limit_17", 47701, "Feed Power Limit 17", "W", Kind.GRID),
        Integer("feed_power_period_17", 47703, "Feed Power Period 17", "s", Kind.GRID),
        Long("feed_power_start_time_18", 47704, "Feed Power Start Time 18", "s", Kind.GRID),
        LongS("feed_power_limit_18", 47706, "Feed Power Limit 18", "W", Kind.GRID),
        Integer("feed_power_period_18", 47708, "Feed Power Period 18", "s", Kind.GRID),
        Long("feed_power_start_time_19", 47709, "Feed Power Start Time 19", "s", Kind.GRID),
        LongS("feed_power_limit_19", 47711, "Feed Power Limit 19", "W", Kind.GRID),
        Integer("feed_power_period_19", 47713, "Feed Power Period 19", "s", Kind.GRID),
        Long("feed_power_start_time_20", 47714, "Feed Power Start Time 20", "s", Kind.GRID),
        LongS("feed_power_limit_20", 47716, "Feed Power Limit 20", "W", Kind.GRID),
        Integer("feed_power_period_20", 47718, "Feed Power Period 20", "s", Kind.GRID),
        Long("feed_power_start_time_21", 47719, "Feed Power Start Time 21", "s", Kind.GRID),
        LongS("feed_power_limit_21", 47721, "Feed Power Limit 21", "W", Kind.GRID),
        Integer("feed_power_period_21", 47723, "Feed Power Period 21", "s", Kind.GRID),
        Long("feed_power_start_time_22", 47724, "Feed Power Start Time 22", "s", Kind.GRID),
        LongS("feed_power_limit_22", 47726, "Feed Power Limit 22", "W", Kind.GRID),
        Integer("feed_power_period_22", 47728, "Feed Power Period 22", "s", Kind.GRID),
        Long("feed_power_start_time_23", 47729, "Feed Power Start Time 23", "s", Kind.GRID),
        LongS("feed_power_limit_23", 47731, "Feed Power Limit 23", "W", Kind.GRID),
        Integer("feed_power_period_23", 47733, "Feed Power Period 23", "s", Kind.GRID),
        Long("feed_power_start_time_24", 47734, "Feed Power Start Time 24", "s", Kind.GRID),
        LongS("feed_power_limit_24", 47736, "Feed Power Limit 24", "W", Kind.GRID),
        Integer("feed_power_period_24", 47738, "Feed Power Period 24", "s", Kind.GRID),

        # SAPN (South Australian Power Networks) settings
        Integer("sapn_up_rate", 47739, "SAPN Up Rate", "%Pn/min", Kind.GRID),
        Integer("sapn_down_rate", 47740, "SAPN Down Rate", "%Pn/min", Kind.GRID),
        LongS("sapn_feed_power_preset", 47741, "SAPN Feed Power Preset", "W", Kind.GRID),
        Integer("single_battery_paral_enable", 47743, "Single Battery Parallel Enable", "", Kind.BAT),
        Integer("battery_busbar_mode", 47744, "Battery Busbar Mode", "", Kind.BAT),
    )

    # Settings added in ARM firmware 22
    # Note: TOU sensors are ALSO in __all_sensors for visibility in HA (intentional duplication)
    __settings_arm_fw_22: tuple[Sensor, ...] = (
        Long("peak_shaving_power_limit", 47542, "Peak Shaving Power Limit"),
        Integer("peak_shaving_soc", 47544, "Peak Shaving SoC"),
        # Peak Shaving enable/disable switch (uses same register as TOU slot 8 work week)
        # 64512 (0xFC00) = Peak shaving enabled, 768 (0x0300) = disabled
        SwitchValue("peak_shaving_enabled", 47591, "Peak Shaving Enabled",
                    on_value=64512, off_value=768, kind=Kind.BAT),
        # TOU Slots 5-8 (also in __all_sensors for sensor visibility)
        TimeOfDay("tou_slot5_start_time", 47571, "TOU Slot 5 Start Time", Kind.BAT),
        TimeOfDay("tou_slot5_end_time", 47572, "TOU Slot 5 End Time", Kind.BAT),
        WorkWeekV2("tou_slot5_work_week", 47573, "TOU Slot 5 Work Week", Kind.BAT),
        Integer("tou_slot5_param1", 47574, "TOU Slot 5 Parameter 1", "", Kind.BAT),
        Integer("tou_slot5_param2", 47575, "TOU Slot 5 Parameter 2", "", Kind.BAT),
        MonthMask("tou_slot5_months", 47576, "TOU Slot 5 Months", Kind.BAT),
        TimeOfDay("tou_slot6_start_time", 47577, "TOU Slot 6 Start Time", Kind.BAT),
        TimeOfDay("tou_slot6_end_time", 47578, "TOU Slot 6 End Time", Kind.BAT),
        WorkWeekV2("tou_slot6_work_week", 47579, "TOU Slot 6 Work Week", Kind.BAT),
        Integer("tou_slot6_param1", 47580, "TOU Slot 6 Parameter 1", "", Kind.BAT),
        Integer("tou_slot6_param2", 47581, "TOU Slot 6 Parameter 2", "", Kind.BAT),
        MonthMask("tou_slot6_months", 47582, "TOU Slot 6 Months", Kind.BAT),
        TimeOfDay("tou_slot7_start_time", 47583, "TOU Slot 7 Start Time", Kind.BAT),
        TimeOfDay("tou_slot7_end_time", 47584, "TOU Slot 7 End Time", Kind.BAT),
        WorkWeekV2("tou_slot7_work_week", 47585, "TOU Slot 7 Work Week", Kind.BAT),
        Integer("tou_slot7_param1", 47586, "TOU Slot 7 Parameter 1", "", Kind.BAT),
        Integer("tou_slot7_param2", 47587, "TOU Slot 7 Parameter 2", "", Kind.BAT),
        MonthMask("tou_slot7_months", 47588, "TOU Slot 7 Months", Kind.BAT),
        TimeOfDay("tou_slot8_start_time", 47589, "TOU Slot 8 Start Time", Kind.BAT),
        TimeOfDay("tou_slot8_end_time", 47590, "TOU Slot 8 End Time", Kind.BAT),
        WorkWeekV2("tou_slot8_work_week", 47591, "TOU Slot 8 Work Week", Kind.BAT),
        Integer("tou_slot8_param1", 47592, "TOU Slot 8 Parameter 1", "", Kind.BAT),
        Integer("tou_slot8_param2", 47593, "TOU Slot 8 Parameter 2", "", Kind.BAT),
        MonthMask("tou_slot8_months", 47594, "TOU Slot 8 Months", Kind.BAT),
        Integer("dod_holding", 47602, "DoD Holding", "", Kind.BAT),
        Integer("backup_mode_enable", 47605, "Backup Mode Switch"),
        Integer("max_charge_power", 47606, "Max Charge Power"),
        Integer("smart_charging_enable", 47609, "Smart Charging Mode Switch"),
        Integer("eco_mode_enable", 47612, "Eco Mode Switch"),
    )

    def __init__(self, host: str, port: int, comm_addr: int = 0, timeout: int = 1, retries: int = 3):
        super().__init__(host, port, comm_addr if comm_addr else 0xf7, timeout, retries)
        self._READ_DEVICE_VERSION_INFO: ProtocolCommand = self._read_command(0x88b8, 0x0021)
        self._READ_RUNNING_DATA: ProtocolCommand = self._read_command(0x891c, 0x007d)
        self._READ_METER_DATA: ProtocolCommand = self._read_command(0x8ca0, 0x2d)
        self._READ_METER_DATA_EXTENDED: ProtocolCommand = self._read_command(0x8ca0, 0x3a)
        self._READ_METER_DATA_EXTENDED2: ProtocolCommand = self._read_command(0x8ca0, 0x7d)
        self._READ_BATTERY_INFO: ProtocolCommand = self._read_command(0x9088, 0x0018)
        self._READ_BATTERY2_INFO: ProtocolCommand = self._read_command(0x9858, 0x0016)
        self._READ_MPPT_DATA: ProtocolCommand = self._read_command(0x89e5, 0x3d)
        self._READ_PARALLEL_DATA: ProtocolCommand = self._read_command(0x28a0, 0x56)
        # Observation registers for undocumented data
        # Observation sensor commands - split into blocks (max 125 registers per read due to Modbus limitations)
        # 48xxx range: 48000-48806 (807 regs total) - split into 7 blocks
        self._READ_OBS_48XXX_1: ProtocolCommand = self._read_command(48000, 125)   # 48000-48124
        self._READ_OBS_48XXX_2: ProtocolCommand = self._read_command(48125, 125)   # 48125-48249
        self._READ_OBS_48XXX_3: ProtocolCommand = self._read_command(48250, 125)   # 48250-48374
        self._READ_OBS_48XXX_4: ProtocolCommand = self._read_command(48375, 125)   # 48375-48499
        self._READ_OBS_48XXX_5: ProtocolCommand = self._read_command(48500, 125)   # 48500-48624
        self._READ_OBS_48XXX_6: ProtocolCommand = self._read_command(48625, 125)   # 48625-48749
        self._READ_OBS_48XXX_7: ProtocolCommand = self._read_command(48750, 57)    # 48750-48806
        # 33xxx range: 33000-33501 (502 regs total) - split into 5 blocks
        self._READ_OBS_33XXX_1: ProtocolCommand = self._read_command(33000, 125)   # 33000-33124
        self._READ_OBS_33XXX_2: ProtocolCommand = self._read_command(33125, 125)   # 33125-33249
        self._READ_OBS_33XXX_3: ProtocolCommand = self._read_command(33250, 125)   # 33250-33374
        self._READ_OBS_33XXX_4: ProtocolCommand = self._read_command(33375, 125)   # 33375-33499
        self._READ_OBS_33XXX_5: ProtocolCommand = self._read_command(33500, 2)     # 33500-33501
        # 38xxx range: 38000-38463 (464 regs total) - split into 4 blocks
        self._READ_OBS_38XXX_1: ProtocolCommand = self._read_command(38000, 125)   # 38000-38124
        self._READ_OBS_38XXX_2: ProtocolCommand = self._read_command(38125, 125)   # 38125-38249
        self._READ_OBS_38XXX_3: ProtocolCommand = self._read_command(38250, 125)   # 38250-38374
        self._READ_OBS_38XXX_4: ProtocolCommand = self._read_command(38375, 89)    # 38375-38463
        # 55xxx range: 55000-55402 (403 regs total) - split into 4 blocks
        self._READ_OBS_55XXX_1: ProtocolCommand = self._read_command(55000, 125)   # 55000-55124
        self._READ_OBS_55XXX_2: ProtocolCommand = self._read_command(55125, 125)   # 55125-55249
        self._READ_OBS_55XXX_3: ProtocolCommand = self._read_command(55250, 125)   # 55250-55374
        self._READ_OBS_55XXX_4: ProtocolCommand = self._read_command(55375, 28)    # 55375-55402
        self._has_eco_mode_v2: bool = True
        self._has_peak_shaving: bool = True
        self._has_battery: bool = True
        self._has_battery2: bool = False
        self._has_meter: bool = True
        self._has_meter_extended: bool = False
        self._has_meter_extended2: bool = False
        self._has_mppt: bool = False
        self._has_parallel: bool = False
        # Observation sensors for undocumented registers (disabled by default)
        # Set to True to enable observation of these registers for debugging/research
        self._observe_48xxx: bool = False  # Slave-specific battery registers
        self._observe_33xxx: bool = False  # Grid configuration/limits
        self._observe_38xxx: bool = False  # Grid phase settings
        self._observe_55xxx: bool = False  # Energy counters
        # Parallel system topology detection (auto-detected on first ILLEGAL_DATA_ADDRESS)
        self._parallel_topology: str = "standalone"  # "standalone", "master_in_parallel", "slave_in_parallel"
        self._sensors = self.__all_sensors
        self._sensors_battery = self.__all_sensors_battery
        self._sensors_battery2 = self.__all_sensors_battery2
        self._sensors_meter = self.__all_sensors_meter
        self._sensors_mppt = self.__all_sensors_mppt
        self._sensors_parallel = self.__all_sensors_parallel
        self._sensors_obs_48xxx = self.__observation_sensors_48xxx
        self._sensors_obs_33xxx = self.__observation_sensors_33xxx
        self._sensors_obs_38xxx = self.__observation_sensors_38xxx
        self._sensors_obs_55xxx = self.__observation_sensors_55xxx
        self._settings: dict[str, Sensor] = {s.id_: s for s in self.__all_settings}
        self._sensors_map: dict[str, Sensor] | None = None

    @staticmethod
    def _single_phase_only(s: Sensor) -> bool:
        """Filter to exclude phase2/3 sensors on single phase inverters"""
        return not ((s.id_.endswith('2') or s.id_.endswith('3')) and 'pv' not in s.id_)

    @staticmethod
    def _not_extended_meter(s: Sensor) -> bool:
        """Filter to exclude extended meter sensors"""
        return s.offset < 36045

    @staticmethod
    def _not_extended_meter2(s: Sensor) -> bool:
        """Filter to exclude extended meter sensors"""
        return s.offset < 36058

    @staticmethod
    def _not_slave_only_restricted(s: Sensor) -> bool:
        """Filter to exclude registers that SLAVE inverters in parallel systems cannot access.

        Slave inverters in parallel systems don't have access to:
        - Battery Info (36000-36149) - master aggregates battery data
        - Meter Data (36995-37074) - meter connected to master only
        - Battery Settings (47500-47546) - master controls battery
        - EMS/TOU Settings (47547-47591, 47594-47650) - master manages EMS/TOU
          EXCEPTION: 47592-47593 (Peak Shaving power/SOC slot 8) ARE accessible on slave
        - Parallel System global data (10400-10411) - master manages system coordination

        Note: Standalone and master_in_parallel inverters have access to all these registers
        (except parallel system registers which don't exist on standalone).
        """
        return not (
            (36000 <= s.offset <= 36149) or  # Battery Info
            (36995 <= s.offset <= 37074) or  # Meter Data
            (47500 <= s.offset <= 47546) or  # Battery Settings
            (47547 <= s.offset <= 47591) or  # EMS/TOU (slots 1-8 start/end/week)
            (47594 <= s.offset <= 47650) or  # EMS/TOU (slots 8 months + other settings)
            (10400 <= s.offset <= 10411)     # Parallel System (global data)
        )
        # Registers accessible on SLAVE inverters (intentionally NOT blocked):
        # - 45353 (battery_charge_current) - Battery charge current limit
        # - 45355 (battery_discharge_current) - Battery discharge current limit
        # - 47592 (tou_slot8_param1) - Peak Shaving power limit for slot 8
        # - 47593 (tou_slot8_param2) - Peak Shaving SOC for slot 8

    @staticmethod
    def _not_parallel_system(s: Sensor) -> bool:
        """Filter to exclude parallel system registers (10400-10485).

        These registers only exist on inverters in parallel systems (master or slave with data).
        Standalone inverters don't have these registers.
        """
        return not (10400 <= s.offset <= 10485)

    async def read_device_info(self):
        response = await self._read_from_socket(self._READ_DEVICE_VERSION_INFO)
        response = response.response_data()
        # Modbus registers from 35000 - 35032
        self.modbus_version = read_unsigned_int(response, 0)
        self.rated_power = read_unsigned_int(response, 2)
        self.ac_output_type = read_unsigned_int(response, 4)  # 0: 1-phase, 1: 3-phase (4 wire), 2: 3-phase (3 wire)
        self.serial_number = self._decode(response[6:22])  # 35003 - 350010
        self.model_name = self._decode(response[22:32])  # 35011 - 35015
        self.dsp1_version = read_unsigned_int(response, 32)  # 35016
        self.dsp2_version = read_unsigned_int(response, 34)  # 35017
        self.dsp_svn_version = read_unsigned_int(response, 36)  # 35018
        self.arm_version = read_unsigned_int(response, 38)  # 35019
        self.arm_svn_version = read_unsigned_int(response, 40)  # 35020
        self.firmware = self._decode(response[42:54])  # 35021 - 35027
        self.arm_firmware = self._decode(response[54:66])  # 35027 - 35032

        # Filter PV sensors based on MPPT count
        # Standard mapping: MPPT1->PV1+PV2, MPPT2->PV3+PV4, MPPT3->PV5+PV6, MPPT4->PV7+PV8
        # Note: Main sensors (35103-35119) only have PV1-4, extended PV5-16 are in _sensors_mppt
        if is_3_mppt(self):
            # 3 MPPT inverters: PV1-4 (main sensors) + PV5-16 (MPPT sensors, filtered below to PV5-6)
            # Keep PV1-4 in main sensors, filter MPPT sensors to PV5-6 only (not PV7-16)
            self._sensors_mppt = tuple(filter(lambda s: not any(f'pv{i}' in s.id_ for i in range(7, 17)), self._sensors_mppt))
        elif is_4_mppt(self):
            # 4 MPPT inverters (e.g. ET50): PV1-8, filter out PV9-16 from MPPT sensors
            self._sensors_mppt = tuple(filter(lambda s: not any(f'pv{i}' in s.id_ for i in range(9, 17)), self._sensors_mppt))
        elif not is_4_mppt(self) and self.rated_power < 15000:
            # Small inverters (< 15kW) without explicit 3/4 MPPT: PV1-4 only (2 MPPT assumed)
            self._sensors = tuple(filter(lambda s: 'pv4' not in s.id_, self._sensors))
            self._sensors = tuple(filter(lambda s: 'pv3' not in s.id_, self._sensors))

        if is_single_phase(self):
            # this is single phase inverter, filter out all L2 and L3 sensors
            self._sensors = tuple(filter(self._single_phase_only, self._sensors))
            self._sensors_meter = tuple(filter(self._single_phase_only, self._sensors_meter))

        # Battery configuration detection (deterministic by model, no fallbacks)
        # Most ET models have 1 battery input, only ET 25-30kW models have 2
        # Note: Battery2 defaults to False (line ~726), only explicitly enabled for 2-battery models
        if is_2_battery(self):
            self._has_battery2 = True
            logger.debug("Model has 2 battery inputs (ET 25-30kW series)")
        elif is_1_battery(self):
            self._has_battery2 = False
            logger.debug("Model has 1 battery input (confirmed by model detection)")

        if is_745_platform(self) or self.rated_power >= 15000:
            self._has_mppt = True
            self._has_meter_extended = True
            self._has_meter_extended2 = True
        else:
            self._sensors_meter = tuple(filter(self._not_extended_meter, self._sensors_meter))

        # Check and add EcoModeV2 settings added in (ETU fw 19)
        try:
            await self._read_from_socket(self._read_command(47547, 6))
            self._settings.update({s.id_: s for s in self.__settings_arm_fw_19})
        except RequestRejectedException as ex:
            if ex.message == ILLEGAL_DATA_ADDRESS:
                logger.debug("EcoModeV2 settings not supported, switching to EcoModeV1.")
                self._has_eco_mode_v2 = False
        except RequestFailedException:
            logger.debug("Cannot read EcoModeV2 settings, switching to EcoModeV1.")
            self._has_eco_mode_v2 = False

        # Check and add Peak Shaving settings added in (ETU fw 22)
        try:
            await self._read_from_socket(self._read_command(47589, 6))
            self._settings.update({s.id_: s for s in self.__settings_arm_fw_22})
        except RequestRejectedException as ex:
            if ex.message == ILLEGAL_DATA_ADDRESS:
                logger.debug("PeakShaving setting not supported, disabling it.")
                self._has_peak_shaving = False
        except RequestFailedException:
            logger.debug("Cannot read _has_peak_shaving settings, disabling it.")
            self._has_peak_shaving = False

        # Detect parallel system topology by reading register 10400 (Inverter Quantity)
        # This register tells us the system configuration:
        # - 1: Standalone inverter (no parallel system)
        # - >1: Master in parallel system (coordinates N inverters)
        # - ILLEGAL_DATA_ADDRESS: Slave in parallel system (can't access master-only register 10400)
        try:
            response = await self._read_from_socket(self._read_command(10400, 1))
            inverter_quantity = int.from_bytes(response.read(2), byteorder="big", signed=False)
            if inverter_quantity > 1:
                # Multiple inverters configured - this is the MASTER in parallel system
                logger.info(
                    "Detected MASTER inverter in parallel system with %d inverters. "
                    "Full access to battery, meter, EMS/TOU, and parallel coordination.",
                    inverter_quantity
                )
                self._parallel_topology = "master_in_parallel"
                self._has_parallel = True
            elif inverter_quantity == 1:
                # Single inverter - STANDALONE system
                logger.info(
                    "Detected STANDALONE inverter (single inverter system). "
                    "Has battery, meter, EMS/TOU access. No parallel system registers."
                )
                self._parallel_topology = "standalone"
                self._has_parallel = False
            else:
                # Unexpected value (0 or negative) - treat as standalone
                logger.warning("Unexpected inverter quantity %d, treating as standalone.", inverter_quantity)
                self._parallel_topology = "standalone"
                self._has_parallel = False
        except RequestRejectedException as ex:
            if ex.message == ILLEGAL_DATA_ADDRESS:
                # Can't read register 10400 - this is a SLAVE in parallel system
                logger.info(
                    "Register 10400 (Inverter Quantity) not accessible - detected SLAVE inverter in parallel system. "
                    "Filtering out battery info, meter, EMS/TOU, and master-only parallel registers."
                )
                self._parallel_topology = "slave_in_parallel"
                self._has_parallel = True  # Has some parallel sensors (10412+), but not master-only ones
            else:
                raise ex
        except RequestFailedException as ex:
            logger.debug("Cannot determine parallel topology (communication error): %s", ex)
            # Keep default "standalone" topology on communication errors
            self._has_parallel = False

    async def read_runtime_data(self) -> dict[str, Any]:
        response = await self._read_from_socket(self._READ_RUNNING_DATA)
        data = self._map_response(response, self._sensors)

        self._has_battery = data.get('battery_mode', 0) != 0
        if self._has_battery:
            try:
                response = await self._read_from_socket(self._READ_BATTERY_INFO)
                data.update(self._map_response(response, self._sensors_battery))
            except RequestRejectedException as ex:
                if ex.message == ILLEGAL_DATA_ADDRESS:
                    logger.info("Battery values not supported, disabling further attempts.")
                    self._has_battery = False
                else:
                    raise ex
        if self._has_battery2:
            try:
                response = await self._read_from_socket(self._READ_BATTERY2_INFO)
                data.update(
                    self._map_response(response, self._sensors_battery2))
            except RequestRejectedException as ex:
                if ex.message == ILLEGAL_DATA_ADDRESS:
                    logger.info("Battery 2 values not supported, disabling further attempts.")
                    self._has_battery2 = False
                else:
                    raise ex

        if self._has_meter and self._has_meter_extended2:
            try:
                response = await self._read_from_socket(self._READ_METER_DATA_EXTENDED2)
                data.update(self._map_response(response, self._sensors_meter))
            except RequestRejectedException as ex:
                if ex.message == ILLEGAL_DATA_ADDRESS:
                    logger.info("Extended meter values not supported, disabling further attempts.")
                    self._has_meter_extended2 = False
                    self._sensors_meter = tuple(filter(self._not_extended_meter2, self._sensors_meter))
                    try:
                        response = await self._read_from_socket(self._READ_METER_DATA_EXTENDED)
                        data.update(
                            self._map_response(response, self._sensors_meter))
                    except RequestRejectedException as ex2:
                        if ex2.message == ILLEGAL_DATA_ADDRESS:
                            logger.info("Extended meter values not supported, disabling further attempts.")
                            self._has_meter_extended = False
                            self._sensors_meter = tuple(filter(self._not_extended_meter, self._sensors_meter))
                            try:
                                response = await self._read_from_socket(self._READ_METER_DATA)
                                data.update(
                                    self._map_response(response, self._sensors_meter))
                            except RequestRejectedException as ex3:
                                if ex3.message == ILLEGAL_DATA_ADDRESS:
                                    logger.info("Meter values not supported, disabling further attempts.")
                                    self._has_meter = False
                                else:
                                    raise ex3
                        else:
                            raise ex2
                else:
                    raise ex
        elif self._has_meter and self._has_meter_extended:
            try:
                response = await self._read_from_socket(self._READ_METER_DATA_EXTENDED)
                data.update(self._map_response(response, self._sensors_meter))
            except RequestRejectedException as ex:
                if ex.message == ILLEGAL_DATA_ADDRESS:
                    logger.info("Extended meter values not supported, disabling further attempts.")
                    self._has_meter_extended = False
                    self._sensors_meter = tuple(filter(self._not_extended_meter, self._sensors_meter))
                    try:
                        response = await self._read_from_socket(self._READ_METER_DATA)
                        data.update(
                            self._map_response(response, self._sensors_meter))
                    except RequestRejectedException as ex2:
                        if ex2.message == ILLEGAL_DATA_ADDRESS:
                            logger.info("Meter values not supported, disabling further attempts.")
                            self._has_meter = False
                        else:
                            raise ex2
                else:
                    raise ex
        elif self._has_meter:
            try:
                response = await self._read_from_socket(self._READ_METER_DATA)
                data.update(self._map_response(response, self._sensors_meter))
            except RequestRejectedException as ex:
                if ex.message == ILLEGAL_DATA_ADDRESS:
                    logger.info("Meter values not supported, disabling further attempts.")
                    self._has_meter = False
                else:
                    raise ex

        if self._has_mppt:
            try:
                response = await self._read_from_socket(self._READ_MPPT_DATA)
                data.update(self._map_response(response, self._sensors_mppt))
            except RequestRejectedException as ex:
                if ex.message == ILLEGAL_DATA_ADDRESS:
                    logger.info("MPPT values not supported, disabling further attempts.")
                    self._has_mppt = False
                else:
                    raise ex

        if self._has_parallel:
            try:
                response = await self._read_from_socket(self._READ_PARALLEL_DATA)
                data.update(self._map_response(response, self._sensors_parallel))
                # Calculate meter current from power and voltage: I = P / V
                # Power sources: parallel_meter_active_power_r/s/t (registers 10481/10483/10485)
                # Voltage sources: vgrid/vgrid2/vgrid3 (registers 35121/35126/35131)
                for phase, power_key, voltage_key in [
                    ("l1", "parallel_meter_active_power_r", "vgrid"),
                    ("l2", "parallel_meter_active_power_s", "vgrid2"),
                    ("l3", "parallel_meter_active_power_t", "vgrid3"),
                ]:
                    power = data.get(power_key, 0) or 0
                    voltage = data.get(voltage_key, 0) or 0
                    if voltage > 0:
                        current = round(power / voltage, 2)
                    else:
                        current = 0.0
                    data[f"parallel_meter_current_{phase}_calc"] = current
            except RequestRejectedException as ex:
                if ex.message == ILLEGAL_DATA_ADDRESS:
                    logger.info("Parallel system values not supported, disabling further attempts.")
                    self._has_parallel = False
                else:
                    raise ex

        # Observation sensors for undocumented registers (disabled by default)
        if self._observe_48xxx:
            try:
                # Read 48xxx in 7 blocks (max 125 registers per read)
                for read_cmd in [self._READ_OBS_48XXX_1, self._READ_OBS_48XXX_2, self._READ_OBS_48XXX_3,
                                self._READ_OBS_48XXX_4, self._READ_OBS_48XXX_5, self._READ_OBS_48XXX_6,
                                self._READ_OBS_48XXX_7]:
                    response = await self._read_from_socket(read_cmd)
                    data.update(self._map_response(response, self._sensors_obs_48xxx))
            except RequestRejectedException as ex:
                if ex.message == ILLEGAL_DATA_ADDRESS:
                    logger.debug("Observation 48xxx read failed (ILLEGAL_DATA_ADDRESS), will retry on next update.")
                else:
                    raise ex

        if self._observe_33xxx:
            try:
                # Read 33xxx in 5 blocks (max 125 registers per read)
                for read_cmd in [self._READ_OBS_33XXX_1, self._READ_OBS_33XXX_2, self._READ_OBS_33XXX_3,
                                self._READ_OBS_33XXX_4, self._READ_OBS_33XXX_5]:
                    response = await self._read_from_socket(read_cmd)
                    data.update(self._map_response(response, self._sensors_obs_33xxx))
            except RequestRejectedException as ex:
                if ex.message == ILLEGAL_DATA_ADDRESS:
                    logger.debug("Observation 33xxx read failed (ILLEGAL_DATA_ADDRESS), will retry on next update.")
                else:
                    raise ex

        if self._observe_38xxx:
            try:
                # Read 38xxx in 4 blocks (max 125 registers per read)
                for read_cmd in [self._READ_OBS_38XXX_1, self._READ_OBS_38XXX_2, self._READ_OBS_38XXX_3,
                                self._READ_OBS_38XXX_4]:
                    response = await self._read_from_socket(read_cmd)
                    data.update(self._map_response(response, self._sensors_obs_38xxx))
            except RequestRejectedException as ex:
                if ex.message == ILLEGAL_DATA_ADDRESS:
                    logger.debug("Observation 38xxx read failed (ILLEGAL_DATA_ADDRESS), will retry on next update.")
                else:
                    raise ex

        if self._observe_55xxx:
            try:
                # Read 55xxx in 4 blocks (max 125 registers per read)
                for read_cmd in [self._READ_OBS_55XXX_1, self._READ_OBS_55XXX_2, self._READ_OBS_55XXX_3,
                                self._READ_OBS_55XXX_4]:
                    response = await self._read_from_socket(read_cmd)
                    data.update(self._map_response(response, self._sensors_obs_55xxx))
            except RequestRejectedException as ex:
                if ex.message == ILLEGAL_DATA_ADDRESS:
                    logger.debug("Observation 55xxx read failed (ILLEGAL_DATA_ADDRESS), will retry on next update.")
                else:
                    raise ex

        # Add inverter serial number as a constant sensor value
        data["serial_number"] = self.serial_number

        return data

    async def read_sensor(self, sensor_id: str) -> Any:
        sensor: Sensor = self._get_sensor(sensor_id)
        if sensor:
            return await self._read_sensor(sensor)
        if sensor_id.startswith("modbus"):
            response = await self._read_from_socket(self._read_command(int(sensor_id[7:]), 1))
            return int.from_bytes(response.read(2), byteorder="big", signed=True)
        raise ValueError(f'Unknown sensor "{sensor_id}"')

    async def read_setting(self, setting_id: str) -> Any:
        setting: Sensor = self._settings.get(setting_id)
        if setting:
            # Early exit if we already know this register is inaccessible (slave inverter)
            # Topology is detected in read_device_info() by reading register 10400
            if self._parallel_topology == "slave_in_parallel" and not self._not_slave_only_restricted(setting):
                raise RequestRejectedException(ILLEGAL_DATA_ADDRESS)
            return await self._read_sensor(setting)
        if setting_id.startswith("modbus"):
            response = await self._read_from_socket(self._read_command(int(setting_id[7:]), 1))
            return int.from_bytes(response.read(2), byteorder="big", signed=True)
        raise ValueError(f'Unknown setting "{setting_id}"')

    async def _read_sensor(self, sensor: Sensor) -> Any:
        try:
            count = (sensor.size_ + (sensor.size_ % 2)) // 2
            response = await self._read_from_socket(self._read_command(sensor.offset, count))
            return sensor.read_value(response)
        except RequestRejectedException as ex:
            if ex.message == ILLEGAL_DATA_ADDRESS:
                logger.debug("Unsupported sensor/setting %s", sensor.id_)
                self._settings.pop(sensor.id_, None)
                raise ValueError(f'Unknown sensor/setting "{sensor.id_}"')
            return None

    async def write_setting(self, setting_id: str, value: Any):
        setting = self._settings.get(setting_id)
        if setting:
            await self._write_setting(setting, value)
        else:
            if setting_id.startswith("modbus"):
                await self._read_from_socket(self._write_command(int(setting_id[7:]), int(value)))
            else:
                raise ValueError(f'Unknown setting "{setting_id}"')

    async def _write_setting(self, setting: Sensor, value: Any):
        if setting.size_ == 1:
            # modbus can address/store only 16 bit values, read the other 8 bytes
            response = await self._read_from_socket(self._read_command(setting.offset, 1))
            raw_value = setting.encode_value(value, response.response_data()[0:2])
        else:
            raw_value = setting.encode_value(value)
        if len(raw_value) <= 2:
            value = int.from_bytes(raw_value, byteorder="big", signed=True)
            await self._read_from_socket(self._write_command(setting.offset, value))
        else:
            await self._read_from_socket(self._write_multi_command(setting.offset, raw_value))

    async def read_settings_data(self) -> dict[str, Any]:
        data = {}
        for setting in self.settings():
            try:
                value = await self.read_setting(setting.id_)
                data[setting.id_] = value
            except (ValueError, RequestFailedException):
                logger.exception("Error reading setting %s.", setting.id_)
                data[setting.id_] = None
        return data

    async def get_grid_export_limit(self) -> int:
        return await self.read_setting('grid_export_limit')

    async def set_grid_export_limit(self, export_limit: int) -> None:
        if export_limit >= 0:
            await self.write_setting('grid_export_limit', export_limit)

    async def get_operation_modes(self, include_emulated: bool) -> tuple[OperationMode, ...]:
        result = list(OperationMode)
        if not self._has_peak_shaving:
            result.remove(OperationMode.PEAK_SHAVING)
        if not is_745_platform(self):
            result.remove(OperationMode.SELF_USE)
        if not include_emulated:
            result.remove(OperationMode.ECO_CHARGE)
            result.remove(OperationMode.ECO_DISCHARGE)
        return tuple(result)

    async def get_operation_mode(self) -> OperationMode | None:
        mode_id = await self.read_setting('work_mode')
        try:
            mode = OperationMode(mode_id)
        except ValueError:
            logger.debug("Unknown work_mode value %s", mode_id)
            return None
        if OperationMode.ECO != mode:
            return mode
        eco_mode = await self.read_setting('eco_mode_1')
        if eco_mode.is_eco_charge_mode():
            return OperationMode.ECO_CHARGE
        if eco_mode.is_eco_discharge_mode():
            return OperationMode.ECO_DISCHARGE
        return OperationMode.ECO

    async def set_operation_mode(self, operation_mode: OperationMode, eco_mode_power: int = 100,
                                 eco_mode_soc: int = 100) -> None:
        if operation_mode == OperationMode.GENERAL:
            await self.write_setting('work_mode', 0)
            await self._set_offline(False)
            await self._clear_battery_mode_param()
        elif operation_mode == OperationMode.OFF_GRID:
            await self.write_setting('work_mode', 1)
            await self._set_offline(True)
            await self.write_setting('backup_supply', 1)
            await self.write_setting('cold_start', 4)
            await self._clear_battery_mode_param()
        elif operation_mode == OperationMode.BACKUP:
            await self.write_setting('work_mode', 2)
            await self._set_offline(False)
            await self._clear_battery_mode_param()
        elif operation_mode == OperationMode.ECO:
            await self.write_setting('work_mode', 3)
            await self._set_offline(False)
        elif operation_mode == OperationMode.PEAK_SHAVING:
            await self.write_setting('work_mode', 4)
            await self._set_offline(False)
            await self._clear_battery_mode_param()
        elif operation_mode == OperationMode.SELF_USE:
            await self.write_setting('work_mode', 5)
            await self._set_offline(False)
            await self._clear_battery_mode_param()
        elif operation_mode in (OperationMode.ECO_CHARGE, OperationMode.ECO_DISCHARGE):
            if eco_mode_power < 0 or eco_mode_power > 100:
                raise ValueError()
            if eco_mode_soc < 0 or eco_mode_soc > 100:
                raise ValueError()

            eco_mode: EcoMode | Sensor = self._settings.get('eco_mode_1')
            # Load the current values to try to detect schedule type
            try:
                await self._read_sensor(eco_mode)
            except ValueError:
                pass
            eco_mode.set_schedule_type(ScheduleType.ECO_MODE, is_745_platform(self))
            if operation_mode == OperationMode.ECO_CHARGE:
                await self.write_setting('eco_mode_1', eco_mode.encode_charge(eco_mode_power, eco_mode_soc))
            else:
                await self.write_setting('eco_mode_1', eco_mode.encode_discharge(eco_mode_power))
            await self.write_setting('eco_mode_2_switch', 0)
            await self.write_setting('eco_mode_3_switch', 0)
            await self.write_setting('eco_mode_4_switch', 0)
            await self.write_setting('work_mode', 3)
            await self._set_offline(False)

    async def get_ongrid_battery_dod(self) -> int:
        return 100 - await self.read_setting('battery_discharge_depth')

    async def set_ongrid_battery_dod(self, dod: int) -> None:
        if 0 <= dod <= 100:
            await self.write_setting('battery_discharge_depth', 100 - dod)

    def _get_sensor(self, sensor_id: str) -> Sensor | None:
        if self._sensors_map is None:
            self._sensors_map = {s.id_: s for s in self.sensors()}
        return self._sensors_map.get(sensor_id)

    @property
    def sensor_name_prefix(self) -> str:
        """
        Generate entity ID prefix based on last 4 characters of serial number.

        Used to distinguish multiple inverters in parallel systems in Home Assistant.
        Format: GWxxxx_ where xxxx are last 4 characters of serial number.

        Examples:
            - Serial 9040KETF00CW0000 → GW0000_
            - Serial 9040KETF254L0008 → GW0008_

        Returns empty string if serial_number is not yet available.
        """
        if self.serial_number and len(self.serial_number) >= 4:
            return f"GW{self.serial_number[-4:]}_"
        return ""

    def sensors(self) -> tuple[Sensor, ...]:
        # Main runtime sensors (PV, grid, battery power, TOU, etc.)
        result = self._sensors

        # Filter slave-restricted sensors if this is a slave in parallel system
        if self._parallel_topology == "slave_in_parallel":
            result = tuple(filter(self._not_slave_only_restricted, result))

        # Meter data sensors
        # - Available on standalone and master_in_parallel
        # - NOT available on slave_in_parallel (meter connected to master only)
        if self._parallel_topology != "slave_in_parallel":
            result = result + self._sensors_meter

        # Battery info sensors (36000-36149)
        # - Available on standalone and master_in_parallel
        # - NOT available on slave_in_parallel (master aggregates battery data)
        if self._has_battery and self._parallel_topology != "slave_in_parallel":
            result = result + self._sensors_battery
        if self._has_battery2 and self._parallel_topology != "slave_in_parallel":
            result = result + self._sensors_battery2

        # MPPT sensors - available on all topologies
        if self._has_mppt:
            result = result + self._sensors_mppt

        # Parallel system sensors (10400-10485)
        # - NOT available on standalone (registers don't exist)
        # - Available on master_in_parallel (all registers)
        # - Partially available on slave_in_parallel (10412+, not 10400-10411)
        if self._has_parallel:
            parallel_sensors = self._sensors_parallel
            # Filter master-only parallel registers on slave (10400-10411: global system data)
            if self._parallel_topology == "slave_in_parallel":
                parallel_sensors = tuple(filter(self._not_slave_only_restricted, parallel_sensors))
            result = result + parallel_sensors

        # Observation sensors for undocumented registers (disabled by default)
        # Enable by setting inverter._observe_48xxx = True, etc.
        if self._observe_48xxx:
            result = result + self._sensors_obs_48xxx
        if self._observe_33xxx:
            result = result + self._sensors_obs_33xxx
        if self._observe_38xxx:
            result = result + self._sensors_obs_38xxx
        if self._observe_55xxx:
            result = result + self._sensors_obs_55xxx

        return result

    def settings(self) -> tuple[Sensor, ...]:
        result = tuple(self._settings.values())
        # Filter slave-restricted settings if this is a slave in parallel system
        # (battery settings, EMS/TOU settings, parallel system master-only settings)
        if self._parallel_topology == "slave_in_parallel":
            result = tuple(filter(self._not_slave_only_restricted, result))
        return result

    async def discover_parallel_slaves(self) -> dict[int, dict[str, Any]]:
        """
        Auto-discover all slave inverters in a parallel system.

        Reads register 10400 to determine total inverter count, then scans
        Modbus IDs 1-15 to find slave inverters and read their serial numbers
        from registers 35003-35010 (8 registers × 2 bytes = 16 ASCII chars).

        Returns:
            dict mapping Modbus comm_addr to inverter info:
            {
                1: {
                    'serial_number': '9040KETF254L0008',
                    'comm_addr': 1,
                    'role': 'slave',
                    'sensor_prefix': 'GW0008_'
                },
                ...
            }

        Raises:
            RequestFailedException: If master inverter not accessible
            ValueError: If not in parallel system

        Example:
            master = await goodwe.connect('10.10.20.91', 247)
            slaves = await master.discover_parallel_slaves()
            print(f"Found {len(slaves)} slave inverters")
            for addr, info in slaves.items():
                print(f"  Slave {addr}: {info['serial_number']}")
        """
        # Ensure we have device info (serial number, parallel count)
        if not self.serial_number:
            await self.read_device_info()

        # Check if this is a parallel system
        if not self._has_parallel:
            raise ValueError(
                f"Inverter {self.serial_number} is not in a parallel system "
                f"(_has_parallel={self._has_parallel})"
            )

        # Read total inverter count from register 10400
        try:
            response = await self._read_from_socket(self._read_command(10400, 1))
            total_inverters = int.from_bytes(response, byteorder='big')
            logger.info(f"Parallel system has {total_inverters} inverters total")
        except Exception as e:
            raise RequestFailedException(
                f"Failed to read parallel inverter count from register 10400: {e}"
            ) from e

        if total_inverters <= 1:
            logger.warning(f"Parallel count is {total_inverters}, no slaves to discover")
            return {}

        # Expected number of slaves (total - 1 master)
        expected_slaves = total_inverters - 1

        # Scan Modbus IDs 1-15 to find slaves
        discovered_slaves = {}

        for comm_addr in range(1, 16):  # Modbus slave IDs typically 1-15
            if len(discovered_slaves) >= expected_slaves:
                break  # Found all expected slaves

            try:
                # Try to read serial number from registers 35003-35010 (8 registers)
                # Create temporary connection with different comm_addr
                from .protocol import ModbusRtuReadCommand
                command = ModbusRtuReadCommand(comm_addr, 35003, 8)
                response = await self._read_from_socket(command)

                # Decode serial number (16 ASCII characters from 8 registers)
                serial_bytes = bytes(response)
                serial_number = serial_bytes.decode('ascii', errors='ignore').rstrip('\x00')

                if serial_number and len(serial_number) >= 4:
                    # Valid serial number found - this is a slave
                    sensor_prefix = f"GW{serial_number[-4:]}_"

                    discovered_slaves[comm_addr] = {
                        'serial_number': serial_number,
                        'comm_addr': comm_addr,
                        'role': 'slave',
                        'sensor_prefix': sensor_prefix
                    }

                    logger.info(
                        f"Found slave inverter at Modbus ID {comm_addr}: "
                        f"{serial_number} (prefix: {sensor_prefix})"
                    )
                else:
                    logger.debug(f"Modbus ID {comm_addr}: Invalid serial number")

            except Exception as e:
                logger.debug(f"Modbus ID {comm_addr}: No response ({type(e).__name__})")
                continue

        # Verify we found all expected slaves
        if len(discovered_slaves) != expected_slaves:
            logger.warning(
                f"Expected {expected_slaves} slaves but found {len(discovered_slaves)}: "
                f"{list(discovered_slaves.keys())}"
            )

        return discovered_slaves

    async def _clear_battery_mode_param(self) -> None:
        await self._read_from_socket(self._write_command(0xb9ad, 1))

    async def _set_offline(self, mode: bool) -> None:
        value = bytes.fromhex('00070000') if mode else bytes.fromhex('00010000')
        await self._read_from_socket(self._write_multi_command(0xb997, value))
