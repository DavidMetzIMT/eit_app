"""To update the gui an UpdateAgent is here defined. By posting data through 
the agent, a specified part of the gui will be updated

Those data has to be EventdataClass and should contain a updating function 
to run as string and corresponding specific data. 

Each updating function has to to be registered in a the Catalog UPDATE_EVENTS
trouh the call
>> register_func_in_catalog(updating_func)

"""

from abc import ABC
from dataclasses import dataclass, is_dataclass
from logging import getLogger
import threading
from typing import Any, Callable, List
from PyQt5 import QtGui

from eit_app.gui import Ui_MainWindow
from eit_app.gui_utils import (
    block_signals,
    set_QSlider_position,
    set_comboBox_index,
    set_comboBox_items,
    set_QSlider_scale,
    set_QTableWidget,
)
from eit_app.sciospec.setup import SciospecSetup
from eit_model.imaging import (
    Imaging,
    AbsoluteImaging,
    TimeDifferenceImaging,
    FrequenceDifferenceImaging,
)
from glob_utils.decorator.decorator import catch_error
from glob_utils.flags.status import BaseStatus


logger = getLogger(__name__)


def is_dataclass_instance(obj):
    return is_dataclass(obj) and not isinstance(obj, type)


################################################################################
# Event Dataclass use to trigger an update
################################################################################


class EventDataClass(ABC):
    """Abstract class of the dataclass defined for each update events"""
    func:str


################################################################################
# Event Agent
################################################################################


class UpdateAgent:
    def __init__(self, app, events_ctlg) -> None:
        """This agent runs updating funntion of the Gui (app) 
        depending on the data posted

        Args:
            app (_type_): GUI, Ui_MainWindow
            events (_type_): event catalog, a registed of all updating 
            function callbacks
        """
        self._subscribers = {}
        self._app = app
        self._events_ctlg = events_ctlg

    def _mk_dict(self, data: EventDataClass)->dict:
        """Transform the event data in dict and add the "app" key

        Args:
            data (EventDataClass): event data

        Returns:
            dict: data as dict with added "app" key
        """
        d = data.__dict__
        d["app"] = self._app
        return d

    @catch_error
    def post(self, data: EventDataClass):
        """Run the update event correspoding to the event data

        Args:
            data (EventDataClass): event data
        """
        if not is_dataclass_instance(data) or not isinstance(data, EventDataClass):
            logger.error("data are not compatible for update")
            return

        logger.info(f"thread update_event {threading.get_ident()}")
        data = self._mk_dict(data)
        func = data.pop("func")
        logger.debug(f"updating {func=} with {data=}")
        self._events_ctlg[func](**data)


################################################################################
# Update events Catalog
################################################################################

# catalog of update functions event
UPDATE_EVENTS: dict[str, Callable] = {}


def register_func_in_catalog(func: Callable):
    """Add the function to the UPDATE_EVENTS catalog"""
    name = func.__name__
    UPDATE_EVENTS[func.__name__] = func

################################################################################
# Update fucntions and assiociated EventDataClass
################################################################################


# ## TEMPLATE TO ADD AN UPDATING FUCNTION
# # -------------------------------------------------------------------------------
# ## Update somthing
# # ------------------------------------------------------------------------------

# def update_something(app: Ui_MainWindow, data: Any):
#     """code for updating somteh from app"""

# register_func_in_catalog(update_something)

# @dataclass
# class EvtDataFoo(EventDataClass):
#     """Event data to update the list of detected sciospec device"""
#     data: Any
#     func: str = update_something.__name__


# -------------------------------------------------------------------------------
## Update available EIT devices
# -------------------------------------------------------------------------------


def update_available_devices(app: Ui_MainWindow, device: dict):
    """Refesh the list of devices in the comboBox"""
    items = list(device) or ["None device"]
    set_comboBox_items(app.cB_ports, items)


register_func_in_catalog(update_available_devices)


@dataclass
class EvtDataSciospecDevices(EventDataClass):
    """Event data to update the list of detected sciospec device"""
    device: dict
    func: str = update_available_devices.__name__


# -------------------------------------------------------------------------------
## Update available capture devices
# -------------------------------------------------------------------------------


def update_available_capture_devices(app: Ui_MainWindow, device: dict):
    """Refesh the list of devices in the comboBox"""
    items = list(device) or ["None device"]
    set_comboBox_items(app.cB_capture_devices, items)


register_func_in_catalog(update_available_capture_devices)


@dataclass
class EvtDataCaptureDevices(EventDataClass):
    """Do not set func"""

    device: dict
    func: str = update_available_capture_devices.__name__


# -------------------------------------------------------------------------------
## Update device status
# -------------------------------------------------------------------------------


def update_device_status(app: Ui_MainWindow, connected: bool, connect_prompt: str):
    """Actualize the status of the device"""
    app.lab_device_status.setText(connect_prompt)
    app.lab_device_status.adjustSize
    color = (
        "background-color: green;color :white"
        if connected
        else "background-color: red;color :black"
    )
    app.lab_device_status.setStyleSheet(color)


register_func_in_catalog(update_device_status)


@dataclass
class EvtDataSciospecDevConnected(EventDataClass):

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
    block_signals(app.sBd_frame_rate.setValue, setup.get_frame_rate())
    block_signals(
        app.sBd_max_frame_rate.setValue, setup.get_max_frame_rate()
    )
    block_signals(app.sB_burst.setValue, setup.get_burst())
    block_signals(
        app.sBd_exc_amp.setValue, setup.get_exc_amp() * 1000
    )  # from A -> mA
    block_signals(app.sBd_freq_min.setValue, setup.get_freq_min())
    block_signals(app.sBd_freq_max.setValue, setup.get_freq_max())
    block_signals(app.sB_freq_steps.setValue, setup.get_freq_steps())
    block_signals(app.cB_scale.setCurrentText, setup.get_freq_scale())

    app.sBd_freq_max.setEnabled(set_freq_max_enable)
    color = "background-color: red" if error else "background-color: white"
    app.lab_maxF.setStyleSheet(color)
    app.lab_minF.setStyleSheet(color)
    app.lab_steps.setStyleSheet(color)

    set_QTableWidget(app.tw_exc_mat_model, setup.get_exc_pattern_mdl(), 0)
    set_QTableWidget(app.tw_exc_mat_chip, setup.get_exc_pattern(), 0)
    update_freqs_list(app, setup.get_freqs_list())


register_func_in_catalog(update_device_setup)


@dataclass
class EvtDataSciospecDevSetup(EventDataClass):
    setup: SciospecSetup
    set_freq_max_enable: bool = True
    error: bool = False
    func: str = update_device_setup.__name__


# -------------------------------------------------------------------------------
## Update Frequency list for the imaging inputs
# -------------------------------------------------------------------------------


def update_freqs_list(app: Ui_MainWindow, freqs: List[Any]):
    set_comboBox_items(app.cB_eit_imaging_ref_freq, list(freqs))
    set_comboBox_items(app.cB_eit_imaging_meas_freq, list(freqs))


# -------------------------------------------------------------------------------
## Update live measurements state
# -------------------------------------------------------------------------------


@dataclass
class MeasuringStatusUpdateData:
    lab_txt: str
    lab_style: str
    pB_txt: str
    pB_status_tip: str


class MeasuringStatus(BaseStatus):
    NOT_MEASURING = MeasuringStatusUpdateData(
        lab_txt="NOT MEASURING",
        lab_style="background-color: red",
        pB_txt="Start",
        pB_status_tip="Start aquisition of a new measurement dataset (Ctrl + Shift +Space)",
    )
    MEASURING = MeasuringStatusUpdateData(
        lab_txt="MEASUREMENTS RUN",
        lab_style="background-color: green; color :white",
        pB_txt="Pause",
        pB_status_tip="Pause aquisition of measurement dataset (Ctrl + Shift +Space)",
    )
    PAUSED = MeasuringStatusUpdateData(
        lab_txt="MEASUREMENTS PAUSED",
        lab_style="background-color: yellow",
        pB_txt="Resume",
        pB_status_tip="Restart aquisition of measurement dataset (Ctrl + Shift +Space)",
    )


def update_meas_status(app: Ui_MainWindow, meas_status: MeasuringStatus):
    """Update the live measurements status label and the mesurements
    start/pause/resume button"""
    v: MeasuringStatusUpdateData = meas_status.value
    app.lab_live_meas_status.setText(v.lab_txt)
    app.lab_live_meas_status.setStyleSheet(v.lab_style)
    app.pB_start_meas.setText(v.pB_txt)
    app.pB_start_meas.setStatusTip(v.pB_status_tip)


register_func_in_catalog(update_meas_status)


@dataclass
class EvtDataSciospecDevMeasuringStatusChanged(EventDataClass):
    meas_status: MeasuringStatus
    func: str = update_meas_status.__name__


# -------------------------------------------------------------------------------
## Update live measurements state
# -------------------------------------------------------------------------------


@dataclass
class CaptureStatusUpdateData:
    lab_txt: str
    lab_style: str
    pB_txt: str = "Start capture"
    pB_status_tip: str = ""
    pB_enable: bool = True
    pB_con_txt: str = "Disconnect"
    pB_con_status_tip: str = ""
    pB_con_enable: bool = True


class CaptureStatus(BaseStatus):
    NOT_CONNECTED = CaptureStatusUpdateData(
        lab_txt="NOT CONNECTED",
        lab_style="background-color: red; color :black",
        pB_txt="Start capture",
        pB_status_tip="",
        pB_con_txt="Connect",
    )
    CONNECTED = CaptureStatusUpdateData(
        lab_txt="CONNECTED",
        lab_style="background-color: grey",
        pB_txt="Start capture",
        pB_status_tip="",
    )
    REPLAY = CaptureStatusUpdateData(
        lab_txt="REPLAY",
        lab_style="background-color: blue; color :white",
        pB_txt="Start capture",
        pB_status_tip="",
        pB_enable=False,
        pB_con_enable=True,
    )
    MEASURING = CaptureStatusUpdateData(
        lab_txt="MEASURING",
        lab_style="background-color: darkGreen; color :white",
        pB_txt="Start capture",
        pB_enable=False,
        pB_con_enable=True,
    )
    LIVE = CaptureStatusUpdateData(
        lab_txt="LIVE",
        lab_style="background-color: green; color :white",
        pB_txt="Stop capture",
    )


def update_capture_status(app: Ui_MainWindow, capture_mode: CaptureStatus):
    """Update the live measurements status label and the mesurements
    start/pause/resume button"""
    v: CaptureStatusUpdateData = capture_mode.value
    app.lab_capture_status.setText(v.lab_txt)
    app.lab_capture_status.setStyleSheet(v.lab_style)
    app.pB_capture_start_stop.setText(v.pB_txt)
    app.pB_capture_start_stop.setStatusTip(v.pB_status_tip)
    app.pB_capture_start_stop.setEnabled(v.pB_enable)
    app.pB_capture_connect.setText(v.pB_con_txt)


register_func_in_catalog(update_capture_status)


@dataclass
class EvtDataCaptureStatusChanged(EventDataClass):
    capture_mode: CaptureStatus
    func: str = update_capture_status.__name__


# -------------------------------------------------------------------------------
## Update replay status
# -------------------------------------------------------------------------------
@dataclass
class ReplayStatusUpdateData:
    lab_txt: str
    lab_style: str
    pB_icon: str = ":/icons/icons/icon_play.png"


class ReplayStatus(BaseStatus):
    OFF = ReplayStatusUpdateData(
        lab_txt="NONE DATASET",
        lab_style="background-color: red; color :black",
        pB_icon=":/icons/icons/icon_play.png",
    )
    LOADED = ReplayStatusUpdateData(
        lab_txt="DATASET LOADED",
        lab_style="background-color: green; color :white",
        pB_icon=":/icons/icons/icon_play.png",
    )
    PLAYING = ReplayStatusUpdateData(
        lab_txt="REPLAY RUN",
        lab_style="background-color: blue; color :white",
        pB_icon=":/icons/icons/icon_pause.png",
    )


def update_replay_status(app: Ui_MainWindow, status: ReplayStatus):
    """Update the status label"""
    v: ReplayStatusUpdateData = status.value
    app.lab_replay_status.setText(v.lab_txt)
    app.lab_replay_status.setStyleSheet(v.lab_style)
    icon = QtGui.QIcon()
    icon.addPixmap(QtGui.QPixmap(v.pB_icon), QtGui.QIcon.Normal, QtGui.QIcon.Off)
    app.pB_replay_play.setIcon(icon)


register_func_in_catalog(update_replay_status)


@dataclass
class EvtDataReplayStatusChanged(EventDataClass):
    status: ReplayStatus
    func: str = update_replay_status.__name__


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
        ref["show"] = True
    elif isinstance(imaging, FrequenceDifferenceImaging):
        meas_0["show"] = True

    app.cB_eit_imaging_ref_frame.setEnabled(ref["show"])
    app.lab_ref_frame_idx.setEnabled(ref["show"])
    app.lab_freq_meas_0.setText(ref["lab_text"])

    app.cB_eit_imaging_ref_freq.setEnabled(meas_0["show"])
    app.lab_freq_meas_0.setEnabled(meas_0["show"])
    app.lab_freq_meas_0.setText(meas_0["lab_text"])

    app.cB_eit_imaging_meas_freq.setEnabled(meas_1["show"])
    app.lab_freq_meas_1.setEnabled(meas_1["show"])
    app.lab_freq_meas_1.setText(meas_1["lab_text"])


register_func_in_catalog(update_imaging_inputs_fields)


@dataclass
class EvtDataImagingInputsChanged(EventDataClass):
    imaging: Imaging
    func: str = update_imaging_inputs_fields.__name__


# -------------------------------------------------------------------------------
## Update EITData plot options
# -------------------------------------------------------------------------------


def update_EITData_plots_options(app: Ui_MainWindow):
    """Activate/deactivate checkbox for EITData plots"""
    app.chB_eit_data_Uplot.setEnabled(True)
    app.chB_eit_data_Udiffplot.setEnabled(True)
    app.chB_eit_data_y_log.setEnabled(True)


register_func_in_catalog(update_EITData_plots_options)


@dataclass
class EvtDataEITDataPlotOptionsChanged(EventDataClass):
    func: str = update_EITData_plots_options.__name__


# -------------------------------------------------------------------------------
## Update frame aquisition progress
# -------------------------------------------------------------------------------


def update_progress_acquired_frame(
    app: Ui_MainWindow, idx_frame: int = 0, progression: int = 0
):
    """Update the progression bar and the idx of the aquired frame"""
    logger.debug("update_progress_acquired_frame-in")
    if idx_frame is not None:
        app.sB_actual_frame_cnt.setValue(idx_frame)
    app.meas_progress_bar.setValue(progression)
    logger.debug("update_progress_acquired_frame-ou")


register_func_in_catalog(update_progress_acquired_frame)


@dataclass
class EvtDataNewFrameProgress(EventDataClass):
    """Set idx_frame to `None` to NOT update it"""

    idx_frame: int = 0
    progression: int = 0
    func: str = update_progress_acquired_frame.__name__


# -------------------------------------------------------------------------------
## Update frame info text (during acquisition and replay)
# -------------------------------------------------------------------------------


def update_frame_info(app: Ui_MainWindow, info: str = ""):
    if info is not None:
        app.tE_frame_info.setText("\r\n".join(info))


register_func_in_catalog(update_frame_info)


@dataclass
class EvtDataNewFrameInfo(EventDataClass):
    info: str = ""
    func: str = update_frame_info.__name__


# -------------------------------------------------------------------------------
## Update autosave inputs options
# -------------------------------------------------------------------------------


def update_autosave_options(app: Ui_MainWindow, autosave:bool, save_img:bool, load_after_meas:bool):
    """Activate/deactivate saving options"""
    app.lE_meas_dataset_dir.setEnabled(app.chB_dataset_autosave.isChecked())
    app.chB_dataset_save_img.setEnabled(app.chB_dataset_autosave.isChecked())
    app.chB_load_after_meas.setEnabled(app.chB_dataset_autosave.isChecked())
    block_signals(app.chB_dataset_autosave.setChecked, autosave)
    block_signals(app.chB_dataset_save_img.setChecked, save_img)
    block_signals(app.chB_load_after_meas.setChecked, load_after_meas)
    # app.chB_dataset_save_img.setChecked(
    #     app.chB_dataset_autosave.isChecked() and app.chB_dataset_save_img.isChecked()
    # )

    # app.chB_load_after_meas.setChecked(
    #     app.chB_dataset_autosave.isChecked() and app.chB_load_after_meas.isChecked()
    # )


register_func_in_catalog(update_autosave_options)


@dataclass
class EvtDataAutosaveOptionsChanged(EventDataClass):
    autosave:bool
    save_img:bool
    load_after_meas:bool
    func: str = update_autosave_options.__name__


# -------------------------------------------------------------------------------
## Update replay measurements state (after loading a measurement dataset)
# -------------------------------------------------------------------------------


def update_dataset_loaded(app: Ui_MainWindow, dataset_dir: str, nb_loaded_frame: int):
    """update the path of the loaded dataset and init the combosboxes and slider
    for the nb of loaded frames"""
    app.tE_load_dataset_dir.setText(dataset_dir)
    set_comboBox_items(app.cB_replay_frame_idx, list(range(nb_loaded_frame)))
    set_comboBox_items(app.cB_eit_imaging_ref_frame, list(range(nb_loaded_frame)))
    set_QSlider_scale(app.slider_replay, nb_pos=nb_loaded_frame)


register_func_in_catalog(update_dataset_loaded)


@dataclass
class EvtDataMeasDatasetLoaded(EventDataClass):
    dataset_dir: str
    nb_loaded_frame: int
    func: str = update_dataset_loaded.__name__


# -------------------------------------------------------------------------------
## Update replay idx (after loading a measurement dataset)
# -------------------------------------------------------------------------------


def update_replay_frame_changed(app: Ui_MainWindow, idx: int):
    """update the path of the loaded dataset and init the combosboxes and slider
    for the nb of loaded frames"""
    set_comboBox_index(app.cB_replay_frame_idx, index=idx)
    set_QSlider_position(app.slider_replay, pos=idx)


register_func_in_catalog(update_replay_frame_changed)


@dataclass
class EvtDataReplayFrameChanged(EventDataClass):
    idx: int
    func: str = update_replay_frame_changed.__name__


# -------------------------------------------------------------------------------
## Update replay idx (after loading a measurement dataset)
# -------------------------------------------------------------------------------


def update_captured_image(app: Ui_MainWindow, image: QtGui.QImage):
    """update the path of the loaded dataset and init the combosboxes and slider
    for the nb of loaded frames"""
    if not isinstance(image, QtGui.QImage):
        logger.warning(f"{image=} is not an QtGui.QImage")
        return
    app.video_frame.setPixmap(QtGui.QPixmap.fromImage(image))


register_func_in_catalog(update_captured_image)


@dataclass
class EvtDataCaptureImageChanged(EventDataClass):
    image: QtGui.QImage
    func: str = update_captured_image.__name__


if __name__ == "__main__":
    """"""
    a = EvtDataSciospecDevices("")
    print(a)
    print(MeasuringStatus.NOT_MEASURING._name_.lower())
