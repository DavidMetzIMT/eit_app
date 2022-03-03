
import ast
from genericpath import isdir
import math
import os
from logging import getLogger
from typing import List, Union
from matplotlib import pyplot as plt

import numpy as np
import pandas as pd
from eit_app.app.dialog_boxes import show_msgBox
from eit_app.io.sciospec.com_constants import *
from eit_app.io.sciospec.utils import *
# from eit_app.utils.utils_path import save_as_pickle
from glob_utils.files.files import (DataLoadedNotCompatibleError, FileExt,
                                    OpenDialogFileCancelledException,
                                    dialog_get_file_with_ext, load_pickle_app, save_as_pickle,
                                    search_for_file_with_ext)
from glob_utils.pth.path_utils import (OpenDialogDirCancelledException,
                                       get_datetime_s, get_dir)

logger = getLogger(__name__)


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
        self.reinit(ch)
        
    def reinit(self, ch):
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

    def compute_max_frame_rate(self):
        """ Compute the maximum frame rate corresponding to the actual frequencies sweep 

        Notes
        -----
        - see documentation of the EIT device"""
        f_i = self.freq_config.make_freqs_list() #ndarray

        n_freq = float(self.freq_config.freq_steps)
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
        if self.frame_rate>self.max_frame_rate:
            self.frame_rate=self.max_frame_rate

    def save(self, dir:str=None):
        """ Save the setup in pkl file"""
        try:
            if not dir:
                dir= get_dir(
                    title='Select a directory, where the setup will be saved')
            file=os.path.join(dir, f'setup_{get_datetime_s()}')
            save_as_pickle(file, self)
            logger.info(f'Setup: {self.__dict__} \n saved in file : {dir} ')
        except OpenDialogDirCancelledException as e:
            logger.info(f'Saving setup cancelled:({e})')

    def load(self, path:str=None):
        """ Load the setup out of a pkl file """
        try:
            print(f'{path=}')
            if path is None:
                file_path = dialog_get_file_with_ext(ext=FileExt.pkl)
            elif isdir(path):
                files= search_for_file_with_ext(path,ext=FileExt.pkl)
                file_path=[f for f in files if 'setup_' in f]
                file_path= os.path.join(path,file_path[0])

            if 'setup_' not in file_path:
                logger.error('tryed to load a non setup file')
                return

            load_pickle_app(file_path,self)
            # set_attributes(self,loaded_setup)
            logger.info(f'Setup: {self.__dict__} \n loaded from file : {file_path} ')
        except OpenDialogFileCancelledException as e:
            # show_msgBox('Loading cancelled','', "I")
            logger.info(f'Loading cancelled {e}')
        except DataLoadedNotCompatibleError:
            show_msgBox('Please select a setup file', 'Not a setup file', "Warning")
            # print('wrong pickle file choosen!!!')

    ## Get methods
    def get_channel(self):
        """ Return the number of channnel used in the device"""
        return self.device_infos.channel

    def get_exc_amp_d(self, for_ser:bool=False)-> Union[List[bytes], float]:
        """ Return excitation amplitude (double precision):
        - in Bytes for sending to the device
        - in float for simple get """
        return [0x00] if for_ser else self.exc_amp

    def get_exc_amp(self, for_ser:bool=False)-> Union[List[bytes], float]:
        """ Return excitation amplitude (single precision):
        - in Bytes for sending to the device
        - in float for simple get """
        return convertFloat2Bytes(self.exc_amp) if for_ser else self.exc_amp

    def get_burst(self, for_ser:bool=False)-> Union[List[bytes], float]:
        """ Return burst:
        - in Bytes for sending to the device
        - in float for simple get """
        return convertInt2Bytes(self.burst, 2) if for_ser else self.burst 

    def get_frame_rate(self, for_ser:bool=False)-> Union[List[bytes], float]:
        """ Return frame rate:
        - in Bytes for sending to the device
        - in float for simple get """
        return convertFloat2Bytes(self.frame_rate) if for_ser else self.frame_rate

    def get_max_frame_rate(self)-> float:
        """ Return max frame rate computed from the used frequence config"""
        return self.max_frame_rate

    def get_freq_config(self, for_ser:bool=False)-> List[bytes]:
        """ Return the used frequence config:
        - in Bytes for sending to the device"""
        if not for_ser:
            return []
        data =[]
        data=convertFloat2Bytes(self.freq_config.freq_min)
        data.extend(convertFloat2Bytes(self.freq_config.freq_max))
        data.extend(convertInt2Bytes(self.freq_config.freq_steps, 2)) # Steps is defined on 2 bytes
        if self.freq_config.freq_scale== OP_LINEAR.name:
            data.append(OP_LINEAR.tag)
        elif self.freq_config.freq_scale== OP_LOG.name:
            data.append(OP_LOG.tag)
        else:
            raise TypeError("wrong Scale Str")
        return data

    def get_freq_min(self)-> float: 
        """ Return the min frequency used to build the frequencies list"""
        return self.freq_config.freq_min

    def get_freq_max(self)-> float:
        """ Return the max frequency used to build the frequencies list"""
        return self.freq_config.freq_max

    def get_freq_scale(self)-> str:
        """ Return the scale used between min and max frequencies to build the frequencies list"""
        return self.freq_config.freq_scale

    def get_freq_steps(self)-> int:
        """ Return the number of steps used between min and max frequencies to build the frequencies list"""
        return self.freq_config.freq_steps

    def get_freqs(self)->List[float]:
        """ Return the frequencies list"""
        return  self.freq_config.freqs
    
    def get_exc_pattern(self, for_ser:bool=False)-> Union[List[bytes], List[List[bytes]]]:
        """ Return excitation pattern:
        - in Bytes for sending to the device (only one index)
        - in float for simple get (the whole list)"""
        return list(self.exc_pattern[self.exc_pattern_idx]) if for_ser else self.exc_pattern

    def get_exc_stamp(self, for_ser:bool=False)-> Union[List[bytes], bool]:
        """ Return excitation stamp from output config:
        - in Bytes for sending to the device
        - in bool for simple get"""
        return [int(self.output_config.exc_stamp)] if for_ser else self.output_config.exc_stamp

    def get_current_stamp(self, for_ser:bool=False)-> Union[List[bytes], bool]:
        """ Return current stamp from output config:
        - in Bytes for sending to the device
        - in bool for simple get"""
        return [int(self.output_config.current_stamp)]if for_ser else self.output_config.current_stamp

    def get_time_stamp(self, for_ser:bool=False)-> Union[List[bytes], bool]:
        """ Return time stamp from output config:
        - in Bytes for sending to the device
        - in bool for simple get"""
        return [int(self.output_config.time_stamp)] if for_ser else self.output_config.time_stamp

    def get_sn(self, for_ser:bool=False)-> Union[List[bytes], str]:
        """ Return serial number:
        - in Bytes for sending to the device (NOT USED, SN can't be changed..)
        - in str for simple get"""
        return self.device_infos.sn if for_ser else self.device_infos.sn_formated

    def get_ip(self, for_ser:bool=False)-> Union[List[bytes], str]:
        """ Return ip adress:
        - in Bytes for sending to the device
        - in str for simple get"""
        return self.ethernet_config.ip if for_ser else self.ethernet_config.ip_formated

    def get_mac(self, for_ser:bool=False)-> Union[List[bytes], str]:
        """ Return mac adress:
        - in Bytes for sending to the device (NOT USED, MAC ADRESS can't be changed..)
        - in str for simple get"""
        return self.ethernet_config.mac if for_ser else self.ethernet_config.mac_formated

    def get_dhcp(self, for_ser:bool=False)-> Union[List[bytes], bool]:
        """ Return dhcp:
        - in Bytes for sending to the device
        - in bool for simple get"""
        return [int(self.ethernet_config.dhcp)] if for_ser else self.ethernet_config.dhcp
    
    ## Set methods

    def set_channel(self, ch:int=32):
        """ Set value of channel of the device"""
        self.device_infos.channel= ch

    def set_exc_amp_d(self, value:Union[List[bytes], float], for_ser:bool=False):
        """ Set value of excitation amplitude (double precision):
        - out of Bytes from the device (rx_frame)
        - from a float for simple set """
        self.exc_amp =convert4Bytes2Float(value[DATA_START_INDX:-1]) if for_ser else value

    def set_exc_amp(self, value:Union[List[bytes], float], for_ser:bool=False):
        """ Set value of excitation amplitude (single precision):
        - out of Bytes from the device (rx_frame)
        - from a float for simple set """
        self.exc_amp =convert4Bytes2Float(value[DATA_START_INDX:-1]) if for_ser else value

    def set_burst(self, value:Union[List[bytes], int], for_ser:bool=False):
        """ Set value of burst:
        - out of Bytes from the device (rx_frame)
        - from an int for simple set """
        self.burst =convertBytes2Int(value[DATA_START_INDX:-1]) if for_ser else value 
        
    def set_frame_rate(self, value:Union[List[bytes], float], for_ser:bool=False):
        """ Set value of frame rate:
        - out of Bytes from the device (rx_frame)
        - from a float for simple set """
        self.frame_rate=convert4Bytes2Float(value[DATA_START_INDX:-1]) if for_ser else value if value>0 else 1.0
        
    def set_freq_config(self, value:List[bytes]=None, for_ser:bool=False, **kwargs):
        """ Set values of frequence config:
        - out of Bytes from the device (rx_frame)
        - from a **kwargs from freq_config.set_data for simple set """
        if for_ser:
            data= value[DATA_START_INDX:-1]
            scale={OP_LINEAR.tag:OP_LINEAR.name, OP_LOG.tag:OP_LOG.name}
            freq_max_enable, error = self.freq_config.set_data(
                freq_min=convert4Bytes2Float(data[:4]),
                freq_max=convert4Bytes2Float(data[4:8]),
                freq_steps=convertBytes2Int(data[8:10]),
                freq_scale=scale[data[10]],
            )

        else:
            freq_max_enable, error=self.freq_config.set_data(**kwargs)

        self.compute_max_frame_rate()
        return freq_max_enable, error
        
            # if data[10]== OP_LINEAR.tag:
            #     self.freq_config.freq_scale=OP_LINEAR.name
            # elif data[10]== OP_LOG.tag:
            #     self.freq_config.freq_scale=OP_LOG.name
            # else:
            #     raise TypeError("wrong scale byte")
        
    # def set_freq_config(self, freq_min:float=1000.0, freq_max:float=10000.0, steps:int=1, scale:str=''):
    #     freq_max_enable, error=self.freq_config.set_data(freq_min, freq_max, steps, scale)
    #     self.compute_max_frame_rate()
    #     return freq_max_enable, error
    
    def set_exc_pattern(self, value:Union[List[bytes], List[List[int]]], for_ser:bool=False):
        """ Set excitation pattern:
        - out of Bytes from the device (rx_frame)
        - from a List for simple set """
        if for_ser:
            data= value[DATA_START_INDX:-1]
            self.exc_pattern = [data[i*2:(i+1)*2] for i in range(len(data)//2)]
        else:
            self.exc_pattern=value

    def set_exc_stamp(self, value:Union[List[bytes], bool], for_ser:bool=False):
        """ Set value of excitation stamp from output config:
        - out of Bytes from the device (rx_frame)
        - from a bool for simple set """
        self.output_config.exc_stamp= True# bool(value[DATA_START_INDX:-1][0]) if for_ser else value
        
    def set_current_stamp(self, value:Union[List[bytes], bool], for_ser:bool=False):
        """ Set value of current stamp from output config:
        - out of Bytes from the device (rx_frame)
        - from a bool for simple set """
        self.output_config.current_stamp=True# bool(value[DATA_START_INDX:-1][0]) if for_ser else value
        
    def set_time_stamp(self, value:Union[List[bytes], bool], for_ser:bool=False):
        """ Set value of time stamp from output config:
        - out of Bytes from the device (rx_frame)
        - from a bool for simple set """
        self.output_config.time_stamp=True# bool(value[DATA_START_INDX:-1][0]) if for_ser else value
        
    def set_ip(self, value:Union[List[bytes], str], for_ser:bool=False):
        """ Set value of ip adress:
        - out of Bytes from the device (rx_frame)
        - from a str for simple set (NOT IMPLEMENTED)"""
        if for_ser:
            data= value[DATA_START_INDX:-1]
            length= LENGTH_IP_ADRESS
            self.ethernet_config.ip= data[:length]
            self.ethernet_config.ip_formated = (
                f'{str(data[0])}.{str(data[1])}.{str(data[2])}.{str(data[3])}'
            )

        else:
            raise Exception('not implemented') # TODO

    def set_mac(self, value:Union[List[bytes], str], for_ser:bool=False):
        """ Set value of mac adress:
        - out of Bytes from the device (rx_frame)
        - (error)"""
        if for_ser:
            data= value[DATA_START_INDX:-1]
            length= LENGTH_MAC_ADRESS
            self.ethernet_config.mac= data[:length]
            ID= mkListOfHex(data[:length])
            self.ethernet_config.mac_formated = (
                f'{ID[0]}:{ID[1]}:{ID[2]}:{ID[3]}:{ID[4]}:{ID[5]}'
            )

        else:
            raise Exception('Error in use of this method')

    def set_dhcp(self, value:Union[List[bytes], bool], for_ser:bool=False):
        """ Set value of dhcp:
        - out of Bytes from the device (rx_frame)
        - from a bool for simple set"""
        self.ethernet_config.dhcp=True# bool(value[DATA_START_INDX:-1][0]) if for_ser else value
    
    def set_sn(self, value:Union[List[bytes], float], for_ser:bool=False):
        """ Set value of mac adress:
        - out of Bytes from the device (rx_frame)
        - (error)"""
        if for_ser:
            rx_op_data= value[OPTION_BYTE_INDX:-1]
            length = LENGTH_SERIAL_NUMBER
            self.device_infos.sn= rx_op_data[:length]
            ID= mkListOfHex(rx_op_data[:length])
            self.device_infos.sn_formated = (
                f'{ID[0]}-{ID[1]}{ID[2]}-{ID[3]}{ID[4]}-{ID[5]}{ID[6]}'
            )

        else:
            raise Exception('Error in use of this method')

    def set_exc_pattern_idx(self, idx:int):
        """ Set value of idx of actual pattern:
        used to latch each pattern for setting exc_pattern to the device"""
        self.exc_pattern_idx=idx

    def make_freqs_list(self):
        """ Make the frequencies list and return it"""
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
        self.freq_min= float(1000.0)
        self.freq_max= float(1000.0)
        self.freq_steps= int(1)
        self.freq_scale= OP_LINEAR.name
        self.freqs=[]
        self.make_freqs_list()
        
        
    def make_freqs_list(self):
        """ Make the Frequencies list of frequencies accoreding to the 
        frequency sweep configuration

        Notes
        -----
        - see documentation of the EIT device"""
        if self.freq_scale==OP_LINEAR.name:
            self.freqs= np.linspace(self.freq_min,self.freq_max, self.freq_steps)
        elif self.freq_scale==OP_LOG.name:
            freq_min= np.log10(self.freq_min)
            freq_max = np.log10(self.freq_max)
            self.freqs= np.logspace(freq_min,freq_max, self.freq_steps)
        else:
            TypeError('incorrect scale')
        return self.freqs
    

    def set_data(self, freq_min:float=1000.0, freq_max:float=10000.0, freq_steps:int=1, freq_scale:str=''):

        self.freq_min=freq_min
        self.freq_max= freq_max
        self.freq_scale= freq_scale if freq_scale in [OP_LINEAR.name, OP_LOG.name] else OP_LINEAR.name
        self.freq_steps = freq_steps or 1

        # Set minF and maxF
        if self.freq_steps == 1:
            set_freq_max_enable= False
            self.freq_max=self.freq_min
            error= False
        else:# be sure that minF < maxF
            set_freq_max_enable= True
            if self.freq_max<=self.freq_min:
                self.freq_max=self.freq_min
                error=True
            else:
                error= False
        
        self.freqs= self.freq_min if error else self.make_freqs_list()

        return set_freq_max_enable, error


if __name__ == '__main__':

    freq_min = np.log10(100)
    freq_max = np.log10(1000)
    freq_steps = 10


    freqs= np.logspace(freq_min,freq_max,freq_steps)
    print(f'{freqs=}')
    plt.plot(np.array(freqs))
    plt.show()