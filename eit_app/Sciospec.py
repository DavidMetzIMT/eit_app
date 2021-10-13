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
import struct

import numpy as np
import pandas as pd
from matplotlib.pyplot import tick_params

from utils.eit_dataset import *
from utils.eit_model import *
from utils.SciospecCONSTANTS import *

__author__ = "David Metz"
__copyright__ = "Copyright (c) 2021"
__credits__ = ["David Metz"]
__license__ = "GPLv3"
__version__ = "2.0.0"
__maintainer__ = "David Metz"
__email__ = "d.metz@tu-bs.de"
__status__ = "Production"


################################################################################
## Class for Sciopec Device ####################################################
################################################################################

class SciospecDev(object):
    """  Class to save infos about the Sciospec device and interact with it
    
    Regroup all informations, setup of the connected Sciospec EIT device
    and allow to interact with it according to is user guide.    """
    def __init__(self, paths):
        self.channel = 32
        self.serialInterface= [] #SciospecSerialInterface() # the serial interface is set outside this class (e.g. in the app_backend)
        self.setup= SciospecSetup(self.channel)
        self.verbose=0 # for debugging
        self.paths= paths
        self.log=[]
        self.add2Log('INIT: Device object created')
        self.status = 'no Device connected'
        self.dataset:EITDataSet=0
        self.dataUp=0
        self.flagMeasRunning= False
        if self.verbose>0:
            print('Start: __init__ Device')

    ## =========================================================================
    ##  Setter methods 
    ## =========================================================================

    def setSerialInterface(self, serial_interface):
        """ link the serial interface for the device
        
        Parameters
        ----------
        serial_interface: "SerialInterface" object connected to the hardware
        
        Notes
        -----
        - it had been made sure that a Sciospec device is connected"""
        self.serialInterface=serial_interface

    def setDataSet(self,dataset):
        """ Link the dataset to use during measurement
        
        Parameters
        ----------
        dataset: "EITDataSet" object connected to the hardware"""
        self.dataset = dataset # actual dataset with one frame

    def add2Log(self, new_text_entry):
        """ Add in device log the "new_text_entry"
        
        Parameters
        ----------
        new_text_entry: should be a str"""
        self.log.append(str(new_text_entry))
        if self.verbose >0: 
            print(str(new_text_entry))
            
    ## =========================================================================
    ##  Methods for sending data/commands
    ## =========================================================================
    
    def _send_cmd_frame(self,cmd, op):
        """ Send a command frame to the device
        according to the cmd and op parameters
        
        Parameters
        ----------
        cmd: SciospecCmd object
        op: Sciospecoption object

        Notes
        -----
        - all cmd, op, and ack are defined as constant in SciospecCONSTANTS.py""" 
        cmd_frame = self.mkCmdFrame(cmd, op)
        msg_tmp= 'TX_msg: ' + str(cmd_frame)
        self.add2Log(msg_tmp)
        if self.verbose>0:
            print(msg_tmp)
        self.serialInterface.writeSerial(cmd_frame)

    def mkCmdFrame(self,cmd, op):
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
        data= self._preparetData2Send(cmd, op)   
        if cmd.type == 0: # send cmd without option
            cmd_frame = [cmd.tag_byte, 0x00, cmd.tag_byte]
        else:
            length_byte= op.length_byte[cmd.type-1]
            if length_byte == 0x00:
                raise TypeError('not allowed option for the command')
            elif length_byte== 0x01: # send cmd with option
                cmd_frame = [cmd.tag_byte, length_byte ,op.option_byte ,cmd.tag_byte]
            else:
                if 1 + len(data) == length_byte: # send cmd with option and data
                    cmd_frame = [cmd.tag_byte, length_byte,op.option_byte]
                    for data_i in data:
                        cmd_frame.append(data_i)
                    cmd_frame.append(cmd.tag_byte)
                else:
                    raise TypeError('Data do not have right lenght')
        return cmd_frame

    def _preparetData2Send(self,cmd, op):
        """ select the right data to send to the device
        corresponding to the cmd and op parameters
        
        Parameters
        ----------
        cmd: SciospecCmd object
        op: Sciospecoption object

        Returns
        -------
        data: List of int8 (byte)
            data to send to the device

        Notes
        -----
        - all cmd, op, and ack are defined as constant in SciospecCONSTANTS.py
        - the errors were for the testing of that method and should never be raised"""
        cmd_tag= cmd.tag_byte
        option_byte=op.option_byte
        data= [0x00]
        # that "switch" is not that optimal but works...'
        if cmd_tag == CMD_SET_MEAS_SETUP.tag_byte:
            # Treat the RX data for the CMD_Get_Meas_Setup
            if option_byte==OP_EXC_AMPLITUDE.option_byte:
                data= convertFloat2Bytes(self.setup.Excitation_Amplitude)
            elif option_byte== OP_BURST_COUNT.option_byte:
                data=convertInt2Bytes(self.setup.Burst, 2) # Burst is defined on 2 bytes
            elif option_byte== OP_FRAME_RATE.option_byte:
                data= convertFloat2Bytes(self.setup.Frame_rate)
            elif option_byte== OP_EXC_FREQUENCIES.option_byte:
                data=convertFloat2Bytes(self.setup.FrequencyConfig.Min_F_Hz)
                data.extend(convertFloat2Bytes(self.setup.FrequencyConfig.Max_F_Hz))
                data.extend(convertInt2Bytes(self.setup.FrequencyConfig.Steps, 2)) # Steps is defined on 2 bytes
                if self.setup.FrequencyConfig.Scale== OP_LINEAR.name:
                    data.append(OP_LINEAR.option_byte)
                elif self.setup.FrequencyConfig.Scale== OP_LOG.name:
                    data.append(OP_LOG.option_byte)
                else:
                   raise TypeError("wrong Scale Str")
            elif option_byte== OP_EXC_PATTERN.option_byte:
                data= self.setup.Excitation_Pattern[self.setup.Pattern_i]
            elif option_byte== OP_RESET_SETUP.option_byte:
                pass
            else:
                raise TypeError("wrong option_byte for Measurement_Setup")
        elif cmd_tag == CMD_SET_OUTPUT_CONFIG.tag_byte:
            # Treat the RX data for the CMD_Get_Output_Configuration
            if option_byte==OP_EXC_STAMP.option_byte:
                data= [self.setup.OutputConfig.Excitation_stamp]
            elif option_byte== OP_CURRENT_STAMP.option_byte:
                data= [self.setup.OutputConfig.Current_stamp]
            elif option_byte== OP_TIME_STAMP.option_byte:
                data= [self.setup.OutputConfig.Time_stamp]
            else:
                raise TypeError("wrong option_byte for OutputConfig")
        elif cmd_tag == CMD_SET_ETHERNET_CONFIG.tag_byte:
            # Treat the RX data for the CMD_Get_Ethernet_Configuration
            if option_byte==OP_IP_ADRESS.option_byte:
                data = self.setup.SN
            elif option_byte== OP_DHCP.option_byte:
                data= [self.setup.EthernetConfig.DHCP_Activated]
            else:
                raise TypeError("wrong option_byte for EthernetConfig")
        if self.verbose>0:
            print('Data to send:' + str(data))
        return data

    ## =========================================================================
    ##  Methods for recieved data
    ## =========================================================================

    def treatNewRxFrame(self,rx_frame):
        """ Called by the SerialInterface "PollreadSerial" to treat the recieved frame

        Parameters
        ----------
        rx_frame: list of int8 (byte)"""
        self._sort_frame(rx_frame)

    def _sort_frame(self,rx_frame):
        """ Sort the recieved frame between Acknwoledgement and Messages

        in case of Ack, the option_byte of the RX_Ack is check and the rx_ack is save in the log
        in case of Messages, the rx_msg is save in the log and te rx_frame is further treated 

        Parameters
        ----------
        rx_frame: list of int8 (byte)
        
        Returns
        -------
        should only return 1...."""
        len_rx_frame= len(rx_frame) # first test if it is an ack
        if len_rx_frame<4:
            return 0
            raise TypeError('error rx_frame "%s"' % rx_frame) # should never come to that a fram is at least 4 bytes
        else:
            tmp=rx_frame[:]
            tmp[OPTION_BYTE_INDX]=0
            if tmp==ACK_FRAME:  # if the rx_frame is an ACK_frame analize the ack!
                rx_ack=self.checkAck(rx_frame[OPTION_BYTE_INDX])
                # Todoe handling of NACk.... is missing (however is never happenning, and during data sending no ack is send with....)
                self.add2Log(rx_ack.string_out)
            else: # if the rx_frame is a msg treat it!
                rx_msg= 'RX_msg: ' + str(bytearray(rx_frame))
                self.add2Log(rx_msg)
                self._extract_rx_data(rx_frame)
            return 1

    def checkAck(self,rx_ack_byte):
        """ look for the Ack corresponding to the given rx_ack_byte  
        
        Parameters
        ----------
        x_ack_byte: int8
        
        Returns
        -------
        rx_ack : SciospecAck object
            recieved Acknoledgement     """
        for ack_i in ACK:
            if ack_i.ack_byte==rx_ack_byte:
                rx_ack= ack_i
                break
            else:
                rx_ack= SciospecAck('ACK_not_regonized', 0x00, 2, 'ack_byte_not_regonized')
        return rx_ack

    def _extract_rx_data(self, rx_frame):
        """ Extract the data from rx_frame and save them to the right properties of device 
        
        Parameters
        ----------
        rx_frame: list of int8 (byte)

        Notes
        -----
        - the errors were for the testing of that method and should never be raised"""
        rx_tmp = rx_frame[:-1] # discard the last cmd_byte
        cmd_tag= rx_tmp[CMD_BYTE_INDX]
        length_data= rx_tmp[LENGTH_BYTE_INDX]
        option_byte= rx_tmp[OPTION_BYTE_INDX]
        data= rx_tmp[DATA_START_INDX:]
        rx_op_data= rx_tmp[OPTION_BYTE_INDX:]
        # that "switch" is not that optimal but works...'
        if cmd_tag == CMD_DEVICE_SERIAL_NUMBER.tag_byte:
            # Treat the RX data for the CMD_Device_Serial_Number
            self._format_sn_ip_mac('SN', rx_op_data)
        elif cmd_tag == CMD_GET_MEAS_SETUP.tag_byte:
            # Treat the RX data for the CMD_Get_Meas_Setup
            if option_byte==OP_EXC_AMPLITUDE.option_byte:
                self.setup.Excitation_Amplitude =convert4Bytes2Float(data)
            elif option_byte== OP_BURST_COUNT.option_byte:
                self.setup.Burst =convertBytes2Int(data)
            elif option_byte== OP_FRAME_RATE.option_byte:
                self.setup.Frame_rate=convert4Bytes2Float(data)
            elif option_byte== OP_EXC_FREQUENCIES.option_byte:
                self.setup.FrequencyConfig.Min_F_Hz=convert4Bytes2Float(data[0:4])
                self.setup.FrequencyConfig.Max_F_Hz=convert4Bytes2Float(data[4:8])
                self.setup.FrequencyConfig.Steps=convertBytes2Int(data[8:10])
                if data[10]== OP_LINEAR.option_byte:
                    self.setup.FrequencyConfig.Scale=OP_LINEAR.name
                elif data[10]== OP_LOG.option_byte:
                    self.setup.FrequencyConfig.Scale=OP_LOG.name
                else:
                    raise TypeError("wrong scale byte")
            elif option_byte== OP_EXC_PATTERN.option_byte:
                self.setup.Excitation_Pattern=[]
                for i in range(len(data)//2):
                    self.setup.Excitation_Pattern.append(data[i*2:(i+1)*2])
            else:
                raise TypeError("wrong option_byte for Measurement_Setup")
        elif cmd_tag == CMD_GET_OUTPUT_CONFIG.tag_byte:
            # Treat the RX data for the CMD_Get_Output_Configuration
            if option_byte==OP_EXC_STAMP.option_byte:
                self.setup.OutputConfig.Excitation_stamp= data[0]==1 # convert to bool
            elif option_byte== OP_CURRENT_STAMP.option_byte:
                self.setup.OutputConfig.Current_stamp= data[0]==1 # convert to bool
            elif option_byte== OP_TIME_STAMP.option_byte:
                self.setup.OutputConfig.Time_stamp= data[0]==1 # convert to bool
            else:
                raise TypeError("wrong option_byte for OutputConfig")
        elif cmd_tag == CMD_START_STOP_MEAS.tag_byte:
            # Treat the measurements data
            self.dataset.addRxData2DataSet(rx_op_data)
        elif cmd_tag == CMD_GET_ETHERNET_CONFIG.tag_byte:
            # Treat the RX data for the CMD_Get_Ethernet_Configuration
            if option_byte==OP_IP_ADRESS.option_byte:
                self._format_sn_ip_mac('IP', data)
            elif option_byte== OP_MAC_ADRESS.option_byte:
                self._format_sn_ip_mac('MAC', data)
            elif option_byte== OP_DHCP.option_byte:
                self.setup.EthernetConfig.DHCP_Activated= data[0]==1 # convert to bool
            else:
                raise TypeError("wrong option_byte for EthernetConfig")
        else:
            raise TypeError("Command not recognized")
        self.dataUp = 1 # for GUI update

    def _format_sn_ip_mac(self, type, rx_data):
        """ Save and make the corresponding str format for display
        for serial number (SN), IP Adress(IP), and MAC-Adress(MAC)
        
        Parameters
        ----------
        rx_data: list of int8 (byte)
        type: str 
            type of data to save and formate: SN, IP, MAC"""
        if type.upper() == 'SN':
            length = LENGTH_SERIAL_NUMBER
            self.setup.SN= rx_data[:length]
            ID= mkListOfHex(rx_data[:length], length)
            self.setup.SN_str= ID[0]+ '-' +ID[1] +ID[2] +'-' +ID[3] +ID[4]+ '-'+ID[5]+ ID[6]
            if self.verbose>0:
                print(self.setup.SN_str)
        elif type.upper() == 'IP':
            length= LENGTH_IP_ADRESS
            self.setup.EthernetConfig.IPAdress= rx_data[:length]
            self.setup.EthernetConfig.IPAdress_str= str(rx_data[0])+ '.' +str(rx_data[1])+ '.' +str(rx_data[2])+ '.' +str(rx_data[3])
            if self.verbose>0:
                print(self.setup.EthernetConfig.IPAdress_str)
        elif type.upper() == 'MAC':
            length= LENGTH_MAC_ADRESS
            self.setup.EthernetConfig.MACAdress= rx_data[:length]
            ID= mkListOfHex(rx_data, length)
            self.setup.EthernetConfig.MACAdress_str= ID[0]+ ':' +ID[1]+ ':' +ID[2] + ':' +ID[3]+ ':' +ID[4]+ ':'+ID[5]
            if self.verbose>0:
                print(self.setup.EthernetConfig.MACAdress_str)

    ## =========================================================================
    ##  Methods excecuting task on the device
    ## =========================================================================
    
    def getSN(self):
        ''' Ask for the serial nummer of the Device

        Notes
        -----
        - the serial number is saved in "self.setup.SN"'''
        self._send_cmd_frame(CMD_DEVICE_SERIAL_NUMBER, OP_NULL)


    def start_meas(self, path=None):
        """ Start measurements
        
        Parameters
        ----------
        path : str
            filename_path where the data has to be saved"""
        # self.dataset.initDataSet(self.setup, path) ## Prepare the Dataset
        self._send_cmd_frame(CMD_START_STOP_MEAS, OP_START_MEAS)
        self.flagMeasRunning= True

    def stop_meas(self):
        """ Stop measurements
        """
        self._send_cmd_frame(CMD_START_STOP_MEAS, OP_STOP_MEAS)
        self.flagMeasRunning = False

    def set_setup(self):
        """ Send the setup to the device
        
        Notes
        -----
        - will set the device with the actula values of self.setup"""
        self._send_cmd_frame(CMD_SET_OUTPUT_CONFIG, OP_EXC_STAMP)
        self._send_cmd_frame(CMD_SET_OUTPUT_CONFIG, OP_CURRENT_STAMP)
        self._send_cmd_frame(CMD_SET_OUTPUT_CONFIG, OP_TIME_STAMP)
        self._send_cmd_frame(CMD_SET_ETHERNET_CONFIG, OP_DHCP)
        self._send_cmd_frame(CMD_SET_MEAS_SETUP, OP_RESET_SETUP)
        self._send_cmd_frame(CMD_SET_MEAS_SETUP, OP_EXC_AMPLITUDE)
        self._send_cmd_frame(CMD_SET_MEAS_SETUP, OP_BURST_COUNT)
        self._send_cmd_frame(CMD_SET_MEAS_SETUP, OP_FRAME_RATE)
        self._send_cmd_frame(CMD_SET_MEAS_SETUP, OP_EXC_FREQUENCIES)
        for self.setup.Pattern_i in range(len(self.setup.Excitation_Pattern)):
            self._send_cmd_frame(CMD_SET_MEAS_SETUP, OP_EXC_PATTERN)

    def get_setup(self):
        """ Ask for the setup of the device
        
        Notes
        -----
        - self.setup properties will be updated with values from device"""
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


    def software_reset(self):
        """ Sofware reset the device
        
        Notes
        -----
        - a restart is needed after this method"""
        self._send_cmd_frame(CMD_SOFT_RESET,OP_NULL)

    ## =========================================================================
    ##  Methods relative to loading and saving setups of the device
    ## =========================================================================
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
        data2save, name, types = getAllSubattributes(self.setup)
        if self.verbose>0:
            print('data loaded : '+ str(data2save))
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
        data, name, types = getAllSubattributes(self.setup)
        for i in range(len(df.values)):
            if self.verbose>0:
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
                setattr(self.setup, df.values[i][0], val)
            else:
                setattr(getattr(self.setup,attr_str[:indexPt]), attr_str[indexPt+1:], val)
        dataloaded, name, types = getAllSubattributes(self.setup)
        if self.verbose>0:
            print('data loaded : '+ str(dataloaded))
        pass

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
        self.Channel = ch
        self.Excitation_Amplitude= float(10.0)
        self.Excitation_Pattern = [[ 1, 2], [2, 3]]
        self.Pattern_i= int(0)
        self.Frame_rate=float(1.0)
        self.MaxFrameRate=float(1.0)
        self.Burst= int(0)
        self.SN_str= '00-0000-0000-0000'
        self.SN= [0,0,0,0,0,0,0]
        self.OutputConfig= OutputConfig()
        self.EthernetConfig= EthernetConfig()
        self.FrequencyConfig= FrequencyConfig()

#         DELAY_BTW_2FREQ = 42 # in µs
# MIN_SAMPLING_TIME =208 # in µs
# DELAY_BTW_2INJ = 651 # in µs
# UPPER_LIMIT_FRAME_RATE = 100 # in fps
    
    def computeMaxFrameRate(self):
        """ Compute the maximum frame rate corresponding to the actual frequencies sweep 

        Notes
        -----
        - see documentation of the EIT device"""
        f_i = self.FrequencyConfig.mkFrequencyList() #ndarray

        n_freq = float(self.FrequencyConfig.Steps)
        t_freq = float(DELAY_BTW_2FREQ) # in s
 
        n_inject= float(len(self.Excitation_Pattern))
        t_inject= float(DELAY_BTW_2INJ) # in s

        T_fi = np.reciprocal(f_i) # in s
        T_ms= np.ones_like(f_i)*MIN_SAMPLING_TIME # in s
        max_Tms_fi= np.maximum(T_ms,T_fi)
        sum_max_Tms_fi = float(max_Tms_fi.sum())
        t_min= n_inject*(t_inject+t_freq*(n_freq-1)+ sum_max_Tms_fi)

        if t_min != 0.0:
            self.MaxFrameRate= float(1/t_min)

        
class OutputConfig(object):
    """ Class regrouping all info about the ouput configuration of the device,
    what for stamp are given out with meas. data

    Notes
    -----
    - see documentation of the EIT device"""
    def __init__(self):
        self.Excitation_stamp= int(1)
        self.Current_stamp= int(1)
        self.Time_stamp=int(1)

class EthernetConfig(object):
    """ Class regrouping all info about the ethernet configuration of the device:
    IPAdress, MAC Adress, etc.

    Notes
    -----
    - see documentation of the EIT device"""
    def __init__(self):
        self.IPAdress= [0,0,0,0]
        self.MACAdress= [0,0,0,0,0,0]
        self.IPAdress_str= '0.0.0.0'
        self.MACAdress_str= '00:00:00:00:00:00'
        self.DHCP_Activated=int(0)

class FrequencyConfig(object):
    """ Class regrouping all parameters for the frequency sweep configuration
    of the device used during the measurement

    Notes
    -----
    - see documentation of the EIT device"""
    def __init__(self):
        self.Min_F_Hz= float(1000.0)
        self.Max_F_Hz= float(1000.0)
        self.Steps= int(1)
        self.Scale= OP_LINEAR.name
        self.frequencyList=[]
        
        self.mkFrequencyList()
        
        
    def mkFrequencyList(self):
        """ Make the Frequencies list of frequencies accoreding to the 
        frequency sweep configuration

        Notes
        -----
        - see documentation of the EIT device"""
        if self.Scale==OP_LINEAR.name:
            self.frequencyList= np.linspace(self.Min_F_Hz,self.Max_F_Hz, self.Steps)
        elif self.Scale==OP_LOG.name:
            self.frequencyList= np.logspace(self.Min_F_Hz,self.Max_F_Hz, self.Steps)
        else:
            TypeError('incorrect scale')
        return self.frequencyList

################################################################################
##  Functions for Sciopec Device ###############################################
################################################################################

def mkListOfHex(rx_data, length):
    """ return a list of str of the Hex-representatiopn of the list of int8

    Parameters
    ----------
    rx_data: list of int8 (e.g. [0xD1, 0x00, 0xD1])
    length: int
        set the ouput list length

    Returns
    -------
    ID: list of str
        which are the Hex representatiopn of the list of int8 (RX_data)  
        (e.g. [0xD1, 0x00, 0xD1] >> ['D1', '00', 'D1'])

    Notes
    -----
    - used to generate the str of the serial number and Mac adress"""
    list_hex= []
    for i in range(length):
        tmp=hex(rx_data[i]).replace('0x','')
        if len(tmp)==1:
            list_hex.append('0'+tmp.capitalize())
        else:
            list_hex.append(tmp.capitalize())
    return list_hex

def convert4Bytes2Float(data_4bytes):
    """ Convert the represention of a single float format (a list of 4 int8 (4 Bytes)) of a number 
    to its float value 

    Parameters
    ----------
    data_4bytes: list of 4 int8 representing a float value according the single float format
    
    Returns
    -------
    out_float: corresponding float

    Notes
    -----
    - see documentation of the EIT device"""
    if len(data_4bytes)==4:
        out_float=struct.unpack('>f', bytearray(data_4bytes))[0]
    else:
        raise TypeError(f"Only 4Bytes allowed: {data_4bytes} transmitted") 
    return out_float

def convertFloat2Bytes(float_val):
    """ Convert a float value to its single float format (a list of 4 int8 (4 Bytes))
    representation

    Parameters
    ----------
    float_val: float
    
    Returns
    -------
    list of 4 int8 representing float_val according thesingle float format

    Notes
    -----
    - see documentation of the EIT device"""
    return list(struct.pack(">f", float_val))

def convertBytes2Int(data_Bytes):
    """ Convert a list of int8 to an integer

    Parameters
    ----------
    data_Bytes: list of int8 representing an integer (e.g. [0x00, 0x01] >> int(1))
    
    Returns
    -------
    out_int: corresponding integer

    Notes
    -----
    - see documentation of the EIT device"""
    '''return a list of 4 int (4 Bytes)'''
    if len(data_Bytes)>1:
        out_int=int.from_bytes(bytearray(data_Bytes),"big")
    else:
        out_int=int.from_bytes(bytes(data_Bytes),"big")
    return out_int

def convertInt2Bytes(int_val, n_bytes):
    """ Convert an integer to its representaion as a list of int8 with n_bytes

    Parameters
    ----------
    int_val: int
        value to convert in list of int8
    n_bytes: int
        length of the output list
    
    Returns
    -------
    list of n_bytes int8

    Notes
    -----
    - see documentation of the EIT device"""
    return list((int(int_val)).to_bytes(n_bytes, byteorder='big'))

def getAllSubattributes(obj_):
    """ List all attributes  and subattributes of an object 

    Parameters
    ----------
    obj_: object
        value to convert in list of int8
    
    Returns
    -------
    data: misc
        values of the attributes  and subattributes of obj_ 
    name:  str
        of the attributes  and subattributes of obj_ 
    types: str
        types of the attributes  and subattributes of obj_
    
    Notes
    -----
    - use to load/save the setup of EIT device from/in an excel-file """

    import inspect
    attributes = inspect.getmembers(obj_, lambda a:not(inspect.isroutine(a)))
    attr=[a for a in attributes if not(a[0].startswith('__') and a[0].endswith('__'))]
    name= []
    data= []
    types= []
    for i in range(len(attr)):
        if sum([str(type(attr[i][1])).find(t) for t in ['list', 'float', 'int', 'str']])> 0:
            name.append(attr[i][0])
            data.append(attr[i][1])
        else:
            data_tmp, name_tmp, types_tmp = getAllSubattributes(getattr(obj_, attr[i][0]))
            name_tmp2=[]
            for name_i in name_tmp:
                name_tmp2.append(attr[i][0] + '.' +name_i)
            if len(data_tmp)>1:
                name.extend(name_tmp2)
                data.extend(data_tmp)
            else:
                name.append(name_tmp2)
                data.append(data_tmp)
    types = [type(item) for item in data]        
    return data, name , types

if __name__ == '__main__':
    pass
