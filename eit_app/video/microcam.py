import sys
import time
import logging
from typing import Any, Tuple

import cv2
import numpy as np
from eit_app.video.device_abs import (
    CaptureDevices,
    CaptureFrameError,
    NoCaptureDeviceSelected,
)
from eit_app.video.capture import convert_frame_to_Qt_format
from PyQt5.QtGui import QImage


logger = logging.getLogger(__name__)


class MicroUSBCamera(CaptureDevices):
    """Capture device for USB Micro Cameras based on OpenCV library"""

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
        self._settings = {k: None for k in self.props}

    def connect_device(self) -> None:
        self._initializated.clear()
        if self._name not in self._devices_available:
            logger.error(f'Device "{self._name}" not available')
            logger.debug(f"Availabe devices:{self._devices_available}")
            raise NoCaptureDeviceSelected(f'Device "{self._name}" not available')

        self._device = self._connect_to_device(self._devices_available[self._name])
        self._check_device()

    def _connect_to_device(self, index: int):
        # MAC OS do not need option CAP_SHOW
        return (
            cv2.VideoCapture(index)
            if sys.platform.startswith("darwin")
            else cv2.VideoCapture(index, cv2.CAP_DSHOW)
        )

    def disconnect_device(self) -> None:
        self._device = None

    def get_devices_available(self) -> dict[str, Any]:
        self._devices_available = {}
        for index, _ in enumerate(range(10)):

            cap = self._connect_to_device(index)
            # cap = cv2.VideoCapture(index)
            if cap.read()[0]:
                self._devices_available[f"MicroUSB {index}"] = index
                cap.release()
        if self._devices_available:
            self._name = list(self._devices_available.keys())[0]
        return self._devices_available

    def set_settings(self, **kwargs) -> None:
        if not self._initializated.is_set():  # raise error if no device selected
            raise NoCaptureDeviceSelected()
        # set size of the frame
        size = kwargs["size"] if "size" in kwargs else None
        if size is None:
            return
        self._device.set(cv2.CAP_PROP_FRAME_WIDTH, size[0])
        self._device.set(cv2.CAP_PROP_FRAME_HEIGHT, size[1])
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
        if not self._initializated.is_set():  # raise error if no device selected
            raise NoCaptureDeviceSelected()
        self._settings = {k: self._device.get(v) for k, v in self.props.items()}
        [logger.info(f"{k}: {v}") for k, v in self._settings.items()]
        return self._settings

    def capture_frame(self) -> Tuple[np.ndarray, None]:
        if not self.is_connected():
            return None
        if not self._initializated.is_set():  # raise error if no device selected
            raise NoCaptureDeviceSelected()
        success, frame = self._device.read()
        if not success:  # raise error if reading of a frame not succesful
            raise CaptureFrameError()
        return frame

    def get_Qimage(self, frame: np.ndarray) -> QImage:
        return convert_frame_to_Qt_format(frame)

    def load_frame(self, file_path: str) -> np.ndarray:
        return cv2.imread(file_path, cv2.IMREAD_COLOR)

    def save_frame(self, frame: np.ndarray, file_path: str):
        cv2.imwrite(file_path, frame)

    def is_connected(self) -> bool:
        if self._device is None:
            return False
        success, _ = self._device.read()
        return success

    def _check_device(self) -> None:
        """Check if the device works, here we read frame and verify that it is
        succesful
        """
        self._initializated.set(val=self.is_connected)


if __name__ == "__main__":
    """"""
    a = MicroUSBCamera()
