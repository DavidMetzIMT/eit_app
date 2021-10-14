
import time

from eit_app.io.video.microcamera import MicroCam, convert_frame_to_Qt_format
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QImage


class Worker(QThread):
    finished = pyqtSignal()
    progress = pyqtSignal()

    def __init__(self, sleeptime=None):
        super(Worker,self).__init__()
        self.sleeptime= sleeptime if sleeptime else 0.1

    def run(self):
        while(1):
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
