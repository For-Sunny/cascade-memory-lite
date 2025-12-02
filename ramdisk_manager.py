"""
RAM Disk Manager - Cross-Platform RAM Disk Setup for CASCADE Memory
"Fast Memory for the Masses"

Handles RAM disk creation and management on Windows and Linux.
No admin rights required for basic usage (uses existing RAM disks).

Windows: Uses ImDisk or existing RAM disk drive
Linux: Uses tmpfs mounts

Credits:
- Nova's RAM disk optimization idea
- Jason Glass & the Basement Revolution
- NOVA_MASTER project

Created: December 2025
"""

import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class RAMDiskManager:
    """
    Cross-platform RAM disk manager.

    Usage:
        manager = RAMDiskManager()

        # Check if RAM disk is available
        if manager.is_available():
            path = manager.get_path()
            print(f"RAM disk at: {path}")

        # Or auto-setup (may need admin on first run)
        path = manager.setup(size_mb=512)
    """

    def __init__(self, preferred_path: Optional[str] = None):
        """
        Initialize RAM disk manager.

        Args:
            preferred_path: Preferred RAM disk path (auto-detected if None)
        """
        self.system = platform.system().lower()
        self.preferred_path = preferred_path
        self._detected_path: Optional[Path] = None

    def is_available(self) -> bool:
        """Check if a RAM disk is available."""
        path = self.get_path()
        return path is not None and path.exists()

    def get_path(self) -> Optional[Path]:
        """
        Get the RAM disk path.

        Returns:
            Path to RAM disk, or None if not available
        """
        if self._detected_path and self._detected_path.exists():
            return self._detected_path

        # Check preferred path first
        if self.preferred_path:
            p = Path(self.preferred_path)
            if p.exists():
                self._detected_path = p
                return p

        # Auto-detect based on platform
        if self.system == "windows":
            return self._detect_windows_ramdisk()
        elif self.system == "linux":
            return self._detect_linux_ramdisk()
        else:
            logger.warning(f"Unsupported platform: {self.system}")
            return None

    def _detect_windows_ramdisk(self) -> Optional[Path]:
        """Detect existing RAM disk on Windows."""
        # Common RAM disk drive letters
        common_letters = ['R', 'Z', 'Y', 'X', 'T']

        for letter in common_letters:
            path = Path(f"{letter}:/")
            if path.exists():
                # Check if it's actually a RAM disk by checking drive type
                try:
                    import ctypes
                    drive_type = ctypes.windll.kernel32.GetDriveTypeW(f"{letter}:\\")
                    # 0=Unknown, 1=No root, 2=Removable, 3=Fixed, 4=Network, 5=CD, 6=RAMDisk
                    # RAM disks often show as Fixed (3) or Unknown (0)
                    if drive_type in [0, 3, 6]:
                        # Additional check: RAM disks are usually fast and small
                        self._detected_path = path
                        logger.info(f"Detected potential RAM disk: {path}")
                        return path
                except:
                    pass

        # Check for ImDisk virtual disks
        imdisk_paths = [
            Path("R:/"),
            Path(os.environ.get("RAMDISK", "R:/")),
        ]

        for path in imdisk_paths:
            if path.exists():
                self._detected_path = path
                return path

        return None

    def _detect_linux_ramdisk(self) -> Optional[Path]:
        """Detect existing RAM disk (tmpfs) on Linux."""
        # Common tmpfs mount points
        common_paths = [
            Path("/dev/shm"),           # Standard shared memory
            Path("/run/user") / str(os.getuid()),  # User runtime dir
            Path("/tmp"),               # Often tmpfs on modern systems
            Path("/run/cascade"),       # Custom mount point
        ]

        for path in common_paths:
            if path.exists():
                # Check if it's actually tmpfs
                try:
                    result = subprocess.run(
                        ["df", "-T", str(path)],
                        capture_output=True,
                        text=True
                    )
                    if "tmpfs" in result.stdout:
                        self._detected_path = path
                        logger.info(f"Detected tmpfs at: {path}")
                        return path
                except:
                    pass

        # /dev/shm almost always exists and is tmpfs
        if Path("/dev/shm").exists():
            self._detected_path = Path("/dev/shm")
            return self._detected_path

        return None

    def setup(self, size_mb: int = 512) -> Optional[Path]:
        """
        Setup a RAM disk (may require admin privileges).

        Args:
            size_mb: Size in megabytes

        Returns:
            Path to RAM disk, or None if setup failed
        """
        # First check if one already exists
        existing = self.get_path()
        if existing:
            logger.info(f"Using existing RAM disk: {existing}")
            return existing

        # Try to create one
        if self.system == "windows":
            return self._setup_windows_ramdisk(size_mb)
        elif self.system == "linux":
            return self._setup_linux_ramdisk(size_mb)
        else:
            logger.error(f"Cannot setup RAM disk on {self.system}")
            return None

    def _setup_windows_ramdisk(self, size_mb: int) -> Optional[Path]:
        """
        Setup RAM disk on Windows using ImDisk.

        Requires ImDisk to be installed: https://sourceforge.net/projects/imdisk-toolkit/
        """
        # Check if ImDisk is available
        imdisk_path = shutil.which("imdisk")

        if not imdisk_path:
            # Check common install locations
            common_paths = [
                r"C:\Windows\System32\imdisk.exe",
                r"C:\Program Files\ImDisk\imdisk.exe",
            ]
            for p in common_paths:
                if Path(p).exists():
                    imdisk_path = p
                    break

        if not imdisk_path:
            logger.error(
                "ImDisk not found. Install from: https://sourceforge.net/projects/imdisk-toolkit/\n"
                "Or manually create a RAM disk and set RAMDISK environment variable."
            )
            return None

        # Create RAM disk on R: drive
        drive_letter = "R"
        size_bytes = size_mb * 1024 * 1024

        try:
            # Remove existing if present
            subprocess.run(
                [imdisk_path, "-D", "-m", f"{drive_letter}:"],
                capture_output=True
            )

            # Create new RAM disk
            result = subprocess.run(
                [imdisk_path, "-a", "-s", str(size_bytes), "-m", f"{drive_letter}:", "-p", "/fs:ntfs /q /y"],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                path = Path(f"{drive_letter}:/")
                self._detected_path = path
                logger.info(f"Created RAM disk: {path} ({size_mb}MB)")
                return path
            else:
                logger.error(f"ImDisk failed: {result.stderr}")
                return None

        except Exception as e:
            logger.error(f"Failed to create Windows RAM disk: {e}")
            return None

    def _setup_linux_ramdisk(self, size_mb: int) -> Optional[Path]:
        """Setup RAM disk on Linux using tmpfs."""
        mount_point = Path("/run/cascade")

        try:
            # Create mount point
            mount_point.mkdir(parents=True, exist_ok=True)

            # Mount tmpfs (requires sudo)
            result = subprocess.run(
                ["sudo", "mount", "-t", "tmpfs", "-o", f"size={size_mb}M", "tmpfs", str(mount_point)],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                # Set permissions
                subprocess.run(["sudo", "chmod", "777", str(mount_point)])
                self._detected_path = mount_point
                logger.info(f"Created RAM disk: {mount_point} ({size_mb}MB)")
                return mount_point
            else:
                logger.error(f"Mount failed: {result.stderr}")
                # Fall back to /dev/shm
                fallback = Path("/dev/shm/cascade")
                fallback.mkdir(exist_ok=True)
                self._detected_path = fallback
                logger.info(f"Using fallback: {fallback}")
                return fallback

        except Exception as e:
            logger.error(f"Failed to create Linux RAM disk: {e}")
            # Try /dev/shm fallback
            try:
                fallback = Path("/dev/shm/cascade")
                fallback.mkdir(exist_ok=True)
                self._detected_path = fallback
                return fallback
            except:
                return None

    def get_info(self) -> dict:
        """Get information about the RAM disk."""
        path = self.get_path()

        info = {
            "platform": self.system,
            "available": path is not None,
            "path": str(path) if path else None,
        }

        if path and path.exists():
            try:
                if self.system == "windows":
                    import ctypes
                    free_bytes = ctypes.c_ulonglong(0)
                    total_bytes = ctypes.c_ulonglong(0)
                    ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                        str(path),
                        None,
                        ctypes.pointer(total_bytes),
                        ctypes.pointer(free_bytes)
                    )
                    info["total_mb"] = total_bytes.value / (1024 * 1024)
                    info["free_mb"] = free_bytes.value / (1024 * 1024)
                else:
                    stat = os.statvfs(path)
                    info["total_mb"] = (stat.f_blocks * stat.f_frsize) / (1024 * 1024)
                    info["free_mb"] = (stat.f_bavail * stat.f_frsize) / (1024 * 1024)
            except:
                pass

        return info


def get_cascade_ramdisk_path(create_subdir: bool = True) -> Optional[Path]:
    """
    Convenience function to get RAM disk path for CASCADE.

    Args:
        create_subdir: Create 'cascade_memory' subdirectory

    Returns:
        Path ready for CASCADE Memory use
    """
    manager = RAMDiskManager()
    base_path = manager.get_path()

    if not base_path:
        return None

    if create_subdir:
        cascade_path = base_path / "cascade_memory"
        cascade_path.mkdir(exist_ok=True)
        return cascade_path

    return base_path


# CLI interface
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    print("RAM Disk Manager - CASCADE Memory Lite")
    print("=" * 50)

    manager = RAMDiskManager()
    info = manager.get_info()

    print(f"Platform: {info['platform']}")
    print(f"RAM disk available: {info['available']}")

    if info['available']:
        print(f"Path: {info['path']}")
        if 'total_mb' in info:
            print(f"Total: {info['total_mb']:.0f} MB")
            print(f"Free: {info['free_mb']:.0f} MB")
    else:
        print("\nNo RAM disk detected.")
        print("\nTo create one:")

        if info['platform'] == 'windows':
            print("  1. Install ImDisk: https://sourceforge.net/projects/imdisk-toolkit/")
            print("  2. Run: imdisk -a -s 512M -m R: -p \"/fs:ntfs /q /y\"")
            print("  Or use RAMDisk software like SoftPerfect RAM Disk")
        else:
            print("  1. Run: sudo mount -t tmpfs -o size=512M tmpfs /run/cascade")
            print("  2. Or use /dev/shm (usually already available)")

        print("\nOr set RAMDISK environment variable to your RAM disk path.")

    # Show CASCADE-ready path
    cascade_path = get_cascade_ramdisk_path()
    if cascade_path:
        print(f"\nCASCADE Memory path: {cascade_path}")
