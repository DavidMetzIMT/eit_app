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
import numpy as np
from eit_app.threads_process.threads_worker import Poller
from glob_utils.flags.flag import CustomFlag
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

IMG_SIZES={
    # '1600 x 1200':(1600,1200), 
    '1280 x 960':(1280,960),
    # '800 x 600':(800,600),
    '640 x 480':(640,480)
}
EXT_IMG= {'PNG': '.png', 'JPEG':'.jpg'}

SNAPSHOT_DIR= 'snapshots'


################################################################################
## Class Capture Devices
################################################################################
class NoCaptureDeviceSelected(Exception):
    """"""
class CaptureFrameError(Exception):
    """"""
    
class CaptureDevices(ABC):

    devices_available:dict[str,Any]
    device:Any
    initializated:CustomFlag
    settings:dict

    def __init__(self) -> None:
        super().__init__()
        self.devices_available={}
        self.device=None
        self.initializated=CustomFlag()
        self.settings={}
        self._post_init_()

    @abstractmethod   
    def _post_init_(self)->None:
        """Post init for specific object initialisation process"""

    @abstractmethod
    def connect_device(self, name:str)-> None:
        """Connect the device corresponding to the name given as arg

        Raises:
            NoCaptureDeviceSelected: if no devices has been selected

        Args:
            name (str): name of the device (one of the key returned by
            self.get_devices_available)
        """

    @abstractmethod
    def get_devices_available(self)-> dict[str,Any]:
        """Create and return a dictionary of availables devices:

        self.devices_available= {'name1 ': specific data to device 1, ...}

        Returns:
            dict: dictionary of availables devices
        """        
    @abstractmethod
    def set_settings(self, **kwargs)-> None:
        """Set devices settings such as size of frame, etc.

        Note: should call self.get_setting() at the end

        Raises:
            NoCaptureDeviceSelected: if no devices has been selected

        Args:
            use kwargs to be flexible... 
        """        
    @abstractmethod
    def get_settings(self)-> dict[str,Any]:
        """Read actual setting of the connected capture device

        - update self.settings= {'property1':val_prop1, ...}
        - logging of setting (debug)

        Raises:
            NoCaptureDeviceSelected: if no devices has been selected

        Returns:
            dict[str,Any]: settings dictionnary
        """        

    @abstractmethod
    def capture_frame(self)-> np.ndarray:
        """Capture a frame on connected device and return it as an ndarray

        Raises:
            NoCaptureDeviceSelected: if no devices has been selected
            CaptureFrameError: if an error occur during capture

        Returns:
            np.ndarray: captured array
        """

    @abstractmethod
    def get_Qimage(self, frame:np.ndarray)-> QImage:
        """Convert a frame (ndarray) in a Qt Image format object

        Args:
            frame (np.ndarray): frame to convert

        Returns:
            QImage: Qt Image 
        """

    @abstractmethod
    def load_frame(self, file_path:str)-> np.ndarray:#
        """Load a frame (ndarray) contained in a file 

        Args:
            file_path (str): path of the file to load

        Returns:
            np.ndarray: loaded frame
        """        

    @abstractmethod
    def save_frame (self, frame:np.ndarray, file_path:str)-> None:
        """Save passed frame (ndarray) in file_path

        Args:
            frame (np.ndarray): [description]
            path (str): [description]
        """        
    
class MicroUSBCamera(CaptureDevices):
    """Class 
    """    

    def _post_init_(self)->None:
        self.props={
            'Frame_width':cv2.CAP_PROP_FRAME_WIDTH,
            'Frame_height':cv2.CAP_PROP_FRAME_HEIGHT,
            # cv2.CAP_PROP_FPS, cv2.CAP_PROP_POS_MSEC,
            # Fcv2.CAP_PROP_FRAME_COUNT, cv2.CAP_PROP_BRIGHTNESS,
            # cv2.CAP_PROP_CONTRAST, cv2.CAP_PROP_SATURATION,
            # cv2.CAP_PROP_HUE, cv2.CAP_PROP_GAIN,
            # cv2.CAP_PROP_CONVERT_RGB
        }
        self.settings={ k: None for k, _ in self.props.items() }

    def connect_device(self, name:str)-> None:
        self.initializated.clear()
        if name not in self.devices_available:
            logger.error(f'Device "{name}" not available')
            logger.debug(f'Availabe devices:{self.devices_available}')
            raise NoCaptureDeviceSelected(f'Device "{name}" not available')

        self.devices_available[name]
        self.device=cv2.VideoCapture(
            self.devices_available[name] ,cv2.CAP_DSHOW)
        self._check_device()

    def get_devices_available(self)-> dict[str, Any]:
        for index, _ in enumerate(range(10)):
            cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
            if cap.read()[0]:
                self.devices_available[f'MicroUSB {index}']=index
                cap.release()
        return self.devices_available

    def set_settings(self,**kwargs)-> None:
        if not self.initializated.is_set(): # raise error if no device selected
            raise NoCaptureDeviceSelected()
        # set size of the frame
        size = kwargs['size'] if 'size' in kwargs else None
        if size is None:
            return
        self.device.set(cv2.CAP_PROP_FRAME_WIDTH,size[0])
        self.device.set(cv2.CAP_PROP_FRAME_HEIGHT,size[1])
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

    def get_settings(self)-> dict[str,Any]:
        if not self.initializated.is_set(): # raise error if no device selected
            raise NoCaptureDeviceSelected()

        self.settings={k: self.device.get(v) for k, v in self.props.items()}
        [logger.info(f'{k}: {v}') for k, v in self.settings.items()]
        return self.settings

    
    def capture_frame(self)-> np.ndarray:
        if not self.initializated.is_set():# raise error if no device selected
            raise NoCaptureDeviceSelected()

        succeed, frame = self.device.read()
        if not succeed: # raise error if reading of a frame not succesful
            raise CaptureFrameError()    
        return frame
    
    def get_Qimage(self, frame:np.ndarray)-> QImage:
        return convert_frame_to_Qt_format(frame)

    def load_frame(self, file_path:str)-> np.ndarray:
        return cv2.imread(file_path, cv2.IMREAD_COLOR)
        
    def save_frame(self, frame: np.ndarray, file_path:str):
        cv2.imwrite(file_path, frame)
    
    def _check_device(self):
        """Check if the device works, here we read frame and verify that it is
        succesful
        """
        succeed, _=self.device.read()
        if succeed:
            self.initializated.set()
        else:
            self.initializated.clear()

################################################################################
## Class Video Capture Module
################################################################################

class CaptureStatus(Enum):
    """ Status for the Video Capture Module
    """    
    live=auto()
    meas=auto()
    idle=auto()

def handle_capture_device_error(func):
    """Decorator to handle the errors from CaptureDevices in 
    Video Capture Modules
    """    
    def wrapper(self,*args, **kwargs) -> Any:
        try:
            return func(self, *args, **kwargs)
        except NoCaptureDeviceSelected as e:
            self.set_idle()
            logger.warning(f'No Capture Device Selected; ({e})')
        except CaptureFrameError as e:
            logger.error(f'Capture frame failed; ({e})')
    return wrapper
class VideoCaptureModule(object):
    """ Handel a capture device and can provide
    a live, a measuring and an idle mode using a worker thread    
    """    
    def __init__(
        self, 
        capture_type:CaptureDevices,
        queue_in:Queue,  
        queue_out:Queue) -> None:

        super().__init__()
        self.queue_in= queue_in # recieve path were the frame has to be saved
        self.queue_out= queue_out # send the Qimage to dipslay
        self.worker=Poller(
            name='live_capture',pollfunc=self._poll,sleeptime=0.05)
        self.worker.start()
        self.worker.start_polling()
        self.status=CaptureStatus.idle
        self.capture_type=capture_type

        self.image_size= IMG_SIZES[list(IMG_SIZES.keys())[-1]]
        self.image_file_ext= EXT_IMG[list(EXT_IMG.keys())[0]]
        self.save_image_path= ''
        self.last_frame=None
        self.devices:list[str]=[]
        self.processes={
            CaptureStatus.idle: self._idle,
            CaptureStatus.meas:self._meas,
            CaptureStatus.live:self._live_frame
        }

    def set_capture_type(self,capture_type:CaptureDevices)->None:
        """Set the type of capture device

        Args:
            capture_type (CaptureDevices): a CaptureDevices object
        """        
        self.capture_type=capture_type

    def get_devices_available(self)->list[str]:
        """ Return a list of the name of the availbale devices

        Returns:
            list[str]: names of the available devices
        """        
        self.devices=list(self.capture_type.get_devices_available().keys())
        logger.info(f'Capture devices available: {[d for d in self.devices]}')
        return self.devices

    @handle_capture_device_error
    def select_device(self, name:str)->None:
        """Select a device 

        Args:
            name (str): name of the device, which has to be in the self.devices
        """
        
        self.capture_type.connect_device(name)
        logger.info(f'Video capture device: {name} - CONNECTED')
        
    @handle_capture_device_error
    def set_image_size(self, size:str)->None:
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
            logger.error(f'Wrong imgae size : {size}')
            return
        self.image_size= IMG_SIZES[size]
        self.capture_type.set_settings(size=self.image_size)

    def set_image_file_format(self, file_ext=list(EXT_IMG.keys())[0])->None:
        """Set the file format for image saving

        Args:
            file_ext ([type], optional): file extension.
            Defaults to list(EXT_IMG.keys())[0].
        """        
        self.image_file_ext= EXT_IMG[file_ext]
        logger.debug(f'image_file_ext selected {self.image_file_ext}')

    def set_idle(self)->None:
        """Set Idle Mode
        """        
        self.status=CaptureStatus.idle
        logger.debug('Idle mode')

    def set_meas(self)->None:
        """Set Measuring Mode
        """        
        self.status=CaptureStatus.meas
        logger.debug('Meas mode')

    def set_live(self)->None:
        """Set Live Mode
        """        
        self.status=CaptureStatus.live
        logger.debug('Live mode')

    def _poll(self)->None:
        """Call the process corresponding to the actual status
        """        
        self.processes[self.status]()

    def _idle(self)->None:
        """Idle process

        Do Nothing
        """        

    def _meas(self)->None:
        """Measuring process

        Wait on queue_in for a path where actual frame has to be saved.
        and post the actual image in queue out (eg. for display on GUI)
        """        
        if self.queue_in.empty():
            return
        path=self.queue_in.get()
        QtImage=self.snapshot(path)
        self.queue_out.put(QtImage)

    def _live_frame(self)->None:
        """Live process

        Read and post the actual image in queue out (eg. for display on GUI)
        """        
        QtImage= self.snapshot()
        self.queue_out.put(QtImage)
    
    @handle_capture_device_error
    def snapshot(self, path:str=None)-> QImage:
        """Make a snapshot and return a Qt image

        Args:
            path (str, optional): If path is not `None`, the captured 
            frame(ndarray) is saved at this path. Defaults to `None`.

        Returns:
            QImage: captured Qt image
        """       
        
        frame= self.capture_type.capture_frame()
        QtImage= self.capture_type.get_Qimage(frame)
        if path and isinstance(path, str):
            path, _= os.path.splitext(path)
            path= path + self.image_file_ext
            self.capture_type.save_frame(frame, path)
            logger.debug(f'Image saved in {path}')
        return QtImage
        
    def load_image(self,path:str=None)-> QImage:
        """Load an image out of an file in which a frame (ndarray) has been
        saved

        Args:
            path (str, optional): . Defaults to None.

        Returns:
            QImage: Loaded image in Qt format
        """        
        if path is None:
            return self.snapshot() # capture actual frame

        _, ext =os.path.split(path)
        if ext not in list(EXT_IMG.values()) and not is_file(path):
            return None
        frame = self.capture_type.load_frame(path)
        QtImage= self.capture_type.get_Qimage(frame)
        logger.debug(f'\nImage "{path}" - Loaded')
        self.queue_out.put(QtImage)
        return QtImage


def convert_frame_to_Qt_format(frame:np.ndarray)-> QImage:
    """Convert a frame (ndarray) to a Qt formatted image

     Raises:
        TypeError: if frame is not an ndarray

    Args:
        frame (np.ndarray): frame to convert

    Returns:
        QImage: corresponding Qt image 
    """
    if not isinstance(frame, np.ndarray):
        raise TypeError(f'{frame=} should be an ndarray')
        
    return QImage(
        frame.data,
        frame.shape[1],
        frame.shape[0],
        QImage.Format_RGB888).rgbSwapped()



if __name__ == '__main__':
    """"""    
    
    print(list(EXT_IMG.values()))
    a= MicroUSBCamera()
    
