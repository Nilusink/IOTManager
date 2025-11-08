from iot_manager.utils.debugging import debugger, DebugLevel
from iot_manager.core import HTTPServer, DeviceBuffer, IOTDevice, DeviceManager
from time import perf_counter
from icecream import ic
# from time import sleep
import asyncio
import signal
import sys

SIGNALS: list[signal.Signals]
if sys.platform == 'win32':
    SIGNALS = [signal.SIGINT, signal.SIGTERM]

else:
    SIGNALS = [signal.SIGINT, signal.SIGTERM, signal.SIGHUP, signal.SIGPIPE]


async def main() -> None:
    # debugging setup
    start = perf_counter()

    def time_since_start() -> str:
        """
        stylized time since game start
        gamestart being time since `mainloop` was called
        """
        t_ms = round(perf_counter() - start, 4)

        t1, t2 = str(t_ms).split(".")
        return f"{t1: >4}.{t2: <4} |> "

    ic.configureOutput(prefix=time_since_start)
    debugger.init(
        "./IOTManager.log",
        write_debug=True,
        debug_level=DebugLevel.log
    )

    # manager
    dev_man = DeviceManager()

    # buffer
    dev_buf = DeviceBuffer()
    dev_buf.add_device(IOTDevice(
        0,
        ("192.168.68.10", 80),
        ["/weather", "/brightness"]
    ), 2)

    # http server
    server = HTTPServer(
        dev_buf,
        dev_man,
        ("0.0.0.0", 12345)
    )

    # cleanup
    def cleanup(*_, **__) -> None:
        """
        correctly stops the program
        """
        debugger.log("main: stopping program ...")
        dev_buf.shutdown()
        debugger.info("main: IOTManager stopped")

    # register cleanup function for OS interrupts
    for s in SIGNALS:
        signal.signal(s, cleanup)

    debugger.info("main: IOTManager started")

    try:
        await asyncio.gather(server.serve())

    except KeyboardInterrupt:
        cleanup()


if __name__ == '__main__':
    asyncio.run(main())
