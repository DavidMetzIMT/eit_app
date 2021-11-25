#!C:\Anaconda3\envs\py38_app python
# -*- coding: utf-8 -*-
""" Set all the method needed to  

"""

from __future__ import absolute_import, division, print_function
import logging
import os
from  sys import argv, exit
from logging import getLogger
import time
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
from eit_app.eit.rec_abs import RecCMDs
from eit_app.eit.rec_ai import ReconstructionAI
from eit_app.eit.rec_pyeit import ReconstructionPyEIT
from eit_app.io.video.microcamera import MicroCam, VideoCaptureModule
from eit_app.app.gui import Ui_MainWindow as app_gui
from eit_app.app.dialog_boxes import show_msgBox, openFileNameDialog
from eit_app.eit.eit_model import EITModelClass


# from eit_app.app.newQlabel import MyLabel
from eit_app.eit.plots import PlotImage2D, PlotDiffPlot, PlotUPlot, plot_measurements, plot_rec
from eit_app.io.sciospec.device import IOInterfaceSciospec
from eit_app.io.sciospec.com_constants import OP_LINEAR, OP_LOG
from eit_app.utils.utils_path import createPath, get_date_time
# from eit_app.eit.meas_preprocessing import *
from eit_app.threads_process.threads_worker import CustomWorker
from eit_app.utils.constants import EXT_TXT, MEAS_DIR, DEFAULT_IMG_SIZES,EXT_IMG, SNAPSHOT_DIR
from eit_app.app.utils import set_comboBox_items, set_table_widget, set_slider
from eit_app.app.update_gui_listener import setup_update_event_handlers, UpdateEvents
from glob_utils.flags.flag import CustomFlag, CustomTimer
from eit_app.io.sciospec.meas_dataset import EitMeasurementDataset
from glob_utils.log.log import change_level_logging, main_log


# Ensure using PyQt5 backend
matplotlib.use('QT5Agg')

__author__ = "David Metz"
__copyright__ = "Copyright 2021, microEIT"
__credits__ = ["David Metz"]
__license__ = "GPL"
__version__ = "2.0.0"
__maintainer__ = "David Metz"
__email__ = "d.metz@tu-bs.de"
__status__ = "Production"

logger = getLogger(__name__)




log_level={
    'DEBUG':logging.DEBUG,
    'INFO':logging.INFO,
    'WARNING':logging.WARNING
}



class UiBackEnd(QtWidgets.QMainWindow, app_gui):
    
    def __init__(   self):
        super().__init__()
        self._initilizated=CustomFlag()
        self.setupUi(self) # call the method to setup the UI created with designer
        self._post_init()
        self._initilizated.set()
    
    def _post_init(self):
        
        _translate = QtCore.QCoreApplication.translate
        # Set app title
        self.setWindowTitle(_translate("MainWindow","EIT aquisition for Sciospec device "+ __version__))
        
        self.figure_graphs = figure()
        self.canvas_graphs = FigureCanvas(self.figure_graphs)
        self.toolbar_graphs = NavigationToolbar(self.canvas_graphs, self)
        self.layout_graphs.addWidget(self.toolbar_graphs)
        self.layout_graphs.addWidget(self.canvas_graphs)

        self.figure_rec = figure()
        self.canvas_rec = FigureCanvas(self.figure_rec)
        self.toolbar_rec = NavigationToolbar(self.canvas_rec, self)
        self.layout_rec.addWidget(self.toolbar_rec)
        self.layout_rec.addWidget(self.canvas_rec)

        self._init_main_objects()

        # link callbacks
        self._link_callbacks()

        self.comboBox_init()

        # self._update_gui_data()
        self._update_log()
        self._update_device_setup_from_gui()
        self._callback_refresh_device_list()
        self._callback_plots_to_show()
        self._callback_imaging_params_changed()
        self._callback_autosave()
        self._callback_refresh_capture_devices()
        self.up_events.post(UpdateEvents.device_status,self, self.io_interface)
        self.up_events.post(UpdateEvents.live_meas_status, self, self.live_meas_status)
        self.up_events.post(UpdateEvents.replay_status, self, self.replay_status)
    
        self._init_multithreading_workers()
        

    def _init_main_objects(self):

 
        createPath(MEAS_DIR,append_datetime=False)
        createPath(SNAPSHOT_DIR,append_datetime=False)

        self.dataset = EitMeasurementDataset()

        self.io_interface = IOInterfaceSciospec()
        
        self.eit_model= EITModelClass()
        self.io_interface.setup.exc_pattern= self.eit_model.InjPattern

        self.data_to_compute= Queue(maxsize=256)
        self.figure_to_plot= Queue(maxsize=256)
        self.computing=ComputeMeas(self.io_interface.getQueueOut(),self.figure_to_plot)

        self.live_meas_status=CustomFlag()
        self.replay_status=CustomFlag()
        self.replay=CustomFlag()
        self.replay_timer= CustomTimer(max_time=self.sB_replay_time.value(), time_stp=0.05)
        self.live_capture=CustomFlag()
        # setting of the camera
        self.captured_imgs= Queue(maxsize=256)
        self.capture_module=VideoCaptureModule(MicroCam(),self.io_interface.get_queue_video_module(),self.captured_imgs)
        # self.device.set_queue_out_video_module(self.capture_module.get_queue_in())
        self.up_events=CustomEvents()
        setup_update_event_handlers(self.up_events)

    def comboBox_init(self):
        """ """
        set_comboBox_items(self.cB_log_level, list(log_level.keys()))
        set_comboBox_items(self.cB_scale, [OP_LINEAR.name, OP_LOG.name])
        set_comboBox_items(self.cB_solver, ['JAC', 'BP', 'GREIT'])
        set_comboBox_items(self.cB_eit_imaging_type, list(IMAGING_TYPE.keys()))
        set_comboBox_items(self.cB_transform_volt, list(DATA_TRANSFORMATIONS.keys())[:4])
        set_comboBox_items(self.cB_img_size, list(DEFAULT_IMG_SIZES.keys()), set_index=-1)
        set_comboBox_items(self.cB_img_file_ext, list(EXT_IMG.keys()))
        set_comboBox_items(self.cB_ref_frame_idx, [0])

    def _link_callbacks(self):
        """ """
        self.cB_log_level.activated.connect(self._update_log)

        # device relative callbacks
        self.pB_refresh.clicked.connect(self._callback_refresh_device_list)
        self.pB_connect.clicked.connect(self._callback_connect_device)
        self.pB_disconnect.clicked.connect(self._callback_disconnect_device)
        self.pB_get_setup.clicked.connect(self._callback_get_device_setup)
        self.pB_set_setup.clicked.connect(self._callback_set_device_setup)
        self.pB_reset.clicked.connect(self._callback_softreset_device)
        self.pB_save_setup.clicked.connect(self._callback_save_setup)
        self.pB_load_setup.clicked.connect(self._callback_load_setup)
        self.pB_start_meas.clicked.connect(self._callback_start_measurement)
        self.pB_stop_meas.clicked.connect(self._callback_stop_measurement)

        self.sBd_freq_min.valueChanged.connect(self._update_device_setup_from_gui)
        self.sBd_freq_max.valueChanged.connect(self._update_device_setup_from_gui)
        self.sB_freq_steps.valueChanged.connect(self._update_device_setup_from_gui)
        self.cB_scale.activated.connect(self._update_device_setup_from_gui)
        self.sBd_frame_rate.valueChanged.connect(self._update_device_setup_from_gui)
        
        self.chB_dataset_autoset.toggled.connect(self._callback_autosave)
        self.chB_dataset_save_img.toggled.connect(self._callback_autosave)

        # frame plot/ 
        self.cB_current_idx_frame.activated.connect(self._callback_current_frame_selected)
        self.chB_plot_graph.toggled.connect(self._callback_plots_to_show)
        self.chB_Uplot.toggled.connect(self._callback_plots_to_show)
        self.chB_diff.toggled.connect(self._callback_plots_to_show)
        self.chB_plot_image_rec.toggled.connect(self._callback_plots_to_show)
        self.chB_y_log.toggled.connect(self._callback_plots_to_show)

        # loading maesuremenst / replay
        self.pB_load_meas_dataset.clicked.connect(self._callback_load_dataset)
        self.pB_replay_back_begin.clicked.connect(self._callback_replay_back_begin)
        self.pB_replay_goto_end.clicked.connect(self._callback_replay_goto_end)
        self.pB_replay_play.clicked.connect(self._callback_replay_play)
        self.pB_replay_pause.clicked.connect(self._callback_replay_pause)
        self.pB_replay_stop.clicked.connect(self._callback_replay_stop)
        self.sB_replay_time.valueChanged.connect(self._callback_replay_time_changed)
        self.slider_replay.valueChanged.connect(self._callback_replay_slider_changed)

        #EIT reconstruction
        self.pB_set_reconstruction.clicked.connect(self._callback_set_reconstruction)
        self.tabW_reconstruction.currentChanged.connect(self._callback_ScalePlot)
        ## pyeit
        self.scalePlot_vmax.valueChanged.connect(self._callback_ScalePlot)
        self.scalePlot_vmin.valueChanged.connect(self._callback_ScalePlot)
        self.normalize.toggled.connect(self._callback_ScalePlot) 
        # self.cB_solver.activated.connect(self._callback_set_reconstruction)

        # eit imaging 
        self.cB_eit_imaging_type.activated.connect(self._callback_imaging_params_changed)
        self.cB_ref_frame_idx.currentIndexChanged.connect(self._callback_imaging_params_changed)
        self.cB_freq_meas_0.activated.connect(self._callback_imaging_params_changed)
        self.cB_freq_meas_1.activated.connect(self._callback_imaging_params_changed)
        self.cB_transform_volt.activated.connect(self._callback_imaging_params_changed)
        self.showAbsValue.toggled.connect(self._callback_imaging_params_changed)

        # Video capture
        self.pB_refresh_video_devices.clicked.connect(self._callback_refresh_capture_devices)
        self.pB_capture_start.clicked.connect(self._callback_live_capture_start)
        self.pB_capture_stop.clicked.connect(self._callback_live_capture_stop)
        self.pB_capture_snapshot.clicked.connect(self._callback_capture_snapshot)
        self.cB_video_devices.activated.connect(self._callback_set_capture_device)
        self.cB_img_size.activated.connect(self._callback_set_capture_device)
        self.cB_img_file_ext.activated.connect(self._callback_set_capture_device)

    def _init_multithreading_workers(self):
        # to treat live view of measured data
        self.workers = {}

        workers= {  'live_view'      : [CustomWorker, 0.05, self._poll_live_view],
                    'update'    : [CustomWorker,0.05, self._poll_update]
                        # 'serial'        : [Worker,0.01, self._poll_read_serial],
                        # 'ListenQueue'   : [Worker,0.1, self._listener_queue_in],
                    # 'video'         : [CustomWorker, 0.1, self._poll_capture, False]
                }
        
        for key, data in workers.items():
            self.workers[key]= data[0](data[1])
            self.workers[key].progress.connect(data[2])
            self.workers[key].start()
            self.workers[key].start_polling()

    def _update_log(self):
        change_level_logging(level=log_level[self.cB_log_level.currentText()])

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
        # print(f'live:{self.live_meas_status.is_set()}, replay:{self.replay_status.is_set()}')
        if self.live_meas_status.has_changed():
            self.up_events.post(UpdateEvents.live_meas_status, self, self.live_meas_status)
            self.live_meas_status.ack_change()
            if self.live_meas_status.is_set():
                self.replay_status.clear()
                self.capture_module.set_meas()
            else:
                self.capture_module.set_idle()
                self._callback_live_capture_start(look_memory_flag=True)

        if self.replay_status.has_changed():
            self.up_events.post( UpdateEvents.replay_status, self, self.replay_status)
            self.replay_status.ack_change()

        if self.live_meas_status.is_set():
            self.up_events.post(UpdateEvents.progress_frame, self,self.get_current_frame_cnt(), self.get_dataset().get_filling())
            self.nb_burst_reached()

        self.replay_pulse()
                
        self.is_device_unplugged()

    def _poll_update(self):
        
        """ Called by UpdateGuiWorker
        In case that the device send the flag devDataUp (e.g. new data recieved)
            >> update the gui
        Also this poll report of device disconnection to the user  """ 

        self.is_new_computed_data()
        self.is_new_captured_image()

    
    def is_new_computed_data(self):
        """"""
        if self.figure_to_plot.empty():
            return
            
        while not self.figure_to_plot.empty():
            data=self.figure_to_plot.get()

        try:
            dataset:EitMeasurementDataset=data['dataset']
            idx_frame= data['idx_frame']

            if dataset == 'random':
                self._update_canvas(data)
                return

            # print(f'plot{dataset.get_idx_frame(idx_frame)}, time {get_date_time()}')
            # print(f'plot{dataset.meas_frame[idx_frame].loaded_frame_path}, time {get_date_time()}')
            self.up_events.post(
                UpdateEvents.info_data_computed,
                self,
                self.live_meas_status,
                dataset.get_idx_frame(idx_frame),
                dataset.get_info(idx_frame)
            )
            self._update_canvas(data)
        except AttributeError as e:
            logger.error(f'new computed data not displayed : source ({e})')
    
    def is_new_captured_image(self):
        """"""
        if not self.captured_imgs.empty():
            while not self.captured_imgs.empty():
                image:QtGui.QImage=self.captured_imgs.get()
            self.display_image(image)

    def nb_burst_reached(self)-> None:
        """"""
        burst=self.io_interface.setup.get_burst()
        if burst > 0 and self.get_dataset().frame_cnt == burst:
            self._callback_stop_measurement() 

    def is_device_unplugged(self)-> None:
        """Test if device has been unplugged of turned off"""
        if self.io_interface._not_connected() and self.io_interface.status_prompt!=self.lab_device_status.text():
            self.up_events.post(UpdateEvents.device_status,self, self.io_interface)
            show_msgBox('The device has been disconnected!', 'Error: Device disconnected', "Critical")
            self._callback_refresh_device_list()

    def replay_pulse(self):
        if self.replay.is_set() and self.replay_timer.increment():
            set_slider(self.slider_replay, next=True, loop=True)

    ## ======================================================================================================================================================
    ##  Interaction with device:
    ## ======================================================================================================================================================
    
    def _callback_refresh_device_list(self):
        """Refresh the list of available sciospec devices"""
        self.io_interface.getAvailableSciospecDevices()
        self.up_events.post(UpdateEvents.device_list_refreshed,self, self.io_interface)
    
    def _callback_connect_device(self):
        """ Connect with selected sciospec device"""
        device_name= str(self.cB_ports.currentText()) # get actual ComPort
        self.io_interface.connectSciospecDevice(device_name, baudrate=115200)
        self.up_events.post(UpdateEvents.device_status,self, self.io_interface)
                    
    def _callback_disconnect_device(self):
        """ Disconnect the sciospec device"""
        self.io_interface.disconnectSciospecDevice()
        self.up_events.post(UpdateEvents.device_status,self, self.io_interface)

    def _callback_get_device_setup(self):
        """ Get setup of the sciospec device and display it"""
        self.io_interface.get_setup()
        self.up_events.post(UpdateEvents.device_setup,self, self.io_interface)

    def _callback_set_device_setup(self):
        """ Set the displayed setup of the sciospec device"""
        self._update_device_setup_from_gui()
        self.io_interface.set_setup()
        self._callback_get_device_setup()

    def _callback_softreset_device(self):
        """ Reset the sciopec device"""
        self.io_interface.software_reset()
        self.up_events.post(UpdateEvents.device_status,self, self.io_interface)
    
    def _callback_start_measurement(self):
        """ Start measurements on sciopec device"""
        self._callback_set_device_setup()
        if self.io_interface.start_meas(self.lE_meas_dataset_dir.text()):
            self.init_gui_for_live_meas()

    def _callback_stop_measurement(self):
        """ Start measurements on sciopec device"""
        self.io_interface.stop_meas()
        self.live_meas_status.clear()
        # self.frame_cnt_old =-1 # reset
    
    def _callback_save_setup(self):
        self.io_interface.save_setup(dir=None)
        
    def _callback_load_setup(self):
        self.io_interface.load_setup()
        self.up_events.post(UpdateEvents.device_setup,self, self.io_interface)

    def _update_device_setup_from_gui(self):
        ''' Save user entry from Gui in setup of dev'''
        ## Update Measurement Setups
        self.io_interface.setup.set_frame_rate(self.sBd_frame_rate.value())
        self.io_interface.setup.set_burst(self.sB_burst.value())
        self.io_interface.setup.set_exc_amp(self.sBd_exc_amp.value()/1000) # from mA -> A

        freq_max_enable, error=self.io_interface.setup.set_freq_config(
            freq_min=self.sBd_freq_min.value(),
            freq_max=self.sBd_freq_max.value(),
            freq_steps=self.sB_freq_steps.value(),
            freq_scale=self.cB_scale.currentText()
        )
        ## OutputConfig Stamps all to one
        self.io_interface.setup.set_dhcp(self.chB_dhcp.isChecked() or True)
        self.io_interface.setup.set_exc_stamp(self.chB_exc_stamp.isChecked() or True)
        self.io_interface.setup.set_current_stamp(self.chB_current_stamp.isChecked() or True)
        self.io_interface.setup.set_time_stamp(self.chB_time_stamp.isChecked() or True)
    
        self.up_events.post(UpdateEvents.device_setup,self, self.io_interface, freq_max_enable, error)

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
            self.get_dataset().set_frame_TD_ref(self.cB_current_idx_frame.currentIndex(), path= path)
   
    def _callback_autosave(self):
        self.io_interface.setAutosave(self.chB_dataset_autoset.isChecked(), self.chB_dataset_save_img.isChecked())
        self.up_events.post(UpdateEvents.autosave_changed,self)

    def _callback_set_reconstruction(self):
        # set some 
        rec={
            0:ReconstructionPyEIT,
            1:ReconstructionAI
        }
        self.eit_model.p=self.eit_p.value()
        self.eit_model.lamb=self.eit_lamda.value()
        self.eit_model.n=self.eit_n.value()
        self.U= np.random.rand(256,2)
        self.labels= ['test','test','test','test']
        self.eit_model.set_solver(self.cB_solver.currentText())
        self.eit_model.FEMRefinement=self.eit_FEMRefinement.value()
        self.computing.set_eit_model(self.eit_model)
        self.computing.set_reconstruction(rec[self.tabW_reconstruction.currentIndex()])

        self.io_interface.putQueueOut(('random', 0, RecCMDs.initialize))
        

    def _callback_ScalePlot(self):
        print('ScalePlot', self.tabW_reconstruction.currentIndex())
        # self.queue_out.put({'cmd': 'setScalePlot', 'vmax':self.scalePlot_vmax.value(), 'vmin': self.scalePlot_vmin.value(), 'normalize':self.normalize.isChecked()})
        # self.image_reconst.setScalePlot(self.scalePlot_vmax.value(), self.scalePlot_vmin.value())
        # self.image_reconst.setNormalize(self.normalize.isChecked())
    
    def _callback_replay_play(self):
        self.replay.set()
        self.replay_timer.reset()

    def _callback_replay_back_begin(self):
        set_slider(self.slider_replay, slider_pos=0)
        
    def _callback_replay_goto_end(self):
        set_slider(self.slider_replay, slider_pos=-1)

    def _callback_replay_pause(self):
        self.replay.clear()
        
    def _callback_replay_stop(self):

        self.replay.clear()
        self._callback_replay_back_begin()
        self.replay_timer.reset()
        
    def _callback_replay_slider_changed(self):
        idx_frame=self.slider_replay.sliderPosition()
        self.cB_current_idx_frame.setCurrentIndex(idx_frame)
        self._show_current_frame(idx_frame)
    
    def _callback_replay_time_changed(self):
        self.replay_timer.set_max_time(self.sB_replay_time.value())

    def _callback_current_frame_selected(self):
        idx_frame=self.cB_current_idx_frame.currentIndex()
        set_slider(self.slider_replay,  slider_pos=idx_frame)
        self._show_current_frame(idx_frame)

    def _show_current_frame(self, idx_frame:int=0):

        if not self.replay_status.is_set() or self.live_meas_status.is_set():
            show_msgBox('First load a measuremment dataset', 'Replay mode not activated', 'Warning' )
            return
        self.compute_frame(idx_frame)

    def _callback_live_capture_start(self, look_memory_flag:bool=False):
        if self.live_meas_status.is_set():
            show_msgBox('First stop measurement', 'Measurement is running', 'Warning' )
            return
        if look_memory_flag and not self.live_capture.is_set():
            return
        self.capture_module.set_live()
        self.live_capture.set()
        
        
    def _callback_live_capture_stop(self, memory_flag:bool=False):
        if self.live_meas_status.is_set():
            show_msgBox('First stop measurement', 'Measurement is running', 'Warning' )
            return
        self.capture_module.set_idle()
        if not memory_flag:
            self.live_capture.clear()

    def _callback_capture_snapshot(self):
        """"""
        self.capture_module.save_image_now(os.path.join(SNAPSHOT_DIR,f'Snapshot_{get_date_time()}'))
        
    def _callback_refresh_capture_devices(self):
        capture_devices= self.capture_module.get_devices_available()
        dev_names=list(capture_devices.keys())
        set_comboBox_items(self.cB_video_devices,dev_names)

    def _callback_set_capture_device(self):
        self._callback_set_capture_device2()
        # self._callback_set_capture_device2()
    def _callback_set_capture_device2(self):
        if self.live_meas_status.is_set():
            show_msgBox('First stop measurement', 'Measurement is running', 'Warning' )
            return
        self._callback_live_capture_stop(memory_flag=True)
        self.capture_module.select_device(name=self.cB_video_devices.currentText())
        self.capture_module.set_image_size(size=self.cB_img_size.currentText())
        self.capture_module.set_image_file_format(file_ext=self.cB_img_file_ext.currentText())
        self._callback_live_capture_start(look_memory_flag=True)
        
            
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
        self.computing.set_plotings(self.plots_to_show, self.figure_graphs)
        self.up_events.post(UpdateEvents.plots_to_show, self)

    def _load_dataset(self, dir_path:str=None):

        if self.live_capture.is_set():
            self._callback_live_capture_stop()
            show_msgBox('Live video stopped', 'Live video still running', 'Information')
        if self.live_meas_status.is_set():
            show_msgBox('Please stop measurements before loading dataset', 'Live measurements still running', 'Warning')
            return
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
        if not self.get_dataset().load_dataset_dir(dir_path):
            return
        self.replay_status.set()
        self.up_events.post(UpdateEvents.device_setup,self, self.io_interface)
        self.up_events.post(UpdateEvents.dataset_loaded,self, self.get_dataset())
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
        # else:
        #     show_msgBox('Directory empty', 'no File has been found in the selected directory', "Warning")
    
    def compute_frame(self, idx_frame:int=0):
        self.io_interface.putQueueOut((self.get_dataset(),idx_frame, RecCMDs.reconstruct))

    def show_corresponding_image(self):
        path_image= self.get_dataset().rx_meas_frame[self.cB_current_idx_frame.currentIndex()].frame_path
        path_image= path_image[:-4]+self.capture_module.image_file_ext
        self.updade_video(path=path_image)

    def init_gui_for_live_meas(self):
        self.up_events.post(UpdateEvents.info_data_computed,self, self.live_meas_status, 0, '')
        self.live_meas_status.set()
        # self.frame_cnt_old=-1
        # self._update_cB_freq(self.get_dataset().freqs_list) # update all comboBox of the frequencies
        # self.save_actual_imgframe()

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
        return self.io_interface.getDataset()
    
    def get_current_frame_cnt(self)-> int:
        return self.get_dataset().get_frame_cnt()

    def _test_compute(self):
        self.io_interface.putQueueOut(('random', 0, RecCMDs.reconstruct))

    # def make_ploting(self, data_to_plot):

    #     # 'self.U, self.labels=data_to_plot['U'], data_to_plot['labels']

    #     if self.chB_plot_image_rec.isChecked() and self.labels.count('Random values')==0:
    #         self.queue_out.put({'cmd': 'recpyEIT', 'v1':self.U[:,1], 'v0': self.U[:,0]})
    #     else:
    #         self._update_canvas()

    def _update_canvas(self, data):
        """"""
        try :
            dataset:EitMeasurementDataset=data['dataset']
            idx_frame=data['idx_frame']

            t = time.time()
            self.figure_rec=plot_rec(self.plots_to_show, self.figure_rec, data)
            self.canvas_rec.draw()
            self.figure_graphs = plot_measurements(self.plots_to_show, self.figure_graphs, data)
            self.canvas_graphs.draw()
            elapsed = time.time() - t

            if dataset=='random':
                return

            voltages= dataset.get_voltages(idx_frame, 0)
            if voltages is not None:
                set_table_widget(self.tableWidgetvoltages_Z, voltages)
                # set_table_widget(self.tableWidgetvoltages_Z_real, np.real(voltages))
                # set_table_widget(self.tableWidgetvoltages_Z_imag, np.imag(voltages))
            
            if isinstance(dataset, EitMeasurementDataset):
                print(f'plot of frame #{dataset.get_idx_frame(idx_frame)}, time {get_date_time()}, lasted {elapsed}')
        except BaseException as e:
            logger.error(f'Error _update_canvas: {e}')

    ## ======================================================================================================================================================
    ##  Setter
    ## ======================================================================================================================================================
    
    # def _listener_queue_in(self):
    #     if not self.queue_in.empty():
    #         #print(self.queue_in.to_list())
    #         data=self.queue_in.get()
    #         print('CMD on queue:',data['cmd'])
    #         if data['cmd']=='updatePlot':
    #             print('updatePlot')
    #             self.image_reconst =data['rec']
    #             self._update_canvas()
                
    # def _update_cB_freq(self, freqs:List[float]):
    #     [set_comboBox_items(cB, [f for f in freqs]) for cB in self.cB_FREQ_LIST]

    # def _update_gui_data(self):
    #     self.canvas.draw()
    #     if not self.live_meas_status.is_set(): 
    #         scrollbar = self.textEditlog.verticalScrollBar()
    #         scrollbar.setValue(scrollbar.maximum())


    def updade_video(self, path=None):
        if path is None:
            img, img_width, img_height= self.capture_module.getImage()
            print('updade_video')
        else:
            img, img_width, img_height= self.capture_module.load_image(path)
        image = QtGui.QImage(img.data, img_width, img_height, QtGui.QImage.Format_RGB888).rgbSwapped()
        self.display_image(image)
    
    def display_image(self, image:QtGui.QImage):
        self.video_frame.setPixmap(QtGui.QPixmap.fromImage(image))
        # self.image_min=image.scaledToHeight(self.video_frame_miniature.height())
        # self.video_frame_miniature.setPixmap(QtGui.QPixmap.fromImage(self.image_min))

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
    # app.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
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
