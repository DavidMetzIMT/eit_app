#!C:\Anaconda3\envs\py38_app python
# -*- coding: utf-8 -*-

"""  Classes and function to interact with the Sciospec EIT device

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

# from typing import ValuesView
from abc import ABC, abstractmethod
from enum import Enum, auto

import os
from queue import Empty, Queue
import time
from typing import Union

import cv2
import numpy as np
from eit_app.threads_process.threads_worker import Poller
from eit_app.utils.flag import CustomFlag
from eit_app.utils.constants import DEFAULT_IMG_SIZES, EXT_IMG
from PyQt5.QtGui import QImage
from logging import getLogger
# from matplotlib.cbook import flatten
# from matplotlib.pyplot import title

# from utils.eit_dataset import *

__author__ = "David Metz"
__copyright__ = "Copyright (c) 2021"
__credits__ = ["David Metz"]
__license__ = "GPLv3"
__version__ = "2.0.0"
__maintainer__ = "David Metz"
__email__ = "d.metz@tu-bs.de"
__status__ = "Production"

# initialize the camera

# (1600,1200) (1280, 960) (800,600) (640,480)

# DEFAULT_SIZES={  #'1600 x 1200':(1600,1200), 
#         #'1280 x 960':(1280, 960),
#         #'800 x 600':(800,600),
#         '640 x 480':(640,480)
#         }
# DEFAULT_FILE_FORMATS= {'PNG': '.png', 'JPEG':'.jpg'}

logger = getLogger(__name__)

class NoCaptureDeviceSelected(Exception):
    """"""
class CaptureFrameError(Exception):
    """"""
    
class CaptureDeviceType(ABC):

    devices_available={}
    device=None
    init=CustomFlag()

    @abstractmethod
    def select_device(self, name:str):
        """"""
    @abstractmethod
    def get_devices_available(self, name)->dict:
        """"""
    @abstractmethod
    def set_properties(self, size):
        """"""
    @abstractmethod
    def print_properties(self):
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
    def save_frame (self, frame:np.ndarray, path:str):
        """"""
    

class MicroCam(CaptureDeviceType):

    def select_device(self, name):
        self.init.clear()
        self.devices_available[name]
        self.device=cv2.VideoCapture(self.devices_available[name] ,cv2.CAP_DSHOW)
        if self.device.read()[0]:
            self.init.set()

    def get_devices_available(self)-> dict:
        for index, _ in enumerate(range(10)):
            cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
            if cap.read()[0]:
                self.devices_available[f'MicroUSB {index}']=index
                cap.release()
        return self.devices_available

    def set_properties(self, size=list(DEFAULT_IMG_SIZES.keys())[-1]):
        image_size= DEFAULT_IMG_SIZES[size]
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
            self.init.set()
        self.print_properties()

    def print_properties(self):

        logger.info(f"CV_CAP_PROP_FRAME_WIDTH: '{self.device.get(cv2.CAP_PROP_FRAME_WIDTH)}'")
        logger.info(f"CV_CAP_PROP_FRAME_HEIGHT : '{self.device.get(cv2.CAP_PROP_FRAME_HEIGHT)}'")
        # print("CAP_PROP_FPS : '{}'".format(capture.get(cv2.CAP_PROP_FPS)))
        # print("CAP_PROP_POS_MSEC : '{}'".format(capture.get(cv2.CAP_PROP_POS_MSEC)))
        # print("CAP_PROP_FRAME_COUNT  : '{}'".format(capture.get(cv2.CAP_PROP_FRAME_COUNT)))
        # print("CAP_PROP_BRIGHTNESS : '{}'".format(capture.get(cv2.CAP_PROP_BRIGHTNESS)))
        # print("CAP_PROP_CONTRAST : '{}'".format(capture.get(cv2.CAP_PROP_CONTRAST)))
        # print("CAP_PROP_SATURATION : '{}'".format(capture.get(cv2.CAP_PROP_SATURATION)))
        # print("CAP_PROP_HUE : '{}'".format(capture.get(cv2.CAP_PROP_HUE)))
        # print("CAP_PROP_GAIN  : '{}'".format(capture.get(cv2.CAP_PROP_GAIN)))
        # print("CAP_PROP_CONVERT_RGB : '{}'".format(capture.get(cv2.CAP_PROP_CONVERT_RGB)))

        
    def capture_frame(self)-> np.ndarray:
        if not self.init.is_set():
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

class CaptureModuleStatus(Enum):
    live=auto()
    meas=auto()
    idle=auto()

class VideoCaptureModule(object):
    """"""
    def __init__(self, capture_type:CaptureDeviceType,queue_in:Queue,  queue_out:Queue) -> None:
        super().__init__()
        self.queue_in= queue_in # recieve path were the frame has to be saved
        self.queue_out= queue_out # send the Qimage to dipslay
        self.live_capture=Poller(name='live_capture',pollfunc=self._poll,sleeptime=0.05)
        self.live_capture.start()
        self.live_capture.start_polling()
        self.status=CaptureModuleStatus.idle
        self.capture_type=capture_type

        self.image_size= DEFAULT_IMG_SIZES[list(DEFAULT_IMG_SIZES.keys())[-1]]
        self.image_file_ext= EXT_IMG[list(EXT_IMG.keys())[0]]
        self.save_image_path= ''
        self.last_frame=None
        self.callbacks={
            CaptureModuleStatus.idle: self._idle,
            CaptureModuleStatus.meas:self._meas,
            CaptureModuleStatus.live:self._live_frame
        }

    def change_capture_type(self,capture_type:CaptureDeviceType):
        self.capture_type=capture_type

    def select_device(self, name:str):
        self.capture_type.select_device(name)
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
        self.status=CaptureModuleStatus.idle
        logger.debug('Idle mode')

    def set_meas(self):
        self.status=CaptureModuleStatus.meas
        logger.debug('Meas mode')
    def set_live(self):
        self.status=CaptureModuleStatus.live
        logger.debug('Live mode')
    # def start_live_capture(self):
    #     self.live_capture.start_polling()

    # def stop_live_capture(self):
    #     self.live_capture.stop_polling()

    def _poll(self):
        """"""
        self.callbacks[self.status]()

    def _idle(self):
        pass

    def _meas(self):
        if self.queue_in.empty():
            return
        path=self.queue_in.get()
        QtImage=self.save_image_now(path)
        logger.debug(f'Image saved in {path}')
        self.queue_out.put(QtImage)

    def _live_frame(self):
        try:
            self.last_frame = self.capture_type.capture_frame()
            QtImage= self.capture_type.get_Qimage(self.last_frame)
            self.queue_out.put(QtImage)
        except NoCaptureDeviceSelected:
            self.set_idle()
            logger.warning('NoCaptureDeviceSelected')
        except CaptureFrameError:
            logger.error('capture frame failed')
        
    def load_image(self,path)-> QImage:
        _, ext =os.path.split(path)
        if ext in list(EXT_IMG.values()):
            QtImage = self.capture_type.load_frame(path)
            logger.debug(f'\nImage loaded: {path}')
            self.queue_out.put(QtImage)
        return QtImage

    def save_image_now(self,path):
        """read and save the actual frame """
        path, _= os.path.splitext(path)
        path= path + self.image_file_ext
        frame= self.capture_type.capture_frame()
        QtImage= self.capture_type.get_Qimage(frame)
        self.capture_type.save_frame(frame, path)
        return QtImage

    def get_queue_in(self):
        return self.queue_in

def convert_frame_to_Qt_format(frame):
    return QImage(frame.data, frame.shape[1], frame.shape[0], QImage.Format_RGB888).rgbSwapped()



if __name__ == '__main__':
    
    print(list(EXT_IMG.values()))
    a= MicroCam()
    print(a.returnCameraIndexes())
    a.selectCam(1)
    
    a.debug()
    
    pass
