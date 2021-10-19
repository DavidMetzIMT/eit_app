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
from typing import List

import numpy as np
import pandas as pd
from matplotlib.pyplot import tick_params
import pickle
from os import listdir
from os.path import isfile, join

from eit_app.eit.model import *
from eit_app.io.sciospec.com_constants import *
from eit_app.io.sciospec.hw_serial_interface import SerialInterface, SERIAL_BAUD_RATE_DEFAULT, SerialInterfaceError
from eit_app.threads_process.threads_worker import HardwarePoller
from eit_app.utils.log import main_log
from eit_app.utils.utils_path import get_date_time
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
    NOT_CONNECTED=enum.auto()
    IDLE=enum.auto()
    MEASURING=enum.auto()
    WAIT_FOR_DEVICE_ANSWER=enum.auto()


class SWInterfaceError(Exception):
    """ Custom Error for SoftWare Interface of a Device"""

class CouldNotWriteToDevice(Exception):
    """ Custom Error """

class CouldNotFindPortInAvailableDevices(Exception):
    """ Custom Error e"""

class NoListOfAvailableDevices(Exception):
    """ Custom Error e"""

class SWInterfaceTimeOutError(Exception):
    """ Custom: error"""
class SWInterfaceSWResetError(Exception):
    """ Custom: error"""


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
    def __init__(self, paths, verbose=False):
        
        self.verbose=verbose # for debugging
        self.paths= paths
        self.treat_rx_frame_worker=HardwarePoller('treat_rx_frame',self.get_last_rx_frame,0.01)
        self.treat_rx_frame_worker.start()
        

        self.init_device()

    def init_device(self):
        """ init the """
        self.channel = 32
        self.interface= SerialInterface(self.verbose) # the serial interface is set outside this class (e.g. in the app_backend)
        self.interface.register_callback(self.append_to_rx_buffer)
        self.setup= SciospecSetup(self.channel)
        self.log=[]
        # self.add2Log('INIT: Device object created')
        self.status=StatusSWInterface.NOT_CONNECTED
        self.status_prompt = NO_DEVICE_CONNECTED_PROMPT

        self.dataset:EITDataSet=None
        self._init_dataset()
        self.flag_new_data=False
        self.flagMeasRunning= False
        self.available_devices = {}
        self.rx_buffer= queue.Queue(maxsize=256) # infine queue.... maybe handle only a certain number of data to reduce memory allocttions???
        self.cmds_history= []
        self.answer_buffer=queue.Queue(maxsize=16)
        
        self.make_callbacks_catalog()
        # self.status_com_is_busy= False
        if self.verbose:
            print('Start: __init__ Device')
    
    def _init_dataset(self):
        self.dataset=EITDataSet(self.paths[1])


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
                OP_NULL.tag:self.dataset.addRxData2DataSet#,
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
    
        while self.status==StatusSWInterface.WAIT_FOR_DEVICE_ANSWER:
            pass
    # def setDataSet(self,dataset):
    #     """ Link the dataset to use during measurement
        
    #     Parameters
    #     ----------
    #     dataset: "EITDataSet" object connected to the hardware"""
    #     self.dataset = dataset # actual dataset with one frame

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
        if cmd_append:
            self._append_last_sended_cmd(cmd)
        cmd_frame = self._make_command_frame(cmd, op)

        try:
            self.interface.write(cmd_frame)
            logger.debug(f'Send cmd "{cmd.name}", op: "{op.name}", cmd_frame :{cmd_frame}')
        except SerialInterfaceError as error:
            self._clear_last_cmd_history()
            raise CouldNotWriteToDevice(error)
        
    def _append_last_sended_cmd(self, cmd:SciospecCmd):
        self.cmds_history.append(cmd)
        self.status=StatusSWInterface.WAIT_FOR_DEVICE_ANSWER
        
    def _clear_oldest_cmd(self)-> SciospecCmd:
        return self.cmds_history.pop(0)
   
    def _clear_cmd_history(self):
        self.cmds_history.clear()
    
    def _clear_last_cmd_history(self)->SciospecCmd:
        return self.cmds_history.pop(-1)
        
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
            self._sort_frame(rx_frame)
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
            raise  SWInterfaceError(f'The length of rx_frame: {rx_frame} is < 4')# should never be raised
        
    def _sort_frame(self,rx_frame:List[bytes]):
        """ Sort the recieved frames between ACKNOWLEGMENT and ANSWERS

        in case of Ack, the option_byte of the RX_Ack is check and the rx_ack is save in the log
        in case of Messages, the rx_msg is save in the log and te rx_frame is further treated 

        Parameters
        ----------
        rx_frame: list of int8 (byte)"""
        # print(f'sorting {rx_frame}')
        answer, oldest_cmd= [], []
        if self._check_is_ack(rx_frame): # if rx_frame is an ACKNOWLEGMENT decide to do sth             
            answer, oldest_cmd= self.treat_rx_ack(rx_frame)
        else: # # if rx_frame is a MSG decide dispatch data.
            answer = self.treat_rx_answer(rx_frame)

        self._extract_answer(answer)
        self._update_status(oldest_cmd)

    def _check_is_ack(self,rx_frame:List[bytes]):
        """ look for the Ack corresponding to the given rx_ack_byte  
        
        Parameters
        ----------
        x_ack_byte: int8
        
        Returns
        -------
        rx_ack : SciospecAck object
            recieved Acknoledgement     """
       
        tmp=rx_frame[:]
        tmp[OPTION_BYTE_INDX]=0
        # print(f'ack check {rx_frame}, {is_ack}')

        return tmp==ACK_FRAME

    def treat_rx_ack(self, rx_frame):
        self.rx_ack= NONE_ACK
        for ack_i in ACK:
            if ack_i.ack_byte==rx_frame[OPTION_BYTE_INDX]:
                self.rx_ack= ack_i
                break

        if self.rx_ack.is_error():
            msg=f'NACK RX: {self.rx_ack.__dict__} - nothing implemented yet, to handle it!!!'
            logger.error(msg)
            # self._clear_oldest_cmd()
            # todo >> determine what to do when is not sucesfull log? retry? 
            raise  SWInterfaceError(msg)
        else:
            oldest_cmd= self._clear_oldest_cmd()
            answer=self._get_odldest_msg_from_buffer()
            if oldest_cmd.answer_type==Answer.WAIT_FOR_ANSWER_AND_ACK:
                msg=f'ACK RX: {self.rx_ack.name} of ANSWER {answer} from CMD {oldest_cmd.name}- SUCCESS'
            elif oldest_cmd.answer_type==Answer.WAIT_FOR_ACK:
                msg= f'ACK RX: {self.rx_ack.name} for CMD {oldest_cmd.name} - SUCCESS'
            logger.info(msg)
            return answer, oldest_cmd

    def treat_rx_answer(self, answer):
        msg=f'ANSWER RX: {answer[:10]}, {self.status==StatusSWInterface.MEASURING}'
        logger.info(msg)
        return self.sort_answer(answer)
        # answer= []
        # if self.status==StatusSWInterface.MEASURING: 
        #     answer=rx_frame # that should ne done if ack is true... maybe use a buffer???
        # else:
        #     self._put_last_answer_to_buffer(rx_frame)
        # return answer

    def sort_answer(self,answer):
        meas= []
        
        if answer[CMD_BYTE_INDX] == CMD_START_STOP_MEAS.tag:# if a measurement self.status==StatusSWInterface.MEASURING: 
            meas=answer # that should ne done if ack is true... maybe use a buffer???
        else:
            self._put_last_answer_to_buffer(answer)
        return meas

    def _update_status(self, oldest_cmd:SciospecCmd):
            
        if not self.cmds_history and oldest_cmd:
            if oldest_cmd.tag == CMD_START_STOP_MEAS.tag:
                self.status=StatusSWInterface.MEASURING
            else:
                self.status=StatusSWInterface.IDLE

    def _extract_answer(self, rx_frame:List[bytes]):
        """ Extract the data from rx_frame and save them to the right place regading the cllbcks catalog 
        
        Parameters
        ----------
        rx_frame: list of int8 (byte)

        Notes
        -----
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
                msg=f'ANSWER RX: {rx_frame} -  TREATED'
                logger.debug(msg)
        except KeyError:
            cmd=get_cmd(cmd_tag)
            op=get_op(cmd.options, op_tag)
            msg= f'Combination of Cmd:"{cmd.name}"({cmd.tag})/ Option:"{op.name}"({op.tag}) - NOT FOUND in callbacks catalog'
            logger.error(msg)
            raise  SWInterfaceError(msg)
            
        except TypeError as error:
            logger.error(error)    
    def _put_last_answer_to_buffer(self, msg):
        self.answer_buffer.put(msg)

    def _get_odldest_msg_from_buffer(self):
        try:
            return self.answer_buffer.get_nowait()
        except queue.Empty: # if empty then return empty ....
            return []



    ## =========================================================================
    ##  Methods excecuting task on the device
    ## =========================================================================
    
    def get_available_sciospec_devices(self):
        """Lists the available Sciospec device is available

        Device infos are ask and if an ack is get: it is a Sciospec device..."""
        
        ports=self.interface.get_ports_available()
        self.available_devices = {}
        self.treat_rx_frame_worker.start_polling()
        for port in ports:
            self.interface.open(port)
            self.get_device_infos()
            if not self.rx_ack.is_error():
                # available_sciospec_devices.append(port)
                device_name = f'Device (SN: {self.setup.get_sn()}) on serial port "{port}"'
                self.available_devices[device_name]=port
            self.interface.close()
        self.treat_rx_frame_worker.stop_polling()
        # print('refresh NOT_CONNECTED')
        self.status=StatusSWInterface.NOT_CONNECTED

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
        self.stop_meas(append=False)
        self.interface.clear_unwanted_rx_frames()
        self.get_device_infos()               
        self.status_prompt= f'Device (SN: {self.setup.get_sn()}) on serial port "{self.interface.get_actual_port_name()}" (b:{self.interface.get_actual_baudrate()} d:8 s:1 p:None) - CONNECTED'
        logger.info(self.status_prompt)

    def disconnect_device(self):
        """" Disconnect the device"""
        self.treat_rx_frame_worker.stop_polling()
        msg=f'Device (SN: {self.setup.get_sn()}) on serial port "{self.interface.get_actual_port_name()}" - DISCONNECTED'
        self.interface.close()
        logger.info(msg)
        self.init_device()
        self.get_available_sciospec_devices() # update the list of Sciospec devices available ????

    def get_device_infos(self):
        """Ask for the serial nummer of the Device """
        self._send_cmd_frame(CMD_GET_DEVICE_INFOS, OP_NULL)
        self.wait_until_not_busy()

    def start_meas(self):
        """ Start measurements """
        # self.dataset.initDataSet(self.setup, path) ## Prepare the Dataset
        self._send_cmd_frame(CMD_START_STOP_MEAS, OP_START_MEAS)
        self.wait_until_not_busy()
        self.flagMeasRunning= True

    def stop_meas(self, append=True):
        """ Stop measurements """
        self._send_cmd_frame(CMD_START_STOP_MEAS, OP_STOP_MEAS, cmd_append=append)
        self.wait_until_not_busy()
        self.flagMeasRunning = False

    def set_setup(self):
        """ Send the setup to the device """
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
        for self.setup.exc_pattern_idx in range(len(self.setup.exc_pattern)):
            self._send_cmd_frame(CMD_SET_MEAS_SETUP, OP_EXC_PATTERN)
        self.wait_until_not_busy()

    def get_setup(self):
        """ Get the setup of the device """
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
        self._send_cmd_frame(CMD_SOFT_RESET,OP_NULL)
        self.wait_until_not_busy()
        raise SWInterfaceSWResetError('please reconnect')

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

class EITDataSet(object):
    """ Class EITDataSet: regroups infos and frames of measurements """
    def __init__(self, path):
        self.initDataSet(SciospecSetup(32), path)
        
    def initDataSet(self, dev_setup:SciospecSetup=SciospecSetup(32), path:str=None):
        self.output_dir=path
        self.name= path[path.rfind(os.path.sep)+1:]
        self.dateTime= get_date_time()
        self.dev_setup= dev_setup
        self.Frame_cnt=0
        self.Frame=[EITFrame(dev_setup)]
        self._last_frame=[EITFrame(dev_setup)]
        self.frequencyList= dev_setup.freq_config.mkFrequencyList()
        self._FrameRef4TD=[EITFrame(dev_setup)]
    
    def addRxData2DataSet(self, rx_data):
        """ convert and add the recieved data to the dataset

        Parameters
        ----------
        rx_data: list of int8  containing:
            [ch_group, excitation+, excitation-, freq_indx_msb, freq_indx_lsb,
            time_stamp_msb, time_stamp_2, time_stamp_1, time_stamp_lsb,
            [real ch1], [imag ch1], ...., [real ch32], [imag ch32]]
        
            where [real ch_i] and [imag ch_i] are single float format (4 Bytes)

        Notes
        -----
        - see documentation of the EIT device    """

        # extraxt and convert rx_data in the dataset
        # print(rx_data)
        ch_group= rx_data[0]
        excitation=rx_data[1:3]
        exc_indx= self._find_excitation_indx(excitation)
        freq_indx= convertBytes2Int(rx_data[3:5])
        time_stamp= convertBytes2Int(rx_data[5:9]) #not used...
 
        u= rx_data[9:]
        n_bytes_real_imag= 4 # we got 4Bytes per value
        voltages_Z=[0] * 32
        # maybe a faster sorting algorithem could be implemented....
        for i in range(16): # the channel voltage meas. come per 16 packages: group1 1-16; group2 17-32
            indx= 2*n_bytes_real_imag*i
            ch= i+(ch_group-1)*16
            voltages_Z[ch]=convert4Bytes2Float(u[indx:indx+n_bytes_real_imag]) + 1j*convert4Bytes2Float(u[indx+n_bytes_real_imag:indx+2*n_bytes_real_imag])
        
        # sort rx_data in the dataset
        
        self.Frame[0].Meas[freq_indx].frequency= self.frequencyList[freq_indx]
        # add the voltages without writing over the old data (in the case of group 2)
        tmp= self.Frame[0].Meas[freq_indx].voltage_Z[exc_indx] 
        self.Frame[0].Meas[freq_indx].voltage_Z[exc_indx]= np.add(tmp, voltages_Z)

        if False:
            print(self.Frame_cnt, freq_indx)
            print(self.Frame.Meas[freq_indx].frequency)
            print(self.Frame.Meas[freq_indx].voltage_real)

        if freq_indx == self.dev_setup.freq_config.steps - 1: 
            self.Frame[0].Meas_frame_cnt += 1 # will be increment 2*excitation_nb times at same freq_indx
        
        # if frame complete Frame_cnt++ and append new Frame      
        if self.Frame[0].Meas_frame_cnt == self.Frame[0].Meas_frame_num:
            self.Frame[0].Frame_indx =  self.Frame_cnt # latch actual frame_cnt to the frame
            self.mkInfoText4Frame(0)
            self.saveSingleFrame(self.output_dir + os.path.sep+f'Frame{self.Frame_cnt:02}') # save dataset with one Frame
            self._last_frame[0]=self.Frame[0] # latch actual to the _last_frame
            if self.Frame_cnt == 0:
                self.setFrameRef4TD(0) # set automaticaly the reference frame fro TimeDiff measurement
            self.Frame=[EITFrame(self.dev_setup)]
            self.Frame_cnt += 1
            
    def setFrameRef4TD(self, indx=0, path=None):
        """ Latch Frame[indx] as reference for time difference mode
        """
        if path is None:
            self._FrameRef4TD[0] = self._last_frame[0] if indx==0 else self.Frame[indx]
        else:
            dataset_tmp=self.loadSingleFrame(path)
            self._FrameRef4TD[0]=dataset_tmp.Frame[0]

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

    def loadSingleFrame(self, file_path):
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
    
    def search4FileWithExtension(self,dirpath, ext='.dat'):

        only_files=[]
        error = 0
        try:
            only_files = [f for f in listdir(dirpath) if isfile(join(dirpath, f)) and f[-len(ext):]==ext]
            if not only_files: # if no files are contains
                error = 1
        except (FileNotFoundError, TypeError): #cancel loading
            pass

        return only_files, error

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

        only_files, error =self.search4FileWithExtension(dirpath, ext='.dat')
        if not error: # if no files are contains
            dataset_tmp=EITDataSet(dirpath)
            for i,filename in enumerate(only_files): # get all the frame data
                frame_path=dirpath+os.path.sep+filename
                dataset_tmp=self.loadSingleFrame(frame_path)
                if i ==0: 
                    self.output_dir=dataset_tmp.output_dir
                    self.name= dataset_tmp.name
                    self.dateTime= dataset_tmp.dateTime
                    self.dev_setup= dataset_tmp.dev_setup
                    self.Frame=[] # reinit frame
                    self.Frame_cnt=len(only_files)
                    self.frequencyList= dataset_tmp.frequencyList
                    self._FrameRef4TD= []
                    self._FrameRef4TD.append(dataset_tmp.Frame[0])
                self.Frame.append(dataset_tmp.Frame[0])
                self.Frame[-1].loaded_frame_path= frame_path
                self.mkInfoText4Frame(i)


        # try:
        #     only_files = [f for f in listdir(dirpath) if isfile(join(dirpath, f)) and f[-4:]=='.dat']
        #     if not only_files: # if no files are contains
        #         error = 1
        #     else:
        #         dataset_tmp=EITDataSet(dirpath)
        #         for i,filename in enumerate(only_files): # get all the frame data
        #             frame_path=dirpath+os.path.sep+filename
        #             dataset_tmp=self.loadSingleFrame(frame_path)
        #             if i ==0: 
        #                 self.output_dir=dataset_tmp.output_dir
        #                 self.name= dataset_tmp.name
        #                 print(self.name, self.output_dir)
        #                 self.dateTime= dataset_tmp.dateTime
        #                 self.dev_setup= dataset_tmp.dev_setup
        #                 self.Frame=[] # reinit frame
        #                 self.Frame_cnt=len(only_files)
        #                 self.frequencyList= dataset_tmp.frequencyList
        #                 self._FrameRef4TD= []
        #                 self._FrameRef4TD.append(dataset_tmp.Frame[0])
        #             self.Frame.append(dataset_tmp.Frame[0])
        #             self.Frame[-1].loaded_frame_path= frame_path
        #             self.mkInfoText4Frame(i)
        # except (FileNotFoundError, TypeError): #cancel loading
        #     error = 2

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
        for Exc_i in self.dev_setup.exc_pattern:
            if Exc_i== excitation:
                break
            indx= indx+1
        return indx

    def mkInfoText4Frame(self, indx):
        """ Create a tex with information about the Frame nb indx
        
        Parameters
        ----------
        indx: int
            index of the frame
        
        Notes
        -----
        save the text under Frame[indx].infoText """
        if indx==-1:
            frame=self.Frame
        else:
            frame=self.Frame[indx]

        frame.infoText= [ f"Dataset name:\t{self.name}",
                    f"Frame#:\t{frame.Frame_indx}",
                    f"TimeStamps:\t{self.dateTime}",
                    f"Sweepconfig:\tFmin = {self.dev_setup.freq_config.min_freq_Hz/1000:.3f} kHz,\r\n\tFmax = {self.dev_setup.freq_config.max_freq_Hz/1000:.3f} kHz",
                    f"\tFSteps = {self.dev_setup.freq_config.steps:.0f},\r\n\tFScale = {self.dev_setup.freq_config.scale}",
                    f"\tAmp = {self.dev_setup.exc_amp:.5f} A,\r\n\tFrameRate = {self.dev_setup.frame_rate:.3f} fps",
                    f"excitation:\t{self.dev_setup.exc_pattern}"]
        

class EITFrame(object):
    """ Class Frame: regroup the voltages values for all frequencies at timestamps
    for all excitation and for one frequency

    Notes
    -----
    e.g. Meas[2] the measured voltages on each channel (VS a commmon GROUND) for the frequency_nb 2
            for the frequency = frequency_val"""
    def __init__(self, setup:SciospecSetup):
        self.Frame_timestamps=0
        self.Frame_indx= 0
        self.Meas_frame_num=len(setup.exc_pattern)*2 # for x excitation x*2 meas are send
        self.Meas_frame_cnt=0 # cnt 
        self.Meas=[EITMeas(setup) for i in range(setup.freq_config.steps)] # Meas[Frequency_indx]
        self.infoText=''
        self.loaded_frame_path=''
    

class EITMeas(object):
    """ Class measurement: regroup the voltage values of all channels of the EIT device
    for all excitation and for one frequency

    Notes
    -----
    e.g. voltage_Z[1][:] the measured voltages on each channel (VS a commmon GROUND) for excitation 1
            for the frequency = frequency_val"""
    def __init__(self, setup:SciospecSetup):
        ch=setup.device_infos.channel
        self.voltage_Z=[[0 for i in range(ch)] for j in range(len(setup.exc_pattern))]
        self.frequency=0 # corresponding excitation frequency


if __name__ == '__main__':

    main_log()

    dev= SWInterface4SciospecDevice(['', ''])
    dev.get_available_sciospec_devices()
    dev.connect_device('Device (SN: 01-0019-0132-0A0C) on serial port "COM3"')
    dev.get_setup()
    dev.start_meas()
    time.sleep(5)
    dev.stop_meas()

    # print(dev.setup.get_exc_stamp(),dev.setup.get_current_stamp(), dev.setup.get_time_stamp())
    # dev.set_setup()

    # dev.software_reset()
    # time.sleep(10)
    # dev.get_setup()
    dev.disconnect_device()

    pass
