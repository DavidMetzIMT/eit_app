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

import glob
import sys
import time

import serial  # get from http://pyserial.sourceforge.net/
from eit_app.io.sciospec.com_constants import *
from eit_app.io.sciospec.device import SciospecDev

__author__ = "David Metz"
__copyright__ = "Copyright (c) 2021"
__credits__ = ["David Metz", "Jonathan Foote","Chris Liechti"]
__license__ = "GPLv3"
__version__ = "2.0.0"
__maintainer__ = "David Metz"
__email__ = "d.metz@tu-bs.de"
__status__ = "Production"


SER_TIMEOUT = 0.1


class SciospecSerialInterface(object):
    """Class to interface with the serial port of Sciospec Device.

    Repeatedly polls hardware, unless we are sending a command
    "Ser" is a serial port class from the pyserial pacakge """

    def __init__(self):
        self.RxFrame = None  # last response retrieved by polling
        self.Callback = None
        self.Verbose = 0  # for debugging
        self.ErrorSerialInterface = ''
        self.Ser = serial.Serial()
        self.BaudRate = 115200  # Default baud rate
        self.PortName = "COM5"
        self.AvailablePorts = ['None']
        self.InitDone = False
        self.dev= SciospecDev(['None'])# to access to some methods

        if self.Verbose > 0: # print for debuging
            print('Start: __init__ Serial_Interface')

    def updateListSerialPorts(self):
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

        result = []
        for port in ports:
            try:
                ser = serial.Serial(port,str(115200), timeout=None)
                try:
                    while ser.in_waiting > 0:
                        ser.read(ser.in_waiting)
                    ser.write(bytearray(self.dev.mkCmdFrame(CMD_START_STOP_MEAS, OP_STOP_MEAS)))  # stop the meas
                    time.sleep(0.1)
                    while ser.in_waiting > 0:
                        ser.read(ser.in_waiting)
                    ser.write(bytearray(self.dev.mkCmdFrame(CMD_DEVICE_SERIAL_NUMBER, OP_NULL))) # ask for the SN number
                    time.sleep(0.1)
                    res = list(ser.read(ser.in_waiting)) # get all data
                    ack_msg=self.dev.checkAck(res[-2])
                    if ack_msg.error==0: # if CMD_ACK recieved then add the port to the list
                        result.append(port)
                except:
                    pass
                ser.close()
                
            except (OSError, serial.SerialException):
                pass
        self.AvailablePorts = result
        return result

    def clearObtained(self):
        """ Clear recieved data by reading them

        Notes
        -----
        - Typically used after the opening a serial port and
        a stop-meas cmd, in case that the device was still sending meas. data"""

        time.sleep(0.5)  # wait a while to be
        while self.Ser.in_waiting > 0:
            self.Ser.read(self.Ser.in_waiting)
        self.InitDone = True

    def openSerial(self, port, baudrate, timeout=None, write_timeout=0):
        """ Open serial interface

        Parameters
        ----------
        port: str
            serial port to connect
        baudrate: str or int
        timeout: int
        write_timeout: int

        Returns
        -------
        results : 1 if open successed, 0 otherwise

        Notes
        -----
        - see also Serialbase in serial package """

        try:
            # open the serial port
            self.Ser = serial.Serial(   port,
                                        str(baudrate), 
                                        timeout=timeout, 
                                        write_timeout=write_timeout)
            self.PortName = port
            # read everything the device could send
            self.Ser.reset_output_buffer()
            self.Ser.reset_input_buffer()
            self.Ser.flush()
            if self.Verbose > 0: # print for debuging
                print('in openSerial', self.Ser.is_open)
            result = 1
        except (OSError, serial.SerialException):
            self.PortName = 'none'
            result = 0
        return result

    def closeSerial(self):
        """ Close serial interface

        Returns
        -------
        results : 1 (is always successful)

        Notes
        -----
        - see also Serialbase in serial package """
        self.Ser.close()
        self.InitDone = False
        return 1

    def registerCallback(self, function):
        """ Register function (external function) to call 
        when the hardware sends a complete data frame
        
        """
        self.Callback = function

    def writeSerial(self, command):
        """ Send a command to the hardware

        Parameters
        ----------
        command: list of int8 (1 Byte) e.g. [0xD1, 0x00, 0xD1]

        Notes
        -----
        if a SerialException is raised >> "ErrorSerialInterface" will be set to identify: disconnection of the device, etc."""

        if self.Verbose > 0: # print for debuging
            print('TX: ' + str(command))

        try:
            self.Ser.write(bytearray(command))
        except serial.SerialException:
            self.ErrorSerialInterface = 'Serial Device not connectedw'

        self.Ser.flush()

    def pollReadSerial(self):
        """ Called repeatedly by thread (e.g. from GUI) for reading the serial port

        when a complete frame has been recieved, it is tramsmitted to the registered function Callback

        RXFrame:  - [cmd_byte, length_byte=0x01, option_byte, cmd_byte]
                  - [cmd_byte, length_byte, option_byte, [data], cmd_byte]
                    

        Notes
        -----
        - the reading is active after running "sefl.clearObtained()"
        - if a SerialException is raised >> "ErrorSerialInterface" will be set to identify: disconnection of the device, etc."""
        
        if self.InitDone == True:
            try:
                self.RxFrame = 0
                if self.Ser.in_waiting >= FRAME_LENGTH_MIN: # a frame is at least 4 bytes
                    self.RxFrame = list(self.Ser.read(LENGTH_BYTE_INDX + 1)) # read up to the length byte
                    length_data2read = self.RxFrame[LENGTH_BYTE_INDX] + 1 # read also the additional "ending CMD Byte"
                    while self.Ser.in_waiting < length_data2read:
                        pass
                    self.RxFrame.extend(list(self.Ser.read(length_data2read)))
                    if self.Verbose > 0: # print for debuging
                        print('RX:' + str(self.RxFrame))
                    if self.Callback:
                        self.Callback(self.RxFrame)
                else:
                    if self.Verbose > 1: # print for debuging
                        print('RX:NONE')
            except serial.SerialException:
                if self.Ser.is_open:
                    self.ErrorSerialInterface = 'Serial Device not connectedr'


if __name__ == '__main__':
    s=SciospecSerialInterface()
    s.updateListSerialPorts()
    print(s.AvailablePorts)
    pass
