from __future__ import absolute_import, division, print_function

import logging
import os

import eit_model.imaging
import eit_model.model
import eit_model.solver_ai
import eit_model.solver_pyeit
import eit_model.reconstruction
import glob_utils.dialog.Qt_dialogs
import glob_utils.directory.utils
import glob_utils.file.csv_utils
import glob_utils.file.mat_utils
import glob_utils.file.txt_utils
import glob_utils.log.log
import glob_utils.log.msg_trans
import matplotlib
import matplotlib.backends.backend_qt5agg
import matplotlib.pyplot
import numpy as np
from glob_utils.file.utils import (FileExt, OpenDialogFileCancelledException,
                                   dialog_get_file_with_ext,
                                   search_for_file_with_ext)
from PyQt5 import QtCore, QtWidgets

import eit_app.com_channels
import eit_app.default.set_default_dir
import eit_app.computation
import eit_app.plots
import eit_app.gui
import eit_app.sciospec.constants
import eit_app.sciospec.device
import eit_app.sciospec.measurement
import eit_app.sciospec.replay
import eit_app.video.capture
import eit_app.video.microcam
from eit_app.default.set_default_dir import AppStdDir, get_dir
from eit_app.export import ExportAgent, ExportFunc, ParamsToLoopOn
from eit_app.gui_utils import set_comboBox_items
from eit_app.update_gui import (EvtDataEITDataPlotOptionsChanged, EvtDataImagingInputsChanged,
                                EvtDataSciospecDevSetup, EvtEitModelLoaded,
                                EvtGlobalDirectoriesSet, EvtInitFormatUI,
                                EvtRecSolverChanged)
from eit_app.widget_3d import Window3DAgent
from eit_app.experimental.fit_circles import show_threshold_overview, evaluate_multi_image, evaluate_single_image

# Ensure using PyQt5 backend
matplotlib.use("QT5Agg")

__author__ = "David Metz"
__copyright__ = "Copyright 2021, David Metz"
__credits__ = ["David Metz"]
__license__ = "GPL"
__version__ = "2.0.0"
__maintainer__ = "David Metz"
__email__ = "d.metz@tu-bs.de"
__status__ = "Production"

logger = logging.getLogger(__name__)

# class UiBackEnd(Ui_MainWindow, QtWidgets.QMainWindow, AddUpdateAgent):
class UiBackEnd(QtWidgets.QMainWindow, eit_app.com_channels.AddUpdateUiAgent):
    def __init__(self) -> None:
        super().__init__()
        self.init_logging()

        self.ui = eit_app.gui.Ui_MainWindow()
        self.ui.setupUi(self)

        self.init_update_ui_agent(self.ui)
        self.set_title()
        eit_app.default.set_default_dir.set_ai_default_dir()
        self.update_gui(EvtGlobalDirectoriesSet())
        self._create_main_objects()
        self._connect_main_objects()
        self._connect_menu()
        self._init_values()

        self.update_gui(EvtInitFormatUI())
        # self._debug_load()

    def _debug_load(self):
        try:
            self.dataset.load(dir_path="E:\\Software_dev\\Python\\eit_app\\measurements\\fish_good_13.05\\dan_fish_1k50k_0.001mA_2_20220513_160256")
            # self._init_rec()
        except BaseException as e:
            logger.error(f"{e}")


    def init_logging(self):
        glob_utils.log.log.change_level_logging(logging.DEBUG)
        start_msg = f"                          Start of EIT app : v{__version__}\n\
                          {__copyright__}"
        logger.info(glob_utils.log.msg_trans.highlight_msg(start_msg))
    
    def eventFilter(self, source: QtCore.QObject, event: QtCore.QEvent) -> bool:

        # disable MouseWheel event on slider_replay
        if source == self.ui.slider_replay and event.type() == QtCore.QEvent.Wheel:
            return True

        return super().eventFilter(source, event)

    def set_title(self) -> None:
        t = f"EIT aquisition for Sciospec device {__version__}"
        self.setWindowTitle(QtCore.QCoreApplication.translate("MainWindow", t))

    def _create_main_objects(self) -> None:

        # set canvas
        self.plot_agent = eit_app.plots.PlottingAgent()

        self.canvas_eit_image = eit_app.plots.CanvasLayout(
            self, self.ui.layout_rec, eit_app.plots.PlotterEITImage2D
        )
        self.plot_agent.add_canvas(self.canvas_eit_image)

        self.canvas_eit_elem_data = eit_app.plots.CanvasLayout(
            self, self.ui.layout_elem_data, eit_app.plots.PlotterEITImageElemData
        )
        self.plot_agent.add_canvas(self.canvas_eit_elem_data)

        self.canvas_greit = eit_app.plots.CanvasLayout(
            self, self.ui.layout_greit, eit_app.plots.PlotterEITImage2Greit
        )
        self.plot_agent.add_canvas(self.canvas_greit)

        self.canvas_eit_data = eit_app.plots.CanvasLayout(
            self, self.ui.layout_Uplot, eit_app.plots.PlotterEITData
        )
        self.plot_agent.add_canvas(self.canvas_eit_data)

        self.canvas_Uch = eit_app.plots.CanvasLayout(
            self, self.ui.layout_Uch, eit_app.plots.PlotterEITChannelVoltage
        )
        self.plot_agent.add_canvas(self.canvas_Uch)

        self.canvas_error = eit_app.plots.CanvasLayout(
            self,
            self.ui.layout_error,
            eit_app.plots.PlotterChannelVoltageMonitoring,
        )
        self.plot_agent.add_canvas(self.canvas_error)

        self.eit_mdl = eit_model.model.EITModel()
        self.reconstruction = eit_model.reconstruction.EITReconstruction()

        self.computing = eit_app.computation.ComputingAgent(self.reconstruction)

        self.dataset = eit_app.sciospec.measurement.MeasurementDataset()
        self.device = eit_app.sciospec.device.SciospecEITDevice(32)
        self.replay_agent = eit_app.sciospec.replay.ReplayMeasurementsAgent()
        self.capture_agent = eit_app.video.capture.VideoCaptureAgent(
            capture_dev=eit_app.video.microcam.MicroUSBCamera(),
            snapshot_dir=get_dir(AppStdDir.snapshot),
        )
        self.export_agent = ExportAgent(self.replay_agent, self.dataset,self.computing, self.ui)
        self.window_3d_agent = Window3DAgent()

    def _connect_menu(self):
        self.ui.action_exit.triggered.connect(self.close)

    def _connect_main_objects(self) -> None:

        self.computing.to_gui.connect(self.to_reciever)
        self.computing.to_plot.connect(self.plot_agent.to_reciever)
        self.computing.to_plot.connect(self.window_3d_agent.to_reciever)

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

        self._signals_to_log()
        self._signals_to_device()
        self._signals_to_dev_setup()
        self._signals_to_dataset()
        self._signals_to_replay()
        self._signals_to_export_import()
        self._signals_to_capture()
        self._signals_to_plot()
        self._signals_to_rec()
        self._signals_to_imaging()
        self._signals_to_monitoring()

        self.comboBox_init()
        self._get_dev_setup()
        self._set_plots_options()
        self._imaging_changed()
        self._monitoring_params()
        self.capture_agent.get_devices()
        self.capture_agent.emit_status_changed()
        self.device.get_devices()
        self.device.to_gui_emit_connect_status()
        self.device.emit_status_changed()
        self._init_eit_mdl()
        self._set_exports()
        self._set_last_fitting_dirpath()

    def comboBox_init(self) -> None:
        """ """
        set_comboBox_items(self.ui.cB_log_level, glob_utils.log.log.list_levels())
        set_comboBox_items(
            self.ui.cB_scale, eit_app.sciospec.constants.frequency_scales()
        )
        set_comboBox_items(
            self.ui.cB_pyeit_solver, eit_model.solver_pyeit.used_solver()
        )
        self._update_rec_params(solver=self.ui.cB_pyeit_solver.currentText())
        set_comboBox_items(
            self.ui.cB_eit_imaging_type, eit_model.imaging.eit_imaging_types()
        )
        set_comboBox_items(
            self.ui.cB_eit_imaging_trans, eit_model.imaging.eit_data_transformations()
        )
        set_comboBox_items(self.ui.cB_eit_imaging_ref_frame, [0])
        set_comboBox_items(
            self.ui.cB_monitoring_trans, eit_model.imaging.eit_data_transformations()
        )

        set_comboBox_items(
            self.ui.cB_capture_img_size, self.capture_agent.used_img_sizes()
        )
        set_comboBox_items(
            self.ui.cB_capture_img_file_ext, self.capture_agent.used_img_exts()
        )
        # init catalogs which neeeds some loading
        self._update_eit_mdl_ctlg()
        self._update_chip_ctlg()

    ############################################################################
    #### Logging
    ############################################################################

    def _signals_to_log(self):
        self.ui.cB_log_level.activated[str].connect(
            glob_utils.log.log.change_level_logging
        )

    ############################################################################
    #### Device, Setup
    ############################################################################

    def _signals_to_device(self):

        self.ui.pB_refresh.clicked.connect(self.device.get_devices)
        self.ui.pB_connect.clicked.connect(self.device.connect_device)
        self.ui.pB_disconnect.clicked.connect(self.device.disconnect_device)
        self.ui.pB_get_setup.clicked.connect(self.device.get_setup)
        self.ui.pB_set_setup.clicked.connect(self.device.set_setup)
        self.ui.pB_reset.clicked.connect(self.device.software_reset)
        self.ui.pB_save_setup.clicked.connect(self.device.save_setup)
        self.ui.pB_load_setup.clicked.connect(self.device.load_setup)
        self.ui.pB_start_meas.clicked.connect(self.device.start_paused_resume_meas)
        self.ui.pB_stop_meas.clicked.connect(self.device.stop_meas)
        self.ui.cB_ports.activated[str].connect(self.device.set_device_name)

    def _signals_to_dev_setup(self):

        self.ui.sBd_exc_amp.valueChanged.connect(self._get_dev_setup)
        self.ui.sB_burst.valueChanged.connect(self._get_dev_setup)
        self.ui.sBd_freq_min.valueChanged.connect(self._get_dev_setup)
        self.ui.sBd_freq_max.valueChanged.connect(self._get_dev_setup)
        self.ui.sB_freq_steps.valueChanged.connect(self._get_dev_setup)
        self.ui.cB_scale.activated.connect(self._get_dev_setup)
        self.ui.sBd_frame_rate.valueChanged.connect(self._get_dev_setup)

    def _get_dev_setup(self) -> None:
        """Save user entry from Gui in setup of device"""
        self.device.setup.set_frame_rate(self.ui.sBd_frame_rate.value())
        self.device.setup.set_burst(self.ui.sB_burst.value())
        self.device.setup.set_exc_amp(self.ui.sBd_exc_amp.value() / 1000)  # mA -> A
        freq_max_enable, error = self.device.setup.set_freq_config(
            freq_min=self.ui.sBd_freq_min.value(),
            freq_max=self.ui.sBd_freq_max.value(),
            freq_steps=self.ui.sB_freq_steps.value(),
            freq_scale=self.ui.cB_scale.currentText(),
        )
        self.update_gui(
            EvtDataSciospecDevSetup(self.device.setup, freq_max_enable, error)
        )

    ############################################################################
    #### Dataset, replay
    ############################################################################

    def _signals_to_dataset(self):
        self.ui.lE_meas_dataset_dir.textChanged[str].connect(self.dataset.set_name)
        self.ui.chB_dataset_autosave.toggled[bool].connect(self.dataset.set_autosave)
        self.ui.chB_dataset_save_img.toggled[bool].connect(self.dataset.set_save_img)
        self.ui.chB_load_after_meas.toggled[bool].connect(
            self.dataset.set_load_after_meas
        )
        self.ui.pB_meas_dataset_load.clicked.connect(self.dataset.load)
        self.ui.pB_load_ref_dataset.clicked.connect(self._loadRef4TD)

    def _signals_to_replay(self):
        self.ui.pB_replay_begin.clicked.connect(self.replay_agent.begin)
        self.ui.pB_replay_end.clicked.connect(self.replay_agent.end)
        self.ui.pB_replay_play.clicked.connect(self.replay_agent.play_pause)
        self.ui.pB_replay_next.clicked.connect(self.replay_agent.next)
        self.ui.pB_replay_back.clicked.connect(self.replay_agent.back)
        self.ui.pB_replay_stop.clicked.connect(self.replay_agent.stop)
        self.ui.sB_replay_time.valueChanged[float].connect(
            self.replay_agent.set_timeout
        )
        self.ui.cB_replay_frame_idx.activated[int].connect(
            self.replay_agent.set_actual_frame
        )
        self.ui.slider_replay.valueChanged[int].connect(
            self.replay_agent.set_actual_frame
        )
        self.ui.slider_replay.installEventFilter(self)

    def _set_actual_frame(self):
        self.replay_agent.set_actual_frame(self.ui.cB_replay_frame_idx.currentIndex())

    def _loadRef4TD(self) -> None:

        try:
            file_path = dialog_get_file_with_ext(
                ext=FileExt.json, title="", initialdir=get_dir(AppStdDir.meas_set)
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
                self.ui.cB_replay_frame_idx.currentIndex(), path=path
            )

    ############################################################################
    #### Export, import
    ############################################################################

    def _signals_to_export_import(self):
        self.ui.pB_export_meas_csv.clicked.connect(self._export_meas_csv)
        self.ui.pB_export_frame_plots.clicked.connect(self._export_frame)
        self.ui.pB_fit_circle_single_image.clicked.connect(self._fit_circle)
        self.ui.pB_fit_circle_multi_image.clicked.connect(self._fit_multi_circle)
        self.ui.pB_fit_circle_overview.clicked.connect(self._show_fit_circle_threshold_overview)


    def _set_last_fitting_dirpath(self, path= None):
        
        self._last_fitting_dirpath= os.path.split(path)[0] if path is not None else None
 
    def _fit_circle(self):
        """"""
        path, _= evaluate_single_image(
            initialdir=self._last_fitting_dirpath,
            threshold_cell=self.ui.sP_fit_circle_threshold_cell.value(),
            threshold_chamber=self.ui.sP_fit_circle_threshold_chamber.value(),
            scale=self.eit_mdl.bbox[1,1]
        )
        self._set_last_fitting_dirpath(path)

    def _fit_multi_circle(self):
        """"""
        path= evaluate_multi_image(
            initialdir=self._last_fitting_dirpath,
            threshold_cell=self.ui.sP_fit_circle_threshold_cell.value(),
            threshold_chamber=self.ui.sP_fit_circle_threshold_chamber.value(),
            scale=self.eit_mdl.bbox[1,1]
        )
        self._set_last_fitting_dirpath(path)

    def _show_fit_circle_threshold_overview(self):
        """"""
        path= show_threshold_overview(initialdir=self._last_fitting_dirpath)
        self._set_last_fitting_dirpath(path)

    def _export_analysis_protocol(self, path:str) -> None:
        """export the measurement protocol"""
        self._export_analysis_protocol_done = False
        rec_type = self.ui.tabW_reconstruction.currentIndex()
        params = self._rec_params(rec_type)
        meas_idx = self.ui.cB_replay_frame_idx.currentIndex()

        def sub(s:str, order:int=1)->str:
            tab=['\t']*order
            return f"{''.join(tab)}{s}"

        logger.debug(f'{self.reconstruction.imaging=}')
        lines= []
        lines.append('Dataset:')
        [lines.append(sub(f'{l}')) for l in self.dataset.get_protocol_info()]
        lines.append('EIT model:')
        [lines.append(sub(f'{l}')) for l in self.eit_mdl.get_protocol_info()]
        lines.append('Imaging:')
        [lines.append(sub(f'{l}')) for l in self.reconstruction.imaging.get_protocol_info()]
        lines.append('Solver:')
        [lines.append(sub(f'{k}: {v}'))for k,v in params.__dict__.items()]
        
        path= f"{path}_protocol"
        glob_utils.file.txt_utils.save_as_txt(path, lines)
        self._export_analysis_protocol_done = True
    
    def _analysis_protocol_exported(self):
        return self._export_analysis_protocol_done


    def _export_meas_csv(self) -> None:
        """Export the actual measurments frames in csv"""
        idx_freq = self.ui.cB_eit_imaging_meas_freq.currentIndex()
        n = self.dataset.get_frame_cnt()
        data = {
            f"frame{i}": np.real(
                self.eit_mdl.get_meas_voltages(
                    self.dataset.get_meas_voltage(i, idx_freq)
                )[0]
            )
            for i in range(n)
        }
        freq = self.dataset.meas_frame[0].freq_label(idx_freq)

        file_path = os.path.join(self.dataset.output_dir, f"Meas#1-{n}_freq{freq}")
        glob_utils.file.csv_utils.save_as_csv(file_path, data)
        logger.debug(f"Measurements exported as CSV in : {file_path}")

    def _set_exports(self):

        self.export_agent.add_export(
            ExportFunc(
                enable_func=self.ui.chB_export_eit_image.isChecked,
                func=self.canvas_eit_image.add_export_path,
                is_exported=self.canvas_eit_image.all_exported,
                before_compute=True,
            )
        )

        self.export_agent.add_export(
            ExportFunc(
                enable_func=self.ui.chB_export_eit_data.isChecked,
                func=self.canvas_eit_data.add_export_path,
                is_exported=self.canvas_eit_data.all_exported,
                before_compute=True,
            )
        )

        self.export_agent.add_export(
            ExportFunc(
                enable_func=self.ui.chB_export_ch_voltages.isChecked,
                func=self.canvas_Uch.add_export_path,
                is_exported=self.canvas_Uch.all_exported,
                before_compute=True,
            )
        )

        self.export_agent.add_export(
            ExportFunc(
                enable_func=self.ui.chB_export_eit_data_mat.isChecked,
                func=self.computing.export_eit_data,
                is_exported=self.computing.exported,
                before_compute=True,
            )
        )

        self.export_agent.add_export(
            ExportFunc(
                enable_func=self.ui.chB_export_analysis_protocol.isChecked,
                func=self._export_analysis_protocol,
                is_exported=self._analysis_protocol_exported,
                before_compute=False,
            )
        )

        self.export_agent.add_params(
            ParamsToLoopOn(
                enable_func=self.ui.chB_export_loop_on_frame.isChecked,
                export_val_in_filename=True,
                combobox=self.ui.cB_replay_frame_idx,
                func_set=self._set_actual_frame,
                tag="frm",
                block=True,
            )
        )

        self.export_agent.add_params(
            ParamsToLoopOn(
                enable_func=self.ui.chB_export_loop_on_meas_frequency.isChecked,
                export_val_in_filename=True,
                combobox=self.ui.cB_eit_imaging_meas_freq,
                func_set=self._imaging_changed,
                tag="",
            )
        )

        self.export_agent.add_params(
            ParamsToLoopOn(
                enable_func=self.ui.chB_export_loop_on_imaging_trans.isChecked,
                export_val_in_filename=True,
                combobox=self.ui.cB_eit_imaging_trans,
                func_set=self._imaging_changed,
                tag="",
            )
        )

    def _export_frame(self):
        """"""
        # activate the plots
        self.ui.chB_eit_image_plot.setChecked(True)
        self.ui.chB_eit_data_monitoring.setChecked(True)
        self.export_agent.run_export()

    ############################################################################
    #### Capture
    ############################################################################

    def _signals_to_capture(self):
        self.ui.pB_capture_refresh.clicked.connect(self.capture_agent.get_devices)
        self.ui.pB_capture_start_stop.clicked.connect(self.capture_agent.start_stop)
        self.ui.pB_capture_snapshot.clicked.connect(self.capture_agent.take_snapshot)
        self.ui.cB_capture_devices.activated[str].connect(
            self.capture_agent.set_device_name
        )
        self.ui.pB_capture_connect.clicked.connect(self.capture_agent.connect_device)
        self.ui.cB_capture_img_size.activated[str].connect(
            self.capture_agent.set_image_size
        )
        self.ui.cB_capture_img_file_ext.activated[str].connect(
            self.capture_agent.set_image_file_format
        )
        self.ui.chB_capture_img_mirror_h.toggled[bool].connect(
            lambda val: self.capture_agent.set_mirror(val, "horizontal")
        )
        self.ui.chB_capture_img_mirror_v.toggled[bool].connect(
            lambda val: self.capture_agent.set_mirror(val, "vertical")
        )

    # def _set_capture_device(self, *args, **kwargs) -> None:
    #     self.capture_agent.set_image_size(self.ui.cB_capture_img_size.currentText())
    #     self.capture_agent.set_image_file_format(file_ext=self.ui.cB_capture_img_file_ext.currentText())

    ############################################################################
    #### Plotting
    ############################################################################

    def _signals_to_plot(self):

        self.ui.chB_eit_image_plot.toggled.connect(self._set_plots_options)
        self.ui.chB_eit_data_monitoring.toggled.connect(self._set_plots_options)
        self.ui.pB_pyvista.clicked.connect(self.open_pyvista)
        self.ui.pB_set_dpi.clicked.connect(self._set_dpi)
        self.ui.scalePlot_vmin.valueChanged.connect(self._set_plots_options)
        self.ui.scalePlot_vmax.valueChanged.connect(self._set_plots_options)
        self.ui.chB_show_electrode.toggled.connect(self._set_plots_options)
        self.ui.chB_show_colorbar.toggled.connect(self._set_plots_options)
        self.ui.chB_show_axis.toggled.connect(self._set_plots_options)
        self.ui.chB_show_title.toggled.connect(self._set_plots_options)


    def _set_plots_options(self) -> None:

        self.ui.tabW_rec.setVisible(self.ui.chB_eit_image_plot.isChecked())
        self.reconstruction.enable_rec(self.ui.chB_eit_image_plot.isChecked())
        self.ui.tabW_monitoring.setVisible(self.ui.chB_eit_data_monitoring.isChecked())
        self.update_gui(EvtDataEITDataPlotOptionsChanged())

        self.canvas_eit_image.set_options(
            show_electrode= self.ui.chB_show_electrode.isChecked(), 
            show_colorbar=self.ui.chB_show_colorbar.isChecked(),
            show_axis=self.ui.chB_show_axis.isChecked(),
            show_title=self.ui.chB_show_title.isChecked(),
        )




    def _set_dpi(self) -> None:

        dpi = self.ui.dsB_dpi_rec.value()
        self.canvas_eit_image.set_options(dpi=dpi)
        self.canvas_eit_data.set_options(dpi=dpi)
        self.canvas_Uch.set_options(dpi=dpi)
        self.canvas_error.set_options(dpi=dpi)

    def open_pyvista(self, checked) -> None:
        self.window_3d_agent.init_window_3d(self.eit_mdl)

    ############################################################################
    #### Reconstruction, computation
    ############################################################################
    def _signals_to_rec(self):
        # EIT reconstruction
        self.ui.pB_set_reconstruction.clicked.connect(self._init_rec)
        self.ui.pB_compute.clicked.connect(self.replay_agent.compute_actual_frame)
        self.ui.cB_pyeit_solver.activated[str].connect(self._update_rec_params)
        self.ui.pB_activate_calibration.clicked[bool].connect(self.reconstruction.enable_calibration)

        # self.ui.chB_eit_mdl_normalize.toggled.connect(self._get_solvers_params)
        # self.ui.sBd_eit_model_fem_refinement.valueChanged.connect(self._get_solvers_params)

    def _init_rec(self) -> None:
        """Init the reconstruction solver"""
        rec_type = self.ui.tabW_reconstruction.currentIndex()
        solver = self._rec_solver(rec_type)
        params = self._rec_params(rec_type)
        self.computing.init_solver(solver, params)

    def _rec_solver(self, rec_type: int = 0) -> None:
        """Return the reconstruction solver"""
        rec = {
            0: eit_model.solver_pyeit.SolverPyEIT,
            1: eit_model.solver_ai.SolverAi,
        }
        return rec[rec_type]

    def _rec_params(self, rec_type: int = 0) -> None:
        """Return the reconstruction parameter"""
        params = {
            0: eit_model.solver_pyeit.PyEitRecParams(
                solver_type=self.ui.cB_pyeit_solver.currentText(),
                p=self.ui.sBd_pyeit_p.value(),
                lamb=self.ui.sBd_pyeit_lamda.value(),
                n=int(self.ui.sBd_pyeit_greit_n.value()),
                normalize=self.ui.chB_eit_mdl_normalize.isChecked(),
                background=self.ui.sBd_pyeit_bckgrnd.value(),
                method=self.ui.cB_pyeit_reg_method.currentText(),
                weight=self.ui.cB_pyeit_bp_weight_method.currentText(),
                mesh_generation_mode_2D=self.ui.chB_eit_mdl_2D_generation.isChecked(),
            ),
            1: eit_model.solver_ai.AiRecParams(
                model_dirpath="",
                normalize=self.ui.chB_eit_mdl_normalize.isChecked(),
            ),
        }
        self.eit_mdl.set_refinement(self.ui.sBd_eit_model_fem_refinement.value())
        return params[rec_type]

    def _update_rec_params(self, solver: str):
        self.update_gui(
            EvtRecSolverChanged(
                preset=eit_model.solver_pyeit.get_rec_params_preset(solver)
            )
        )

    ############################################################################
    #### Imaging,
    ############################################################################

    def _signals_to_imaging(self):
        self.ui.cB_eit_imaging_type.activated.connect(self._imaging_changed)
        self.ui.cB_eit_imaging_ref_frame.currentIndexChanged.connect(
            self._imaging_changed
        )
        self.ui.cB_eit_imaging_ref_freq.activated.connect(self._imaging_changed)
        self.ui.cB_eit_imaging_meas_freq.activated.connect(self._imaging_changed)
        self.ui.cB_eit_imaging_trans.activated.connect(self._imaging_changed)

        self.ui.chB_eit_imaging_trans_abs.toggled.connect(self._imaging_changed)

        # eit model catalog
        self.ui.cB_eit_mdl_ctlg.activated.connect(self._load_eit_mdl)
        self.ui.pB_eit_mdl_refresh_ctlg.clicked.connect(self._update_eit_mdl_ctlg)
        # chip design catalog
        self.ui.cB_chip_ctlg.currentTextChanged.connect(self._load_chip)
        self.ui.pB_chip_refresh_ctlg.clicked.connect(self._update_chip_ctlg)

    def _imaging_changed(self) -> None:
        logger.debug("_imaging_changed")
        imaging_type = self.ui.cB_eit_imaging_type.currentText()
        transform = self.ui.cB_eit_imaging_trans.currentText()
        show_abs = self.ui.chB_eit_imaging_trans_abs.isChecked()

        imaging=eit_model.imaging.build_EITImaging(imaging_type, transform, show_abs)
        self.update_gui(EvtDataImagingInputsChanged(imaging))

        self.reconstruction.imaging= imaging
        # self.reconstruction.set_eit_model(self.eit_mdl)
        self._set_actual_indexesforcomputation(imaging_type)

    def _set_actual_indexesforcomputation(self, imaging_type: str):
        index = eit_app.sciospec.measurement.ExtractIndexes(
            ref_idx=self.ui.cB_eit_imaging_ref_frame.currentIndex(),
            meas_idx=self.ui.cB_replay_frame_idx.currentIndex(),
            ref_freq=self.ui.cB_eit_imaging_ref_freq.currentIndex(),
            meas_freq=self.ui.cB_eit_imaging_meas_freq.currentIndex(),
            imaging=imaging_type,
        )
        self.dataset.set_index_of_data_for_computation(index)

    ############################################################################
    #### Monitoring
    ############################################################################

    def _signals_to_monitoring(self):
        self.ui.chB_monitoring_trans_abs.toggled.connect(self._monitoring_params)
        self.ui.cB_monitoring_trans.activated.connect(self._monitoring_params)

    def _monitoring_params(self) -> None:
        transform = self.ui.cB_monitoring_trans.currentText()
        show_abs = self.ui.chB_monitoring_trans_abs.isChecked()
        self.reconstruction.set_monitoring(transform, show_abs)

    ############################################################################
    #### Eit model
    ############################################################################

    def _init_eit_mdl(self):
        """Load the default eit_mdl define in the `eit_model`-package"""
        # set pattern
        self.eit_mdl.load_defaultmatfile()
        self.update_setup_from_eit_mdl()

    def _update_eit_mdl_ctlg(self):
        """Update catalog of eit_mdl"""
        files = search_for_file_with_ext(get_dir(AppStdDir.eit_model), FileExt.mat)
        set_comboBox_items(self.ui.cB_eit_mdl_ctlg, files)

    def _load_eit_mdl(self):
        """Load eit_mdl"""
        path = os.path.join(
            get_dir(AppStdDir.eit_model), self.ui.cB_eit_mdl_ctlg.currentText()
        )
        self.eit_mdl.load_matfile(path)
        self.update_setup_from_eit_mdl()

    def _update_chip_ctlg(self):
        """Update catalog"""
        files = search_for_file_with_ext(get_dir(AppStdDir.chips), FileExt.txt)
        set_comboBox_items(self.ui.cB_chip_ctlg, files)

    def _load_chip(self):
        """Update catalog"""
        path = os.path.join(
            get_dir(AppStdDir.chips), self.ui.cB_chip_ctlg.currentText()
        )
        self.eit_mdl.load_chip_trans(path)
        self.update_setup_from_eit_mdl()

    def update_setup_from_eit_mdl(self):
        exc_mat = self.eit_mdl.excitation_mat().tolist()
        self.device.setup.set_exc_pattern_mdl(exc_mat)
        exc_mat = self.eit_mdl.excitation_mat_chip().tolist()
        self.device.setup.set_exc_pattern(exc_mat)
        self.update_gui(EvtDataSciospecDevSetup(self.device.setup))
        self.update_gui(EvtEitModelLoaded(self.eit_mdl.name))
        self.reconstruction.eit_model=self.eit_mdl
        self.window_3d_agent.set_eit_model(self.eit_mdl)

    # def kill_workers(self) -> None:
    #     """Kill alls the running threads workers"""
    #     [item.quit() for _, item in self.workers.items()]


if __name__ == "__main__":
    """"""
 
