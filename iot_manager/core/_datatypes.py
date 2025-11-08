"""
_device_buffer.py
07. November 2025

-----------------------

Author:
Nilusink
"""
from dataclasses import dataclass
import typing as tp


@dataclass(frozen=True)
class IOTDevice:
    id: int
    address: tuple[str, int]
    endpoints: tp.Iterable[str]  # e.g. ["/weather", "/brightness"], ["/"]
