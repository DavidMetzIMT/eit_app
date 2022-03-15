#!C:\Anaconda3\envs\py38_app python
# -*- coding: utf-8 -*-
""" Set all the method needed to  

"""

from __future__ import absolute_import, division, print_function
from copy import deepcopy

import logging
import os
from logging import getLogger
from queue import Queue
import threading

import eit_ai.raw_data.load_eidors as matlab
import glob_utils.log.log
import matplotlib
import matplotlib.backends.backend_qt5agg
import matplotlib.pyplot
import numpy as np
from default.set_default_dir import APP_DIRS, AppDirs, set_ai_default_dir
from eit_app.app.dialog_boxes import show_msgBox
from eit_app.app.gui import Ui_MainWindow as app_gui
from eit_app.app.update_event import (
    UPDATE_EVENTS,
    EventsAgent,
    AutosaveOptions,
    DevAvailables,
    DevSetup,
    DevStatus,
    FrameInfo,
    ImagingInputs,
    LiveMeasState,
    LiveStatus,
    MeasDatasetLoaded,
    EITdataPlotOptions,
    FrameProgress,
    ReplayButton,
    ReplayStatus
)

from eit_app.app.gui_utils import set_comboBox_items, set_slider
from eit_app.eit.computation import ComputeMeas
from eit_model.imaging_type import DATA_TRANSFORMATIONS, IMAGING_TYPE, Imaging
from eit_app.eit.plots import (
    CanvasLayout,
    LayoutEITData,
    LayoutEITImage2D,
)
from eit_app.io.sciospec.com_constants import OP_LINEAR, OP_LOG
from eit_app.io.sciospec.device import IOInterfaceSciospec
from eit_app.io.sciospec.meas_dataset import EitMeasurementSet
from eit_app.io.video.microcamera import (
    EXT_IMG,
    IMG_SIZES,
    MicroUSBCamera,
    VideoCaptureModule,
)
from glob_utils.thread_process.threads_worker import CustomWorker
from glob_utils.decorator.decorator import catch_error
from glob_utils.files.files import (
    FileExt,
    OpenDialogFileCancelledException,
    dialog_get_file_with_ext,
    save_as_csv,
    search_for_file_with_ext,
)
from glob_utils.flags.flag import CustomFlag, MultiState, MultiStatewSignal, CustomFlagwSignals
from glob_utils.pth.path_utils import get_datetime_s
from PyQt5 import QtCore, QtGui, QtWidgets
import eit_model.model
import eit_model.solver_pyeit

import eit_app.eit.plots

# Ensure using PyQt5 backend
matplotlib.use("QT5Agg")

__author__ = "David Metz"
__copyright__ = "Copyright 2021, microEIT"
__credits__ = ["David Metz"]
__license__ = "GPL"
__version__ = "2.0.0"
__maintainer__ = "David Metz"
__email__ = "d.metz@tu-bs.de"
__status__ = "Production"

logger = getLogger(__name__)


LOG_LEVELS = {"DEBUG": logging.DEBUG, "INFO": logging.INFO, "WARNING": logging.WARNING}




class UiBackEnd(app_gui, QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._initilizated = CustomFlag()
        self.setupUi(self)  # setup the UI created with designer
        self._post_init()
        self._initilizated.set()

    def _post_init(self) -> None:

        set_ai_default_dir()
        _translate = QtCore.QCoreApplication.translate
        # Set app title
        self.setWindowTitle(
            _translate(
                "MainWindow", f"EIT aquisition for Sciospec device {__version__}"
            )
        )

        self._init_main_objects()

        # link callbacks
        self._link_callbacks()
        self.comboBox_init()


        self._update_log()
        self._update_dev_setup()
        self._refresh_device_list()
        self._plots_to_show()
        self._imaging_params_changed()
        self._autosave()
        self._refresh_capture_devices()

        self.meas_status.change_state(LiveMeasState.Idle)
        self.update_gui(
            DevStatus(self.interface.connected(),self.interface.status_prompt)
        )
        self.update_gui(LiveStatus(self.meas_status))
        self.update_gui(ReplayStatus(self.replay_status))
        self._init_multithreading_workers()
        logger.info(f"thread main {threading.get_ident()}") 


    def _init_main_objects(self) -> None:
        self.update_event=EventsAgent(self,UPDATE_EVENTS)
        # set canvas
        self.plot_agent=eit_app.eit.plots.PlottingAgent()
        self.canvas_rec=CanvasLayout(self, self.layout_rec, LayoutEITImage2D)
        self.plot_agent.add_layouts(self.canvas_rec)
        self.canvas_graphs=CanvasLayout(self, self.layout_graphs, LayoutEITData)
        self.plot_agent.add_layouts(self.canvas_graphs)
        # self.plot_agent.add_layouts(self, self.layout_rec)
        # self.plot_agent.add_layouts(self, self.layout_ch_graph)
        
        self.eit_model = eit_model.model.EITModel()
        self.eit_model.load_defaultmatfile()
        
        # self.figure_to_plot = Queue(maxsize=256)
        self.computing = ComputeMeas(self.plot_agent.add_data2plot)
        self.dataset = EitMeasurementSet()
        self.dataset.new_frame.connect(self.computing.add_data2compute)
        self.dataset.new_frame.connect(self.update_frame)

        self.for_frame_update = Queue(16) # TODO maybe 
        
        self.interface = IOInterfaceSciospec(self.dataset)
        exc_mat= self.eit_model.excitation_mat()+1
        self.interface.setup.exc_pattern= exc_mat.tolist()

        # self.live_meas_status=CustomFlag()
        self.meas_status = MultiStatewSignal(
            [LiveMeasState.Idle, LiveMeasState.Measuring, LiveMeasState.Paused]
        )
        self.meas_status.changed.connect(self.handle_meas_status_change)

        self.replay_status = CustomFlagwSignals()
        self.replay_status.changed.connect(self.handle_replay_status_change)

        self.reply_timerqt= QtCore.QTimer()
        self.reply_timerqt.timeout.connect(self.replay_next_frame)

        self.live_capture = CustomFlag()
        # setting of the camera
        self.captured_imgs = Queue(maxsize=256)
        self.capture_module = VideoCaptureModule(
            MicroUSBCamera(),
            self.captured_imgs,
        )
        self.dataset.new_frame.connect(self.capture_module.add_path) # not tested yet.....
        # self.capture_module.new_image.connect(self.display_image)

    def comboBox_init(self) -> None:
        """ """
        set_comboBox_items(self.cB_log_level, list(LOG_LEVELS.keys()))
        set_comboBox_items(self.cB_scale, [OP_LINEAR.name, OP_LOG.name])
        set_comboBox_items(self.cB_solver, ["JAC", "BP", "GREIT"])
        set_comboBox_items(self.cB_eit_imaging_type, list(IMAGING_TYPE.keys()))
        set_comboBox_items(
            self.cB_transform_volt, list(DATA_TRANSFORMATIONS.keys())[:4]
        )
        set_comboBox_items(self.cB_img_size, list(IMG_SIZES.keys()), set_index=-1)
        set_comboBox_items(self.cB_img_file_ext, list(EXT_IMG.keys()))
        set_comboBox_items(self.cB_ref_frame_idx, [0])
        self._update_eit_ctlg()

    def _link_callbacks(self) -> None:
        """ """
        self.cB_log_level.activated.connect(self._update_log)

        # device relative callbacks
        self.pB_refresh.clicked.connect(self._refresh_device_list)
        self.pB_connect.clicked.connect(self._connect_device)
        self.pB_disconnect.clicked.connect(self._disconnect_device)
        self.pB_get_setup.clicked.connect(self._get_device_setup)
        self.pB_set_setup.clicked.connect(self._set_device_setup)
        self.pB_reset.clicked.connect(self._softreset_device)
        self.pB_save_setup.clicked.connect(self._save_setup)
        self.pB_load_setup.clicked.connect(self._load_setup)
        self.pB_start_meas.clicked.connect(self._start_measurement)
        self.pB_stop_meas.clicked.connect(self._stop_measurement)

        self.sBd_freq_min.valueChanged.connect(self._update_dev_setup)
        self.sBd_freq_max.valueChanged.connect(self._update_dev_setup)
        self.sB_freq_steps.valueChanged.connect(self._update_dev_setup)
        self.cB_scale.activated.connect(self._update_dev_setup)
        self.sBd_frame_rate.valueChanged.connect(self._update_dev_setup)

        self.chB_dataset_autosave.toggled.connect(self._autosave)
        self.chB_dataset_save_img.toggled.connect(self._autosave)
        self.chB_load_after_meas.toggled.connect(self._autosave)
        # frame plot/
        self.cB_current_idx_frame.activated.connect(self._current_frame_selected)
        self.chB_plot_graph.toggled.connect(self._plots_to_show)
        self.chB_Uplot.toggled.connect(self._plots_to_show)
        self.chB_diff.toggled.connect(self._plots_to_show)
        self.chB_plot_image_rec.toggled.connect(self._plots_to_show)
        self.chB_y_log.toggled.connect(self._plots_to_show)

        # loading measurements / replay
        self.pB_load_meas_dataset.clicked.connect(self._load_meas_set)
        self.pB_replay_back_begin.clicked.connect(self._replay_back_begin)
        self.pB_replay_goto_end.clicked.connect(self._replay_goto_end)
        self.pB_replay_play.clicked.connect(self._replay_play)
        # self.pB_replay_pause.clicked.connect(self._replay_pause)
        # self.pB_replay_stop.clicked.connect(self._replay_stop)
        self.sB_replay_time.valueChanged.connect(self._replay_set_timeout)
        self.slider_replay.valueChanged.connect(self._replay_slider_changed)
        self.pB_export_meas_csv.clicked.connect(self._export_meas_csv)
        self.pB_load_ref_dataset.clicked.connect(self._loadRef4TD)

        self.pB_load_eidors_fwd_solution.clicked.connect(
            self._load_eidors_fwd_solution
        )
        self.sB_eidors_factor.valueChanged.connect(self._eidors_reload)
        self.pB_export_data_meas_vs_eidors.clicked.connect(
            self._export_data_meas_vs_eidors
        )

        # EIT reconstruction
        self.pB_set_reconstruction.clicked.connect(self._init_rec)
        ## pyeit
        self.scalePlot_vmax.valueChanged.connect(self._set_solvers_parameters)
        self.scalePlot_vmin.valueChanged.connect(self._set_solvers_parameters)
        self.normalize.toggled.connect(self._set_solvers_parameters)
        self.eit_FEMRefinement.valueChanged.connect(self._set_solvers_parameters)
        # self.cB_solver.activated.connect(self._set_reconstruction)

        # eit imaging
        self.cB_eit_imaging_type.activated.connect(self._imaging_params_changed)
        self.cB_ref_frame_idx.currentIndexChanged.connect(
            self._imaging_params_changed
        )
        self.cB_freq_meas_0.activated.connect(self._imaging_params_changed)
        self.cB_freq_meas_1.activated.connect(self._imaging_params_changed)
        self.cB_transform_volt.activated.connect(self._imaging_params_changed)
        self.showAbsValue.toggled.connect(self._imaging_params_changed)

        self.cB_eit_mdl_ctlg.currentTextChanged.connect(self._set_eit_ctlg)
        self.pB_refresh_eit_mdl_ctlg.clicked.connect(self._update_eit_ctlg)

        # Video capture
        self.pB_refresh_video_devices.clicked.connect(self._refresh_capture_devices)
        self.pB_capture_start.clicked.connect(self._live_capture_start)
        self.pB_capture_stop.clicked.connect(self._live_capture_stop)
        self.pB_capture_snapshot.clicked.connect(self._capture_snapshot)
        self.cB_video_devices.activated.connect(self._set_capture_device)
        self.cB_img_size.activated.connect(self._set_capture_device)
        self.cB_img_file_ext.activated.connect(self._set_capture_device)

    def _abort_if_measuring(func):
        '''Decorator '''
    
        def wrap(self, *args, **kwargs):
            if self.meas_status.is_set(LiveMeasState.Measuring):
                show_msgBox("First stop measurement", "Measurement is running", "Warning")
                return
            func(self, *args, **kwargs)
        return wrap

    def update_frame(self, **kwargs):
        update_data= kwargs.get("update_data", None)
        if update_data is None:
            return
        self.for_frame_update.put(update_data)

    

    def _init_multithreading_workers(self) -> None:
        """Start all threads used for the GUI"""
        self.workers = {}

        workers_settings = {
            "live_view": [CustomWorker, 0.05, self._poll_live_view]
        }

        for key, data in workers_settings.items():
            self.workers[key] = data[0](data[1])
            self.workers[key].progress.connect(data[2])
            self.workers[key].start()
            self.workers[key].start_polling()


    ############################################################################
    # Live view


    def handle_meas_status_change(self):
        self.update_gui(LiveStatus(self.meas_status))
        self.meas_status.ack_change()
        if self.meas_status.is_set(LiveMeasState.Measuring):
            self.replay_status.clear()
            self.capture_module.set_meas()
        else:
            self.capture_module.set_idle()
            self._live_capture_start(look_memory_flag=True)
    
        self.update_gui(ReplayStatus(self.replay_status))

    def handle_replay_status_change(self):
        """"""
        self.update_gui(ReplayStatus(self.replay_status))
        self.replay_status.ack_change()

    def _poll_live_view(self) -> None:
        """Called by live_view_worker
        """
        self.poll_input_buf()
        self.is_device_unplugged()

    def poll_input_buf(self):
        """Get last RX Frame contained in the input_buffer"""

        if self.for_frame_update.empty():
            return
        data = self.for_frame_update.get(block=True)

        self.update_gui(data)

    def is_device_unplugged(self) -> None:
        """Check if the device has been unplugged or turned off
        in that case a msgBox will be displayed to inform the user after the ack
        of the user(click on "OK"-Button) the list of available
        devices will be refreshed"""
        if (
            self.interface._not_connected()
            and self.interface.status_prompt != self.lab_device_status.text()
        ):
            self.update_gui(DevStatus(self.interface.connected(), self.interface.status_prompt))
            show_msgBox(
                "The device has been disconnected!",
                "Error: Device disconnected",
                "Critical",
            )
            self._refresh_device_list()

    ############################################################################
    #### GUI updating method
    ############################################################################

    def update_gui(self, data=None):
        """_summary_

        Args:
            data (_type_, optional): should be a an EvtDataclass . Defaults to None.
        """
        self.update_event.post_event_data(data)

    ############################################################################
    #### Logging
    ############################################################################
    
    def _update_log(self) -> None:
        """Modify the actual logging level"""
        glob_utils.log.log.change_level_logging(
            LOG_LEVELS[self.cB_log_level.currentText()]
        )

    ############################################################################
    #### Interaction with Device
    ############################################################################

    def _refresh_device_list(self) -> None:
        """Refresh the list of available sciospec devices"""
        devs= self.interface.get_available_devices()
        self.update_gui(DevAvailables(devs))

    def _connect_device(self) -> None:
        """Connect with selected sciospec device"""
        device_name = str(self.cB_ports.currentText())  # get actual ComPort
        self.interface.connect_device(device_name, baudrate=115200)
        self.update_gui(
            DevStatus(self.interface.connected(), self.interface.status_prompt))
        
    def _disconnect_device(self) -> None:
        """Disconnect the sciospec device"""
        self.interface.disconnect_sciospec_device()
        self.update_gui(
            DevStatus(self.interface.connected(), self.interface.status_prompt))

    def _get_device_setup(self) -> None:
        """Get setup of the sciospec device and display it"""
        self.interface.get_setup()
        self.update_gui(DevSetup(self.interface.setup))

    def _set_device_setup(self) -> None:
        """Set the displayed setup of the sciospec device"""
        self._update_dev_setup()
        self.interface.set_setup()
        self._get_device_setup()

    def _softreset_device(self) -> None:
        """Reset the sciopec device"""
        self.interface.software_reset()
        self.update_gui(
            DevStatus(self.interface.connected(), self.interface.status_prompt))

    def _start_measurement(self) -> None:
        """Start measurements on sciopec device"""
        if self.meas_status.is_set(LiveMeasState.Idle):
            self._set_device_setup()
            success, self.last_meas_dir = self.interface.start_meas(
                self.lE_meas_dataset_dir.text()
            )
            if success:
                self.init_gui_for_live_meas()
                self.meas_status.change_state(LiveMeasState.Measuring)

        elif self.meas_status.is_set(LiveMeasState.Measuring):
            self.interface.stop_meas()
            self.meas_status.change_state(LiveMeasState.Paused)

        elif self.meas_status.is_set(LiveMeasState.Paused):
            if self.interface.resume_meas():
                self.meas_status.change_state(LiveMeasState.Measuring)

    def _stop_measurement(self) -> None:
        """Start measurements on sciopec device"""
        if self.meas_status.is_set(LiveMeasState.Measuring) or self.meas_status.is_set(
            LiveMeasState.Paused
        ):
            self.interface.stop_meas()
            self.meas_status.change_state(LiveMeasState.Idle)
            self.update_gui(FrameProgress( 0, 0))
            if self.chB_load_after_meas.isChecked():
                self._load_meas_set(self.last_meas_dir)
        # self.frame_cnt_old =-1 # reset

    def _save_setup(self) -> None:
        """Save setup of sciopec device"""
        self.interface.save_setup(dir=None)

    def _load_setup(self) -> None:
        """Load setup of sciopec device"""
        self.interface.load_setup()
        self.update_gui(DevSetup(self.interface.setup))


    def _update_dev_setup(self) -> None:
        """Save user entry from Gui in setup of dev"""
        ## Update Measurement Setups
        self.interface.setup.set_frame_rate(self.sBd_frame_rate.value())
        self.interface.setup.set_burst(self.sB_burst.value())
        self.interface.setup.set_exc_amp(self.sBd_exc_amp.value() / 1000)  # mA -> A

        freq_max_enable, error = self.interface.setup.set_freq_config(
            freq_min=self.sBd_freq_min.value(),
            freq_max=self.sBd_freq_max.value(),
            freq_steps=self.sB_freq_steps.value(),
            freq_scale=self.cB_scale.currentText(),
        )
        ## Outputconfig Stamps all to one
        self.interface.setup.set_dhcp(True)  # self.chB_dhcp.isChecked()
        self.interface.setup.set_exc_stamp(True)  #
        # self.chB_exc_stamp.isChecked() or True)
        self.interface.setup.set_current_stamp(True)
        # self.chB_current_stamp.isChecked() or True)
        self.interface.setup.set_time_stamp(True)
        # self.chB_time_stamp.isChecked()
        
        self.update_gui(DevSetup(self.interface.setup, freq_max_enable, error))
    
    ############################################################################
    #### Reconstruction
    ############################################################################
    def _init_rec(self) -> None:
        """[summary]"""
        # set some
        # rec = {0: ReconstructionPyEIT, 1: ReconstructionAI}
        rec = {0: eit_model.solver_pyeit.SolverPyEIT}
        self._set_solvers_parameters()
        self.U = np.random.rand(256, 2)
        self.labels = ["test", "test", "test", "test"]
        self.computing.set_eit_model(self.eit_model)
        self.computing.set_solver(rec[self.tabW_reconstruction.currentIndex()])
        self.computing.init_solver()
        
        # self.io_interface.put_queue_out(("random", 0, RecCMDs.initialize))

    def _set_solvers_parameters(self) -> None:
        """[summary]"""
        # self.eit_model.p=self.eit_p.value()
        # self.eit_model.lamb=self.eit_lamda.value()
        # self.eit_model.n=self.eit_n.value()
        # self.eit_model.set_solver(self.cB_solver.currentText())
        # self.eit_model.fem.refinement=self.eit_FEMRefinement.value()

    def _loadRef4TD(self) -> None:
        """[summary]"""

        try:

            file_path = dialog_get_file_with_ext(
                ext=FileExt.pkl, title="", initialdir=APP_DIRS.get(AppDirs.meas_set)
            )
        except OpenDialogFileCancelledException:
            return

        # path, cancel= openFileNameDialog(
        #     self,path=APP_DIRS.get(AppDirs.meas_set))
        # if cancel: # Cancelled
        #     return
        self._UpdateRef4TD(path=file_path)

    def _UpdateRef4TD(self, path=None) -> None:
        """[summary]

        Args:
            path ([type], optional): [description]. Defaults to None.
        """
        if self.meas_status.is_set(LiveMeasState.Measuring) == True:
            # Frame to use is ._last_frame[0] is the last updated...
            self.dataset.set_frame_TD_ref()
        else:
            self.dataset.set_frame_TD_ref(
                self.cB_current_idx_frame.currentIndex(), path=path
            )

    def _load_eidors_fwd_solution(self) -> None:  # for Jiawei master thesis
        """load eidors foward solution(voltages) out of an mat-file"""

        sol = matlab.load_mat_var(initialdir=os.getcwd(), var_name="X")
        U, _ = sol[0]
        volt = np.array(U).reshape((16, 16))

        self.eidors_sol = volt
        self._extracted_from__eidors_reload_9(volt)

    def _eidors_reload(self) -> None:  # for Jiawei master thesis
        """replot the data witha different scaling factor"""
        volt = self.eidors_sol
        self._extracted_from__eidors_reload_9(volt)

    def _extracted_from__eidors_reload_9(self, volt):
        volt = volt * self.sB_eidors_factor.value()
        self.dataset.set_voltages(volt, 0, 0)
        self.dataset.set_frame_TD_ref(0)
        self._replay_slider_changed()

    def _export_data_meas_vs_eidors(self) -> None:
        """export the actual raw data in csv from"""
        frame, freq = (
            self.slider_replay.sliderPosition(),
            self.cB_freq_meas_0.currentIndex(),
        )
        data = {
            "measurement": np.real(
                self.dataset.get_voltages(frame, freq)[:, 0:16]
            ),
            "eidors": self.eidors_sol,
        }
        file_path = os.path.join(
            self.dataset.output_dir, f"eidorsvsmeas#{frame}_freq{freq}"
        )
        save_as_csv(file_path, data)
        logger.debug(f"Measurements VS Eidors exported as CSV in : {file_path}")

    def _update_eit_ctlg(self):
        """Update catalog and if changed"""
        files = search_for_file_with_ext(
            APP_DIRS.get(AppDirs.eit_model.value), FileExt.mat
        )
        set_comboBox_items(self.cB_eit_mdl_ctlg, files)

    def _set_eit_ctlg(self):
        """Update catalog and if changed"""
        path = os.path.join(
            APP_DIRS.get(AppDirs.eit_model.value), self.cB_eit_mdl_ctlg.currentText()
        )
        self.eit_model.load_matfile(path)

    ############################################################################
    #### Replay of Measurements
    ############################################################################

    def _autosave(self) -> None:
        """update selected autosave mode"""

        autosave= self.chB_dataset_autosave.isChecked()
        save_img= self.chB_dataset_save_img.isChecked()
        self.dataset.autosave.set(autosave)
        self.dataset.save_img.set(save_img and autosave)

        logger.debug(
            f"Autosave: {self.dataset.autosave.is_set()}, save_img:{self.dataset.save_img.is_set()}"
        )
        self.update_gui(AutosaveOptions())
        

    def _load_meas_set(self) -> None:
        """the callback has to be witouh arguments!"""
        self._load_meas_set()

    @_abort_if_measuring
    @catch_error
    def _load_meas_set(self, dir_path: str = None) -> None:
        """[summary]

        Args:
            dir_path (str, optional): [description]. Defaults to None.
        """
        if self.live_capture.is_set():
            self._live_capture_stop()
            show_msgBox("Live video stopped", "Live video still running", "Information")

        self.replay_status.clear()
        files= self.dataset.load(dir_path)
        if files is not None:
            return
        self.interface.load_setup(self.dataset.output_dir)
        self.replay_status.set()
        self.update_gui(DevSetup(self.interface.setup))
        self.update_gui(MeasDatasetLoaded(self.dataset.output_dir, self.dataset.frame_cnt))
        self._compute_meas_frame(0)

    def _replay_play(self) -> None:
        
        logger.debug(f"{self.reply_timerqt.isActive()}")
        if self.reply_timerqt.isActive():
            logger.debug("PAUSE")
            self._replay_stop()
        else:
            logger.debug("PLAY")
            self._replay_set_timeout()
            self.reply_timerqt.start()

        self.update_gui(ReplayButton(self.reply_timerqt.isActive()))

    def _replay_back_begin(self) -> None:
        self._replay_stop()
        set_slider(self.slider_replay, set_pos=0)

    def _replay_goto_end(self) -> None:
        self._replay_stop()
        set_slider(self.slider_replay, set_pos=-1)

    def _replay_stop(self) -> None:
        """[summary]"""
        self.reply_timerqt.stop()
        self.update_gui(ReplayButton(self.reply_timerqt.isActive()))

    def _replay_slider_changed(self) -> None:
        idx_frame = self.slider_replay.sliderPosition()
        self.cB_current_idx_frame.setCurrentIndex(idx_frame)
        self._compute_meas_frame(idx_frame)

    def _current_frame_selected(self) -> None:
        idx_frame = self.cB_current_idx_frame.currentIndex()
        set_slider(self.slider_replay, set_pos=idx_frame)
        self._compute_meas_frame(idx_frame)

    def _replay_set_timeout(self) -> None:
        msec=int(self.sB_replay_time.value()*1000)
        logger.info(f"new Timeout in msec:{msec}")
        self.reply_timerqt.setInterval(msec)
    
    def replay_next_frame(self) -> None:
        """Generate the increment pulse for the replay function"""
        set_slider(self.slider_replay, next=True, loop=True)

    @_abort_if_measuring
    def _compute_meas_frame(self, idx_frame: int = 0) -> None:
        if not self.replay_status.is_set() :
            show_msgBox(
                "First load a measuremment dataset",
                "Replay mode not activated",
                "Warning",
            )
            return
        self.dataset.emit_frame(idx_frame)
        self.get_picture(idx_frame=idx_frame)

    def _export_meas_csv(self) -> None:
        """Export the actual measurments frames in csv"""
        idx_freq = self.cB_freq_meas_0.currentIndex()
        n = self.dataset.get_frame_cnt()
        data = {
            f"frame{i}": np.real(self.dataset.get_voltages(i, idx_freq)[:, 0:16])
            for i in range(n)
        }
        freq = self.dataset.meas_frame[0].get_freq_val(idx_freq)

        file_path = os.path.join(
            self.dataset.output_dir, f"Meas#1-{n}_freq{freq}Hz"
        )
        save_as_csv(file_path, data)
        logger.debug(f"Measurements exported as CSV in : {file_path}")

    ############################################################################
    #### Interaction with Microcam
    ############################################################################
    
    @_abort_if_measuring
    def _live_capture_start(self, look_memory_flag: bool = False) -> None:
        # if self.meas_status.is_set(LiveMeasState.Measuring):
        #     show_msgBox("First stop measurement", "Measurement is running", "Warning")
        #     return
        if look_memory_flag and not self.live_capture.is_set():
            return
        self.capture_module.set_live()
        self.live_capture.set()

    @_abort_if_measuring
    def _live_capture_stop(self, memory_flag: bool = False) -> None:
        # if self.meas_status.is_set(LiveMeasState.Measuring):
        #     show_msgBox("First stop measurement", "Measurement is running", "Warning")
        #     return
        self.capture_module.set_idle()
        if not memory_flag:
            self.live_capture.clear()

    def _capture_snapshot(self) -> None:
        """Save"""
        path = os.path.join(
            APP_DIRS.get(AppDirs.snapshot), f"Snapshot_{get_datetime_s()}"
        )
        self.capture_module.snapshot(path=path)

    def _refresh_capture_devices(self) -> None:
        capture_devices = self.capture_module.get_devices_available()
        set_comboBox_items(self.cB_video_devices, capture_devices)

    @_abort_if_measuring
    def _set_capture_device(self) -> None:
        # if self.meas_status.is_set(LiveMeasState.Measuring):
        #     show_msgBox("First stop measurement", "Measurement is running", "Warning")
        #     return
        self._live_capture_stop(memory_flag=True)
        self.capture_module.select_device(self.cB_video_devices.currentText())
        self.capture_module.set_image_size(self.cB_img_size.currentText())
        self.capture_module.set_image_file_format(
            file_ext=self.cB_img_file_ext.currentText()
        )
        self._live_capture_start(look_memory_flag=True)

    def get_picture(self, idx_frame: int) -> None:
        if not self.replay_status.is_set():  # only in replay mode
            return
        path = self.dataset.get_frame_path(idx_frame)
        path, _ = os.path.splitext(path)
        path = path + self.capture_module.image_file_ext
        self.capture_module.load_image(path)

    ############################################################################
    #### Plotting
    ############################################################################

    def _imaging_params_changed(self) -> None:

        rec_type = self.cB_eit_imaging_type.currentText()
        if rec_type not in list(IMAGING_TYPE.keys()):
            raise Exception(f"The imaging type {rec_type} ist not known")

        transform_volt = self.cB_transform_volt.currentText()
        if transform_volt not in DATA_TRANSFORMATIONS:
            raise Exception(f"The transformation {transform_volt} unknown")

        idx_freqs = [
            self.cB_freq_meas_0.currentIndex(),
            self.cB_freq_meas_1.currentIndex(),
        ]
        idx_ref_frame = self.cB_ref_frame_idx.currentIndex()

        transform_funcs = [
            DATA_TRANSFORMATIONS[transform_volt],
            DATA_TRANSFORMATIONS["Abs"]
            if self.showAbsValue.isChecked()
            else DATA_TRANSFORMATIONS["Identity"],
        ]

        self.imaging_type: Imaging = IMAGING_TYPE[rec_type](transform_funcs)

        index= [
            [self.cB_current_idx_frame.currentIndex(),self.cB_freq_meas_0.currentIndex()],
            [self.cB_current_idx_frame.currentIndex(),self.cB_freq_meas_1.currentIndex()]
        ]

        self.dataset.set_index_of_data_for_computation(index)
        self.update_gui(ImagingInputs(self.imaging_type))

        self.computing.set_imaging_mode(self.imaging_type)
        self.computing.set_eit_model(self.eit_model)
        # if not self.live_view.is_set():
        #     self.compute_measurement()

    def _plots_to_show(self) -> None:

        self.canvas_rec.set_visible(self.chB_plot_image_rec.isChecked())
        self.computing.enable_rec(self.chB_plot_image_rec.isChecked())
        self.update_gui(EITdataPlotOptions())

    

    def init_gui_for_live_meas(self) -> None:
        self.update_gui(FrameInfo(""))
        # self.live_meas_status.change_state(LiveMeasState.Measuring)

    def closeEvent(self, event) -> None:
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

    def kill_workers(self) -> None:
        """Kill alls the running threads workers"""
        [item.quit() for _, item in self.workers.items()]

    def get_current_frame_cnt(self) -> int:
        return self.dataset.get_frame_cnt()

    @catch_error
    def _update_canvas(self, data) -> None:
        """"""
        # dataset: EitMeasurementSet = data["dataset"]
        # idx_frame = data["idx_frame"]
        # t = time.time()

        # self.figure_graphs = plot_measurements(
        #     self.plots_to_show, self.figure_graphs, data
        # )
        # self.canvas_graphs.draw()
        # elapsed = time.time() - t
        # if dataset == "random":
        #     return
        # # voltages= dataset.get_voltages(idx_frame, 0)
        # # if voltages is not None:
        # #     set_table_widget(self.tableWidgetvoltages_Z, voltages)
        # #     meas_voltage=np.real(voltages[:,:self.eit_model.n_el].flatten())
        # #     ax=self.figure_ch_graph.add_subplot(1,1,1)
        # #     ax.plot(meas_voltage, '-b')
        # #     self.canvas_ch_graph.draw()
        # if isinstance(dataset, EitMeasurementSet):
        #     idx, t = dataset.get_idx_frame(idx_frame), get_datetime_s()
        #     logger.debug(f"Plot Frame #{idx}, time {t}, lasted {elapsed}")

    def display_image(self, image: QtGui.QImage) -> None:
        if not isinstance(image, QtGui.QImage):
            logger.error(f"{image=} is not an QtGui.QImage")
            return
        self.video_frame.setPixmap(QtGui.QPixmap.fromImage(image))

    


if __name__ == "__main__":
    """"""
