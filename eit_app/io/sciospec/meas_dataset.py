#!C:\Anaconda3\envs\py38_app python
# -*- coding: utf-8 -*-

"""  Class to interact with the Sciospec device

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


import os
from logging import getLogger
from sys import argv
from PyQt5.QtWidgets import QApplication

import numpy as np
from eit_app.app.dialog_boxes import show_msgBox

from eit_app.io.sciospec.com_constants import OPTION_BYTE_INDX
from eit_app.io.sciospec.device_setup import SciospecSetup
from eit_app.io.sciospec.utils import convertBytes2Int,convert4Bytes2Float
from eit_app.utils.constants import EXT_PKL, MEAS_DIR
from eit_app.utils.flag import CustomFlag
from eit_app.utils.utils_path import (CancelledError, append_date_time, get_date_time, get_dir, load_pickle,
                                      mk_ouput_dir, save_as_pickle,
                                      search_for_file_with_ext, set_attributes)

__author__ = "David Metz"
__copyright__ = "Copyright (c) 2021"
__credits__ = ["David Metz"]
__license__ = "GPLv3"
__version__ = "2.0.0"
__maintainer__ = "David Metz"
__email__ = "d.metz@tu-bs.de"
__status__ = "Production"

logger = getLogger(__name__)

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
        self.rx_meas_frame=None
        self.meas_frame=None
        self.freqs_list= None
        self._frame_TD_ref=None
        self.flag_new_meas=CustomFlag()
        self.autosave=CustomFlag()
        self.autosave.set()


    def init_for_gui(self,dev_setup:SciospecSetup= SciospecSetup(32), name_measurement:str=None):
        # self.date_time= get_date_time()
        self.name= name_measurement#append_date_time(name_measurement, self.date_time)
        self.output_dir=None #mk_ouput_dir(self.name, default_out_dir=MEAS_DIR)
        self.dev_setup= dev_setup
        self.frame_cnt=0
        self.rx_meas_frame=[EITFrame(dev_setup)]
        self.meas_frame=[EITFrame(dev_setup)]
        self.freqs_list= dev_setup.make_freqs_list()
        self._frame_TD_ref=[EITFrame(dev_setup)]
        return self.name, self.output_dir
        
    def prepare_for_aquisition(self,dev_setup:SciospecSetup, name_measurement:str=None):
        self.date_time= get_date_time()
        self.name= append_date_time(name_measurement, self.date_time)
        self.output_dir=mk_ouput_dir(self.name, default_out_dir=MEAS_DIR)
        self.dev_setup= dev_setup
        self.frame_cnt=0
        self.rx_meas_frame=[EITFrame(dev_setup)]
        self.meas_frame=[EITFrame(dev_setup)]
        self.freqs_list= dev_setup.make_freqs_list()
        self._frame_TD_ref=[EITFrame(dev_setup)]
        self.flag_new_meas=CustomFlag()
        return self.name, self.output_dir
    



    def add_rx_frame_to_dataset(self, rx_frame, for_ser:bool=False, idx:int=0):
        """ add the data from the rx_frame in the dataset 
        (is called when measuring rx_frame have been recieved)"""

        data =self.extract_data(rx_frame)
        # self.append(frame, idx_frm=0)
        self.rx_meas_frame[idx].add_data(data,self.frame_cnt)
        # if frame complete Frame_cnt+ and append new Frame
        if self.rx_meas_frame[idx].is_complete():
            self.frame_save_and_prepare_for_next_rx(idx)

    def frame_save_and_prepare_for_next_rx(self, idx:int=0):
        self.make_info_text_for_frame(idx)
        self.meas_frame[0]=self.rx_meas_frame[idx] # latch actual to the _last_frame
        if self.frame_cnt == 0:
            self.set_frame_TD_ref(idx) # init the reference frame for Time difference measurement
        self.rx_meas_frame[idx]=EITFrame(self.dev_setup) # clear frame 
        if self.autosave.is_set():
            self.save_dataset_single_frame()
        self.frame_cnt += 1
        # self.flag_new_meas.set()
        self.flag_new_meas.set_edge_up()

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
        meas_f=[convert4Bytes2Float(m) for m in meas_data] # conversion of each 4 bytes
        meas_r_i=np.reshape(np.array(meas_f), (-1,2)) # get a matrix with real and imag values in each column
        return meas_r_i[:,0]+1j*meas_r_i[:,1]

    def set_frame_TD_ref(self, indx=0, path=None):
        """ Latch Frame[indx] as reference for time difference mode
        """
        if path is None:
            self._frame_TD_ref[0] = self.meas_frame[0] if indx==0 else self.rx_meas_frame[indx]
        else:
            dataset_tmp:EitMeasurementDataset=self.load_dataset_single_frame(path)
            self._frame_TD_ref[0]=dataset_tmp.meas_frame[0]
    

    def save_dataset_single_frame(self):
        filename= os.path.join(self.output_dir, f'Frame{self.frame_cnt:02}')
        save_as_pickle(filename, self)

    def load_single_frame(self, file_path):
        dataset_tmp:EitMeasurementDataset=self.load_dataset_single_frame(file_path)
        self.meas_frame[0]=dataset_tmp.meas_frame[0]

    def load_dataset_single_frame(self, file_path):
        """Load Dataset file with single frame"""
        return load_pickle(file_path)

    def load_dataset_dir(self, dir_path:str=None):
        """Load Dataset files """
        try:
            if not dir_path:
                dir_path= get_dir(title='Select a directory of the measurement dataset you want to load') 
            filenames =search_for_file_with_ext(dir_path, ext=EXT_PKL)
            # print('filepaths', filenames)
        except FileNotFoundError:
            show_msgBox(f'No {EXT_PKL}-files in directory dirpath!', 'NO Files FOUND', 'Warning')
            return
        except CancelledError:
            print('Loading cancelled')
            return
        
        for filename in filenames:
            if 'setup' in filename:
                filenames.remove(filename)
        if not filenames:
            show_msgBox(f'No frames-files in directory dirpath!', 'NO Files FOUND', 'Warning')
            return
        # print('filepaths', filenames)
        for i,filename in enumerate(filenames): # get all the frame data
            filepath=os.path.join(dir_path, filename)
            dataset_tmp:EitMeasurementDataset=self.load_dataset_single_frame(filepath)
            if i ==0:
                set_attributes(self,dataset_tmp)
                setattr(self, 'output_dir', dir_path)
                    # if key not in self.__dict__.keys():
                    #     print(f'key:{key} not found')
                    # setattr(self, key, getattr(dataset_tmp,key))

                # self.output_dir=dataset_tmp.output_dir
                # self.name= dataset_tmp.name
                # self.date_time= dataset_tmp.dateTime
                # self.dev_setup= dataset_tmp.dev_setup
                # self.frame=[] # reinit frame
                # self.frame_cnt=len(only_files)
                # self.freqs_list= dataset_tmp.frequencyList
                # self._frame_TD_ref= []
                # self._frame_TD_ref.append(dataset_tmp.Frame[0])
            else:
                # setattr(self, 'frame_cnt', getattr(dataset_tmp,'frame_cnt'))
                self.meas_frame.append(dataset_tmp.meas_frame[0])
            self.meas_frame[-1].loaded_frame_path= filepath
        setattr(self, 'frame_cnt', len(self.meas_frame) )
        # print(self.__dict__)

        return filenames

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
        frame = self.rx_meas_frame if indx==-1 else self.rx_meas_frame[indx]
        frame.info_text= [ f"Dataset name:\t{self.name}",
                    f"Frame#:\t{frame.idx}",
                    f"TimeStamps:\t{self.date_time}",
                    f"Sweepconfig:\tFmin = {self.dev_setup.get_freq_min()/1000:.3f} kHz,\r\n\tFmax = {self.dev_setup.get_freq_max()/1000:.3f} kHz",
                    f"\tFSteps = {self.dev_setup.get_freq_steps():.0f},\r\n\tFScale = {self.dev_setup.get_freq_scale()}",
                    f"\tAmp = {self.dev_setup.get_exc_amp():.5f} A,\r\n\tFrameRate = {self.dev_setup.get_frame_rate():.3f} fps",
                    f"excitation:\t{self.dev_setup.get_exc_pattern()}"]
                
    def get_filling(self, idx_frame:int=0):
        return self.rx_meas_frame[idx_frame].filling

    def get_voltages_ref_frame(self, idx_freq:int=0)-> np.ndarray:

        return self._frame_TD_ref[0].get_voltages(idx_freq)
    
    def get_idx_ref_frame(self)-> int:

        return self._frame_TD_ref[0].get_idx()

    def get_idx_frame(self, idx_frame:int=0)-> int:

        return self.meas_frame[idx_frame].get_idx()

    def get_voltages(self, idx_frame:int=0, idx_freq:int=0)-> np.ndarray:
        """Return the measured voltage for the given frequency index"""
        try:
            return self.meas_frame[idx_frame].get_voltages(idx_freq)
        except IndexError:
            print(f'try to access index {idx_frame} in meas_frame {self.meas_frame},{len(self.meas_frame)}')
            return self.meas_frame[0].get_voltages(idx_freq)
           
    def get_freqs_list(self):
        return self.freqs_list
    def get_freq_val(self, idx_freq:int=0):
        try:
            return self.freqs_list[idx_freq]
        except IndexError:
            print(f'try to access index {idx_freq} in fregs_list {self.freqs_list}')
            return self.freqs_list[0]
    def get_info(self, idx_frame:int=0):
        return self.meas_frame[idx_frame].info_text


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
        self.filling:int=0 # pourcentage of filling
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
            self.compute_filling()
            
    def compute_filling(self):
        self.filling= int(self.meas_frame_cnt/(self.meas_frame_nb+1)*100)

    def is_very_first_data(self, data):
        """retrun if data is the very first one for this frame"""
        return data['ch_group']+data['freq_indx']+data['exc_indx']==1

    def is_all_freqs_aquired(self, data):
        """return if all meas for all freqs were aquired for this frame"""
        return data['freq_indx'] == self.freq_steps - 1
    
    def get_voltages(self, idx_freq:int=0)-> np.ndarray:
        """Return the measured voltage for the given frequency index"""
        try:
            return self.meas[idx_freq].get_voltages()
        except IndexError:
            print(f'try to access index {idx_freq} in meas {self.meas},{len(self.meas)}')
            return self.meas[0].get_voltages()
           
    
    def get_idx(self)-> int:
        return self.idx

class EITMeas(object):
    """ Class measurement: regroup the voltage values of all channels of the EIT device
    for all excitation and for one frequency

    Notes
    -----
    e.g. voltage_Z[1][:] the measured voltages on each channel (VS a commmon GROUND) for excitation 1
            for the frequency = frequency_val"""
    def __init__(self, dev_setup:SciospecSetup):
        # self.voltage_Z=[np.zeros(dev_setup.get_channel(),dtype=complex) for j in range(len(dev_setup.get_exc_pattern()))]
        self.voltage_Z=np.zeros((len(dev_setup.get_exc_pattern()),dev_setup.get_channel()),dtype=complex)
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
        self.voltage_Z[exc_indx,start_idx:end_idx]= volt

    def get_voltages(self)-> np.ndarray:
        """Return the measured voltage"""
        return self.voltage_Z#np.array(self.voltage_Z)



if __name__ == '__main__':
    from eit_app.io.sciospec.meas_dataset import EitMeasurementDataset
    app = QApplication(argv)
    # # rec2ui_queue = NewQueue()
    # app.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    # # ui = UiBackEnd(queue_in=rec2ui_queue, queue_out=ui2rec_queue, image_reconst=rec)
    # ui = UiBackEnd()
    # ui.show()
    # p = Process(target=_poll_process4reconstruction, args=(ui2rec_queue,rec2ui_queue,rec))
    # p.daemon=True
    # p.start()
    d = EitMeasurementDataset()
    d.load_dataset_dir()
    exit(app.exec_()) 


    