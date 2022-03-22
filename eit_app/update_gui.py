from abc import ABC
from dataclasses import dataclass, is_dataclass
from distutils.log import debug
from enum import Enum, auto
from logging import getLogger
from os import supports_dir_fd
import threading
from typing import Any, Callable, List
from PyQt5 import QtGui

from eit_app.gui import Ui_MainWindow
from eit_app.gui_utils import (
    change_value_withblockSignal,
    set_comboBox_items,
    set_QSlider_position,
    set_QSlider_scale,
    set_QTableWidget,
)
from eit_app.io.sciospec.setup import SciospecSetup
from eit_model.imaging_type import (
    Imaging,
    AbsoluteImaging,
    TimeDifferenceImaging,
    FrequenceDifferenceImaging,
)
from glob_utils.flags.flag import CustomFlag, MultiState
from glob_utils.decorator.decorator import catch_error
from glob_utils.thread_process.signal import Signal

logger = getLogger(__name__)

def is_dataclass_instance(obj):
    return is_dataclass(obj) and not isinstance(obj, type)

################################################################################
# Event Dataclass use to trigger an update
################################################################################

class EventDataClass(ABC):
    """Abstract class of the dataclass defined for each update events"""

################################################################################
# Event Agent
################################################################################

class EventsAgent:
    """This agent apply update on the GUI (app) depending on the data posted """

    def __init__(self, app, events) -> None:
        self.subscribers = {}
        self.app = app
        self.events = events

    def _mk_dict(self, data:EventDataClass):
        """ Transform the event data in dictionarie and add the "app" key """
        d = data.__dict__
        d["app"] = self.app
        return d

    @catch_error
    def post_event_data(self, data:EventDataClass):
        """Run the update event correspoding to the event data"""

        if not is_dataclass_instance(data) or not isinstance(data, EventDataClass):
            logger.error("data are not compatible for update")
            return

        logger.info(f"thread update_event {threading.get_ident()}")
        data = self._mk_dict(data)
        func = data.pop("func")
        logger.debug(f"updating {func=} with {data=}")
        self.events[func](**data)


class ObjWithSignalToGui(object):
    
    def __init__(self):
        super().__init__()
        self.to_gui=Signal(self)

    def emit_to_gui(self, data:Any)->None:
        kwargs={"update_gui_data": data}
        self.to_gui.fire(None, **kwargs)


################################################################################
# Update events Catalog
################################################################################

# cataolog of update functions event
UPDATE_EVENTS: dict[str, Callable] = {} 


def add_func_to_catalog(func:Callable):
    """Add the function to the catalog"""
    name = func.__name__
    UPDATE_EVENTS[func.__name__] = func


################################################################################
# Update Definition and assiociated dataclasses
################################################################################


# -------------------------------------------------------------------------------
## Update available EIT devices
# -------------------------------------------------------------------------------


def update_available_devices(app: Ui_MainWindow, device: dict):
    """Refesh the list of devices in the comboBox"""
    items = list(device) or ["None device"]
    set_comboBox_items(app.cB_ports, items)


add_func_to_catalog(update_available_devices)

@dataclass
class DevAvailables(EventDataClass):
    device: dict
    func: str = update_available_devices.__name__

# -------------------------------------------------------------------------------
## Update available capture devices
# -------------------------------------------------------------------------------


def update_available_capture_devices(app: Ui_MainWindow, device: dict):
    """Refesh the list of devices in the comboBox"""
    items = list(device) or ["None device"]
    set_comboBox_items(app.cB_video_devices, items)


add_func_to_catalog(update_available_capture_devices)

@dataclass
class CaptureDevAvailables(EventDataClass):
    device: dict
    func: str = update_available_capture_devices.__name__


# -------------------------------------------------------------------------------
## Update device status
# -------------------------------------------------------------------------------


def update_device_status(app: Ui_MainWindow, connected: bool, connect_prompt: str):
    """Actualize the status of the device"""
    app.lab_device_status.setText(connect_prompt)
    app.lab_device_status.adjustSize
    color = "background-color: green" if connected else "background-color: red"
    app.lab_device_status.setStyleSheet(color)


add_func_to_catalog(update_device_status)


@dataclass
class DevStatus(EventDataClass):
    connected: bool
    connect_prompt: str
    func: str = update_device_status.__name__


# -------------------------------------------------------------------------------
## Update device setup
# -------------------------------------------------------------------------------


def update_device_setup(
    app: Ui_MainWindow,
    setup: SciospecSetup,
    set_freq_max_enable: bool = True,
    error: bool = False,
):
    """Actualize the inputs fields for the setup of the device coresponding to it"""
    app.lE_sn.setText(setup.get_sn())
    ## Update EthernetConfig
    app.chB_dhcp.setChecked(bool(setup.ethernet_config.get_dhcp()))
    app.lE_ip.setText(setup.ethernet_config.get_ip())
    app.lE_mac.setText(setup.ethernet_config.get_mac())

    ## Update OutputConfig Stamps
    app.chB_exc_stamp.setChecked(bool(setup.output_config.get_exc_stamp()))
    app.chB_current_stamp.setChecked(bool(setup.output_config.get_current_stamp()))
    app.chB_time_stamp.setChecked(bool(setup.output_config.get_time_stamp()))

    # Update Measurement Setups
    change_value_withblockSignal(app.sBd_frame_rate.setValue, setup.get_frame_rate())
    change_value_withblockSignal(
        app.sBd_max_frame_rate.setValue, setup.get_max_frame_rate()
    )
    change_value_withblockSignal(app.sB_burst.setValue, setup.get_burst())
    change_value_withblockSignal(
        app.sBd_exc_amp.setValue, setup.get_exc_amp() * 1000
    )  # from A -> mA
    change_value_withblockSignal(app.sBd_freq_min.setValue, setup.get_freq_min())
    change_value_withblockSignal(app.sBd_freq_max.setValue, setup.get_freq_max())
    change_value_withblockSignal(app.sB_freq_steps.setValue, setup.get_freq_steps())
    change_value_withblockSignal(app.cB_scale.setCurrentText, setup.get_freq_scale())

    app.sBd_freq_max.setEnabled(set_freq_max_enable)
    color = "background-color: red" if error else "background-color: white"
    app.label_maxF.setStyleSheet(color)
    app.label_minF.setStyleSheet(color)
    app.label_Steps.setStyleSheet(color)

    set_QTableWidget(app.tw_exc_pattern, setup.get_exc_pattern(), 0)
    update_freqs_list(app, setup.get_freqs_list())


add_func_to_catalog(update_device_setup)


@dataclass
class DevSetup(EventDataClass):
    setup: SciospecSetup
    set_freq_max_enable: bool = True
    error: bool = False
    func: str = update_device_setup.__name__


# -------------------------------------------------------------------------------
## Update Frequency list for the imaging inputs
# -------------------------------------------------------------------------------


def update_freqs_list(app: Ui_MainWindow, freqs: List[Any]):
    set_comboBox_items(app.cB_freq_meas_0, list(freqs))
    set_comboBox_items(app.cB_freq_meas_1, list(freqs))


# -------------------------------------------------------------------------------
## Update live measurements state
# -------------------------------------------------------------------------------

@dataclass
class MeasStatusButtonData:
    lab_txt:str
    lab_style:str
    pB_txt:str
    pB_status_tip:str

class MeasuringStates(Enum):
    IDLE = MeasStatusButtonData(
        lab_txt="Idle",
        lab_style="background-color: red",
        pB_txt="Start",
        pB_status_tip="Start aquisition of a new measurement dataset (Ctrl + Shift +Space)"
    )
    MEASURING = MeasStatusButtonData(
        lab_txt="Measuring",
        lab_style="background-color: green",
        pB_txt="Pause",
        pB_status_tip="Pause aquisition of measurement dataset (Ctrl + Shift +Space)"
    )
    PAUSED = MeasStatusButtonData(
        lab_txt="Paused",
        lab_style="background-color: yellow",
        pB_txt="Resume",
        pB_status_tip="Restart aquisition of measurement dataset (Ctrl + Shift +Space)"
    )

def update_meas_status(app: Ui_MainWindow, meas_status: MeasuringStates):
    """Update the live measurements status label and the mesurements
    start/pause/resume button"""
    v:MeasStatusButtonData= meas_status.value    
    app.lab_live_meas_status.setText(v.lab_txt)
    app.lab_live_meas_status.setStyleSheet(v.lab_style)
    app.pB_start_meas.setText(v.pB_txt)
    app.pB_start_meas.setStatusTip(v.pB_status_tip)


add_func_to_catalog(update_meas_status)


@dataclass
class MeasuringStatus(EventDataClass):
    meas_status: MeasuringStates
    func: str = update_meas_status.__name__


# -------------------------------------------------------------------------------
## Update live measurements state
# -------------------------------------------------------------------------------

@dataclass
class CaptureStatusButtonData:
    lab_txt:str
    lab_style:str
    pB_txt:str 
    pB_status_tip:str =""
    pB_enable:bool = True

class CaptureMode(Enum):
    IDLE = CaptureStatusButtonData(
        lab_txt="Idle",
        lab_style="background-color: red",
        pB_txt="Start capture",
        pB_status_tip=""
    )
    MEASURING = CaptureStatusButtonData(
        lab_txt="Measuring",
        lab_style="background-color: blue",
        pB_txt="Start capture",
        pB_enable = False
    )
    LIVE = CaptureStatusButtonData(
        lab_txt="Live",
        lab_style="background-color: green",
        pB_txt="Stop capture"
    )

def update_capture_status(app: Ui_MainWindow, capture_mode: CaptureMode):
    """Update the live measurements status label and the mesurements
    start/pause/resume button"""
    v:CaptureStatusButtonData= capture_mode.value    
    app.lab_capture_mode.setText(v.lab_txt)
    app.lab_capture_mode.setStyleSheet(v.lab_style)
    app.pB_capture_start_stop.setText(v.pB_txt)
    app.pB_capture_start_stop.setStatusTip(v.pB_status_tip)
    app.pB_capture_start_stop.setEnabled(v.pB_enable)

add_func_to_catalog(update_capture_status)

@dataclass
class CaptureStatus(EventDataClass):
    capture_mode: CaptureMode
    func: str = update_capture_status.__name__


# -------------------------------------------------------------------------------
## Update replay status
# -------------------------------------------------------------------------------


def update_replay_status(app: Ui_MainWindow, status: CustomFlag):
    """Update the status label"""

    if status.is_set():
        app.lab_replay_status.setText("REPLAY ON")
        app.lab_replay_status.setStyleSheet("background-color: green")
    else:
        app.lab_replay_status.setText("REPLAY OFF")
        app.lab_replay_status.setStyleSheet("background-color: grey")
        # set_slider(app.slider_replay, set_pos=0)


add_func_to_catalog(update_replay_status)


@dataclass
class ReplayStatus(EventDataClass):
    status: CustomFlag
    func: str = update_replay_status.__name__

# -------------------------------------------------------------------------------
## Update replay play/pause button
# -------------------------------------------------------------------------------


def update_replay_button(app: Ui_MainWindow, play_active:bool):
    """Update the status label"""

    if play_active:
        icon_path = ":/newPrefix/icons/icon_pause.png"
    else:
        icon_path = ":/newPrefix/icons/icon_play.png"

    icon = QtGui.QIcon()
    icon.addPixmap(QtGui.QPixmap(icon_path), QtGui.QIcon.Normal, QtGui.QIcon.Off)
    app.pB_replay_play.setIcon(icon)

add_func_to_catalog(update_replay_button)


@dataclass
class ReplayButton(EventDataClass):
    play_active: bool
    func: str = update_replay_button.__name__

# -------------------------------------------------------------------------------
## Update imaging inputs fields
# -------------------------------------------------------------------------------


def update_imaging_inputs_fields(app: Ui_MainWindow, imaging: Imaging):
    """Activate deactive the input fileddepending on the imaging type"""

    meas_0 = {"show": False, "lab_text": "Ref. Frequency"}
    meas_1 = {"show": True, "lab_text": "Meas. Frequency"}
    ref = {"show": False, "lab_text": "Reference frame #"}

    if isinstance(imaging, AbsoluteImaging):
        pass
    elif isinstance(imaging, TimeDifferenceImaging):
        ref["show"]= True
    elif isinstance(imaging, FrequenceDifferenceImaging):
        meas_0["show"]= True

    app.cB_ref_frame_idx.setEnabled(ref["show"])
    app.lab_ref_frame_idx.setEnabled(ref["show"])
    app.lab_freq_meas_0.setText(ref["lab_text"])

    app.cB_freq_meas_0.setEnabled(meas_0["show"])
    app.lab_freq_meas_0.setEnabled(meas_0["show"])
    app.lab_freq_meas_0.setText(meas_0["lab_text"])

    app.cB_freq_meas_1.setEnabled(meas_1["show"])
    app.lab_freq_meas_1.setEnabled(meas_1["show"])
    app.lab_freq_meas_1.setText(meas_1["lab_text"])


add_func_to_catalog(update_imaging_inputs_fields)


@dataclass
class ImagingInputs(EventDataClass):
    imaging: Imaging
    func: str = update_imaging_inputs_fields.__name__


# -------------------------------------------------------------------------------
## Update EITData plot options
# -------------------------------------------------------------------------------


def update_EITData_plots_options(app: Ui_MainWindow):
    """Activate/deactivate checkbox for EITData plots"""
    app.chB_Uplot.setEnabled(app.chB_plot_graph.isChecked())
    app.chB_diff.setEnabled(app.chB_plot_graph.isChecked())
    app.chB_y_log.setEnabled(app.chB_plot_graph.isChecked())


add_func_to_catalog(update_EITData_plots_options)


@dataclass
class EITDataPlotOptions(EventDataClass):
    func: str = update_EITData_plots_options.__name__


# -------------------------------------------------------------------------------
## Update frame aquisition progress
# -------------------------------------------------------------------------------


def update_progress_acquired_frame(
    app: Ui_MainWindow, idx_frame: int = 0, progression: int = 0
):
    """Update the progression bar and the idx of the aquired frame"""
    logger.debug('update_progress_acquired_frame-in')
    if idx_frame is not None:
        app.sB_actual_frame_cnt.setValue(idx_frame)
    app.meas_progress_bar.setValue(progression)
    logger.debug('update_progress_acquired_frame-ou')


add_func_to_catalog(update_progress_acquired_frame)


@dataclass
class FrameProgress(EventDataClass):
    """Set idx_frame to `None` to NOT update it """
    idx_frame: int = 0
    progression: int = 0
    func: str = update_progress_acquired_frame.__name__


# -------------------------------------------------------------------------------
## Update frame info text (during acquisition and replay)
# -------------------------------------------------------------------------------


def update_frame_info(app: Ui_MainWindow, info: str = ""):
    if info is not None:
        app.tE_frame_info.setText("\r\n".join(info))


add_func_to_catalog(update_frame_info)


@dataclass
class FrameInfo(EventDataClass):
    info: str = ""
    func: str = update_frame_info.__name__


# -------------------------------------------------------------------------------
## Update autosave inputs options
# -------------------------------------------------------------------------------


def update_autosave_options(app: Ui_MainWindow):
    """Activate/deactivate saving options"""
    app.lE_meas_dataset_dir.setEnabled(app.chB_dataset_autosave.isChecked())
    app.chB_dataset_save_img.setEnabled(app.chB_dataset_autosave.isChecked())
    app.chB_load_after_meas.setEnabled(app.chB_dataset_autosave.isChecked())
    app.chB_dataset_save_img.setChecked(
        app.chB_dataset_autosave.isChecked() and app.chB_dataset_save_img.isChecked()
    )

    app.chB_load_after_meas.setChecked(
        app.chB_dataset_autosave.isChecked() and app.chB_load_after_meas.isChecked()
    )


add_func_to_catalog(update_autosave_options)


@dataclass
class AutosaveOptions(EventDataClass):
    func: str = update_autosave_options.__name__


# -------------------------------------------------------------------------------
## Update live measurements state (after loading a measurement dataset)
# -------------------------------------------------------------------------------


def update_dataset_loaded(app: Ui_MainWindow, dataset_dir: str, nb_loaded_frame: int):
    """update the path of the loaded dataset and init the combosboxes and slider
    for the nb of loaded frames"""
    app.tE_load_dataset_dir.setText(dataset_dir)
    set_comboBox_items(app.cB_current_idx_frame, list(range(nb_loaded_frame)))
    set_comboBox_items(app.cB_ref_frame_idx, list(range(nb_loaded_frame)))
    set_QSlider_scale(app.slider_replay, nb_pos=nb_loaded_frame)


add_func_to_catalog(update_dataset_loaded)


@dataclass
class MeasDatasetLoaded(EventDataClass):
    dataset_dir: str
    nb_loaded_frame: int
    func: str = update_dataset_loaded.__name__


if __name__ == "__main__":
    """"""
    a=DevAvailables('')
    print(a)
