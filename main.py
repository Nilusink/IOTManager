from iot_manager.utils.debugging import debugger, DebugLevel
from iot_manager.core import DeviceBuffer, IOTDevice
from time import perf_counter
from icecream import ic
# from time import sleep
import asyncio


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

    # manager setup
    dev_buf = DeviceBuffer()
    dev_buf.add_device(IOTDevice(
        0,
        ("192.168.68.10", 80),
        ["/weather", "/brightness"]
    ), 2)

    try:
        await asyncio.gather(dev_buf.serve())

    except KeyboardInterrupt:
        dev_buf.shutdown()


if __name__ == '__main__':
    asyncio.run(main())
