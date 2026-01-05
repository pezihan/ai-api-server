#!/usr/bin/env python3
# Test script to simulate the exact import chain causing duplicate metrics

import sys
import os

# Add project root to path
sys.path.insert(0, '/Users/yinhua/Desktop/ai-api-server')

print("Testing metrics import chain...")

# This simulates the import path from utils/wan.py
try:
    # First import the metrics module
    from LightX2V.lightx2v.server.metrics import monitor_cli
    print("✓ Metrics module imported successfully")
    
    # Then import the runners that might be importing metrics
    from LightX2V.lightx2v.models.runners.default_runner import DefaultRunner
    print("✓ DefaultRunner imported successfully")
    
    from LightX2V.lightx2v.models.runners.wan.wan_runner import WanRunner
    print("✓ WanRunner imported successfully")
    
    from LightX2V.lightx2v.models.runners.wan.wan_distill_runner import WanDistillRunner
    print("✓ WanDistillRunner imported successfully")
    
    print("\n✓ All imports completed without duplicate metrics errors!")
    
    # Check that the same instance is being used everywhere
    from LightX2V.lightx2v.server.metrics import monitor_cli as cli1
    from LightX2V.lightx2v.models.runners.default_runner import get_monitor_cli as get_cli2
    from LightX2V.lightx2v.models.runners.wan.wan_runner import get_monitor_cli as get_cli3
    
    cli2 = get_cli2()
    cli3 = get_cli3()
    
    print(f"\nInstance check:")
    print(f"cli1 is cli2: {cli1 is cli2}")
    print(f"cli1 is cli3: {cli1 is cli3}")
    print(f"cli2 is cli3: {cli2 is cli3}")
    
    if cli1 is cli2 and cli1 is cli3:
        print("✓ All monitor_cli instances are the same!")
    else:
        print("✗ Different monitor_cli instances detected!")
        
    # Test if we can access a metric
    try:
        # This should not raise an error
        cli1.lightx2v_worker_request_count.inc()
        print("✓ Successfully incremented a metric!")
    except Exception as e:
        print(f"✗ Error accessing metric: {e}")
        import traceback
        traceback.print_exc()
        
except Exception as e:
    print(f"\n✗ Import chain failed: {e}")
    import traceback
    traceback.print_exc()
    
print("\nTesting complete!")