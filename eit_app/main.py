from __future__ import absolute_import, division, print_function

import os
import sys

from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication

from eit_app.backend import UiBackEnd


def main():
    """Run the eit_app"""
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    QApplication.setStyle('Fusion')
    app = QApplication(sys.argv)
    app.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    ui = UiBackEnd()
    ui.show()
    exit(app.exec_())


if __name__ == "__main__":
    from glob_utils.log.log import main_log

    main_log()
    main()
