import os
from enum import Enum
from logging import getLogger
from queue import Queue
from typing import Tuple

import numpy as np
from eit_app.com_channels import (AddToGuiSignal, DataSaveLoadImage,
                                  DataSetStatusWMeas, DataSetStatusWReplay,
                                  SignalReciever)
from eit_app.io.video.device_abs import (CaptureDevices,
                                         handle_capture_device_error)
from eit_app.update_gui import (CaptureStatus, EvtDataCaptureDevices,
                                EvtDataCaptureStatusChanged)
from glob_utils.files.files import is_file, append_extension
from glob_utils.flags.status import AddStatus
from glob_utils.msgbox import infoMsgBox
from glob_utils.pth.path_utils import get_datetime_s
from glob_utils.thread_process.signal import Signal
from glob_utils.thread_process.threads_worker import Poller
from PyQt5.QtGui import QImage

logger = getLogger(__name__)

IMG_SIZES = {
    # '1600 x 1200':(1600,1200),
    "1280 x 960": (1280, 960),
    # '800 x 600':(800,600),
    "640 x 480": (640, 480),
}
EXT_IMG = {"PNG": ".png", "JPEG": ".jpg"}


################################################################################
## Class Video Capture Module
################################################################################

class VideoCaptureAgent(SignalReciever, AddStatus, AddToGuiSignal):
    """Handle a capture device and can provide
    a live, a measuring and an idle mode using a worker thread
    """

    def __init__(self, capture_type: CaptureDevices , snapshot_dir:str) -> None:

        super().__init__()
        self.init_reciever(
            data_callbacks={
                DataSaveLoadImage: self.add_path,
                DataSetStatusWMeas:self.set_status_w_meas,
                DataSetStatusWReplay:self.set_status_w_replay
            }
        )
        self.init_status(status_values=CaptureStatus)

        self.queue_in = Queue()  # recieve path were the frame has to be saved
        self.worker = Poller(name="live_capture", pollfunc=self._poll, sleeptime=0.05)
        self.worker.start()
        self.worker.start_polling()

        self.capture_device = capture_type
        self.snapshot_dir= snapshot_dir

        self.image_size = IMG_SIZES[list(IMG_SIZES.keys())[-1]]
        self.image_file_ext = EXT_IMG[list(EXT_IMG.keys())[0]]
        self.save_image_path = ""
        self.last_frame = None
        self.process = {
            CaptureStatus.IDLE: self._process_idle,
            CaptureStatus.MEASURING: self._process_meas,
            CaptureStatus.LIVE: self._process_live,
        }
        self.new_image=Signal(self)

    
    def emit_new_image(self,image:QImage):
        # logger.debug("video image emitted")
        kwargs={"image":image}
        self.new_image.emit(**kwargs)

    # @abstractmethod - AddStatus
    def status_has_changed(self, status:Enum, was_status:Enum)->None:
        self.to_gui.emit(EvtDataCaptureStatusChanged(status))
        logger.debug(f"Capture module mode set to : {status.value}")

    def set_status_w_meas(self, data:DataSetStatusWMeas):
        """Set internal mode depending on the measuring status of 
        the acquisition device 

        this method is called by a signal from the device at fro each status changes

        if meas_status_dev is `True` the capture_module is set to meas mode
        otherwise the capture_module is set back to live or to idle mode"""
        meas_status_dev= data.meas_status_dev
        if not isinstance(meas_status_dev, bool):
            return

        if meas_status_dev:
            self.set_status(CaptureStatus.MEASURING) 
        else:
            self.reset_to_last_status()
    
    def set_status_w_replay(self, data:DataSetStatusWReplay)-> None:
        """Set internal mode depending on the replay status

        this method is called by a signal from the replay at each status changes

        if replay_status is `True` the capture_module is set to idle mode"""
        replay_status= data.replay_status
        if not isinstance(replay_status, bool):
            return

        if replay_status:
            self.set_status(CaptureStatus.IDLE) 

    def add_path(self, data:DataSaveLoadImage,**kwargs)-> None:
        self.queue_in.put(data.frame_path)


    def get_devices_available(self)-> None:
        """Return a list of the name of the availbale devices

        Returns:
            list[str]: names of the available devices
        """
        devices = self.capture_device.get_devices_available()
        logger.info(f"Capture devices available: {list(devices)}")
        self.to_gui.emit(EvtDataCaptureDevices(devices))

    @handle_capture_device_error
    def connect_device(self, name: str) -> None:
        """Select a device

        Args:
            name (str): name of the device, which has to be in the self.devices
        """
        self.capture_device.connect_device(name)
        logger.info(f"Video capture device: {name} - CONNECTED")
        

    @handle_capture_device_error
    def set_image_size(self, size: str) -> None:
        """Set the captured image size

        Args:
            size (str): key from IMG_SIZES={
                                    '1600 x 1200':(1600,1200),
                                    '1280 x 960':(1280,960),
                                    '800 x 600':(800,600),
                                    '640 x 480':(640,480)
                                }
        """
        if size not in IMG_SIZES:
            logger.error(f"Wrong image size : {size}")
            return
        self.image_size = IMG_SIZES[size]
        self.capture_device.set_settings(size=self.image_size)

    def set_image_file_format(self, file_ext=list(EXT_IMG.keys())[0]) -> None:
        """Set the file format for image saving

        Args:
            file_ext ([type], optional): file extension.
            Defaults to list(EXT_IMG.keys())[0].
        """
        self.image_file_ext = EXT_IMG[file_ext]
        logger.debug(f"image_file_ext selected {self.image_file_ext}")

    def start_stop_capture(self, *args, **kwargs) -> None:
        """Start or Stop Live Capture,
        toggle between both modis IDLE and LIVE
        if MEASURING mode active nothing will be done!
        """
        if self.is_status(CaptureStatus.MEASURING):
            return
        
        if self.is_status(CaptureStatus.IDLE):
            self.set_status(CaptureStatus.LIVE)
        else:
            self.set_status(CaptureStatus.IDLE)

    def capture_stop(self, *args, **kwargs) -> None:
        """Force the capture module to stop capturing,
        """
        if self.is_status(CaptureStatus.MEASURING):
            infoMsgBox(
                title="Measurements are running",
                message="Stop first Measurements"
            )
        
        self.set_status(CaptureStatus.IDLE)

    def _poll(self) -> None:
        """Call the process corresponding to the actual status"""
        self.process[self.get_status()]()

    def _process_idle(self) -> None:
        """Idle process"""
        if self.queue_in.empty():
            return
        path = self.queue_in.get()
        image, frame = self.load_image(path)
        self.emit_new_image(image)

    def _process_meas(self) -> None:
        """Measuring process

        Wait on queue_in for a path where actual frame has to be saved.
        and emit the actual image in queue out (eg. for display on GUI)
        """
        if self.queue_in.empty():
            return
        path = self.queue_in.get()
        image, frame = self._snapshot()
        self.save_image(frame, path)
        self.emit_new_image(image)

    def _process_live(self) -> None:
        """Live process: Read and emit the actual image (eg. for display on GUI)
        """
        image, frame = self._snapshot()
        self.emit_new_image(image)

    def build_snapshot_path(self)->str:
        return os.path.join(self.snapshot_dir, f"Snapshot_{get_datetime_s()}")
        

    def snapshot(self, *args, **kwargs) -> None:
        image, frame = self._snapshot()
        path= self.build_snapshot_path()
        self.save_image(frame, path)
        self.emit_new_image(image)

    @handle_capture_device_error
    def _snapshot(self, path: str = None) -> Tuple[QImage, np.ndarray]:
        """Make a snapshot and return a Qt image

        Args:
            path (str, optional): If path is not `None`, the captured
            frame(ndarray) is saved at this path. Defaults to `None`.

        Returns:
            QImage: captured Qt image
        """

        frame = self.capture_device.capture_frame()
        image = self.capture_device.get_Qimage(frame)
        return image, frame

    def load_image(self, path: str = None)-> Tuple[QImage, np.ndarray]:
        """Load an image out of an file in which a frame (ndarray) has been
        saved

        Args:
            path (str, optional): . Defaults to None.
        """
        if path is None:
            return

        _, ext = os.path.split(path)
        if ext not in list(EXT_IMG.values()) and not is_file(path):
            return None
        frame = self.capture_device.load_frame(path)
        image = self.capture_device.get_Qimage(frame)
        logger.debug(f'\nImage "{path}" - Loaded')
        return image, frame

    def save_image(self, frame:np.ndarray, path:str):
        if path is None:
            return
        
        logger.debug(f"Image saved in {path}")
        path= append_extension(path, self.image_file_ext)
        self.capture_device.save_frame(frame, path)
        


def convert_frame_to_Qt_format(frame: np.ndarray) -> QImage:
    """Convert a frame (ndarray) to a Qt formatted image

     Raises:
        TypeError: if frame is not an ndarray

    Args:
        frame (np.ndarray): frame to convert

    Returns:
        QImage: corresponding Qt image
    """
    if not isinstance(frame, np.ndarray):
        raise TypeError(f"{frame=} should be an ndarray")

    return QImage(
        frame.data, frame.shape[1], frame.shape[0], QImage.Format_RGB888
    ).rgbSwapped()


if __name__ == "__main__":
    """"""
