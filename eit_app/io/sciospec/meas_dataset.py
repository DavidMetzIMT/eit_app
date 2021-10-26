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
import pickle

import numpy as np
from eit_app.io.sciospec.com_constants import OPTION_BYTE_INDX
from eit_app.io.sciospec.device_setup import SciospecSetup
from eit_app.io.sciospec.utils import *
from eit_app.utils.constants import EXT_PKL, MEAS_DIR
from eit_app.utils.log import main_log
from eit_app.utils.utils_path import (append_date_time, get_date_time,
                                      mk_ouput_dir, save_as_pickle,
                                      search4FileWithExtension)

__author__ = "David Metz"
__copyright__ = "Copyright (c) 2021"
__credits__ = ["David Metz"]
__license__ = "GPLv3"
__version__ = "2.0.0"
__maintainer__ = "David Metz"
__email__ = "d.metz@tu-bs.de"
__status__ = "Production"

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
                frame_path=dirpath+ os.path.sep+filename
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
