from __future__ import absolute_import, division, print_function


import os
import logging

import eit_model.model
import eit_model.solver_pyeit
import glob_utils.log.log
import matplotlib
import matplotlib.backends.backend_qt5agg
import matplotlib.pyplot
import numpy as np
from default.set_default_dir import AppStdDir, set_ai_default_dir, get_dir
import eit_model.imaging
from glob_utils.files.files import (
    FileExt,
    OpenDialogFileCancelledException,
    dialog_get_file_with_ext,
    save_as_csv,
    search_for_file_with_ext,
)
from glob_utils.flags.flag import CustomFlag
from glob_utils.msgbox import warningMsgBox
from PyQt5 import QtCore, QtWidgets
from eit_app.com_channels import AddUpdateAgent
from eit_app.eit.computation import ComputingAgent
from eit_app.eit.plots import (
    CanvasLayout,
    PlotterChannelVoltageMonitoring,
    PlotterEITChannelVoltage,
    PlotterEITData,
    PlotterEITImage2D,
    PlottingAgent,
)
from eit_app.gui import Ui_MainWindow
from eit_app.gui_utils import set_comboBox_items
import eit_app.sciospec.constants
from eit_app.sciospec.device import SciospecEITDevice
from eit_app.sciospec.measurement import ExtractIndexes, MeasurementDataset
from eit_app.sciospec.replay import ReplayMeasurementsAgent
from eit_app.update_gui import (
    EvtDataEITDataPlotOptionsChanged,
    EvtDataSciospecDevSetup,
)
from eit_app.video.capture import VideoCaptureAgent
from eit_app.video.microcam import MicroUSBCamera

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

logger = logging.getLogger(__name__)

class UiBackEnd(Ui_MainWindow, QtWidgets.QMainWindow, AddUpdateAgent):
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
    
    def eventFilter(self, source: QtCore.QObject, event: QtCore.QEvent) -> bool:
        
        #disable MouseWheel event on slider_replay
        if source== self.slider_replay and event.type() ==QtCore.QEvent.Wheel:
            return True

        return super().eventFilter(source, event)

    def set_title(self) -> None:
        t = f"EIT aquisition for Sciospec device {__version__}"
        self.setWindowTitle(QtCore.QCoreApplication.translate("MainWindow", t))

    def _create_main_objects(self) -> None:

        # set canvas
        self.plot_agent = PlottingAgent()
        self.canvas_rec = CanvasLayout(self, self.layout_rec, PlotterEITImage2D)
        self.plot_agent.add_canvas(self.canvas_rec)
        self.canvas_graphs = CanvasLayout(self, self.layout_graphs, PlotterEITData)
        self.plot_agent.add_canvas(self.canvas_graphs)
        self.canvas_ch_graph = CanvasLayout(
            self, self.layout_ch_graph, PlotterEITChannelVoltage
        )
        self.plot_agent.add_canvas(self.canvas_ch_graph)
        self.canvas_monitoring = CanvasLayout(
            self, self.layout_monitoring, PlotterChannelVoltageMonitoring
        )
        self.plot_agent.add_canvas(self.canvas_monitoring)
        self.eit_model = eit_model.model.EITModel()
        self.computing = ComputingAgent()
        self.dataset = MeasurementDataset()
        self.device = SciospecEITDevice(32)
        self.replay_agent = ReplayMeasurementsAgent()
        self.live_capture = CustomFlag()
        self.capture_agent = VideoCaptureAgent(
            capture_dev=MicroUSBCamera(), snapshot_dir=get_dir(AppStdDir.snapshot)
        )

    def _connect_main_objects(self) -> None:

        self.computing.to_gui.connect(self.to_reciever)
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

    
    def _init_values(self) -> None:

        self._signals_to_capture()
        self._signals_to_dataset()
        self._signals_to_dev_setup()
        self._signals_to_device()
        self._signals_to_export_import()
        self._signals_to_imaging()
        self._signals_to_log()
        self._signals_to_plot()
        self._signals_to_replay()

        self.comboBox_init()
        self._update_log()
        self._get_dev_setup()
        self._set_plots_options()
        self._imaging_changed()
        self._monitoring_params()
        self.capture_agent.get_devices()
        self.capture_agent.emit_status_changed()
        self.device.get_devices()
        self.device.to_gui_emit_connect_status()
        self.device.emit_status_changed()
        self._init_eit_model()

    def comboBox_init(self) -> None:
        """ """
        set_comboBox_items(self.cB_log_level, glob_utils.log.log.list_levels())
        set_comboBox_items(self.cB_scale, eit_app.sciospec.constants.frequency_scales())
        set_comboBox_items(self.cB_pyeit_solver, eit_model.solver_pyeit.used_solver())
        set_comboBox_items(self.cB_eit_imaging_type, eit_model.imaging.eit_imaging_types())
        set_comboBox_items(self.cB_eit_imaging_trans, eit_model.imaging.eit_data_transformations())
        set_comboBox_items(self.cB_eit_imaging_ref_frame, [0])
        set_comboBox_items(self.cB_monitoring_trans, eit_model.imaging.eit_data_transformations())

        set_comboBox_items(self.cB_capture_img_size, self.capture_agent.used_img_sizes())
        set_comboBox_items(self.cB_capture_img_file_ext, self.capture_agent.used_img_exts())
        # init catalogs which neeeds some loading
        self._update_eit_mdl_ctlg()
        self._update_chip_ctlg()

    ############################################################################
    #### Logging
    ############################################################################

    def _signals_to_log(self):
        self.cB_log_level.activated.connect(self._update_log)

    def _update_log(self) -> None:
        """Modify the actual logging level"""
        glob_utils.log.log.change_level_logging(self.cB_log_level.currentText())

    ############################################################################
    #### Device, Setup
    ############################################################################

    def _signals_to_device(self):

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
    
    def _signals_to_dev_setup(self):

        self.sBd_exc_amp.valueChanged.connect(self._get_dev_setup)
        self.sB_burst.valueChanged.connect(self._get_dev_setup)
        self.sBd_freq_min.valueChanged.connect(self._get_dev_setup)
        self.sBd_freq_max.valueChanged.connect(self._get_dev_setup)
        self.sB_freq_steps.valueChanged.connect(self._get_dev_setup)
        self.cB_scale.activated.connect(self._get_dev_setup)
        self.sBd_frame_rate.valueChanged.connect(self._get_dev_setup)

    def _get_dev_setup(self) -> None:
        """Save user entry from Gui in setup of device"""
        self.device.setup.set_frame_rate(self.sBd_frame_rate.value())
        self.device.setup.set_burst(self.sB_burst.value())
        self.device.setup.set_exc_amp(self.sBd_exc_amp.value() / 1000)  # mA -> A
        freq_max_enable, error = self.device.setup.set_freq_config(
            freq_min=self.sBd_freq_min.value(),
            freq_max=self.sBd_freq_max.value(),
            freq_steps=self.sB_freq_steps.value(),
            freq_scale=self.cB_scale.currentText(),
        )
        self.update_gui(
            EvtDataSciospecDevSetup(self.device.setup, freq_max_enable, error)
        )

    


    ############################################################################
    #### Dataset, replay
    ############################################################################

    def _signals_to_dataset(self):
        self.lE_meas_dataset_dir.textChanged[str].connect(self.dataset.set_name)
        self.chB_dataset_autosave.toggled[bool].connect(self.dataset.set_autosave)
        self.chB_dataset_save_img.toggled[bool].connect(self.dataset.set_save_img)
        self.chB_load_after_meas.toggled[bool].connect(self.dataset.set_load_after_meas)
        self.pB_meas_dataset_load.clicked.connect(self.dataset.load)
        self.pB_load_ref_dataset.clicked.connect(self._loadRef4TD)

    def _signals_to_replay(self):
        self.pB_replay_begin.clicked.connect(self.replay_agent.begin)
        self.pB_replay_end.clicked.connect(self.replay_agent.end)
        self.pB_replay_play.clicked.connect(self.replay_agent.play_pause)
        self.pB_replay_next.clicked.connect(self.replay_agent.next)
        self.pB_replay_back.clicked.connect(self.replay_agent.back)
        self.pB_replay_stop.clicked.connect(self.replay_agent.stop)
        self.sB_replay_time.valueChanged[float].connect(self.replay_agent.set_timeout)
        self.cB_replay_frame_idx.activated[int].connect(self.replay_agent.set_actual_frame)
        self.slider_replay.valueChanged[int].connect(self.replay_agent.set_actual_frame)
        self.slider_replay.installEventFilter(self)
    
    def _loadRef4TD(self) -> None:

        try:
            file_path = dialog_get_file_with_ext(
                ext=FileExt.pkl, title="", initialdir=get_dir(AppStdDir.meas_set)
            )
        except OpenDialogFileCancelledException:
            return
        self._UpdateRef4TD(path=file_path)

    def _UpdateRef4TD(self, path=None) -> None:

        if self.device.is_measuring or self.device.is_paused:
            # Frame to use is ._last_frame[0] is the last updated...
            self.dataset.set_ref_frame()
        else:
            self.dataset.set_ref_frame(
                self.cB_replay_frame_idx.currentIndex(), path=path
            )

    ############################################################################
    #### Export, import
    ############################################################################

    def _signals_to_export_import(self):
        self.pB_export_meas_csv.clicked.connect(self._export_meas_csv)

        self.pB_load_eidors_fwd_solution.clicked.connect(self._load_eidors_fwd_solution)
        self.sB_eidors_factor.valueChanged.connect(self._eidors_reload)
        self.pB_export_data_meas_vs_eidors.clicked.connect(self._export_data_meas_vs_eidors)

    def _load_eidors_fwd_solution(self) -> None:  # for Jiawei master thesis
        """load eidors foward solution(voltages) out of an mat-file"""
        warningMsgBox("Not implemented", "Not implemented")

        # sol = matlab.load_mat_var(initialdir=os.getcwd(), var_name="X")
        # U, _ = sol[0]
        # volt = np.array(U).reshape((16, 16))

        # self.eidors_sol = volt
        # self._extracted_from__eidors_reload_9(volt)

    def _eidors_reload(self) -> None:  # for Jiawei master thesis
        """replot the data witha different scaling factor"""
        warningMsgBox("Not implemented", "Not implemented")
        # volt = self.eidors_sol
        # self._extracted_from__eidors_reload_9(volt)

    def _extracted_from__eidors_reload_9(self, volt):
        warningMsgBox("Not implemented", "Not implemented")
        # volt = volt * self.sB_eidors_factor.value()
        # self.dataset.set_voltages(volt, 0, 0)
        # self.dataset.set_ref_frame(0)
        # self._replay_slider_changed()

    def _export_data_meas_vs_eidors(self) -> None:
        """export the actual raw data in csv from"""
        warningMsgBox("Not implemented", "Not implemented")
        # frame, freq = (
        #     self.slider_replay.sliderPosition(),
        #     self.cB_freq_meas_0.currentIndex(),
        # )
        # data = {
        #     "measurement": np.real(self.dataset.get_meas_voltage(frame, freq)[:, 0:16]),
        #     "eidors": self.eidors_sol,
        # }
        # file_path = os.path.join(
        #     self.dataset.output_dir, f"eidorsvsmeas#{frame}_freq{freq}"
        # )
        # save_as_csv(file_path, data)
        # logger.debug(f"Measurements VS Eidors exported as CSV in : {file_path}")

    def _export_meas_csv(self) -> None:
        """Export the actual measurments frames in csv"""
        idx_freq = self.cB_eit_imaging_meas_freq.currentIndex()
        n = self.dataset.get_frame_cnt()
        data = {
            f"frame{i}": np.real(self.dataset.get_meas_voltage(i, idx_freq)[:, 0:16])
            for i in range(n)
        }
        freq = self.dataset.meas_frame[0].get_freq_val(idx_freq)

        file_path = os.path.join(self.dataset.output_dir, f"Meas#1-{n}_freq{freq}Hz")
        save_as_csv(file_path, data)
        logger.debug(f"Measurements exported as CSV in : {file_path}")

    ############################################################################
    #### Capture
    ############################################################################

    def _signals_to_capture(self):
        self.pB_capture_refresh.clicked.connect(self.capture_agent.get_devices)
        self.pB_capture_start_stop.clicked.connect(self.capture_agent.start_stop)
        self.pB_capture_snapshot.clicked.connect(self.capture_agent.take_snapshot)
        self.cB_capture_devices.activated[str].connect(self.capture_agent.set_device_name)
        self.pB_capture_connect.clicked.connect(self.capture_agent.connect_device)
        self.cB_capture_img_size.activated[str].connect(self.capture_agent.set_image_size)
        self.cB_capture_img_file_ext.activated[str].connect(self.capture_agent.set_image_file_format)

    # def _set_capture_device(self, *args, **kwargs) -> None:
    #     self.capture_agent.set_image_size(self.cB_capture_img_size.currentText())
    #     self.capture_agent.set_image_file_format(file_ext=self.cB_capture_img_file_ext.currentText())

    ############################################################################
    #### Plotting
    ############################################################################
    
    def _signals_to_plot(self):

        self.chB_eit_data_Uplot.toggled.connect(self._set_plots_options)
        self.chB_eit_data_Udiffplot.toggled.connect(self._set_plots_options)
        self.chB_eit_data_y_log.toggled.connect(self._set_plots_options)
        self.chB_eit_image_plot.toggled.connect(self._set_plots_options)

        # self.scalePlot_vmax.valueChanged.connect(self._set_plots_options)
        # self.scalePlot_vmin.valueChanged.connect(self._set_plots_options)

    def _set_plots_options(self) -> None:
        self.canvas_rec.set_visible(self.chB_eit_image_plot.isChecked())
        self.computing.enable_rec(self.chB_eit_image_plot.isChecked())
        self.update_gui(EvtDataEITDataPlotOptionsChanged())

    ############################################################################
    #### Reconstruction, computation
    ############################################################################
    def _signals_to_rec(self):
        # EIT reconstruction
        self.pB_set_reconstruction.clicked.connect(self._init_rec)
        self.pB_compute.clicked.connect(self.replay_agent.compute_actual_frame)

        # self.chB_eit_mdl_normalize.toggled.connect(self._get_solvers_params)
        # self.sBd_eit_model_fem_refinement.valueChanged.connect(self._get_solvers_params)
    
    def _init_rec(self) -> None:
        """Init the reconstruction solver"""
        rec_type = self.tabW_reconstruction.currentIndex()
        solver = self._rec_solver(rec_type)
        params = self._rec_params(rec_type)
        self.computing.init_solver(solver,self.eit_model, params)

    def _rec_solver(self, rec_type: int = 0) -> None:
        """Return the reconstruction solver"""
        rec = {0: eit_model.solver_pyeit.SolverPyEIT}
        return rec[rec_type]

    def _rec_params(self, rec_type: int = 0) -> None:
        """Return the reconstruction parameter"""
        params = {
            0: eit_model.solver_pyeit.PyEitRecParams(
                solver_type=self.cB_pyeit_solver.currentText(),
                p=self.sBd_pyeit_p.value(),
                lamb=self.sBd_pyeit_lamda.value(),
                n=self.sBd_pyeit_greit_n.value(),
                normalize=self.chB_eit_mdl_normalize.isChecked(),
                background= self.sBd_pyeit_bckgrnd.value()
            )
        }
        self.eit_model.set_refinement(self.sBd_eit_model_fem_refinement.value())
        return params[rec_type]
    
    ############################################################################
    #### Imaging,
    ############################################################################
    
    def _signals_to_imaging(self):
        self.cB_eit_imaging_type.activated.connect(self._imaging_changed)
        self.cB_eit_imaging_ref_frame.currentIndexChanged.connect(self._imaging_changed)
        self.cB_eit_imaging_ref_freq.activated.connect(self._imaging_changed)
        self.cB_eit_imaging_meas_freq.activated.connect(self._imaging_changed)
        self.cB_eit_imaging_trans.activated.connect(self._imaging_changed)
        self.chB_eit_imaging_trans_abs.toggled.connect(self._imaging_changed)

        # eit model catalog
        self.cB_eit_mdl_ctlg.currentTextChanged.connect(self._set_eit_mdl_ctlg)
        self.pB_eit_mdl_refresh_ctlg.clicked.connect(self._update_eit_mdl_ctlg)
        # chip design catalog
        self.cB_chip_ctlg.currentTextChanged.connect(self._set_chip_ctlg)
        self.pB_chip_refresh_ctlg.clicked.connect(self._update_chip_ctlg)

    def _imaging_changed(self) -> None:
        imaging_type = self.cB_eit_imaging_type.currentText()
        transform = self.cB_eit_imaging_trans.currentText()
        show_abs = self.chB_eit_imaging_trans_abs.isChecked()
        self.computing.set_imaging_mode(imaging_type, transform, show_abs)
        self.computing.set_eit_model(self.eit_model)
        self._set_actual_indexesforcomputation(imaging_type)

    def _set_actual_indexesforcomputation(self, imaging_type: str):
        index = ExtractIndexes(
            ref_idx=self.cB_eit_imaging_ref_frame.currentIndex(),
            meas_idx=self.cB_replay_frame_idx.currentIndex(),
            ref_freq=self.cB_eit_imaging_ref_freq.currentIndex(),
            meas_freq=self.cB_eit_imaging_meas_freq.currentIndex(),
            imaging=imaging_type,
        )
        self.dataset.set_index_of_data_for_computation(index)

    ############################################################################
    #### Monitoring
    ############################################################################

    def _signals_to_monitoring(self):
        self.chB_monitoring_trans_abs.toggled.connect(self._monitoring_params)
        self.cB_monitoring_trans.activated.connect(self._monitoring_params)

    def _monitoring_params(self) -> None:
        transform = self.cB_monitoring_trans.currentText()
        show_abs = self.chB_monitoring_trans_abs.isChecked()
        self.computing.set_monitoring(transform, show_abs)
    

    
    ############################################################################
    #### Eit model
    ############################################################################

    def _init_eit_model(self):
        # set pattern
        self.eit_model.load_defaultmatfile()
        self.update_setup_from_eit_mdl()
        
    def _update_eit_mdl_ctlg(self):
        """Update catalog and if changed"""
        files = search_for_file_with_ext(
            get_dir(AppStdDir.eit_model), FileExt.mat
        )
        set_comboBox_items(self.cB_eit_mdl_ctlg, files)

    def _set_eit_mdl_ctlg(self):
        """Update catalog and if changed"""
        path = os.path.join(
            get_dir(AppStdDir.eit_model), self.cB_eit_mdl_ctlg.currentText()
        )
        self.eit_model.load_matfile(path)
        self.update_setup_from_eit_mdl()

    def _update_chip_ctlg(self):
        """Update catalog and if changed"""
        files = search_for_file_with_ext(
            get_dir(AppStdDir.chips), FileExt.txt
        )
        set_comboBox_items(self.cB_chip_ctlg, files)

    def _set_chip_ctlg(self):
        """Update catalog and if changed"""
        path = os.path.join(
            get_dir(AppStdDir.chips), self.cB_chip_ctlg.currentText()
        )
        self.eit_model.load_chip_trans(path)
        self.update_setup_from_eit_mdl()
    
    def update_setup_from_eit_mdl(self):
        exc_mat = self.eit_model.excitation_mat().tolist()
        self.device.setup.set_exc_pattern_mdl(exc_mat)
        exc_mat = self.eit_model.excitation_mat_chip().tolist()
        self.device.setup.set_exc_pattern(exc_mat)
        self.update_gui(EvtDataSciospecDevSetup(self.device.setup))
    



        

    # def kill_workers(self) -> None:
    #     """Kill alls the running threads workers"""
    #     [item.quit() for _, item in self.workers.items()]


if __name__ == "__main__":
    """"""
