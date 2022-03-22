#!C:\Anaconda3\envs\py38_app python
# -*- coding: utf-8 -*-

"""  
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

import os
import time
from abc import ABC, abstractmethod
from enum import Enum, auto
from logging import getLogger
from queue import Queue
from typing import Any

import cv2
from glob_utils.files.files import is_file
from glob_utils.pth.path_utils import get_datetime_s
import numpy as np
from glob_utils.thread_process.signal import Signal
from glob_utils.thread_process.threads_worker import Poller
from glob_utils.flags.flag import CustomFlag, MultiStatewSignal
from glob_utils.msgbox import askokcancelMsgBox, infoMsgBox, errorMsgBox

from PyQt5.QtGui import QImage

from eit_app.update_gui import CaptureDevAvailables, CaptureMode, CaptureStatus, ObjWithSignalToGui

__author__ = "David Metz"
__copyright__ = "Copyright (c) 2021"
__credits__ = ["David Metz"]
__license__ = "GPLv3"
__version__ = "2.0.0"
__maintainer__ = "David Metz"
__email__ = "d.metz@tu-bs.de"
__status__ = "Production"

logger = getLogger(__name__)

IMG_SIZES = {
    # '1600 x 1200':(1600,1200),
    "1280 x 960": (1280, 960),
    # '800 x 600':(800,600),
    "640 x 480": (640, 480),
}
EXT_IMG = {"PNG": ".png", "JPEG": ".jpg"}

SNAPSHOT_DIR = "snapshots"


################################################################################
## Class Capture Devices
################################################################################
class NoCaptureDeviceSelected(Exception):
    """"""


class CaptureFrameError(Exception):
    """"""


class CaptureDevices(ABC):

    devices_available: dict[str, Any]
    device: Any
    initializated: CustomFlag
    settings: dict

    def __init__(self) -> None:
        super().__init__()
        self.devices_available = {}
        self.device = None
        self.initializated = CustomFlag()
        self.settings = {}
        self._post_init_()

    def _error_if_no_device(func):
        '''Decorator '''
    
        def wrap(self, *args, **kwargs):
            if not self.initializated.is_set():  # raise error if no device selected
                raise NoCaptureDeviceSelected()
            func(self, *args, **kwargs)
        return wrap

    @abstractmethod
    def _post_init_(self) -> None:
        """Post init for specific object initialisation process"""

    @abstractmethod
    def connect_device(self, name: str) -> None:
        """Connect the device corresponding to the name given as arg

        Raises:
            NoCaptureDeviceSelected: if no devices has been selected

        Args:
            name (str): name of the device (one of the key returned by
            self.get_devices_available)
        """

    @abstractmethod
    def get_devices_available(self) -> dict[str, Any]:
        """Create and return a dictionary of availables devices:

        self.devices_available= {'name1 ': specific data to device 1, ...}

        Returns:
            dict: dictionary of availables devices
        """

    @abstractmethod
    def set_settings(self, **kwargs) -> None:
        """Set devices settings such as size of frame, etc.

        Note: should call self.get_setting() at the end

        Raises:
            NoCaptureDeviceSelected: if no devices has been selected

        Args:
            use kwargs to be flexible...
        """

    @abstractmethod
    def get_settings(self) -> dict[str, Any]:
        """Read actual setting of the connected capture device

        - update self.settings= {'property1':val_prop1, ...}
        - logging of setting (debug)

        Raises:
            NoCaptureDeviceSelected: if no devices has been selected

        Returns:
            dict[str,Any]: settings dictionnary
        """

    @abstractmethod
    def capture_frame(self) -> np.ndarray:
        """Capture a frame on connected device and return it as an ndarray

        Raises:
            NoCaptureDeviceSelected: if no devices has been selected
            CaptureFrameError: if an error occur during capture

        Returns:
            np.ndarray: captured array
        """

    @abstractmethod
    def get_Qimage(self, frame: np.ndarray) -> QImage:
        """Convert a frame (ndarray) in a Qt Image format object

        Args:
            frame (np.ndarray): frame to convert

        Returns:
            QImage: Qt Image
        """

    @abstractmethod
    def load_frame(self, file_path: str) -> np.ndarray:  #
        """Load a frame (ndarray) contained in a file

        Args:
            file_path (str): path of the file to load

        Returns:
            np.ndarray: loaded frame
        """

    @abstractmethod
    def save_frame(self, frame: np.ndarray, file_path: str) -> None:
        """Save passed frame (ndarray) in file_path

        Args:
            frame (np.ndarray): [description]
            path (str): [description]
        """


class MicroUSBCamera(CaptureDevices):
    """Class"""

    def _post_init_(self) -> None:
        self.props = {
            "Frame_width": cv2.CAP_PROP_FRAME_WIDTH,
            "Frame_height": cv2.CAP_PROP_FRAME_HEIGHT,
            # cv2.CAP_PROP_FPS, cv2.CAP_PROP_POS_MSEC,
            # Fcv2.CAP_PROP_FRAME_COUNT, cv2.CAP_PROP_BRIGHTNESS,
            # cv2.CAP_PROP_CONTRAST, cv2.CAP_PROP_SATURATION,
            # cv2.CAP_PROP_HUE, cv2.CAP_PROP_GAIN,
            # cv2.CAP_PROP_CONVERT_RGB
        }
        self.settings = {k: None for k in self.props}

    def connect_device(self, name: str) -> None:
        self.initializated.clear()
        if name not in self.devices_available:
            logger.error(f'Device "{name}" not available')
            logger.debug(f"Availabe devices:{self.devices_available}")
            raise NoCaptureDeviceSelected(f'Device "{name}" not available')

        self.devices_available[name]
        self.device = cv2.VideoCapture(self.devices_available[name], cv2.CAP_DSHOW)
        self._check_device()
        

    def get_devices_available(self) -> dict[str, Any]:
        for index, _ in enumerate(range(10)):
            cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
            if cap.read()[0]:
                self.devices_available[f"MicroUSB {index}"] = index
                cap.release()
        return self.devices_available


    def set_settings(self, **kwargs) -> None:
        if not self.initializated.is_set():  # raise error if no device selected
            raise NoCaptureDeviceSelected()
        # set size of the frame
        size = kwargs["size"] if "size" in kwargs else None
        if size is None:
            return
        self.device.set(cv2.CAP_PROP_FRAME_WIDTH, size[0])
        self.device.set(cv2.CAP_PROP_FRAME_HEIGHT, size[1])
        # not Used
        # self.device.set(cv2.CAP_PROP_AUTO_WB, 0)
        # self.device.set(cv2.CAP_PROP_EXPOSURE, 0)
        # self.device.set(cv2.CAP_PROP_GAIN , 0)
        # self.device.set(cv2.CAP_PROP_SATURATION , 0)
        # self.device.set(cv2.CAP_PROP_CONTRAST, 0)
        # self.device.set(cv2.CAP_PROP_BRIGHTNESS, -1)
        # self.device.set(cv2.CAP_PROP_HUE,hue)
        # self.device.set(cv2.CAP_PROP_CONVERT_RGB , 1)
        time.sleep(2)
        self._check_device()
        self.get_settings()

    def get_settings(self) -> dict[str, Any]:
        if not self.initializated.is_set():  # raise error if no device selected
            raise NoCaptureDeviceSelected()

        self.settings = {k: self.device.get(v) for k, v in self.props.items()}
        [logger.info(f"{k}: {v}") for k, v in self.settings.items()]
        return self.settings

    def capture_frame(self) -> np.ndarray:
        if not self.initializated.is_set():  # raise error if no device selected
            raise NoCaptureDeviceSelected()

        succeed, frame = self.device.read()
        if not succeed:  # raise error if reading of a frame not succesful
            raise CaptureFrameError()
        return frame

    def get_Qimage(self, frame: np.ndarray) -> QImage:
        return convert_frame_to_Qt_format(frame)

    def load_frame(self, file_path: str) -> np.ndarray:
        return cv2.imread(file_path, cv2.IMREAD_COLOR)

    def save_frame(self, frame: np.ndarray, file_path: str):
        cv2.imwrite(file_path, frame)

    def _check_device(self):
        """Check if the device works, here we read frame and verify that it is
        succesful
        """
        succeed, _ = self.device.read()
        if succeed:
            self.initializated.set()
        else:
            self.initializated.clear()


################################################################################
## Class Video Capture Module
################################################################################


def handle_capture_device_error(func):
    """Decorator which handle the errors from CaptureDevices in
    Video Capture Modules
    """
    def wrapper(self, *args, **kwargs) -> Any:
        try:
            return func(self, *args, **kwargs)
        except NoCaptureDeviceSelected as e:
            logger.warning(f"No Capture Device Selected; ({e})")
            errorMsgBox(
                title="No Capture Device Selected",
                message=f"{e}"
            )
        except CaptureFrameError as e:
            logger.error(f"Capture frame failed; ({e})")
            errorMsgBox(
                title="Capture frame failed",
                message=f"{e}"
            )
    return wrapper


class VideoCaptureAgent(ObjWithSignalToGui):
    """Handle a capture device and can provide
    a live, a measuring and an idle mode using a worker thread
    """

    def __init__(self, capture_type: CaptureDevices , snapshot_dir:str) -> None:

        super().__init__()
        self.queue_in = Queue()  # recieve path were the frame has to be saved
        self.worker = Poller(name="live_capture", pollfunc=self._poll, sleeptime=0.05)
        self.worker.start()
        self.worker.start_polling()
        self.mode = MultiStatewSignal(list(CaptureMode))
        self.mode.reset(CaptureMode.IDLE)
        # self.live_capture = CustomFlag()
        self.capture_device = capture_type
        self.snapshot_dir= snapshot_dir
        self.aquisition_device_is_measuring= CustomFlag()
        self.was_mode = CaptureMode.IDLE

        self.image_size = IMG_SIZES[list(IMG_SIZES.keys())[-1]]
        self.image_file_ext = EXT_IMG[list(EXT_IMG.keys())[0]]
        self.save_image_path = ""
        self.last_frame = None
        self.process = {
            CaptureMode.IDLE: self._process_idle,
            CaptureMode.MEASURING: self._process_meas,
            CaptureMode.LIVE: self._process_live,
        }
        self.new_image=Signal(self)

        self.mode.changed.connect(self.mode_changed) 
    
    def emit_new_image(self,image:QImage):
        logger.debug("video image emitted")
        kwargs={"image":image}
        self.new_image.fire(False, **kwargs)

    def mode_changed(self):
        """Update the was life flag, called by status changed signal"""
        self.was_mode = self.mode.was_set()
        mode_now:CaptureMode = self.mode.actual_state()
        self.emit_to_gui(CaptureStatus(mode_now))
        logger.debug(f"Capture module mode set to : {mode_now.value}")
    
    def set_mode(self, meas_status_dev:bool ,**kwargs):
        """Set internal mode depending on the measuring status of 
        the acquisition device 

        this method is called by a signal from the device at fro each status changes

        if meas_status_dev is `True` the capture_module is set to meas mode
        otherwise the capture_module is set back to live or to idle mode"""
        if not isinstance(meas_status_dev, bool):
            return

        if self.aquisition_device_is_measuring.is_set():
            self.mode.change_state(CaptureMode.MEASURING) 
        else:
            self.mode.change_state(self.was_mode)

    def add_path(self, frame_path:str='None',**kwargs):

        if not isinstance(frame_path, str):
            logger.error(f'wrong type of data, type str expected: {frame_path=}')
            return
        if frame_path=='None':
            return
        self.queue_in.put(frame_path)


    def get_devices_available(self)-> None:
        """Return a list of the name of the availbale devices

        Returns:
            list[str]: names of the available devices
        """
        devices = self.capture_device.get_devices_available()
        logger.info(f"Capture devices available: {list(devices)}")
        self.emit_to_gui(CaptureDevAvailables(devices))

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
        if self.mode.is_set(CaptureMode.MEASURING):
            return
        
        if self.mode.is_set(CaptureMode.IDLE):
            self.mode.change_state(CaptureMode.LIVE)
        else:
            self.mode.change_state(CaptureMode.IDLE)

    def capture_stop(self, *args, **kwargs) -> None:
        """Force the capture module to stop capturing,
        """
        if self.mode.is_set(CaptureMode.MEASURING):
            infoMsgBox(
                title="Measurements are running",
                message="Stop first Measurements"
            )
        
        self.mode.change_state(CaptureMode.IDLE)

    def _poll(self) -> None:
        """Call the process corresponding to the actual status"""
        self.process[self.mode.actual_state()]()

    def _process_idle(self) -> None:
        """Idle process"""

    def _process_meas(self) -> None:
        """Measuring process

        Wait on queue_in for a path where actual frame has to be saved.
        and emit the actual image in queue out (eg. for display on GUI)
        """
        if self.queue_in.empty():
            return
        path = self.queue_in.get()
        image = self._snapshot(path)
        self.emit_new_image(image)

    def _process_live(self) -> None:
        """Live process: Read and emit the actual image (eg. for display on GUI)
        """
        image = self._snapshot()
        self.emit_new_image(image)


    def build_snapshot_path(self)->str:
        return os.path.join(self.snapshot_dir, f"Snapshot_{get_datetime_s()}")

    def snapshot(self, *args, **kwargs) -> QImage:
        path= self.build_snapshot_path()
        return self._snapshot(path)

    @handle_capture_device_error
    def _snapshot(self, path: str = None) -> QImage:
        """Make a snapshot and return a Qt image

        Args:
            path (str, optional): If path is not `None`, the captured
            frame(ndarray) is saved at this path. Defaults to `None`.

        Returns:
            QImage: captured Qt image
        """

        frame = self.capture_device.capture_frame()
        QtImage = self.capture_device.get_Qimage(frame)
        if path and isinstance(path, str):
            path, _ = os.path.splitext(path)
            path = path + self.image_file_ext
            self.capture_device.save_frame(frame, path)
            logger.debug(f"Image saved in {path}")
        return QtImage

    def load_image(self, path: str = None):
        """Load an image out of an file in which a frame (ndarray) has been
        saved

        Args:
            path (str, optional): . Defaults to None.
        """
        if path is None:
            return self._snapshot()  # capture actual frame

        _, ext = os.path.split(path)
        if ext not in list(EXT_IMG.values()) and not is_file(path):
            return None
        frame = self.capture_device.load_frame(path)
        image = self.capture_device.get_Qimage(frame)
        logger.debug(f'\nImage "{path}" - Loaded')
        self.emit_new_image(image)


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

    print(list(EXT_IMG.values()))
    a = MicroUSBCamera()
