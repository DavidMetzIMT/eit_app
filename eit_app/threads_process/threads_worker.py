
from time import sleep

from PyQt5.QtCore import QThread, pyqtSignal
from threading import Thread, Event

class Poller(Thread):
    """ thread to repeatedly poll
    sleeptime: time to sleep between pollfunc calls
    pollfunc: function to repeatedly call to poll hardware"""

    def __init__(self,name, pollfunc, sleeptime=None,deamon=True) -> None:
        Thread.__init__(self)

        self.name = f'Hardware Poller "{name}"'
        self.pollfunc = pollfunc
        self.sleeptime = sleeptime or 0.1
        self.daemon=deamon
        self._runflag = Event()  # clear this to pause thread
        self._runflag.clear()    
      
    def run(self):
        self.worker()

    def worker(self):
        while 1:
            if self._runflag.is_set():
                self.pollfunc()
                sleep(self.sleeptime)
            else:
                sleep(0.1)

    def start_polling(self):
        self._runflag.set()

    def stop_polling(self):
        self._runflag.clear()

    def pause_polling(self):
        self.stop_polling()

    def resume_polling(self):
        self.stop_polling()

    def is_running(self):
        return(self._runflag.is_set())



class Worker(QThread):

    finished = pyqtSignal()
    progress = pyqtSignal()

    def __init__(self, name, sleeptime=None, verbose=False):
        super(Worker,self).__init__()
        self.name = f'Worker "{name}"'
        self.sleeptime = sleeptime or 0.1
        self.verbose=verbose

    def run(self):
        while 1:
            if self.verbose:
                print(f'{self.name} is running!!')
            sleep(self.sleeptime)
            self.progress.emit()
    
class CustomWorker(QThread):

    finished = pyqtSignal()
    progress = pyqtSignal()

    def __init__(self, sleeptime:float=None):  # sourcery skip: or-if-exp-identity
        super(CustomWorker,self).__init__()
        self.sleeptime= sleeptime or 0.1
        self._runflag = Event()  # clear this to pause thread
        self._runflag.clear()  

    def start_polling(self):
        self._runflag.set()

    def stop_polling(self):
        self._runflag.clear()

    def is_running(self):
        return self._runflag.is_set()

    def run(self):
        while 1:
            sleep(self.sleeptime)
            while self.is_running():
                self.progress.emit()
                sleep(self.sleeptime)
# class WorkerCam(QThread):

#     image_update = pyqtSignal(QImage)

#     def __init__(self, sleeptime=None):  # sourcery skip: or-if-exp-identity
#         super(WorkerCam,self).__init__()
#         self.thread_active = False
#         self.sleeptime= sleeptime or 0.1
#         self.sleeptime = sleeptime
#         self._runflag = Event()  # clear this to pause thread
#         self._runflag.clear()  

#     def set_capture_device(self, device:MicroCam):
#         self.capture_device= device

#     def start_capture(self):
#         self._runflag.set()

#     def stop_capture(self):
#         self._runflag.clear()
#     # def running(self):
#     #     return(self.runflag.is_set())

#     def is_running(self):
#         return(self._runflag.is_set())


#     def run(self):
#         while 1:
#             sleep(self.sleeptime)
#             while self.thread_active:
#                 ret, frame = self.capture_device.capture_frame()
#                 if ret:
#                     self.image_update.emit(convert_frame_to_Qt_format(frame))
#                 sleep(self.sleeptime)