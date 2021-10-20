#!C:\Anaconda3\envs\py38_app python
# -*- coding: utf-8 -*-

"""  CONSTANTS to interact with the Sciospec EIT device

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
along with this program.  If not, see <https://www.gnu.org/licenses/>. 

Notes
-----
- see documentation of the EIT device for more details

"""
from enum import Enum, auto
from typing import List
import numpy as np
from eit_app.io.sciospec.utils import *
import pandas as pd
import ast

__author__ = "David Metz"
__copyright__ = "Copyright (c) 2021"
__credits__ = ["David Metz"]
__license__ = "GPLv3"
__version__ = "2.0.0"
__maintainer__ = "David Metz"
__email__ = "d.metz@tu-bs.de"
__status__ = "Production"

################################################################################
##  Diverse CONSTANTS for Sciopec device #######################################
################################################################################

FRAME_LENGTH_MIN = 4
CMD_BYTE_INDX = 0
LENGTH_BYTE_INDX = 1
OPTION_BYTE_INDX = 2
DATA_START_INDX = 3
LENGTH_SERIAL_NUMBER =7
LENGTH_IP_ADRESS = 4 
LENGTH_MAC_ADRESS = 6

DELAY_BTW_2FREQ = 42 * 10**-6 # in s
MIN_SAMPLING_TIME =208 * 10**-6 # in s
DELAY_BTW_2INJ = 651 * 10**-6 # in s
UPPER_LIMIT_FRAME_RATE = 100 # in fps

class Answer(Enum):
    IDLE=auto()
    WAIT_FOR_ANSWER_AND_ACK=auto()
    WAIT_FOR_ACK=auto()
    IDLE_MEAS=auto() #do not wait for ackno

class CmdTypes(Enum):
    simple=auto()
    set_w_option=auto()
    get_w_option=auto()


################################################################################
##  Class of commands and options for the Sciospec device #######################
################################################################################

class SciospecCmd(object):
    """ CMD : command structure description:
            name: str
            tag_byte: CMD Byte
            type: 0 simple set/get/ask command without option
            1 set command with options
            2 get command with options"""
    def __init__(self, name='', tag_byte= 0x00, type=CmdTypes.simple, answer_type=Answer.IDLE):
        self.name: str = name
        self.tag: bytes = tag_byte
        self.type: int = type
        self.answer_type = answer_type
        self.options=[]
    def set_options(self, options:list=[]):
        self.options=options


class SciospecOption(object):
    """ OP: Option structure description:
            name: str 
            tag: OB Byte
            LL_byte: 
                length_byte[0] lenght Byte for set command with options
                length_byte[1] lenght Byte for get command with options """
    def __init__(self, name='', option_byte= 0x00, length_byte=[0x00,0x00]):
        self.name: str = name
        self.tag: bytes = option_byte
        self.LL_bytes: bytearray = length_byte
        
################################################################################
##  Commands and options CONSTANTS for the Sciospec device######################
################################################################################       

## -----------------------------------------------------------------------------
## Save Settings - 0x90
CMD_SAVE_SETTINGS           = SciospecCmd('CMD_Save_Settings',0x90,CmdTypes.simple, Answer.WAIT_FOR_ACK)
# Options for "Save_Settings"
OP_NULL                     = SciospecOption('OP_Null',0x00, [0x00,0x00])
CMD_SAVE_SETTINGS.set_options([OP_NULL])

## -----------------------------------------------------------------------------
## Software Reset - 0xA1
CMD_SOFT_RESET              = SciospecCmd('CMD_Software_Reset',0xA1,CmdTypes.simple, Answer.WAIT_FOR_ACK)
# Options for "Save_Settings"
CMD_SOFT_RESET.set_options([OP_NULL])

## -----------------------------------------------------------------------------
## Set_Measurement_Setup - 0xB0 / Get_Measurement_Setup - 0xB1
CMD_SET_MEAS_SETUP          = SciospecCmd('CMD_Set_Measurement_Setup',0xB0,CmdTypes.set_w_option,Answer.WAIT_FOR_ACK)
CMD_GET_MEAS_SETUP          = SciospecCmd('CMD_Get_Measurement_Setup',0xB1,CmdTypes.get_w_option,Answer.WAIT_FOR_ANSWER_AND_ACK)
# Options for "Set_Measurement_Setup"/"Get_Measurement_Setup"
OP_RESET_SETUP              = SciospecOption('OP_Reset_Setup',0x01, [0x01,0x00])
OP_BURST_COUNT              = SciospecOption('OP_Burst_Count',0x02, [0x03,0x01])
OP_FRAME_RATE               = SciospecOption('OP_Frame_Rate',0x03, [0x05,0x01])
OP_EXC_FREQUENCIES          = SciospecOption('OP_Excitation_Frequencies',0x04, [0x0C,0x01])
OP_EXC_AMPLITUDE_DOUBLE     = SciospecOption('OP_Excitation_Amplitude_double',0x05, [0x09,0x01]) # Double Precision
OP_EXC_AMPLITUDE            = SciospecOption('OP_Excitation_Amplitude',0x05, [0x05,0x01]) # Single Precision
OP_EXC_PATTERN              = SciospecOption('OP_Excitation_Sequence',0x06, [0x03,0x01])
OP_ACTIVE_GUARD             = SciospecOption('OP_Active_Guard',0x07, [0x01,0x01])

OP_LINEAR                   = SciospecOption('LINEAR',0x00, [0x00,0x00])
OP_LOG                      = SciospecOption('LOG',0x01, [0x00,0x00])
used_cmds= [
    OP_RESET_SETUP,
    OP_BURST_COUNT,
    OP_FRAME_RATE,
    OP_EXC_FREQUENCIES,
    OP_EXC_AMPLITUDE,
    OP_EXC_PATTERN]
CMD_SET_MEAS_SETUP.set_options(used_cmds)
CMD_GET_MEAS_SETUP.set_options(used_cmds[1:]) 
## -----------------------------------------------------------------------------
## Set_Output_Configuration - 0xB2 / Get_Output_Configuration - 0xB3
CMD_SET_OUTPUT_CONFIG       = SciospecCmd('CMD_Set_Output_Configuration',0xB2,CmdTypes.set_w_option,Answer.WAIT_FOR_ACK)
CMD_GET_OUTPUT_CONFIG       = SciospecCmd('CMD_Get_Output_Configuration',0xB3,CmdTypes.get_w_option,Answer.WAIT_FOR_ANSWER_AND_ACK)
# Options for "Set_Output_Configuration"/"Get_Output_Configuration"
OP_EXC_STAMP                = SciospecOption('OP_Excitation_Setting',0x01, [0x02,0x01])
OP_CURRENT_STAMP            = SciospecOption('OP_Current_Row',0x02, [0x02,0x01])
OP_TIME_STAMP               = SciospecOption('OP_Timestamp',0x03, [0x02,0x01])
CMD_SET_OUTPUT_CONFIG.set_options([OP_EXC_STAMP, OP_CURRENT_STAMP, OP_TIME_STAMP])
CMD_GET_OUTPUT_CONFIG.set_options([OP_EXC_STAMP, OP_CURRENT_STAMP, OP_TIME_STAMP])
## -----------------------------------------------------------------------------
## Start_Stop_Measurement - 0xB4
CMD_START_STOP_MEAS         = SciospecCmd('CMD_Start_Stop_Measurement',0xB4,CmdTypes.set_w_option,Answer.WAIT_FOR_ACK)
# Options for "Start_Stop_Measurement"
OP_STOP_MEAS                = SciospecOption('OP_Stop_Measurement',0x00, [0x01,0x00])
OP_START_MEAS               = SciospecOption('OP_Start_Measurement',0x01, [0x01,0x00])
CMD_START_STOP_MEAS.set_options([OP_START_MEAS, OP_STOP_MEAS])
## -----------------------------------------------------------------------------
## Set_Ethernet_Configuration - 0xBD / Get_Ethernet_Configuration - 0xBE
CMD_SET_ETHERNET_CONFIG     = SciospecCmd('CMD_Set_Ethernet_Configuration',0xBD,CmdTypes.set_w_option,Answer.WAIT_FOR_ACK)# NOT USED
CMD_GET_ETHERNET_CONFIG     = SciospecCmd('CMD_Get_Ethernet_Configuration',0xBE,CmdTypes.get_w_option,Answer.WAIT_FOR_ANSWER_AND_ACK)
# Options for "Set_Ethernet_Configuration/Get_Ethernet_Configuration"
OP_IP_ADRESS                = SciospecOption('OP_IP_adress',0x01, [0x05,0x01]) #set get Static IP adress
OP_MAC_ADRESS               = SciospecOption('OP_MAC_adress',0x02, [0x00,0x01]) # only get Mac adress
OP_DHCP                     = SciospecOption('OP_DHCP',0x03, [0x02,0x01]) # activate/deactivate DHCP
CMD_SET_ETHERNET_CONFIG.set_options([OP_IP_ADRESS, OP_MAC_ADRESS, OP_DHCP])
CMD_GET_ETHERNET_CONFIG.set_options([OP_IP_ADRESS, OP_MAC_ADRESS, OP_DHCP])
## -----------------------------------------------------------------------------
## Set_ExtPort_Channel - 0xC2 / Get_ExtPort_Channel - 0xC3
CMD_SET_EXPORT_CHANNEL      = SciospecCmd('CMD_Set_ExtPort_Channel',0xC2,CmdTypes.set_w_option,Answer.WAIT_FOR_ACK)# NOT USED
CMD_GET_EXPORT_CHANNEL      = SciospecCmd('CMD_Get_ExtPort_Channel',0xC3,CmdTypes.simple,Answer.WAIT_FOR_ANSWER_AND_ACK)# NOT USED
# Options for "Set_ExtPort_Channel /Get_ExtPort_Channel "
OP_CH_1_16_NOT_CONNECTED    = SciospecOption('OP_Ch_1_16_not_connected',0x00, [0x01,0x01]) #set get Static IP adress # NOT USED
OP_CH_1_16_CONNECTED_PORT1  = SciospecOption('OP_Ch_1_16_connected_Port1',0x01, [0x01,0x01]) # only get Mac adress # NOT USED
OP_CH_1_16_CONNECTED_PORT2  = SciospecOption('OP_Ch_1_16_connected_Port2',0x02, [0x01,0x01]) # activate/deactivate DHCP # NOT USED
OP_CH_1_16_CONNECTED_PORT3  = SciospecOption('OP_Ch_1_16_connected_Port3',0x03, [0x01,0x01]) # activate/deactivate DHCP # NOT USED
CMD_SET_EXPORT_CHANNEL.set_options([OP_CH_1_16_NOT_CONNECTED, OP_CH_1_16_CONNECTED_PORT1, OP_CH_1_16_CONNECTED_PORT2, OP_CH_1_16_CONNECTED_PORT3])
CMD_GET_EXPORT_CHANNEL.set_options([OP_NULL])

## -----------------------------------------------------------------------------
## Get_ExtPort_Module - 0xC5
CMD_GET_EXPORT_MODULE       = SciospecCmd('CMD_Get_ExtPort_Module',0xC5,CmdTypes.simple,Answer.WAIT_FOR_ANSWER_AND_ACK) # NOT USED
# Options for "Get_ExtPort_Module"
CMD_GET_EXPORT_MODULE.set_options([OP_NULL])
## -----------------------------------------------------------------------------
## Set_Battery_Control - 0xC6 / Get_Battery_Control - 0xC7
CMD_SET_BATTERY_CONTROL     = SciospecCmd('CMD_Set_Battery_Control',0xC6,CmdTypes.set_w_option,Answer.WAIT_FOR_ACK) # NOT USED
CMD_GET_BATTERY_CONTROL     = SciospecCmd('CMD_Get_Battery_Control',0xC7,CmdTypes.get_w_option,Answer.WAIT_FOR_ANSWER_AND_ACK) # NOT USED
# Options for "Set_Battery_Control /Get_Battery_Control "
OP_BATTERY_STATUS          = SciospecOption('OP_Battery_Status',0x01, [0x01,0x01]) # NOT USED
OP_BATTERY_MODE            = SciospecOption('OP_Battery_mode',0x02, [0x02,0x01])  # NOT USED
OP_BATTERY_MIN_CAPACITY     = SciospecOption('OP_Battery_min_capacity',0x03, [0x02,0x01]) # NOT USED
CMD_SET_BATTERY_CONTROL.set_options([OP_BATTERY_STATUS, OP_BATTERY_MODE,OP_BATTERY_MIN_CAPACITY])
CMD_SET_BATTERY_CONTROL.set_options([OP_BATTERY_STATUS, OP_BATTERY_MODE,OP_BATTERY_MIN_CAPACITY])
## -----------------------------------------------------------------------------
## Set_LED_Control - 0xC8 / Get_LED_Control - 0xC9
CMD_SET_LED_CONTROL         = SciospecCmd('CMD_Set_LED_Control',0xC8,CmdTypes.set_w_option,Answer.WAIT_FOR_ACK) # NOT USED
CMD_GET_LED_CONTROL         = SciospecCmd('CMD_Get_LED_Control',0xC9,CmdTypes.get_w_option,Answer.WAIT_FOR_ANSWER_AND_ACK) # NOT USED
# Options for "Set_ExtPort_Channel /Get_ExtPort_Channel "
OP_AUTOMODE_ON_OFF          = SciospecOption('OP_Automode_on_off ',0x01, [0x02,0x01]) #set get Static IP adress # NOT USED
OP_STATUS_LED               = SciospecOption('OP_Status_LED',0x02, [0x02,0x02]) #set get Static IP adress # NOT USED
OP_MANUAL_LED               = SciospecOption('OP_manual_LED',0x03, [0x03,0x01]) # only get Mac adress # NOT USED

CMD_SET_LED_CONTROL.set_options([OP_AUTOMODE_ON_OFF,OP_STATUS_LED,OP_MANUAL_LED])
CMD_GET_LED_CONTROL.set_options([OP_AUTOMODE_ON_OFF,OP_STATUS_LED,OP_MANUAL_LED])

## -----------------------------------------------------------------------------
## Device_Serial_Number - 0xD1
CMD_GET_DEVICE_INFOS    = SciospecCmd('CMD_Device_Serial_Number',0xD1,CmdTypes.simple,Answer.WAIT_FOR_ANSWER_AND_ACK)
# Options for "Device_Serial_Number"
CMD_GET_DEVICE_INFOS.set_options([OP_NULL])
## -----------------------------------------------------------------------------
# Set_Current_Source_Setting - 0xB6 / Get_Current_Source_Setting - 0xB7
CMD_SET_CURRENT_SETTING   = SciospecCmd('CMD_Set_Current_Source_Setting',0xB6,CmdTypes.set_w_option,Answer.WAIT_FOR_ACK) # NOT USED
CMD_GET_CURRENT_SETTING   = SciospecCmd('CMD_Get_Current_Source_Setting',0xB7,CmdTypes.simple,Answer.WAIT_FOR_ANSWER_AND_ACK) # NOT USED
# Options for "Set_Current_Source_Setting"/"Get_Current_Source_Setting"
OP_DC_SOURCE              = SciospecOption('DC_Source',0x01, 0x01) # NOT USED
OP_AC_SOURCE              = SciospecOption('AC_Source',0x02, 0x01) # NOT USED
CMD_SET_CURRENT_SETTING.set_options([OP_AC_SOURCE, OP_DC_SOURCE])
CMD_GET_CURRENT_SETTING.set_options([OP_NULL])


# list of used CMD
cmds = [
    CMD_SAVE_SETTINGS,
    CMD_SOFT_RESET,
    CMD_SET_OUTPUT_CONFIG,
    CMD_GET_OUTPUT_CONFIG,
    CMD_START_STOP_MEAS,
    CMD_SET_ETHERNET_CONFIG,
    CMD_GET_ETHERNET_CONFIG,
    CMD_GET_DEVICE_INFOS
    ]
#l ist of used OP
# ops=[
#     OP_NULL,
#     OP_RESET_SETUP,         
#     OP_BURST_COUNT,          
#     OP_FRAME_RATE,           
#     OP_EXC_FREQUENCIES,      
#     # OP_EXC_AMPLITUDE_DOUBLE, 
#     OP_EXC_AMPLITUDE,        
#     OP_EXC_PATTERN,          
#     OP_ACTIVE_GUARD,         
#     # OP_LINEAR ,              
#     # OP_LOG,                  
#     OP_EXC_STAMP,            
#     OP_CURRENT_STAMP,        
#     OP_TIME_STAMP,          
#     OP_STOP_MEAS,            
#     OP_START_MEAS,           
#     OP_IP_ADRESS ,           
#     OP_MAC_ADRESS,           
#     OP_DHCP                
# ]

def  get_cmd(tag)->SciospecCmd:
    for cmd in cmds:
        if cmd.tag==tag:
            return cmd
    return SciospecCmd('CMD_not_found')

def  get_op(ops, tag)->SciospecOption:
    for op in ops:
        if op.tag==tag:
            return op
    return SciospecOption('OP_not_found')


################################################################################
##  Class of acknoledgments of the Sciospec device##############################
################################################################################

class SciospecAck(object):
    """ACK: Acknowlegement structure description:
            name= str
            ack_byte: OB Byte
            self.error:  0 transmission succeed , >0 transmission error (return ack_byte)
            self.string_out: str (the string which is displaed e.g. ACK: Cmd executed) """
    def __init__(self, name='', ack_byte= 0x00, error=bool, string_out= ''):
        self.name: str = name
        self.ack_byte: bytes = ack_byte
        self.error: bool = error
        self.string_out: str = string_out
    def is_nack(self):
        return self.error

################################################################################
##  Acknoledgments CONSTANTS for the Sciospec device############################
################################################################################  

## ACK
ACK_INCORRECT_FRAME_SYNTAX  = SciospecAck('ACK_Incorrect_Frame_syntax ', 0x01, True, 'NACK: Incorrect frame syntax')
ACK_COMMUNICATION_TIMEOUT   = SciospecAck('ACK_Communication_timeout', 0x02, True, 'Timeout: Communication-timeout (less data than expected)')
ACK_SYSTEM_BOOT_READY       = SciospecAck('ACK_System_boot_ready', 0x04, False, 'Wake-Up: System boot ready')
ACK_NACK_CMD_NOT_EXCECUTED  = SciospecAck('ACK_NACK_Cmd_not_executed', 0x81, True, 'NACK: Cmd not executed')
ACK_NACK_CMD_NOT_REGONIZED  = SciospecAck('ACK_NACK_Cmd_not_recognized', 0x82, True, 'NACK: Cmd not recognized')
ACK_ACK_CMD_EXCECUTED       = SciospecAck('ACK_ACK_Cmd_executed', 0x83, False, 'ACK: Cmd executed')
ACK_SYSTEM_READY            = SciospecAck('ACK_System_Ready', 0x84, False, 'System-Ready: System operational and ready')

NONE_ACK                    = SciospecAck('ACK not recieved/not recognized', 0x99, True, 'ACK not recieved/not recognized')

ACKs                         =[  ACK_INCORRECT_FRAME_SYNTAX,
                                ACK_COMMUNICATION_TIMEOUT,
                                ACK_SYSTEM_BOOT_READY,
                                ACK_NACK_CMD_NOT_EXCECUTED,
                                ACK_NACK_CMD_NOT_REGONIZED,
                                ACK_ACK_CMD_EXCECUTED,
                                ACK_SYSTEM_READY]

ACK_FRAME                   = [0x18, 0x01, 0x00, 0x18]


################################################################################
##  Setup class Sciospec EIT Device ############################################
################################################################################
class SciospecSetup(object):
    """ Class regrouping all info (serial number, Ethernet config, etc.),
    meas. parameters (excitation pattern, amplitude, etc.), etc. of the device.
    
    Notes
    -----
    - see documentation of the EIT device    """
    def __init__(self, ch):

        self.exc_amp= float(10.0)
        self.exc_pattern = [[ 1, 2], [2, 3]]
        self.exc_pattern_idx= int(0)
        self.frame_rate=float(1.0)
        self.max_frame_rate=float(1.0)
        self.burst= int(0)
        
        self.device_infos=DeviceInfos(ch)
        self.output_config= OutputConfig()
        self.ethernet_config= EthernetConfig()
        self.freq_config= FrequencyConfig()

    def computeMaxFrameRate(self):
        """ Compute the maximum frame rate corresponding to the actual frequencies sweep 

        Notes
        -----
        - see documentation of the EIT device"""
        f_i = self.freq_config.make_freqs_list() #ndarray

        n_freq = float(self.freq_config.steps)
        t_freq = float(DELAY_BTW_2FREQ) # in s
 
        n_inject= float(len(self.exc_pattern))
        t_inject= float(DELAY_BTW_2INJ) # in s

        T_fi = np.reciprocal(f_i) # in s
        T_ms= np.ones_like(f_i)*MIN_SAMPLING_TIME # in s
        max_Tms_fi= np.maximum(T_ms,T_fi)
        sum_max_Tms_fi = float(max_Tms_fi.sum())
        t_min= n_inject*(t_inject+t_freq*(n_freq-1)+ sum_max_Tms_fi)

        if t_min != 0.0:
            self.max_frame_rate= float(1/t_min)

    def saveSetupDevice(self, file_path, sheetname):
        """ Save the setup of the device in an excel file
        all attributes and subattributes will be saved

        Parameters
        ----------
        file_path: str
        sheetname: str

        Notes
        -----
        - the excel file can be edited..."""
        data2save, name, types = getAllSubattributes(self)
        # add logging
        print('data saved : '+ str(data2save))
        print(name)
        print(types)
        dataframe = pd.DataFrame(data2save, name)
        dataframe.to_excel(file_path,sheet_name= sheetname)
        
        
        
    def loadSetupDevice(self, file_path, sheetname):
        """ Load the setup of the device from an excel file
        all attributes and subattributes will be loaded

        Parameters
        ----------
        file_path: str
        sheetname: str"""
        df= pd.read_excel(file_path,sheet_name=sheetname)
        data, name, types = getAllSubattributes(self)
        for i in range(len(df.values)):
            
            print(df.values[i][0])
            print(df.values[i][1])
            print(types[i])
            ## the obtain data are not the same type as needed (e.g. we  get str for list of int)            
            if  types[i]==type(df.values[i][1]):
                val=df.values[i][1]
            elif types[i]== type(float('0')) and  type(df.values[i][1])== type(int('0')):
                val=float(df.values[i][1])
            else:
                val=ast.literal_eval(df.values[i][1])
            ## set the attributes and sub attributes of the setup
            attr_str= str(df.values[i][0])    
            indexPt= attr_str.find('.')
            if indexPt<0:
                setattr(self, df.values[i][0], val)
            else:
                setattr(getattr(self,attr_str[:indexPt]), attr_str[indexPt+1:], val)
        dataloaded, name, types = getAllSubattributes(self)
        # add logging
        print('data loaded : '+ str(dataloaded))

    def get_burst_for_tx(self):
        """ Get burst data to send to the device"""
        return convertInt2Bytes(self.burst, 2)
    def get_frame_rate_for_tx(self):
        """ Get frame rate data to send to the device"""
        return convertFloat2Bytes(self.frame_rate)
    def get_freq_for_tx(self):
        
        data =[]
        data=convertFloat2Bytes(self.freq_config.min_freq_Hz)
        data.extend(convertFloat2Bytes(self.freq_config.max_freq_Hz))
        data.extend(convertInt2Bytes(self.freq_config.steps, 2)) # Steps is defined on 2 bytes
        if self.freq_config.scale== OP_LINEAR.name:
            data.append(OP_LINEAR.tag)
        elif self.freq_config.scale== OP_LOG.name:
            data.append(OP_LOG.tag)
        else:
            raise TypeError("wrong Scale Str")
        return data
    def get_exc_amp_d_for_tx(self):
        """ Get excitation amplitude (double precision) data to send to the device"""
        return []
    def get_exc_amp_for_tx(self):
        """ Get excitation amplitude (single precision) data to send to the device"""
        return convertFloat2Bytes(self.exc_amp)
    def get_exc_pattern_for_tx(self):
        """ get excitation pattern (only one index) data to send to the device"""
        return self.exc_pattern[self.exc_pattern_idx]
    # def get_linear(self):
    #     return []
    # def get_log(self):
    #     return []
    def get_exc_stamp_for_tx(self):
        return [1]#[int(self.output_config.exc_stamp)]
    def get_current_stamp_for_tx(self):
        return [1]#[int(self.output_config.current_stamp)]
    def get_time_stamp_for_tx(self):
        return [1]#[int(self.output_config.time_stamp)]
    def get_ip_for_tx(self):
        return []
    def get_mac_for_tx(self):
        return []
    def get_dhcp_for_tx(self):
        return [int(self.ethernet_config.dhcp)]
    def get_sn_for_tx(self):
        return self.device_infos.sn
    ##########################################################
    #####Set
    ##########################################################
    def set_burst_from_rx(self, rx_frame):
        data= rx_frame[DATA_START_INDX:-1]
        self.burst =convertBytes2Int(data)
        
    def set_frame_rate_from_rx(self, rx_frame):
        data= rx_frame[DATA_START_INDX:-1]
        self.frame_rate=convert4Bytes2Float(data)
        
    def set_freq_from_rx(self, rx_frame):
        data= rx_frame[DATA_START_INDX:-1]
        self.freq_config.min_freq_Hz=convert4Bytes2Float(data[0:4])
        self.freq_config.max_freq_Hz=convert4Bytes2Float(data[4:8])
        self.freq_config.steps=convertBytes2Int(data[8:10])
        if data[10]== OP_LINEAR.tag:
            self.freq_config.scale=OP_LINEAR.name
        elif data[10]== OP_LOG.tag:
            self.freq_config.scale=OP_LOG.name
        else:
            raise TypeError("wrong scale byte")
        
    def set_exc_amp_d_from_rx(self, rx_frame):
        data= rx_frame[DATA_START_INDX:-1]
        """"""
    def set_exc_amp_from_rx(self, rx_frame):
        data= rx_frame[DATA_START_INDX:-1]
        self.exc_amp =convert4Bytes2Float(data)
        
    def set_exc_pattern_from_rx(self, rx_frame):
        data= rx_frame[DATA_START_INDX:-1]
        self.exc_pattern=[]
        for i in range(len(data)//2):
            self.exc_pattern.append(data[i*2:(i+1)*2])
        
    # def set_linear(self, data):
    #     """"""
    # def set_log(self, data):
    #     """"""
    def set_exc_stamp_from_rx(self, rx_frame):
        data= rx_frame[DATA_START_INDX:-1]
        self.output_config.exc_stamp= bool(data[0])
        
    def set_current_stamp_from_rx(self, rx_frame):
        data= rx_frame[DATA_START_INDX:-1]
        self.output_config.current_stamp= bool(data[0])
        
    def set_time_stamp_from_rx(self, rx_frame):
        data= rx_frame[DATA_START_INDX:-1]
        self.output_config.time_stamp= bool(data[0]) 
        
    def set_ip_from_rx(self, rx_frame):
        data= rx_frame[DATA_START_INDX:-1]
        length= LENGTH_IP_ADRESS
        self.ethernet_config.ip= data[:length]
        self.ethernet_config.ip_formated= str(data[0])+ '.' +str(data[1])+ '.' +str(data[2])+ '.' +str(data[3])
    
    def set_mac_from_rx(self, rx_frame):
        data= rx_frame[DATA_START_INDX:-1]
        length= LENGTH_MAC_ADRESS
        self.ethernet_config.mac= data[:length]
        ID= mkListOfHex(data[:length])
        self.ethernet_config.mac_formated= ID[0]+ ':' +ID[1]+ ':' +ID[2] + ':' +ID[3]+ ':' +ID[4]+ ':'+ID[5]
    
    def set_dhcp_from_rx(self, rx_frame):
        data= rx_frame[DATA_START_INDX:-1]
        self.ethernet_config.dhcp= bool(data[0])
    
    def set_sn_from_rx(self, rx_frame):
        rx_op_data= rx_frame[OPTION_BYTE_INDX:-1]
        length = LENGTH_SERIAL_NUMBER
        self.device_infos.sn= rx_op_data[:length]
        print()
        ID= mkListOfHex(rx_op_data[:length])
        self.device_infos.sn_formated= ID[0]+ '-' +ID[1] +ID[2] +'-' +ID[3] +ID[4]+ '-'+ID[5]+ ID[6]
    
    def get_channel(self):
        """ Get burst val"""
        return self.device_infos.channel
    def get_burst(self):
        """ Get burst val"""
        return self.burst
    def get_frame_rate(self):
        """ Get frame rate data to send to the device"""
        return self.frame_rate
    def get_freq_min(self): 
        return self.freq_config.min_freq_Hz
    def get_freq_max(self):
        return self.freq_config.max_freq_Hz
    def get_freq_scale(self):
        return self.freq_config.scale
    def get_freq(self):
        data =[]
        data=convertFloat2Bytes(self.freq_config.min_freq_Hz)
        data.extend(convertFloat2Bytes(self.freq_config.max_freq_Hz))
        data.extend(convertInt2Bytes(self.freq_config.steps, 2)) # Steps is defined on 2 bytes
        if self.freq_config.scale== OP_LINEAR.name:
            data.append(OP_LINEAR.tag)
        elif self.freq_config.scale== OP_LOG.name:
            data.append(OP_LOG.tag)
        else:
            raise TypeError("wrong Scale Str")
        return self.freq_config.steps, self.freq_config.scale
    def get_exc_amp(self):
        return self.exc_amp
    def get_exc_pattern(self):
        return self.exc_pattern
    def get_freq_scale(self):
        return self.freq_config.scale
    def get_freq_steps(self):
        return self.freq_config.steps
    def get_exc_stamp(self):
        return self.output_config.exc_stamp
    def get_current_stamp(self):
        return self.output_config.current_stamp
    def get_time_stamp(self):
        return self.output_config.time_stamp
    def get_ip(self):
        return self.ethernet_config.ip_formated
    def get_mac(self):
        return self.ethernet_config.mac_formated
    def get_dhcp(self):
        return self.ethernet_config.dhcp
    def get_sn(self):
        return self.device_infos.sn_formated

    def set_exc_pattern_idx(self, idx:int):
        self.exc_pattern_idx=idx

    def make_freqs_list(self):
        return self.freq_config.make_freqs_list()





class DeviceInfos(object):
    """ Class regrouping all info about the ouput configuration of the device,
    what for stamp are given out with meas. data

    Notes
    -----
    - see documentation of the EIT device"""
    def __init__(self,ch):
        self.channel= ch
        self.sn_formated= '00-0000-0000-0000'
        self.sn= [0,0,0,0,0,0,0]   
class OutputConfig(object):
    """ Class regrouping all info about the ouput configuration of the device,
    what for stamp are given out with meas. data

    Notes
    -----
    - see documentation of the EIT device"""
    def __init__(self):
        self.exc_stamp= int(1)
        self.current_stamp= int(1)
        self.time_stamp=int(1)

class EthernetConfig(object):
    """ Class regrouping all info about the ethernet configuration of the device:
    IPAdress, MAC Adress, etc.

    Notes
    -----
    - see documentation of the EIT device"""
    def __init__(self):
        self.ip:List[int]= [0,0,0,0]
        self.mac:List[int]= [0,0,0,0,0,0]
        self.ip_formated:str= '0.0.0.0'
        self.mac_formated:str= '00:00:00:00:00:00'
        self.dhcp:int=0

class FrequencyConfig(object):
    """ Class regrouping all parameters for the frequency sweep configuration
    of the device used during the measurement

    Notes
    -----
    - see documentation of the EIT device"""
    def __init__(self):
        self.min_freq_Hz= float(1000.0)
        self.max_freq_Hz= float(1000.0)
        self.steps= int(1)
        self.scale= OP_LINEAR.name
        self.freqs=[]
        self.make_freqs_list()
        
        
    def make_freqs_list(self):
        """ Make the Frequencies list of frequencies accoreding to the 
        frequency sweep configuration

        Notes
        -----
        - see documentation of the EIT device"""
        if self.scale==OP_LINEAR.name:
            self.freqs= np.linspace(self.min_freq_Hz,self.max_freq_Hz, self.steps)
        elif self.scale==OP_LOG.name:
            self.freqs= np.logspace(self.min_freq_Hz,self.max_freq_Hz, self.steps)
        else:
            TypeError('incorrect scale')
        return self.freqs




if __name__=="__main__":
    """ """
