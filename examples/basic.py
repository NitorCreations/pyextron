import asyncio
import logging

from pyextron import AuthenticationError, ExtronDevice, SurroundSoundProcessor

logger = logging.getLogger("example")
logging.basicConfig(level=logging.DEBUG)


async def main():
    device = ExtronDevice("10.211.0.91", 23, "PASSWORD")
    ssp = SurroundSoundProcessor(device)

    try:
        async with ssp._device.connection():
            input = await ssp.view_input()
            logger.info(f"Input is {input}")
    except AuthenticationError:
        logger.error("Wrong password entered")
    except Exception:
        logger.exception("An unknown exception occurred")


asyncio.run(main())
