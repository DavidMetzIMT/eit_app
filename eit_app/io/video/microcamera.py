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
    '1600 x 1200':(1600,1200), 
    '1280 x 960':(1280,960),
    '800 x 600':(800,600),
    '640 x 480':(640,480)
}
EXT_IMG= {'PNG': '.png', 'JPEG':'.jpg'}

SNAPSHOT_DIR= 'snapshots'
class NoCaptureDeviceSelected(Exception):
    """"""
class CaptureFrameError(Exception):
    """"""
    
class CaptureDeviceType(ABC):

    devices_available:dict[str,Any]
    device:Any
    initializated:CustomFlag

    def __init__(self) -> None:
        super().__init__()

        self.devices_available={}
        self.device=None
        self.initializated=CustomFlag()
        self._post_init_()

    @abstractmethod   
    def _post_init_(self)->None:
        """Post init for specific object initialisation process"""

    @abstractmethod
    def connect_device(self, name:str)-> None:
        """Connect the device corresponding to the name given as arg

        Args:
            name (str): name of the device (one of the key returned by
            self.get_devices_available)
        """        
    @abstractmethod
    def get_devices_available(self)->dict:
        """create and return a dictionary of availables devices:
        self.devices_available= {
            'name device1 ': specific data to connect to the device 1,
            'name device2 ': specific data to connect to the device 2,
        }

        Returns:
            dict: dictionary of availables devices
        """        
        
    @abstractmethod
    def set_properties(self, size)-> None:
        """"""
    @abstractmethod
    def print_properties(self)-> None:
        """"""
    @abstractmethod
    def capture_frame(self)-> np.ndarray:
        """return succeed flag and image"""
    @abstractmethod
    def get_Qimage(self, frame:np.ndarray)-> QImage:
        """"""
    @abstractmethod
    def load_frame(self, path:str)-> np.ndarray:#
        """"""
    @abstractmethod
    def save_frame (self, frame:np.ndarray, path:str)-> None:
        """"""
    

class MicroCam(CaptureDeviceType):

    def _post_init_(self)->None:

        self.props=[
            cv2.CAP_PROP_FRAME_WIDTH,
            cv2.CAP_PROP_FRAME_HEIGHT,
            # cv2.CAP_PROP_FPS,
            # cv2.CAP_PROP_POS_MSEC,
            # Fcv2.CAP_PROP_FRAME_COUNT,
            # cv2.CAP_PROP_BRIGHTNESS,
            # cv2.CAP_PROP_CONTRAST,
            # cv2.CAP_PROP_SATURATION,
            # cv2.CAP_PROP_HUE,
            # cv2.CAP_PROP_GAIN,
            # cv2.CAP_PROP_CONVERT_RGB
        ]

    def connect_device(self, name:str)-> None:

        self.initializated.clear()
        if name not in self.devices_available:
            logger.error(f'Device "{name}" not available')
            logger.debug(f'Availabe devices:{self.devices_available}')
            raise NoCaptureDeviceSelected(f'Device "{name}" not available')

        self.devices_available[name]
        self.device=cv2.VideoCapture(
            self.devices_available[name] ,cv2.CAP_DSHOW)
        if self.device.read()[0]:
            self.initializated.set()

    def get_devices_available(self)-> dict:

        for index, _ in enumerate(range(10)):
            cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
            if cap.read()[0]:
                self.devices_available[f'MicroUSB {index}']=index
                cap.release()
        return self.devices_available

    def set_properties(self,size:str=None)-> None:

        if size is None:
            size= list(IMG_SIZES.keys())[-1] #default size (smaller one)
        image_size= IMG_SIZES[size]
        self.device.set(cv2.CAP_PROP_FRAME_WIDTH,image_size[0])
        self.device.set(cv2.CAP_PROP_FRAME_HEIGHT,image_size[1])
        time.sleep(2)
        ## To test....
        # self.device.set(cv2.CAP_PROP_AUTO_WB, 0)
        # self.device.set(cv2.CAP_PROP_EXPOSURE, 0)
        # self.device.set(cv2.CAP_PROP_GAIN , 0)
        # self.device.set(cv2.CAP_PROP_SATURATION , 0)
        # self.device.set(cv2.CAP_PROP_CONTRAST, 0)
        # self.device.set(cv2.CAP_PROP_BRIGHTNESS, -1)
        # self.device.set(cv2.CAP_PROP_HUE,hue)
        # self.device.set(cv2.CAP_PROP_CONVERT_RGB , 1)
        if self.device.read()[0]:
            self.initializated.set()
        self.print_properties()

    def print_properties(self)-> None:

        data={ prop.__name__: self.device.get(prop) for prop in self.props }
        [logger.info(f'{k}: {v}') for k, v in data.items()]

    
    def capture_frame(self)-> np.ndarray:
        if not self.initializated.is_set():
            raise NoCaptureDeviceSelected()
        succeed, frame = self.device.read()
        if not succeed:
            raise CaptureFrameError()    
        return frame
    
    def get_Qimage(self, frame:np.ndarray)-> QImage:
        """"""
        return convert_frame_to_Qt_format(frame)

    def load_frame(self, path:str)-> np.ndarray:#
        """"""
        return cv2.imread(path, cv2.IMREAD_COLOR)
        
    def save_frame(self, frame: np.ndarray, path:str):
        """"""
        cv2.imwrite(path,frame)

class CaptureStatus(Enum):
    live=auto()
    meas=auto()
    idle=auto()

class VideoCaptureModule(object):
    """"""
    def __init__(
        self, 
        capture_type:CaptureDeviceType,
        queue_in:Queue,  
        queue_out:Queue) -> None:
        super().__init__()
        self.queue_in= queue_in # recieve path were the frame has to be saved
        self.queue_out= queue_out # send the Qimage to dipslay
        self.live_capture=Poller(
            name='live_capture',pollfunc=self._poll,sleeptime=0.05)
        self.live_capture.start()
        self.live_capture.start_polling()
        self.status=CaptureStatus.idle
        self.capture_type=capture_type

        self.image_size= IMG_SIZES[list(IMG_SIZES.keys())[-1]]
        self.image_file_ext= EXT_IMG[list(EXT_IMG.keys())[0]]
        self.save_image_path= ''
        self.last_frame=None
        self.callbacks={
            CaptureStatus.idle: self._idle,
            CaptureStatus.meas:self._meas,
            CaptureStatus.live:self._live_frame
        }

    def change_capture_type(self,capture_type:CaptureDeviceType):
        self.capture_type=capture_type

    def select_device(self, name:str):
        self.capture_type.connect_device(name)
        logger.info(f'Video capture device: {name} - CONNECTED')
        
    def get_devices_available(self)->dict:
        devices=self.capture_type.get_devices_available()
        logger.info(f'Video capture devices available: {[k for k in devices]}')
        return devices
    
    def set_image_size(self, size:str):
        self.capture_type.set_properties(size)

    def set_image_file_format(self, file_ext=list(EXT_IMG.keys())[0]):
        self.image_file_ext= EXT_IMG[file_ext]
        logger.debug(f'image_file_ext selected {self.image_file_ext}')

    def set_idle(self):
        self.status=CaptureStatus.idle
        logger.debug('Idle mode')

    def set_meas(self):
        self.status=CaptureStatus.meas
        logger.debug('Meas mode')

    def set_live(self):
        self.status=CaptureStatus.live
        logger.debug('Live mode')

    def _poll(self)->None:
        """"""
        self.callbacks[self.status]()

    def _idle(self)->None:
        pass

    def _meas(self)->None:
        if self.queue_in.empty():
            return
        try:
            path=self.queue_in.get()
            QtImage=self.save_image_now(path)
            logger.debug(f'Image saved in {path}')
            self.queue_out.put(QtImage)
        except NoCaptureDeviceSelected:
            self.set_idle()
            logger.warning('NoCaptureDeviceSelected')

    def _live_frame(self)->None:
        try:
            self.last_frame = self.capture_type.capture_frame()
            QtImage= self.capture_type.get_Qimage(self.last_frame)
            self.queue_out.put(QtImage)
        except NoCaptureDeviceSelected:
            self.set_idle()
            logger.warning('NoCaptureDeviceSelected')
        except CaptureFrameError:
            logger.error('capture frame failed')
        
    def load_image(self,path:str=None)-> QImage:

        if path is None:
            self._live_frame() # capture actual frame

        _, ext =os.path.split(path)
        if ext not in list(EXT_IMG.values()) and not is_file(path):
            return None
        frame = self.capture_type.load_frame(path)
        QtImage= self.capture_type.get_Qimage(frame)
        logger.debug(f'\nImage loaded: {path}')
        self.queue_out.put(QtImage)
        return QtImage


    def save_image_now(self,path:str=None)-> QImage:
        """read and save the actual frame """
        if path is None:
            self._live_frame() # capture actual frame
        path, _= os.path.splitext(path)
        path= path + self.image_file_ext
        frame= self.capture_type.capture_frame()
        QtImage= self.capture_type.get_Qimage(frame)
        self.capture_type.save_frame(frame, path)
        return QtImage

    def get_queue_in(self):
        return self.queue_in

def convert_frame_to_Qt_format(frame:np.ndarray)-> QImage:
    return QImage(
        frame.data,
        frame.shape[1],
        frame.shape[0], QImage.Format_RGB888).rgbSwapped()



if __name__ == '__main__':
    
    print(list(EXT_IMG.values()))
    a= MicroCam()
    print(a.returnCameraIndexes())
    a.selectCam(1)
    
    a.debug()
    
    pass
