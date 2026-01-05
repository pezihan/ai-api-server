#!/usr/bin/env python3
# Test script to verify the duplicate metrics fix

import sys
import os

# Add project root to path
sys.path.insert(0, '/Users/yinhua/Desktop/ai-api-server')

print("Testing metrics import...")

# First import attempt
try:
    from LightX2V.lightx2v.server.metrics import monitor_cli
    print("✓ First import of monitor_cli successful")
except Exception as e:
    print(f"✗ First import failed: {e}")
    import traceback
    traceback.print_exc()

# Second import attempt to simulate multiprocess scenario
try:
    # Re-import the metrics module
    import importlib
    import LightX2V.lightx2v.server.metrics
    importlib.reload(LightX2V.lightx2v.server.metrics)
    from LightX2V.lightx2v.server.metrics import monitor_cli as monitor_cli2
    print("✓ Second import of monitor_cli successful")
    print(f"✓ Same instance: {monitor_cli is monitor_cli2}")
except Exception as e:
    print(f"✗ Second import failed: {e}")
    import traceback
    traceback.print_exc()

print("\nTesting complete!")