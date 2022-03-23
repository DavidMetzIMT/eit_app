from enum import Enum
from logging import getLogger
from typing import Any, Union

from eit_app.io.sciospec.measurement import DataEmitFrame4Computation
from eit_app.io.video.capture import DataSetStatusWReplay
from eit_app.com_channels import (AddToCaptureSignal, AddToDatasetSignal,
                                    AddToGuiSignal, DataReplayStart,
                                    SignalReciever)
from eit_app.update_gui import EvtDataReplayFrameChanged, EvtDataReplayStatusChanged, ReplayStatus
from glob_utils.flags.status import AddStatus
from glob_utils.msgbox import warningMsgBox
from PyQt5 import QtCore

logger = getLogger(__name__)


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
                warningMsgBox(
                    title='No Measurement loaded!',
                    message='Please load measurements first!'
                )
                return None

            return func(self, *args, **kwargs) 
            
        return wrap


class ReplayMeasurementsAgent(
    SignalReciever,
    AddStatus, 
    AddToGuiSignal,
    AddToDatasetSignal,
    AddToCaptureSignal
):

    timerqt: QtCore.QTimer

    def __init__(self) -> None:
        super().__init__()
        self.init_reciever(
            data_callbacks={DataReplayStart:self.start}
        )
        self.init_status(status_values=ReplayStatus)
        self.nb_frame_loaded=0
        self.actual_frame_idx=0

        self.timerqt=QtCore.QTimer()
        self.timerqt.timeout.connect(self.next)

    def activate_timer(self)->None:
        """Update the was life flag, called by status changed signal"""
        if self.is_idle:
            self.timerqt.stop()
        elif self.is_playing:
            self.timerqt.start()

    # @abstractmethod - AddStatus
    def status_has_changed(self, status:Enum, was_status:Enum)->None:
        """Update the was life flag, called by status changed signal"""
        self.activate_timer()
        self.to_gui.emit(EvtDataReplayStatusChanged(status))
        replay_status= self.is_idle or self.is_playing
        self.to_capture.emit(DataSetStatusWReplay(replay_status))
        logger.debug(f"ReplayMeasurements Status set to : {status.value}")

    @property
    def is_idle(self)->bool:
        return self.is_status(ReplayStatus.IDLE)
    
    @property
    def is_playing(self)->bool:
        return self.is_status(ReplayStatus.PLAYING)

    @property
    def is_off(self)->bool:
        return self.is_status(ReplayStatus.OFF)


    def set_mode(self, meas_status_dev:bool ,**kwargs):
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
    ##  
    ## =========================================================================    

    
    @check_is_on
    def compute_meas_frame(self, idx:int=0)->None:
        self.to_dataset.emit(DataEmitFrame4Computation(idx))
        self.to_gui.emit(EvtDataReplayFrameChanged(idx))
    
    def compute_actual_frame(self,*args, **kwargs):
        self.compute_meas_frame(self.actual_frame_idx)
   
    def start(self, data:DataReplayStart, **kwargs)-> None:
        self.set_nb_frame_loaded(data.nb_frame)
        self.begin()

    def set_nb_frame_loaded(self, nb_frame:int):
        self.nb_frame_loaded= nb_frame

    def play(self) -> None:
        if self.is_off:
            warningMsgBox(
                title='No Measurement loaded!',
                message='Please load measurements first!'
            )
            return
        elif self.is_idle:
            self.set_status(ReplayStatus.PLAYING)
        elif self.is_playing:
            self.set_status(ReplayStatus.IDLE)

    
    def begin(self) -> None:
        self.set_actual_frame(0)
        self.compute_actual_frame()


    def end(self) -> None:
        self.set_actual_frame(self.nb_frame_loaded-1)
        self.compute_actual_frame()

    def next(self) -> None:
        self._inc_position(forward=True)
        self.compute_actual_frame()

    def back(self) -> None:
        self._inc_position(forward=False)
        self.compute_actual_frame()

    def _inc_position(self, forward:bool=True):
        """Increment the position of the cursor

        Args:
            slider (QSlider): slider object to set
            set_pos (int, optional): position. Defaults to `0`. 
            If set to `-1` the slider will be set to the end
        """
        inc= {True:1, False:-1}

        self.actual_frame_idx= self.actual_frame_idx + inc[forward]
        self.actual_frame_idx = self.actual_frame_idx % self.nb_frame_loaded

    def stop(self) -> None:
        """[summary]"""
        self.set_status(ReplayStatus.IDLE)

    def set_actual_frame(self, idx:int, **kwargs) -> None:
        self.actual_frame_idx= idx

    def set_timeout(self, sec:float, *args,**kwargs) -> None:
        msec=int(sec*1000)
        logger.info(f"new Timeout in msec:{msec}")
        self.timerqt.setInterval(msec)

