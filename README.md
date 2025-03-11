# pyextron

[![Linting](https://github.com/NitorCreations/pyextron/actions/workflows/ruff.yaml/badge.svg)](https://github.com/NitorCreations/pyextron/actions/workflows/ruff.yaml)
[![Tests](https://github.com/NitorCreations/pyextron/actions/workflows/unittest.yaml/badge.svg)](https://github.com/NitorCreations/pyextron/actions/workflows/unittest.yaml)

Library for communicating with [Extron](https://www.extron.com/) devices. Developed with the following devices in mind:

* SSP 200 surround sound processors
* SW HD 4K PLUS Series switchers

This library uses our [pytelnetdevice](https://github.com/NitorCreations/pytelnetdevice) library under the hood.

## Usage

```python
import asyncio
import logging

from pyextron import SurroundSoundProcessor, ExtronDevice, AuthenticationError

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
        logger.error(f"Wrong password entered")
    except Exception:
        logger.exception(f"An unknown exception occurred")

asyncio.run(main())
```

Assuming the specified password is correct, the above should output:

```
DEBUG:asyncio:Using selector: EpollSelector
DEBUG:pyextron:Device is asking for password, entering
DEBUG:pyextron:Connected and authenticated to 10.211.0.91:23
DEBUG:pyextron:Sending command: $
DEBUG:pyextron:Received response: 1
INFO:example:Input is 1
```

## License

GNU GENERAL PUBLIC LICENSE version 3
