# #!C:\Anaconda3\envs\py38_app python
# # -*- coding: utf-8 -*-
# """  Class for the communication with serial port of the Sciospec device

#     code modify from:
#     #  HW_Thread.py
#     #  Classes for communication with asynchronous hardware
#     #  written by Jonathan Foote jtf@rotormind.com 3/2013
#     #  Updated for Python 3.6 by Jonathan Foote  3/2019
#     #
#     #  Works with example Arduino code from
#     #  https://github.com/headrotor/Python-Arduino-example
#     #  Share & enjoy!
#     #
#     # -----------------------------------------------------------------------------
#     #
#     # This program is free software; you can redistribute it and/or modify
#     # it under the terms of the GNU General Public License as  as published
#     # by the Free Software Foundation http://www.gnu.org/licenses/gpl-2.0.html
#     # This program is distributed WITHOUT ANY WARRANTY use at your own risk blah blah

# Copyright (C) 2021  David Metz

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>. """

# from __future__ import print_function
# from ast import Bytes

# import glob
# import logging
# import sys
# import time
# from typing import List

# import serial  # get from http://pyserial.sourceforge.net/
# from eit_app.io.sciospec.com_constants import *
# #from eit_app.io.sciospec.device import SciospecDevice
# from glob_utils.thread_process.threads_worker import HardwarePoller, Worker
# from glob_utils.log.log import main_log

# from abc import ABC, abstractmethod


# #This class has to be remodeled for a generic interface
# class HWInterface(ABC):
#     """ abstract class of HardWare Interfaces for setting the methods and there responsabilities"""

#     @abstractmethod
#     def get_ports_available(self)->List[str]:
#         """ Lists the ports available on the system"""

#     @abstractmethod
#     def open(self, port_name, baudrate, timeout, write_timeout):
#         """ Open interface

#         Raises:
#             serial.PortNotOpenError: [description]

#         Returns:
#             [type]: [description]
#         """

#     @abstractmethod
#     def close(self):
#         """ Close interface """


#     @abstractmethod
#     def register_callback(self, func=None):
#         """Register function (external function) to call
#         when the hardware sends a complete data frame

#         Args:
#             func: function, who . Defaults to None.
#         """

#     @abstractmethod
#     def no_callback(self, rx_frame:List[Bytes]=[]):
#         """[summary]

#         Args:
#             rx_frame (list, optional): [description]. Defaults to [].
#         """


#     @abstractmethod
#     def write(self, command:List[Bytes]):
#         """ Send a command to the hardware

#         Parameters
#         ----------
#         command: list of int8 (1 Byte) e.g. [0xD1, 0x00, 0xD1]

#         Notes
#         -----
#         if a SerialException is raised >> "ErrorSerialInterface" will be set to identify: disconnection of the device, etc."""

#     @abstractmethod
#     def poll_read(self):
#         """ Called repeatedly by thread (e.g. from GUI) for reading the serial port

#         when a complete frame has been recieved, it is tramsmitted to the registered function Callback

#         RXFrame:  - [cmd_byte, length_byte=0x01, option_byte, cmd_byte]
#                   - [cmd_byte, length_byte, option_byte, [data], cmd_byte]


#         Notes
#         -----
#         - the reading is active after running "sefl.clearObtained()"
#         - if a SerialException is raised >> "ErrorSerialInterface" will be set to identify: disconnection of the device, etc."""


#     @abstractmethod
#     def get_sciospec_complete_frame(self):
#         """[summary]
#         """


#     @abstractmethod
#     def read_bytes(self, nb_bytes:int= 1) -> list:
#         """ Read on serial port a number of bytes

#         Args:
#             nb_bytes (int): number of bytes to read. Default is set to 1

#         Raises:
#             ErrorSerialInterface: [description]

#         Returns:
#             list: list of read bytes
#         """

# if __name__ == '__main__':
#     pass
