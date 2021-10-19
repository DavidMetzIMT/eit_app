#!C:\Anaconda3\envs\py38_app python
# -*- coding: utf-8 -*-
""" Set all the method needed to 

"""

from __future__ import absolute_import, division, print_function

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
from eit_app.app.event import post_event




from eit_app.io.video.microcamera import MicroCam
from eit_app.app.gui import Ui_MainWindow as app_gui
from eit_app.app.dialog_boxes import *
from eit_app.eit.model import *
from eit_app.eit.reconstruction import ReconstructionPyEIT
from eit_app.threads_process.process_queue import NewQueue
# from eit_app.app.newQlabel import MyLabel
from eit_app.eit.plots import plot_conductivity_map, plot_measurements
from eit_app.io.sciospec.device import *
from eit_app.io.sciospec.com_constants import OP_LINEAR, OP_LOG
from eit_app.io.sciospec.hw_serial_interface import *
from eit_app.utils.utils_path import createPath
from eit_app.eit.meas_preprocessing import *
from eit_app.threads_process.threads_worker import Worker, WorkerCam
from eit_app.utils.constants import EXT_TXT, MEAS_DIR, SETUPS_DIR, DEFAULT_IMG_SIZES,EXT_IMG
from eit_app.app.utils import setItems_comboBox
from eit_app.app.update_gui_listener import setup_update_event_handlers, UpdateDeviceEvents
# Ensure using PyQt5 backend
matplotlib.use('QT5Agg')

__author__ = "David Metz"
__copyright__ = "Copyright 2021, microEIT"
__credits__ = ["David Metz"]
__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = "David Metz"
__email__ = "d.metz@tu-bs.de"
__status__ = "Production"


class UiBackEnd(QtWidgets.QMainWindow, app_gui):
    
    def __init__(
        self,
        queue_in:NewQueue=None,
        queue_out:NewQueue=None,
        image_reconst:ReconstructionPyEIT=None,
        parent=None):
        
        # super(Ui_MainWindow, self).__init__(parent=parent)
        super().__init__()
        self.queue_in = queue_in # for multiprocessing
        self.queue_out = queue_out # for multiprocessing
        self.image_reconst=image_reconst
        self.setupUi(self) # call the method to setup the UI created with designer
        self._init_backend()
        self._init_multithreading_workers() # init the multithreadings workers
        
    
    def _init_backend(self):
        
        # Set app title and logo
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("MainWindow","EIT aquisition for Sciospec device "+ __version__))
        self.setWindowIcon(QtGui.QIcon('docs/icons/EIT.png'))
        self.cB_Scale.addItems([OP_LINEAR.name, OP_LOG.name])
        
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.PlotLayout.addWidget(self.toolbar)
        self.PlotLayout.addWidget(self.canvas)

        self._init_objects()

        # define callbacks for each button
        # PushButtons
        self.pB_refresh.clicked.connect(self._callback_Refresh)
        self.pB_connect.clicked.connect(self._callback_Connect)
        self.pB_disconnect.clicked.connect(self._callback_Disconnect)
        self.pB_Get_Setup.clicked.connect(self._callback_GetSetup)
        self.pB_Set_Setup.clicked.connect(self._callback_SetSetup)
        self.pB_Start.clicked.connect(self._callback_Start)
        self.pB_Stop.clicked.connect(self._callback_Stop)
        self.pB_SaveSetup.clicked.connect(self._callback_SaveSetup)
        self.pB_LoadSetup.clicked.connect(self._callback_LoadSetup)
        self.pB_Reset.clicked.connect(self._callback_Reset)
        self.pB_LoadDataSet.clicked.connect(self._callback_LoadDataSet)
        self.pB_ImagRec.clicked.connect(self._callback_Reconstruct)
        self.pB_loadRef.clicked.connect(self._callback_loadRef4TD)
        self.pB_Uplot.clicked.connect(self._callback_Uplot)
        self.pB_set_eit.clicked.connect(self._callback_set_eit)  
        self.cB_Frame_indx.activated.connect(self._callback_show_frame)
        self.cB_Frequency.activated.connect(self._callback_show_frame)


        self.pB_backbegin.clicked.connect(self._callback_ReplayBackBegin)
        self.pB_gotoend.clicked.connect(self._callback_ReplayGotoEnd)
        self.pB_play.clicked.connect(self._callback_ReplayPlay)
        self.pB_pause.clicked.connect(self._callback_ReplayPause)
        self.pB_stop.clicked.connect(self._callback_ReplaysStop)
        self.Slider_replay_time.valueChanged.connect(self._callback_Replay)

        self.minF.valueChanged.connect(self._update_freq_config)
        self.maxF.valueChanged.connect(self._update_freq_config)
        self.Steps.valueChanged.connect(self._update_freq_config)
        self.cB_Scale.activated.connect(self._update_freq_config)
        # self.Excitation_pattern.dataChanged.connect(self._update_freq_config)

        self.rB_RawData.setChecked(True)# init one at least!!!
        self.rB_RawData.toggled.connect(self._callback_update_plot)

        self.rB_TimeDiff.toggled.connect(self._callback_update_plot)
        self.cB_Frequency4TD.activated.connect(self._update_gui_data)
        self.pB_UpdateRef4TD.clicked.connect(self._callback_UpdateRef4TD)
        self.rB_FreqDiff.toggled.connect(self._callback_update_plot)
        self.cB_Frequency4FD_0.activated.connect(self._update_gui_data)
        self.cB_Frequency4FD_1.activated.connect(self._update_gui_data)

        self.showReal.setChecked(True) # init one at least!!!
        self.showReal.toggled.connect(self._callback_update_plot)
        self.showImag.toggled.connect(self._callback_update_plot)
        self.showMagnitude.toggled.connect(self._callback_update_plot)
        self.showPhase.toggled.connect(self._callback_update_plot)
        self.showAbsValue.toggled.connect(self._callback_update_plot)
        self.checkB_YLog.toggled.connect(self._callback_update_plot)

        self.rB_plot_graph.toggled.connect(self._callback_update_plot)
        self.checkB_Uplot.toggled.connect(self._callback_update_plot)
        self.checkB_diff.toggled.connect(self._callback_update_plot)
        self.rB_Image.toggled.connect(self._callback_update_plot)

        self.cB_ReconstructionAlgorithm.activated.connect(self._callback_initpyEIT)
        self.scalePlot_vmax.valueChanged.connect(self._callback_ScalePlot)
        self.scalePlot_vmin.valueChanged.connect(self._callback_ScalePlot)
        self.normalize.toggled.connect(self._callback_ScalePlot) 

        self.cB_video_devices.activated.connect(self._callback_set_cam)
        self.pB_refresh_video_devices.clicked.connect(self._callback_refresh_video_devices)
        self.cB_Image_format.activated.connect(self._callback_set_cam)
        self.cB_Image_fille_format.activated.connect(self._callback_set_cam)
        
        setItems_comboBox(self.cB_ReconstructionAlgorithm, ['JAC', 'BP', 'GREIT','NN'], handler=self._callback_initpyEIT)
        setItems_comboBox(self.cB_Image_format, list(DEFAULT_IMG_SIZES.keys()), handler=self._callback_set_cam)
        setItems_comboBox(self.cB_Image_fille_format, list(EXT_IMG.keys()), handler=self._callback_set_cam)

        self._update_gui_data()
        self._update_freq_config()
        self._callback_Refresh() # get actual comports
        self._get_imaging_parameters()
        self._callback_refresh_video_devices()


    def _init_objects(self):

        ## try of drawing a rectangle ...failed...
        # tmp_geo=self.video_frame.geometry()
        # self.video_frame = MyLabel(self)
        # self.video_frame.setCursor(Qt.CrossCursor)
        # self.video_frame.setGeometry(tmp_geo)

        # PATH_SETUP= os.getcwd() + "\Setup"
        createPath(SETUPS_DIR,append_datetime=False)
        # PATH_MEAS= os.getcwd() + "\Measurements"
        createPath(MEAS_DIR,append_datetime=False) 

        self._verbose=0
        self.LiveView=False
        self.EITDev = SWInterface4SciospecDevice([SETUPS_DIR, MEAS_DIR])# create object for serial communication

        self.liveDS = EITDataSet(MEAS_DIR)
        self.loadedDS = EITDataSet(MEAS_DIR)
        
        self.SerialInterface= SerialInterface()
        # self.SerialInterface.registerCallback(self.EITDev.treatNewRxFrame)
        # self.log_tmp= self.EITDev.log[:]
        self.EITDevDataUp= self.EITDev.flag_new_data
        self.Frame_cnt_old= -1 #self.liveDS.Frame_cnt

        self.EITModel= EITModelClass()
        self.EITDev.setup.exc_pattern= self.EITModel.InjPattern

        self.replay_play=False
        # setting of the camera
        self.micro_cam=MicroCam()
        self.micro_cam.selectCam(0)

        setup_update_event_handlers()
        
    def _init_multithreading_workers(self):
        # to treat live view of measured data
        self.workers = {}

        # workers= {     'live_view'      : [Worker, 0.05, self._poll_live_view ], 
        #                 'gui_update'    : [Worker,0.1, self._poll_update],
        #                 'serial'        : [Worker,0.01, self._poll_read_serial],
        #                 'ListenQueue'   : [Worker,0.1, self._listener_queue_in],
        #                 'video'         : [WorkerCam,0.1, self.ImageUpdateSlot]
        #         }
        
        # self.LiveViewWorkerSleeptime= 0.05
        # self.workers['live_view']= Worker(self.LiveViewWorkerSleeptime)
        # # self.LiveViewWorker = Worker(self.LiveViewWorkerSleeptime)
        # self.workers['live_view'].progress.connect(self._poll_live_view)
        # self.workers['live_view'].start()
        # self.div_10_cnt=0

        # # to actualize the gui
        # self.UpdateGuiWorkerSleeptime= 0.1
        # self.workers['gui_update'] = Worker(self.UpdateGuiWorkerSleeptime)
        # self.workers['gui_update'].progress.connect(self._poll_update)
        # self.workers['gui_update'].start()

        # # for the reading of the serial interface
        # self.SerialWorkerSleeptime= 0.01
        # self.workers['serial'] = Worker(self.SerialWorkerSleeptime)
        # self.workers['serial'].progress.connect(self._poll_read_serial)
        # self.workers['serial'].start()

        # # Listen the Queue in
        # self.ListenQueueSleeptime= 0.1
        # self.workers['ListenQueue'] = Worker(self.ListenQueueSleeptime)
        # self.workers['ListenQueue'].progress.connect(self._listener_queue_in)
        # self.workers['ListenQueue'].start()


        # self.ListenQueueSleeptime= 0.1
        # self.workers['video'] = WorkerCam()
        # self.workers['video'].image_update.connect(self.ImageUpdateSlot)
        # self.workers['video'].set_capture_device(self.micro_cam)
        # self.workers['video'].start()


    ## ======================================================================================================================================================
    ##  Automatic update of log and detection of D 
    ## ======================================================================================================================================================
    def _poll_live_view(self):
        """ Called by live_view_worker

        In case of liveView
            - if a new frame is available > plot/reconstruction...
            - in case that frame number is reach stop >> terminate measurement /live view
        
        Notes
        -----
            - live view is started with Start Meas.
            - live view can be stopped with Stop Meas.
        """

        if self.LiveView: # start measuremment
            self.label_LiveView.setText('LIVE')
            self.label_LiveView.setStyleSheet("background-color: green")

            if not self.liveDS.Frame_cnt== self.Frame_cnt_old: # new frame is available
                self.Frame_cnt_old =self.liveDS.Frame_cnt # reset
                self.compute_measurement()
                self._display_infotext_meas() # show infos about actual frame

                if self.pB_Video.isChecked():
                    path=os.path.join(self.liveDS.output_dir, f'Frame{self.liveDS.Frame_cnt+1:02}')
                    self.micro_cam.save_actual_frame(path)
                # if self.pB_Video.isChecked():

                #     self.micro_cam.save_image_path=self.liveDS.output_dir + os.path.sep +f'Frame{self.liveDS.Frame_cnt+1:02}'
                #     self.updade_video()
                #     self.micro_cam.save_image_path=''
                # self._plot_graphs()
            if self.EITDev.setup.burst>0 and self.liveDS.Frame_cnt == self.EITDev.setup.burst:
                self._callback_Stop() # >> self.LiveView = False 
                self._LoadDataSet(self.liveDS.output_dir)
        else:
            self.label_LiveView.setText('OFF')
            self.label_LiveView.setStyleSheet("background-color: red")
            self.progressBarFrame.setValue(0)

            # if self.pB_Video.isChecked():
            #     self.div_10_cnt +=1
            #     if self.div_10_cnt==1:
            #         self.div_10_cnt =0
            #         self.updade_video()

    def _poll_update(self):
        """ Called by UpdateGuiWorker

        In case that the device send the flag devDataUp (e.g. new data recieved)
            >> update the gui
        Also this poll report of device disconnection to the user  """ 
        # self.updade_video()

        # testlive Uplot
        if self.EITDevDataUp != self.EITDev.flag_new_data:
            self.EITDevDataUp, self.EITDev.flag_new_data = 0,0
            self._update_gui_data()

        # # Automatic detection of device disconnection
        # if self.SerialInterface.Ser.is_open:
        #     if self.SerialInterface.ErrorSerialInterface:
        #         self.SerialInterface.ErrorSerialInterface=''
        #         self._callback_Disconnect()
        #         self.EITDev.add2Log("Critical-" +'Error: ' + self.SerialInterface.ErrorSerialInterface+' :Please reconnect device' )
        #         self._update_gui_data()
        #         showDialog(self,'Error: ' + self.SerialInterface.ErrorSerialInterface + str(datetime.datetime.now()), 'Please reconnect device',  "Critical")

        if self.pB_Video.isChecked() and not self.workers['video'].thread_active:
            self.workers['video'].start_capture()
        elif not self.pB_Video.isChecked() and self.workers['video'].thread_active:
            self.workers['video'].stop_capture()

        # look if the recontruction is done
        # self._listener_queue_in() 

    def _poll_read_serial(self):
        """ Called by serial_worker
        Read the serial interface
        """
        self.SerialInterface.pollReadSerial()

        if self.replay_play:
            self.replay_timeBuffer+=self.SerialWorkerSleeptime
            if self.replay_timeBuffer>=self.replay_timeThreshold:
                self.replay_timeBuffer=0.0
                self.setSliderReplay(self.Slider_replay_time, next=True, loop=True)

    ## ======================================================================================================================================================
    ##  Callbacks 
    ## ======================================================================================================================================================
    def _callback_Refresh(self):
        '''Refresh the list of available COMports and update the list in the ComboBox '''
        self.EITDev.get_available_sciospec_devices()
        ## Update the comBox
        post_event(UpdateDeviceEvents.device_list_refreshed,self, self.EITDev)
    
    def _callback_Connect(self):
        ''' Open the serial port with the name port'''
        device_name= str(self.cB_comport.currentText()) # get actual ComPort
        try:
            self.EITDev.connect_device(device_name, baudrate=115200)
        except NoListOfAvailableDevices as error:
            showDialog(self,error.__str__(), 'Error: Refresh first', "Critical") 
        except CouldNotFindPortInAvailableDevices as error:
            showDialog(self,error.__str__(), 'Error: no Device connected', "Critical")
        post_event(UpdateDeviceEvents.device_connected,self, self.EITDev)
                    
    def _callback_Disconnect(self):
        ''' Disconnect actual device'''
        self.EITDev.disconnect_device()
        post_event(UpdateDeviceEvents.device_disconnected,self, self.EITDev)

        
    def _callback_Reset(self):
        self.is_flagMeas_Stop()
        if self.testSerialisOpen():
            self.EITDev.software_reset()
        self._update_gui_data()
    
    def _callback_GetSetup(self):
        # self.is_flagMeas_Stop()
        try:
            self.EITDev.get_setup()
        except CouldNotWriteToDevice as error:
            showDialog(self,error.__str__(), 'Error: no Device connected', "Critical")

        # self._update_gui_data() 

    def _callback_SetSetup(self):
        self.is_flagMeas_Stop()
        self._get_dev_setup_from_gui()
        if self.testSerialisOpen():
            self.EITDev.set_setup()
        self._update_gui_data()
        self._callback_GetSetup()
    
    def _callback_Start(self):
        self._get_dev_setup_from_gui()
        self.is_flagMeas_Stop()
        p,a= createPath(MEAS_DIR + os.path.sep + self.DataSetName.text(),append_datetime=True)
        self.DataSetName.setText(p[p.rfind(os.path.sep)+1:])
        if self.testSerialisOpen():
            self.liveDS.initDataSet(self.EITDev.setup, p)
            self.EITDev.setDataSet(self.liveDS)
            self.EITDev.start_meas()
            self.LiveView=True
            self.initLiveView()
        self._update_gui_data()
        
    def _callback_Stop(self):
        if self.testSerialisOpen():
            self.LiveView=False
            self.EITDev.stop_meas()
        self.Frame_cnt_old =-1 # reset
        self._update_gui_data()

    def _callback_SaveSetup(self):
        fileName, _= openFileNameDialog(self,path=SETUPS_DIR)
        sheetName= "Setup Device"
        if fileName:
            try: 
                self.EITDev.saveSetupDevice(fileName, sheetName)
            except PermissionError:
                showDialog(self,'please close the setup file \r\nor select an other one', 'Error: no write permision', "Critical")
            self._update_gui_data()
        
    def _callback_LoadSetup(self):
        fileName, _= openFileNameDialog(self,path=SETUPS_DIR)
        sheetName= "Setup Device"
        if fileName:
            self.EITDev.loadSetupDevice(fileName,sheetName)
            self._update_gui_data()
        
    def _callback_LoadDataSet(self): # the call back has to be  witouh arguments!!!
        self._LoadDataSet()

    def _LoadDataSet(self, dirpath:str=None):
        self.pB_Video.setChecked(False) # deactivate the video liveview!

        if not dirpath: # if dirpath not given then open dialog 
            dirpath, cancel= openDirDialog(self,path=MEAS_DIR)
            if cancel: # Cancelled
                return

        #image >>lokk what for images are in the directory
        formats = list(EXT_IMG.values())
        errors=[0]*len(formats)
        for i, extension in enumerate(formats):
            _, errors[i] =self.loadedDS.search4FileWithExtension(dirpath, ext=extension)
        

        # if not any(errors):
        #     self.donotdisplayloadedimage= True


        only_files, error = self.loadedDS.LoadDataSet(dirpath)
        if not error:
            #image >>look what for images are in the directory
            formats = list(EXT_IMG.values())
            errors=[0]*len(formats)
            for i, extension in enumerate(formats):
                _, errors[i] =self.loadedDS.search4FileWithExtension(dirpath, ext=extension)
            # only one sort of imge is save in on directory
            try:
                # setItems_comboBox(self, self.cB_Image_fille_format, items=None, handler=None, reset_box = False, set_index=errors.index(0))
                self.cB_Image_fille_format.setCurrentIndex(errors.index(0))
                self._callback_set_cam()
                
                self.displayloadedimage= True
            except ValueError:
                self.displayloadedimage= False

            setItems_comboBox(self.cB_Frame_indx, [i for i in range(len(only_files))])

            self.setSliderReplay(self.Slider_replay_time,  slider_pos=0, pos_min=0, pos_max=len(only_files)-1, single_step=1)
            self._update_cB_freq(self.loadedDS.frequencyList) # update all comboBox of the frequencies
            self._callback_show_frame()
            self._update_gui_data()
            return 1
        else:
            showDialog(self,'Directory empty', 'no File has been found in the selected directory', "Warning")
            return 0
        
    def _callback_show_frame(self):
        """
        Called by the 

        """
        self.setSliderReplay(self.Slider_replay_time,  slider_pos=self.cB_Frame_indx.currentIndex())
        if self.LiveView==False and not self.loadedDS.name==MEAS_DIR[MEAS_DIR.rfind(os.path.sep)+1:]: # only active when live view is inactive and dataset has been loaded
            self._display_infotext_meas()
            self.show_corresponding_image()
            self.compute_measurement()

    def show_corresponding_image(self):
        if self.displayloadedimage:
            path_image= self.loadedDS.Frame[self.cB_Frame_indx.currentIndex()].loaded_frame_path
            path_image= path_image[:-4]+self.micro_cam.image_file_ext
            self.updade_video(path=path_image)


    def _display_infotext_meas(self):
        # select right parameter depending on liveview
        if self.LiveView==True:
            selectFreq_indx= self.cB_Frequency.currentIndex()
            Frame = self.liveDS._last_frame[0]
            Meas= Frame.Meas[selectFreq_indx]
        else:
            selectFrame_indx= self.cB_Frame_indx.currentIndex()
            selectFreq_indx= self.cB_Frequency.currentIndex()
            Frame = self.loadedDS.Frame[selectFrame_indx]
            Meas= Frame.Meas[selectFreq_indx]
        # display  info text of the frame
        self.textEdit.setText("\r\n".join(Frame.infoText)) 
        # display meas value in tables      
        self.setTableWidget( self.tableWidgetvoltages_Z, Meas.voltage_Z)
        self.setTableWidget(self.tableWidgetvoltages_Z_real, np.real(Meas.voltage_Z))
        self.setTableWidget( self.tableWidgetvoltages_Z_imag, np.imag(Meas.voltage_Z))

    def initLiveView(self):
        self.textEdit.clear()
        self._update_cB_freq(self.liveDS.frequencyList) # update all comboBox of the frequencies
        if self.pB_Video.isChecked():
            path=os.path.join(self.liveDS.output_dir, f'Frame{self.liveDS.Frame_cnt:02}')
            self.micro_cam.save_actual_frame(path)
        
    def closeEvent(self, event):
        """Generate 'question' dialog on clicking 'X' button in title bar.

        Reimplement the closeEvent() event handler to include a 'Question'
        dialog with options on how to proceed - Save, Close, Cancel buttons
        """
        reply = QMessageBox.question(
            self, "Message",
            "Are you sure you want to quit? Any unsaved work will be lost.",
            QMessageBox.Save | QMessageBox.Close | QMessageBox.Cancel,
            QMessageBox.Save)
        if reply == QMessageBox.Save:
            # dosometthing to save work???
            event.accept()
        elif reply == QMessageBox.Close:
            event.accept()
        elif reply == QMessageBox.Cancel:
            event.ignore()

        self.kill_workers()
        
    def kill_workers(self):
        for key, item in self.workers.items():
            item.quit()

    def _callback_Uplot(self):
        pass    

    def is_flagMeas_Stop(self):
        if self.EITDev.flagMeasRunning:
            showDialog(self,'Measurement not stopped', 'Measurement has been stopped', "Information")
            self._callback_Stop()

    def compute_measurement(self):

        self._get_imaging_parameters()

        self.U= np.random.rand(256,2)
        self.current_labels= ['Random values' for _ in range(4)]
        if self.LiveView==True:
            if self.liveDS.Frame_cnt>0:
                setItems_comboBox(self.cB_Frame_indx, [self.liveDS.Frame_cnt-1], reset_box=False, set_index=-1) # actualize the 
                self.U, self.current_labels= Voltages4Reconstruct(  dataset=self.liveDS,
                                                                    frameIndx= 0,
                                                                    imagingParameters= self.ImagingParameters,
                                                                    EITModel= self.EITModel,
                                                                    liveView=self.LiveView)
        else:
            if self.loadedDS.Frame_cnt>0:
                path_txt= self.loadedDS.Frame[self.cB_Frame_indx.currentIndex()].loaded_frame_path
                path_txt, _ = os.path.splitext(path_txt)
                path_txt= path_txt + EXT_TXT
                self.U, self.current_labels = Voltages4Reconstruct( self.loadedDS, 
                                                                    self.cB_Frame_indx.currentIndex(), 
                                                                    self.ImagingParameters, 
                                                                    self.EITModel, 
                                                                    liveView=self.LiveView, 
                                                                    path=path_txt)

        if self.rB_Image.isChecked() and self.current_labels.count('Random values')==0:
            self.queue_out.put({'cmd': 'recpyEIT', 'v1':self.U[:,1], 'v0': self.U[:,0]})
        else:
            self._plot_graphs()


    def _plot_graphs(self):
        self.figure.clear()
        self.figure= plot_measurements( self.figure, 
                                        self.U, 
                                        self.image_reconst, 
                                        self.current_labels, 
                                        self.Graphs2Plot, 
                                        self.ImagingParameters)
        self.canvas.draw()

    def _callback_loadRef4TD(self):
        path, cancel= openFileNameDialog(self,path=MEAS_DIR)
        if cancel: # Cancelled
            return
        self._callback_UpdateRef4TD(path=path)    
        
    def _callback_UpdateRef4TD(self, path=None):
        if self.LiveView==True:
            self.liveDS.setFrameRef4TD() # Frame to use is ._last_frame[0] is the last updated...
        else:
            self.loadedDS.setFrameRef4TD(self.cB_Frame_indx.currentIndex(), path= path)
   
    def _callback_initpyEIT(self):
        # set some 
        self.EITModel.p=self.eit_p.value()
        self.EITModel.lamb=self.eit_lamda.value()
        self.EITModel.n=self.eit_n.value()
        self.U= np.random.rand(256,2)
        self.current_labels= ['test','test','test','test']

        self.EITModel.set_solver(self.cB_ReconstructionAlgorithm.currentText())
        self.EITModel.FEMRefinement=self.eit_FEMRefinement.value()
        self.queue_out.put({'cmd': 'initpyEIT', 'eit_model':self.EITModel, 'plot2Gui': self.figure})
        

    def _callback_set_eit(self):
        self._callback_initpyEIT()
        

                
    
    def _callback_Reconstruct(self):
        self.figure.clear()
        self.image_reconst.imageReconstruct()
        self.canvas.draw()

    def _callback_ScalePlot(self):
        self.queue_out.put({'cmd': 'setScalePlot', 'vmax':self.scalePlot_vmax.value(), 'vmin': self.scalePlot_vmin.value(), 'normalize':self.normalize.isChecked()})
        # self.image_reconst.setScalePlot(self.scalePlot_vmax.value(), self.scalePlot_vmin.value())
        # self.image_reconst.setNormalize(self.normalize.isChecked())

    def _callback_update_plot(self):

        self._get_dev_setup_from_gui()

        tmp1=[]
        tmp1.extend(self.ImagingParameters)
        self._get_imaging_parameters()
        
        
        cmp1= all(elem1 ==elem for elem1, elem in zip(tmp1, self.ImagingParameters))
        if self._verbose>0:
            print(tmp1)
            print(self.ImagingParameters, cmp1, self.Graphs2Plot)
        if self.LiveView==False:
            self.compute_measurement()
        self._update_gui_data()

    def _callback_ReplayBackBegin(self):
        self.setSliderReplay(self.Slider_replay_time, slider_pos=0)
        
    def _callback_ReplayGotoEnd(self):
        self.setSliderReplay(self.Slider_replay_time, slider_pos=-1)

    def _callback_ReplayPlay(self):
        self.replay_play= True
        self.replay_timeThreshold= self.replay_refresh_time.value()
        self.replay_timeBuffer=0.0
        
    def _callback_ReplayPause(self):
        self.replay_play= False
        
    def _callback_ReplaysStop(self):
        self.replay_play= False
        self.setSliderReplay(self.Slider_replay_time, slider_pos=0)
        self.replay_timeBuffer=0.0
        
    def _callback_Replay(self):
        self.cB_Frame_indx.setCurrentIndex(self.Slider_replay_time.sliderPosition())
        self._callback_show_frame()

    def _callback_refresh_video_devices(self):

        if self.pB_Video.isChecked():
            showDialog(self,'Stop capture before changing capture device', 'Error', 'Warning' )
        else:
            devices_indx= self.micro_cam.returnCameraIndexes()
            self.cB_video_devices.clear()
            if not devices_indx:
                items=['None video devices']
            else:
                items=[str(item) for item in devices_indx]

            setItems_comboBox( self.cB_video_devices,items, handler=self._callback_set_cam)

    def _callback_set_cam(self):
        
        if self.pB_Video.isChecked():
            
            showDialog(self,'Stop capture before changing capture device', 'Error', 'Warning' )
        else:
            self.micro_cam.selectCam(index=self.cB_video_devices.currentIndex())
            self.micro_cam.setCamProp(size=self.cB_Image_format.currentText())
            self.micro_cam.setImagefileFormat(file_ext=self.cB_Image_fille_format.currentText())
            
    def testSerialisOpen(self):
        if self.SerialInterface.Ser.is_open:
            return 1
        else:
            showDialog(self,'Please connect a Device', 'Error: no Device connected', "Critical")
            return 0
    ## ======================================================================================================================================================
    ##  Setter
    ## ======================================================================================================================================================
    
    def setSliderReplay(self, slider:QSlider,  slider_pos=0, pos_min=0, pos_max=None, single_step=1,page_step=1, next=False, loop=True):
        if not next:
            if slider_pos==-1:
                slider.setSliderPosition(slider.maximum())
            else:
                slider.setSliderPosition(slider_pos)
        else:
            if slider.sliderPosition()==slider.maximum():
                if loop:
                    slider.setSliderPosition(0)
                else:
                    pass
            else:
                slider.setSliderPosition(slider.sliderPosition()+1)

        if not pos_max==None: # change axis of slider only when the max change!
            slider.setMaximum(pos_max)
            slider.setMinimum(pos_min)    
            slider.setSingleStep(single_step)
            slider.setPageStep(page_step)
        
        return slider.sliderPosition(), slider.maximum()

    def _get_dev_setup_from_gui(self):
        ''' Save user entry from Gui in setup of dev'''
        ## save inputs Data OutputConfig Stamps all to one
        self.EITDev.setup.output_config.exc_stamp = 1
        self.EITDev.setup.output_config.current_stamp = 1
        self.EITDev.setup.output_config.time_stamp = 1

        ## Update EthernetConfig no changes
        if self.DHCP_Activated.isChecked():
            self.EITDev.setup.ethernet_config.dhcp= 1
        else:
            self.EITDev.setup.ethernet_config.dhcp= 0
            # self.EITDev.setup.EthernetConfig.IPAdress_str

        ## Update Measurement Setups
        self.EITDev.setup.frame_rate=self.FrameRate.value()
        self.EITDev.setup.burst= self.Burst.value()
        self.EITDev.setup.exc_amp=self.Current_Amplitude.value()/1000 # from mA -> A

        self.EITDev.setup.freq_config.min_freq_Hz=self.minF.value()
        self.EITDev.setup.freq_config.max_freq_Hz=self.maxF.value()
        self.EITDev.setup.freq_config.steps=self.Steps.value()
        self.EITDev.setup.freq_config.scale=self.cB_Scale.currentText()
        self.EITDev.setup.freq_config.mkFrequencyList()

        disableEntryField = self.rB_TimeDiff.isChecked()
        self.cB_Frequency4FD_0.setDisabled(disableEntryField)
        self.cB_Frequency4FD_1.setDisabled(disableEntryField)
        self.cB_Frequency4TD.setDisabled(not disableEntryField)
        self.pB_UpdateRef4TD.setDisabled(not disableEntryField)

    def _listener_queue_in(self):
        
        if not self.queue_in.empty():
            #print(self.queue_in.to_list())
            data=self.queue_in.get()
            print('CMD on queue:',data['cmd'])
            if data['cmd']=='updatePlot':
                print('updatePlot')
                self.image_reconst =data['rec']
                self._plot_graphs()
                
    def _get_imaging_parameters(self):

        self.ImagingParameters= [   [self.rB_RawData.isChecked(),self.cB_Frequency.currentIndex(), 0],
                                    [self.rB_TimeDiff.isChecked(), self.cB_Frequency4TD.currentIndex(), 0],
                                    [self.rB_FreqDiff.isChecked(), self. cB_Frequency4FD_0.currentIndex(), self. cB_Frequency4FD_1.currentIndex()],
                                    [self.showReal.isChecked(), self.showImag.isChecked(), self.showMagnitude.isChecked(), self.showPhase.isChecked(),self.showAbsValue.isChecked()],
                                    [self.checkB_YLog.isChecked()]]

        self.Graphs2Plot={ 'image': self.rB_Image.isChecked(),
                           'uplot': self.checkB_Uplot.isChecked(),
                            'diff': self.checkB_diff.isChecked()}

        if not any(self.Graphs2Plot.values()):
            self.checkB_Uplot.setChecked(True)
            self.Graphs2Plot['uplot']=True

        if self._verbose>0:
            print(self.ImagingParameters)
            print(any(self.Graphs2Plot.values()),self.Graphs2Plot.values())

    def _update_cB_freq(self, frequencies):
        
        for cB in [self.cB_Frequency, self.cB_Frequency4TD, self. cB_Frequency4FD_0, self. cB_Frequency4FD_1]:
            setItems_comboBox(cB, [f for f in frequencies])

    def _update_freq_config(self):

        minF_val=self.minF.value()
        maxF_val=self.maxF.value()
        steps_val=self.Steps.value()
        scale_val=self.cB_Scale.currentText()

        # Set Steps , also is setps 0 changed in 1
        if steps_val== 0:
            steps_val=1
        
        # Set minF and maxF
        # Deactivate maxF if steps 1 is entered, and set minF = maxF
        self.maxF.setStyleSheet("background-color: white")
        self.minF.setStyleSheet("background-color: white")
        self.Steps.setStyleSheet("background-color: white")
        if steps_val == 1:
            self.maxF.setEnabled(False)
            maxF_val=minF_val
        else:# be sure that minF < maxF
            self.maxF.setEnabled(True) 
            if maxF_val < minF_val:
                maxF_val = minF_val
            elif maxF_val == minF_val:
                self.maxF.setStyleSheet("background-color: red") # indicate user that steps >1  and 
                self.minF.setStyleSheet("background-color: red")
                self.Steps.setStyleSheet("background-color: red")

            #     steps_val = 1
            
        self.EITDev.setup.freq_config.steps = steps_val
        self.EITDev.setup.freq_config.min_freq_Hz = minF_val
        self.EITDev.setup.freq_config.max_freq_Hz = maxF_val
        self.EITDev.setup.freq_config.scale= scale_val

        self.EITDev.setup.computeMaxFrameRate() # self.EITDev.setup.FrequencyConfig.mkFrequencyList() is also called....

        # update directly if not user dont see that change...
        self.minF.setValue(self.EITDev.setup.freq_config.min_freq_Hz)
        self.maxF.setValue(self.EITDev.setup.freq_config.max_freq_Hz)
        self.Steps.setValue(self.EITDev.setup.freq_config.steps)

        self.MaxFrameRate.setValue(self.EITDev.setup.max_frame_rate)#

        self._update_cB_freq(self.EITDev.setup.freq_config.freqs)
        self._update_gui_data()

    def _update_gui_data(self):
        
        self.canvas.draw()
        # self.queue_in.put(self.EITDev.log)

        if self._verbose:
            print('_update_gui_data')

        if not self.LiveView: 
            # time.sleep(0.2)
            ## Update log
            # log_str= "\r\n".join(self.EITDev.log)
            # self.textEditlog.setText(log_str)
            # self.log_tmp= self.EITDev.log[:]
            scrollbar = self.textEditlog.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

            ## Update device status DONE USING A LISTENER
            # self.status_device.setText(self.EITDev.status_prompt)
            # self.status_device.adjustSize
            # if 'no Device connected' in self.EITDev.status_prompt:
            #     self.status_device.setStyleSheet("background-color: red")
            # else:
            #     self.status_device.setStyleSheet("background-color: green")

            # ## Update the comBox DONE USING A LISTENER
            # self.cB_comport.clear()
            # if not self.SerialInterface.AvailablePorts:
            #     self.cB_comport.addItem('None COMport')
            # else:
            #     self.cB_comport.addItems(self.SerialInterface.AvailablePorts)
                
            ## Update SN
            self.SN.setText(self.EITDev.setup.sn_formated)
            
            ## Update EthernetConfig
            self.DHCP_Activated.setChecked(self.EITDev.setup.ethernet_config.dhcp)
            self.IP_Adress.setText(self.EITDev.setup.ethernet_config.ip_formated)
            self.MAC_Adress.setText(self.EITDev.setup.ethernet_config.mac_formated)

            ## Update OutputConfig Stamps
            self.Excitation_Stamp.setChecked(self.EITDev.setup.output_config.exc_stamp)
            self.Current_Stamp.setChecked(self.EITDev.setup.output_config.current_stamp)
            self.Time_Stamp.setChecked(self.EITDev.setup.output_config.time_stamp)
            
            ## Update Measurement Setups
            self.FrameRate.setValue(self.EITDev.setup.frame_rate)
            self.Burst.setValue(self.EITDev.setup.burst)
            self.Current_Amplitude.setValue(self.EITDev.setup.exc_amp*1000) # from A -> mA
            self.minF.setValue(self.EITDev.setup.freq_config.min_freq_Hz)
            self.maxF.setValue(self.EITDev.setup.freq_config.max_freq_Hz)
            self.Steps.setValue(self.EITDev.setup.freq_config.steps)
            self.cB_Scale.setCurrentText(self.EITDev.setup.freq_config.scale)

            self.setTableWidget(self.Excitation_pattern,self.EITDev.setup.exc_pattern,0)
        

        ## Update RX frame
        self.actualFramecnt.setValue(self.liveDS.Frame_cnt)
        
        self.progressBarFrame.setValue(int(self.liveDS.Frame[0].Meas_frame_cnt/(self.liveDS.Frame[0].Meas_frame_num+1)*100))
    
    def ImageUpdateSlot(self, img: QtGui.QImage):
        # self.FeedLabel.setPixmap(QPixmap.fromImage(Image))
        self.image=img
        self.video_frame.setPixmap(QtGui.QPixmap.fromImage(self.image))
        self.image_min=self.image.scaledToHeight(self.video_frame_miniature.height())
        self.video_frame_miniature.setPixmap(QtGui.QPixmap.fromImage(self.image_min))

    def updade_video(self, path=None):

        if path==None:
            img, img_width, img_height= self.micro_cam.getImage()
            print('updade_video')
        else:
            img, img_width, img_height= self.micro_cam.load_saveImage(path)

        self.image = QtGui.QImage(img.data, img_width, img_height, QtGui.QImage.Format_RGB888).rgbSwapped()
        self.video_frame.setPixmap(QtGui.QPixmap.fromImage(self.image))
        self.image_min=self.image.scaledToHeight(self.video_frame_miniature.height())
        self.video_frame_miniature.setPixmap(QtGui.QPixmap.fromImage(self.image_min))
    
    def setTableWidget(self, tableWidget,list2display, decimal=4):
        list2display=np.array(list2display)
        if np.prod(list2display.shape)>1: 
            numrows = len(list2display)  # 6 rows in your example
            numcols = len(list2display[0])  # 3 columns in your example
            tableWidget.setColumnCount(numcols)# Set colums and rows in QTableWidget
            tableWidget.setRowCount(numrows)
            for row in range(numrows):# Loops to add values into QTableWidget
                for column in range(numcols):
                    tableWidget.setItem(row, column, QtWidgets.QTableWidgetItem(f"{list2display[row][column]:.{decimal}f}"))
        else:
            tableWidget.clearContents()
# Step 1: Create a worker class


def _poll_process4reconstruction(queue_in=None, queue_out=None, rec:ReconstructionPyEIT()=ReconstructionPyEIT()):

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
    ui = UiBackEnd(queue_in=rec2ui_queue, queue_out=ui2rec_queue, image_reconst=rec)
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
