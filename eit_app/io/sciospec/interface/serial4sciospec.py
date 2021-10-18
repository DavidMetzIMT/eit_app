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
from ast import Bytes

import glob
import logging
import sys
import time
from typing import List

import serial  # get from http://pyserial.sourceforge.net/
from eit_app.io.sciospec.com_constants import *
#from eit_app.io.sciospec.device import SciospecDevice
from eit_app.threads_process.threads_worker import HardwarePoller, Worker
from eit_app.utils.log import main_log

from abc import ABC, abstractmethod

__author__ = "David Metz"
__copyright__ = "Copyright (c) 2021"
__credits__ = ["David Metz", "Jonathan Foote","Chris Liechti"]
__license__ = "GPLv3"
__version__ = "2.0.0"
__maintainer__ = "David Metz"
__email__ = "d.metz@tu-bs.de"
__status__ = "Production"

logger = logging.getLogger(__name__)

SER_TIMEOUT = 0.1
SERIAL_BAUD_RATE_DEFAULT= 115200

class Interface(ABC):
    """ Class responsible for defining """
    
    @abstractmethod
    def get_ports_available(self)->List[str]:
        """ Lists the ports available on the system

        Returns
        -------
        A list of the serial ports available on the system
        
        raises EnvironmentError
        ------------------------
        On unsupported or unknown platforms"""
        
        
    @abstractmethod
    def clear_unwanted_rx_frames(self):
        """ Clear recieved data by reading them

        Notes
        -----
        - Typically used after the opening a serial port and
        a stop-meas cmd, in case that the device was still sending meas. data (measurement not stopped correctly)"""

    @abstractmethod
    def open_interface(self, port_name, baudrate=SERIAL_BAUD_RATE_DEFAULT, timeout=None, write_timeout=0):
        """ Open interface

        Raises:
            serial.PortNotOpenError: [description]

        Returns:
            [type]: [description]
        """
        
    @abstractmethod
    def close_interface(self):
        """ Close interface """


    @abstractmethod
    def register_callback(self, func=None):
        """Register function (external function) to call 
        when the hardware sends a complete data frame

        Args:
            func: function, who . Defaults to None.
        """
 
    @abstractmethod
    def no_callback(self, rx_frame:List[Bytes]=[]):
        """[summary]

        Args:
            rx_frame (list, optional): [description]. Defaults to [].
        """


    @abstractmethod
    def write_serial(self, command:List[Bytes]):
        """ Send a command to the hardware

        Parameters
        ----------
        command: list of int8 (1 Byte) e.g. [0xD1, 0x00, 0xD1]

        Notes
        -----
        if a SerialException is raised >> "ErrorSerialInterface" will be set to identify: disconnection of the device, etc."""

    @abstractmethod
    def poll_read_serial(self):
        """ Called repeatedly by thread (e.g. from GUI) for reading the serial port

        when a complete frame has been recieved, it is tramsmitted to the registered function Callback

        RXFrame:  - [cmd_byte, length_byte=0x01, option_byte, cmd_byte]
                  - [cmd_byte, length_byte, option_byte, [data], cmd_byte]
                    

        Notes
        -----
        - the reading is active after running "sefl.clearObtained()"
        - if a SerialException is raised >> "ErrorSerialInterface" will be set to identify: disconnection of the device, etc."""


    @abstractmethod
    def get_sciospec_complete_frame(self):
        """[summary]
        """


    @abstractmethod
    def read_bytes(self, nb_bytes:int= 1) -> list:
        """ Read on serial port a number of bytes

        Args:
            nb_bytes (int): number of bytes to read. Default is set to 1

        Raises:
            ErrorSerialInterface: [description]

        Returns:
            list: list of read bytes
        """



class SerialInterfaceError(Exception):
    def __init__(self,port:serial.Serial, msg) -> None:
        super().__init__(msg)
        self.port=port
        
class DoNotWriteToSerial(SerialInterfaceError):
    pass

class SerialInterface(Interface):
    """Class to interface with the serial port of Sciospec Device.

    Repeatedly polls hardware, unless we are sending a command
    "Ser" is a serial port class from the pyserial pacakge """

    def __init__(self, verbose=False)-> None:
        self.last_rx_frame = None  # last response retrieved by polling
        self.callback = None
        self.register_callback()
        self._verbose = verbose  # for debugging
        self.ErrorSerialInterface = ''
        self.serial_port = serial.Serial()
        self.ports_available = []
        self._initializated = False
        self.listen_worker = HardwarePoller(name='Serial',
                                            sleeptime=0.01,
                                            pollfunc=self.poll_read_serial,
                                            verbose=verbose)
        self.listen_worker.start()

        if self._verbose: # print for debuging
            print('__init__ SerialInterface - done')

    def get_ports_available(self)->List[str]:
        """ Lists serial port names on which Sciospec device is available

        Device infos are ask and if an ack is get: it is a Sciospec device...

        Returns
        -------
        A list of the serial ports available on the system
        
        raises EnvironmentError
        ------------------------
        On unsupported or unknown platforms"""
        
        if sys.platform.startswith('win'):
            ports = ['COM%s' % (i + 1) for i in range(256)]
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            # this excludes your current terminal "/dev/tty"
            ports = glob.glob('/dev/tty[A-Za-z]*')
        elif sys.platform.startswith('darwin'):
            ports = glob.glob('/dev/tty.*')
        else:
            raise EnvironmentError('Unsupported platform')

        actual_ports = []
        for port in ports:
            try:
                ser = serial.Serial(port,str(SERIAL_BAUD_RATE_DEFAULT), timeout=None)
                actual_ports.append(port)
                ser.close()
            except (OSError, serial.SerialException):
                pass
        
        self.ports_available = actual_ports
        
        msg=f'Available serial ports : {self.ports_available}'
        logger.info(msg)

        return self.ports_available
    
    def clear_unwanted_rx_frames(self):
        """ Clear recieved data by reading them

        Notes
        -----
        - Typically used after the opening a serial port and
        a stop-meas cmd, in case that the device was still sending meas. data"""

        self.listen_worker.stop_polling()
        time.sleep(0.5)  # wait a while
        while self.serial_port.in_waiting:
            self.serial_port.read(self.serial_port.in_waiting)
        self.listen_worker.start_polling()
        
    def open_interface(self, port_name, baudrate=SERIAL_BAUD_RATE_DEFAULT, timeout=None, write_timeout=0):
        """ Open serial interface

        Args:
            port ([type]): [description]
            baudrate ([type], optional): [description]. Defaults to SERIAL_BAUD_RATE_DEFAULT.
            timeout ([type], optional): [description]. Defaults to None.
            write_timeout (int, optional): [description]. Defaults to 0.

        Raises:
            serial.PortNotOpenError: [description]
        """
        try:
            # open the serial port
            self.serial_port = serial.Serial(   port_name,
                                                str(self.baudrate), 
                                                timeout=timeout, 
                                                write_timeout=write_timeout)
            # read everything the device could send
            self.serial_port.reset_output_buffer()
            self.serial_port.reset_input_buffer()
            self.serial_port.flush()
            self.clear_unwanted_rx_frames()

            msg=f'Connection to serial port {port_name} - OPENED'
            logger.info(msg)

        except (OSError, serial.SerialException) as error:
            initial_error_message= error.__str__()
            msg=    f'Connection to serial port {port_name} - FAILED\
                    \n  >>ErrorSource:{initial_error_message}'
            logger.error(msg)
            raise SerialInterfaceError( self.serial_port, msg)
        

    def close_interface(self):
        """ Close serial interface """

        self.listen_worker.stop_polling() # stop  the automatic polling on the hardware 
        msg=f'Connection to serial port {self.serial_port.name} - CLOSED'
        logger.info(msg)
        self.serial_port.close() # close the serial interface


    def register_callback(self, func=None):
        """Register function (external function) to call 
        when the hardware sends a complete data frame

        Args:
            func: function, who . Defaults to None.
        """
        self.callback = func or self.no_callback
    
    def no_callback(self, rx_frame:list=[]):

        msg='Callback for rx_frame not defined'
        # time.sleep(0.1)
        logger.warning(msg)

    def write_serial(self, command:list):
        """ Send a command to the hardware

        Parameters
        ----------
        command: list of int8 (1 Byte) e.g. [0xD1, 0x00, 0xD1]

        Notes
        -----
        if a SerialException is raised >> "ErrorSerialInterface" will be set to identify: disconnection of the device, etc."""

        try:
            self.serial_port.write(bytearray(command))
            msg='TX: ' + str(command)
            logger.info(msg)
        except (serial.SerialException, serial.PortNotOpenError) as error:
            initial_error_message= error.__str__()
            msg=f'Writing CMD: {command} to serial device "{self.serial_port.name}" - FAILED\
                \n  >>ErrorSource:{initial_error_message}'
            logger.error(msg)
            raise SerialInterfaceError(self.serial_port, msg)

        self.serial_port.flush()

    def poll_read_serial(self):
        """ Called repeatedly by thread (e.g. from GUI) for reading the serial port

        when a complete frame has been recieved, it is tramsmitted to the registered function Callback

        RXFrame:  - [cmd_byte, length_byte=0x01, option_byte, cmd_byte]
                  - [cmd_byte, length_byte, option_byte, [data], cmd_byte]
                    

        Notes
        -----
        - the reading is active after running "sefl.clearObtained()"
        - if a SerialException is raised >> "ErrorSerialInterface" will be set to identify: disconnection of the device, etc."""

        self.last_rx_frame= self.get_sciospec_complete_frame()
        if self.last_rx_frame:
            self.callback(self.last_rx_frame)

    def get_sciospec_complete_frame(self):
        """[summary]

        Returns:
            [type]: [description]
        """
        rx_frame = []
        if self.serial_port.in_waiting >= FRAME_LENGTH_MIN: # a frame is at least 4 bytes
            rx_frame = self.read_bytes(LENGTH_BYTE_INDX + 1) # read up to the length byte
            length_data2read = rx_frame[LENGTH_BYTE_INDX] + 1 # read also the additional "ending CMD Byte"
            while self.serial_port.in_waiting < length_data2read: # dangerous ...timer use?
                pass
            rx_frame.extend(self.read_bytes(length_data2read))
            msg=f'RX: {rx_frame}'
            logger.info(msg)
        # print('in_waiting',self.serial_port.in_waiting)
        return rx_frame


    def read_bytes(self, nb_bytes:int= 1) -> list:
        """ Read on serial port a number of bytes

        Args:
            nb_bytes (int): number of bytes to read. Default is set to 1

        Raises:
            ErrorSerialInterface: [description]

        Returns:
            list: list of read bytes
        """
        try:
            return list(self.serial_port.read(nb_bytes))
        except (serial.SerialException, serial.PortNotOpenError) as error:
            initial_error_message= error.__str__()
            msg=f'Reading of {nb_bytes}Bytes from serial port "{self.serial_port.name}" - FAILED\
                \n  >>ErrorSource:{initial_error_message}'
            logger.error(msg)
            raise SerialInterfaceError(self.serial_port, msg)


if __name__ == '__main__':

    main_log()
    s=SerialInterface(verbose=False)


    # logger.info("An INFO message from " + __name__)
    # logger.debug("An INFO message from " + __name__)
    # logger.error("An INFO message from " + __name__)
    # logger.critical("An INFO message from " + __name__)
    # logger.warning("An INFO message from " + __name__)
    s.get_ports_available()
    try:
        s.open_serial('COM3')
    except SerialInterfaceError as e:
        print('handle not opened serial')
    try:
        s.write_serial( [0xB4, 0x01, 0x01, 0xB4])
    except SerialInterfaceError as e:
        print('handle not write serial')
    

    time.sleep(0.1)
    

    for _ in range(10000):
        pass
    time.sleep(1)
    s.close_serial()
    sys.exit()
