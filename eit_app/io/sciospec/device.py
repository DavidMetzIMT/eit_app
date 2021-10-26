#!C:\Anaconda3\envs\py38_app python
# -*- coding: utf-8 -*-

"""  Classes and function to interact with the Sciospec EIT device

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

import ast
from re import A
import struct
from typing import Any, List
import copy
import numpy as np
import pandas as pd
from matplotlib.pyplot import flag, tick_params
import pickle
from os import listdir
from os.path import isfile, join

from eit_app.eit.model import *
from eit_app.io.sciospec.meas_dataset import EitMeasurementDataset
from eit_app.io.sciospec.device_setup import SciospecSetup
from eit_app.io.sciospec.com_constants import *
from eit_app.io.sciospec.hw_serial_interface import HARDWARE_NOT_DETECTED, SerialInterface, SERIAL_BAUD_RATE_DEFAULT, SerialInterfaceError
from eit_app.threads_process.threads_worker import HardwarePoller
from eit_app.utils.constants import EXT_PKL, MEAS_DIR
from eit_app.utils.log import main_log
from eit_app.utils.utils_path import get_date_time, mk_ouput_dir, append_date_time, save_as_pickle, search4FileWithExtension
from eit_app.io.sciospec.utils import *
from eit_app.utils.flag import Flag
from eit_app.app.dialog_boxes import show_dialog, show_msgBox
import signal
import time
import logging
import queue
import enum

from dataclasses import dataclass
__author__ = "David Metz"
__copyright__ = "Copyright (c) 2021"
__credits__ = ["David Metz"]
__license__ = "GPLv3"
__version__ = "2.0.0"
__maintainer__ = "David Metz"
__email__ = "d.metz@tu-bs.de"
__status__ = "Production"

logger = logging.getLogger(__name__)


NO_DEVICE_CONNECTED_PROMPT= 'No device connected'

class StatusSWInterface(enum.Enum):
    NOT_CONNECTED='NOT_CONNECTED'
    IDLE='IDLE'
    MEASURING='MEASURING'
    WAIT_FOR_DEVICE='WAIT_FOR_DEVICE'


class SWInterfaceError(Exception):
    """ Custom Error for SoftWare Interface of a Device"""

class CouldNotWriteToDevice(SWInterfaceError):
    """ Custom Error """

class CouldNotFindPortInAvailableDevices(SWInterfaceError):
    """ Custom Error e"""

class NoListOfAvailableDevices(SWInterfaceError):
    """ Custom Error e"""

class TimeOut(SWInterfaceError):
    """ Custom: error"""
class SWReset(SWInterfaceError):
    """ Custom: error"""

class MeasurementsRunningError(SWInterfaceError):
    """ Custom: error"""


class Buffer(object):
    """ Class to manage a FIFO queue with custom methods for use as a buffer"""
    def __init__(self, maxsize=None) -> None:
        self.buffer= queue.Queue(maxsize=maxsize)
    
    def is_full(self):
        return self.buffer.full()
    def is_empty(self):
        return self.buffer.empty()

    def add(self, data):
        self.buffer.put(data)
        
    def get_oldest(self):
        try:
            return self.buffer.get_nowait()
        except queue.Empty: # if empty then return empty ....
            return []
   
    def clear(self):
        while not self.buffer.empty():
            self.buffer.get_nowait()

    def rm_last(self):
        tmp= queue.Queue()
        while not self.buffer.empty():
            tmp.put_nowait(self.buffer.get_nowait())

        while not tmp.empty():
            last=tmp.get_nowait()
            if not tmp.empty():
                self.buffer.put_nowait(last)
        return last or []


################################################################################
## Class for Sciopec Device ####################################################
################################################################################

class SWInterface4SciospecDevice(object):
    """  Class responsible of the SoftWare Interface of a Sciospec Device
    functions
    - save infos about the Sciospec device
    - interact with it
    
    Regroup all informations, setup of the connected Sciospec EIT device
    and allow to interact with it according to is user guide.    """
    def __init__(self):
        """Constructor """
        self.treat_rx_frame_worker=HardwarePoller(name='treat_rx_frame',pollfunc=self.get_last_rx_frame,sleeptime=0.01)
        self.treat_rx_frame_worker.start()
        self._post_init_()

    def _post_init_(self):
        """ init the """
        self.channel = 32
        self.interface= SerialInterface()
        self.interface.register_callback(self.append_to_rx_buffer)
        self.setup=SciospecSetup(self.channel)
        self.status=StatusSWInterface.NOT_CONNECTED
        self.status_prompt = NO_DEVICE_CONNECTED_PROMPT
        self.dataset:EitMeasurementDataset=EitMeasurementDataset()
        self.flag_new_data=Flag()
        self.available_devices = {}
        self.rx_buffer= queue.Queue(maxsize=256) # infine queue.... maybe handle only a certain number of data to reduce memory allocttions???
        self.cmds_history=Buffer(maxsize=16)
        self.responses_history=Buffer(maxsize=16)
        self.make_callbacks_catalog()

    def _prepare_dataset(self, meas_name:str):
        """Prepare dataset for measurements
        return the name of the data set and the output directory """
        name, output_dir =self.dataset.prepare_for_aquisition(self.setup, meas_name)
        return name, output_dir

    def make_callbacks_catalog(self):
        """Link the CMD/OP to the pre/postprocess of the data"""
        self.cllbcks={
            CMD_SAVE_SETTINGS.tag:{
                OP_NULL.tag: None
                },
            CMD_SOFT_RESET.tag:{
                OP_NULL.tag: None
                },
            CMD_SET_MEAS_SETUP.tag:{
                OP_RESET_SETUP.tag: None,
                OP_BURST_COUNT.tag: self.setup.get_burst,
                OP_FRAME_RATE.tag: self.setup.get_frame_rate,
                OP_EXC_FREQUENCIES.tag: self.setup.get_freq_config,
                OP_EXC_AMPLITUDE.tag: self.setup.get_exc_amp,
                OP_EXC_PATTERN.tag: self.setup.get_exc_pattern
                },
            CMD_GET_MEAS_SETUP.tag:{
                # OP_RESET_SETUP.tag: None,
                OP_BURST_COUNT.tag: self.setup.set_burst,
                OP_FRAME_RATE.tag: self.setup.set_frame_rate,
                OP_EXC_FREQUENCIES.tag: self.setup.set_freq_config,
                OP_EXC_AMPLITUDE.tag: self.setup.set_exc_amp,
                OP_EXC_PATTERN.tag: self.setup.set_exc_pattern
                },
            CMD_SET_OUTPUT_CONFIG.tag:{
                OP_EXC_STAMP.tag: self.setup.get_exc_stamp,
                OP_CURRENT_STAMP.tag: self.setup.get_current_stamp,
                OP_TIME_STAMP.tag: self.setup.get_time_stamp
                },
            CMD_GET_OUTPUT_CONFIG.tag:{
                OP_EXC_STAMP.tag: self.setup.set_exc_stamp,
                OP_CURRENT_STAMP.tag: self.setup.set_current_stamp,
                OP_TIME_STAMP.tag: self.setup.set_time_stamp
                },
            CMD_START_STOP_MEAS.tag:{
                OP_NULL.tag:self.dataset.add_rx_frame_to_dataset#,
                # OP_STOP_MEAS.tag:None,
                # OP_START_MEAS.tag: None
                },
            CMD_SET_ETHERNET_CONFIG.tag:{
                OP_IP_ADRESS.tag: None,
                OP_MAC_ADRESS.tag: None,
                OP_DHCP.tag: self.setup.get_dhcp
                },
            CMD_GET_ETHERNET_CONFIG.tag:{
                OP_IP_ADRESS.tag: self.setup.set_ip,
                OP_MAC_ADRESS.tag: self.setup.set_mac,
                OP_DHCP.tag: self.setup.set_dhcp
                },
            # CMD_SET_EXPORT_CHANNEL.tag:{:},
            # CMD_GET_EXPORT_CHANNEL.tag:{:},
            # CMD_GET_EXPORT_MODULE.tag:{:},
            # CMD_SET_BATTERY_CONTROL.tag:{:},
            # CMD_GET_BATTERY_CONTROL.tag:{:},
            # CMD_SET_LED_CONTROL.tag:{:},
            # CMD_GET_LED_CONTROL.tag:{:},
            CMD_GET_DEVICE_INFOS.tag:{
                OP_NULL.tag:self.setup.set_sn
                } #,
            # CMD_SET_CURRENT_SETTING.tag:{:},
            # CMD_GET_CURRENT_SETTING.tag:{:}
        }
    def wait_until_not_busy(self, time_out=None):
    
        while self.status==StatusSWInterface.WAIT_FOR_DEVICE:
            pass

    ## =========================================================================
    ##  Methods for sending data/commands
    ## =========================================================================
    
    def _send_cmd_frame(self,cmd:SciospecCmd, op:SciospecOption, cmd_append=True):
        """ Send a command frame to the device
        
        Parameters
        ----------
        cmd: SciospecCmd object
        op: Sciospecoption object

        Notes
        -----
        - all cmd, op, and ack are defined as constant in SciospecCONSTANTS.py"""
        # self.wait_until_not_busy()
        self.rx_ack= NONE_ACK # clear last recieved acknolegment
        cmd_frame = self._make_command_frame(cmd, op)
        if cmd_append:
            self.cmds_history.add([cmd, op])
            self.status=StatusSWInterface.WAIT_FOR_DEVICE
        try:
            self.interface.write(cmd_frame)
            logger.debug(f'Send cmd "{cmd.name}", op: "{op.name}", cmd_frame :{cmd_frame}')
        except SerialInterfaceError as error:
            self.cmds_history.rm_last()
            self.update_status(oldest_cmd=(CMD_GET_DEVICE_INFOS, OP_NULL))
            show_msgBox(error.__str__(), 'Communication with device -FAILED', "Critical")
            # raise CouldNotWriteToDevice(error)
            
    def _make_command_frame(self,cmd:SciospecCmd, op:SciospecOption):
        """ Make the command frame to send
        according to the cmd and op parameters
        
        Parameters
        ----------
        cmd: SciospecCmd object
        op: Sciospecoption object

        Returns
        -------
        cmd_frame: List of int8 (byte)
            the frame to send to the device

        Notes
        -----
        - all cmd, op, and ack are defined as constant in SciospecCONSTANTS.py
        - the errors were for the testing of that method and should never be raised"""
        
        if op not in cmd.options:
            raise SWInterfaceError(f'Command "{cmd.name}" ({cmd.tag}) not compatible with option "{op.name}"({op.tag})')
        
        if cmd.type == CmdTypes.simple: # send simple cmd (without option)
            cmd_frame = [cmd.tag, 0x00, cmd.tag]
        else:
            LL_byte= op.LL_bytes[0] if cmd.type == CmdTypes.set_w_option else op.LL_bytes[1]
            if LL_byte == 0x00:
                raise TypeError('not allowed option for the command')
            elif LL_byte== 0x01: # send cmd with option
                cmd_frame = [cmd.tag, LL_byte ,op.tag ,cmd.tag]
            else: 
                data= self._get_data_to_send(cmd, op)
                if len(data)+1 == LL_byte: # send cmd with option and data
                    cmd_frame = [cmd.tag, LL_byte, op.tag]
                    for d in data:
                        cmd_frame.append(d)
                    cmd_frame.append(cmd.tag)
                else:
                    raise TypeError('Data do not have right lenght')
        return cmd_frame

    def _get_data_to_send(self,cmd:SciospecCmd, op:SciospecOption) -> bytearray:
        """Provide the data to send corresponding to the cmd and option
            >> call the correspoding function from the cllbcks catalog

        Args:
            cmd (SciospecCmd): command
            op (SciospecOption): option

        Returns:
            bytearray: data to send
        """

        try:
            print(self.cllbcks[cmd.tag][op.tag](True))

            return self.cllbcks[cmd.tag][op.tag](True) or [0x00]
        except KeyError:
            msg= f'Combination of Cmd:"{cmd.name}"({cmd.tag})/ Option:"{op.name}"({op.tag}) - NOT FOUND in callbacks catalog'
            logger.error(msg)
            raise  SWInterfaceError(msg)            
        
    ## =========================================================================
    ##  Methods for recieved data
    ## =========================================================================

    def append_to_rx_buffer(self,rx_frame:List[bytes]):
        """ Called by the SerialInterface "PollreadSerial" to treat the recieved frame
        Parameters
        ----------
        rx_frame: list of int8 (byte)"""
        
        self.rx_buffer.put_nowait(rx_frame)

    def get_last_rx_frame(self):
        try:
            rx_frame=self.rx_buffer.get_nowait()
            if rx_frame==[HARDWARE_NOT_DETECTED]:
                self.disconnect_device()
            else:
                rx_frame=self._verify_len_of_rx_frame(rx_frame)
                self.treat_rx_frame(rx_frame)
        except queue.Empty:
            pass # do nothing for the moment
        except SWInterfaceError as e:
            logger.error(e)

    def _verify_len_of_rx_frame(self,rx_frame:List[bytes]):
        """ refify the len of the rx frame, which should be >= 4"""
        if len(rx_frame)>=4:
            # print('rx_frame verified',rx_frame, type(rx_frame), type(rx_frame[0]))
            return rx_frame
        else:
            raise SWInterfaceError(f'The length of rx_frame: {rx_frame} is < 4')# should never be raised
        
    def treat_rx_frame(self,rx_frame:List[bytes]):
        """ Sort the recieved frames between ACKNOWLEGMENT,MEASURING, RESPONSE 
        and treat them accordingly"""
        if self.is_ack(rx_frame):          
            self.treat_rx_ack(rx_frame)
        elif self.is_meas(rx_frame):
            self.treat_rx_meas(rx_frame)
        else: # is_resp
            self.treat_rx_response(rx_frame)

    def is_ack(self,rx_frame:List[bytes])-> bool:
        """ Return if rx_frame is an ACKNOWLEGMENT frame  """
        tmp=rx_frame[:]
        tmp[OPTION_BYTE_INDX]=0
        return tmp==ACK_FRAME

    def is_meas(self,rx_frame:List[bytes])-> bool:
        """ Return if rx_frame is a MEASURING frame """
        return rx_frame[CMD_BYTE_INDX] == CMD_START_STOP_MEAS.tag

    def treat_rx_ack(self, rx_frame):
        """ Treat the recieved ACKNOWLEGMENT frame:
        - identify the ack (and save it in rx_ack)
        - if NACK > raise error
        - if ACK the oldest cmd and oldest response are proceed"""
        
        self.rx_ack=self.identify_ack(rx_frame)
        if self.rx_ack.is_nack():
            self.handle_nack()
        else:
            oldest_cmd, oldest_response = self.handle_ack()
            self.proceed_answer(oldest_response, oldest_cmd)

    def treat_rx_meas(self, rx_frame):
        """Treat the recieved MEASURING frame
        - logging
        - proceeding of the frame"""
        msg=f'RX_MEAS: {rx_frame[:20]}'
        logger.info(msg)
        self.proceed_answer(rx_frame)

    def treat_rx_response(self, rx_frame):
        """ Treat the recieved RESPONSE frame
        - logging
        - add the response to the history (it will be )"""
        msg=f'RX_RESP: {rx_frame}'
        logger.info(msg)
        self.responses_history.add(rx_frame)
        
    def proceed_answer(self, answer, oldest_cmd=None):
        """ proceed answers (MEASURING and RESPONSE frame)"""
        self._extract_data(answer)
        self.update_status(oldest_cmd)

    def identify_ack(self, rx_frame)-> SciospecAck:
        """return the corresponding SciospecAck object
        if not found in the list "ACKs", return "NONE_ACK"""""
        rx_ack= NONE_ACK
        for ack_i in ACKs:
            if ack_i.ack_byte==rx_frame[OPTION_BYTE_INDX]:
                rx_ack= ack_i
                break
        return rx_ack

    def handle_nack(self):
        """  Handle NAck:
        -do some logging
        -raise an error ... Handling of NACK is not implemented..."""
        msg=f'RX_NACK: {self.rx_ack.__dict__} - nothing implemented yet, to handle it!!!'
        logger.error(msg)
        raise  SWInterfaceError(msg)

    def handle_ack(self):
        """ Handle Ack:
        - return/delete odlest cmd from cmd history
        - return/delete odlest response from response history
        - do some logging        
        """
        oldest_cmd= self.cmds_history.get_oldest()
        oldest_response=self.responses_history.get_oldest()
        if oldest_cmd[0].answer_type==Answer.WAIT_FOR_ANSWER_AND_ACK:
            msg=f'RX_ACK: {self.rx_ack.name} of ANSWER {oldest_response} from CMD {oldest_cmd[0].name}- SUCCESS'
        elif oldest_cmd[0].answer_type==Answer.WAIT_FOR_ACK:
            msg= f'RX_ACK: {self.rx_ack.name} for CMD {oldest_cmd[0].name} - SUCCESS'
        logger.info(msg)
        return oldest_cmd, oldest_response

    def _extract_data(self, rx_frame:List[bytes]):
        """ Extract the data from rx_frame and save them to the right place regading the cllbcks catalog 

        - the errors were for the testing of that method and should never be raised"""
        
        if not rx_frame:
            return
        self.flag_new_data.clear()
        cmd_tag= rx_frame[CMD_BYTE_INDX]
        if OP_NULL.tag in self.cllbcks[cmd_tag].keys(): # some answer do not have options (meas, sn)
            op_tag=OP_NULL.tag
        else:
            op_tag= rx_frame[OPTION_BYTE_INDX]
        try:
            if self.cllbcks[cmd_tag][op_tag]:
                self.cllbcks[cmd_tag][op_tag](rx_frame,True)
                self.flag_new_data.set()
                msg=f'RX_ANSWER: {rx_frame} -  TREATED'
                logger.debug(msg)
        except KeyError:
            cmd=get_cmd(cmd_tag)
            op=get_op(cmd.options, op_tag)
            msg= f'Combination of Cmd:"{cmd.name}"({cmd.tag})/ Option:"{op.name}"({op.tag}) - NOT FOUND in callbacks catalog'
            logger.error(msg)
            raise  SWInterfaceError(msg)
            
        except TypeError as error:
            logger.error(error)  

    def update_status(self, oldest_cmd:SciospecCmd):
            
        if self.cmds_history.is_empty() and oldest_cmd:
            cmd, op= oldest_cmd[0], oldest_cmd[1]
            if cmd.tag == CMD_START_STOP_MEAS.tag and op.tag == OP_START_MEAS.tag:
                self.status=StatusSWInterface.MEASURING
            else:
                self.status=StatusSWInterface.IDLE
    
    def is_measuring(self):
        return self.status==StatusSWInterface.MEASURING
    def not_connected(self):
        return self.status==StatusSWInterface.NOT_CONNECTED
    
    def if_measuring_stop(self, force:bool=False)->None:

        if self.is_measuring():
            if force:
                self.stop_meas()
                show_msgBox('Measurements have been stopped', 'Measurements still running!', "Information")
            else:
                show_msgBox('Please stop measurements first', 'Measurements still running!', "Information")

    

    ## =========================================================================
    ##  Methods excecuting task on the device
    ## =========================================================================



    def get_available_sciospec_devices(self):
        """Lists the available Sciospec device is available
        - Device infos are ask and if an ack is get: it is a Sciospec device..."""
        ports=self.interface.get_ports_available()
        self.available_devices = {}
        self.treat_rx_frame_worker.start_polling()
        tmp=TmpBuffer(self.setup.device_infos)
        for port in ports:
            self.interface.open(port)
            self.get_device_infos()
            if not self.rx_ack.is_nack():
                device_name = f'Device (SN: {self.setup.get_sn()}) on serial port "{port}"'
                self.available_devices[device_name]=port
            self.interface.close()
        self.treat_rx_frame_worker.stop_polling()
        self.status=StatusSWInterface.NOT_CONNECTED
        tmp.restitute_object_from_buffer(self.setup.device_infos)
        msg = f'Sciospec devices available: {[k for k in self.available_devices]}'
        logger.info(msg)

        return self.available_devices
        
    def connect_device(self, device_name:str, baudrate=SERIAL_BAUD_RATE_DEFAULT):
        """" Connect a sciopec device"""
        if not self.available_devices:
            show_msgBox(
                'Please refresh the list of availables device first and retry!',
                'no devices available', "Warning")
            return
        if device_name not in self.available_devices.keys():
            msg= f'Sciospec device "{device_name}" - NOT FOUND'
            logger.warning(msg)
            show_msgBox(
                f'Please reconnect your device "{device_name}" and retry ({msg})',
                'Device - NOT FOUND ', "Critical") 
            return
        self.treat_rx_frame_worker.start_polling()
        self.interface.open(self.available_devices[device_name], baudrate)
        self.get_device_infos()               
        self.status_prompt= f'Device (SN: {self.setup.get_sn()}) on serial port "{self.interface.get_actual_port_name()}" (b:{self.interface.get_actual_baudrate()} d:8 s:1 p:None) - CONNECTED'
        logger.info(self.status_prompt)

    def disconnect_device(self):
        """" Disconnect the sciopec device"""
        self.if_measuring_stop(force=True)
        self.treat_rx_frame_worker.stop_polling()
        msg=f'Device (SN: {self.setup.get_sn()}) on serial port "{self.interface.get_actual_port_name()}" - DISCONNECTED'
        self.interface.close()
        logger.info(msg)
        self._post_init_()
        self.get_available_sciospec_devices() # update the list of Sciospec devices available ????

    def get_device_infos(self):
        """Ask for the serial nummer of the Device """
        self.if_measuring_stop(force=False)
        self._send_cmd_frame(CMD_GET_DEVICE_INFOS, OP_NULL)
        self.wait_until_not_busy()

    def start_meas(self, name_measurement:str='default_meas_name'):
        """ Start measurements """
        self.if_measuring_stop(force=False)
        name, output_dir =self._prepare_dataset(name_measurement)
        self._send_cmd_frame(CMD_START_STOP_MEAS, OP_START_MEAS)
        self.wait_until_not_busy()
        return name, output_dir

    def stop_meas(self, append=True):
        """ Stop measurements """
        self._send_cmd_frame(CMD_START_STOP_MEAS, OP_STOP_MEAS, cmd_append=append)
        self.wait_until_not_busy()
        
    def set_setup(self):
        """ Send the setup to the device """
        self.if_measuring_stop(force=False)
        logger.info('### SET SETUP FROM DEVICE ####')
        self._send_cmd_frame(CMD_SET_OUTPUT_CONFIG, OP_EXC_STAMP)
        self._send_cmd_frame(CMD_SET_OUTPUT_CONFIG, OP_CURRENT_STAMP)
        self._send_cmd_frame(CMD_SET_OUTPUT_CONFIG, OP_TIME_STAMP)
        self._send_cmd_frame(CMD_SET_ETHERNET_CONFIG, OP_DHCP)
        self._send_cmd_frame(CMD_SET_MEAS_SETUP, OP_RESET_SETUP)
        self._send_cmd_frame(CMD_SET_MEAS_SETUP, OP_EXC_AMPLITUDE)
        self._send_cmd_frame(CMD_SET_MEAS_SETUP, OP_BURST_COUNT)
        self._send_cmd_frame(CMD_SET_MEAS_SETUP, OP_FRAME_RATE)
        self._send_cmd_frame(CMD_SET_MEAS_SETUP, OP_EXC_FREQUENCIES)
        for idx in range(len(self.setup.get_exc_pattern())):
            self.setup.set_exc_pattern_idx(idx)
            self._send_cmd_frame(CMD_SET_MEAS_SETUP, OP_EXC_PATTERN)
        self.wait_until_not_busy()

    def get_setup(self):
        """ Get the setup of the device """
        self.if_measuring_stop(force=False)
        logger.info('### GET SETUP FROM DEVICE ####')
        self._send_cmd_frame(CMD_GET_MEAS_SETUP, OP_EXC_AMPLITUDE)
        self._send_cmd_frame(CMD_GET_MEAS_SETUP, OP_BURST_COUNT)
        self._send_cmd_frame(CMD_GET_MEAS_SETUP, OP_FRAME_RATE)
        self._send_cmd_frame(CMD_GET_MEAS_SETUP, OP_EXC_FREQUENCIES)
        self._send_cmd_frame(CMD_GET_MEAS_SETUP, OP_EXC_PATTERN)
        self._send_cmd_frame(CMD_GET_OUTPUT_CONFIG, OP_EXC_STAMP)
        self._send_cmd_frame(CMD_GET_OUTPUT_CONFIG, OP_CURRENT_STAMP)
        self._send_cmd_frame(CMD_GET_OUTPUT_CONFIG, OP_TIME_STAMP)
        self._send_cmd_frame(CMD_GET_ETHERNET_CONFIG, OP_IP_ADRESS)
        self._send_cmd_frame(CMD_GET_ETHERNET_CONFIG, OP_MAC_ADRESS)
        self._send_cmd_frame(CMD_GET_ETHERNET_CONFIG, OP_DHCP)
        self.wait_until_not_busy()

    def software_reset(self):
        """ Sofware reset the device
        Notes: a restart is needed after this method"""
        self.if_measuring_stop(force=False)
        self._send_cmd_frame(CMD_SOFT_RESET,OP_NULL)
        self.wait_until_not_busy()
        time.sleep(10)
        self.disconnect_device()
        show_msgBox(
                'Reset done',
                'Device reset ', "Information")
        



    # ## =========================================================================
    # ##  Methods relative to loading and saving setups of the device
    # ## =========================================================================
    def saveSetupDevice(self, file):
        self.setup.saveSetupDevice(file)
        
    def loadSetupDevice(self, file):
        self.setup.loadSetupDevice(file)

        
class TmpBuffer:
    tmp:Any=None
    
    def __init__(self, obj:Any) -> None:
        self.buffering_object(obj)

    def buffering_object(self, obj:Any):
        self.tmp=copy.deepcopy(obj)

    def restitute_object_from_buffer(self,original_obj):
        for k in self.tmp.__dict__.keys():
            setattr(original_obj, k, getattr(self.tmp,k))


if __name__ == '__main__':

    main_log()

    dev= SWInterface4SciospecDevice()
    dev.get_available_sciospec_devices()
    dev.connect_device('Device (SN: 01-0019-0132-0A0C) on serial port "COM3"')
    dev.get_setup()
    dev.set_setup()
    dev.start_meas()
    time.sleep(5)
    dev.stop_meas()
    dev.disconnect_device()

