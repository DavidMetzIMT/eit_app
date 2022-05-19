import logging
from queue import Queue
from typing import Any, Tuple, Union

import numpy as np
from eit_app.com_channels import (AddToGuiSignal, AddToPlotSignal,
                                  Data2Compute, Data2Plot, SignalReciever)
from eit_app.eit.plots import (PlotterChannelVoltageMonitoring,
                               PlotterEITChannelVoltage, PlotterEITData,
                               PlotterEITImage2D, PlotterEITImage2Greit,
                               PlotterEITImageElemData)
from eit_app.update_gui import EvtDataImagingInputsChanged, EvtPopMsgBox
from eit_model.data import EITData, EITMeasMonitoring
from eit_model.greit import greit_filter
from eit_model.imaging import IMAGING_TYPE, ChannelVoltageImaging, Imaging
from eit_model.model import EITModel
from eit_model.plot import CustomLabels, EITPlotsType
from eit_model.solver_abc import RecParams, Solver
from glob_utils.decorator.decorator import catch_error
from glob_utils.thread_process.threads_worker import Poller
import glob_utils.file.mat_utils

logger = logging.getLogger(__name__)


class ComputingAgent(SignalReciever, AddToPlotSignal, AddToGuiSignal):
    def __init__(self):
        """The Computing agent is responsible to compute EIT image in a
        separate Thread compute.

        for that data of type Data2Compute should be added its input buffer
        directly by calling the "add_data2compute"-method or using it
        SignalReciever functionality by passing the data though a signal

        The images ar then directly send to the plottingagent responsible of
        plotting the image , voltages graphs, ...

        """
        super().__init__()

        self.init_reciever(data_callbacks={Data2Compute: self.add_data2compute})

        self.input_buf = Queue()
        self.compute_worker = Poller(
            name="compute", pollfunc=self._poll_input_buf, sleeptime=0.01
        )
        self.compute_worker.start()
        self.compute_worker.start_polling()

        self.eit_imaging: Imaging = None
        self.monitoring = None
        self.eit_model: EITModel = None
        self.U, self.labels = None, None
        self.extract_voltages = False
        self.solver: Solver = None
        self.rec_enable = False
        self.params = None
        self.last_eit_data: EITData= None
        self._data_exported=False
        self.reset_monitoring_data()
        self.calibration:np.ndarray= None # diag matrix shape (n_exc,n_exc) with calibration coef
        self._enable_calibration= False

    def add_data2compute(self, data: Data2Compute = None, **kwargs):
        """Put the data in the input buffer

        Args:
            data (Data2Compute, optional): data for computation. Defaults to None.
        """
        if not isinstance(data, Data2Compute):
            logger.error(f"wrong type of data, type Data2Compute expected: {data=}")
            return
        self.input_buf.put(data)

    def _poll_input_buf(self):
        """Retrieve the last data to compute out of input_buffer

        here data 2 compute can be ignorde if betwet two threads polling
        multiple data has been added. it doesn't make sense to compute all of
        then if computation take so much time
        """
        if self.input_buf.empty():
            return
        # process only the last data added, ignore the rest
        while not self.input_buf.empty():
            data = self.input_buf.get()
        self.process(data)

    def enable_calibration(self, val:bool=True):
        self._enable_calibration= val
        self.calibration= None

    def compute_calibration(self, data: Data2Compute):
        if not self._enable_calibration: 
            return


        v=self.eit_imaging.transformer.run(data.v_ref.volt, False)
        v_exc_max= np.max(v, axis=1)
        v_max= max(v_exc_max)
        coef=np.reciprocal(v_exc_max.astype(float))*v_max
        self.calibration=np.diag(coef)

        title= 'Calibration result'
        msg=f'\
Calibration done\n\
method : coef(exc)= max(v)/max(v(exc,:))\n\r\
v from {data.v_ref.labels.lab_frame_idx},{data.v_ref.labels.lab_frame_freq}\n\
and transformed {self.eit_imaging.transformer.transform}, {self.eit_imaging.transformer.show_abs}\n\r\
Corrections coeffs: {coef}'
        logger.debug(msg)
        self.to_gui.emit(EvtPopMsgBox(title, msg, 'info'))


        self._enable_calibration= False

    @catch_error
    def process(self, data: Data2Compute) -> None:
        """Compute the eit image
        - get eit_data for reconstruction
        - reconstruct eit image

        Args:
            data (Data2Compute): data for reconstruction
        """
        self._is_processing= True
        self._actual_frame_name = data.v_meas.get_frame_name()
        data= self._preprocess_calibration(data)
        self._preprocess_monitoring(data)
        eit_data, plot_labels = self._prepocess_eitdata(data)
        self._rec_image(eit_data, plot_labels)
        self._is_processing= False

    def _preprocess_calibration(self, data: Data2Compute) -> Data2Compute:
        """"""
        self.compute_calibration(data)

        if self.calibration is None:
            return data

        data.v_ref.volt= np.matmul(self.calibration, data.v_ref.volt)
        data.v_meas.volt= np.matmul(self.calibration, data.v_meas.volt)

        return data

    def _prepocess_eitdata(
        self, data: Data2Compute
    ) -> Tuple[EITData, dict[EITPlotsType, CustomLabels], str]:
        """Returns the eit_data for reconstruction. During this method
        the eit data are send for plotting

        Args:
            data (Data2Compute): data for reconstruction

        Returns:
            Tuple[EITData, dict[EITPlotsType, CustomLabels], str]: eit_data for rec,
            labels for plots , and actual frame name
        """

        # prepocess eitdata for eit_imaging
        logger.debug(f'{self.eit_imaging=}')
        eit_data, eit_volt, plot_labels = self.eit_imaging.process_data(
            v_ref=data.v_ref, v_meas=data.v_meas, eit_model=self.eit_model
        )
        self.to_plot.emit(Data2Plot(eit_data, plot_labels, PlotterEITData))
        self.last_eit_data= eit_data
        logger.info(f"{self._actual_frame_name} - Voltages preproccessed")
        return eit_data, plot_labels

    def _preprocess_monitoring(self, data: Data2Compute) -> None:
        """Prepocee the data for the monitoring of the voltages. During
        this method the voltages values are send for ploting
        """
        # prepocess channel voltages for visualisation
        ch_data, ch_volt, ch_labels = self.monitoring.process_data(
            v_ref=data.v_ref, v_meas=data.v_meas, eit_model=self.eit_model
        )
        self.to_plot.emit(Data2Plot(ch_data, ch_labels, PlotterEITChannelVoltage))

        self.monitoring_data.add(ch_volt.volt_frame, data.v_meas.get_frame_name())
        self.to_plot.emit(
            Data2Plot(self.monitoring_data, ch_labels, PlotterChannelVoltageMonitoring)
        )
        logger.info(f"{self._actual_frame_name} - Voltages Monitoring preproccessed")

    def _rec_image(self, eit_data: EITData, labels: dict[EITPlotsType, CustomLabels]):
        """Reconstruct EIT image

        Args:
            eit_data (EITData): _description_
            labels (dict[EITPlotsType, CustomLabels]): _description_
            frame_name (str): for logging
        """
        if not self.rec_enable:
            return
        if not self.solver or not self.solver.ready.is_set():  #
            logger.warning("Solver not set")
            return
        img_rec = self.solver.rec(eit_data)
        self.to_plot.emit(Data2Plot(img_rec, labels, PlotterEITImage2D))
        self.to_plot.emit(Data2Plot(img_rec, labels, PlotterEITImageElemData))
        
        self.to_plot.emit(Data2Plot(greit_filter(img_rec), labels, PlotterEITImage2Greit))
        logger.info(f"{self._actual_frame_name} - Image rec")

    def enable_rec(self, enable: bool = True):
        """Enable the EIT image reconstruction. if set to `False` only
        preprocessing of data to compute is done. (voltage meas. will be plot)
        """
        self.rec_enable = enable

    @catch_error
    def init_solver(self, solver: Solver, eit_model: EITModel, params: Any) -> None:
        """Initialize internal solver, optionaly new solver or reconstruction
        parameters can be set before
        """
        self.set_solver(solver, eit_model)
        self.set_rec_params(params)

        img_rec, data_sim = self.solver.prepare_rec(self.params)
        self.to_plot.emit(Data2Plot(img_rec, {}, PlotterEITImage2D))
        self.to_plot.emit(Data2Plot(data_sim, {}, PlotterEITData))

    def set_imaging_mode(self, eit_imaging: str, transform: str, show_abs: bool):
        """Set ei imaging mode for reconstruction"""
        if not isinstance(eit_imaging, str):
            raise TypeError("eit_imaging should be str")
        self.eit_imaging = IMAGING_TYPE[eit_imaging](transform, show_abs)
        self.to_gui.emit(EvtDataImagingInputsChanged(self.eit_imaging))

    def set_eit_model(self, eit_model: EITModel):
        """Set the used EIT model environement"""
        if not isinstance(eit_model, EITModel):
            raise TypeError("eit_model should be EITModel")
        self.eit_model = eit_model

    def set_solver(self, solver: Solver, eit_model: EITModel)->None:
        """Create reconstruction solver"""
        self.set_eit_model(eit_model)
        if not issubclass(solver, Solver):
            raise TypeError("solver should be Solver")
        self.solver = solver(self.eit_model)
        logger.info(f"Reconstructions solver selected: {self.solver}")

    def set_rec_params(self, params: RecParams):
        """Set reconstruction parameters for solver"""
        if not isinstance(params, RecParams):
            raise TypeError("params should be RecParams")
        self.params = params

    def set_monitoring(self, transform: str, show_abs: bool):
        """Set voltage channel imaging mode for data visualisation"""
        self.monitoring = ChannelVoltageImaging(transform, show_abs)

    def reset_monitoring_data(self):
        """Clear the Eit monitoring data for visualization"""
        self.monitoring_data = EITMeasMonitoring()
    
    def export_eit_data(self, path):
        self._data_exported=False
        data = {'X_h': self.last_eit_data.ref_frame,'X_ih': self.last_eit_data.frame }
        path= f"{path}"
        glob_utils.file.mat_utils.save_as_mat(path, data)
        self._data_exported=True
        
    def exported(self)->bool:
        return self._data_exported


if __name__ == "__main__":
    """"""
