# #!C:\Anaconda3\envs\py38_app python
# # -*- coding: utf-8 -*-

# """  Class to interact with the Sciospec device

# Copyright (C) 2021  David Metz

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>. """

# import datetime
# import os
# import pickle
# from os import listdir
# from os.path import isfile, join

# import numpy as np

# from eit_app.io.sciospec.device import SciospecSetup, convert4Bytes2Float, convertBytes2Int
# from eit_app.io.sciospec.com_constants import *

# __author__ = "David Metz"
# __copyright__ = "Copyright (c) 2021"
# __credits__ = ["David Metz"]
# __license__ = "GPLv3"
# __version__ = "2.0.0"
# __maintainer__ = "David Metz"
# __email__ = "d.metz@tu-bs.de"
# __status__ = "Production"

# ## ======================================================================================================================================================
# ##  Class for the DataSet obtained from the EIT Device
# ## ======================================================================================================================================================

# class EITDataSet(object):
#     """ Class EITDataSet: regroup Infos and frames of measurements """
#     def __init__(self, path):
#         self.initDataSet(SciospecSetup(32), path)
        
#     def initDataSet(self, dev_setup:SciospecSetup=SciospecSetup(32), path:str=None):
#         self.output_dir=path
#         self.name= path[path.rfind(os.path.sep)+1:]
#         self.dateTime= str(datetime.datetime.now())
#         self.dev_setup= dev_setup
#         self.Frame_cnt=0
#         self.Frame=[EITFrame(dev_setup)]
#         self._last_frame=[EITFrame(dev_setup)]
#         self.frequencyList= dev_setup.FrequencyConfig.mkFrequencyList()
#         self._FrameRef4TD=[EITFrame(dev_setup)]
        
    
#     def addRxData2DataSet(self, rx_data):
#         """ convert and add the recieved data to the dataset

#         Parameters
#         ----------
#         rx_data: list of int8  containing:
#             [ch_group, excitation+, excitation-, freq_indx_msb, freq_indx_lsb,
#             time_stamp_msb, time_stamp_2, time_stamp_1, time_stamp_lsb,
#             [real ch1], [imag ch1], ...., [real ch32], [imag ch32]]
        
#             where [real ch_i] and [imag ch_i] are single float format (4 Bytes)

#         Notes
#         -----
#         - see documentation of the EIT device    """

#         # extraxt and convert rx_data in the dataset
#         # print(rx_data)
#         ch_group= rx_data[0]
#         excitation=rx_data[1:3]
#         exc_indx= self._find_excitation_indx(excitation)
#         freq_indx= convertBytes2Int(rx_data[3:5])
#         time_stamp= convertBytes2Int(rx_data[5:9]) #not used...
 
#         u= rx_data[9:]
#         n_bytes_real_imag= 4 # we got 4Bytes per value
#         voltages_Z=[0] * 32
#         # maybe a faster sorting algorithem could be implemented....
#         for i in range(16): # the channel voltage meas. come per 16 packages: group1 1-16; group2 17-32
#             indx= 2*n_bytes_real_imag*i
#             ch= i+(ch_group-1)*16
#             voltages_Z[ch]=convert4Bytes2Float(u[indx:indx+n_bytes_real_imag]) + 1j*convert4Bytes2Float(u[indx+n_bytes_real_imag:indx+2*n_bytes_real_imag])
        
#         # sort rx_data in the dataset
        
#         self.Frame[0].Meas[freq_indx].frequency= self.frequencyList[freq_indx]
#         # add the voltages without writing over the old data (in the case of group 2)
#         tmp= self.Frame[0].Meas[freq_indx].voltage_Z[exc_indx] 
#         self.Frame[0].Meas[freq_indx].voltage_Z[exc_indx]= np.add(tmp, voltages_Z)

#         if False:
#             print(self.Frame_cnt, freq_indx)
#             print(self.Frame.Meas[freq_indx].frequency)
#             print(self.Frame.Meas[freq_indx].voltage_real)

#         if freq_indx == self.dev_setup.FrequencyConfig.Steps - 1: 
#             self.Frame[0].Meas_frame_cnt += 1 # will be increment 2*excitation_nb times at same freq_indx
        
#         # if frame complete Frame_cnt++ and append new Frame      
#         if self.Frame[0].Meas_frame_cnt == self.Frame[0].Meas_frame_num:
#             self.Frame[0].Frame_indx =  self.Frame_cnt # latch actual frame_cnt to the frame
#             self.mkInfoText4Frame(0)
#             self.saveSingleFrame(self.output_dir + os.path.sep+f'Frame{self.Frame_cnt:02}') # save dataset with one Frame
#             self._last_frame[0]=self.Frame[0] # latch actual to the _last_frame
#             if self.Frame_cnt == 0:
#                 self.setFrameRef4TD(0) # set automaticaly the reference frame fro TimeDiff measurement
#             self.Frame=[EITFrame(self.dev_setup)]
#             self.Frame_cnt += 1
            
#     def setFrameRef4TD(self, indx=0, path=None):
#         """ Latch Frame[indx] as reference for time difference mode
#         """
#         if path != None:
#              dataset_tmp=self.loadSingleFrame(path)
#              self._FrameRef4TD[0]=dataset_tmp.Frame[0]
#         else:
#             if indx==0:
#                 self._FrameRef4TD[0]=self._last_frame[0]
#             else:
#                 self._FrameRef4TD[0]=self.Frame[indx]

#     def saveSingleFrame(self,file_path):
#         """ Save single Frame to a .dat-file
#         Parameters
#         ----------
#         file_path: str
#             path of file without ending
        
#         Notes
#         -----
#         - such files can not be read..."""
#         ## maybe create a text_format of the dataset to save it as a txt-file
#         with open(file_path + '.dat', "wb") as fp:   #Pickling
#             pickle.dump(self, fp)

#     def loadSingleFrame(self, file_path):
#         """Load Dataset file (.dat)

#         Parameters
#         ----------
#         file_path: str
#             path of file

#         Returns
#         -------
#         dataset: "EITDataSet" object
        
#         Notes
#         -----
#         - such files can not be read..."""
#         ## maybe create a text_format of the dataset to load it as a txt-file
#         with open(file_path, "rb") as fp:   # Unpickling
#             dataset= pickle.load(fp)
#             return dataset
#     def search4FileWithExtension(self,dirpath, ext='.dat'):

#         only_files=[]
#         error = 0
#         try:
#             only_files = [f for f in listdir(dirpath) if isfile(join(dirpath, f)) and f[-len(ext):]==ext]
#             if not only_files: # if no files are contains
#                 error = 1
#         except (FileNotFoundError, TypeError): #cancel loading
#             pass

#         return only_files, error

#     def extract(self):
#         pass

#     def LoadDataSet(self, dirpath):
#         """Load Dataset files (.dat)

#         Parameters
#         ----------
#         dirpath: str
#             directory path of of the dataset

#         Returns
#         -------
#         only_files_ list of str
#             list of filename (), error
#         error: 1 if no frame files found, 2 if dirpath not given (canceled), 0 if everything loaded """
#         # only_files=[]
#         # error = 0

#         only_files, error =self.search4FileWithExtension(dirpath, ext='.dat')
#         if not error: # if no files are contains
#             dataset_tmp=EITDataSet(dirpath)
#             for i,filename in enumerate(only_files): # get all the frame data
#                 frame_path=dirpath+os.path.sep+filename
#                 dataset_tmp=self.loadSingleFrame(frame_path)
#                 if i ==0: 
#                     self.output_dir=dataset_tmp.output_dir
#                     self.name= dataset_tmp.name
#                     self.dateTime= dataset_tmp.dateTime
#                     self.dev_setup= dataset_tmp.dev_setup
#                     self.Frame=[] # reinit frame
#                     self.Frame_cnt=len(only_files)
#                     self.frequencyList= dataset_tmp.frequencyList
#                     self._FrameRef4TD= []
#                     self._FrameRef4TD.append(dataset_tmp.Frame[0])
#                 self.Frame.append(dataset_tmp.Frame[0])
#                 self.Frame[-1].loaded_frame_path= frame_path
#                 self.mkInfoText4Frame(i)


#         # try:
#         #     only_files = [f for f in listdir(dirpath) if isfile(join(dirpath, f)) and f[-4:]=='.dat']
#         #     if not only_files: # if no files are contains
#         #         error = 1
#         #     else:
#         #         dataset_tmp=EITDataSet(dirpath)
#         #         for i,filename in enumerate(only_files): # get all the frame data
#         #             frame_path=dirpath+os.path.sep+filename
#         #             dataset_tmp=self.loadSingleFrame(frame_path)
#         #             if i ==0: 
#         #                 self.output_dir=dataset_tmp.output_dir
#         #                 self.name= dataset_tmp.name
#         #                 print(self.name, self.output_dir)
#         #                 self.dateTime= dataset_tmp.dateTime
#         #                 self.dev_setup= dataset_tmp.dev_setup
#         #                 self.Frame=[] # reinit frame
#         #                 self.Frame_cnt=len(only_files)
#         #                 self.frequencyList= dataset_tmp.frequencyList
#         #                 self._FrameRef4TD= []
#         #                 self._FrameRef4TD.append(dataset_tmp.Frame[0])
#         #             self.Frame.append(dataset_tmp.Frame[0])
#         #             self.Frame[-1].loaded_frame_path= frame_path
#         #             self.mkInfoText4Frame(i)
#         # except (FileNotFoundError, TypeError): #cancel loading
#         #     error = 2

#         return only_files, error

#     def _find_excitation_indx(self, excitation):
#         """ Return the index of the given excitation in the excitation_Pattern

#         Parameters
#         ----------
#         excitation: list of int (e.g. [1, 2])

#         Returns
#         -------
#         indx: int
#             index of the given excitation in self.dev_setup.excitation_Pattern """
#         indx = 0
#         for Exc_i in self.dev_setup.Excitation_Pattern:
#             if Exc_i== excitation:
#                 break
#             indx= indx+1
#         return indx

#     def mkInfoText4Frame(self, indx):
#         """ Create a tex with information about the Frame nb indx
        
#         Parameters
#         ----------
#         indx: int
#             index of the frame
        
#         Notes
#         -----
#         save the text under Frame[indx].infoText """
#         if indx==-1:
#             frame=self.Frame
#         else:
#             frame=self.Frame[indx]

#         frame.infoText= [ f"Dataset name:\t{self.name}",
#                     f"Frame#:\t{frame.Frame_indx}",
#                     f"TimeStamps:\t{self.dateTime}",
#                     f"Sweepconfig:\tFmin = {self.dev_setup.FrequencyConfig.Min_F_Hz/1000:.3f} kHz,\r\n\tFmax = {self.dev_setup.FrequencyConfig.Max_F_Hz/1000:.3f} kHz",
#                     f"\tFSteps = {self.dev_setup.FrequencyConfig.Steps:.0f},\r\n\tFScale = {self.dev_setup.FrequencyConfig.Scale}",
#                     f"\tAmp = {self.dev_setup.Excitation_Amplitude:.5f} A,\r\n\tFrameRate = {self.dev_setup.Frame_rate:.3f} fps",
#                     f"excitation:\t{self.dev_setup.Excitation_Pattern}"]
        

# class EITFrame(object):
#     """ Class Frame: regroup the voltages values for all frequencies at timestamps
#     for all excitation and for one frequency

#     Notes
#     -----
#     e.g. Meas[2] the measured voltages on each channel (VS a commmon GROUND) for the frequency_nb 2
#             for the frequency = frequency_val"""
#     def __init__(self, setup):
#         self.Frame_timestamps=0
#         self.Frame_indx= 0
#         self.Meas_frame_num=len(setup.Excitation_Pattern)*2 # for x excitation x*2 meas are send
#         self.Meas_frame_cnt=0 # cnt 
#         self.Meas=[EITMeas(setup) for i in range(setup.FrequencyConfig.Steps)] # Meas[Frequency_indx]
#         self.infoText=''
#         self.loaded_frame_path=''
    

# class EITMeas(object):
#     """ Class measurement: regroup the voltage values of all channels of the EIT device
#     for all excitation and for one frequency

#     Notes
#     -----
#     e.g. voltage_Z[1][:] the measured voltages on each channel (VS a commmon GROUND) for excitation 1
#             for the frequency = frequency_val"""
#     def __init__(self, setup):
#         ch=setup.Channel
#         self.voltage_Z=[[0 for i in range(ch)] for j in range(len(setup.Excitation_Pattern))]
#         self.frequency=0 # corresponding excitation frequency
