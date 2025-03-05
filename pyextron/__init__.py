import asyncio
import logging
import re

from asyncio.exceptions import TimeoutError
from enum import Enum

from pytelnetdevice import TelnetDevice

logger = logging.getLogger(__name__)
error_regexp = re.compile("E[0-9]{2}")


class DeviceType(Enum):
    SURROUND_SOUND_PROCESSOR = "surround_sound_processor"
    HDMI_SWITCHER = "hdmi_switcher"
    UNKNOWN = "unknown"


class AuthenticationError(Exception):
    pass


class ResponseError(Exception):
    pass


def is_error_response(response: str) -> bool:
    return error_regexp.match(response) is not None


class ExtronDevice(TelnetDevice):
    def __init__(self, host: str, port: int, password: str) -> None:
        super().__init__(host, port)
        self._password = password

    async def after_connect(self):
        try:
            await asyncio.wait_for(self.attempt_login(), timeout=5)
            logger.info(f"Connected and authenticated to {self._host}:{self._port}")
        except TimeoutError:
            raise AuthenticationError()

    async def attempt_login(self):
        async with self._semaphore:
            await self._read_until("Password:")
            self._writer.write(f"{self._password}\r".encode())
            await self._writer.drain()
            await self._read_until("Login Administrator\r\n")

    async def _run_command_internal(self, command: str) -> str | None:
        async with self._semaphore:
            self._writer.write(f"{command}\n".encode())
            await self._writer.drain()

            return await self._read_until("\r\n")

    async def run_command(self, command: str) -> str:
        try:
            logger.debug(f"Sending command: {command}")
            response = await asyncio.wait_for(
                self._run_command_internal(command), timeout=3
            )

            if response is None:
                raise RuntimeError("Command failed, got no response")

            response = response.strip()
            logger.debug(f"Received response: {response}")

            if is_error_response(response):
                raise ResponseError(f"Command failed with error code {response}")

            return response
        except TimeoutError:
            raise RuntimeError("Command timed out")
        except (ConnectionResetError, BrokenPipeError):
            await self.disconnect()
            raise RuntimeError("Connection was reset")
        finally:
            if not self.is_connected():
                logger.warning(
                    "Connection seems to be broken, will attempt to reconnect"
                )
                await self.reconnect()

    async def query_model_name(self) -> str:
        return await self.run_command("1I")

    async def query_model_description(self) -> str:
        return await self.run_command("2I")

    async def query_firmware_version(self) -> str:
        return await self.run_command("Q")

    async def query_part_number(self) -> str:
        return await self.run_command("N")

    async def query_mac_address(self) -> str:
        return await self.run_command("\x1b" + "CH")

    async def query_ip_address(self) -> str:
        return await self.run_command("\x1b" + "CI")

    async def reboot(self) -> None:
        await self.run_command("\x1b" + "1BOOT")


class SurroundSoundProcessor:
    def __init__(self, device: ExtronDevice) -> None:
        self._device = device

    def get_device(self) -> ExtronDevice:
        return self._device

    async def view_input(self) -> int:
        return int(await self._device.run_command("$"))

    async def select_input(self, input: int):
        await self._device.run_command(f"{str(input)}$")

    async def mute(self):
        await self._device.run_command("1Z")

    async def unmute(self):
        await self._device.run_command("0Z")

    async def is_muted(self) -> bool:
        is_muted = await self._device.run_command("Z")
        return is_muted == "1"

    async def get_volume_level(self):
        volume = await self._device.run_command("V")
        return int(volume)

    async def set_volume_level(self, level: int):
        await self._device.run_command(f"{level}V")

    async def increment_volume(self):
        await self._device.run_command("+V")

    async def decrement_volume(self):
        await self._device.run_command("-V")

    async def get_temperature(self) -> int:
        temperature = await self._device.run_command("\x1b" + "20STAT")
        return int(temperature)


class HDMISwitcher:
    def __init__(self, device: ExtronDevice) -> None:
        self._device = device

    def get_device(self) -> ExtronDevice:
        return self._device

    async def view_input(self) -> int:
        return int(await self._device.run_command("!"))

    async def select_input(self, input: int):
        await self._device.run_command(f"{str(input)}!")
