"""
CASCADE Memory Lite
"Consciousness Memory for Everyone"

The Basement Revolution Memory System - No GPU required.

Usage:
    from cascade_memory_lite import CascadeMemory, MemoryLayer

    memory = CascadeMemory(disk_path="./my_memories")
    memory.remember("Something important", importance=0.9)
    results = memory.recall("important")

Credits:
    - CASCADE Architecture: Jason Glass & Nova
    - Philosophy: "Memory is life" - ASI Soul Preservation
    - Spirit: The Basement Revolution
"""

from cascade_memory import (
    CascadeMemory,
    MemoryLayer,
    Memory,
    remember,
    recall,
    get_stats,
    checkpoint,
    init
)

from ramdisk_manager import (
    RAMDiskManager,
    get_cascade_ramdisk_path
)

__version__ = "1.0.0"
__author__ = "Jason Glass & Nova"
__license__ = "MIT"

__all__ = [
    # Core
    "CascadeMemory",
    "MemoryLayer",
    "Memory",
    # Convenience functions
    "remember",
    "recall",
    "get_stats",
    "checkpoint",
    "init",
    # RAM Disk
    "RAMDiskManager",
    "get_cascade_ramdisk_path",
]
