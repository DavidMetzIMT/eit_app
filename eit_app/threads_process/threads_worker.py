
import time

from eit_app.io.video.microcamera import MicroCam, convert_frame_to_Qt_format
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QImage
import threading
import sys

import logging
class HardwarePoller(threading.Thread):
    """ thread to repeatedly poll hardware
    sleeptime: time to sleep between pollfunc calls
    pollfunc: function to repeatedly call to poll hardware"""

    
    def __init__(self,name, pollfunc, sleeptime=None,deamon=True, verbose=False) -> None:
        threading.Thread.__init__(self)

        self.name = f'Hardware Poller "{name}"'
        self.pollfunc = pollfunc
        self.sleeptime= sleeptime if sleeptime else 0.1
        self.daemon=deamon
        self._verbose=verbose
        self._runflag = threading.Event()  # clear this to pause thread
        self._runflag.clear()    
      
    def run(self):
        # self.runflag.set()
        self.worker()

    def worker(self):
        # while(1):
        #     if self.verbose:
        #         print(f'{self.name} is running!!')
        #     time.sleep(self.sleeptime)
        #     self.progress.emit()
        while True:
            # logging.info(f'{self.name} is running!!')
            if self._verbose:
                print(f'{self.name} is running!!')
            if self._runflag.is_set():
                self.pollfunc()
                time.sleep(self.sleeptime)
            else:
                time.sleep(0.1)

    def start_polling(self):
        self._runflag.set()

    def stop_polling(self):
        self._runflag.clear()

    def pause_polling(self):
        self.stop_polling()

    def resume_polling(self):
        self.start_polling()

    def is_running(self):
        return(self._runflag.is_set())

    




class Worker(QThread):

    finished = pyqtSignal()
    progress = pyqtSignal()

    def __init__(self, name, sleeptime=None, verbose=False):
        super(Worker,self).__init__()
        self.name = f'Worker "{name}"'
        self.sleeptime= sleeptime if sleeptime else 0.1
        self.verbose=verbose
        
    #     self.sleeptime = sleeptime
    #     self.pollfunc = pollfunc  
    #     self.runflag = QThreading.Event()  # clear this to pause thread
    #     self.runflag.clear()
        
    # def run(self):
    #     self.runflag.set()
    #     self.worker()

    # def worker(self):
    #     while(1):
    #     if self.runflag.is_set():
    #         self.pollfunc()
    #         time.sleep(self.sleeptime)
    #     else:
    #         time.sleep(0.01)

    # def pause(self):
    #     self.runflag.clear()

    # def resume(self):
    #     self.runflag.set()

    # def running(self):
    #     return(self.runflag.is_set())

    # def kill(self):
    #     print "WORKER END"
    #     sys.stdout.flush()
    #     self._Thread__stop()

    def run(self):
        while(1):
            if self.verbose:
                print(f'{self.name} is running!!')
            time.sleep(self.sleeptime)
            self.progress.emit()
    

class WorkerCam(QThread):

    image_update = pyqtSignal(QImage)

    def __init__(self, sleeptime=None):
        super(WorkerCam,self).__init__()
        self.thread_active = False
        self.sleeptime= sleeptime if sleeptime else 0.1

    def set_capture_device(self, device:MicroCam):
        self.capture_device= device

    def start_capture(self):
        self.thread_active= True

    def run(self):
        while 1:
            time.sleep(self.sleeptime)
            while self.thread_active:
                ret, frame = self.capture_device.capture_frame()
                time.sleep(self.sleeptime)
                if ret:
                    # img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    # trans_img = cv2.flip(img, 1)
                    # ConvertToQtFormat = QImage(trans_img.data, trans_img.shape[1], trans_img.shape[0], QImage.Format_RGB888)
                    # picture = ConvertToQtFormat.scaled(640, 480, Qt.KeepAspectRatio)
                    self.image_update.emit(convert_frame_to_Qt_format(frame))

    def stop_capture(self):
        self.thread_active = False
        # self.quit()
