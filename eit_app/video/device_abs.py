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


from abc import ABC, abstractmethod
import logging
from typing import Any, Tuple
import numpy as np
from glob_utils.flags.flag import CustomFlag
import PyQt5.QtGui
import glob_utils.dialog.Qt_dialogs


__author__ = "David Metz"
__copyright__ = "Copyright (c) 2021"
__credits__ = ["David Metz"]
__license__ = "GPLv3"
__version__ = "2.0.0"
__maintainer__ = "David Metz"
__email__ = "d.metz@tu-bs.de"
__status__ = "Production"

logger = logging.getLogger(__name__)


################################################################################
## Class Capture Devices
################################################################################


class NoCaptureDeviceSelected(Exception):
    """"""


class CaptureFrameError(Exception):
    """"""


def handle_capture_device_error(func):
    """Decorator which handle the errors from CaptureDevices in
    Video Capture Modules
    """

    def wrapper(self, *args, **kwargs) -> Any:
        try:
            return func(self, *args, **kwargs)
        except NoCaptureDeviceSelected as e:
            logger.warning(f"No Capture Device Selected; ({e})")
            glob_utils.dialog.Qt_dialogs.errorMsgBox(
                title="No Capture Device Selected", message=f"{e}"
            )
        except CaptureFrameError as e:
            logger.error(f"Capture frame failed; ({e})")
            glob_utils.dialog.Qt_dialogs.errorMsgBox(
                title="Capture frame failed", message=f"{e}"
            )

    return wrapper


################################################################################
## Class Capture Devices
################################################################################


class CaptureDevices(ABC):

    _devices_available: dict[str, Any]
    _device: Any
    _name: str
    _initializated: CustomFlag
    _settings: dict

    def __init__(self) -> None:
        super().__init__()
        self._devices_available = {}
        self._device = None
        self._initializated = CustomFlag()
        self._settings = {}
        self._post_init_()

    def _error_if_no_device(func):
        """Decorator which test if the device has been initializated

        Raises:
            NoCaptureDeviceSelected: raised if not initializated
        """

        def wrap(self, *args, **kwargs):
            """"""
            if not self._initializated.is_set():  # raise error if no device selected
                raise NoCaptureDeviceSelected()
            func(self, *args, **kwargs)

        return wrap

    def set_name(self, name: str) -> None:
        """Set the name of the device."""
        if self._name == name:
            return

        if self.is_connected():
            logger.warning(
                "Capture Device already connected - please disconnect first capture device"
            )
            glob_utils.dialog.Qt_dialogs.warningMsgBox(
                title="Capture Device already connected",
                message="please disconnect first capture device",
            )
            return
        self._name = name

    @abstractmethod
    def _post_init_(self) -> None:
        """Post init for specific object initialisation process"""

    @abstractmethod
    def connect_device(self) -> None:
        """Connect the device corresponding to the self._name

        Raises:
            NoCaptureDeviceSelected: if no devices has been selected
        """

    @abstractmethod
    def disconnect_device(self) -> None:
        """Disconnect the device"""

    @abstractmethod
    def is_connected(self):
        """"""

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
    def capture_frame(self) -> Tuple[np.ndarray, None]:
        """Capture a frame on connected device and return it as an ndarray

        Raises:
            NoCaptureDeviceSelected: if no devices has been selected
            CaptureFrameError: if an error occur during capture

        Returns:
            Tuple[np.ndarray, None]: captured array or None if unsuccesfull
        """

    @abstractmethod
    def get_Qimage(self, frame: np.ndarray) -> PyQt5.QtGui.QImage:
        """Convert a frame (ndarray) in a Qt Image format object

        Args:
            frame (np.ndarray): frame to convert

        Returns:
            QImage: Qt Image
        """

    @abstractmethod
    def load_frame(self, file_path: str) -> np.ndarray:
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
