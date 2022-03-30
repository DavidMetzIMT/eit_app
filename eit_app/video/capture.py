import os
from enum import Enum
from logging import getLogger
from queue import Queue
from typing import Tuple

import numpy as np
from eit_app.com_channels import (
    AddToGuiSignal,
    DataSaveLoadImage,
    DataSetStatusWMeas,
    DataSetStatusWReplay,
    SignalReciever,
)
from eit_app.video.device_abs import CaptureDevices, handle_capture_device_error
from eit_app.update_gui import (
    CaptureStatus,
    EvtDataCaptureDevices,
    EvtDataCaptureImageChanged,
    EvtDataCaptureStatusChanged,
)
from glob_utils.files.files import is_file, append_extension
from glob_utils.flags.status import AddStatus
from glob_utils.msgbox import infoMsgBox
from glob_utils.pth.path_utils import get_datetime_s
from glob_utils.thread_process.threads_worker import Poller
from PyQt5.QtGui import QImage

logger = getLogger(__name__)

IMAGE_SIZES = {
    # '1600 x 1200':(1600,1200),
    # "1280 x 960": (1280, 960),
    # '800 x 600':(800,600),
    "640 x 480": (640, 480),
}

IMAGE_FILE_FORMAT = {
    "PNG": ".png",
    # "JPEG": ".jpg"
}


################################################################################
## Class Video Capture Module
################################################################################

class VideoCaptureAgent(SignalReciever, AddStatus, AddToGuiSignal):
    def __init__(self, capture_dev: CaptureDevices, snapshot_dir: str) -> None:
        """Handle a capture device 

        Args:
            capture_dev (CaptureDevices): capture device
            snapshot_dir (str): directory for snapshot saving
        """
        super().__init__()
        self.init_reciever(
            data_callbacks={
                DataSaveLoadImage: self.add_path,
                DataSetStatusWMeas: self.set_status_w_meas,
                DataSetStatusWReplay: self.set_status_w_replay,
            }
        )
        self.init_status(status_values=CaptureStatus)

        self._buffer_in = Queue()  # recieve path were the frame has to be saved
        self._worker = Poller(name="live_capture", pollfunc=self._poll, sleeptime=0.05)
        self._worker.start()
        self._worker.start_polling()

        self.capture_device = capture_dev
        self.snapshot_dir = snapshot_dir

        self.image_size = IMAGE_SIZES[list(IMAGE_SIZES.keys())[-1]]
        self.image_file_ext = IMAGE_FILE_FORMAT[list(IMAGE_FILE_FORMAT.keys())[0]]
        self.process = {
            CaptureStatus.NOT_CONNECTED: self._process_replay,
            CaptureStatus.CONNECTED: self._process_replay,
            CaptureStatus.REPLAY: self._process_replay,
            CaptureStatus.MEASURING: self._process_meas,
            CaptureStatus.LIVE: self._process_live,
        }

    def emit_new_Qtimage(self, frame: np.ndarray):
        """Send image to displaay in gui"""
        if frame is None:
            return
        image = self.capture_device.get_Qimage(frame)
        logger.debug("video image emitted")
        self.to_gui.emit(EvtDataCaptureImageChanged(image))

    # @abstractmethod - AddStatus
    def status_has_changed(self, status: Enum, was_status: Enum) -> None:
        self.to_gui.emit(EvtDataCaptureStatusChanged(status))
        logger.debug(f"Capture module mode set to : {status.value}")

    def set_status_w_meas(self, data: DataSetStatusWMeas):
        """Set internal mode depending on the measuring status of
        the acquisition device

        this method is called by a signal from the device at fro each status changes

        if meas_status_dev is `True` the capture_module is set to meas mode
        otherwise the capture_module is set back to live or to idle mode"""
        meas_status_dev = data.meas_status_dev
        if not isinstance(meas_status_dev, bool):
            return

        if self.is_status(CaptureStatus.NOT_CONNECTED):
            return

        if meas_status_dev:
            self.set_status(CaptureStatus.MEASURING)
        else:
            self.reset_to_last_status()

    def set_status_w_replay(self, data: DataSetStatusWReplay) -> None:
        """Set internal mode depending on the replay status

        this method is called by a signal from the replay at each status changes

        if replay_status is `True` the capture_module is set to idle mode"""
        replay_status = data.replay_status
        if not isinstance(replay_status, bool):
            return

        if replay_status:
            self.set_status(CaptureStatus.REPLAY)
        else:
            self.reset_to_last_status()

    def add_path(self, data: DataSaveLoadImage, **kwargs) -> None:
        self._buffer_in.put(data.frame_path)
        logger.info(f"Capture frame path added: {data.frame_path}")

    def get_devices(self) -> None:
        """Return a list of the name of the availbale devices

        Returns:
            list[str]: names of the available devices
        """
        devices = self.capture_device.get_devices_available()
        logger.info(f"Capture devices available: {list(devices)}")
        self.to_gui.emit(EvtDataCaptureDevices(devices))

    def set_device_name(self, name: str, **kwargs) -> None:
        self.capture_device.set_name(name)

    @handle_capture_device_error
    def connect_device(self, name: str = None, **kwargs) -> None:
        """Select a device

        Args:
            name (str): name of the device, which has to be in the self.devices
        """
        if self.capture_device.is_connected():
            self.capture_device.disconnect_device()
            self.set_status(CaptureStatus.NOT_CONNECTED)
            logger.info(
                f"Video capture device: {self.capture_device._name} - DISCONNECTED"
            )
        else:
            self.capture_device.connect_device()
            self.set_status(CaptureStatus.CONNECTED)
            logger.info(f"Video capture device: {self.capture_device._name} - CONNECTED")

    @handle_capture_device_error
    def set_image_size(self, size: str, **kwargs) -> None:
        """Set the captured image size

        Args:
            size (str): key from IMG_SIZES={
                                    '1600 x 1200':(1600,1200),
                                    '1280 x 960':(1280,960),
                                    '800 x 600':(800,600),
                                    '640 x 480':(640,480)
                                }
        """
        if size not in IMAGE_SIZES:
            logger.error(f"Wrong image size : {size}")
            return
        self.image_size = IMAGE_SIZES[size]
        self.capture_device.set_settings(size=self.image_size)

    def set_image_file_format(self, file_ext: str=list(IMAGE_FILE_FORMAT.keys())[0], **kwargs) -> None:
        """Set the file format for image saving

        Args:
            file_ext ([type], optional): file extension.
            Defaults to list(EXT_IMG.keys())[0].
        """
        self.image_file_ext = IMAGE_FILE_FORMAT[file_ext]
        logger.debug(f"image_file_ext selected {self.image_file_ext}")

    def start_stop(self, *args, **kwargs) -> None:
        """Start or Stop Live Capture,
        toggle between both modis IDLE and LIVE
        if MEASURING mode active nothing will be done!
        """
        if self.is_status(CaptureStatus.MEASURING):
            infoMsgBox(
                title="Measurements are running", message="Stop first Measurements"
            )
            return

        if self.is_status(CaptureStatus.NOT_CONNECTED):
            infoMsgBox(
                title="No Capture device connected",
                message="Connect first a capture device!",
            )
            logger.info("No Capture device connected - Connect first capture device!")
            return

        if self.is_status(CaptureStatus.CONNECTED):
            self.set_status(CaptureStatus.LIVE)
        else:
            self.set_status(CaptureStatus.CONNECTED)

    def _poll(self) -> None:
        """Call the process corresponding to the actual status"""
        self.process[self.get_status()]()

    def _process_idle(self) -> None:
        """Idle process: nop"""

    def _process_replay(self) -> None:
        """Replay process:
        - retrieve path in the input buffer
        - load the correspoding image
        - send the image for display
        """
        if self._buffer_in.empty():
            return
        path = self._buffer_in.get()
        logger.info("replay loading image")
        frame = self.load_image(path)
        self.emit_new_Qtimage(frame)

    def _process_meas(self) -> None:
        """Measuring process:
        - retrieve path in the input buffer
        - take an image (and send the image for display)
        - save the image
        """
        if self._buffer_in.empty():
            return
        path = self._buffer_in.get()
        frame = self._shoot_image()
        self.save_image(frame, path)

    def _process_live(self) -> None:
        """Live process:
        - take an image
        - send the image for display
        """
        self._shoot_image()

    def build_snapshot_path(self) -> str:
        """Create a generic snapshot path"""
        return os.path.join(self.snapshot_dir, f"Snapshot_{get_datetime_s()}")

    def take_snapshot(self, *args, **kwargs) -> None:
        """Take a single snapshot
        - build a generic snapshot path
        - take an image (and send the image for display)
        - save the image
        """
        path = self.build_snapshot_path()
        frame = self._shoot_image()
        self.save_image(frame, path)


    @handle_capture_device_error
    def _shoot_image(self) -> np.ndarray:
        """Shoot an image and send the image for display

        Returns:
            np.ndarray: captured image frame
        """
        frame= self.capture_device.capture_frame()
        self.emit_new_Qtimage(frame)
        return frame

    def load_image(self, path: str = None) -> np.ndarray:
        """Load an image frame

        Args:
            path (str, optional): file path. Defaults to None.

        Returns:
            np.ndarray: loaded image frame
        """
        if path is None:
            return None, None

        filepath = None
        for ext in list(IMAGE_FILE_FORMAT.values()):
            filepath = append_extension(path, ext)
            if is_file(filepath):
                break
        if filepath is None:
            return None, None
        frame = self.capture_device.load_frame(filepath)
        logger.debug(f'\nImage "{path}" - Loaded')
        return frame

    def save_image(self, frame: np.ndarray, path: str):
        """Save an image frame 

        Args:
            frame (np.ndarray): image frame to save
            path (str, optional): file path. Defaults to None.
        """
        if path is None or frame is None:
            return
        logger.debug(f"Image saved in {path}")
        path = append_extension(path, self.image_file_ext)
        self.capture_device.save_frame(frame, path)
    
    def used_img_exts(self)->list[str]:
        return list(IMAGE_FILE_FORMAT.keys())

    def used_img_sizes(self)->list[str]:
        return list(IMAGE_SIZES.keys())


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
