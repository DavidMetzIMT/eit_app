
from __future__ import absolute_import, division, print_function


import os
import sys
import time
from multiprocessing import Process
from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication
from eit_app.app.backend import Ui_MainWindow
from eit_app.eit.reconstruction import ReconstructionPyEIT
from eit_app.threads_process.process_queue import NewQueue


def _poll_process4reconstruction(queue_in=None, queue_out=None, rec:ReconstructionPyEIT=ReconstructionPyEIT()):
    while True :
        time.sleep(0.1)
        rec.pollCallback(queue_in=queue_in, queue_out=queue_out)

def main():
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    rec= ReconstructionPyEIT()
    ui2rec_queue = NewQueue()
    rec2ui_queue = NewQueue()
    app = QApplication(sys.argv)
    app.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    ui = Ui_MainWindow(queue_in=rec2ui_queue, queue_out=ui2rec_queue, image_reconst=rec)
    ui.show()
    p = Process(target=_poll_process4reconstruction, args=(ui2rec_queue,rec2ui_queue,rec))
    p.daemon=True
    p.start()
    sys.exit(app.exec_())  

if __name__ == "__main__":
    from viztracer import VizTracer
    
    with VizTracer() as tracer:
        main()
    # 