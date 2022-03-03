#!C:\Anaconda3\envs\py38_app python
# -*- coding: utf-8 -*-
""" Set all the method needed to  

"""

from __future__ import absolute_import, division, print_function

import logging
import os
import time
from logging import getLogger
from queue import Queue
from sys import argv, exit

import matplotlib
import numpy as np
from default.set_default_dir import APP_DIRS, AppDirs, set_ai_default_dir
from eit_app.app.dialog_boxes import openFileNameDialog, show_msgBox
from eit_app.app.event import CustomEvents
from eit_app.app.gui import Ui_MainWindow as app_gui
from eit_app.app.update_gui_listener import (UpdateEvents,
                                             setup_update_event_handlers)
from eit_app.app.utils import set_comboBox_items, set_slider, set_table_widget
from eit_app.eit.computation import ComputeMeas
from eit_app.eit.eit_model import EITModelClass
from eit_app.eit.imaging_type import (DATA_TRANSFORMATIONS, IMAGING_TYPE,
                                      Imaging)
from eit_app.eit.plots import (PlotDiffPlot, PlotImage2D, PlotUPlot,
                               plot_measurements, plot_rec)
from eit_app.eit.rec_abs import RecCMDs
from eit_app.eit.rec_ai import ReconstructionAI
from eit_app.eit.rec_pyeit import ReconstructionPyEIT
from eit_app.io.sciospec.com_constants import OP_LINEAR, OP_LOG
from eit_app.io.sciospec.device import IOInterfaceSciospec
from eit_app.io.sciospec.meas_dataset import EitMeasurementSet
from eit_app.io.video.microcamera import (EXT_IMG, IMG_SIZES, MicroUSBCamera,
                                          VideoCaptureModule)
from eit_app.threads_process.threads_worker import CustomWorker
from glob_utils.flags.flag import CustomFlag, CustomTimer
from glob_utils.log.log import change_level_logging, main_log
from glob_utils.pth.path_utils import get_datetime_s, mk_new_dir
from glob_utils.files.files import save_as_csv,dialog_get_file_with_ext,FileExt,OpenDialogFileCancelledException
from matplotlib.backends.backend_qt5agg import \
    FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import \
    NavigationToolbar2QT as NavigationToolbar
from matplotlib.pyplot import figure
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication

import eit_ai.raw_data.load_eidors as matlab

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

class UiBackEnd(app_gui, QtWidgets.QMainWindow):
    
    def __init__(self)->None:
        super().__init__()
        self._initilizated=CustomFlag()
        self.setupUi(self) # setup the UI created with designer
        self._post_init()
        self._initilizated.set()
    
    def _post_init(self) -> None:
        set_ai_default_dir()
        _translate = QtCore.QCoreApplication.translate
        # Set app title
        self.setWindowTitle(
            _translate(
                "MainWindow", f'EIT aquisition for Sciospec device {__version__}'
            )
        )


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
        self._c_update_log()
        self._update_dev_setup()
        self._c_refresh_device_list()
        self._c_plots_to_show()
        self._c_imaging_params_changed()
        self._c_autosave()
        self._c_refresh_capture_devices()
        self.up_events.post(
            UpdateEvents.device_status,self, self.io_interface)
        self.up_events.post(
            UpdateEvents.live_meas_status, self, self.live_meas_status)
        self.up_events.post(
            UpdateEvents.replay_status, self, self.replay_status)

        self._init_multithreading_workers()
        
    def _init_main_objects(self)->None:

        # mk_new_dir(dir_name=MEAS_DIR)
        # mk_new_dir(dir_name=SNAPSHOT_DIR)
        # add dir in default dirs TODO
        self.dataset = EitMeasurementSet()
        self.io_interface = IOInterfaceSciospec()
        self.eit_model= EITModelClass()
        self.io_interface.setup.exc_pattern= self.eit_model.InjPattern

        self.data_to_compute= Queue(maxsize=256)
        self.figure_to_plot= Queue(maxsize=256)
        self.computing=ComputeMeas(
            self.io_interface.get_queue_out(),
            self.figure_to_plot
        )

        self.live_meas_status=CustomFlag()
        self.replay_status=CustomFlag()
        self.replay=CustomFlag()
        self.replay_timer= CustomTimer(
            max_time=self.sB_replay_time.value(), time_stp=0.05)
        self.live_capture=CustomFlag()
        # setting of the camera
        self.captured_imgs= Queue(maxsize=256)
        self.capture_module=VideoCaptureModule(
            MicroUSBCamera(),
            self.io_interface.get_queue_video_module(),
            self.captured_imgs
        )
        self.up_events=CustomEvents()
        setup_update_event_handlers(self.up_events)

    def comboBox_init(self)->None:
        """ """
        set_comboBox_items(
            self.cB_log_level,list(log_level.keys()))
        set_comboBox_items(
            self.cB_scale, [OP_LINEAR.name, OP_LOG.name])
        set_comboBox_items(
            self.cB_solver, ['JAC', 'BP', 'GREIT'])
        set_comboBox_items(
            self.cB_eit_imaging_type, list(IMAGING_TYPE.keys()))
        set_comboBox_items(
            self.cB_transform_volt, list(DATA_TRANSFORMATIONS.keys())[:4])
        set_comboBox_items(
            self.cB_img_size, list(IMG_SIZES.keys()), set_index=-1)
        set_comboBox_items(
            self.cB_img_file_ext, list(EXT_IMG.keys()))
        set_comboBox_items(
            self.cB_ref_frame_idx, [0])

    def _link_callbacks(self)->None:
        """ """
        self.cB_log_level.activated.connect(self._c_update_log)

        # device relative callbacks
        self.pB_refresh.clicked.connect(self._c_refresh_device_list)
        self.pB_connect.clicked.connect(self._c_connect_device)
        self.pB_disconnect.clicked.connect(self._c_disconnect_device)
        self.pB_get_setup.clicked.connect(self._c_get_device_setup)
        self.pB_set_setup.clicked.connect(self._c_set_device_setup)
        self.pB_reset.clicked.connect(self._c_softreset_device)
        self.pB_save_setup.clicked.connect(self._c_save_setup)
        self.pB_load_setup.clicked.connect(self._c_load_setup)
        self.pB_start_meas.clicked.connect(self._c_start_measurement)
        self.pB_stop_meas.clicked.connect(self._c_stop_measurement)

        self.sBd_freq_min.valueChanged.connect(self._update_dev_setup)
        self.sBd_freq_max.valueChanged.connect(self._update_dev_setup)
        self.sB_freq_steps.valueChanged.connect(self._update_dev_setup)
        self.cB_scale.activated.connect(self._update_dev_setup)
        self.sBd_frame_rate.valueChanged.connect(self._update_dev_setup)
        
        self.chB_dataset_autoset.toggled.connect(self._c_autosave)
        self.chB_dataset_save_img.toggled.connect(self._c_autosave)

        # frame plot/ 
        self.cB_current_idx_frame.activated.connect(
            self._c_current_frame_selected)
        self.chB_plot_graph.toggled.connect(self._c_plots_to_show)
        self.chB_Uplot.toggled.connect(self._c_plots_to_show)
        self.chB_diff.toggled.connect(self._c_plots_to_show)
        self.chB_plot_image_rec.toggled.connect(self._c_plots_to_show)
        self.chB_y_log.toggled.connect(self._c_plots_to_show)

        # loading measurements / replay
        self.pB_load_meas_dataset.clicked.connect(self._c_load_meas_set)
        self.pB_replay_back_begin.clicked.connect(self._c_replay_back_begin)
        self.pB_replay_goto_end.clicked.connect(self._c_replay_goto_end)
        self.pB_replay_play.clicked.connect(self._c_replay_play)
        self.pB_replay_pause.clicked.connect(self._c_replay_pause)
        self.pB_replay_stop.clicked.connect(self._c_replay_stop)
        self.sB_replay_time.valueChanged.connect(self._c_replay_time_changed)
        self.slider_replay.valueChanged.connect(self._c_replay_slider_changed)
        self.pB_export_meas_csv.clicked.connect(self._c_export_meas_csv)
        self.pB_load_ref_dataset.clicked.connect(self._c_loadRef4TD)

        self.pB_load_eidors_fwd_solution.clicked.connect(self._c_load_eidors_fwd_solution)
        self.sB_eidors_factor.valueChanged.connect(self._c_eidors_reload)
        self.pB_export_data_meas_vs_eidors.clicked.connect(self._c_export_data_meas_vs_eidors)

        #EIT reconstruction
        self.pB_set_reconstruction.clicked.connect(self._c_init_rec)
        ## pyeit
        self.scalePlot_vmax.valueChanged.connect(self._c_set_eit_model_data)
        self.scalePlot_vmin.valueChanged.connect(self._c_set_eit_model_data)
        self.normalize.toggled.connect(self._c_set_eit_model_data) 
        self.eit_FEMRefinement.valueChanged.connect(self._c_set_eit_model_data)
        # self.cB_solver.activated.connect(self._c_set_reconstruction)

        # eit imaging 
        self.cB_eit_imaging_type.activated.connect(
            self._c_imaging_params_changed)
        self.cB_ref_frame_idx.currentIndexChanged.connect(
            self._c_imaging_params_changed)
        self.cB_freq_meas_0.activated.connect(self._c_imaging_params_changed)
        self.cB_freq_meas_1.activated.connect(self._c_imaging_params_changed)
        self.cB_transform_volt.activated.connect(self._c_imaging_params_changed)
        self.showAbsValue.toggled.connect(self._c_imaging_params_changed)

        # Video capture
        self.pB_refresh_video_devices.clicked.connect(
            self._c_refresh_capture_devices)
        self.pB_capture_start.clicked.connect(self._c_live_capture_start)
        self.pB_capture_stop.clicked.connect(self._c_live_capture_stop)
        self.pB_capture_snapshot.clicked.connect(self._c_capture_snapshot)
        self.cB_video_devices.activated.connect(self._c_set_capture_device)
        self.cB_img_size.activated.connect(self._c_set_capture_device)
        self.cB_img_file_ext.activated.connect(self._c_set_capture_device)

    def _init_multithreading_workers(self)->None:
        """Start all threads used for the GUI """        
        self.workers = {}

        workers_settings= {
            'live_view':[CustomWorker, 0.05, self._poll_live_view],
            'update':[CustomWorker,0.05, self._poll_update]
            # 'serial'        : [Worker,0.01, self._poll_read_serial],
            # 'ListenQueue'   : [Worker,0.1, self._listener_queue_in],
            # 'video'         : [CustomWorker, 0.1, self._poll_capture, False]
        }
        
        for key, data in workers_settings.items():
            self.workers[key]= data[0](data[1])
            self.workers[key].progress.connect(data[2])
            self.workers[key].start()
            self.workers[key].start_polling()


    ############################################################################
    # Live view
    def _poll_live_view(self)->None:
        """ Called by live_view_worker

        In case of liveView
            - if a new frame is available > plot/reconstruction...
            - in case that frame number is reach stop 
            >> terminate measurement /live view
        
        Notes
        -----
            - live view is started with Start Meas.
            - live view can be stopped with Stop Meas.
        """
    
        if self.live_meas_status.has_changed():
            self.up_events.post(
                UpdateEvents.live_meas_status,
                self,
                self.live_meas_status)
            self.live_meas_status.ack_change()
            if self.live_meas_status.is_set():
                self.replay_status.clear()
                self.capture_module.set_meas()
            else:
                self.capture_module.set_idle()
                self._c_live_capture_start(look_memory_flag=True)

        if self.replay_status.has_changed():
            self.up_events.post(
                UpdateEvents.replay_status,
                self,
                self.replay_status)
            self.replay_status.ack_change()

        if self.live_meas_status.is_set():
            self.up_events.post(
                UpdateEvents.progress_frame,
                self,
                self.meas_dataset.get_frame_cnt(),
                self.meas_dataset.get_filling())
            self.nb_measurements_reached()
        self.replay_pulse()    
        self.is_device_unplugged()

    def _poll_update(self)->None:
        """ Called by UpdateGuiWorker
        In case that the device send the flag devDataUp (e.g. new data recieved)
            >> update the gui
        Also this poll report of device disconnection to the user  """ 
        self.is_new_computed_data()
        self.is_new_captured_image()

    
    def is_new_computed_data(self)->None:
        """Check if a new data have been computed/are available for plotting: 
        in that case the data displayed/plot"""
        if self.figure_to_plot.empty():
            return
        #empty the queue (possible lost of monitored data)
        while not self.figure_to_plot.empty():
            data=self.figure_to_plot.get()
        try:
            dataset=data['dataset']
            if isinstance(dataset, EitMeasurementSet):
                idx_frame= data['idx_frame']
                self.up_events.post(
                    UpdateEvents.info_data_computed,
                    self,
                    self.live_meas_status,
                    dataset.get_idx_frame(idx_frame),
                    dataset.get_frame_info(idx_frame)
                )
            # print(data['U'])
            self._update_canvas(data)
        except AttributeError as e:
            logger.error(f'new computed data not displayed : source ({e})')
    
    def is_new_captured_image(self)->None:
        """Check if a new image has been captured/ is available: 
        in that case the image will be displayed"""
        if self.captured_imgs.empty():
            return

        while not self.captured_imgs.empty():# empty the queue
            image=self.captured_imgs.get()
        self.display_image(image)

    def nb_measurements_reached(self)-> None: 
        """Check if the number of Burst(measurements) is reached, 
        in that case the measurement mode will be stopped on the device
        Notes:
        # TODO move that feature to in the device directly()
        # """
        burst=self.io_interface.setup.get_burst()
        if burst > 0 and self.meas_dataset.frame_cnt == burst:
            self._c_stop_measurement() 

    def is_device_unplugged(self)-> None:
        """Check if the device has been unplugged or turned off
        in that case a msgBox will be displayed to inform the user after the ack
        of the user(click on "OK"-Button) the list of available
        devices will be refreshed"""
        if self.io_interface._not_connected() and \
        self.io_interface.status_prompt!=self.lab_device_status.text():
            self.up_events.post(
                UpdateEvents.device_status,
                self,
                self.io_interface
            )
            show_msgBox(
                'The device has been disconnected!',
                'Error: Device disconnected',
                "Critical"
            )
            self._c_refresh_device_list()

    def replay_pulse(self)->None:
        """Generate the increment pulse for the replay function """        
        if self.replay.is_set() and self.replay_timer.increment():
            set_slider(self.slider_replay, next=True, loop=True)

    ############################################################################
    #### Logging
    ############################################################################
    def _c_update_log(self)->None:
        """Modify the actual logging level"""
        change_level_logging(level=log_level[self.cB_log_level.currentText()])

    ############################################################################
    #### Interaction with Device 
    ############################################################################
     
    def _c_refresh_device_list(self)->None:
        """Refresh the list of available sciospec devices"""
        self.io_interface.get_available_devices()
        self.up_events.post(
            UpdateEvents.device_list_refreshed,self, self.io_interface)
    
    def _c_connect_device(self)->None:
        """Connect with selected sciospec device"""
        device_name= str(self.cB_ports.currentText()) # get actual ComPort
        self.io_interface.connect_device(device_name, baudrate=115200)
        self.up_events.post(UpdateEvents.device_status,self, self.io_interface)
                    
    def _c_disconnect_device(self)->None:
        """Disconnect the sciospec device"""
        self.io_interface.disconnect_sciospec_device()
        self.up_events.post(UpdateEvents.device_status,self, self.io_interface)

    def _c_get_device_setup(self)->None:
        """Get setup of the sciospec device and display it"""
        self.io_interface.get_setup()
        self.up_events.post(UpdateEvents.device_setup,self, self.io_interface)

    def _c_set_device_setup(self)->None:
        """Set the displayed setup of the sciospec device"""
        self._update_dev_setup()
        self.io_interface.set_setup()
        self._c_get_device_setup()

    def _c_softreset_device(self)->None:
        """Reset the sciopec device"""
        self.io_interface.software_reset()
        self.up_events.post(UpdateEvents.device_status,self, self.io_interface)
    
    def _c_start_measurement(self)->None:
        """Start measurements on sciopec device"""
        self._c_set_device_setup()
        if self.io_interface.start_meas(self.lE_meas_dataset_dir.text()):
            self.init_gui_for_live_meas()
    
    # def _c_resume_measurement(self)->None:
    #     """Start measurements on sciopec device"""
    #     # self._c_set_device_setup()
    #     if self.io_interface.resume_meas(self.lE_meas_dataset_dir.text()):
    #         # self.up_events.post(
    #         # UpdateEvents.info_data_computed,self, self.live_meas_status, 0, '')
    #         self.live_meas_status.set()

    def _c_stop_measurement(self)->None:
        """Start measurements on sciopec device"""
        self.io_interface.stop_meas()
        self.live_meas_status.clear()
        # self.frame_cnt_old =-1 # reset
    
    def _c_save_setup(self)->None:
        """Save setup of sciopec device"""
        self.io_interface.save_setup(dir=None)
        
    def _c_load_setup(self)->None:
        """Load setup of sciopec device"""
        self.io_interface.load_setup()
        self.up_events.post(UpdateEvents.device_setup,self, self.io_interface)

    def _update_dev_setup(self)->None:
        ''' Save user entry from Gui in setup of dev'''
        ## Update Measurement Setups
        self.io_interface.setup.set_frame_rate(self.sBd_frame_rate.value())
        self.io_interface.setup.set_burst(self.sB_burst.value())
        self.io_interface.setup.set_exc_amp(self.sBd_exc_amp.value()/1000) # mA -> A

        freq_max_enable, error=self.io_interface.setup.set_freq_config(
            freq_min=self.sBd_freq_min.value(),
            freq_max=self.sBd_freq_max.value(),
            freq_steps=self.sB_freq_steps.value(),
            freq_scale=self.cB_scale.currentText()
        )
        ## Outputconfig Stamps all to one
        self.io_interface.setup.set_dhcp(True)# self.chB_dhcp.isChecked()
        self.io_interface.setup.set_exc_stamp(True)#
            #self.chB_exc_stamp.isChecked() or True)
        self.io_interface.setup.set_current_stamp(True)
            #self.chB_current_stamp.isChecked() or True)
        self.io_interface.setup.set_time_stamp(True)
        # self.chB_time_stamp.isChecked()
    
        self.up_events.post(
            UpdateEvents.device_setup,
            self,
            self.io_interface,
            freq_max_enable,
            error
        )

    ############################################################################
    #### Reconstruction
    ############################################################################
    def _c_init_rec(self)->None:
        """[summary]
        """        
        # set some 
        rec={
            0:ReconstructionPyEIT,
            1:ReconstructionAI
        }
        self._c_set_eit_model_data()
        self.U= np.random.rand(256,2)
        self.labels= ['test','test','test','test']
        self.computing.set_eit_model(self.eit_model)
        self.computing.set_reconstruction(
            rec[self.tabW_reconstruction.currentIndex()])

        self.io_interface.put_queue_out(('random', 0, RecCMDs.initialize))
    
    def _c_loadRef4TD(self)->None:
        """[summary]
        """

        try:

            file_path= dialog_get_file_with_ext(
                ext=FileExt.pkl,title='', initialdir=APP_DIRS.get(AppDirs.meas_set))   
        except OpenDialogFileCancelledException:
            return

        # path, cancel= openFileNameDialog(
        #     self,path=APP_DIRS.get(AppDirs.meas_set))
        # if cancel: # Cancelled
        #     return
        self._c_UpdateRef4TD(path=file_path)    
        
    def _c_UpdateRef4TD(self, path=None)->None:
        """[summary]

        Args:
            path ([type], optional): [description]. Defaults to None.
        """        
        if self.live_meas_status.is_set()==True:
            # Frame to use is ._last_frame[0] is the last updated...
            self.meas_dataset.set_frame_TD_ref() 
        else:
            self.meas_dataset.set_frame_TD_ref(
                self.cB_current_idx_frame.currentIndex(), path= path)
        
    def _c_set_eit_model_data(self)->None:
        """[summary]
        """        
        self.eit_model.p=self.eit_p.value()
        self.eit_model.lamb=self.eit_lamda.value()
        self.eit_model.n=self.eit_n.value()
        self.eit_model.set_solver(self.cB_solver.currentText())
        self.eit_model.fem.refinement=self.eit_FEMRefinement.value()

    def _c_load_eidors_fwd_solution(self) -> None:    # for Jiawei master thesis
        """load eidors foward solution(voltages) out of an mat-file"""
       
        sol = matlab.load_mat_var(initialdir=os.getcwd(),  var_name="X")
        U, _ = sol[0]
        volt= np.array(U).reshape((16,16))

        self.eidors_sol= volt
        self._extracted_from__c_eidors_reload_9(volt)

    def _c_eidors_reload(self) -> None:    # for Jiawei master thesis
        """replot the data witha different scaling factor"""
        volt= self.eidors_sol
        self._extracted_from__c_eidors_reload_9(volt)

    def _extracted_from__c_eidors_reload_9(self, volt):
        volt = volt * self.sB_eidors_factor.value()
        self.meas_dataset.set_voltages(volt, 0, 0)
        self.meas_dataset.set_frame_TD_ref(0)
        self._c_replay_slider_changed()

    def _c_export_data_meas_vs_eidors(self)-> None:
        """ export the actual raw data in csv from"""
        frame, freq= self.slider_replay.sliderPosition(), self.cB_freq_meas_0.currentIndex()
        data= {
            'measurement':np.real(self.meas_dataset.get_voltages(frame, freq)[:,0:16]),
            'eidors': self.eidors_sol
        }
        file_path=os.path.join(
            self.meas_dataset.output_dir, f'eidorsvsmeas#{frame}_freq{freq}')
        save_as_csv(file_path, data)
        logger.debug(f'Measurements VS Eidors exported as CSV in : {file_path}')
        

    ############################################################################
    #### Replay of Measurements
    ############################################################################
    
    def _c_autosave(self)->None:
        """update selected autosave mode """        
        self.io_interface.set_autosave(
            self.chB_dataset_autoset.isChecked(),
            self.chB_dataset_save_img.isChecked())
        self.up_events.post(UpdateEvents.autosave_changed,self)
    
    def _c_load_meas_set(self)->None:
        """the callback has to be witouh arguments! """
        self._load_meas_set()
    
    def _load_meas_set(self, dir_path:str=None)->None:
        """[summary]

        Args:
            dir_path (str, optional): [description]. Defaults to None.
        """        
        if self.live_capture.is_set():
            self._c_live_capture_stop()
            show_msgBox(
                'Live video stopped',
                'Live video still running',
                'Information'
            )
        if self.live_meas_status.is_set():
            show_msgBox(
                'Please stop measurements before loading dataset',
                'Live measurements still running',
                'Warning'
            )
            return
        self.replay_status.clear()
        if not self.meas_dataset.load_meas_dir(dir_path):
            return
        self.io_interface.load_setup(self.meas_dataset.output_dir)
        self.replay_status.set()
        self.up_events.post(UpdateEvents.device_setup,self, self.io_interface)
        self.up_events.post(UpdateEvents.dataset_loaded,self, self.meas_dataset)
        self.compute_frame(idx_frame=0)

    def _c_replay_play(self)->None:
        self.replay.set()
        self.replay_timer.reset()

    def _c_replay_back_begin(self)->None:
        set_slider(self.slider_replay, set_pos=0)
        
    def _c_replay_goto_end(self)->None:
        set_slider(self.slider_replay, set_pos=-1)

    def _c_replay_pause(self)->None:
        self.replay.clear()
        
    def _c_replay_stop(self)->None:
        """[summary]
        """        
        self.replay.clear()
        self._c_replay_back_begin()
        self.replay_timer.reset()
        
    def _c_replay_slider_changed(self)->None:
        idx_frame=self.slider_replay.sliderPosition()
        self.cB_current_idx_frame.setCurrentIndex(idx_frame)
        self._compute_meas_frame(idx_frame)
    
    def _c_replay_time_changed(self)->None:
        self.replay_timer.set_max_time(self.sB_replay_time.value())

    def _c_current_frame_selected(self)->None:
        idx_frame=self.cB_current_idx_frame.currentIndex()
        set_slider(self.slider_replay,  set_pos=idx_frame)
        self._compute_meas_frame(idx_frame)

    def _compute_meas_frame(self, idx_frame:int=0)->None:
        if not self.replay_status.is_set() or self.live_meas_status.is_set():
            show_msgBox(
                'First load a measuremment dataset',
                'Replay mode not activated',
                'Warning'
            )
            return
        self.compute_frame(idx_frame)
    
    def _c_export_meas_csv(self)-> None:
        """Export the actual measurments frames in csv"""
        idx_freq=  self.cB_freq_meas_0.currentIndex()
        n=self.meas_dataset.get_frame_cnt()
        data= { 
            f'frame{i}':np.real(
                self.meas_dataset.get_voltages(i, idx_freq)[:,0:16]) for i in range(n) }
        freq= self.meas_dataset.get_freq_val(idx_freq)

        file_path=os.path.join(
            self.meas_dataset.output_dir, f'Meas#1-{n}_freq{freq}Hz')
        save_as_csv(file_path,data)
        logger.debug(f'Measurements exported as CSV in : {file_path}')
        

    ############################################################################
    #### Interaction with Microcam
    ############################################################################

    def _c_live_capture_start(self, look_memory_flag:bool=False)->None:
        if self.live_meas_status.is_set():
            show_msgBox(
                'First stop measurement',
                'Measurement is running',
                'Warning'
            )
            return
        if look_memory_flag and not self.live_capture.is_set():
            return
        self.capture_module.set_live()
        self.live_capture.set()
        
        
    def _c_live_capture_stop(self, memory_flag:bool=False)->None:
        if self.live_meas_status.is_set():
            show_msgBox(
                'First stop measurement',
                'Measurement is running',
                'Warning'
            )
            return
        self.capture_module.set_idle()
        if not memory_flag:
            self.live_capture.clear()

    def _c_capture_snapshot(self)->None:
        """Save """
        path=os.path.join(
                APP_DIRS.get(AppDirs.snapshot),f'Snapshot_{get_datetime_s()}'
        )
        self.capture_module.snapshot(path=path)
    
    def _c_refresh_capture_devices(self)->None:
        capture_devices= self.capture_module.get_devices_available()
        set_comboBox_items(self.cB_video_devices,capture_devices)

    def _c_set_capture_device(self)->None:
        if self.live_meas_status.is_set():
            show_msgBox(
                'First stop measurement',
                'Measurement is running',
                'Warning'
            )
            return
        self._c_live_capture_stop(memory_flag=True)
        self.capture_module.select_device(self.cB_video_devices.currentText())
        self.capture_module.set_image_size(self.cB_img_size.currentText())
        self.capture_module.set_image_file_format(
            file_ext=self.cB_img_file_ext.currentText())
        self._c_live_capture_start(look_memory_flag=True)

    ############################################################################
    #### Plotting
    ############################################################################
            
    def _c_imaging_params_changed(self)->None:

        rec_type= self.cB_eit_imaging_type.currentText()
        if rec_type not in list(IMAGING_TYPE.keys()):
            raise Exception(f'The imaging type {rec_type} ist not known')
            
        transform_volt=self.cB_transform_volt.currentText()
        if transform_volt not in DATA_TRANSFORMATIONS:
            raise Exception(f'The transformation {transform_volt} unknown')

        idx_freqs=[
            self.cB_freq_meas_0.currentIndex(),
            self.cB_freq_meas_1.currentIndex()
        ]
        idx_ref_frame= self.cB_ref_frame_idx.currentIndex()

        transform_funcs=[
            DATA_TRANSFORMATIONS[transform_volt], 
            DATA_TRANSFORMATIONS['Abs'] if self.showAbsValue.isChecked()\
                else DATA_TRANSFORMATIONS['Identity']
        ]

        self.imaging_type:Imaging=IMAGING_TYPE[rec_type](
            idx_freqs, idx_ref_frame, transform_funcs)

        self.up_events.post(UpdateEvents.freqs_inputs, self, self.imaging_type)

        self.computing.set_computation(self.imaging_type)
        self.computing.set_eit_model(self.eit_model)
        # if not self.live_view.is_set():
        #     self.compute_measurement()

    def _c_plots_to_show(self)->None:
        self.plots_to_show=[ 
            PlotImage2D(
                is_visible=self.chB_plot_image_rec.isChecked()
                ),
            PlotUPlot(
                is_visible=self.chB_Uplot.isChecked() and\
                    self.chB_plot_graph.isChecked(),
                y_axis_log= self.chB_y_log.isChecked()
                ),
            PlotDiffPlot(
                self.chB_diff.isChecked() and self.chB_plot_graph.isChecked(),
                y_axis_log=self.chB_y_log.isChecked()
                )
        ]
        self.computing.set_plotings(self.plots_to_show, self.figure_graphs)
        self.up_events.post(UpdateEvents.plots_to_show, self)


    def compute_frame(self, idx_frame:int=0)->None:
        data_for_queue=(
            self.meas_dataset,
            idx_frame,
            RecCMDs.reconstruct
        )
        self.io_interface.put_queue_out(data_for_queue)
        self.get_picture(idx_frame=idx_frame) # 

    def get_picture(self, idx_frame:int)->None:
        if not self.replay_status.is_set(): # only in replay mode
            return
        path= self.meas_dataset.get_frame_path(idx_frame)
        path,_= os.path.splitext(path)
        path= path + self.capture_module.image_file_ext
        self.capture_module.load_image(path)

    def init_gui_for_live_meas(self)->None:
        self.up_events.post(
            UpdateEvents.info_data_computed,self, self.live_meas_status, 0, '')
        self.live_meas_status.set()


    def closeEvent(self, event)->None:
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
        
    def kill_workers(self)->None:
        """ Kill alls the running threads workers """        
        [item.quit() for _, item in self.workers.items()]
        
    @property
    def meas_dataset(self)-> EitMeasurementSet:
        """Return the measurement dataset from the IO_interface()"""
        return self.io_interface.getDataset()
    
    def get_current_frame_cnt(self)-> int:
        return self.meas_dataset.get_frame_cnt()

    def _test_compute(self)->None:
        self.io_interface.put_queue_out(('random', 0, RecCMDs.reconstruct))

    def _update_canvas(self, data)->None:
        """"""
        try:
            dataset:EitMeasurementSet=data['dataset']
            idx_frame=data['idx_frame']
            t = time.time()
            self.figure_rec=plot_rec(self.plots_to_show, self.figure_rec, data)
            self.canvas_rec.draw()
            self.figure_graphs = plot_measurements(
                self.plots_to_show, self.figure_graphs, data)
            self.canvas_graphs.draw()
            elapsed = time.time() - t
            if dataset=='random':
                return
            voltages= dataset.get_voltages(idx_frame, 0)
            if voltages is not None:
                set_table_widget(self.tableWidgetvoltages_Z, voltages)
            if isinstance(dataset, EitMeasurementSet):
                idx, t=dataset.get_idx_frame(idx_frame), get_datetime_s()
                logger.debug(f'Plot Frame #{idx}, time {t}, lasted {elapsed}')
        except BaseException as e:
            logger.error(f'Error _update_canvas: {e}')
    
    def display_image(self, image:QtGui.QImage)->None:
        if not isinstance(image, QtGui.QImage):
            logger.error(f'{image=} is not an QtGui.QImage')
            return
        self.video_frame.setPixmap(QtGui.QPixmap.fromImage(image))

if __name__ == "__main__":
    """"""


