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
import logging
import threading
from typing import Any, Callable, List
from PyQt5 import QtGui, QtWidgets

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


logger = logging.getLogger(__name__)


def is_dataclass_instance(obj):
    return is_dataclass(obj) and not isinstance(obj, type)


################################################################################
# Event Dataclass use to trigger an update
################################################################################


class EventDataClass(ABC):
    """Abstract class of the dataclass defined for each update events"""

    func: str


################################################################################
# Event Agent
################################################################################


class UpdateAgent:
    def __init__(self, ui, events_ctlg) -> None:
        """This agent runs updating funntion of the Gui (app)
        depending on the data posted

        Args:
            app (_type_): GUI, Ui_MainWindow
            events (_type_): event catalog, a registed of all updating
            function callbacks
        """
        self._subscribers = {}
        self._ui = ui
        self._events_ctlg = events_ctlg

    @catch_error
    def post(self, data: EventDataClass):
        """Run the update event correspoding to the event data

        Args:
            data (EventDataClass): event data
        """
        if not is_dataclass_instance(data) or not isinstance(data, EventDataClass):
            logger.error("data are not compatible for update")
            return

        # logger.debug(f"thread update_event {threading.get_ident()}")
        data = self._mk_dict(data)
        func = data.pop("func")
        # logger.debug(f"updating {func=} with {data=}")
        self._events_ctlg[func](**data)

    def _mk_dict(self, data: EventDataClass) -> dict:
        """Transform the event data in dict and add the "app" key

        Args:
            data (EventDataClass): event data

        Returns:
            dict: data as dict with added "app" key
        """
        d = data.__dict__
        d["ui"] = self._ui
        return d


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

# def update_something(ui: Ui_MainWindow, data: Any):
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

# Colors for status
blue_light = "#bce6ff"
red_light = "#ff9f9c"
green_light = "#74a26b"
orange_light = "#ffd062"

# colors for buttons
bck_gnd_buttons = "#00aaff"


def initial_formatting_of_ui(ui: Ui_MainWindow):
    """Run some initial custom formating on gui object"""
    # set background of all buttons
    bck_gnd = "* { background-color: " + f"{bck_gnd_buttons}" + " }"
    for button in ui.centralwidget.findChildren(QtWidgets.QPushButton):
        button.setStyleSheet(bck_gnd)  # blue


register_func_in_catalog(initial_formatting_of_ui)


@dataclass
class EvtInitFormatUI(EventDataClass):
    """Event data to update the list of detected sciospec device"""

    func: str = initial_formatting_of_ui.__name__


# -------------------------------------------------------------------------------
## Update available EIT devices
# -------------------------------------------------------------------------------


def update_available_devices(ui: Ui_MainWindow, device: dict):
    """Refesh the list of devices in the comboBox"""
    items = list(device) or ["None device"]
    set_comboBox_items(ui.cB_ports, items)


register_func_in_catalog(update_available_devices)


@dataclass
class EvtDataSciospecDevices(EventDataClass):
    """Event data to update the list of detected sciospec device"""

    device: dict
    func: str = update_available_devices.__name__


# -------------------------------------------------------------------------------
## Update available capture devices
# -------------------------------------------------------------------------------


def update_available_capture_devices(ui: Ui_MainWindow, device: dict):
    """Refesh the list of devices in the comboBox"""
    items = list(device) or ["None device"]
    set_comboBox_items(ui.cB_capture_devices, items)


register_func_in_catalog(update_available_capture_devices)


@dataclass
class EvtDataCaptureDevices(EventDataClass):
    """Do not set func"""

    device: dict
    func: str = update_available_capture_devices.__name__


# -------------------------------------------------------------------------------
## Update device status
# -------------------------------------------------------------------------------


def update_device_status(ui: Ui_MainWindow, connected: bool, connect_prompt: str):
    """Actualize the status of the device"""
    ui.lab_device_status.setText(connect_prompt)
    ui.lab_device_status.adjustSize
    color = (
        f"background-color: {green_light}; color :white"
        if connected
        else f"background-color: {red_light}; color :black"
    )
    ui.lab_device_status.setStyleSheet(color)


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
    ui: Ui_MainWindow,
    setup: SciospecSetup,
    set_freq_max_enable: bool = True,
    error: bool = False,
):
    """Actualize the inputs fields for the setup of the device coresponding to it"""
    ui.lE_sn.setText(setup.get_sn())
    ## Update EthernetConfig
    ui.chB_dhcp.setChecked(bool(setup.ethernet_config.get_dhcp()))
    ui.lE_ip.setText(setup.ethernet_config.get_ip())
    ui.lE_mac.setText(setup.ethernet_config.get_mac())

    ## Update OutputConfig Stamps
    ui.chB_exc_stamp.setChecked(bool(setup.output_config.get_exc_stamp()))
    ui.chB_current_stamp.setChecked(bool(setup.output_config.get_current_stamp()))
    ui.chB_time_stamp.setChecked(bool(setup.output_config.get_time_stamp()))

    # Update Measurement Setups
    block_signals(ui.sBd_frame_rate.setValue, setup.get_frame_rate())
    block_signals(ui.sBd_max_frame_rate.setValue, setup.get_max_frame_rate())
    block_signals(ui.sB_burst.setValue, setup.get_burst())
    block_signals(ui.sBd_exc_amp.setValue, setup.get_exc_amp() * 1000)  # from A -> mA
    block_signals(ui.sBd_freq_min.setValue, setup.get_freq_min())
    block_signals(ui.sBd_freq_max.setValue, setup.get_freq_max())
    block_signals(ui.sB_freq_steps.setValue, setup.get_freq_steps())
    block_signals(ui.cB_scale.setCurrentText, setup.get_freq_scale())

    ui.sBd_freq_max.setEnabled(set_freq_max_enable)
    color = f"background-color: {red_light}" if error else "background-color: white"
    ui.lab_maxF.setStyleSheet(color)
    ui.lab_minF.setStyleSheet(color)
    ui.lab_steps.setStyleSheet(color)

    set_QTableWidget(ui.tw_exc_mat_model, setup.get_exc_pattern_mdl(), 0)
    set_QTableWidget(ui.tw_exc_mat_chip, setup.get_exc_pattern(), 0)
    update_freqs_list(ui, setup.get_freqs_list())


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


def update_freqs_list(ui: Ui_MainWindow, freqs: List[Any]):
    set_comboBox_items(ui.cB_eit_imaging_ref_freq, list(freqs))
    set_comboBox_items(ui.cB_eit_imaging_meas_freq, list(freqs))


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
        lab_style=f"background-color: {red_light}; color :black",
        pB_txt="Start",
        pB_status_tip="Start aquisition of a new measurement dataset (Ctrl + Shift +Space)",
    )
    MEASURING = MeasuringStatusUpdateData(
        lab_txt="MEASUREMENTS RUN",
        lab_style=f"background-color: {green_light}; color :black",
        pB_txt="Pause",
        pB_status_tip="Pause aquisition of measurement dataset (Ctrl + Shift +Space)",
    )
    PAUSED = MeasuringStatusUpdateData(
        lab_txt="MEASUREMENTS PAUSED",
        lab_style=f"background-color: {orange_light}; color :black",
        pB_txt="Resume",
        pB_status_tip="Restart aquisition of measurement dataset (Ctrl + Shift +Space)",
    )


def update_meas_status(ui: Ui_MainWindow, meas_status: MeasuringStatus):
    """Update the live measurements status label and the mesurements
    start/pause/resume button"""
    v: MeasuringStatusUpdateData = meas_status.value
    ui.lab_live_meas_status.setText(v.lab_txt)
    ui.lab_live_meas_status.setStyleSheet(v.lab_style)
    ui.pB_start_meas.setText(v.pB_txt)
    ui.pB_start_meas.setStatusTip(v.pB_status_tip)


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
        lab_style=f"background-color: {red_light}; color :black",
        pB_txt="Start capture",
        pB_status_tip="",
        pB_con_txt="Connect",
    )
    CONNECTED = CaptureStatusUpdateData(
        lab_txt="CONNECTED",
        lab_style=f"background-color: {orange_light}; color :black",
        pB_txt="Start capture",
        pB_status_tip="",
    )
    REPLAY_AUTO = CaptureStatusUpdateData(
        lab_txt="REPLAY Auto",
        lab_style=f"background-color: {green_light}; color :black",
        pB_txt="Start capture",
        pB_status_tip="",
        pB_enable=False,
        pB_con_enable=True,
    )
    REPLAY_MAN = CaptureStatusUpdateData(
        lab_txt="REPLAY MAN",
        lab_style=f"background-color: {blue_light}; color :black",
        pB_txt="Start capture",
        pB_status_tip="",
        pB_enable=False,
    )

    MEASURING = CaptureStatusUpdateData(
        lab_txt="MEASURING",
        lab_style=f"background-color: {green_light}; color :black",
        pB_txt="Start capture",
        pB_enable=False,
        pB_con_enable=True,
    )
    LIVE = CaptureStatusUpdateData(
        lab_txt="LIVE",
        lab_style=f"background-color: {green_light}; color :black",
        pB_txt="Stop capture",
    )


def update_capture_status(ui: Ui_MainWindow, capture_mode: CaptureStatus):
    """Update the live measurements status label and the mesurements
    start/pause/resume button"""
    v: CaptureStatusUpdateData = capture_mode.value
    ui.lab_capture_status.setText(v.lab_txt)
    ui.lab_capture_status.setStyleSheet(v.lab_style)
    ui.pB_capture_start_stop.setText(v.pB_txt)
    ui.pB_capture_start_stop.setStatusTip(v.pB_status_tip)
    ui.pB_capture_start_stop.setEnabled(v.pB_enable)
    if "CONN" in v.lab_txt:
        ui.pB_capture_connect.setText(v.pB_con_txt)


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
        lab_style=f"background-color: {red_light}; color :black",
        pB_icon=":/icons/icons/icon_play.png",
    )
    LOADED = ReplayStatusUpdateData(
        lab_txt="DATASET LOADED",
        lab_style=f"background-color: {blue_light}; color :black",
        pB_icon=":/icons/icons/icon_play.png",
    )
    PLAYING = ReplayStatusUpdateData(
        lab_txt="REPLAY RUN",
        lab_style=f"background-color: {green_light}; color :black",
        pB_icon=":/icons/icons/icon_pause.png",
    )


def update_replay_status(ui: Ui_MainWindow, status: ReplayStatus):
    """Update the status label"""
    v: ReplayStatusUpdateData = status.value
    ui.lab_replay_status.setText(v.lab_txt)
    ui.lab_replay_status.setStyleSheet(v.lab_style)
    icon = QtGui.QIcon()
    icon.addPixmap(QtGui.QPixmap(v.pB_icon), QtGui.QIcon.Normal, QtGui.QIcon.Off)
    ui.pB_replay_play.setIcon(icon)


register_func_in_catalog(update_replay_status)


@dataclass
class EvtDataReplayStatusChanged(EventDataClass):
    status: ReplayStatus
    func: str = update_replay_status.__name__


# -------------------------------------------------------------------------------
## Update imaging inputs fields
# -------------------------------------------------------------------------------


def update_imaging_inputs_fields(ui: Ui_MainWindow, imaging: Imaging):
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

    ui.cB_eit_imaging_ref_frame.setEnabled(ref["show"])
    ui.lab_ref_frame_idx.setEnabled(ref["show"])
    ui.lab_freq_meas_0.setText(ref["lab_text"])

    ui.cB_eit_imaging_ref_freq.setEnabled(meas_0["show"])
    ui.lab_freq_meas_0.setEnabled(meas_0["show"])
    ui.lab_freq_meas_0.setText(meas_0["lab_text"])

    ui.cB_eit_imaging_meas_freq.setEnabled(meas_1["show"])
    ui.lab_freq_meas_1.setEnabled(meas_1["show"])
    ui.lab_freq_meas_1.setText(meas_1["lab_text"])


register_func_in_catalog(update_imaging_inputs_fields)


@dataclass
class EvtDataImagingInputsChanged(EventDataClass):
    imaging: Imaging
    func: str = update_imaging_inputs_fields.__name__


# -------------------------------------------------------------------------------
## Update EITData plot options
# -------------------------------------------------------------------------------


def update_EITData_plots_options(ui: Ui_MainWindow):
    """Activate/deactivate checkbox for EITData plots"""
    # ui.rB_UPlot.setEnabled(ui.chB_eit_data_monitoring.isChecked())
    # ui.rB_Uch.setEnabled(ui.chB_eit_data_monitoring.isChecked())

    # ui.rB_monitoring.setEnabled(ui.chB_eit_data_monitoring.isChecked())


register_func_in_catalog(update_EITData_plots_options)


@dataclass
class EvtDataEITDataPlotOptionsChanged(EventDataClass):
    func: str = update_EITData_plots_options.__name__


# -------------------------------------------------------------------------------
## Update frame aquisition progress
# -------------------------------------------------------------------------------


def update_progress_acquired_frame(
    ui: Ui_MainWindow, idx_frame: int = 0, progression: int = 0
):
    """Update the progression bar and the idx of the aquired frame"""
    logger.debug("update_progress_acquired_frame-in")
    if idx_frame is not None:
        ui.sB_actual_frame_cnt.setValue(idx_frame)
    ui.meas_progress_bar.setValue(progression)
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


def update_frame_info(ui: Ui_MainWindow, info: str = ""):
    if info is not None:
        ui.tE_frame_info.setText("\r\n".join(info))


register_func_in_catalog(update_frame_info)


@dataclass
class EvtDataNewFrameInfo(EventDataClass):
    info: str = ""
    func: str = update_frame_info.__name__


# -------------------------------------------------------------------------------
## Update autosave inputs options
# -------------------------------------------------------------------------------


def update_autosave_options(
    ui: Ui_MainWindow, autosave: bool, save_img: bool, load_after_meas: bool
):
    """Activate/deactivate saving options"""
    ui.lE_meas_dataset_dir.setEnabled(ui.chB_dataset_autosave.isChecked())
    ui.chB_dataset_save_img.setEnabled(ui.chB_dataset_autosave.isChecked())
    ui.chB_load_after_meas.setEnabled(ui.chB_dataset_autosave.isChecked())
    block_signals(ui.chB_dataset_autosave.setChecked, autosave)
    block_signals(ui.chB_dataset_save_img.setChecked, save_img)
    block_signals(ui.chB_load_after_meas.setChecked, load_after_meas)
    # ui.chB_dataset_save_img.setChecked(
    #     ui.chB_dataset_autosave.isChecked() and ui.chB_dataset_save_img.isChecked()
    # )

    # ui.chB_load_after_meas.setChecked(
    #     ui.chB_dataset_autosave.isChecked() and ui.chB_load_after_meas.isChecked()
    # )


register_func_in_catalog(update_autosave_options)


@dataclass
class EvtDataAutosaveOptionsChanged(EventDataClass):
    autosave: bool
    save_img: bool
    load_after_meas: bool
    func: str = update_autosave_options.__name__


# -------------------------------------------------------------------------------
## Update replay measurements state (after loading a measurement dataset)
# -------------------------------------------------------------------------------


def update_dataset_loaded(ui: Ui_MainWindow, dataset_dir: str, nb_loaded_frame: int):
    """update the path of the loaded dataset and init the combosboxes and slider
    for the nb of loaded frames"""
    ui.tE_load_dataset_dir.setText(dataset_dir)
    set_comboBox_items(ui.cB_replay_frame_idx, list(range(nb_loaded_frame)))
    set_comboBox_items(ui.cB_eit_imaging_ref_frame, list(range(nb_loaded_frame)))
    set_QSlider_scale(ui.slider_replay, nb_pos=nb_loaded_frame)


register_func_in_catalog(update_dataset_loaded)


@dataclass
class EvtDataMeasDatasetLoaded(EventDataClass):
    dataset_dir: str
    nb_loaded_frame: int
    func: str = update_dataset_loaded.__name__


# -------------------------------------------------------------------------------
## Update replay idx (after loading a measurement dataset)
# -------------------------------------------------------------------------------


def update_replay_frame_changed(ui: Ui_MainWindow, idx: int):
    """update the path of the loaded dataset and init the combosboxes and slider
    for the nb of loaded frames"""
    set_comboBox_index(ui.cB_replay_frame_idx, index=idx)
    set_QSlider_position(ui.slider_replay, pos=idx)


register_func_in_catalog(update_replay_frame_changed)


@dataclass
class EvtDataReplayFrameChanged(EventDataClass):
    idx: int
    func: str = update_replay_frame_changed.__name__


# -------------------------------------------------------------------------------
## Update replay idx (after loading a measurement dataset)
# -------------------------------------------------------------------------------


def update_captured_image(ui: Ui_MainWindow, image: QtGui.QImage, image_path: str):
    """update the path of the loaded dataset and init the combosboxes and slider
    for the nb of loaded frames"""
    if not isinstance(image, QtGui.QImage):
        logger.warning(f"{image=} is not an QtGui.QImage")
        return

    ui.video_frame.setPixmap(QtGui.QPixmap.fromImage(image))
    # resize the group box to fit image size
    w = max(image.width() + 20, ui.groupBox_video.minimumWidth())
    ui.groupBox_video.setMaximumWidth(w)
    ui.lE_path_video_frame.setText(image_path)


register_func_in_catalog(update_captured_image)


@dataclass
class EvtDataCaptureImageChanged(EventDataClass):
    image: QtGui.QImage
    image_path: str = ""
    func: str = update_captured_image.__name__


if __name__ == "__main__":
    """"""
    a = EvtDataSciospecDevices("")
    print(a)
    print(MeasuringStatus.NOT_MEASURING._name_.lower())
