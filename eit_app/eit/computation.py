
from queue import Queue
import logging
from typing import Any, Tuple
from eit_model.imaging_type import Imaging
import numpy as np
from eit_app.eit.plots import (
    PlotterChannelVoltageMonitoring,
    PlotterEITChannelVoltage,
    PlotterEITImage2D,
    PlotterEITData,
)
from glob_utils.thread_process.threads_worker import Poller
from glob_utils.decorator.decorator import catch_error
from eit_model.solver_abc import Solver, RecParams
from eit_model.model import EITModel
from eit_model.data import EITData,EITMeasMonitoring
from eit_model.plot import EITPlotsType, CustomLabels
from eit_app.com_channels import (
    AddToPlotSignal,
    Data2Compute,
    SignalReciever,
    Data2Plot,
)

logger = logging.getLogger(__name__)


class ComputingAgent(SignalReciever, AddToPlotSignal):


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

        self.eit_imaging = None
        self.ch_imaging = None
        self.eit_model = None
        self.U, self.labels = None, None
        self.extract_voltages = False
        self.solver: Solver = None
        self.rec_enable = False
        self.params = None
        self.reset_monitoring_data()

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
        #process only the last data added, ignore the rest
        while not self.input_buf.empty():
            data = self.input_buf.get()
        self.process(data)

    @catch_error
    def process(self, data: Data2Compute) -> None:
        """Compute the eit image
        - get eit_data for reconstruction
        - reconstruct eit image

        Args:
            data (Data2Compute): data for reconstruction
        """
        self._preprocess_ch_voltage_for_monitoring(data)
        eit_data, labels , frame_name=self._prepocess(data)
        self._rec_image(eit_data, labels, frame_name)
        
    def _prepocess(self, data: Data2Compute)-> Tuple[EITData, dict[EITPlotsType, CustomLabels], str]:
        """Returns the eit_data for reconstruction. During this method 
        the eit data er send fro ploting

        Args:
            data (Data2Compute): data for reconstruction

        Returns:
            Tuple[EITData, dict[EITPlotsType, CustomLabels], str]: eit_data for rec,
            labels for plots , and actual frame name
        """
        frame_name= data.labels[1][0]
        # prepocess eitdata for eit_imaging
        eit_data, labels = self.eit_imaging.process_data(
            **data.__dict__, eit_model=self.eit_model
        )
        self.to_plot.emit(Data2Plot(eit_data, labels, PlotterEITData))

        logger.info(f"{frame_name} - Voltages preproccessed")
        return eit_data, labels, frame_name

    def _preprocess_ch_voltage_for_monitoring(self, data: Data2Compute)-> None:
        """Prepocee the data for the monitoring of the voltages. During 
        this method the voltages values are send for ploting
        """
         # prepocess channel voltages for visualisation
        ch_data, ch_labels = self.ch_imaging.process_data(
            **data.__dict__, eit_model=self.eit_model
        )
        self.to_plot.emit(Data2Plot(ch_data, ch_labels, PlotterEITChannelVoltage))

        # volt, frame_idx= 1,1
        # self.eitmonitoringdata.add(volt, frame_idx)

        v = np.random.randn(256, 9)
        d = EITMeasMonitoring(volt_frame=v)
        self.to_plot.emit(Data2Plot(d, ch_labels, PlotterChannelVoltageMonitoring))

    def _rec_image(self, eit_data:EITData, labels:dict[EITPlotsType, CustomLabels], frame_name: str ):
        """Reconstruct EIT image 

        Args:
            eit_data (EITData): _description_
            labels (dict[EITPlotsType, CustomLabels]): _description_
            frame_name (str): for logging
        """
        if not self.rec_enable: 
            return
        if not self.solver.ready.is_set(): #
            logger.warning("Solver not set")
            return
        img_rec = self.solver.rec(eit_data)
        self.to_plot.emit(Data2Plot(img_rec, labels, PlotterEITImage2D))
        logger.info(f"Frame #{frame_name} - Image rec")

    def set_imaging_mode(self, eit_imaging: Imaging):
        """Set ei imaging mode for reconstruction
        """
        if not isinstance(eit_imaging, Imaging):
            return
        self.eit_imaging = eit_imaging

    def set_eit_model(self, eit_model: EITModel):
        """Set the used EIT model environement
        """
        if not isinstance(eit_model, EITModel):
            return
        self.eit_model = eit_model
    
    def enable_rec(self, enable: bool = True):
        """Enable the EIT image reconstruction. if set to `False` only 
        preprocessing of data to compute is done. (voltage meas. will be plot)
        """
        self.rec_enable = enable

    def set_solver(self, solver: Solver):
        """Create reconstruction solver
        """
        if not isinstance(self.eit_model, EITModel) and not isinstance(solver, Solver):
            return
        self.solver = solver(self.eit_model)
        logger.info(f"Reconstructions solver selected: {self.solver}")

    def set_rec_params(self, params: RecParams):
        """Set reconstruction parameters for solver"""
        if not isinstance(params, RecParams):
            return
        self.params = params

    @catch_error
    def init_solver(self, solver: Solver= None, params: Any = None)->None:
        """Initialize internal solver, optionaly new solver or reconstruction 
        parameters can be set before
        """
        self.set_solver(solver)
        self.set_rec_params(params)

        img_rec, data_sim = self.solver.prepare_rec(self.params)
        self.to_plot.emit(Data2Plot(img_rec, {}, PlotterEITImage2D))
        self.to_plot.emit(Data2Plot(data_sim, {}, PlotterEITData))

    def set_ch_imaging_mode(self, ch_imaging: Imaging):
        """Set voltage channel imaging mode for data visualisation
        """
        if not isinstance(ch_imaging, Imaging):
            return
        self.ch_imaging = ch_imaging

    def reset_monitoring_data(self):
        """Clear the Eit monitoring data for visualization
        """
        self.eitmonitoringdata = EITMeasMonitoring()


if __name__ == "__main__":
    """"""
    a = ComputingAgent()
    a.to_plot
