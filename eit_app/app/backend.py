#!C:\Anaconda3\envs\py38_app python
# -*- coding: utf-8 -*-
""" Set all the method needed to 

"""

from __future__ import absolute_import, division, print_function
import traceback
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
from eit_app.app.event import CustomEvents
from pathlib import Path



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
from eit_app.app.utils import set_comboBox_items, set_table_widget,set_slider
from eit_app.app.update_gui_listener import setup_update_event_handlers, UpdateDeviceEvents
from eit_app.utils.flag import Flag
from eit_app.io.sciospec.meas_dataset import EitMeasurementDataset

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
    
    def __init__(   self,
                    queue_in:NewQueue=None, queue_out:NewQueue=None,
                    image_reconst:ReconstructionPyEIT=None,
                    parent=None):
    
        super().__init__()
        self.queue_in = queue_in # for multiprocessing
        self.queue_out = queue_out # for multiprocessing
        self.image_reconst=image_reconst
        self.setupUi(self) # call the method to setup the UI created with designer
        self._post_init()
    

    def _post_init(self):
        _translate = QtCore.QCoreApplication.translate
        # Set app title and logo
        self.setWindowTitle(_translate("MainWindow","EIT aquisition for Sciospec device "+ __version__))
        self.setWindowIcon(QtGui.QIcon('docs/icons/EIT.png'))
        # 
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.PlotLayout.addWidget(self.toolbar)
        self.PlotLayout.addWidget(self.canvas)

        self._init_main_objects()

        # link callbacks
        self.link_callbacks_for_interaction_on_device_tab()
        self.link_callbacks_for_interaction_on_measurement_tab()
        self.link_callbacks_for_interaction_on_eitplotter_tab()
        self.link_callbacks_for_interaction_on_video_tab()

        self._update_gui_data()
        self._update_device_setup_from_gui()
        self._callback_refresh_device_list() # get actual comports
        self._get_imaging_parameters()
        self._callback_refresh_video_devices()
        self.up_events.post(UpdateDeviceEvents.device_status,self, self.device)
        

        self._init_multithreading_workers() # init the multithreadings workers

    def _init_main_objects(self):

        createPath(SETUPS_DIR,append_datetime=False)
        createPath(MEAS_DIR,append_datetime=False) 

        # self._verbose=0
        self.live_view=Flag()
        self.device = SWInterface4SciospecDevice()# create object for serial communication

        self.liveDS = EitMeasurementDataset()
        self.liveDS.init_for_gui()
        self.loadedDS = EitMeasurementDataset()
        self.loadedDS.init_for_gui()

        self.EITDevDataUp= self.device.flag_new_data
        self.frame_cnt_old= -1 #self.liveDS.Frame_cnt

        self.eit_model= EITModelClass()
        self.device.setup.exc_pattern= self.eit_model.InjPattern

        self.replay_play=Flag()
        # setting of the camera
        self.micro_cam=MicroCam()
        self.micro_cam.selectCam(0)
        ## try of drawing a rectangle ...failed...
        # tmp_geo=self.video_frame.geometry()
        # self.video_frame = MyLabel(self)
        # self.video_frame.setCursor(Qt.CrossCursor)
        # self.video_frame.setGeometry(tmp_geo)
        self.up_events=CustomEvents()
        setup_update_event_handlers(self.up_events)

    def link_callbacks_for_interaction_on_device_tab(self):
        """ """
        self.pB_refresh.clicked.connect(self._callback_refresh_device_list)
        self.pB_connect.clicked.connect(self._callback_connect_device)
        self.pB_disconnect.clicked.connect(self._callback_disconnect_device)
        self.pB_get_setup.clicked.connect(self._callback_get_device_setup)
        self.pB_set_setup.clicked.connect(self._callback_set_device_setup)
        self.pB_save_setup.clicked.connect(self._callback_SaveSetup)
        self.pB_load_setup.clicked.connect(self._callback_LoadSetup)
        self.pB_reset.clicked.connect(self._callback_softreset_device)

        self.sBd_freq_min.valueChanged.connect(self._update_device_setup_from_gui)
        self.sBd_freq_max.valueChanged.connect(self._update_device_setup_from_gui)
        self.sB_freq_steps.valueChanged.connect(self._update_device_setup_from_gui)
        self.cB_scale.activated.connect(self._update_device_setup_from_gui)
        self.sBd_frame_rate.valueChanged.connect(self._update_device_setup_from_gui)
        set_comboBox_items(self.cB_scale, [OP_LINEAR.name, OP_LOG.name])


    def link_callbacks_for_interaction_on_measurement_tab(self):
        """ """
        self.pB_start_meas.clicked.connect(self._callback_start_measurement)
        self.pB_stop_meas.clicked.connect(self._callback_stop_measurement)


        self.pB_load_meas_dataset.clicked.connect(self._callback_LoadDataSet)
        self.pB_reconstruction.clicked.connect(self._callback_Reconstruct)
        self.pB_loadRef.clicked.connect(self._callback_loadRef4TD)
        self.pB_Uplot.clicked.connect(self._callback_Uplot)
         
        self.cB_Frame_indx.activated.connect(self._callback_show_frame)
        self.cB_freq_abs_meas.activated.connect(self._callback_show_frame)

        
        self.chB_plot_graph.toggled.connect(self._callback_update_plot)
        self.chB_Uplot.toggled.connect(self._callback_update_plot)
        self.chB_diff.toggled.connect(self._callback_update_plot)
        self.chB_plot_image_rec.toggled.connect(self._callback_update_plot)
        self.cB_rec_method.activated.connect(self._callback_initpyEIT)
        set_comboBox_items(self.cB_rec_method, ['JAC', 'BP', 'GREIT','NN'])

        self.rB_abs_meas.setChecked(True)# init one at least!!!
        self.rB_abs_meas.toggled.connect(self._callback_update_plot)
        self.rB_time_diff_meas.toggled.connect(self._callback_update_plot)
        self.cB_freq_time_meas.activated.connect(self._update_gui_data)
        self.pB_set_ref_time_diff.clicked.connect(self._callback_UpdateRef4TD)
        self.rB_freq_diff_meas.toggled.connect(self._callback_update_plot)
        self.cB_freq_freq_meas_0.activated.connect(self._update_gui_data)
        self.cB_freq_freq_meas_1.activated.connect(self._update_gui_data)

        self.showReal.setChecked(True) # init one at least!!!
        self.showReal.toggled.connect(self._callback_update_plot)
        self.showImag.toggled.connect(self._callback_update_plot)
        self.showMagnitude.toggled.connect(self._callback_update_plot)
        self.showPhase.toggled.connect(self._callback_update_plot)
        self.showAbsValue.toggled.connect(self._callback_update_plot)
        self.chB_y_log.toggled.connect(self._callback_update_plot)

        self.pB_backbegin_replay_meas.clicked.connect(self._callback_ReplayBackBegin)
        self.pB_gotoend_replay_meas.clicked.connect(self._callback_ReplayGotoEnd)
        self.pB_play_replay_meas.clicked.connect(self._callback_ReplayPlay)
        self.pB_pause_replay_meas.clicked.connect(self._callback_ReplayPause)
        self.pB_stop_replay_meas.clicked.connect(self._callback_ReplaysStop)
        self.slider_replay_meas.valueChanged.connect(self._callback_Replay)

    def link_callbacks_for_interaction_on_eitplotter_tab(self):
        """"""
        self.scalePlot_vmax.valueChanged.connect(self._callback_ScalePlot)
        self.scalePlot_vmin.valueChanged.connect(self._callback_ScalePlot)
        self.normalize.toggled.connect(self._callback_ScalePlot) 
        self.pB_set_eit.clicked.connect(self._callback_set_eit) 

    def link_callbacks_for_interaction_on_video_tab(self):
        """ """
        self.cB_video_devices.activated.connect(self._callback_set_cam)
        self.pB_refresh_video_devices.clicked.connect(self._callback_refresh_video_devices)
        self.cB_img_size.activated.connect(self._callback_set_cam)
        self.cB_img_file_ext.activated.connect(self._callback_set_cam)
        set_comboBox_items(self.cB_img_size, list(DEFAULT_IMG_SIZES.keys()))
        set_comboBox_items(self.cB_img_file_ext, list(EXT_IMG.keys()))

    
        
    def _init_multithreading_workers(self):
        # to treat live view of measured data
        self.workers = {}

        workers= {     'live_view'      : [Worker, 0.05, self._poll_live_view ], 
                        'gui_update'    : [Worker,0.1, self._poll_update],
                        # 'serial'        : [Worker,0.01, self._poll_read_serial],
                        'ListenQueue'   : [Worker,0.1, self._listener_queue_in],
                        'video'         : [WorkerCam,0.1, self.ImageUpdateSlot]
                }
        
        # self.LiveViewWorkerSleeptime= 0.05
        # self.workers['live_view']= Worker(self.LiveViewWorkerSleeptime)
        # # self.LiveViewWorker = Worker(self.LiveViewWorkerSleeptime)
        # self.workers['live_view'].progress.connect(self._poll_live_view)
        # self.workers['live_view'].start()
        # self.div_10_cnt=0

        # to actualize the gui
        self.UpdateGuiWorkerSleeptime= 0.1
        self.workers['gui_update'] = Worker(self.UpdateGuiWorkerSleeptime)
        self.workers['gui_update'].progress.connect(self._poll_update)
        self.workers['gui_update'].start()

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

        if self.live_view: # start measuremment
            self.lab_live_view.setText('LIVE')
            self.lab_live_view.setStyleSheet("background-color: green")

            if self.liveDS.frame_cnt != self.frame_cnt_old: # new frame is available
                self.frame_cnt_old =self.liveDS.frame_cnt # reset
                self.compute_measurement()
                self._display_infotext_meas() # show infos about actual frame

                if self.pB_start_video.isChecked():
                    path=os.path.join(self.liveDS.output_dir, f'Frame{self.liveDS.frame_cnt+1:02}')
                    self.micro_cam.save_actual_frame(path)
                # if self.pB_Video.isChecked():

                #     self.micro_cam.save_image_path=self.liveDS.output_dir + os.path.sep +f'Frame{self.liveDS.Frame_cnt+1:02}'
                #     self.updade_video()
                #     self.micro_cam.save_image_path=''
                # self._plot_graphs()
            if self.device.setup.burst>0 and self.liveDS.frame_cnt == self.device.setup.burst:
                self._callback_stop_measurement() # >> self.LiveView = False 
                self._LoadDataSet(self.liveDS.output_dir)
        else:
            self.lab_live_view.setText('OFF')
            self.lab_live_view.setStyleSheet("background-color: red")
            self.meas_progress_bar.setValue(0)

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

        # # testlive Uplot
        # if self.EITDevDataUp != self.device.flag_new_data:
        #     self.EITDevDataUp, self.device.flag_new_data = 0,0
        #     self._update_gui_data()

        self.is_device_unplugged()
            
        # # Automatic detection of device disconnection
        # if self.SerialInterface.Ser.is_open:
        #     if self.SerialInterface.ErrorSerialInterface:
        #         self.SerialInterface.ErrorSerialInterface=''
        #         self._callback_Disconnect()
        #         self.EITDev.add2Log("Critical-" +'Error: ' + self.SerialInterface.ErrorSerialInterface+' :Please reconnect device' )
        #         self._update_gui_data()
        #         showDialog('Error: ' + self.SerialInterface.ErrorSerialInterface + str(datetime.datetime.now()), 'Please reconnect device',  "Critical")

        # if self.pB_start_video.isChecked() and not self.workers['video'].thread_active:
        #     self.workers['video'].start_capture()
        # elif not self.pB_start_video.isChecked() and self.workers['video'].thread_active:
        #     self.workers['video'].stop_capture()

        # look if the recontruction is done
        # self._listener_queue_in() 

    # def _poll_read_serial(self):
    #     """ Called by serial_worker
    #     Read the serial interface
    #     """
    #     self.SerialInterface.pollReadSerial()

    #     if self.replay_play:
    #         self.replay_timeBuffer+=self.SerialWorkerSleeptime
    #         if self.replay_timeBuffer>=self.replay_timeThreshold:
    #             self.replay_timeBuffer=0.0
    #             setSliderReplay(self.Slider_replay_time, next=True, loop=True)

    def is_device_unplugged(self):
        # test if device has been unplugged of turned off
        if self.device.not_connected() and self.device.status_prompt!=self.lab_device_status.text():
            self.up_events.post(UpdateDeviceEvents.device_status,self, self.device)
            show_msgBox('The device has been disconnected!', 'Error: Device disconnected', "Critical")
            self._callback_refresh_device_list()

    ## ======================================================================================================================================================
    ##  Callbacks 
    ## ======================================================================================================================================================
    def _callback_refresh_device_list(self):
        """Refresh the list of available sciospec devices"""
        self.device.get_available_sciospec_devices()
        self.up_events.post(UpdateDeviceEvents.device_list_refreshed,self, self.device)
    
    def _callback_connect_device(self):
        """ Connect with selected sciospec device"""
        device_name= str(self.cB_ports.currentText()) # get actual ComPort
        self.device.connect_device(device_name, baudrate=115200)
        self.up_events.post(UpdateDeviceEvents.device_status,self, self.device)
                    
    def _callback_disconnect_device(self):
        """ Disconnect the sciospec device"""
        self.device.disconnect_device()
        self.up_events.post(UpdateDeviceEvents.device_status,self, self.device)

    def _callback_get_device_setup(self):
        """ Get setup of the sciospec device and display it"""
        self.device.get_setup()
        self.up_events.post(UpdateDeviceEvents.device_setup,self, self.device)

    def _callback_set_device_setup(self):
        """ Set the displayed setup of the sciospec device"""
        self._update_device_setup_from_gui()
        self.device.set_setup()
        self._callback_get_device_setup()

    def _callback_softreset_device(self):
        """ Reset the sciopec device"""
        self.device.software_reset()
        self.up_events.post(UpdateDeviceEvents.device_status,self, self.device)
    
    def _callback_start_measurement(self):

        self._update_device_setup_from_gui()
        p,a= createPath(MEAS_DIR + os.path.sep + self.meas_dataset_name.text(),append_datetime=True)
        self.meas_dataset_name.setText(p[p.rfind(os.path.sep)+1:])
        
        # self.liveDS.initDataSet(self.EITDev.setup, p)
        # self.EITDev.setDataSet(self.liveDS)
        self.device.start_meas(self.meas_dataset_name.text())
        self.live_view.set()
        self.initLiveView()
        self._update_gui_data()

    def _callback_stop_measurement(self):

        self.live_view.clear()
        self.device.stop_meas()
        self.frame_cnt_old =-1 # reset
        self._update_gui_data()

    
    def _callback_SaveSetup(self):
        fileName, _= openFileNameDialog(self,path=SETUPS_DIR)
        if fileName:
            try: 
                sheetName= "Setup Device"
                self.device.saveSetupDevice(fileName, sheetName)
            except PermissionError:
                show_msgBox('please close the setup file \r\nor select an other one', 'Error: no write permision', "Critical")
            self._update_gui_data()
        
    def _callback_LoadSetup(self):
        fileName, _= openFileNameDialog(self,path=SETUPS_DIR)
        if fileName:
            sheetName= "Setup Device"
            self.device.loadSetupDevice(fileName,sheetName)
            self._update_gui_data()
        
    def _callback_LoadDataSet(self): # the call back has to be  witouh arguments!!!
        self._LoadDataSet()

    def _LoadDataSet(self, dirpath:str=None):
        self.pB_start_video.setChecked(False) # deactivate the video liveview!

        if not dirpath: # if dirpath not given then open dialog 
            dirpath, cancel= openDirDialog(self,path=MEAS_DIR)
            if cancel: # Cancelled
                return

        #image >>lokk what for images are in the directory
        formats = list(EXT_IMG.values())
        errors=[0]*len(formats)
        for i, extension in enumerate(formats):
            _, errors[i] =search4FileWithExtension(dirpath, ext=extension)
        

        # if not any(errors):
        #     self.donotdisplayloadedimage= True


        only_files, error = self.loadedDS.LoadDataSet(dirpath)
        if not error:
            #image >>look what for images are in the directory
            formats = list(EXT_IMG.values())
            errors=[0]*len(formats)
            for i, extension in enumerate(formats):
                _, errors[i] =search4FileWithExtension(dirpath, ext=extension)
            # only one sort of imge is save in on directory
            try:
                # setItems_comboBox(self, self.cB_Image_fille_format, items=None, handler=None, reset_box = False, set_index=errors.index(0))
                self.cB_img_file_ext.setCurrentIndex(errors.index(0))
                self._callback_set_cam()
                
                self.displayloadedimage= True
            except ValueError:
                self.displayloadedimage= False

            set_comboBox_items(self.cB_Frame_indx, [i for i in range(len(only_files))])

            set_slider(self.slider_replay_meas,  slider_pos=0, pos_min=0, pos_max=len(only_files)-1, single_step=1)
            self._update_cB_freq(self.loadedDS.freqs_list) # update all comboBox of the frequencies
            self._callback_show_frame()
            self._update_gui_data()
            return 1
        else:
            show_msgBox('Directory empty', 'no File has been found in the selected directory', "Warning")
            return 0
        
    def _callback_show_frame(self):
        """
        Called by the 

        """
        set_slider(self.slider_replay_meas,  slider_pos=self.cB_Frame_indx.currentIndex())
        if self.live_view==False and not self.loadedDS.name==MEAS_DIR[MEAS_DIR.rfind(os.path.sep)+1:]: # only active when live view is inactive and dataset has been loaded
            self._display_infotext_meas()
            self.show_corresponding_image()
            self.compute_measurement()

    def show_corresponding_image(self):
        if self.displayloadedimage:
            path_image= self.loadedDS.frame[self.cB_Frame_indx.currentIndex()].loaded_frame_path
            path_image= path_image[:-4]+self.micro_cam.image_file_ext
            self.updade_video(path=path_image)

    def _display_infotext_meas(self):
        # select right parameter depending on liveview
        if self.live_view==True:
            selectFreq_indx= self.cB_freq_abs_meas.currentIndex()
            Frame = self.liveDS._last_frame[0]
        else:
            selectFrame_indx= self.cB_Frame_indx.currentIndex()
            selectFreq_indx= self.cB_freq_abs_meas.currentIndex()
            Frame = self.loadedDS.frame[selectFrame_indx]
        Meas= Frame.meas[selectFreq_indx]
        # display  info text of the frame
        self.textEdit.setText("\r\n".join(Frame.info_text)) 
        # display meas value in tables      
        set_table_widget( self.tableWidgetvoltages_Z, Meas.voltage_Z)
        set_table_widget(self.tableWidgetvoltages_Z_real, np.real(Meas.voltage_Z))
        set_table_widget( self.tableWidgetvoltages_Z_imag, np.imag(Meas.voltage_Z))

    def initLiveView(self):
        self.textEdit.clear()
        self._update_cB_freq(self.liveDS.freqs_list) # update all comboBox of the frequencies
        if self.pB_start_video.isChecked():
            path=os.path.join(self.liveDS.output_dir, f'Frame{self.liveDS.frame_cnt:02}')
            self.micro_cam.save_actual_frame(path)
        
    def closeEvent(self, event):
        """Generate 'question' dialog on clicking 'X' button in title bar.

        Reimplement the closeEvent() event handler to include a 'Question'
        dialog with options on how to proceed - Save, Close, Cancel buttons
        """
        # reply = QMessageBox.question(
        #     self, "Message",
        #     "Are you sure you want to quit? Any unsaved work will be lost.",
        #     QMessageBox.Save | QMessageBox.Close | QMessageBox.Cancel,
        #     QMessageBox.Save)
        # if reply in [QMessageBox.Save, QMessageBox.Close]:
        #     # dosometthing to save work???
        #     event.accept()
        # elif reply == QMessageBox.Cancel:
        #     event.ignore()

        self.kill_workers()
        
    def kill_workers(self):
        for key, item in self.workers.items():
            item.quit()

    def _callback_Uplot(self):
        pass    

    # def is_flagMeas_Stop(self):
    #     if self.eit_device.flagMeasRunning:
    #         showDialog('Measurement not stopped', 'Measurement has been stopped', "Information")
    #         self._callback_Stop()

    def compute_measurement(self):

        self._get_imaging_parameters()

        self.U= np.random.rand(256,2)
        self.current_labels= ['Random values' for _ in range(4)]
        if self.live_view==True:
            if self.liveDS.frame_cnt>0:
                set_comboBox_items(self.cB_Frame_indx, [self.liveDS.frame_cnt-1], reset_box=False, set_index=-1) # actualize the 
                self.U, self.current_labels= Voltages4Reconstruct(  dataset=self.liveDS,
                                                                    frameIndx= 0,
                                                                    imagingParameters= self.ImagingParameters,
                                                                    EITModel= self.eit_model,
                                                                    liveView=self.live_view)
        else:
            if self.loadedDS.frame_cnt>0:
                path_txt= self.loadedDS.frame[self.cB_Frame_indx.currentIndex()].loaded_frame_path
                path_txt, _ = os.path.splitext(path_txt)
                path_txt= path_txt + EXT_TXT
                self.U, self.current_labels = Voltages4Reconstruct( self.loadedDS, 
                                                                    self.cB_Frame_indx.currentIndex(), 
                                                                    self.ImagingParameters, 
                                                                    self.eit_model, 
                                                                    liveView=self.live_view, 
                                                                    path=path_txt)

        if self.chB_plot_image_rec.isChecked() and self.current_labels.count('Random values')==0:
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
        if self.live_view==True:
            self.liveDS.set_frame_TD_ref() # Frame to use is ._last_frame[0] is the last updated...
        else:
            self.loadedDS.set_frame_TD_ref(self.cB_Frame_indx.currentIndex(), path= path)
   
    def _callback_initpyEIT(self):
        # set some 
        self.eit_model.p=self.eit_p.value()
        self.eit_model.lamb=self.eit_lamda.value()
        self.eit_model.n=self.eit_n.value()
        self.U= np.random.rand(256,2)
        self.current_labels= ['test','test','test','test']

        self.eit_model.set_solver(self.cB_rec_method.currentText())
        self.eit_model.FEMRefinement=self.eit_FEMRefinement.value()
        self.queue_out.put({'cmd': 'initpyEIT', 'eit_model':self.eit_model, 'plot2Gui': self.figure})
        

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
        """"""
        # self._update_device_setup_from_gui()

        # tmp1=[]
        # tmp1.extend(self.ImagingParameters)
        # self._get_imaging_parameters()
        
        
        # cmp1= all(elem1 ==elem for elem1, elem in zip(tmp1, self.ImagingParameters))
        # # logger
        # # if self._verbose>0:
        # #     print(tmp1)
        # #     print(self.ImagingParameters, cmp1, self.Graphs2Plot)
        # if self.live_view==False:
        #     self.compute_measurement()
        # self._update_gui_data()

    def _callback_ReplayBackBegin(self):
        set_slider(self.slider_replay_meas, slider_pos=0)
        
    def _callback_ReplayGotoEnd(self):
        set_slider(self.slider_replay_meas, slider_pos=-1)

    def _callback_ReplayPlay(self):
        self.replay_play.set()
        self.replay_timeThreshold= self.replay_refresh_time.value()
        self.replay_timeBuffer=0.0
        
    def _callback_ReplayPause(self):
        self.replay_play.clear()
        
    def _callback_ReplaysStop(self):
        self.replay_play.clear()
        set_slider(self.slider_replay_meas, slider_pos=0)
        self.replay_timeBuffer=0.0
        
    def _callback_Replay(self):
        self.cB_Frame_indx.setCurrentIndex(self.slider_replay_meas.sliderPosition())
        self._callback_show_frame()

    def _callback_refresh_video_devices(self):

        if self.pB_start_video.isChecked():
            show_msgBox('Stop capture before changing capture device', 'Error', 'Warning' )
        else:
            devices_indx= self.micro_cam.returnCameraIndexes()
            self.cB_video_devices.clear()
            if not devices_indx:
                items=['None video devices']
            else:
                items=[str(item) for item in devices_indx]

            set_comboBox_items( self.cB_video_devices,items)

    def _callback_set_cam(self):
        
        if self.pB_start_video.isChecked():
            show_msgBox('Stop capture before changing capture device', 'Error', 'Warning' )
        else:
            self.micro_cam.selectCam(index=self.cB_video_devices.currentIndex())
            self.micro_cam.setCamProp(size=self.cB_img_size.currentText())
            self.micro_cam.setImagefileFormat(file_ext=self.cB_img_file_ext.currentText())
            
    # def testSerialisOpen(self):
    #     if self.SerialInterface.Ser.is_open:
    #         return 1
    #     else:
    #         showDialog('Please connect a Device', 'Error: no Device connected', "Critical")
    #         return 0
    ## ======================================================================================================================================================
    ##  Setter
    ## ======================================================================================================================================================
    
    def _update_device_setup_from_gui(self):
        ''' Save user entry from Gui in setup of dev'''
        ## Update Measurement Setups
        self.device.setup.set_frame_rate(self.sBd_frame_rate.value())
        self.device.setup.set_burst(self.sB_burst.value())
        self.device.setup.set_exc_amp(self.sBd_exc_amp.value()/1000) # from mA -> A

        freq_max_enable, error=self.device.setup.set_freq_config(
            freq_min=self.sBd_freq_min.value(),
            freq_max=self.sBd_freq_max.value(),
            freq_steps=self.sB_freq_steps.value(),
            freq_scale=self.cB_scale.currentText()
        )
        ## OutputConfig Stamps all to one 
        self.device.setup.set_dhcp(self.chB_dhcp.isChecked() or True)
        self.device.setup.set_exc_stamp(self.chB_exc_stamp.isChecked() or True)
        self.device.setup.set_current_stamp(self.chB_current_stamp.isChecked() or True)
        self.device.setup.set_time_stamp(self.chB_time_stamp.isChecked() or True)
    
        self.up_events.post(UpdateDeviceEvents.device_setup,self, self.device, freq_max_enable, error)
        

        # disableEntryField = self.rB_TimeDiff.isChecked()
        # self.cB_Frequency4FD_0.setDisabled(disableEntryField)
        # self.cB_Frequency4FD_1.setDisabled(disableEntryField)
        # self.cB_Frequency4TD.setDisabled(not disableEntryField)
        # self.pB_UpdateRef4TD.setDisabled(not disableEntryField)

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

        self.ImagingParameters= [   [self.rB_abs_meas.isChecked(),self.cB_freq_abs_meas.currentIndex(), 0],
                                    [self.rB_time_diff_meas.isChecked(), self.cB_freq_time_meas.currentIndex(), 0],
                                    [self.rB_freq_diff_meas.isChecked(), self. cB_freq_freq_meas_0.currentIndex(), self. cB_freq_freq_meas_1.currentIndex()],
                                    [self.showReal.isChecked(), self.showImag.isChecked(), self.showMagnitude.isChecked(), self.showPhase.isChecked(),self.showAbsValue.isChecked()],
                                    [self.chB_y_log.isChecked()]]

        self.Graphs2Plot={ 'image': self.chB_plot_image_rec.isChecked(),
                           'uplot': self.chB_Uplot.isChecked() and self.chB_plot_graph.isChecked(),
                            'diff': self.chB_diff.isChecked() and self.chB_plot_graph.isChecked()}

        if not any(self.Graphs2Plot.values()):
            self.chB_Uplot.setChecked(True)
            self.chB_plot_graph.setChecked(True)
            self.Graphs2Plot['uplot']=True
        # logger
        # if self._verbose>0:
        #     print(self.ImagingParameters)
        #     print(any(self.Graphs2Plot.values()),self.Graphs2Plot.values())

    def _update_cB_freq(self, freqs:List[float]):
        
        for cB in [self.cB_freq_abs_meas, self.cB_freq_time_meas, self. cB_freq_freq_meas_0, self.cB_freq_freq_meas_1]:
            set_comboBox_items(cB, [f for f in freqs])

    # def _update_freq_config(self):

    #     set_freq_max_enable, error=self._update_device_setup_from_gui()

    #     self.sBd_freq_max.setEnabled(set_freq_max_enable)

    #     color= 'red' if error else 'white'
    #     for sB in [self.sBd_freq_min, self.sBd_freq_max, self.sB_freq_steps]: 
    #         sB.setStyleSheet(f"background-color: {color}")
    #     # self.eit_device.setup.set_freq_steps = steps_val
    #     # self.eit_device.setup.freq_config.freq_min = minF_val
    #     # self.eit_device.setup.freq_config.freq_max = maxF_val
    #     # self.eit_device.setup.freq_config.freq_scale= scale_val

    #     # minF_val=self.sBd_freq_min.value()
    #     # maxF_val=self.sBd_freq_max.value()
    #     # steps_val=self.sB_freq_steps.value()
    #     # scale_val=self.cB_scale.currentText()

    #     # Set Steps , also is setps 0 changed in 1
    #     # if steps_val== 0:
    #     #     steps_val=1
        
    #     # Set minF and maxF
    #     # Deactivate maxF if steps 1 is entered, and set minF = maxF
        
    #     # if steps_val == 1:
    #     #     self.sBd_freq_max.setEnabled(False)
    #     #     maxF_val=minF_val
    #     # else:# be sure that minF < maxF
    #     #     self.sBd_freq_max.setEnabled(True) 
    #     #     if maxF_val < minF_val:
    #     #         maxF_val = minF_val
    #     #     elif maxF_val == minF_val:
    #     #         self.sBd_freq_max.setStyleSheet("background-color: red") # indicate user that steps >1  and 
    #     #         self.sBd_freq_min.setStyleSheet("background-color: red")
    #     #         self.sB_freq_steps.setStyleSheet("background-color: red")

    #         #     steps_val = 1
            
    #     # self.eit_device.setup.freq_config.freq_steps = steps_val
    #     # self.eit_device.setup.freq_config.freq_min = minF_val
    #     # self.eit_device.setup.freq_config.freq_max = maxF_val
    #     # self.eit_device.setup.freq_config.freq_scale= scale_val

    #     # self.eit_device.setup.compute_max_frame_rate() # self.EITDev.setup.FrequencyConfig.mkFrequencyList() is also called....

    #     # update directly if not user dont see that change...

    #     post_event(UpdateDeviceEvents.device_setup,self, self.eit_device, set_freq_max_enable, error)

    #     self._update_cB_freq(self.eit_device.setup.freq_config.freqs)
    #     # self._update_gui_data()

    def _update_gui_data(self):
        
        self.canvas.draw()
        # self.queue_in.put(self.EITDev.log)
        # logger
        # if self._verbose:
            # print('_update_gui_data')

        if not self.live_view: 
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
                
            # ## Update SN
            # self.SN.setText(self.eit_device.setup.device_infos.sn_formated)
            
            # ## Update EthernetConfig
            # self.DHCP_Activated.setChecked(self.eit_device.setup.ethernet_config.dhcp)
            # self.IP_Adress.setText(self.eit_device.setup.ethernet_config.ip_formated)
            # self.MAC_Adress.setText(self.eit_device.setup.ethernet_config.mac_formated)

            # ## Update OutputConfig Stamps
            # self.Excitation_Stamp.setChecked(self.eit_device.setup.output_config.exc_stamp)
            # self.Current_Stamp.setChecked(self.eit_device.setup.output_config.current_stamp)
            # self.Time_Stamp.setChecked(self.eit_device.setup.output_config.time_stamp)
            
            # ## Update Measurement Setups
            # self.FrameRate.setValue(self.eit_device.setup.frame_rate)
            # self.Burst.setValue(self.eit_device.setup.burst)
            # self.Current_Amplitude.setValue(self.eit_device.setup.exc_amp*1000) # from A -> mA
            # self.minF.setValue(self.eit_device.setup.freq_config.min_freq_Hz)
            # self.maxF.setValue(self.eit_device.setup.freq_config.max_freq_Hz)
            # self.Steps.setValue(self.eit_device.setup.freq_config.steps)
            # self.cB_Scale.setCurrentText(self.eit_device.setup.freq_config.scale)

            # self.setTableWidget(self.Excitation_pattern,self.eit_device.setup.exc_pattern,0)
        

        ## Update RX frame
        # self.actualFramecnt.setValue(self.liveDS.frame_cnt)
        
        # self.progressBarFrame.setValue(int(self.liveDS.frame[0].meas_frame_cnt/(self.liveDS.frame[0].meas_frame_nb+1)*100))
    
    def ImageUpdateSlot(self, img: QtGui.QImage):
        # self.FeedLabel.setPixmap(QPixmap.fromImage(Image))
        self.image=img
        self.video_frame.setPixmap(QtGui.QPixmap.fromImage(self.image))
        self.image_min=self.image.scaledToHeight(self.video_frame_miniature.height())
        self.video_frame_miniature.setPixmap(QtGui.QPixmap.fromImage(self.image_min))

    def updade_video(self, path=None):

        if path is None:
            img, img_width, img_height= self.micro_cam.getImage()
            print('updade_video')
        else:
            img, img_width, img_height= self.micro_cam.load_saveImage(path)

        self.image = QtGui.QImage(img.data, img_width, img_height, QtGui.QImage.Format_RGB888).rgbSwapped()
        self.video_frame.setPixmap(QtGui.QPixmap.fromImage(self.image))
        self.image_min=self.image.scaledToHeight(self.video_frame_miniature.height())
        self.video_frame_miniature.setPixmap(QtGui.QPixmap.fromImage(self.image_min))
    
    
# Step 1: Create a worker class


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
