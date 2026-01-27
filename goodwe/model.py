"""Constants identifying inverter type/model."""
from .inverter import Inverter

PLATFORM_105_MODELS = ("ESU", "EMU", "ESA", "BPS", "BPU", "EMJ", "IJL")
PLATFORM_205_MODELS = ("ETU", "ETL", "ETR", "BHN", "EHU", "BHU", "EHR", "BTU")
PLATFORM_745_LV_MODELS = ("ESN", "EBN", "EMN", "SPN", "ERN", "ESC", "HLB", "HMB", "HBB", "EOA")
PLATFORM_745_HV_MODELS = ("ETT", "HTA", "HUB", "AEB", "SPB", "CUB", "EUB", "HEB", "ERB", "BTT", "ETF", "ARB", "URB",
                          "EBR")
PLATFORM_753_MODELS = ("AES", "HHI", "ABP", "EHB", "HSB", "HUA", "CUA")

ET_MODEL_TAGS = PLATFORM_205_MODELS + PLATFORM_745_LV_MODELS + PLATFORM_745_HV_MODELS + PLATFORM_753_MODELS + (
    "ETC", "BTC", "BTN",  # Qianhai
    "40KET", "50KET")  # High power ET models
ES_MODEL_TAGS = PLATFORM_105_MODELS
DT_MODEL_TAGS = ("DTU", "DTS",
                 "MSU", "MST", "MSC", "DSN", "DTN", "DST", "NSU", "SSN", "SST", "SSX", "SSY",
                 "PSB", "PSC")

SINGLE_PHASE_MODELS = ("DSN", "DST", "NSU", "SSN", "SST", "SSX", "SSY",  # DT
                       "MSU", "MST", "PSB", "PSC",
                       "MSC",  # Found on third gen MS
                       "EHU", "EHR", "HSB",  # ET
                       "ESN", "EMN", "ERN", "EBN", "HLB", "HMB", "HBB", "SPN")  # ES Gen 2

# MPPT configuration by model
# MPPT3: 3 MPPT inputs with 1-2 strings per MPPT
MPPT3_MODELS = ("MSU", "MST", "PSC", "MSC",
                "10KET", "12KET", "15KET",  # ET series: 3 MPPT, 1 string/MPPT
                "25KET", "29K9ET", "25KMT",  # ET series: 3 MPPT, 2 strings/MPPT
                "40KET")  # ET40: 3 MPPT, 2 strings/MPPT

# MPPT4: 4 MPPT inputs
MPPT4_MODELS = ("HSB", "50KET")  # ET50: 4 MPPT, 2 strings/MPPT

# Battery configuration by model
# Single battery input models (most ET series)
BAT_1_MODELS = ("6000ET", "8000ET",  # ET 6-8kW: 1 battery, 2 MPPT
                "10KET", "12KET", "15KET",  # ET 10-15kW: 1 battery, 3 MPPT
                "20KET",  # ET 20kW: 1 battery, 2 MPPT (2 strings/MPPT)
                "40KET", "50KET")  # ET 40-50kW: 1 battery, 3-4 MPPT

# Dual battery input models (high power)
BAT_2_MODELS = ("25KET", "29K9ET")  # ET 25-30kW: 2 batteries, 3 MPPT


def is_single_phase(inverter: Inverter) -> bool:
    return any(model in inverter.serial_number for model in SINGLE_PHASE_MODELS)


def is_3_mppt(inverter: Inverter) -> bool:
    return any(model in inverter.serial_number for model in MPPT3_MODELS)


def is_4_mppt(inverter: Inverter) -> bool:
    return any(model in inverter.serial_number for model in MPPT4_MODELS)


def is_1_battery(inverter: Inverter) -> bool:
    """Check if inverter has single battery input (most ET models)."""
    return any(model in inverter.serial_number for model in BAT_1_MODELS)


def is_2_battery(inverter: Inverter) -> bool:
    """Check if inverter has dual battery inputs (ET 25-30kW models)."""
    return any(model in inverter.serial_number for model in BAT_2_MODELS)


def is_745_platform(inverter: Inverter) -> bool:
    return any(model in inverter.serial_number for model in PLATFORM_745_LV_MODELS) or any(
        model in inverter.serial_number for model in PLATFORM_745_HV_MODELS)


def is_753_platform(inverter: Inverter) -> bool:
    return any(model in inverter.serial_number for model in PLATFORM_753_MODELS)
