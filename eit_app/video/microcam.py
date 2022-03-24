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


import time
from logging import getLogger
from typing import Any

import cv2
import numpy as np
from eit_app.video.device_abs import (CaptureDevices, CaptureFrameError,
                                      NoCaptureDeviceSelected)
from eit_app.video.capture import convert_frame_to_Qt_format
from PyQt5.QtGui import QImage

__author__ = "David Metz"
__copyright__ = "Copyright (c) 2021"
__credits__ = ["David Metz"]
__license__ = "GPLv3"
__version__ = "2.0.0"
__maintainer__ = "David Metz"
__email__ = "d.metz@tu-bs.de"
__status__ = "Production"

logger = getLogger(__name__)


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

    def connect_device(self, name: str=None) -> None:
        self.initializated.clear()
        if self.name not in self.devices_available:
            logger.error(f'Device "{self.name}" not available')
            logger.debug(f"Availabe devices:{self.devices_available}")
            raise NoCaptureDeviceSelected(f'Device "{self.name}" not available')

        self.device = cv2.VideoCapture(self.devices_available[self.name], cv2.CAP_DSHOW)
        self._check_device()
    
    def disconnect_device(self) -> None:
        self.device= None
        

    def get_devices_available(self) -> dict[str, Any]:
        
        self.devices_available={}
        for index, _ in enumerate(range(10)):
            cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
            if cap.read()[0]:
                self.devices_available[f"MicroUSB {index}"] = index
                cap.release()
        if self.devices_available:
            self.name=list(self.devices_available.keys())[0]
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
        if not self.is_connected():
            return None
        if not self.initializated.is_set():  # raise error if no device selected
            raise NoCaptureDeviceSelected()

        success, frame = self.device.read()
        if not success:  # raise error if reading of a frame not succesful
            raise CaptureFrameError()
        return frame

    def get_Qimage(self, frame: np.ndarray) -> QImage:
        return convert_frame_to_Qt_format(frame)

    def load_frame(self, file_path: str) -> np.ndarray:
        return cv2.imread(file_path, cv2.IMREAD_COLOR)

    def save_frame(self, frame: np.ndarray, file_path: str):
        cv2.imwrite(file_path, frame)


    def is_connected(self)->bool:
        if self.device is None:
            return False
        success, _ = self.device.read()
        return success

    def _check_device(self):
        """Check if the device works, here we read frame and verify that it is
        succesful
        """
        if self.is_connected:
            self.initializated.set()
        else:
            self.initializated.clear()


if __name__ == "__main__":
    """"""
    a = MicroUSBCamera()
