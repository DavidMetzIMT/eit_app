#!C:\Anaconda3\envs\py38_app python
# -*- coding: utf-8 -*-
""" Set all the method needed to 

"""

from __future__ import absolute_import, division, print_function
from copy import deepcopy
import os
from  sys import argv, exit
from time import sleep
from logging import getLogger
from multiprocessing import Process
import time
from typing import List

import matplotlib

from matplotlib.pyplot import figure
import numpy as np
# from cv2 import *
from matplotlib.backends.backend_qt5agg import \
    FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import \
    NavigationToolbar2QT as NavigationToolbar
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication
from eit_app.app.event import CustomEvents
from eit_app.eit.computation import ComputeMeas
from eit_app.eit.imaging_type import DATA_TRANSFORMATIONS, IMAGING_TYPE, Imaging

from queue import Queue
from eit_app.eit.rec_abs import RecCMDs, Reconstruction
from eit_app.eit.rec_ai import ReconstructionAI
from eit_app.eit.rec_pyeit import ReconstructionPyEIT

from eit_app.io.video.microcamera import MicroCam
from eit_app.app.gui import Ui_MainWindow as app_gui
from eit_app.app.dialog_boxes import show_msgBox, openFileNameDialog, openDirDialog
from eit_app.eit.model import EITModelClass
from eit_app.eit.reconstruction import ReconstructionPyEIT_old
from eit_app.threads_process.process_queue import NewQueue
# from eit_app.app.newQlabel import MyLabel
from eit_app.eit.plots import PlotImage2D, PlotDiffPlot, PlotType, PlotUPlot, plot_measurements
from eit_app.io.sciospec.device import SWInterface4SciospecDevice
from eit_app.io.sciospec.com_constants import OP_LINEAR, OP_LOG
from eit_app.utils.utils_path import createPath, get_date_time, search_for_file_with_ext
# from eit_app.eit.meas_preprocessing import *
from eit_app.threads_process.threads_worker import Worker, WorkerCam
from eit_app.utils.constants import EXT_TXT, MEAS_DIR, SETUPS_DIR, DEFAULT_IMG_SIZES,EXT_IMG
from eit_app.app.utils import set_comboBox_items, set_table_widget, set_slider
from eit_app.app.update_gui_listener import setup_update_event_handlers, UpdateEvents
from eit_app.utils.flag import CustomFlag, CustomTimer
from eit_app.io.sciospec.meas_dataset import EitMeasurementDataset
from eit_app.utils.log import main_log


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

logger = getLogger(__name__)


class UiBackEnd(QtWidgets.QMainWindow, app_gui):
    
    def __init__(   self,
                    queue_in:NewQueue=None, queue_out:NewQueue=None,
                    image_reconst:ReconstructionPyEIT=None,
                    parent=None):
    
        super().__init__()
        self._initilizated=False
        self.queue_in = queue_in # for multiprocessing
        self.queue_out = queue_out # for multiprocessing
        self.image_reconst=image_reconst # for multiprocessing
        self.setupUi(self) # call the method to setup the UI created with designer
        self._post_init()
    
    def _post_init(self):
        
        _translate = QtCore.QCoreApplication.translate
        # Set app title and logo
        self.setWindowTitle(_translate("MainWindow","EIT aquisition for Sciospec device "+ __version__))
        self.setWindowIcon(QtGui.QIcon('docs/icons/EIT.png'))
        
        self.figure = figure()
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.PlotLayout.addWidget(self.toolbar)
        self.PlotLayout.addWidget(self.canvas)
        self._init_main_objects()

        # link callbacks
        self.link_callbacks_for_interaction_with_device()
        self.link_callbacks_for_interaction_on_measurement_tab()
        self.link_callbacks_for_interaction_on_eitplotter_tab()
        self.link_callbacks_for_interaction_on_video_tab()
        self.comboBox_init()

        self._update_gui_data()
        self._update_device_setup_from_gui()
        self._callback_refresh_device_list() # get actual comports
        self._callback_plots_to_show()
        self._callback_imaging_params_changed()
        self._callback_autosave()
        self._callback_refresh_video_devices()
        self.up_events.post(UpdateEvents.device_status,self, self.device)
        self.up_events.post(UpdateEvents.live_meas_status, self, self.live_meas_status)
        self.up_events.post(UpdateEvents.replay_status, self, self.replay_status)
    
        self._init_multithreading_workers() # init the multithreadings workers
        self._initilizated=True

    def _init_main_objects(self):

        createPath(SETUPS_DIR,append_datetime=False)
        createPath(MEAS_DIR,append_datetime=False) 
        self.data_to_compute= Queue(maxsize=256)
        self.figure_to_plot= Queue(maxsize=256)

        # self._verbose=0
        self.live_meas_status=CustomFlag()
        self.device = SWInterface4SciospecDevice()# create object for serial communication

        # self.get_dataset() = EitMeasurementDataset()
        # self.get_dataset().init_for_gui()
        self.loadedDS = EitMeasurementDataset()
        self.loadedDS.init_for_gui()

        self.EITDevDataUp= self.device.flag_new_data
        self.frame_cnt_old= -1 #self.liveDS.Frame_cnt

        self.eit_model= EITModelClass()
        self.device.setup.exc_pattern= self.eit_model.InjPattern

        self.computing=ComputeMeas(self.device.get_queue_out(),self.figure_to_plot)

        self.replay_status=CustomFlag()
        self.replay=CustomFlag()
        self.replay_timer= CustomTimer()
        self.replay_timer.set_max_cnt(self.sB_replay_refresh_time.value())
        self.replay_timer.set_step(0.05)
        # self.replay_timeBuffer==self.replay_timeThreshold
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

    def comboBox_init(self):

        set_comboBox_items(self.cB_scale, [OP_LINEAR.name, OP_LOG.name])
        set_comboBox_items(self.cB_solver, ['JAC', 'BP', 'GREIT'])
        set_comboBox_items(self.cB_eit_imaging_type, list(IMAGING_TYPE.keys()))
        set_comboBox_items(self.cB_transform_volt, list(DATA_TRANSFORMATIONS.keys())[:4])
        set_comboBox_items(self.cB_img_size, list(DEFAULT_IMG_SIZES.keys()))
        set_comboBox_items(self.cB_img_file_ext, list(EXT_IMG.keys()))
        set_comboBox_items(self.cB_ref_frame_idx, [0])
        self.cB_FREQ_LIST=[self.cB_freq_meas_0, self.cB_freq_meas_1]

    def link_callbacks_for_interaction_on_measurement_tab(self):
        """ """
        self.pB_load_meas_dataset.clicked.connect(self._callback_load_dataset)
         
        self.cB_current_frame_indx.activated.connect(self._callback_current_frame_selected)

        self.chB_plot_graph.toggled.connect(self._callback_plots_to_show)
        self.chB_Uplot.toggled.connect(self._callback_plots_to_show)
        self.chB_diff.toggled.connect(self._callback_plots_to_show)
        self.chB_plot_image_rec.toggled.connect(self._callback_plots_to_show)
        self.chB_y_log.toggled.connect(self._callback_plots_to_show)

        self.cB_solver.activated.connect(self._callback_set_reconstruction)

        self.cB_eit_imaging_type.activated.connect(self._callback_imaging_params_changed)

        self.cB_ref_frame_idx.currentIndexChanged.connect(self._callback_imaging_params_changed)
        
        self.cB_freq_meas_0.activated.connect(self._callback_imaging_params_changed)
        self.cB_freq_meas_1.activated.connect(self._callback_imaging_params_changed)
        self.cB_transform_volt.activated.connect(self._callback_imaging_params_changed)
        self.showAbsValue.toggled.connect(self._callback_imaging_params_changed)

        self.pB_backbegin_replay_meas.clicked.connect(self._callback_ReplayBackBegin)
        self.pB_gotoend_replay_meas.clicked.connect(self._callback_ReplayGotoEnd)
        self.pB_play_replay_meas.clicked.connect(self._callback_ReplayPlay)
        self.pB_pause_replay_meas.clicked.connect(self._callback_ReplayPause)
        self.pB_stop_replay_meas.clicked.connect(self._callback_ReplaysStop)
        self.sB_replay_refresh_time.valueChanged.connect(self._callback_replay_refresh_time_changed)
        self.slider_replay_meas.valueChanged.connect(self._callback_pos_replay_slider_changed)

    def link_callbacks_for_interaction_on_eitplotter_tab(self):
        """"""
        self.scalePlot_vmax.valueChanged.connect(self._callback_ScalePlot)
        self.scalePlot_vmin.valueChanged.connect(self._callback_ScalePlot)
        self.normalize.toggled.connect(self._callback_ScalePlot) 
        self.pB_set_reconstruction.clicked.connect(self._callback_set_reconstruction)
        self.tabW_reconstruction.currentChanged.connect(self._callback_ScalePlot)

    def link_callbacks_for_interaction_on_video_tab(self):
        """ """
        self.cB_video_devices.activated.connect(self._callback_set_cam)
        self.pB_refresh_video_devices.clicked.connect(self._callback_refresh_video_devices)
        self.cB_img_size.activated.connect(self._callback_set_cam)
        self.cB_img_file_ext.activated.connect(self._callback_set_cam)
        

    def _init_multithreading_workers(self):
        # to treat live view of measured data
        self.workers = {}

        workers= {  'live_view'      : [Worker, 0.05, self._poll_live_view ],
                    'update'    : [Worker,0.05, self._poll_update]
                        # 'serial'        : [Worker,0.01, self._poll_read_serial],
                        # 'ListenQueue'   : [Worker,0.1, self._listener_queue_in],
                        # 'video'         : [WorkerCam,0.1, self.ImageUpdateSlot]
                }
        
        for key, data in workers.items():
            self.workers[key]= data[0](data[1])
            self.workers[key].progress.connect(data[2])
            self.workers[key].start()

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
        if self.live_meas_status.has_changed():
            self.up_events.post(UpdateEvents.live_meas_status, self, self.live_meas_status)
            self.live_meas_status.ack_change()
            if self.live_meas_status.is_set():
                self.replay_status.clear()
            
        if self.replay_status.has_changed():
            self.up_events.post( UpdateEvents.replay_status, self, self.replay_status)
            self.replay_status.ack_change()

        if self.live_meas_status.is_set():
            self.up_events.post(
                UpdateEvents.progress_acq_frame,
                self,
                self.get_dataset().frame_cnt,
                self.get_dataset().get_filling()
            )
            self.nb_burst_reached()

        self.replay_pulse()
                
        self.is_device_unplugged()

    def _poll_update(self):
        
        """ Called by UpdateGuiWorker

        In case that the device send the flag devDataUp (e.g. new data recieved)
            >> update the gui
        Also this poll report of device disconnection to the user  """ 
        # self.updade_video()

        # if self.pB_start_video.isChecked() and not self.workers['video'].thread_active:
        #     self.workers['video'].start_capture()
        # elif not self.pB_start_video.isChecked() and self.workers['video'].thread_active:
        #     self.workers['video'].stop_capture()

        # look if the recontruction is done
        # self._listener_queue_in() 
        self.new_data_computed_available()

    def new_data_computed_available(self):
        """"""
        if not self.figure_to_plot.empty():
        
            while not self.figure_to_plot.empty():
                data=self.figure_to_plot.get()
            
            try:
                dataset:EitMeasurementDataset=data['dataset']
                idx_frame= data['idx_frame']
                print(f'plot{dataset.get_idx_frame(idx_frame)}, time {get_date_time()}')
                print(f'plot{dataset.meas_frame[idx_frame].loaded_frame_path}, time {get_date_time()}')
                self.up_events.post(
                    UpdateEvents.info_data_computed,
                    self,
                    self.live_meas_status.is_set(),
                    dataset.get_idx_frame(idx_frame),
                    dataset.get_info()
                )
                self._update_canvas(data)
            except AttributeError:
                pass
        

    def nb_burst_reached(self)-> None:
        """"""
        burst=self.device.setup.get_burst()
        if burst > 0 and self.get_dataset().frame_cnt == burst:
            self._callback_stop_measurement() 
            # self._LoadDataSet(self.get_dataset().output_dir)

    def save_actual_imgframe(self)-> None:
        """"""
        if self.pB_start_video.isChecked():
            path=os.path.join(self.get_dataset().output_dir, f'Frame{self.frame_cnt_old+1:02}')
            self.micro_cam.save_actual_frame(path)

    def is_device_unplugged(self)-> None:
        """Test if device has been unplugged of turned off"""
        if self.device.not_connected() and self.device.status_prompt!=self.lab_device_status.text():
            self.up_events.post(UpdateEvents.device_status,self, self.device)
            show_msgBox('The device has been disconnected!', 'Error: Device disconnected', "Critical")
            self._callback_refresh_device_list()

    def replay_pulse(self):
        if self.replay.is_set() and self.replay_timer.increment():
            set_slider(self.slider_replay_meas, next=True)

    ## ======================================================================================================================================================
    ##  Interaction with device:
    ## ======================================================================================================================================================
    
    def link_callbacks_for_interaction_with_device(self):
        """ """
        self.pB_refresh.clicked.connect(self._callback_refresh_device_list)
        self.pB_connect.clicked.connect(self._callback_connect_device)
        self.pB_disconnect.clicked.connect(self._callback_disconnect_device)
        self.pB_get_setup.clicked.connect(self._callback_get_device_setup)
        self.pB_set_setup.clicked.connect(self._callback_set_device_setup)
        self.pB_reset.clicked.connect(self._callback_softreset_device)
        self.pB_save_setup.clicked.connect(self._callback_save_setup)
        self.pB_load_setup.clicked.connect(self._callback_load_setup)

        self.sBd_freq_min.valueChanged.connect(self._update_device_setup_from_gui)
        self.sBd_freq_max.valueChanged.connect(self._update_device_setup_from_gui)
        self.sB_freq_steps.valueChanged.connect(self._update_device_setup_from_gui)
        self.cB_scale.activated.connect(self._update_device_setup_from_gui)
        self.sBd_frame_rate.valueChanged.connect(self._update_device_setup_from_gui)
        set_comboBox_items(self.cB_scale, [OP_LINEAR.name, OP_LOG.name])
        
        self.pB_start_meas.clicked.connect(self._callback_start_measurement)
        self.pB_stop_meas.clicked.connect(self._callback_stop_measurement)
        self.chB_dataset_autoset.toggled.connect(self._callback_autosave)
    
    def _callback_refresh_device_list(self):
        """Refresh the list of available sciospec devices"""
        self.device.get_available_sciospec_devices()
        self.up_events.post(UpdateEvents.device_list_refreshed,self, self.device)
    
    def _callback_connect_device(self):
        """ Connect with selected sciospec device"""
        device_name= str(self.cB_ports.currentText()) # get actual ComPort
        self.device.connect_device(device_name, baudrate=115200)
        self.up_events.post(UpdateEvents.device_status,self, self.device)
                    
    def _callback_disconnect_device(self):
        """ Disconnect the sciospec device"""
        self.device.disconnect_device()
        self.up_events.post(UpdateEvents.device_status,self, self.device)

    def _callback_get_device_setup(self):
        """ Get setup of the sciospec device and display it"""
        self.device.get_setup()
        self.up_events.post(UpdateEvents.device_setup,self, self.device)

    def _callback_set_device_setup(self):
        """ Set the displayed setup of the sciospec device"""
        self._update_device_setup_from_gui()
        self.device.set_setup()
        self._callback_get_device_setup()

    def _callback_softreset_device(self):
        """ Reset the sciopec device"""
        self.device.software_reset()
        self.up_events.post(UpdateEvents.device_status,self, self.device)
    
    def _callback_start_measurement(self):
        """ Start measurements on sciopec device"""
        self._callback_set_device_setup()
        self.device.start_meas(self.lE_meas_dataset_dir.text())
        self.init_gui_for_live_meas()

    def _callback_stop_measurement(self):
        """ Start measurements on sciopec device"""
        self.device.stop_meas()
        self.live_meas_status.clear()
        self.frame_cnt_old =-1 # reset
    
    def _callback_save_setup(self):
        self.device.save_setup(dir=None)
        
    def _callback_load_setup(self):
        self.device.load_setup()
        self.up_events.post(UpdateEvents.device_setup,self, self.device)

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
    
        self.up_events.post(UpdateEvents.device_setup,self, self.device, freq_max_enable, error)

    def _callback_load_dataset(self): # the call back has to be witouh arguments!!!
        self._load_dataset()

    def _callback_loadRef4TD(self):
        path, cancel= openFileNameDialog(self,path=MEAS_DIR)
        if cancel: # Cancelled
            return
        self._callback_UpdateRef4TD(path=path)    
        
    def _callback_UpdateRef4TD(self, path=None):
        if self.live_meas_status.is_set()==True:
            self.get_dataset().set_frame_TD_ref() # Frame to use is ._last_frame[0] is the last updated...
        else:
            self.loadedDS.set_frame_TD_ref(self.cB_current_frame_indx.currentIndex(), path= path)
   
    def _callback_autosave(self):
        self.device.set_autosave(self.chB_dataset_autoset.isChecked())
        self.up_events.post(UpdateEvents.autosave_changed,self)

    def _callback_set_reconstruction(self):
        # set some 
        rec={0:ReconstructionPyEIT, 1:ReconstructionAI}
        self.eit_model.p=self.eit_p.value()
        self.eit_model.lamb=self.eit_lamda.value()
        self.eit_model.n=self.eit_n.value()
        self.U= np.random.rand(256,2)
        self.labels= ['test','test','test','test']
        self.eit_model.set_solver(self.cB_solver.currentText())
        self.eit_model.FEMRefinement=self.eit_FEMRefinement.value()
        self.computing.set_eit_model(self.eit_model)
        self.computing.set_reconstruction(rec[self.tabW_reconstruction.currentIndex()])

        self.device.put_queue_out(('random', 0, RecCMDs.initialize))
        
    def _callback_Reconstruct(self):
        """"""
        # self.figure.clear()
        # self.image_reconst.imageReconstruct()
        # self.canvas.draw()

    def _callback_ScalePlot(self):
        print('ScalePlot', self.tabW_reconstruction.currentIndex())
        # self.queue_out.put({'cmd': 'setScalePlot', 'vmax':self.scalePlot_vmax.value(), 'vmin': self.scalePlot_vmin.value(), 'normalize':self.normalize.isChecked()})
        # self.image_reconst.setScalePlot(self.scalePlot_vmax.value(), self.scalePlot_vmin.value())
        # self.image_reconst.setNormalize(self.normalize.isChecked())
    
    def _callback_ReplayPlay(self):
        self.replay.set()
        self.replay_timer.reset()

    def _callback_ReplayBackBegin(self):
        set_slider(self.slider_replay_meas, slider_pos=0)
        
    def _callback_ReplayGotoEnd(self):
        set_slider(self.slider_replay_meas, slider_pos=-1)

    def _callback_ReplayPause(self):
        self.replay.clear()
        
    def _callback_ReplaysStop(self):
        self.replay.clear()
        set_slider(self.slider_replay_meas, slider_pos=0)
        self.replay_timer.reset()
        
    def _callback_pos_replay_slider_changed(self):
        idx_frame=self.slider_replay_meas.sliderPosition()
        self.cB_current_frame_indx.setCurrentIndex(idx_frame)
        self._show_current_frame(idx_frame)
    
    def _callback_replay_refresh_time_changed(self):
        self.replay_timer.set_max_cnt(self.sB_replay_refresh_time.value())

    
    def _callback_current_frame_selected(self):
        idx_frame=self.cB_current_frame_indx.currentIndex()
        set_slider(self.slider_replay_meas,  slider_pos=idx_frame)
        self._show_current_frame(idx_frame)

    def _show_current_frame(self, idx_frame:int=0):
        if not self.replay_status.is_set() or self.live_meas_status.is_set:
            show_msgBox('First load a measuremment dataset', 'Replay mode not actvated', 'Warning' )
            return
        self.compute_frame(idx_frame)

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
            set_comboBox_items(self.cB_video_devices,items)

    def _callback_set_cam(self):
        
        if self.pB_start_video.isChecked():
            show_msgBox('Stop capture before changing capture device', 'Error', 'Warning' )
        else:
            self.micro_cam.selectCam(index=self.cB_video_devices.currentIndex())
            self.micro_cam.setCamProp(size=self.cB_img_size.currentText())
            self.micro_cam.setImagefileFormat(file_ext=self.cB_img_file_ext.currentText())
            
    def _callback_imaging_params_changed(self):

        rec_type= self.cB_eit_imaging_type.currentText()
        if rec_type not in list(IMAGING_TYPE.keys()):
            raise Exception(f'The imaging type {rec_type} ist not known')
        transform_volt=self.cB_transform_volt.currentText()
        if transform_volt not in DATA_TRANSFORMATIONS:
            raise Exception(f'The transformation {transform_volt} ist not known')

        idx_freqs=[self.cB_freq_meas_0.currentIndex(), self.cB_freq_meas_1.currentIndex()]
        idx_ref_frame= self.cB_ref_frame_idx.currentIndex()
        # self.pB_set_ref_time_diff.clicked.connect(self._callback_UpdateRef4TD)
        transform_funcs=[
            DATA_TRANSFORMATIONS[transform_volt], 
            DATA_TRANSFORMATIONS['Abs'] if self.showAbsValue.isChecked() else DATA_TRANSFORMATIONS['Identity']]
        # self.cB_transform_volt
        # self.showAbsValue.toggled.connect(self._callback_update_plot)
        
        self.imaging_type:Imaging=IMAGING_TYPE[rec_type](idx_freqs, idx_ref_frame, transform_funcs)

        self.up_events.post(UpdateEvents.freqs_inputs, self, self.imaging_type)

        self.computing.set_computation(self.imaging_type)
        self.computing.set_eit_model(self.eit_model)
        # if not self.live_view.is_set():
        #     self.compute_measurement()

    def _callback_plots_to_show(self):
        self.plots_to_show=[ 
            PlotImage2D(
                is_visible=self.chB_plot_image_rec.isChecked()
                ),
            PlotUPlot(
                is_visible=self.chB_Uplot.isChecked() and self.chB_plot_graph.isChecked(),
                y_axis_log= self.chB_y_log.isChecked()
                ),
            PlotDiffPlot(
                self.chB_diff.isChecked() and self.chB_plot_graph.isChecked(),
                y_axis_log=self.chB_y_log.isChecked()
                )
        ]
        self.computing.set_plotings(self.plots_to_show, self.figure)
        # self.up_events.post(UpdateEvents.plots_to_show, self)

    def _load_dataset(self, dir_path:str=None):
        print('here1')
        if self.pB_start_video.isChecked():
            self.pB_start_video.setChecked(False)
            show_msgBox('Live video stopped', 'Live video still running', 'Information')
        print('here1')
        if self.live_meas_status.is_set():
            show_msgBox('Please stop measurements before loading dataset', 'Live measurements still running', 'Warning')
            return
        print('here1')

        # if not dirpath: # if dirpath not given then open dialog 
        #     dirpath, cancel= openDirDialog(self,path=MEAS_DIR)
        #     if cancel: # Cancelled
        #         return

        # #image >>lokk what for images are in the directory
        # formats = list(EXT_IMG.values())
        # errors=[0]*len(formats)
        # for i, extension in enumerate(formats):
        #     _, errors[i] =search_for_file_with_ext(dirpath, ext=extension)
        
        # if not any(errors):
        #     self.donotdisplayloadedimage= True
        self.replay_status.clear()
        print('here1')
        if not self.get_dataset().load_dataset_dir(dir_path):
            print('here1')
            return
        print('here1')
        self.replay_status.set()
        print('here1')
        
        self.up_events.post(UpdateEvents.device_setup,self, self.device)
        print('here1')
        self.up_events.post(UpdateEvents.dataset_loaded,self, self.get_dataset())
        print('here1')
   

        # if not error:
        #     #image >>look what for images are in the directory
        #     formats = list(EXT_IMG.values())
        #     errors=[0]*len(formats)
        #     for i, extension in enumerate(formats):
        #         _, errors[i] =search_for_file_with_ext(dirpath, ext=extension)
        #     # only one sort of imge is save in on directory
        #     try:
        #         # setItems_comboBox(self, self.cB_Image_fille_format, items=None, handler=None, reset_box = False, set_index=errors.index(0))
        #         self.cB_img_file_ext.setCurrentIndex(errors.index(0))
        #         self._callback_set_cam()
        #         self.displayloadedimage= True
        #     except ValueError:
        #         self.displayloadedimage= False
        
        self.compute_frame(idx_frame=0)
        print('here1')
            
            # self._update_gui_data()
            
        # else:
        #     show_msgBox('Directory empty', 'no File has been found in the selected directory', "Warning")
    
    def compute_frame(self, idx_frame:int=0):
        self.device.put_queue_out((self.get_dataset(),idx_frame, RecCMDs.rec))

    def show_corresponding_image(self):
        if self.displayloadedimage:
            path_image= self.loadedDS.rx_meas_frame[self.cB_current_frame_indx.currentIndex()].loaded_frame_path
            path_image= path_image[:-4]+self.micro_cam.image_file_ext
            self.updade_video(path=path_image)

    def init_gui_for_live_meas(self):
        self.live_meas_status.set()
        self.frame_cnt_old=-1
        self.textEdit.clear()
        # self._update_cB_freq(self.get_dataset().freqs_list) # update all comboBox of the frequencies
        self.save_actual_imgframe()

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
        for _, item in self.workers.items():
            item.quit()

    def get_dataset(self)-> EitMeasurementDataset:
        return self.device.get_dataset()

    def _test_compute(self):
        self.device.put_queue_out(('random', 0, RecCMDs.rec))

    def make_ploting(self, data_to_plot):

        # 'self.U, self.labels=data_to_plot['U'], data_to_plot['labels']

        if self.chB_plot_image_rec.isChecked() and self.labels.count('Random values')==0:
            self.queue_out.put({'cmd': 'recpyEIT', 'v1':self.U[:,1], 'v0': self.U[:,0]})
        else:
            self._update_canvas()

    def _update_canvas(self, data):
        """"""


        dataset:EitMeasurementDataset=data['dataset']
        idx_frame=data['idx_frame']
        voltages= dataset.get_voltages(idx_frame, 0)
        if voltages is not None:
            set_table_widget(self.tableWidgetvoltages_Z, voltages)
            # set_table_widget(self.tableWidgetvoltages_Z_real, np.real(voltages))
            # set_table_widget(self.tableWidgetvoltages_Z_imag, np.imag(voltages))


        t = time.time()
        self.figure = plot_measurements(self.plots_to_show, self.figure, data['U'], data['labels'], data['eit_model'])
        self.canvas.draw()
        elapsed = time.time() - t
        
        if isinstance(dataset, EitMeasurementDataset):
            print(f'plot of frame #{dataset.get_idx_frame(idx_frame)}, time {get_date_time()}, lasted {elapsed}')

    ## ======================================================================================================================================================
    ##  Setter
    ## ======================================================================================================================================================
    
    def _listener_queue_in(self):
        if not self.queue_in.empty():
            #print(self.queue_in.to_list())
            data=self.queue_in.get()
            print('CMD on queue:',data['cmd'])
            if data['cmd']=='updatePlot':
                print('updatePlot')
                self.image_reconst =data['rec']
                self._update_canvas()
                
    def _update_cB_freq(self, freqs:List[float]):
        [set_comboBox_items(cB, [f for f in freqs]) for cB in self.cB_FREQ_LIST]

    def _update_gui_data(self):
        self.canvas.draw()
        if not self.live_meas_status.is_set(): 
            scrollbar = self.textEditlog.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    
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


# def _poll_process4reconstruction(queue_in=None, queue_out=None, rec:ReconstructionPyEIT=ReconstructionPyEIT()):

#     while True :
#         sleep(0.1)
#         rec.pollCallback(queue_in=queue_in, queue_out=queue_out)

def main():
    main_log()
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    # rec= ReconstructionPyEIT()
    # ui2rec_queue = NewQueue()
    app = QApplication(argv)
    # rec2ui_queue = NewQueue()
    app.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    # ui = UiBackEnd(queue_in=rec2ui_queue, queue_out=ui2rec_queue, image_reconst=rec)
    ui = UiBackEnd()
    ui.show()
    # p = Process(target=_poll_process4reconstruction, args=(ui2rec_queue,rec2ui_queue,rec))
    # p.daemon=True
    # p.start()
    exit(app.exec_())  

if __name__ == "__main__":
    # from viztracer import VizTracer
    
    # with VizTracer() as tracer:
    main()
    # 
