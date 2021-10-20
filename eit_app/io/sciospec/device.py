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
from matplotlib.pyplot import tick_params
import pickle
from os import listdir
from os.path import isfile, join

from eit_app.eit.model import *
from eit_app.io.sciospec import dataset
from eit_app.io.sciospec.com_constants import *
from eit_app.io.sciospec.hw_serial_interface import SerialInterface, SERIAL_BAUD_RATE_DEFAULT, SerialInterfaceError
from eit_app.threads_process.threads_worker import HardwarePoller
from eit_app.utils.constants import EXT_PKL, MEAS_DIR
from eit_app.utils.log import main_log
from eit_app.utils.utils_path import get_date_time, mk_ouput_dir, append_date_time, save_as_pickle, search4FileWithExtension
from eit_app.io.sciospec.utils import *
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
    """ class to manage a queue"""
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
    def __init__(self, verbose=False):
        
        self.verbose=verbose # for debugging
        # self.paths= paths
        self.treat_rx_frame_worker=HardwarePoller('treat_rx_frame',self.get_last_rx_frame,0.01)
        self.treat_rx_frame_worker.start()
        

        self.init_device()

    def init_device(self):
        """ init the """
        self.channel = 32
        self.interface= SerialInterface(self.verbose) # the serial interface is set outside this class (e.g. in the app_backend)
        self.interface.register_callback(self.append_to_rx_buffer)
        self.setup=SciospecSetup(self.channel)
        
        self.log=[]
        # self.add2Log('INIT: Device object created')
        self.status=StatusSWInterface.NOT_CONNECTED
        self.status_prompt = NO_DEVICE_CONNECTED_PROMPT

        self.dataset:EitMeasurementDataset=EitMeasurementDataset()
        self.flag_new_data=False
        self.flagMeasRunning= False
        self.available_devices = {}
        self.rx_buffer= queue.Queue(maxsize=256) # infine queue.... maybe handle only a certain number of data to reduce memory allocttions???
        self.cmds_history=Buffer(maxsize=16)
        self.responses_history=Buffer(maxsize=16)
        
        self.make_callbacks_catalog()
        # self.status_com_is_busy= False
        if self.verbose:
            print('Start: __init__ Device')



    def _prepare_dataset(self, name_measurement:str):
        name, output_dir =self.dataset.prepare_for_aquisition(self.setup, name_measurement) ## Prepare the Dataset
        # self.make_callbacks_catalog()
        return name, output_dir


    def set_flag_new_data(self):
        self.flag_new_data=True
    def clear_flag_new_data(self):
        self.flag_new_data=False
    def is_flag_new_data(self):
        return self.flag_new_data


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
                OP_BURST_COUNT.tag: self.setup.get_burst_for_tx,
                OP_FRAME_RATE.tag: self.setup.get_frame_rate_for_tx,
                OP_EXC_FREQUENCIES.tag: self.setup.get_freq_for_tx,
                OP_EXC_AMPLITUDE.tag: self.setup.get_exc_amp_for_tx,
                OP_EXC_PATTERN.tag: self.setup.get_exc_pattern_for_tx
                },
            CMD_GET_MEAS_SETUP.tag:{
                # OP_RESET_SETUP.tag: None,
                OP_BURST_COUNT.tag: self.setup.set_burst_from_rx,
                OP_FRAME_RATE.tag: self.setup.set_frame_rate_from_rx,
                OP_EXC_FREQUENCIES.tag: self.setup.set_freq_from_rx,
                OP_EXC_AMPLITUDE.tag: self.setup.set_exc_amp_from_rx,
                OP_EXC_PATTERN.tag: self.setup.set_exc_pattern_from_rx
                },
            CMD_SET_OUTPUT_CONFIG.tag:{
                OP_EXC_STAMP.tag: self.setup.get_exc_stamp_for_tx,
                OP_CURRENT_STAMP.tag: self.setup.get_current_stamp_for_tx,
                OP_TIME_STAMP.tag: self.setup.get_time_stamp_for_tx
                },
            CMD_GET_OUTPUT_CONFIG.tag:{
                OP_EXC_STAMP.tag: self.setup.set_exc_stamp_from_rx,
                OP_CURRENT_STAMP.tag: self.setup.set_current_stamp_from_rx,
                OP_TIME_STAMP.tag: self.setup.set_time_stamp_from_rx
                },
            CMD_START_STOP_MEAS.tag:{
                OP_NULL.tag:self.dataset.add_rx_frame_to_dataset#,
                # OP_STOP_MEAS.tag:None,
                # OP_START_MEAS.tag: None
                },
            CMD_SET_ETHERNET_CONFIG.tag:{
                OP_IP_ADRESS.tag: None,
                OP_MAC_ADRESS.tag: None,
                OP_DHCP.tag: self.setup.get_dhcp_for_tx
                },
            CMD_GET_ETHERNET_CONFIG.tag:{
                OP_IP_ADRESS.tag: self.setup.set_ip_from_rx,
                OP_MAC_ADRESS.tag: self.setup.set_mac_from_rx,
                OP_DHCP.tag: self.setup.set_dhcp_from_rx
                },
            # CMD_SET_EXPORT_CHANNEL.tag:{:},
            # CMD_GET_EXPORT_CHANNEL.tag:{:},
            # CMD_GET_EXPORT_MODULE.tag:{:},
            # CMD_SET_BATTERY_CONTROL.tag:{:},
            # CMD_GET_BATTERY_CONTROL.tag:{:},
            # CMD_SET_LED_CONTROL.tag:{:},
            # CMD_GET_LED_CONTROL.tag:{:},
            CMD_GET_DEVICE_INFOS.tag:{
                OP_NULL.tag:self.setup.set_sn_from_rx
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
            raise CouldNotWriteToDevice(error)

        
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
            return self.cllbcks[cmd.tag][op.tag]() or [0x00]
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
        # try:
        # print(f'appending to queue {rx_frame}')
        self.rx_buffer.put_nowait(rx_frame)
        # except queue.Full:
        #     self.rx_buffer.get_nowait() #delete oldest
        #     self.rx_buffer.put_nowait(rx_frame) # add the newest...

    def get_last_rx_frame(self):

        try:
            rx_frame=self.rx_buffer.get_nowait()
            # print(f'get from queue {rx_frame}')
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
        self.flag_new_data = False
        cmd_tag= rx_frame[CMD_BYTE_INDX]
        if OP_NULL.tag in self.cllbcks[cmd_tag].keys(): # some answer do not have options (meas, sn)
            op_tag=OP_NULL.tag
        else:
            op_tag= rx_frame[OPTION_BYTE_INDX]
        try:
            if self.cllbcks[cmd_tag][op_tag]:
                self.cllbcks[cmd_tag][op_tag](rx_frame)
                self.flag_new_data = True
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

            
    def is_status_measuring(self)->bool:
        return self.status==StatusSWInterface.MEASURING
    

    ## =========================================================================
    ##  Methods excecuting task on the device
    ## =========================================================================
    

    def buffering_device_infos(self):
        """"""
        return copy.deepcopy(self.setup.device_infos)

    def retitute_device_infos(self,tmp):
        for k in tmp.__dict__.keys():
            print(k)
            setattr(self.setup.device_infos, k, getattr(tmp,k))
        """"""


    def get_available_sciospec_devices(self):
        """Lists the available Sciospec device is available

        Device infos are ask and if an ack is get: it is a Sciospec device..."""
        
        ports=self.interface.get_ports_available()
        self.available_devices = {}
        self.treat_rx_frame_worker.start_polling()
        
        tmp_device_infos = self.buffering_device_infos()
        for port in ports:
            self.interface.open(port)
            self.get_device_infos()
            if not self.rx_ack.is_nack():
                # available_sciospec_devices.append(port)
                device_name = f'Device (SN: {self.setup.get_sn()}) on serial port "{port}"'
                self.available_devices[device_name]=port
            self.interface.close()
        self.treat_rx_frame_worker.stop_polling()
        # print('refresh NOT_CONNECTED')
        self.status=StatusSWInterface.NOT_CONNECTED
        self.retitute_device_infos(tmp_device_infos)

        msg = f'Sciospec devices available: {[k for k in self.available_devices]}'
        logger.info(msg)

        return self.available_devices
        
    def connect_device(self, device_name:str, baudrate=SERIAL_BAUD_RATE_DEFAULT):

        if not self.available_devices:
            raise NoListOfAvailableDevices(
                'Please refresh the list of availables device first, and retry to connect')

        if device_name not in self.available_devices.keys():
            msg= f'Sciospec device "{device_name}" - NOT FOUND'
            logger.warning(msg)
            raise CouldNotFindPortInAvailableDevices(
                f'Please reconnect your device, and retry ({msg})')
        
        self.treat_rx_frame_worker.start_polling()
        port= self.available_devices[device_name]
        self.interface.open(port, baudrate)
        self.get_device_infos()               
        self.status_prompt= f'Device (SN: {self.setup.get_sn()}) on serial port "{self.interface.get_actual_port_name()}" (b:{self.interface.get_actual_baudrate()} d:8 s:1 p:None) - CONNECTED'
        logger.info(self.status_prompt)

    def disconnect_device(self):
        """" Disconnect the device"""
        if self.is_status_measuring():
            raise MeasurementsRunningError('Please stop first the measurements')
        self.treat_rx_frame_worker.stop_polling()
        msg=f'Device (SN: {self.setup.get_sn()}) on serial port "{self.interface.get_actual_port_name()}" - DISCONNECTED'
        self.interface.close()
        logger.info(msg)
        self.init_device()
        self.get_available_sciospec_devices() # update the list of Sciospec devices available ????

    def get_device_infos(self):
        """Ask for the serial nummer of the Device """
        if self.is_status_measuring():
            raise MeasurementsRunningError('Please stop first the measurements')
        self._send_cmd_frame(CMD_GET_DEVICE_INFOS, OP_NULL)
        self.wait_until_not_busy()


    def start_meas(self, name_measurement:str='default_meas_name'):
        """ Start measurements """
        if self.is_status_measuring():
            raise MeasurementsRunningError('Please stop first the measurements')
        name, output_dir =self._prepare_dataset(name_measurement)
        self._send_cmd_frame(CMD_START_STOP_MEAS, OP_START_MEAS)
        self.wait_until_not_busy()
        return name, output_dir

    def stop_meas(self, append=True):
        """ Stop measurements """
        self._send_cmd_frame(CMD_START_STOP_MEAS, OP_STOP_MEAS, cmd_append=append)
        self.wait_until_not_busy()
        # self.flagMeasRunning = False

    def set_setup(self):
        """ Send the setup to the device """
        if self.is_status_measuring():
            raise MeasurementsRunningError('Please stop first the measurements')
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
        if self.is_status_measuring():
            raise MeasurementsRunningError('Please stop first the measurements')
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
        if self.is_status_measuring():
            raise MeasurementsRunningError('Please stop first the measurements')
        self._send_cmd_frame(CMD_SOFT_RESET,OP_NULL)
        self.wait_until_not_busy()
        raise SWReset('please reconnect')


    # ## =========================================================================
    # ##  Methods relative to loading and saving setups of the device
    # ## =========================================================================
    def saveSetupDevice(self, file):
        self.setup.saveSetupDevice(file)
        
    def loadSetupDevice(self, file):
        self.setup.loadSetupDevice(file)


## ======================================================================================================================================================
##  Class for the DataSet obtained from the EIT Device
## ======================================================================================================================================================

class EitMeasurementDataset(object):
    """ Class EITDataSet: regroups infos and frames of measurements """
    def __init__(self):
        self.date_time= None
        self.name= None
        self.output_dir=None
        self.dev_setup=None
        self.frame_cnt=None
        self.frame=None
        self._last_frame=None
        self.freqs_list= None
        self._frame_TD_ref=None

    def init_for_gui(self,dev_setup:SciospecSetup= SciospecSetup(32), name_measurement:str=None):
        # self.date_time= get_date_time()
        self.name= name_measurement#append_date_time(name_measurement, self.date_time)
        self.output_dir=None #mk_ouput_dir(self.name, default_out_dir=MEAS_DIR)
        self.dev_setup= dev_setup
        self.frame_cnt=0
        self.frame=[EITFrame(dev_setup)]
        self._last_frame=[EITFrame(dev_setup)]
        self.freqs_list= dev_setup.make_freqs_list()
        self._frame_TD_ref=[EITFrame(dev_setup)]
        return self.name, self.output_dir
    def prepare_for_aquisition(self,dev_setup:SciospecSetup, name_measurement:str=None):
        self.date_time= get_date_time()
        self.name= append_date_time(name_measurement, self.date_time)
        self.output_dir=mk_ouput_dir(self.name, default_out_dir=MEAS_DIR)
        self.dev_setup= dev_setup
        self.frame_cnt=0
        self.frame=[EITFrame(dev_setup)]
        self._last_frame=[EITFrame(dev_setup)]
        self.freqs_list= dev_setup.make_freqs_list()
        self._frame_TD_ref=[EITFrame(dev_setup)]
        return self.name, self.output_dir
    
    def add_rx_frame_to_dataset(self, rx_frame):
        """ add the data from the rx_frame in the dataset 
        (is called when measuring rx_frame have been recieved)"""

        idx= 0
        data =self.extract_data(rx_frame)
        # self.append(frame, idx_frm=0)
        self.frame[idx].add_data(data,self.frame_cnt)
        # if frame complete Frame_cnt+ and append new Frame
        if self.frame[idx].is_complete():
            self.frame_save_and_prepare_for_next_rx(idx)

    def frame_save_and_prepare_for_next_rx(self, idx:int=0):
        self.make_info_text_for_frame(idx)
        self.save_frame()
        self._last_frame[0]=self.frame[idx] # latch actual to the _last_frame
        if self.frame_cnt == 0:
            self.set_frame_TD_ref(idx) # init the reference frame for Time difference measurement
        self.frame[idx]=EITFrame(self.dev_setup) # clear frame 
        self.frame_cnt += 1

    def extract_data(self,rx_frame):
        """extract the single data out of the rx_frame, convert them if applicable
        return them as a dict"""
        data={}
        rx_data= rx_frame[OPTION_BYTE_INDX:-1]
        data['ch_group']= rx_data[0]
        excitation=rx_data[1:3]
        data['exc_indx']= self._find_excitation_indx(excitation)
        data['freq_indx']= convertBytes2Int(rx_data[3:5])
        data['time_stamp']= convertBytes2Int(rx_data[5:9]) 
        data['voltages'] = self.convert_meas_data(rx_data[9:])
        return data

    def convert_meas_data(self, meas_data):
        """return float voltages values () corresponding to meas data (bytes single float) """
        n_bytes_real_imag= 4 # we got 4Bytes per value
        meas_data=np.reshape(np.array(meas_data), (-1, n_bytes_real_imag)) # reshape the meas data in lock of 4 bytes
        meas_data=meas_data.tolist() # back to list for conversion
        meas_f=[convert4Bytes2Float(m)for m in meas_data] # conversion of each 4 bytes
        meas_r_i=np.reshape(np.array(meas_f), (-1,2)) # get a matrix with real and imag values in each column
        return meas_r_i[:,0]+1j*meas_r_i[:,1]

    def set_frame_TD_ref(self, indx=0, path=None):
        """ Latch Frame[indx] as reference for time difference mode
        """
        if path is None:
            self._frame_TD_ref[0] = self._last_frame[0] if indx==0 else self.frame[indx]
        else:
            dataset_tmp=self.load_single_frame(path)
            self._frame_TD_ref[0]=dataset_tmp.Frame[0]
    

    def save_frame(self):
        filename= os.path.join(self.output_dir, f'Frame{self.frame_cnt:02}')
        save_as_pickle(filename, self)

    def saveSingleFrame(self,file_path):
        """ Save single Frame to a .dat-file
        Parameters
        ----------
        file_path: str
            path of file without ending
        
        Notes
        -----
        - such files can not be read..."""
        ## maybe create a text_format of the dataset to save it as a txt-file
        with open(file_path + '.dat', "wb") as fp:   #Pickling
            pickle.dump(self, fp)

    def load_single_frame(self, file_path):
        """Load Dataset file (.dat)

        Parameters
        ----------
        file_path: str  path of file

        Returns
        -------
        dataset: "EITDataSet" object
        
        Notes
        -----
        - such files can not be read..."""
        ## maybe create a text_format of the dataset to load it as a txt-file
        with open(file_path, "rb") as fp:   # Unpickling
            return pickle.load(fp)
    
    

    def extract(self):
        pass

    def LoadDataSet(self, dirpath):
        """Load Dataset files (.dat)

        Parameters
        ----------
        dirpath: str
            directory path of of the dataset

        Returns
        -------
        only_files_ list of str
            list of filename (), error
        error: 1 if no frame files found, 2 if dirpath not given (canceled), 0 if everything loaded """
        # only_files=[]
        # error = 0

        only_files, error =search4FileWithExtension(dirpath, ext=EXT_PKL)
        if not error: # if no files are contains
            dataset_tmp=EitMeasurementDataset(dirpath)
            for i,filename in enumerate(only_files): # get all the frame data
                frame_path=dirpath+os.path.sep+filename
                dataset_tmp=self.load_single_frame(frame_path)
                if i ==0: 
                    self.output_dir=dataset_tmp.output_dir
                    self.name= dataset_tmp.name
                    self.date_time= dataset_tmp.dateTime
                    self.dev_setup= dataset_tmp.dev_setup
                    self.frame=[] # reinit frame
                    self.frame_cnt=len(only_files)
                    self.freqs_list= dataset_tmp.frequencyList
                    self._frame_TD_ref= []
                    self._frame_TD_ref.append(dataset_tmp.Frame[0])
                self.frame.append(dataset_tmp.Frame[0])
                self.frame[-1].loaded_frame_path= frame_path
                self.make_info_text_for_frame(i)

        return only_files, error

    def _find_excitation_indx(self, excitation):
        """ Return the index of the given excitation in the excitation_Pattern

        Parameters
        ----------
        excitation: list of int (e.g. [1, 2])

        Returns
        -------
        indx: int
            index of the given excitation in self.dev_setup.excitation_Pattern """
        indx = 0
        for Exc_i in self.dev_setup.get_exc_pattern():
            if Exc_i== excitation:
                break
            indx += 1
        return indx

    def make_info_text_for_frame(self, indx):
        """ Create a tex with information about the Frame nb indx
        
        Parameters
        ----------
        indx: int
            index of the frame
        
        Notes
        -----
        save the text under Frame[indx].infoText """
        frame = self.frame if indx==-1 else self.frame[indx]
        frame.info_text= [ f"Dataset name:\t{self.name}",
                    f"Frame#:\t{frame.idx}",
                    f"TimeStamps:\t{self.date_time}",
                    f"Sweepconfig:\tFmin = {self.dev_setup.get_freq_min()/1000:.3f} kHz,\r\n\tFmax = {self.dev_setup.get_freq_max()/1000:.3f} kHz",
                    f"\tFSteps = {self.dev_setup.get_freq_steps():.0f},\r\n\tFScale = {self.dev_setup.get_freq_scale()}",
                    f"\tAmp = {self.dev_setup.get_exc_amp():.5f} A,\r\n\tFrameRate = {self.dev_setup.get_frame_rate():.3f} fps",
                    f"excitation:\t{self.dev_setup.get_exc_pattern()}"]
        

class EITFrame(object):
    """ Class Frame: regroup the voltages values for all frequencies at timestamps
    for all excitation and for one frequency

    Notes
    -----
    e.g. Meas[2] the measured voltages on each channel (VS a commmon GROUND) for the frequency_nb 2
            for the frequency = frequency_val"""
    def __init__(self, dev_setup:SciospecSetup):
        self.time_stamp=0 
        self.idx= 0
        self.freqs_list= dev_setup.make_freqs_list()
        self.freq_steps= dev_setup.get_freq_steps()
        self.meas_frame_nb=len(dev_setup.get_exc_pattern())*2 # for x excitation x*2 meas are send
        self.meas_frame_cnt=0 # cnt 
        self.meas=[EITMeas(dev_setup) for i in range(self.freq_steps)] # Meas[Frequency_indx]
        self.info_text=''
        self.loaded_frame_path=''
    
    def set_freq(self, data):
        """ set the frequence value in the corresponding Measuremeent object """
        self.meas[data['freq_indx']].set_freq(self.freqs_list[data['freq_indx']])

    def add_voltages(self, data):
        self.meas[data['freq_indx']].add_voltages(data)

    def is_complete(self):
        """return if teh frame is complete"""
        return self.meas_frame_cnt == self.meas_frame_nb

    def set_time_stamp(self, data):
        """ not defined"""
        # if data['ch_group']==1:
        #     self.time_stamp= data['time_stamp']
        # elif self.time_stamp != data['time_stamp']:
        #     raise Exception(f'time_stamp error expected {self.time_stamp}, rx: {data["time_stamp"]}')

    def add_data(self, data:dict, frame_cnt:int):
        """ add rx data to this frame"""
        if self.is_very_first_data(data):
            self.idx= frame_cnt
        self.set_time_stamp(data)
        self.set_freq(data)
        self.add_voltages(data)
        if self.is_all_freqs_aquired(data):
            self.meas_frame_cnt += 1

    def is_very_first_data(self, data):
        """retrun if data is the very first one for this frame"""
        return data['ch_group']+data['freq_indx']+data['exc_indx']==1

    def is_all_freqs_aquired(self, data):
        """return if all meas for all freqs were aquired for this frame"""
        return data['freq_indx'] == self.freq_steps - 1

class EITMeas(object):
    """ Class measurement: regroup the voltage values of all channels of the EIT device
    for all excitation and for one frequency

    Notes
    -----
    e.g. voltage_Z[1][:] the measured voltages on each channel (VS a commmon GROUND) for excitation 1
            for the frequency = frequency_val"""
    def __init__(self, dev_setup:SciospecSetup):
        self.voltage_Z=[np.zeros(dev_setup.get_channel()) for j in range(len(dev_setup.get_exc_pattern()))]
        # self.voltage_Z=[[0 for i in range(dev_setup.get_channel())] for j in range(len(dev_setup.get_exc_pattern()))]
        self.frequency=None # corresponding excitation frequency

    def set_freq(self, freq_val):
        """set the frequency value for the actual measurements"""
        self.frequency=freq_val
    def add_voltages(self, data):
        """add rx voltage to the voltages matrix"""
        n_ch_meas_per_frame= 16
        ch_group=data['ch_group']
        exc_indx=data['exc_indx']
        volt = data['voltages']
        n_ch_meas_per_frame=16
        if volt.shape[0] != n_ch_meas_per_frame:
            raise Exception(f'n_ch_meas_per_frame :{n_ch_meas_per_frame} is not correct {volt.shape[0]} voltages recieved' )
        start_idx=(ch_group-1)*n_ch_meas_per_frame
        end_idx=(ch_group)*n_ch_meas_per_frame
        self.voltage_Z[exc_indx][start_idx:end_idx]= volt


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

