"""
_device_buffer.py
07. November 2025

Periodically requests data from an IOT sensor (e.g. Environment sensor)
and acts as a "relay" so subscribers can request data from one central
host and to remove stress from small ics

Author:
Nilusink
"""
from concurrent.futures import ThreadPoolExecutor, Future
from http import HTTPStatus

from fastapi import FastAPI, HTTPException
from copy import copy
import typing as tp
import uvicorn
import requests
import time

from ..utils.debugging import debugger  # , DebugLevel  # , run_with_debug
from ._datatypes import IOTDevice


class _DeviceParams(tp.TypedDict):
    device: IOTDevice
    interval: float
    last_update: float
    last_data: dict[str, dict]


class DeviceBuffer:
    _clients: dict[int, _DeviceParams]
    _current_client_id = 0

    def __init__(
            self,
            address: tuple[str, int] = ("0.0.0.0", 12345),
    ) -> None:
        debugger.trace("dev_buf: initializing...")

        # param handling
        self._address = copy(address)

        # variable setup
        self._clients = {}
        self.__running = True

        # threading
        self._pool = ThreadPoolExecutor(max_workers=8)

        # webserver setup
        self._app = FastAPI()

        # register endpoints
        self._setup_routes()

        # start background threads
        self._pool.submit(self._device_requester)

        debugger.log("dev_buf: initialized")

    def _setup_routes(self):
        @self._app.get("/device/{device_id}/{endpoint:path}")
        async def get_device(device_id: int, endpoint: str) -> dict:
            """
            forwards device requests

            :param device_id: device request id
            :param endpoint: normal device endpoint
            """
            endpoint = '/' + endpoint.strip().rstrip("/")
            debugger.trace(f"dev_buf: getting device {device_id}, \"{endpoint}\"")

            data = self.get_device_data(device_id, endpoint)

            if data == -1:
                debugger.info("dev_buf: invalid endpoint")
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND,
                )

            elif data is ...:
                debugger.info("dev_buf: no data")
                raise HTTPException(
                    status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                )

            return data

    def _device_requester(self) -> None:
        """
        background task, handles the device requests
        """
        debugger.trace("dev_buf: starting device requester")

        while self.__running:
            now = time.time()
            for did, device in self._clients.items():

                # check if device data needs to be updated
                if (now - device["last_update"]) > device["interval"]:
                    self._update_device(did, True)
                    device["last_update"] = time.time()

        debugger.trace("dev_buf: device requester stopped")

    # @run_with_debug(
    #     show_call=True,
    #     show_finish=True,
    #     reraise_errors=True,
    # )
    def _update_device(
            self,
            device_id: int,
            background: bool = True
    ) -> None | Future:
        """
        update a devices data

        :param device_id: device to update
        :param background: starts thread if true
        """
        if background:
            return self._pool.submit(self._update_device, device_id, False)

        # request data from given address
        device = self._clients[device_id]
        debugger.trace(
            f"dev_buf: updating device {device_id} at "
            f"{device['device'].address}"
        )

        for endpoint in device["device"].endpoints:
            debugger.trace(
                f"dev_buf: requesting http://{device['device'].address[0]}:"
                f"{device['device'].address[1]}{endpoint}"
            )
            # request single endpoint and save to buffer
            try:
                data = requests.get(
                    f"http://{device['device'].address[0]}:"
                    f"{device['device'].address[1]}{endpoint}",
                    timeout=min(device["interval"] / 2, 5)
                ).json()

            except (
                    TimeoutError,
                    requests.ReadTimeout,
                    requests.ConnectTimeout,
                    requests.ConnectionError
            ):
                debugger.log(
                    f"dev_buf: failed to get data form "
                    f"{device['device'].address}"
                )
                continue

            device["last_data"][endpoint] = data

            debugger.trace(
                f"dev_buf: updated device {device_id} at \"{endpoint}\": {data}"
            )

    def add_device(self, device: IOTDevice, interval_s: float) -> int:
        """
        add an IOT device to the request list

        :param device: IOT device to add
        :param interval_s: interval in seconds between device requests
        :returns: client id
       """
        cid = device.id

        debugger.log(f"dev_buf: adding device {cid} at {device.address}")

        self._clients[cid] = {
            "device": device,
            "interval": interval_s,
            "last_update": 0,
            "last_data": {ep: ... for ep in device.endpoints},
        }

        return cid

    def remove_device(self, device_id: int) -> bool:
        """
        remove an IOT device from the request list

        :param device_id: device to remove
        :return: success
        """
        debugger.log(f"dev_buf: removing device {device_id}")
        if device_id in self._clients:
            self._clients.pop(device_id)
            return True

        return False

    def get_device_data(self, device_id: int, endpoint: str) -> dict | int:
        """
        return the data of the given device and endpoint
        """
        if endpoint not in self._clients[device_id]["last_data"]:
            return -1

        return self._clients[device_id]["last_data"][endpoint]

    async def serve(self):
        """Run this buffer as its own FastAPI server."""
        config = uvicorn.Config(
            self._app,
            host=self._address[0],
            port=self._address[1],
            log_level="warning"
            # log_level={
            #     # DebugLevel.error: "error",
            #     # DebugLevel.warning: "warning",
            #     # DebugLevel.info: "info",
            #     # DebugLevel.log: "debug",
            #     # DebugLevel.trace: "trace"
            # }[debugger.debug_level]
        )
        server = uvicorn.Server(config)
        await server.serve()

    def shutdown(self) -> None:
        debugger.trace("dev_buf: shutdown called")

        if not self.__running:
            debugger.trace("dev_buf: already shutdown...")
            return

        # shutdown threads
        self.__running = False

        debugger.trace("dev_buf: waiting for threads ...")
        self._pool.shutdown(wait=True)

        debugger.log("dev_buf: shutdown")

    def __del__(self):
        debugger.trace("dev_buf: __del__ called")
        self.shutdown()
