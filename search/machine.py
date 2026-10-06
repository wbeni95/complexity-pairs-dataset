"""Process priority and machine-load measurement (standard library only).

Search runs share the machine with other timing-sensitive work, so experiment scripts call
`set_below_normal_priority()` first and record the system-wide CPU utilisation during the run with `CpuMeter`.
"""
from __future__ import annotations

import ctypes
import os
import platform
import sys
import time


BELOW_NORMAL_PRIORITY_CLASS = 0x4000


def set_below_normal_priority() -> bool:
    """Windows: BELOW_NORMAL_PRIORITY_CLASS (0x4000), confirmed by reading it back. POSIX: nice +10.
    Returns True on success.

    Note: the untyped one-liner `kernel32.SetPriorityClass(kernel32.GetCurrentProcess(), 0x4000)` FAILS on
    64-bit CPython (returns 0, GetLastError() = 6, ERROR_INVALID_HANDLE): ctypes' default int return type
    truncates the pseudo-handle. The argument and return types must be declared, as below."""
    try:
        if sys.platform == "win32":
            from ctypes import wintypes
            k = ctypes.WinDLL("kernel32", use_last_error=True)
            k.GetCurrentProcess.restype = wintypes.HANDLE
            k.SetPriorityClass.argtypes = [wintypes.HANDLE, wintypes.DWORD]
            k.SetPriorityClass.restype = wintypes.BOOL
            k.GetPriorityClass.argtypes = [wintypes.HANDLE]
            k.GetPriorityClass.restype = wintypes.DWORD
            h = k.GetCurrentProcess()
            return bool(k.SetPriorityClass(h, BELOW_NORMAL_PRIORITY_CLASS)) and \
                k.GetPriorityClass(h) == BELOW_NORMAL_PRIORITY_CLASS
        os.nice(10)
        return True
    except Exception:
        return False


class _FILETIME(ctypes.Structure):
    _fields_ = [("lo", ctypes.c_uint32), ("hi", ctypes.c_uint32)]


def _system_times():
    """(busy, total) CPU time counters summed over all logical CPUs, or None if unavailable."""
    if sys.platform == "win32":
        idle, kernel, user = _FILETIME(), _FILETIME(), _FILETIME()
        k = ctypes.WinDLL("kernel32")
        k.GetSystemTimes.argtypes = [ctypes.POINTER(_FILETIME)] * 3
        k.GetSystemTimes.restype = ctypes.c_int
        if not k.GetSystemTimes(ctypes.byref(idle), ctypes.byref(kernel), ctypes.byref(user)):
            return None
        val = lambda ft: (ft.hi << 32) | ft.lo  # noqa: E731
        i, k, u = val(idle), val(kernel), val(user)   # kernel time includes idle time
        return (k + u - i, k + u)
    try:
        with open("/proc/stat") as f:
            parts = [int(x) for x in f.readline().split()[1:]]
        idle = parts[3] + (parts[4] if len(parts) > 4 else 0)
        return (sum(parts) - idle, sum(parts))
    except OSError:
        return None


class CpuMeter:
    """System-wide CPU utilisation (all logical CPUs, 0..1) and this process's CPU time between start and stop."""

    def start(self):
        self.t0 = time.perf_counter()
        self.p0 = time.process_time()
        self.s0 = _system_times()
        return self

    def stop(self) -> dict:
        wall = time.perf_counter() - self.t0
        cpu = time.process_time() - self.p0
        s1 = _system_times()
        util = None
        if self.s0 and s1 and s1[1] > self.s0[1]:
            util = (s1[0] - self.s0[0]) / (s1[1] - self.s0[1])
        return {
            "wall_seconds": round(wall, 3),
            "process_cpu_seconds": round(cpu, 3),
            "system_cpu_utilisation": None if util is None else round(util, 4),
            "logical_cpus": os.cpu_count(),
        }


def environment() -> dict:
    return {
        "python": platform.python_version(),
        "implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "logical_cpus": os.cpu_count(),
    }
