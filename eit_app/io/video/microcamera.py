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
import os
import time

import cv2
import numpy as np
from eit_app.utils.constants import DEFAULT_IMG_SIZES, EXT_IMG
from PyQt5.QtGui import QImage

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

class MicroCam(object):


    def __init__(self) -> None:
        super().__init__()
        
        self.cam=cv2.VideoCapture(0,cv2.CAP_DSHOW)#=0#=VideoCapture(0,cv2.CAP_DSHOW)
        self.init=False
        self.image_size= DEFAULT_IMG_SIZES[list(DEFAULT_IMG_SIZES.keys())[-1]]
        self.image_file_ext= EXT_IMG[list(EXT_IMG.keys())[0]]
        self.save_image_path= ''
        self.actual_frame=None

    def selectCam(self, index=1):
        self.cam=cv2.VideoCapture(index ,cv2.CAP_DSHOW)
        self.init=True
        pass
    def returnCameraIndexes(self):
        # checks the first 10 indexes.
        index = 0
        arr = []
        for _ in range(10):
            cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
            if cap.read()[0]:
                arr.append(index)
                cap.release()
            index += 1
        return arr

    def setCamProp(self, size=list(DEFAULT_IMG_SIZES.keys())[-1], hue= 0):
        
        self.image_size= DEFAULT_IMG_SIZES[size]
        self.cam.set(cv2.CAP_PROP_FRAME_WIDTH,self.image_size[0])
        self.cam.set(cv2.CAP_PROP_FRAME_HEIGHT,self.image_size[1])
        time.sleep(2)
        ## To test....
        self.cam.set(cv2.CAP_PROP_AUTO_WB, 0)
        self.cam.set(cv2.CAP_PROP_EXPOSURE, 0)
        self.cam.set(cv2.CAP_PROP_GAIN , 0)
        self.cam.set(cv2.CAP_PROP_SATURATION , 0)
        self.cam.set(cv2.CAP_PROP_CONTRAST, 0)
        self.cam.set(cv2.CAP_PROP_BRIGHTNESS, -1)
        self.cam.set(cv2.CAP_PROP_HUE,hue)
        self.cam.set(cv2.CAP_PROP_CONVERT_RGB , 1)
        self.print_prop()

    def setImagefileFormat(self, file_ext=list(EXT_IMG.keys())[0]):
        self.image_file_ext= EXT_IMG[file_ext]
    
    def save_actual_frame(self, path):
        if isinstance(self.actual_frame,np.ndarray):
             save_frame(path, self.actual_frame)
    
    def saveImage(self, path):
        # only one sort of imge is save in on directory
        if self.init:
            _, img = self.cam.read()
            cv2.imwrite(path+self.image_file_ext,img)
        
    def capture_frame(self):
        ret, frame = self.cam.read()
        self.actual_frame= frame
        return ret, frame

    def getImage(self):

        if self.init:
            pass
        else:
            print('no Camera selected')

        _, img = self.cam.read()
        print('image read')
        img_width, img_height = np.shape(img)[1], np.shape(img)[0]
        
        if self.save_image_path:
            cv2.imwrite(self.save_image_path+self.image_file_ext,img)

        return img, img_width, img_height 

    def load_saveImage(self,path):
        img= cv2.imread(path, cv2.IMREAD_COLOR)
        print('image loaded')
        img_width, img_height = np.shape(img)[1], np.shape(img)[0]
        return img, img_width, img_height

    def print_prop(self):
        capture= self.cam
        print("CV_CAP_PROP_FRAME_WIDTH: '{}'".format(capture.get(cv2.CAP_PROP_FRAME_WIDTH)))
        print("CV_CAP_PROP_FRAME_HEIGHT : '{}'".format(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)))
        print("CAP_PROP_FPS : '{}'".format(capture.get(cv2.CAP_PROP_FPS)))
        print("CAP_PROP_POS_MSEC : '{}'".format(capture.get(cv2.CAP_PROP_POS_MSEC)))
        print("CAP_PROP_FRAME_COUNT  : '{}'".format(capture.get(cv2.CAP_PROP_FRAME_COUNT)))
        print("CAP_PROP_BRIGHTNESS : '{}'".format(capture.get(cv2.CAP_PROP_BRIGHTNESS)))
        print("CAP_PROP_CONTRAST : '{}'".format(capture.get(cv2.CAP_PROP_CONTRAST)))
        print("CAP_PROP_SATURATION : '{}'".format(capture.get(cv2.CAP_PROP_SATURATION)))
        print("CAP_PROP_HUE : '{}'".format(capture.get(cv2.CAP_PROP_HUE)))
        print("CAP_PROP_GAIN  : '{}'".format(capture.get(cv2.CAP_PROP_GAIN)))
        print("CAP_PROP_CONVERT_RGB : '{}'".format(capture.get(cv2.CAP_PROP_CONVERT_RGB)))

    def debug(self):

        # self.setCamProp()
        self.print_prop()

        time.sleep(2)
        self.cam.set(10, 100)
        s, img = self.cam.read()
        cv2.imshow("cam-test",img)
        cv2.waitKey(0)


def save_frame(path, frame, extension=EXT_IMG['PNG']):
    if extension:
        path, _= os.path.splitext(path)
        path= path + extension
    cv2.imwrite(path,frame)

def load_frame(path, extension=EXT_IMG['PNG']):
    if os.path.exists(path):
        _, ext= os.path.splitext(path)
        if ext==extension:
            frame= cv2.imread(path, cv2.IMREAD_COLOR)
            print(f'\nImage loaded: {path}')
    # img_width, img_height = np.shape(img)[1], np.shape(img)[0]

    return convert_frame_to_Qt_format(frame)

def convert_frame_to_Qt_format(frame):

    return QImage(frame.data, frame.shape[1], frame.shape[0], QImage.Format_RGB888).rgbSwapped()




#     cam = VideoCapture(1)   # 0 -> index of camera
# s, img = cam.read()
# if s:    # frame captured without any errors
#     # namedWindow("cam-test",SIZE)
#     imshow("cam-test",img)
#     waitKey(0)
#     destroyWindow("cam-test")
#     imwrite("filename.jpg",img) #save image


# import sys
# from PyQt5.QtGui import QImage
# from PyQt5.QtWidgets import *
# from PyQt5.QtCore import *
# import cv2

# class MainWindow(QWidget):
#     def __init__(self):
#         super(MainWindow, self).__init__()

#         self.VBL = QVBoxLayout()

#         self.FeedLabel = QLabel()
#         self.VBL.addWidget(self.FeedLabel)

#         self.CancelBTN = QPushButton("Cancel")
#         self.CancelBTN.clicked.connect(self.CancelFeed)
#         self.VBL.addWidget(self.CancelBTN)

#         self.Worker1 = Worker1()

#         self.Worker1.start()
#         self.Worker1.ImageUpdate.connect(self.ImageUpdateSlot)
#         self.setLayout(self.VBL)

#     def ImageUpdateSlot(self, Image):
#         self.FeedLabel.setPixmap(QPixmap.fromImage(Image))

#     def CancelFeed(self):
#         self.Worker1.stop()

# class WorkerCam(QThread):

#     image_update = pyqtSignal(QImage)

#     def __init__(self, sleeptime=None):
#         super(WorkerCam,self).__init__()
#         self.thread_active = False
#         self.sleeptime= sleeptime if sleeptime else 0.1

#     def set_capture_device(self, device:MicroCam):
#         self.capture_device= device

#     def start_capture(self):
#         self.thread_active= True

#     def run(self):
#         while 1:
#             time.sleep(self.sleeptime)
#             while self.thread_active:
#                 ret, frame = self.capture_device.capture_frame()
#                 time.sleep(self.sleeptime)
#                 if ret:
#                     # img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#                     # trans_img = cv2.flip(img, 1)
#                     # ConvertToQtFormat = QImage(trans_img.data, trans_img.shape[1], trans_img.shape[0], QImage.Format_RGB888)
#                     # picture = ConvertToQtFormat.scaled(640, 480, Qt.KeepAspectRatio)
#                     self.image_update.emit(convert_frame_to_Qt_format(frame))

#     def stop_capture(self):
#         self.thread_active = False
#         # self.quit()

if __name__ == '__main__':
    
    print(list(EXT_IMG.values()))
    a= MicroCam()
    print(a.returnCameraIndexes())
    a.selectCam(1)
    
    a.debug()
    
    pass
