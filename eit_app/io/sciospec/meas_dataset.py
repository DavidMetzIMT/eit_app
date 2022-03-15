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


from copy import deepcopy
from dataclasses import dataclass
import os
from logging import getLogger
from sys import argv
from typing import Tuple, Union

import numpy as np
from default.set_default_dir import APP_DIRS, AppDirs
from eit_app.app.dialog_boxes import show_msgBox
from eit_app.app.update_event import FrameInfo, FrameProgress
# from eit_app.app.update_event import UpdateEvents
from eit_app.eit.computation import ComputeMeas, Data2Compute
from eit_app.io.sciospec.com_constants import OPTION_BYTE_INDX
from eit_app.io.sciospec.device_setup import SciospecSetup
from eit_app.io.sciospec.utils import convert4Bytes2Float, convertBytes2Int
from eit_app.io.video.microcamera import VideoCaptureModule
from glob_utils.files.files import (
    FileExt,
    load_pickle_app,
    save_as_pickle,
    search_for_file_with_ext,
    set_attributes,
)
from glob_utils.flags.flag import CustomFlag
from glob_utils.pth.path_utils import (
    OpenDialogDirCancelledException,
    append_date_time,
    get_datetime_s,
    get_dir,
    mk_new_dir,
)
from glob_utils.unit.unit import eng
from glob_utils.decorator.decorator import catch_error

from glob_utils.thread_process.signal import Signal


__author__ = "David Metz"
__copyright__ = "Copyright (c) 2021"
__credits__ = ["David Metz"]
__license__ = "GPLv3"
__version__ = "2.0.0"
__maintainer__ = "David Metz"
__email__ = "d.metz@tu-bs.de"
__status__ = "Production"

logger = getLogger(__name__)

@dataclass
class RXFrameData:
    ch_group:int
    exc_indx:int
    freq_indx:int
    time_stamp:int
    voltages:np.ndarray

    def __post_init__(self):
        logger.debug(f'{self.ch_group=}, {self.exc_indx=}, {self.freq_indx=}, {self.time_stamp=}, {self.voltages=}')

    def is_first(self):
        return self.ch_group + self.freq_indx + self.exc_indx == 1


## =============================================================================
##  Class for the DataSet obtained from the EIT Device
## =============================================================================


class EitMeasurementSet(object):
    """Class EITDataSet: regroups infos and frames of measurements"""

    def __init__(self):
        # self.queue_out_video_module:Queue=None
        self.time_stamps = None
        self.name = None
        self.output_dir = None
        self.dev_setup = None
        self.frame_cnt = None
        self.rx_meas_frame: EITFrame = None
        self.meas_frame:list[EITFrame] = []
        # self.freqs_list = None
        # self._ref_frame:EITFrame = None
        self._ref_frame_idx:int =0
        self.flag_new_meas = CustomFlag()
        self.autosave = CustomFlag()
        self.autosave.set()
        self.save_img = CustomFlag()
        self.new_frame=Signal(self)
     

    ## =========================================================================
    ##  Aquisition
    ## =========================================================================

    def initForAquisition(self, dev_setup: SciospecSetup, name_measurement: str = None)-> Tuple[str, str]:

        self.time_stamps = get_datetime_s()
        self.name = append_date_time(name_measurement, self.time_stamps)
        self.output_dir = None
        if self.autosave.is_set():
            self.output_dir = mk_new_dir(self.name, APP_DIRS.get(AppDirs.meas_set))
        
        self.dev_setup = dev_setup
        self.frame_cnt = 0
        self.meas_frame = [None]
        # self.freqs_list = dev_setup.make_freqs_list()
        # self._ref_frame = None
        self._ref_frame_idx =0
        self.flag_new_meas = CustomFlag()
        
        self.init_rx_frame()

        return self.name, self.output_dir
    
    def init_rx_frame(self)-> None:
        self.rx_meas_frame = EITFrame(
            self.frame_cnt, self.dev_setup, self.output_dir, self.time_stamps
        )

    def init_resume(self):
        self.init_rx_frame()
        # self.rx_meas_frame = EITFrame(self.dev_setup)  # clear frame

    def add_rx_frame_to_dataset(self, rx_frame, for_ser: bool = False):
        """add the data from the rx_frame in the dataset
        (is called when measuring rx_frame have been recieved)
        attention for_ser need to be defined"""

        self.rx_meas_frame.add_data(rx_frame)
        self.emit_progression()

        if not self.rx_meas_frame.is_complete():
            return
        
        logger.info(f"Frame #{self.frame_cnt} - complete")
        idx=0
        self.meas_frame[idx] = self.rx_meas_frame
        self.save_frame(idx)
        self.emit_frame(idx)
        self.frame_cnt += 1
        self.flag_new_meas.set_edge_up()
        self.init_rx_frame()

    # def frame_save_and_prepare_for_next_rx(self):


        # self.rx_meas_frame= EITFrame(self.dev_setup)  # clear frame


    # def latch_rx_frame_to_meas(self, idx_meas_frame: int = 0):

    #     self.meas_frame[idx_meas_frame] = self.rx_meas_frame

        # if self.autosave.is_set():
        #     self.meas_frame[idx_meas_frame].frame_path = os.path.join(
        #         self.output_dir, f"Frame{self.frame_cnt:02}.pkl"
        #     )
        # if self.frame_cnt == 0:
        #     self.set_frame_TD_ref(0)

    def set_frame_TD_ref(self, idx: int = 0, path: str = None):
        """Latch Frame[indx] as reference for time difference mode"""
        if path is None:
            self._ref_frame_idx = idx
        else:
            meas_frame = self.load_frame(path)
            self._ref_frame_idx = 0
            self.meas_frame.insert(0,meas_frame)
            self.meas_frame[0].frame_path = path
            self.meas_frame[0].make_info_text()

    ## =========================================================================
    ##  New_Frame Signal
    ## =========================================================================
    
    def set_index_of_data_for_computation(self, index:list[list[int]]):
        self.index_extract= index
    
    def emit_frame(self, idx:int=0)->None:

        self.index_extract[0][0]= idx # By measuring only the first index can be send
        self.index_extract[1][0]= idx

        ref_idx= self.index_extract[0][0]
        ref_freq= self.index_extract[0][1]
        meas_idx= self.index_extract[1][0]
        meas_freq= self.index_extract[1][1]

        if ref_freq == meas_freq: # is  TD or absolute#
            f_ref= self._ref_frame 
        elif ref_idx==meas_idx:
            f_ref= self.meas_frame[ref_idx]
        else:
            raise ValueError('Wrong index_of_data_for_computation ')
        v_ref = f_ref.get_voltages(ref_freq)
        l_ref= [f_ref.frame_label(), f_ref.freq_label(ref_freq)]

        f_meas = self.meas_frame[meas_idx]
        v_meas = f_meas.get_voltages(meas_freq)
        l_meas= [ f_meas.frame_label(), f_meas.freq_label(meas_freq) ]

        # logger.debug(f'{v_ref=}')
        logger.debug(f'{l_ref=}')
        # logger.debug(f'{v_meas=}')
        logger.debug(f'{l_meas=}')

        kwargs= {
            "data": Data2Compute(v_ref,v_meas, [l_ref, l_meas]), # data fro computation
            "update_data": FrameInfo(f_meas.info_text), # frame info for 
            "frame_path": f_meas.frame_path # for microcamera
        }

        self.new_frame.fire(False, **kwargs)

    def emit_progression(self)->None:

        kwargs= {
            "update_data": FrameProgress(self.get_frame_cnt(), self.get_filling())
        }
        
        self.new_frame.fire(False, **kwargs)


    ## =========================================================================
    ##  Save load
    ## =========================================================================

    @catch_error
    def save_frame(self, idx: int = 0)->None:
        """Save the meas_frame #idx in as pickle

        Args:
            idx (int, optional): index of the frame to save. Defaults to 0.
        """
        if not self.autosave.is_set():
            return
        path = self.meas_frame[idx].frame_path
        logger.debug(f"Frame #{self.meas_frame[idx].idx} saved in: {path}")
        save_as_pickle(path, self.meas_frame[idx])

    def load_frame(self, file_path):
        """Load measurement frame"""
        return load_pickle_app(file_path)

    def load_single_frame(self, file_path, idx:int=0):
        meas_frame = self.load_frame(file_path)
        self.meas_frame[idx] = meas_frame

    def load_meas_dir(self, dir_path: str = None) -> Union[list[str], None]:
        """Load Dataset files"""
        try:
            if not dir_path:
                title = "Select a directory of the measurement dataset you want to load"
                dir_path = get_dir(
                    title=title, initialdir=APP_DIRS.get(AppDirs.meas_set)
                )
            filenames = search_for_file_with_ext(dir_path, ext=FileExt.pkl)
            # print('filepaths', filenames)
        except FileNotFoundError as e:
            logger.warning(f"FileNotFoundError: ({e})")
            show_msgBox(f"{e}", "FileNotFoundError", "Warning")
            return None
        except OpenDialogDirCancelledException as e:
            logger.info(f"Loading cancelled: ({e})")
            return None

        for filename in filenames:
            if "Frame" not in filename:  # remove all other pkl-files
                filenames.remove(filename)

        if not filenames:
            show_msgBox(
                "No frames-files in directory dirpath!", "NO Files FOUND", "Warning"
            )
            return None
        # print('filepaths', filenames)
        for i, filename in enumerate(filenames):  # get all the frame data
            filepath = os.path.join(dir_path, filename)
            dataset_tmp = self.load_frame(filepath)
            if i == 0:
                set_attributes(self, dataset_tmp)
                setattr(self, "output_dir", dir_path)
            else:
                # setattr(self, 'frame_cnt', getattr(dataset_tmp,'frame_cnt'))
                self.meas_frame.append(dataset_tmp.meas_frame[0])
            self.meas_frame[-1].frame_path = filepath
            self.make_info_text_for_frame(-1)
        setattr(self, "frame_cnt", len(self.meas_frame))
        # print(self.__dict__)

        return filenames

    ## =========================================================================
    ##  Setter/getter
    ## =========================================================================

    def get_filling(self):
        return self.rx_meas_frame.filling

    @property
    def _ref_frame(self):
        return self.meas_frame[self._ref_frame_idx]

    def get_voltages_ref_frame(self, idx_freq: int = 0) -> np.ndarray:
        return self.get_voltages(self._ref_frame_idx, idx_freq)

    def get_idx_ref_frame(self) -> int:
        return self.get_idx_frame(self._ref_frame_idx)

    def get_idx_frame(self, idx_frame: int = 0) -> int:
        if self.meas_frame[idx_frame] is None:
            return None
        return self.meas_frame[idx_frame].get_idx()

    def get_voltages(self, idx_frame: int = 0, idx_freq: int = 0) -> np.ndarray:
        """Return the measured voltage for the given frequency index"""
        return self.meas_frame[idx_frame].get_voltages(idx_freq)

    def set_voltages(
        self, U: np.ndarray, idx_frame: int = 0, idx_freq: int = 0
    ) -> None:
        self.meas_frame[idx_frame].set_voltages(U, idx_freq)

    # def get_freqs_list(self):
    #     """"""
    #     # return self.freqs_list

    # def get_freq_val(self, idx_freq: int = 0):
    #     """TODO"""
    #     return self.freqs_list[idx_freq]

    def get_frame_info(self, idx: int = 0):
        return None if self.meas_frame is None else self.meas_frame[idx].info_text

    def get_frame_path(self, idx: int = 0) -> str:
        """Return the path of the measured frame #idx

        Args:
            idx (int, optional): index of the measured frame. Defaults to 0.

        Returns:
            str: path of the measured frame #idx
        """
        return self.meas_frame[idx].frame_path

    def get_frame_cnt(self):
        # self.frame_cnt = len(self.meas_frame)
        return self.frame_cnt

    
    
class EITFrame(object):
    """Class Frame: regroup the voltages values for all frequencies at timestamps
    for all excitation and for one frequency

    Notes
    -----
    e.g. Meas[2] the measured voltages on each channel (VS a commmon GROUND) for the frequency_nb 2
            for the frequency = frequency_val"""

    def __init__(self, index:int , dev_setup: SciospecSetup, output_dir:str, time_stamp=str):

        self.idx = index
        self.dev_setup = dev_setup
        self.time_stamp = time_stamp

        self.make_frame_path(output_dir)

        self.freqs_list = self.dev_setup.make_freqs_list()
        self.freq_steps = self.dev_setup.get_freq_steps()
        # for x excitation x*2 measurement stream are send
        self.meas_frame_nb = (len(self.dev_setup.get_exc_pattern()) * 2)
        self.meas_frame_cnt = 0  # cnt
        self.meas = [EITMeas(dev_setup) for _ in range(self.freq_steps)]

        self.make_info_text()
        logger.debug(f"init Frame:{self.__dict__}")
    
    def make_frame_path(self, output_dir):
        self.frame_path=os.path.join(output_dir, f"Frame{self.idx:02}")

    def make_info_text(self):
        """Create a tex with information about the Frame nb indx"""

        dir, file = os.path.split(self.frame_path)
        _, dataset_name=os.path.split(dir)

        Fmin = eng(self.dev_setup.get_freq_min(), "Hz")
        Fmax = eng(self.dev_setup.get_freq_max(), "Hz")
        Amp = eng(self.dev_setup.get_exc_amp(), "A")

        self.info_text = [
            f"Dataset name:\t{dataset_name}",
            f"Frame filename:\t{file}",
            f"dirname:\t{dir}",
            f"Frame#:\t{self.idx}",
            f"TimeStamps:\t{self.time_stamp}",
            f"Sweepconfig:\tFmin = {Fmin},\r\n\tFmax = {Fmax}",
            f"\tFSteps = {self.freq_steps:.0f},\r\n\tFScale = {self.dev_setup.get_freq_scale()}",
            f"\tAmp = {Amp},\r\n\tFrameRate = {self.dev_setup.get_frame_rate():.3f} fps",
            f"excitation:\t{self.dev_setup.get_exc_pattern()}",
        ]        

    def add_voltages(self, data:RXFrameData):
        self.meas[data.freq_indx].add_voltages(data)
        val= self.freqs_list[data.freq_indx]
        self.meas[data.freq_indx].set_freq(val)

    def is_complete(self):
        """return if teh frame is complete"""
        return self.meas_frame_cnt == self.meas_frame_nb

    def add_data(self, rx_frame):
        """add rx data to this frame"""

        data=self.extract_data(rx_frame)

        # if data.is_first():
        #     # self.idx = frame_cnt
        #     self.meas_frame_cnt += 1
        self.add_voltages(data)

        if self.is_all_freqs_aquired(data):
            self.meas_frame_cnt += 1
    
    def extract_data(self, rx_frame:list):
        """extract the single data out of the rx_frame, convert them if applicable
        return them as a dict"""
        rx_data = rx_frame[OPTION_BYTE_INDX:-1]

        return RXFrameData(
            ch_group= rx_data[0],
            exc_indx= self._find_excitation_indx(rx_data[1:3]),
            freq_indx= convertBytes2Int(rx_data[3:5]),
            time_stamp= convertBytes2Int(rx_data[5:9]),
            voltages= convert_meas_data(rx_data[9:]),
        )

    def _find_excitation_indx(self, excitation:list):
        """Return the index of the given excitation in the excitation_Pattern"""
        indx = 0
        for Exc_i in self.dev_setup.get_exc_pattern():
            if Exc_i == excitation:
                break
            indx += 1
        return indx

    @property
    def filling(self)->int:
        """Pourcentage of the actual filling grade of the frame
        nb_meas_recieved / nb_meas_expected *100

        Returns:
            int: between 1 and 100
        """
        return int(self.meas_frame_cnt / (self.meas_frame_nb + 1) * 100)

    # def is_very_first_data(self, data):
    #     """retrun if data is the very first one for this frame"""
    #     return data["ch_group"] + data["freq_indx"] + data["exc_indx"] == 1

    def is_all_freqs_aquired(self, data:RXFrameData):
        """return if all meas for all freqs were aquired for this frame"""
        return data.freq_indx == self.freq_steps - 1

    def get_voltages(self, idx_freq: int = 0) -> np.ndarray:
        """Return the measured voltage for the given frequency index"""
        try:
            return self.meas[idx_freq].get_voltages()
        except IndexError:
            print(
                f"try to access index {idx_freq} in meas {self.meas},{len(self.meas)}"
            )
            return self.meas[0].get_voltages()

    def get_idx(self) -> int:
        return self.idx

    def set_voltages(self, U: np.ndarray, idx_freq: int = 0) -> None:
        self.meas[idx_freq].set_voltages(U)

    
    def frame_label(self) -> str:
        return f"Frame #{self.get_idx()}"

    # def ref_frame_label(self) -> str:
    #     return f"RefFrame #{self.get_idx_ref_frame()}"
    
    def freq_label(self, idx) -> str:
        return f"Frequency {eng(self.get_freq_val(idx),'Hz')}"

    def get_freq_val(self, idx)->float:
        return self.freqs_list[idx]

class EITMeas(object):
    """Class measurement: regroup the voltage values of all channels of the EIT device
    for all excitation and for one frequency

    Notes
    -----
    e.g. voltage_Z[1][:] the measured voltages on each channel (VS a commmon GROUND) for excitation 1
            for the frequency = frequency_val"""

    def __init__(self, dev_setup: SciospecSetup):
        self.voltage_Z = np.zeros(
            (len(dev_setup.get_exc_pattern()), dev_setup.get_channel()), dtype=complex
        )
        self.frequency = None  # corresponding excitation frequency

    def set_freq(self, freq_val):
        """set the frequency value for the actual measurements"""
        self.frequency = freq_val

    def add_voltages(self, data:RXFrameData):
        """add rx voltage to the voltages matrix"""
        n_ch_meas_per_frame = 16
        ch_group = data.ch_group
        exc_indx = data.exc_indx
        volt = data.voltages
        n_ch_meas_per_frame = 16
        if volt.shape[0] != n_ch_meas_per_frame:
            raise Exception(
                f"n_ch_meas_per_frame :{n_ch_meas_per_frame} is not correct {volt.shape[0]} voltages recieved"
            )
        start_idx = (ch_group - 1) * n_ch_meas_per_frame
        end_idx = (ch_group) * n_ch_meas_per_frame
        self.voltage_Z[exc_indx, start_idx:end_idx] = volt

    def get_voltages(self) -> np.ndarray:
        """Return the measured voltage"""
        return self.voltage_Z  # np.array(self.voltage_Z)

    def set_voltages(self, U: np.ndarray) -> None:
        self.voltage_Z[0:16, 0:16] = U
        print(f"{self.voltage_Z}")


def convert_meas_data(meas_data):
    """return float voltages values () corresponding to meas data (bytes single float)"""
    n_bytes_real_imag = 4  # we got 4Bytes per value
    meas_data = np.reshape(
        np.array(meas_data), (-1, n_bytes_real_imag)
    )  # reshape the meas data in lock of 4 bytes
    meas_data = meas_data.tolist()  # back to list for conversion
    meas_f = [
        convert4Bytes2Float(m) for m in meas_data
    ]  # conversion of each 4 bytes
    meas_r_i = np.reshape(
        np.array(meas_f), (-1, 2)
    )  # get a matrix with real and imag values in each column
    return meas_r_i[:, 0] + 1j * meas_r_i[:, 1]




if __name__ == "__main__":
    from eit_app.io.sciospec.meas_dataset import EitMeasurementSet
    from PyQt5.QtWidgets import QApplication
    import glob_utils.log.log
    glob_utils.log.log.main_log()

    app = QApplication(argv)
    # # rec2ui_queue = NewQueue()
    # app.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    # # ui = UiBackEnd(queue_in=rec2ui_queue, queue_out=ui2rec_queue, image_reconst=rec)
    # ui = UiBackEnd()
    # ui.show()
    # p = Process(target=_poll_process4reconstruction, args=(ui2rec_queue,rec2ui_queue,rec))
    # p.daemon=True
    # p.start()
    


    print(os.path.split('E:/Software_dev/Python/eit_app/measurements/reffish_0.1uA_1k_d100_20220301_152132'))
    
    d = EitMeasurementSet(1)
    d.initForAquisition(SciospecSetup(32))
    d.save_frame()

    # d.load_meas_dir()
    # exit(app.exec_())
