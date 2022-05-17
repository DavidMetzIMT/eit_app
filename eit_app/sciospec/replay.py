from enum import Enum
import logging
from threading import Timer
from typing import Any, Callable, Iterable, Mapping, Union

from eit_app.sciospec.measurement import DataEmitFrame4Computation
from eit_app.video.capture import SetStatusWReplayStatus
from eit_app.com_channels import (
    AddToCaptureSignal,
    AddToDatasetSignal,
    AddToGuiSignal,
    DataReplayStart,
    SignalReciever,
)
from eit_app.update_gui import (
    EvtDataReplayFrameChanged,
    EvtDataReplayStatusChanged,
    ReplayStatus,
)
from glob_utils.flags.status import AddStatus
import glob_utils.dialog.Qt_dialogs
from PyQt5 import QtCore

logger = logging.getLogger(__name__)


def check_is_on(func):
    """Decorator: which check if the device is not measuring

    - if device is not measuring >> the function is run
    - if device is measuring:
        - the measurement can be stopped by setting force_stop to `True`. A
        info msgBox will be popped to inform the user and the
        function will be run
        - otherwise a info msgBox will be popped to ask the user to stop
        the measuremnet before using that function

    Args:
        force_stop (bool, optional): set to `True` to force the device to
        run the function after stoping the measurements. Defaults to `False`.
    """

    def wrap(self, *args, **kwargs) -> Union[Any, None]:
        if self.is_off:
            logger.warning("No Measurement loaded!, Please load measurements first!")
            glob_utils.dialog.Qt_dialogs.warningMsgBox(
                title="No Measurement loaded!",
                message="Please load measurements first!",
            )
            return None
        return func(self, *args, **kwargs)

    return wrap


class RepeatTimer(Timer):
    """Thread Timer which start all over again"""

    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)


class ReplayMeasurementsAgent(
    SignalReciever, AddStatus, AddToGuiSignal, AddToDatasetSignal, AddToCaptureSignal
):
    """This Class is responsible of the replay of measurements"""

    def __init__(self) -> None:
        super().__init__()
        self.init_reciever(data_callbacks={DataReplayStart: self.start})
        self.init_status(status_values=ReplayStatus)
        self.nb_frame_loaded = 0
        self.actual_frame_idx = 0
        self.timeout = 1.0
        self.set_timer()

    ## =========================================================================
    ##  Status
    ## =========================================================================

    def start(self, data: DataReplayStart, **kwargs) -> None:
        """Start the replay of a loaded dataset
        (called from dataset signal after loading )

        Args:
            data (DataReplayStart): contain the nb of frame loaded
        """
        self.nb_frame_loaded = data.nb_frame
        self.set_status(ReplayStatus.LOADED)
        self.begin()

    def set_actual_frame(self, idx: int, **kwargs) -> None:
        """Set actual frame and compute it (called from GUI)"""
        self._set_actual_frame(idx)
        self.compute_actual_frame()

    def set_timeout(self, sec: float, *args, **kwargs) -> None:
        """Set timeout of the timer, if the timer is running, it will be
        stopped and restarted with new value (called from GUI)
        """
        logger.info(f"new Timeout in sec:{sec}")
        self.timeout = sec
        self.timer.cancel()
        self.activate_deactivate_timer()

    def compute_actual_frame(self, *args, **kwargs):
        """Compute the actual frame (self.actual_frame_idx),
        called in intern and from GUI signal
        """
        self.compute_meas_frame(self.actual_frame_idx)

    ## =========================================================================
    ##  Status
    ## =========================================================================

    # @abstractmethod - AddStatus
    def status_has_changed(self, status: Enum, was_status: Enum) -> None:
        """Update the was life flag, called by status changed signal"""
        self.activate_deactivate_timer()
        self.to_gui.emit(EvtDataReplayStatusChanged(status))
        self.to_capture.emit(SetStatusWReplayStatus(self.is_playing, self.is_idle))
        logger.debug(f"ReplayMeasurements Status set to : {status.value}")

    @property
    def is_idle(self) -> bool:
        return self.is_status(ReplayStatus.LOADED)

    @property
    def is_playing(self) -> bool:
        return self.is_status(ReplayStatus.PLAYING)

    @property
    def is_off(self) -> bool:
        return self.is_status(ReplayStatus.OFF)

    def set_mode(self, meas_status_dev: bool, **kwargs):
        """Set internal mode depending on the measuring status of
        the acquisition device

        this method is called by a signal from the device at fro each status changes

        if meas_status_dev is `True` the capture_module is set to meas mode
        otherwise the capture_module is set back to live or to idle mode"""
        if not isinstance(meas_status_dev, bool):
            return

        if meas_status_dev:
            self.set_status(ReplayStatus.OFF)

    ## =========================================================================
    ##  Timer
    ## =========================================================================

    def set_timer(self):
        """Set timer with self.timeout, the timer call the method next"""
        self.timer = RepeatTimer(self.timeout, self.next)

    def activate_deactivate_timer(self) -> None:
        """Depending on the actual Status of the Agent, the tiemr is cancelled
        or set and started
        """
        if self.is_idle:
            self.timer.cancel()
        elif self.is_playing:
            self.set_timer()
            self.timer.start()

    ## =========================================================================
    ## Signal for frame computation
    ## =========================================================================

    @check_is_on
    def compute_meas_frame(self, idx: int = 0) -> None:
        """Send signals for computation of frame idx and gui update"""
        self.to_dataset.emit(DataEmitFrame4Computation(idx))
        self.to_gui.emit(EvtDataReplayFrameChanged(idx))

    ## =========================================================================
    ## Automatic replay
    ## =========================================================================

    def play_pause(self, *args, **kwargs) -> None:
        """Play/Pause the dataset replay"""
        if self.is_off:
            logger.warning("No Measurement loaded!, Please load measurements first!")
            glob_utils.dialog.Qt_dialogs.warningMsgBox(
                title="No Measurement loaded!",
                message="Please load measurements first!",
            )
            return
        elif self.is_idle:
            self.set_status(ReplayStatus.PLAYING)
        elif self.is_playing:
            self.set_status(ReplayStatus.LOADED)

    def begin(self, *args, **kwargs) -> None:
        """Back to first frame"""
        self._set_actual_frame(0)
        self.compute_actual_frame()

    def end(self, *args, **kwargs) -> None:
        """Goto last frame"""
        self._set_actual_frame(self.nb_frame_loaded - 1)
        self.compute_actual_frame()

    def next(self, *args, **kwargs) -> None:
        """Next frame"""
        self._inc_frame_idx(forward=True)
        self.compute_actual_frame()

    def back(self, *args, **kwargs) -> None:
        """Previous frame"""
        self._inc_frame_idx(forward=False)
        self.compute_actual_frame()

    def stop(self, *args, **kwargs) -> None:
        """Stop the automatic replay"""
        self.set_status(ReplayStatus.LOADED)

    ## =========================================================================
    ## Intenal methods
    ## =========================================================================

    def _inc_frame_idx(self, forward: bool = True):
        """Increment the frame index

        Args:
            forward (bool, optional): the increment direction
        """
        inc = {True: 1, False: -1}

        self.actual_frame_idx = self.actual_frame_idx + inc[forward]
        self.actual_frame_idx = self.actual_frame_idx % self.nb_frame_loaded

    def _set_actual_frame(self, idx: int) -> None:
        self.actual_frame_idx = idx
