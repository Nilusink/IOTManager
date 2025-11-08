"""
_device_manager.py
08. November 2025

manages devices (surprise)

Author:
Nilusink
"""
from copy import copy
import typing as tp

from ._datatypes import IOTDevice


# TODO: replace with proper database!
DEVICE_DATA: dict[int, IOTDevice] = {
    0: IOTDevice(0, ("192.168.68.10", 80), ("/weather", "/brightness")),
    1: IOTDevice(1, ("192.168.68.11", 80), ("/weather", "/brightness")),
    2: IOTDevice(1, ("192.168.68.12", 80), ("/weather", "/brightness")),
    3: IOTDevice(1, ("192.168.68.13", 80), ("/weather", "/brightness"))
}


class DeviceManager:
    def __init__(self) -> None:
        self._device_data = DEVICE_DATA

    def get_device(self, device_id: int) -> IOTDevice:
        """
        get device by its id

        :param device_id: target device id
        :return: iot device
        """
        if device_id not in self._device_data:
            raise ValueError("Device id not found")

        return self._device_data[device_id]

    def get_address(self, device_id: int) -> tuple[str, int]:
        """
        get a devices ip address (and port)

        :param device_id: target device id
        :return: (ip, port)
        """
        if device_id not in self._device_data:
            raise ValueError("Device id not found")

        return copy(self._device_data[device_id].address)

    def get_endpoints(self, device_id: int) -> tp.Iterable[str]:
        """
        get all available endpoints of a device

        :param device_id: the device id
        :return: list of device ids
        """
        if device_id not in self._device_data:
            raise ValueError("Device id not found")

        return copy(self._device_data[device_id].endpoints)

    def find_by_ip(self, device_ip: str) -> int:
        """
        find a devices' id by its address

        :param device_ip:
        :return: -1 if not found
        """
        for device in self._device_data.values():
            if device.address[0] == device_ip:
                return device.id

        return -1
