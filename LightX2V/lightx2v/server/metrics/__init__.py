# -*-coding=utf-8-*-  

from .metrics import server_process
from .monitor import Monitor

# Use lazy initialization to prevent duplicate registrations in multiprocess environments
_monitor_cli_instance = None

def get_monitor_cli():
    """Get the monitor CLI instance (lazy initialization)."""
    global _monitor_cli_instance
    if _monitor_cli_instance is None:
        _monitor_cli_instance = Monitor()
    return _monitor_cli_instance

# For backward compatibility, provide the instance directly
monitor_cli = get_monitor_cli()
