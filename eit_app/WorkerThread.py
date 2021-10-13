
from PyQt5.QtCore import QThread, pyqtSignal
import time

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