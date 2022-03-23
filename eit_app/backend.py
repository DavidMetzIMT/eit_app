from __future__ import absolute_import, division, print_function
import logging
import os
import threading
from logging import getLogger
from typing import Any
import eit_ai.raw_data.load_eidors as matlab
import eit_model.model
import eit_model.solver_pyeit
import glob_utils.log.log
import matplotlib
import matplotlib.backends.backend_qt5agg
import matplotlib.pyplot
import numpy as np
from default.set_default_dir import APP_DIRS, AppDirs, set_ai_default_dir
from eit_model.imaging_type import (DATA_TRANSFORMATIONS, IMAGING_TYPE,
                                    ChannelVoltageImaging)
from glob_utils.files.files import (FileExt, OpenDialogFileCancelledException,
                                    dialog_get_file_with_ext, save_as_csv,
                                    search_for_file_with_ext)
from glob_utils.flags.flag import CustomFlag, CustomFlagwSignals
from glob_utils.msgbox import  warningMsgBox
from PyQt5 import QtCore, QtGui, QtWidgets
import eit_app.eit.plots
from eit_app.eit.computation import ComputingAgent
from eit_app.eit.plots import (CanvasLayout, LayoutEITChannelVoltage,
                               LayoutEITData, LayoutEITImage2D)
from eit_app.gui import Ui_MainWindow as app_gui
from eit_app.gui_utils import (set_comboBox_items)
from eit_app.io.sciospec.com_constants import OP_LINEAR, OP_LOG
from eit_app.io.sciospec.device import SciospecEITDevice
from eit_app.io.sciospec.measurement import ExtractIndexes, MeasurementDataset
from eit_app.io.sciospec.replay import ReplayMeasurementsAgent
from eit_app.io.video.microcam import MicroUSBCamera
from eit_app.io.video.capture import EXT_IMG, IMG_SIZES,VideoCaptureAgent
from eit_app.com_channels import AddUpdateAgent

from eit_app.update_gui import (EvtDataAutosaveOptionsChanged,
                                EvtDataEITDataPlotOptionsChanged,
                                EvtDataImagingInputsChanged,
                                EvtDataSciospecDevSetup)

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


class UiBackEnd(app_gui, QtWidgets.QMainWindow, AddUpdateAgent):
    def __init__(self) -> None:
        super().__init__()
        self._initilizated = CustomFlag()
        self.setupUi(self)  # setup the UI created with designer
        self.set_title()
        set_ai_default_dir()
        self._create_main_objects()
        self._connect_main_objects()
        self._init_values()
        self._initilizated.set()
    
    def set_title(self)->None:
        t= f"EIT aquisition for Sciospec device {__version__}"
        self.setWindowTitle(QtCore.QCoreApplication.translate("MainWindow", t ))

    def _create_main_objects(self) -> None:

        # set canvas
        self.plot_agent=eit_app.eit.plots.PlottingAgent()
        self.canvas_rec=CanvasLayout(self, self.layout_rec, LayoutEITImage2D)
        self.plot_agent.add_layouts(self.canvas_rec)
        self.canvas_graphs=CanvasLayout(self, self.layout_graphs, LayoutEITData)
        self.plot_agent.add_layouts(self.canvas_graphs)
        self.canvas_ch_graph=CanvasLayout(self, self.layout_ch_graph, LayoutEITChannelVoltage)
        self.plot_agent.add_layouts(self.canvas_ch_graph)

        self.eit_model = eit_model.model.EITModel()
    
        self.computing = ComputingAgent()
        self.dataset = MeasurementDataset()

        self.device = SciospecEITDevice(32)

        # self.replay_status = CustomFlagwSignals()
        # self.replay_timerqt= QtCore.QTimer()

        self.replay_agent= ReplayMeasurementsAgent()

        self.live_capture = CustomFlag()
        # setting of the camera
        self.capture_agent = VideoCaptureAgent(
            capture_type= MicroUSBCamera(), 
            snapshot_dir=APP_DIRS.get(AppDirs.snapshot)
        )
    
    def _connect_main_objects(self)->None:

        self.computing.to_plot.connect(self.plot_agent.to_reciever)

        self.dataset.to_gui.connect(self.to_reciever)
        self.dataset.to_computation.connect(self.computing.to_reciever)
        self.dataset.to_device.connect(self.device.to_reciever)
        self.dataset.to_capture.connect(self.capture_agent.to_reciever)
        self.dataset.to_replay.connect(self.replay_agent.to_reciever)

        self.device.to_gui.connect(self.to_reciever)
        self.device.to_dataset.connect(self.dataset.to_reciever)

        self.device.to_capture.connect(self.capture_agent.to_reciever)

        self.replay_agent.to_gui.connect(self.to_reciever)
        self.replay_agent.to_dataset.connect(self.dataset.to_reciever)
        self.replay_agent.to_capture.connect(self.capture_agent.to_reciever)

        self.capture_agent.to_gui.connect(self.to_reciever)
        self.capture_agent.new_image.connect(self.display_image)

        # set pattern
        self.eit_model.load_defaultmatfile()
        exc_mat= self.eit_model.excitation_mat()+1
        self.device.setup.set_exc_pattern(exc_mat.tolist())
    

    def _init_values(self) -> None:

        # link callbacks
        self._link_callbacks()
        self.comboBox_init()


        self._update_log()
        self._get_dev_setup()
        self._plots_to_show()
        self._imaging_params_changed()
        self._ch_imaging_params()
        self._autosave()

        self.capture_agent.get_devices_available()
        self.capture_agent.emit_status_changed()

        self.device.get_devices()
        self.device.to_gui_emit_connect_status()
        self.device.emit_status_changed()

        # self.update_gui(ReplayStatus(self.replay_status))
        # self._init_update_worker()
        logger.info(f"thread main {threading.get_ident()}") 

    def comboBox_init(self) -> None:
        """ """
        set_comboBox_items(self.cB_log_level, list(LOG_LEVELS.keys()))
        set_comboBox_items(self.cB_scale, [OP_LINEAR.name, OP_LOG.name])
        set_comboBox_items(self.cB_solver, ["JAC", "BP", "GREIT"])
        set_comboBox_items(self.cB_eit_imaging_type, list(IMAGING_TYPE.keys()))
        set_comboBox_items(
            self.cB_transform_volt, list(DATA_TRANSFORMATIONS.keys())[:4]
        )
        set_comboBox_items(
            self.cB_transform_ch_volt, list(DATA_TRANSFORMATIONS.keys())[:4]
        )
        set_comboBox_items(self.cB_img_size, list(IMG_SIZES.keys()), init_index=-1)
        set_comboBox_items(self.cB_img_file_ext, list(EXT_IMG.keys()))
        set_comboBox_items(self.cB_ref_frame_idx, [0])
        self._update_eit_ctlg()

    def _link_callbacks(self) -> None:
        """ """
        self.cB_log_level.activated.connect(self._update_log)

        # device relative callbacks
        self.pB_refresh.clicked.connect(self.device.get_devices)
        self.pB_connect.clicked.connect(self.device.connect_device)
        self.pB_disconnect.clicked.connect(self.device.disconnect_device)
        self.pB_get_setup.clicked.connect(self.device.get_setup)
        self.pB_set_setup.clicked.connect(self.device.set_setup)
        self.pB_reset.clicked.connect(self.device.software_reset)
        self.pB_save_setup.clicked.connect(self.device.save_setup)
        self.pB_load_setup.clicked.connect(self.device.load_setup)
        self.pB_start_meas.clicked.connect(self.device.start_paused_resume_meas)
        self.pB_stop_meas.clicked.connect(self.device.stop_meas)

        self.cB_ports.activated[str].connect(self.device.set_device_name)

        self.sBd_freq_min.valueChanged.connect(self._get_dev_setup)
        self.sBd_freq_max.valueChanged.connect(self._get_dev_setup)
        self.sB_freq_steps.valueChanged.connect(self._get_dev_setup)
        self.cB_scale.activated.connect(self._get_dev_setup)
        self.sBd_frame_rate.valueChanged.connect(self._get_dev_setup)

        self.lE_meas_dataset_dir.textChanged.connect(self._autosave)
        self.chB_dataset_autosave.toggled.connect(self._autosave)
        self.chB_dataset_save_img.toggled.connect(self._autosave)
        self.chB_load_after_meas.toggled.connect(self._autosave)
        # frame plot/
        self.cB_current_idx_frame.activated[int].connect(self.replay_agent.set_actual_frame)
        self.chB_plot_graph.toggled.connect(self._plots_to_show)
        self.chB_Uplot.toggled.connect(self._plots_to_show)
        self.chB_diff.toggled.connect(self._plots_to_show)
        self.chB_plot_image_rec.toggled.connect(self._plots_to_show)
        self.chB_y_log.toggled.connect(self._plots_to_show)

        # loading measurements / replay
        self.pB_load_meas_dataset.clicked.connect(self.dataset.load)
        self.pB_replay_begin.clicked.connect(self.replay_agent.begin)
        self.pB_replay_end.clicked.connect(self.replay_agent.end)
        self.pB_replay_play.clicked.connect(self.replay_agent.play)
        self.pB_replay_next.clicked.connect(self.replay_agent.next)
        self.pB_replay_back.clicked.connect(self.replay_agent.back)
        self.pB_replay_stop.clicked.connect(self.replay_agent.stop)
        self.sB_replay_time.valueChanged[float].connect(self.replay_agent.set_timeout)
        self.slider_replay.valueChanged[int].connect(self.replay_agent.set_actual_frame)
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
        self.scalePlot_vmax.valueChanged.connect(self._get_solvers_params)
        self.scalePlot_vmin.valueChanged.connect(self._get_solvers_params)
        self.normalize.toggled.connect(self._get_solvers_params)
        self.eit_FEMRefinement.valueChanged.connect(self._get_solvers_params)
        # self.cB_solver.activated.connect(self._set_reconstruction)

        # eit imaging
        self.pB_compute.clicked.connect(self.replay_agent.compute_actual_frame)
        self.cB_eit_imaging_type.activated.connect(self._imaging_params_changed)
        self.cB_ref_frame_idx.currentIndexChanged.connect(
            self._imaging_params_changed
        )
        self.cB_freq_meas_0.activated.connect(self._imaging_params_changed)
        self.cB_freq_meas_1.activated.connect(self._imaging_params_changed)
        self.cB_transform_volt.activated.connect(self._imaging_params_changed)
        self.showAbsValue.toggled.connect(self._imaging_params_changed)
        self.chB_abs_ch_vol.toggled.connect(self._ch_imaging_params)
        self.cB_transform_ch_volt.activated.connect(self._ch_imaging_params)

        self.cB_eit_mdl_ctlg.currentTextChanged.connect(self._set_eit_ctlg)
        self.pB_refresh_eit_mdl_ctlg.clicked.connect(self._update_eit_ctlg)

        # Video capture
        self.pB_refresh_video_devices.clicked.connect(self.capture_agent.get_devices_available)
        self.pB_capture_start_stop.clicked.connect(self.capture_agent.start_stop_capture)
        self.pB_capture_stop.clicked.connect(self.capture_agent.capture_stop)
        self.pB_capture_snapshot.clicked.connect(self.capture_agent.snapshot)
        self.cB_video_devices.activated.connect(self._set_capture_device)
        self.cB_img_size.activated.connect(self._set_capture_device)
        self.cB_img_file_ext.activated.connect(self._set_capture_device)
        
    def _abort_if_measuring(func):
        '''Decorator '''
    
        def wrap(self, *args, **kwargs)-> Any:
            if self.device.is_measuring:
                warningMsgBox("Measurement is running","First stop measurement")
                return
            return func(self, *args, **kwargs)
        return wrap

    ############################################################################
    #### callback for the change of status which are signal-based
    ############################################################################
    
    # def handle_meas_status_change(self):
    #     if self.device.is_measuring or self.device.is_paused:
    #         self.replay_status.clear()
    #         # self.capture_module.set_meas()
    #     else:
    #         # self.capture_module.set_idle()
    #         self._live_capture_start(look_memory_flag=True)
    
    #     self.update_gui(ReplayStatus(self.replay_status))

    # def handle_replay_status_change(self):
    #     """"""
    #     self.update_gui(ReplayStatus(self.replay_status))
    #     self.replay_status.ack_change()

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

    def _get_dev_setup(self) -> None:
        """Save user entry from Gui in setup of device"""
        self.device.setup.set_frame_rate(self.sBd_frame_rate.value())
        self.device.setup.set_burst(self.sB_burst.value())
        self.device.setup.set_exc_amp(self.sBd_exc_amp.value() / 1000)  # mA -> A
        freq_max_enable, error = self.device.setup.set_freq_config(
            freq_min=self.sBd_freq_min.value(),
            freq_max=self.sBd_freq_max.value(),
            freq_steps=self.sB_freq_steps.value(),
            freq_scale=self.cB_scale.currentText()
        )
        self.update_gui(EvtDataSciospecDevSetup(self.device.setup, freq_max_enable, error))

    ############################################################################
    #### Reconstruction
    ############################################################################
    def _init_rec(self) -> None:
        """[summary]"""
        rec_type= self.tabW_reconstruction.currentIndex()
        solver= self._get_solver(rec_type)
        params= self._get_solvers_params(rec_type)
        self.computing.set_eit_model(self.eit_model)
        self.computing.set_solver(solver)
        self.computing.set_rec_params(params)
        self.computing.init_solver()

    def _get_solver(self,rec_type:int=0) -> None:
        """[summary]"""
        rec = {
            0: eit_model.solver_pyeit.SolverPyEIT
        }
        return rec[rec_type]

    def _get_solvers_params(self,rec_type:int=0) -> None:
        """[summary]"""
        params = {
            0:  eit_model.solver_pyeit.PyEitRecParams(
                    solver_type=self.cB_solver.currentText(),
                    p=self.eit_p.value(),
                    lamb=self.eit_lamda.value(),
                    n=self.eit_n.value()
                )
        }
        return params[rec_type]
        # self.eit_model.fem.refinement=self.eit_FEMRefinement.value()

    def _loadRef4TD(self) -> None:
        """[summary]"""

        try:
            file_path = dialog_get_file_with_ext(
                ext=FileExt.pkl, title="", initialdir=APP_DIRS.get(AppDirs.meas_set)
            )
        except OpenDialogFileCancelledException:
            return
        self._UpdateRef4TD(path=file_path)

    def _UpdateRef4TD(self, path=None) -> None:
        """[summary]

        Args:
            path ([type], optional): [description]. Defaults to None.
        """
        if self.device.is_measuring or self.device.is_paused:
            # Frame to use is ._last_frame[0] is the last updated...
            self.dataset.set_ref_frame()
        else:
            self.dataset.set_ref_frame(
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
        self.dataset.set_ref_frame(0)
        # self._replay_slider_changed()

    def _export_data_meas_vs_eidors(self) -> None:
        """export the actual raw data in csv from"""
        frame, freq = (
            self.slider_replay.sliderPosition(),
            self.cB_freq_meas_0.currentIndex(),
        )
        data = {
            "measurement": np.real(
                self.dataset.get_meas_voltage(frame, freq)[:, 0:16]
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

        self.dataset.set_name(self.lE_meas_dataset_dir.text())

        autosave= self.chB_dataset_autosave.isChecked()
        save_img= self.chB_dataset_save_img.isChecked()
        self.dataset._autosave.set(autosave)
        self.dataset._save_img.set(save_img and autosave)

        logger.debug(
            f"Autosave: {self.dataset._autosave.is_set()}, save_img:{self.dataset._save_img.is_set()}"
        )
        self.update_gui(EvtDataAutosaveOptionsChanged())
        

    # def _load_meas_set(self) -> None:
    #     """the callback has to be witouh arguments!"""
    #     self._load_meas_set()

    # @_abort_if_measuring
    # @catch_error
    # def _load_meas_set(self, dir_path: str = None) -> None:
    #     """[summary]

    #     Args:
    #         dir_path (str, optional): [description]. Defaults to None.
    #     """
    #     if self.live_capture.is_set():
    #         self._live_capture_stop()
    #         infoMsgBox("Live video still running","Live video stopped")

    #     self.replay_status.clear()
    #     files= self.dataset.load(dir_path)
    #     if files is not None:
    #         return
    #     self.device.load_setup(self.dataset.output_dir)
    #     self.replay_status.set()
    #     self._compute_meas_frame(0)

    # def _replay_play(self) -> None:
        
    #     logger.debug(f"{self.replay_timerqt.isActive()}")
    #     if self.replay_timerqt.isActive():
    #         logger.debug("PAUSE")
    #         self._replay_stop()
    #     else:
    #         logger.debug("PLAY")
    #         self._replay_set_timeout()
    #         self.replay_timerqt.start()

    #     # self.update_gui(ReplayButton(self.replay_timerqt.isActive()))

    # def _replay_begin(self) -> None:
    #     set_QSlider_position(self.slider_replay, pos=0)

    # def _replay_end(self) -> None:
    #     set_QSlider_position(self.slider_replay, pos=-1)
    
    # def _replay_next(self) -> None:
    #     inc_QSlider_position(self.slider_replay, forward=True)

    # def _replay_back(self) -> None:
    #     inc_QSlider_position(self.slider_replay, forward=False)

    # def _replay_stop(self) -> None:
    #     """[summary]"""
    #     self.replay_timerqt.stop()
    #     # self.update_gui(ReplayButton(self.replay_timerqt.isActive()))

    # def _replay_slider_changed(self) -> None:
    #     idx_frame = self.slider_replay.sliderPosition()
    #     self.cB_current_idx_frame.setCurrentIndex(idx_frame)
    #     self._compute_meas_frame(idx_frame)

    # def _current_frame_selected(self) -> None:
    #     idx_frame = self.cB_current_idx_frame.currentIndex()
    #     set_QSlider_position(self.slider_replay, pos=idx_frame)
    #     self._compute_meas_frame(idx_frame)

    # def _replay_set_timeout(self) -> None:
    #     msec=int(self.sB_replay_time.value()*1000)
    #     logger.info(f"new Timeout in msec:{msec}")
    #     self.replay_timerqt.setInterval(msec)
    
    # @_abort_if_measuring
    # def _compute_meas_frame(self, idx_frame: int = 0) -> None:
    #     if not self.replay_status.is_set() :
    #         warningMsgBox(
    #             "Replay mode not activated",
    #             "First load a measuremment dataset"
    #         )
    #         return
    #     self.dataset.emit_meas_frame(idx_frame)
    #     self.get_picture(idx_frame=idx_frame)

    def _export_meas_csv(self) -> None:
        """Export the actual measurments frames in csv"""
        idx_freq = self.cB_freq_meas_0.currentIndex()
        n = self.dataset.get_frame_cnt()
        data = {
            f"frame{i}": np.real(self.dataset.get_meas_voltage(i, idx_freq)[:, 0:16])
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
    def _set_capture_device(self,*args, **kwargs) -> None:

        self.capture_agent.connect_device(self.cB_video_devices.currentText())
        self.capture_agent.set_image_size(self.cB_img_size.currentText())
        self.capture_agent.set_image_file_format(
            file_ext=self.cB_img_file_ext.currentText()
        )

    # def get_picture(self, idx_frame: int) -> None:
    #     if not self.replay_status.is_set():  # only in replay mode
    #         return
    #     path = self.dataset.get_meas_path(idx_frame)
    #     path, _ = os.path.splitext(path)
    #     path = path + self.capture_agent.image_file_ext
    #     self.capture_agent.load_image(path)

    ############################################################################
    #### Plotting
    ############################################################################

    def _actual_imaging_mode(self):

        imaging_mode = self.cB_eit_imaging_type.currentText()
        if imaging_mode not in list(IMAGING_TYPE.keys()):
            raise Exception(f"The imaging type {imaging_mode} ist not known")
        return imaging_mode

    def _imaging_params_changed(self) -> None:

        imaging_type = self._actual_imaging_mode()
        transform = self.cB_transform_volt.currentText()
        show_abs= self.showAbsValue.isChecked()

        eit_imaging = IMAGING_TYPE[imaging_type](transform, show_abs)
        self.computing.set_imaging_mode(eit_imaging)
        self.update_gui(EvtDataImagingInputsChanged(eit_imaging))
        self._set_actual_indexesforcomputation(imaging_type)

    def _set_actual_indexesforcomputation(self, imaging_type:str):

        index= ExtractIndexes(
            ref_idx=self.cB_ref_frame_idx.currentIndex(),
            meas_idx=self.cB_current_idx_frame.currentIndex(),
            ref_freq=self.cB_freq_meas_0.currentIndex(),
            meas_freq=self.cB_freq_meas_1.currentIndex(),
            imaging=imaging_type
        )
        self.dataset.set_index_of_data_for_computation(index)
        self.computing.set_eit_model(self.eit_model)

    def _ch_imaging_params(self) -> None:
        transform = self.cB_transform_ch_volt.currentText()
        show_abs =  self.chB_abs_ch_vol.isChecked()
        self.ch_imaging= ChannelVoltageImaging(transform, show_abs)
        self.computing.set_ch_imaging_mode(self.ch_imaging)

    def _plots_to_show(self) -> None:
        self.canvas_rec.set_visible(self.chB_plot_image_rec.isChecked())
        self.computing.enable_rec(self.chB_plot_image_rec.isChecked())
        self.update_gui(EvtDataEITDataPlotOptionsChanged())


    def display_image(self, image: QtGui.QImage= None, **kwargs) -> None:

        if not isinstance(image, QtGui.QImage):
            logger.warning(f"{image=} is not an QtGui.QImage")
            return
        self.video_frame.setPixmap(QtGui.QPixmap.fromImage(image))
        

    
    # def kill_workers(self) -> None:
    #     """Kill alls the running threads workers"""
    #     [item.quit() for _, item in self.workers.items()]


if __name__ == "__main__":
    """"""
