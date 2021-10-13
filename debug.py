

from utils.eit_reconstruction import ReconstructionPyEIT
import datetime
import multiprocessing
import os
import sys
import time
from multiprocessing import Process
from os import path
from pickle import TRUE

import matplotlib
import matplotlib.figure
import matplotlib.pyplot as plt
import numpy as np
from cv2 import *
from matplotlib.backends.backend_qt5agg import \
    FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import \
    NavigationToolbar2QT as NavigationToolbar
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import (QGuiApplication, QImage, QKeyEvent, QPainter, QPen,
                         QPixmap)
from PyQt5.QtWidgets import (QApplication, QComboBox, QFontComboBox,
                             QMessageBox, QSlider)

from utils.microcamera import MicroCam, WorkerCam
from app_gui import Ui_MainWindow as app_gui
from utils.dialog_boxes import *
from utils.eit_dataset import *
from utils.eit_model import *
from utils.eit_reconstruction import ReconstructionPyEIT
from utils.new_queue import NewQueue
from utils.newQlabel import MyLabel
from utils.plots import plot_conductivity_map, plot_measurements
from utils.Sciospec import *
from utils.SciospecCONSTANTS import OP_LINEAR, OP_LOG
from utils.SciospecSerialInterfaceClass import *
from utils.utils_path import createPath
from utils.VoltagesProcessing import *
from utils.WorkerThread import Worker
from utils.constants import EXT_TXT, MEAS_DIR, SETUPS_DIR, DEFAULT_IMG_SIZES,EXT_IMG

import pyeit.mesh.plot as mplot

if __name__ == '__main__':
    rec= ReconstructionPyEIT()
    rec.initPyeit(EITModelClass())
    pts = np.array([[1,0,1], [1,1,0], [0,1,1], [0,0,1]])
    tri = np.array([[0,1,2,3]])
    mplot.tetplot(pts, tri, edge_color=(0.2, 0.2, 1.0, 1.0), alpha=0.01)
