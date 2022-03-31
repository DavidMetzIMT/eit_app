import os
from dataclasses import dataclass
from logging import getLogger
from sys import argv
from typing import Union

import numpy as np
from default.set_default_dir import APP_DIRS, AppStdDir
from eit_app.sciospec.constants import OPTION_BYTE_INDX
from eit_app.sciospec.setup import SciospecSetup
from eit_app.sciospec.utils import convert4Bytes2Float, convertBytes2Int
from eit_app.com_channels import (
    AddToCaptureSignal,
    AddToComputationSignal,
    AddToDeviceSignal,
    AddToGuiSignal,
    AddToReplaySignal,
    Data2Compute,
    DataAddRxMeasStream,
    DataCheckBurst,
    DataEmitFrame4Computation,
    DataInit4Start,
    DataLoadLastDataset,
    DataLoadSetup,
    DataReInit4Pause,
    DataReplayStart,
    DataSaveLoadImage,
    SignalReciever,
)
from eit_app.update_gui import (
    EvtDataAutosaveOptionsChanged,
    EvtDataMeasDatasetLoaded,
    EvtDataNewFrameInfo,
    EvtDataNewFrameProgress,
)
from eit_model.imaging import IMAGING_TYPE
from glob_utils.decorator.decorator import catch_error
from glob_utils.files.files import FileExt, search_for_file_with_ext
from glob_utils.files.json import read_json, save_to_json
from glob_utils.flags.flag import CustomFlag
from glob_utils.msgbox import warningMsgBox
from glob_utils.pth.path_utils import (
    append_date_time,
    get_datetime_s,
    get_dir,
    mk_new_dir,
)
from glob_utils.types.dict import dict_nested, visualise
from glob_utils.unit.unit import eng

logger = getLogger(__name__)

N_CH_PER_STREAM = 16
## =============================================================================
##  Class for the DataSet obtained from the EIT Device
## =============================================================================


@dataclass
class ExtractIndexes:
    """This Class is used to transform the frame and frequencies indexes

    ref_idx: int > ref frame index for TD
    ref_freq: int > ref freq index for FD
    meas_idx: int > actual frame index (for TD and absolute)
    meas_freq: int > frequency index fro TD or freq 1 for FD
    imaging: str


    for TD abd absolute
        ref_idx= None   >> the ref frame of the measuremnet setup will be used
        ref_freq= meas_freq
        meas_idx
        meas_freq
    
    for FD
        ref_idx= meas_idx   >> the same frame is used but a different frequency
        ref_freq
        meas_idx
        meas_freq

    """
    ref_idx: int
    ref_freq: int
    meas_idx: int
    meas_freq: int
    imaging: str

    def __post_init__(self):
        if self.imaging not in IMAGING_TYPE:
            logger.error(
                f"Wrong imaging {self.imaging}, expected {IMAGING_TYPE.keys()}"
            )
        if any(s in self.imaging for s in ["Time", "Absolute"]):
            self.set_TD_mode()
        elif "Frequence" in self.imaging:
            self.set_FD_mode()
    
    def set_ref_idx(self, idx: int):
        if self.ref_idx is not None:
            self.ref_idx = idx

    def set_meas_idx(self, idx: int):
        if idx is not None:
            self.meas_idx = idx

    def set_TD_mode(self):
        self.ref_idx = None
        self.ref_freq = self.meas_freq

    def set_FD_mode(self):
        self.ref_idx = self.meas_idx


class RXMeasStreamData:
    """This Class is used for the extraction of single informations contained
    in a rx measurement frame

    see documentation of Sciospec EIT device
    """
    ch_group: int
    exc_indx: int
    freq_indx: int
    time_stamp: int
    voltage: np.ndarray

    def __init__(self, rx_meas_stream: list[bytes], excitation: list[list[int]]):
        """See in Sciospec documentation"""
        rx_data = rx_meas_stream[OPTION_BYTE_INDX:-1]
        self.ch_group = rx_data[0]
        self.exc_indx = self._find_excitation_indx(rx_data[1:3], excitation)
        self.freq_indx = convertBytes2Int(rx_data[3:5])
        self.time_stamp = convertBytes2Int(rx_data[5:9])
        self.voltage = convert_meas_data(rx_data[9:])
        logger.debug(
            f"RX MEAS data: {self.ch_group=}, {self.exc_indx=}, {self.freq_indx=}, {self.time_stamp=}, {self.voltage=} - TREATED"
        )

    # def is_first(self):
    #     return self.ch_group + self.freq_indx + self.exc_indx == 1

    def _find_excitation_indx(self, exc: list[int], excitation: list[list[int]]):
        """Return the index of the given excitation in the excitation_Pattern"""
        try:
            idx = excitation.index(exc)
        except ValueError as e:
            logger.error(f"RX excitation: {exc} is not in {excitation=}\r{e}")
            idx = 0
        return idx


## =============================================================================
##  EITMeasurements
## =============================================================================


class VoltageMeas(object):
    """Regroup the channel voltages acuired by a EIT device for all excitation
    for one frequency

    Notes
    -----
    e.g. voltage[1][:] the measured voltages on each channel (VS a commmon GROUND) for excitation 1
            for the frequency = frequency_val"""

    voltage: np.ndarray = None  # complex ndarray in V with shape(n_exc, n_channel)
    frequency: float = None  # frequency value in Hz

    def __init__(self, dev_setup: SciospecSetup = None, **kwargs):
        self.frequency = None
        self.voltage = np.array([], dtype=complex)
        if dev_setup is not None:
            n_exc = len(dev_setup.get_exc_pattern())
            n_channel = dev_setup.get_channel()
            self.voltage = np.zeros((n_exc, n_channel), dtype=complex)
        # logger.debug(f"{self.voltage=}")
        self.set_from_dict(**kwargs)

    def set_freq(self, freq_val: float) -> None:
        """set the frequency value for the actual measurements
        """
        self.frequency = freq_val

    def add_rx_stream_data(self, stream: RXMeasStreamData) -> None:
        """Add rx stream data to the in the voltage array
        at the correct position
        """
        # test if voltage shape is correct!
        if stream.voltage.shape[0] != N_CH_PER_STREAM:
            raise Exception(
                f"Wrong shape of voltage: {stream.voltage.shape[0]} expected {N_CH_PER_STREAM=}"
            )
        start_idx = (stream.ch_group - 1) * N_CH_PER_STREAM
        end_idx = (stream.ch_group) * N_CH_PER_STREAM
        self.voltage[stream.exc_indx, start_idx:end_idx] = stream.voltage

    def get_voltage(self) -> np.ndarray:
        """Return the measured voltage
        """
        # logger.debug('VOLTAGES', self.voltage)
        return self.voltage

    def set_voltages(self, U: np.ndarray) -> None:
        self.voltage[0:16, 0:16] = U
        print(f"{self.voltage}")

    @property
    def __dict__(self):
        """Redefinition for saving of the complex values as json
        """
        return {
            "voltage": {
                "array_real": np.real(self.voltage),
                "array_imag": np.imag(self.voltage),
            },
            "frequency": self.frequency,
        }

    def set_from_dict(self, **kwargs):
        """Set attributes by passing kwargs or a dict

        kwargs should be equivalent to self.__dict__
        """
        # special setting of voltages >> back to ndarray dtype= complex
        volt = kwargs.pop("voltage", {})
        if all(key in volt for key in ["array_real", "array_imag"]):
            self.voltage = np.array(volt["array_real"]) + 1j * np.array(
                volt["array_imag"]
            )

        # set all others passed attr
        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)


## =============================================================================
##  Class for the DataSet obtained from the EIT Device
## =============================================================================


class MeasurementFrame(object):
    """Class Frame: regroup the voltages values for all frequencies at timestamps
    for all excitation and for one frequency

    Notes
    -----
    e.g. Meas[2] the measured voltages on each channel (VS a commmon GROUND) for the frequency_nb 2
            for the frequency = frequency_val
    """
    
    idx: int
    dataset_name: str
    time_stamp: str
    info: str
    path: str
    meas: list[VoltageMeas]
    freq_list: np.ndarray
    freq_steps: int
    excitation: list[list[int]]
    _meas_stream_max: int
    _meas_stream_cnt: int
    _dev_setup: SciospecSetup

    def __init__(
        self,
        index: int,
        dataset_name: str,
        dev_setup: SciospecSetup,
        output_dir: str,
        time_stamp: str,
        **kwargs,
    ):

        self.idx = index
        self.dataset_name = dataset_name
        self.time_stamp = time_stamp
        self.path = self.build_path(output_dir, index)
        self._dev_setup = dev_setup
        self.freq_list = dev_setup.get_freqs_list()
        self.freq_steps = dev_setup.get_freq_steps()
        self.excitation = dev_setup.get_exc_pattern()
        # for x excitation x*2 measurement stream are send
        self.meas = [VoltageMeas(dev_setup, frequency=val) for val in self.freq_list]
        self._meas_stream_max = len(self.excitation) * 2
        self._meas_stream_cnt = 0
        self.info = self.build_info()
        logger.debug(f"Initialisation of Frame:{self.__dict__}")

    def set_from_dict(self, **kwargs):
        """Set attributes by passing kwargs or a dict.
        Kwargs should be equivalent to self.__dict__.
        """
        # special setting of meas
        meas = kwargs.pop("meas", [])
        if isinstance(meas, list) and len(meas) > 0:
            self.meas = [VoltageMeas(**m) for m in meas]

        # set all others passed attr
        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)

        # rebuild the info in case something has been changed (e.g. path)
        self.info = self.build_info()

    def build_path(self, output_dir: str, idx: int) -> str:
        """Return a formatted frame path"""
        return os.path.join(output_dir, f"Frame{idx:02}")

    def build_info(self):
        """Create an information text about the frame."""
        dir, file = os.path.split(self.path)
        Fmin = eng(self._dev_setup.get_freq_min(), "Hz")
        Fmax = eng(self._dev_setup.get_freq_max(), "Hz")
        Amp = eng(self._dev_setup.get_exc_amp(), "A")
        return [
            f"Dataset name:\t{self.dataset_name}",
            f"Frame filename:\t{file}",
            f"dirname:\t{dir}",
            f"Frame#:\t{self.idx}",
            f"TimeStamps:\t{self.time_stamp}",
            f"Sweepconfig:\tFmin = {Fmin},\r\n\tFmax = {Fmax}",
            f"\tFSteps = {self.freq_steps:.0f},\r\n\tFScale = {self._dev_setup.get_freq_scale()}",
            f"\tFList: {self.freq_list}",
            f"\tAmp = {Amp},\r\n\tFrameRate = {self._dev_setup.get_frame_rate():.3f} fps",
            f"Excitation:\t{self.excitation}",
        ]

    def is_complete(self) -> bool:
        """Assess if so the frame is complete.
        The number of added meas stream is compared to the expected number."""
        return self._meas_stream_cnt == self._meas_stream_max

    def add_data(self, rx_meas_stream: list[bytes] = None, **kwargs):
        """add rx data to this frame"""
        if rx_meas_stream is None:
            return
        stream = RXMeasStreamData(rx_meas_stream, self.excitation)
        self.add_rx_stream(stream)

        if self.is_last_freq(stream):
            # this is done two time only at the end of a complete
            # measurements streaming which look like:
            #   expected _meas_stream_nb = m_exc * 2 #TODO?? m_exc* n_freq *2
            #   meas stream : exc 1, freq 1, group 1
            #   meas stream : exc 1, freq 1, group 2
            #             ...
            #   meas stream : exc m, freq 1, group 1
            #   meas stream : exc m, freq 1, group 2
            #   meas stream : exc 1, freq 2, group 1
            #   meas stream : exc 1, freq 2, group 2
            #             ...
            #   meas stream : exc m, freq 2, group 1
            #   meas stream : exc m, freq 2, group 2
            #             ...
            #   meas stream : exc m, freq n, group 1 >> _meas_stream_cnt += 1
            #   meas stream : exc m, freq n, group 2 >> _meas_stream_cnt += 1
            self._meas_stream_cnt += 1

    def add_rx_stream(self, stream: RXMeasStreamData):
        """Send stream to be added in corresponding EITmeas item"""
        self.meas[stream.freq_indx].add_rx_stream_data(stream)
        # val= self.freq_list[data.freq_indx]
        # self.meas[data.freq_indx].set_freq(val)

    @property
    def filling(self) -> int:
        """Pourcentage of the actual filling grade of the frame
        nb_meas_recieved / nb_meas_expected *100

        Returns:
            int: between 0 and 99
        """
        return int(self._meas_stream_cnt / self._meas_stream_max * 100)

    def is_last_freq(self, stream: RXMeasStreamData) -> bool:
        """Assess if the stream contain data of the last frequency"""
        return stream.freq_indx == self.freq_steps - 1

    def get_voltages(self, idx_freq: int = 0) -> np.ndarray:
        """Return the measured voltage for the given frequency index"""
        return self.meas[idx_freq].get_voltage()

    def get_idx(self) -> int:
        return self.idx

    def set_voltages(self, U: np.ndarray, idx_freq: int = 0) -> None:
        self.meas[idx_freq].set_voltages(U)

    def frame_label(self) -> str:
        return f"Frame #{self.get_idx()}"

    def freq_label(self, idx: int) -> str:
        return f"Frequency {eng(self.get_freq_val(idx),'Hz')}"

    def get_freq_val(self, idx: int) -> float:
        return self.freq_list[idx]

    ## =========================================================================
    ##  Save load
    ## =========================================================================

    @catch_error
    def save(self, path: str = None) -> None:
        """Save the meas_frame #idx as

        Args:
            idx (int, optional): index of the frame to save. Defaults to 0.
        """

        path = self.path if path is None else path
        d = dict_nested(self, ignore_private=True)
        save_to_json(path, d)
        logger.debug(f"Frame #{self.idx} saved in: {self.path}")
        visualise(d)

    def load(self, path: str) -> bool:
        """Load measurement frame
        """
        frame_as_dict = read_json(path)
        if frame_as_dict is None:
            return False

        # correct the frame path (if dataset moved...)
        frame_as_dict["path"] = path
        self.set_from_dict(**frame_as_dict)
        logger.debug(f"Frame #{self.idx} loaded : {self.path}")
        visualise(frame_as_dict)
        return True


## =============================================================================
##  Class for the DataSet obtained from the EIT Device
## =============================================================================

class MeasurementDataset(
    SignalReciever,
    AddToGuiSignal,
    AddToDeviceSignal,
    AddToComputationSignal,
    AddToCaptureSignal,
    AddToReplaySignal,
):
    """Class EITMeasSet: regroups infos and manage the frames of measurements
    """

    time_stamps: str
    name: str
    output_dir: str
    dev_setup: SciospecSetup
    frame_cnt: int
    meas_frame: list[MeasurementFrame] # meas. frame list used during acquisition and loading
    _rx_meas_frame: MeasurementFrame # meas. frame used during acquisition
    _ref_frame: MeasurementFrame # meas. frame used tio save acztual TD ref frame
    _autosave: CustomFlag
    _save_img: CustomFlag
    _load_after_meas: CustomFlag
    def __init__(self):
        super().__init__()

        self.init_reciever(
            data_callbacks={
                DataInit4Start: self.init_4_start,
                DataReInit4Pause: self.reinit_4_pause,
                DataAddRxMeasStream: self.add_data,
                DataEmitFrame4Computation: self.emit_frame_4_computatiom,
                DataLoadLastDataset: self.load_last_dataset
            }
        )

        self.time_stamps = ""
        self.name = ""
        self.output_dir = ""
        self.dev_setup = None
        self.frame_cnt = 0
        self._rx_meas_frame = None
        self.meas_frame = []
        self._ref_frame = None

        self._autosave = CustomFlag()
        self._autosave.set()
        self._save_img = CustomFlag()
        self._save_img.set()
        self._load_after_meas = CustomFlag()
        self._load_after_meas.set()
        self._update_gui_autosave()

    ## =========================================================================
    ##  Aquisition
    ## =========================================================================

    def init_4_start(self, data: DataInit4Start) -> None:
        """Initialization of the dataset for acquisition (called by a signal)
        - set output dir
        """
        self.dev_setup = data.dev_setup
        self.time_stamps = get_datetime_s()
        folder = append_date_time(self.name, self.time_stamps)
        self.output_dir = None
        if self._autosave.is_set():
            self.output_dir = mk_new_dir(folder, APP_DIRS.get(AppStdDir.meas_set))
            self.dev_setup.save(self.output_dir)

        self.frame_cnt = 0
        self.meas_frame = [None]
        self._rx_meas_frame = self.get_new_frame_for_acquisition()

    def reinit_4_pause(self, data: DataReInit4Pause):
        """Reinitialization of the dataset after meas. paused
        (called by a signal)
        - the rx_meas_frame is reset
        """
        self._rx_meas_frame = self.get_new_frame_for_acquisition()

    def add_data(self, data: DataAddRxMeasStream):
        """Add the data recieved from device (called by a signal)
        """
        self.add_to_dataset(data.rx_meas_stream)

    def emit_frame_4_computatiom(self, data: DataEmitFrame4Computation):
        """Send frame to computation (called by a signal)
        """
        self.emit_meas_frame(data.idx)
    
    def load_last_dataset(self,  data:DataLoadLastDataset):
        
        if self._load_after_meas.is_set():
            self.load_auto(self.output_dir)


    def set_name(self, name: str = None, *args, **kwargs) -> None:
        """set new name of the dataset (Called by the gui)

        Args:
            name (str, optional): name of the dataset. Defaults to None.
        """
        if name is None:
            return
        logger.debug(f"Set meas dataset:{name}")
        self.name = name

    @catch_error
    def add_to_dataset(self, rx_meas_stream: list[bytes] = None, **kwargs):
        """Add the rx_meas_stream in the _rx_meas_frame
        - send the data to _rx_meas_frame and emit acquisition progession

        if _rx_meas_frame is complete
        the actula frame is saved and send to computation
        """
        self._rx_meas_frame.add_data(rx_meas_stream)
        self.emit_progression()

        if not self._rx_meas_frame.is_complete():
            return

        logger.info(f"Frame #{self.frame_cnt} - complete")
        idx = 0
        self.meas_frame[idx] = self._rx_meas_frame
        if self.frame_cnt == 0:
            self._ref_frame = self._rx_meas_frame
        self._save_meas_frame(idx)
        self.emit_meas_frame(idx)
        self.frame_cnt += 1
        self._rx_meas_frame = self.get_new_frame_for_acquisition()

    def get_new_frame_for_acquisition(self) -> MeasurementFrame:
        """Return a new measurement frame out of the actual set after
        init_4_start
        - index=self.frame_cnt,
        - dataset_name=self.name,
        - dev_setup=self.dev_setup,
        - output_dir=self.output_dir,
        - time_stamp=self.time_stamps,
        """
        return MeasurementFrame(
            index=self.frame_cnt,
            dataset_name=self.name,
            dev_setup=self.dev_setup,
            output_dir=self.output_dir,
            time_stamp=self.time_stamps,
        )

    def set_ref_frame(self, idx: int = 0, path: str = None):
        """Latch meas_frame[idx] as reference for time difference mode
        """
        if path is None:
            if len(self.meas_frame) > idx:
                self._ref_frame = self.meas_frame[idx]
            path = self.meas_frame[0].build_path(self.output_dir, idx)
            self._ref_frame = self._load_frame(path)
        else:
            meas_frame, success = self._load_frame(path)
            self._ref_frame = meas_frame
            self._ref_frame.path = path
            self._ref_frame.build_info()

    ## =========================================================================
    ##  New_Frame Signal
    ## =========================================================================

    def set_index_of_data_for_computation(self, extract_idx: ExtractIndexes):
        self.extract_idx = extract_idx

    def emit_meas_frame(self, idx: int = None) -> None:
        """Send signals with corresponding frame data for
        computation plotting and update
        used:
        - after a fram is acquired
        - or for computation from a loaded dataset
        """
        if idx is None:
            return
        self.extract_idx.set_ref_idx(idx)
        self.extract_idx.set_meas_idx(idx)

        ref_idx = self.extract_idx.ref_idx
        ref_freq = self.extract_idx.ref_freq
        meas_idx = self.extract_idx.meas_idx
        meas_freq = self.extract_idx.meas_freq

        if ref_idx is None:
            v_ref = self.get_ref_voltage(ref_freq)
            l_ref = self.get_ref_labels(ref_freq)
        else:
            v_ref = self.get_meas_voltage(ref_idx, ref_freq)
            l_ref = self.get_meas_labels(ref_idx, ref_freq)

        v_meas = self.get_meas_voltage(meas_idx, meas_freq)
        l_meas = self.get_meas_labels(meas_idx, meas_freq)

        logger.debug(f"Emit Frame for computation {l_meas=} {l_ref=}")

        self.to_gui.emit(EvtDataNewFrameInfo(self.get_meas_info(meas_idx)))
        self.to_device.emit(DataCheckBurst(self.get_frame_cnt()))
        self.to_computation.emit(Data2Compute(v_ref, v_meas, [l_ref, l_meas]))
        self.to_capture.emit(DataSaveLoadImage(self.get_meas_path(meas_idx)))

    def emit_progression(self) -> None:
        """Send signal to update Frame aquisition progress bar"""
        logger.debug(
            f"Emit progression frame# {self.get_frame_cnt()} fill:{self.get_filling()} "
        )
        self.to_gui.emit(
            EvtDataNewFrameProgress(self.get_frame_cnt(), self.get_filling())
        )

    ## =========================================================================
    ##  Save load
    ## =========================================================================

    @catch_error
    def _save_meas_frame(self, idx: int = 0, path: str = None) -> None:
        """Save the meas_frame #idx as

        Args:
            idx (int, optional): index of the frame to save. Defaults to 0.
        """
        if not self._autosave.is_set():
            return
        self.meas_frame[idx].save(path)

    def _load_frame(self, path: str) -> Union[MeasurementFrame, bool]:
        """Load measurement frame

        Args:
            path (str): loading path

        Returns:
            Union[MeasurementFrame, bool]: Loade frame and success
        """

        frame = self.get_new_frame_for_acquisition()
        success = frame.load(path)
        return frame, success

    def load(self, *args, **kwargs) -> None:
        """Load a measurement dataset (called from gui)
        - the user will be aske to selected a dir via a dialog
        """
        self.load_auto()

    def load_auto(self, dir_path: str = None) -> None:
        """Load measurement files contained in measurement dataset directory
        """
        if not self._load_json(dir_path):
            return
        # Update GUI
        self.to_gui.emit(EvtDataMeasDatasetLoaded(self.output_dir, self.frame_cnt))
        # load setup in device
        self.to_device.emit(DataLoadSetup(self.output_dir))
        # Start replay of the measurements
        self.to_replay.emit(DataReplayStart(self.frame_cnt))

    @catch_error
    def _load_json(self, dir_path: str = None) -> bool:
        """Load a measurement files contained in measurement dataset directory
        , only JSON-files
        
        Args:
            dir_path (str, optional): . Defaults to None. If None the user will
            be asked to select a dir via a dialog

        Returns:
            bool: sucess of loading
        """

        if (dir_path := self._get_meas_dir(dir_path)) is None:
            return False

        if (filenames := self._get_all_frame_file(dir_path, ext=FileExt.json)) is None:
            return False

        # load the setup present in the directory
        self.dev_setup = SciospecSetup(32)
        if self.dev_setup.load(dir_path) is None:
            return False

        # During loading of the frame the dev_setup is used to build first init
        # values for frame which are overwritten during loading process with
        # new data if contained in loaded json-file
        self.meas_frame = []
        for file in filenames:
            filepath = os.path.join(dir_path, file)
            frame, success = self._load_frame(filepath)
            if success:
                self.meas_frame.append(frame)

        self.time_stamps = self.meas_frame[0].time_stamp
        self.name = self.meas_frame[0].dataset_name
        self.output_dir = dir_path
        self.frame_cnt = len(self.meas_frame)

        self._rx_meas_frame = None  # not used with loaded dataset
        self._ref_frame = self.meas_frame[0]  # reset for loaded dataset

        return True

    def _get_meas_dir(self, dir_path: str) -> Union[str, None]:

        if not dir_path:
            title = "Select a measurement dataset directory"
            initialdir = APP_DIRS.get(AppStdDir.meas_set)
            dir_path = get_dir(title=title, initialdir=initialdir)
        return dir_path

    def _get_all_frame_file(
        self, dir_path: str, ext=FileExt.pkl
    ) -> Union[list[str], None]:
        """Return"""
        try:
            filenames = search_for_file_with_ext(dir_path, ext=ext)
        except FileNotFoundError as e:
            logger.warning(f"FileNotFoundError: ({e})")
            warningMsgBox(
                "FileNotFoundError",
                f"{e}",
            )
            return None

        for filename in filenames:
            if "Frame" not in filename:  # remove all other files
                filenames.remove(filename)

        if not filenames:
            warningMsgBox(
                "Files Not Found", f"No Frames-files in directory: {dir_path}!"
            )
            return None

        return filenames

    ## =========================================================================
    ##  Setter/getter
    ## =========================================================================

    def get_filling(self) -> int:
        """Return the Filling pourcentage of the _rx_meas_frame"""
        return self._rx_meas_frame.filling

    def get_meas_voltage(self, idx_frame: int = 0, idx_freq: int = 0) -> np.ndarray:
        """Return the measured voltage for the given frequency index
        """
        return self.meas_frame[idx_frame].get_voltages(idx_freq)

    def get_meas_labels(self, idx_frame: int = 0, idx_freq: int = 0) -> np.ndarray:
        """Return the measured voltage for the given frequency index"""
        return [
            self.meas_frame[idx_frame].frame_label(),
            self.meas_frame[idx_frame].freq_label(idx_freq),
        ]

    def get_ref_labels(self, idx_freq: int = 0) -> np.ndarray:
        """Return the measured voltage for the given frequency index"""
        return [self._ref_frame.frame_label(), self._ref_frame.freq_label(idx_freq)]

    def get_ref_voltage(self, idx_freq: int = 0) -> np.ndarray:
        """Return the TD ref measured voltage for the given frequency index"""
        return self._ref_frame.get_voltages(idx_freq)

    def get_meas_idx(self, idx_frame: int = 0) -> int:
        """Return the index of the meas frame, during acquisition idx_frame 
        is only 0 and the idx is contained in the frame itself
        """
        if self.meas_frame[idx_frame] is None:
            return None
        return self.meas_frame[idx_frame].get_idx()

    def get_ref_idx(self) -> int:
        """Return the index of the ref frame"""
        return self._ref_frame.get_idx()

    def set_voltages(
        self, U: np.ndarray, idx_frame: int = 0, idx_freq: int = 0
    ) -> None:
        self.meas_frame[idx_frame].set_voltages(U, idx_freq)

    def get_meas_path(self, idx: int = 0) -> str:
        """Return the path of the measured frame #idx

        Args:
            idx (int, optional): index of the measured frame. Defaults to 0.

        Returns:
            str: path of the measured frame #idx
        """
        return self.meas_frame[idx].path  #

    def get_meas_info(self, idx: int = 0) -> str:
        """Return the path of the measured frame #idx

        Args:
            idx (int, optional): index of the measured frame. Defaults to 0.

        Returns:
            str: path of the measured frame #idx
        """
        return self.meas_frame[idx].info

    def get_frame_cnt(self)->int:
        return self.frame_cnt

    def _update_gui_autosave(self):
        self.to_gui.emit(
            EvtDataAutosaveOptionsChanged(
                self._autosave.is_set(),
                self._save_img.is_set(),
                self._load_after_meas.is_set()
            )
        )

    def set_autosave(self, val:bool= None, *kwargs):
        if val is None:
            return
        self._autosave.set(val)
        if not self._autosave.is_set():
            self._save_img.set(False)
            self._load_after_meas.set(False)
        self._update_gui_autosave()

    def set_save_img(self, val:bool= None, *kwargs):
        if val is None:
            return
        self._save_img.set(val)
        self._update_gui_autosave()
    
    def set_load_after_meas(self, val:bool= None, *kwargs):
        if val is None:
            return
        self._load_after_meas.set(val)
        self._update_gui_autosave()


def convert_meas_data(meas_data):
    """return float voltages values () corresponding to meas data 
    (bytes single float)
    """
    n_bytes_real_imag = 4  # we got 4Bytes per value
    # reshape the meas data in block of 4 bytes
    meas_data = np.reshape( np.array(meas_data), (-1, n_bytes_real_imag))  
    meas_data = meas_data.tolist()  # back to list for conversion
    meas_f = [convert4Bytes2Float(m) for m in meas_data]  # conversion of each 4 bytes
    # get a matrix with real and imag values in each column
    meas_r_i = np.reshape(np.array(meas_f), (-1, 2))  
    return meas_r_i[:, 0] + 1j * meas_r_i[:, 1]


if __name__ == "__main__":
    import glob_utils.log.log
    from eit_app.sciospec.measurement import MeasurementDataset
    from PyQt5.QtWidgets import QApplication

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

    print(
        os.path.split(
            "E:/Software_dev/Python/eit_app/measurements/reffish_0.1uA_1k_d100_20220301_152132"
        )
    )

    d = MeasurementDataset(1)
    # d.initForAquisition(SciospecSetup(32))
    d._save_meas_frame()

    # d.load_meas_dir()
    # exit(app.exec_())
