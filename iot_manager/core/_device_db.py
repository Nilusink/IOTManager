"""
Device database interface.

| ``Path``: iot_manager/core/_device_db.py
| ``Project``: IOTManager
| ``Created``: 10.06.2026
| ``Authors``: Nilusink
"""

import ipaddress
import sqlite3
import typing as tp
from dataclasses import dataclass
from enum import Enum
from os import PathLike
from types import EllipsisType

DEFAULT_TABLES: tp.Final[list[str]] = [
    """CREATE TABLE IF NOT EXISTS device_data
(
    id   integer not null
        constraint table_name_pk
            primary key autoincrement,
    ip   integer not null,
    port integer not null
)""",
    """CREATE TABLE IF NOT EXISTS endpoints
(
    eid  integer not null
        constraint eid_pk
            primary key autoincrement,
    name text    not null,
    type integer not null,
    did  integer not null
        constraint endpoints_device_data_id_fk
            references device_data
)""",
]


class EndpointType(Enum):
    """Specify endpoint type."""

    GET = 0
    POST = 1
    PUT = 2


@dataclass(frozen=True)
class Device:
    """Device data."""

    id: int
    ip: ipaddress.IPv4Address
    port: int
    endpoints: list[tuple[str, EndpointType]]


class DeviceDB:
    """
    Device database interface.

    :cvar _default_path: default database path

    :ivar _conn: sqlite3 connection
    """

    # region ClassVars
    _default_path: tp.ClassVar[str] = "./devices.db"
    # endregion

    # region InstanceVars
    _conn: sqlite3.Connection
    # endregion

    def __init__(self, path: PathLike | EllipsisType = ...) -> None:
        if isinstance(path, EllipsisType):
            path_ = self._default_path

        else:
            path_ = path

        self._conn = sqlite3.connect(path_)

    def __check_create(self) -> None:
        """Check if all tables exist, if not, create them."""
        cursor = self._conn.cursor()

        # iterate default tables
        for table in DEFAULT_TABLES:
            cursor.execute(table)

        # apply changes
        self._conn.commit()
        cursor.close()

    def get_devices(self) -> list[Device]:
        """Get all devices."""
        cursor = self._conn.cursor()

        # get all devices
        cursor.execute("SELECT id, ip, port FROM device_data;")

        # create devices
        out = []
        for device in cursor.fetchall():
            # get endpoints and convert to device
            out.append(
                Device(
                    id=device[0],
                    ip=ipaddress.IPv4Address(device[1]),
                    port=device[2],
                    endpoints=self.get_endpoints(device[0]),
                )
            )

        cursor.close()
        return out

    def get_device(self, device_id: int) -> Device:
        """Get a single device."""
        cursor = self._conn.cursor()

        # get device data
        cursor.execute(
            "SELECT id, ip, port FROM device_data where id = ?",
            (device_id,),
        )

        # fetch data
        data = cursor.fetchone()
        cursor.close()

        # convert to device
        return Device(
            id=data[0],
            ip=ipaddress.IPv4Address(data[1]),
            port=data[2],
            endpoints=self.get_endpoints(data[0]),
        )

    def get_endpoints(self, device_id: int) -> list[tuple[str, EndpointType]]:
        """Get all endpoints for a device."""
        cursor = self._conn.cursor()

        # query search
        cursor.execute(
            "SELECT name, type from endpoints where did = ?",
            (device_id,),
        )

        # get results
        endpoints = cursor.fetchall()
        cursor.close()

        return [(e[0], EndpointType(e[1])) for e in endpoints]

    def register_device(
        self,
        ip: ipaddress.IPv4Address,
        port: int,
        endpoints: list[tuple[str, EndpointType]],
        device_id: int | None = None,
    ) -> int:
        """
        Register a new device.

        :param device_id: id of new device, if none, it will auto-increment
        :param ip: ip address of new device
        :param port: port of new device
        :param endpoints: endpoints of new device
        :return: id of new device, else: -1: id conflict, -2: ip conflict,
            -3: create failure
        """
        cursor = self._conn.cursor()

        # check if device already exists
        cursor.execute(
            "SELECT * FROM device_data WHERE id = ?",
            (device_id,),
        )
        if cursor.fetchone() is not None:
            return -1

        # check if IP already exists
        ip_: int = int(ip)
        cursor.execute(
            "SELECT id FROM device_data WHERE ip = ?",
            (ip_,),
        )
        if cursor.fetchone() is not None:
            return -2

        # device doesn't exist, create it
        if device_id is None:
            cursor.execute(
                "INSERT INTO device_data (ip, port) VALUES (?, ?)",
                (ip_, port),
            )
            self._conn.commit()

            # get id of new device
            did: int = cursor.lastrowid or -3

            if did < 0:
                cursor.close()
                return did

        else:
            cursor.execute(
                "INSERT INTO device_data (id, ip, port) VALUES (?, ?, ?)",
                (device_id, ip_, port),
            )
            did: int = device_id

        # create endpoints
        for endpoint in endpoints:
            cursor.execute(
                "INSERT INTO endpoints (did, name, type) VALUES (?, ?, ?)",
                (did, endpoint[0], endpoint[1].value),
            )

        # commit changes
        self._conn.commit()
        cursor.close()

        return did


if __name__ == "__main__":
    db = DeviceDB()
    print(db.get_devices())
    # print(
    #     db.register_device(
    #         "192.168.68.15",
    #         80,
    #         [("weather", EndpointType.GET), ("blink", EndpointType.POST)],
    #     )
    # )
