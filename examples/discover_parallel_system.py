#!/usr/bin/env python3
"""
Example: Auto-discover all inverters in a parallel system.

This script connects to a master inverter and automatically discovers
all slave inverters in the parallel system by:
1. Reading register 10400 to get total inverter count
2. Scanning Modbus IDs 1-15 to find slaves
3. Reading each slave's serial number from registers 35003-35010
4. Generating unique sensor prefixes (GWxxxx_) for each inverter

Usage:
    python discover_parallel_system.py <master_ip>

Example:
    python discover_parallel_system.py 10.10.20.91
"""

import asyncio
import sys
import logging

import goodwe

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def discover_system(master_ip: str, master_comm_addr: int = 247):
    """
    Discover all inverters in a parallel system.

    Args:
        master_ip: IP address of master inverter
        master_comm_addr: Modbus communication address of master (default 247)
    """
    print(f"\n{'='*60}")
    print(f"Parallel System Discovery")
    print(f"{'='*60}\n")

    # Connect to master inverter
    print(f"Connecting to master inverter at {master_ip}:{master_comm_addr}...")
    try:
        master = await goodwe.connect(master_ip, 502, master_comm_addr)
        print(f"✓ Connected to {master.model_name or 'ET-series'} inverter\n")
    except Exception as e:
        print(f"✗ Failed to connect: {e}")
        return

    # Read master device info
    try:
        await master.read_device_info()
        print(f"Master Inverter:")
        print(f"  Serial Number:     {master.serial_number}")
        print(f"  Model:             {master.model_name or 'Unknown'}")
        print(f"  Rated Power:       {master.rated_power}W")
        print(f"  Firmware:          {master.firmware}")
        print(f"  Sensor Prefix:     {master.sensor_name_prefix}")
        print()
    except Exception as e:
        print(f"✗ Failed to read device info: {e}")
        return

    # Check if this is a parallel system
    if not master._has_parallel:
        print("⚠ This inverter is not in a parallel system.")
        print("  (Register 10400 returned error or count <= 1)")
        return

    # Discover slaves
    print(f"Discovering slave inverters...")
    print(f"(Scanning Modbus IDs 1-15 for active slaves)\n")

    try:
        slaves = await master.discover_parallel_slaves()

        if not slaves:
            print("⚠ No slave inverters found.")
            print("  Expected slaves but discovery returned empty.")
            return

        print(f"✓ Found {len(slaves)} slave inverter(s):\n")

        for comm_addr, info in sorted(slaves.items()):
            print(f"Slave Inverter #{comm_addr}:")
            print(f"  Serial Number:     {info['serial_number']}")
            print(f"  Modbus Comm Addr:  {info['comm_addr']}")
            print(f"  Role:              {info['role']}")
            print(f"  Sensor Prefix:     {info['sensor_prefix']}")
            print()

        # Summary
        total_inverters = 1 + len(slaves)  # master + slaves
        print(f"{'='*60}")
        print(f"Summary:")
        print(f"  Total Inverters:   {total_inverters}")
        print(f"  Master:            {master.serial_number} ({master.sensor_name_prefix})")
        for comm_addr, info in sorted(slaves.items()):
            print(f"  Slave {comm_addr}:           {info['serial_number']} ({info['sensor_prefix']})")
        print(f"{'='*60}\n")

        # Integration guidance
        print("Home Assistant Integration:")
        print("  Use sensor_prefix to distinguish entities:")
        print(f"    Master: {master.sensor_name_prefix}vpv1, {master.sensor_name_prefix}ppv1, ...")
        for comm_addr, info in sorted(slaves.items()):
            prefix = info['sensor_prefix']
            print(f"    Slave {comm_addr}: {prefix}vpv1, {prefix}ppv1, ...")
        print()

    except ValueError as e:
        print(f"✗ Discovery failed: {e}")
    except Exception as e:
        logger.exception("Unexpected error during discovery")
        print(f"✗ Unexpected error: {e}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python discover_parallel_system.py <master_ip> [comm_addr]")
        print("\nExample:")
        print("  python discover_parallel_system.py 10.10.20.91")
        print("  python discover_parallel_system.py 10.10.20.91 247")
        sys.exit(1)

    master_ip = sys.argv[1]
    master_comm_addr = int(sys.argv[2]) if len(sys.argv) > 2 else 247

    asyncio.run(discover_system(master_ip, master_comm_addr))


if __name__ == '__main__':
    main()
