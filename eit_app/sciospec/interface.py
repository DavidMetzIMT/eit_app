#!C:\Anaconda3\envs\py38_app python
# -*- coding: utf-8 -*-
"""  Class for the communication with serial port of the Sciospec device
    
    code modify from:
    #  HW_Thread.py
    #  Classes for communication with asynchronous hardware
    #  written by Jonathan Foote jtf@rotormind.com 3/2013
    #  Updated for Python 3.6 by Jonathan Foote  3/2019
    #
    #  Works with example Arduino code from 
    #  https://github.com/headrotor/Python-Arduino-example
    #  Share & enjoy!
    #
    # -----------------------------------------------------------------------------
    #
    # This program is free software; you can redistribute it and/or modify
    # it under the terms of the GNU General Public License as  as published 
    # by the Free Software Foundation http://www.gnu.org/licenses/gpl-2.0.html
    # This program is distributed WITHOUT ANY WARRANTY use at your own risk blah blah

Copyright (C) 2021  David Metz

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>. """


from __future__ import print_function
import contextlib
from abc import ABC, abstractmethod

from glob import glob
import logging
import sys
from time import sleep
from typing import Union, Any

from serial import (
    Serial,
    SerialException,
    PortNotOpenError,
)  # get from http://pyserial.sourceforge.net/
from eit_app.sciospec.constants import *
from glob_utils.thread_process.threads_worker import Poller
from glob_utils.thread_process.signal import Signal
from glob_utils.flags.flag import CustomFlag

logger = logging.getLogger(__name__)

SER_TIMEOUT = 0.1
SERIAL_BAUD_RATE_DEFAULT = 115200
HARDWARE_NOT_DETECTED = 0xFF

SUCCESS = {True: "SUCCESS", False: "FAIL"}

# ===============================================================================
#     Serial Interface Error (Obslete)
# ===============================================================================


class SerialInterfaceError(Exception):
    """Custom Error for serial interface"""

    def __init__(self, port: Serial, msg) -> None:
        super().__init__(msg)
        self.port = port


# ===============================================================================
#     Interface Abstract Class
# ===============================================================================


class Interface(ABC):
    """"""

    new_rx_frame: Signal  # Signal used to transmit new rx frame
    error: Signal  # Signal used to transmit error occruring during opening, writing, or listening process
    is_connected: CustomFlag

    def __init__(
        self, name_listener_thread: str = "listener", sleeptime: float = 0.01
    ) -> None:
        super().__init__()

        self.new_rx_frame = Signal(self)
        self.error = Signal(self)
        self.is_connected = CustomFlag()
        self.is_connected.clear()

        self.listener = Poller(
            name=name_listener_thread, sleeptime=sleeptime, pollfunc=self._poll
        )
        self.listener.start()

    def _poll(self):
        self.listen()

    def listening_activate(self, activate: bool = True):
        """Activate/Deactivate the polling"""
        if activate:
            self.listener.start_polling()
        else:
            self.listener.stop_polling()

    @abstractmethod
    def open(self) -> bool:
        """Open the interface, if successful return `True`"""

    @abstractmethod
    def close(self):
        """Close serial interface
        don't forget to stop the listener with self.listener.stop_polling()"""

    @abstractmethod
    def write(self, data) -> bool:
        """Write data to port, if successful return `True`"""

    @abstractmethod
    def listen(self):
        """Method called by the listener

        here come the code to read the port or wahtever you want to listen"""


# ===============================================================================
#     Sciospec Serial (USB) Interface Class
# ===============================================================================


class SciospecSerialInterface(Interface):
    """Class to interface with the serial port of Sciospec Device.

    Repeatedly polls hardware, unless we are sending a command
    "Ser" is a serial port class from the pyserial pacakge"""

    def __init__(self) -> None:
        """Constructor responsible of attrs init and starting the HW Poller(thread)"""
        super().__init__(name_listener_thread="serial listener", sleeptime=0.01)
        self.rx_frame = None  # last response retrieved by polling
        self.serial_port = Serial()
        self.is_connected.set(self.serial_port.is_open)
        self.ports_available = []
        logger.debug("__init__ SerialInterface - done")

    # @abstractmethod
    def open(self, port: str = None, baudrate: int = None, **kwargs) -> bool:
        """Open the interface, if successful return `True`

        Args:
            port (str): serial port e.g. "COM1"
            baudrate (int, optional): Defaults to SERIAL_BAUD_RATE_DEFAULT.
            kwargs see SerialBase
        """
        if baudrate is None:
            baudrate = SERIAL_BAUD_RATE_DEFAULT
        success = self._open(port=port, baudrate=str(baudrate), **kwargs)
        self.is_connected.set(self.serial_port.is_open)
        logger.debug(f"Opening serial port: {port} - {SUCCESS[success]}")
        self.listener.start_polling()
        return success

    # @abstractmethod
    def close(self) -> bool:
        """Close serial interface"""
        self.listener.stop_polling()
        port = self.get_port_name()
        success = self._close()
        self.is_connected.set(self.serial_port.is_open)
        logger.debug(f"Closing serial port: {port} - {SUCCESS[success]}")
        return success

    # @abstractmethod
    def write(self, data: list[bytes]) -> bool:
        """Write data to serial port, if successful return `True`"""
        return self._write(data)

    # @abstractmethod
    def listen(self):
        """Listen the serial port"""
        self.rx_frame = self._get_rx_frame()
        if self.rx_frame is None:
            return
        kwargs = {"rx_frame": self.rx_frame}
        self.new_rx_frame.emit(**kwargs)

    def _catch_error(return_result: bool = False, return_success: bool = False):
        """_summary_

        Args:
            return_result (bool, optional): if true return the result of the func. if an error occur it return None. Defaults to False.
            return_success (bool, optional): if True return if the fucn could be susselly or not run. Defaults to False.
        """

        def _fire_error(func):
            def wrap(self, *args, **kwargs) -> Union[bool, Any, None]:

                success = False
                result = None
                try:
                    result = func(self, *args, **kwargs)
                    success = True
                except SerialException as error:
                    if "Der E/A-Vorgang" in error.__str__():
                        self.close()
                    if "PermissionError(13" in error.__str__():
                        self.close()
                    kwargs = {"error": error}
                    self.error.emit(**kwargs)
                    # logger.debug(traceback.format_exc())
                except PortNotOpenError as error:
                    kwargs = {"error": error}
                    self.error.emit(**kwargs)
                    # logger.debug(traceback.format_exc())
                except OSError as error:
                    kwargs = {"error": error}
                    self.error.emit(**kwargs)
                    # logger.debug(traceback.format_exc())

                if return_result:
                    return result
                if return_success:
                    return success

            return wrap

        return _fire_error

    def reinit(self):
        """Reinit the interface"""
        self.ports_available = []
        self.rx_frame = None
        logger.debug("Reinitialisation of SciospecSerialInterface - DONE")

    def get_port_name(self):
        return self.serial_port.name or "None"

    def get_baudrate(self):
        return self.serial_port.baudrate or "None"

    def set_port_name(self, port_name: str = None):
        self.serial_port.name = port_name

    def set_baudrate(self, baudrate: int = SERIAL_BAUD_RATE_DEFAULT):
        self.serial_port.baudrate = baudrate

    def get_ports_available(self) -> list[str]:
        """Lists all serial port availabel on the system

        Raises:
            EnvironmentError: raised for unsupported or unknown platforms

        Returns:
            list[str]: A list of the serial ports available on the system
        """
        if sys.platform.startswith("win"):
            ports = [f"COM{i + 1}" for i in range(256)]
        elif sys.platform.startswith("linux") or sys.platform.startswith("cygwin"):
            # this excludes your current terminal "/dev/tty"
            ports = glob("/dev/tty[A-Za-z]*")
        elif sys.platform.startswith("darwin"):
            ports = glob("/dev/tty.*")
        else:
            raise EnvironmentError("Unsupported platform")

        actual_ports = []
        for port in ports:
            if "Bluetooth" in port:
                logger.debug(f"Port: {port} -deleted")
                continue
            with contextlib.suppress(OSError, SerialException):
                ser = Serial(port, str(SERIAL_BAUD_RATE_DEFAULT), timeout=None)
                actual_ports.append(port)
                ser.close()
        self.ports_available = actual_ports

        msg = f"Available serial ports : {self.ports_available}"
        logger.debug(msg)

        return self.ports_available

    def _clear_unwanted_rx_frames(self):
        """Clear recieved data by reading them

        Notes
        -----
        - Typically used after the opening a serial port and
        a stop-meas cmd, in case that the device was still sending meas. data"""

        # wait a while
        while self.read_nb_of_availables_bytes():
            sleep(0.5)
            logger.debug(f"clear: {self.serial_port.read_all()}")

    # def _stop_measurements(self):
    #     self.write([CMD_START_STOP_MEAS.tag, 0x01, 0x00, CMD_START_STOP_MEAS.tag])

    @_catch_error(return_success=True)
    def _open(self, **kwargs):
        self.serial_port = Serial(**kwargs)
        # read everything the device could send
        self.serial_port.reset_output_buffer()
        self.serial_port.reset_input_buffer()
        self.serial_port.flush()

    @_catch_error(return_success=True)
    def _close(self, **kwargs):
        self.serial_port.close()  # close the serial interface

    @_catch_error(return_success=True)
    def _write(self, data: list[bytes]):
        self.serial_port.write(bytearray(data))
        logger.debug(f"TX: {data}")
        self.serial_port.flush()

    def _get_rx_frame(self) -> Union[list[bytes], None]:
        """Return a complete data frame if available on the port

        Returns:
            Union[list[bytes], None]: complete data frame or
            None if not availbale or an error occurs
        """
        # a frame is at least 4 bytes
        n_bytes = self.read_nb_of_availables_bytes()
        if n_bytes is None or n_bytes < FRAME_LENGTH_MIN:
            return None
        # read up to the length byte
        rx_frame = self.read_bytes(LENGTH_BYTE_INDX + 1)
        if rx_frame is None:
            return None
        # read also the additional "ending CMD Byte"
        length_data2read = rx_frame[LENGTH_BYTE_INDX] + 1
        # dangerous ...timer use?
        while 1:
            n_bytes = self.read_nb_of_availables_bytes()
            if n_bytes is None:
                return None
            if not n_bytes < length_data2read:
                break

        tmp = self.read_bytes(length_data2read)
        if tmp is None:
            return None
        rx_frame.extend(tmp)
        logger.debug(f"RX: {rx_frame[:10]}")
        return rx_frame

    def read_nb_of_availables_bytes(self) -> Union[int, None]:
        """Return the number of bytes available on the input buffer of the
        serial port

        Returns:
            Union[int, None]: nb bytes or None if an error occur
        """
        return self._read_nb_of_availables_bytes()

    @_catch_error(return_result=True)
    def _read_nb_of_availables_bytes(self) -> int:
        # can raise a SerialException("ClearCommError failed ({!r})".format(ctypes.WinError()))
        return self.serial_port.in_waiting

    def read_bytes(self, nb_bytes: int = 1) -> Union[list[bytes], None]:
        """Read on serial port a number of bytes

        Args:
            nb_bytes (int, optional): number of bytes to read. Defaults to 1.

        Returns:
            Union[list[bytes], None]: list of read bytes or None if an error occur
        """
        return self._read_bytes(nb_bytes)

    @_catch_error(return_result=True)
    def _read_bytes(self, nb_bytes: int = 1) -> list[bytes]:
        # can raise a SerialException("ClearCommError failed ({!r})".format(ctypes.WinError()))
        # can raise a PortNotOpenError()
        return list(self.serial_port.read(nb_bytes))


if __name__ == "__main__":
    from glob_utils.log.log import main_log

    main_log()
    # s = SerialInterface()

    # # logger.debug("An INFO message from " + __name__)
    # # logger.debug("An INFO message from " + __name__)
    # # logger.error("An INFO message from " + __name__)
    # # logger.critical("An INFO message from " + __name__)
    # # logger.warning("An INFO message from " + __name__)
    # s.get_ports_available()
    # try:
    #     s.open_serial("COM3")
    # except SerialInterfaceError as e:
    #     print("handle not opened serial")
    # try:
    #     s.write([0xB4, 0x01, 0x01, 0xB4])
    # except SerialInterfaceError as e:
    #     print("handle not write serial")

    # sleep(0.1)

    # sleep(1)
    # s.close_serial()
    # exit()
    def print_e(**kwargs):
        print(f"{kwargs=}")

    s = SciospecSerialInterface()
    s.error.connect(print_e)
    s.new_rx_frame.connect(print_e)

    # logger.debug("An INFO message from " + __name__)
    # logger.debug("An INFO message from " + __name__)
    # logger.error("An INFO message from " + __name__)
    # logger.critical("An INFO message from " + __name__)
    # logger.warning("An INFO message from " + __name__)
    s.get_ports_available()
    print(s.write([0xB4, 0x01, 0x01, 0xB4]))
    print(s.open("COM4"))
    print(s.open("COM3"))
    print(s.write([209, 0, 209]))
    sleep(0.1)
    print(s.write([0xB4, 0x01, 0x01, 0xB4]))
    for _ in range(10):
        print("111111")
        sleep(0.1)

    print(s.write([0xB4, 0x01, 0x00, 0xB4]))
    for _ in range(10):
        print("111111")
        a = 2
        sleep(0.2)

    # try:
    #     s.open_serial("COM3")
    # except SerialInterfaceError as e:
    #     print("handle not opened serial")
    # try:
    #     s.write([0xB4, 0x01, 0x01, 0xB4])
    # except SerialInterfaceError as e:
    #     print("handle not write serial")

    # sleep(0.1)

    # sleep(1)
    # s.close_serial()
    # exit()
