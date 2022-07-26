import logging
from queue import Queue
from typing import Any


from eit_app.com_channels import (AddToGuiSignal, AddToPlotSignal,
                                  Data2Compute, Data2Plot, SignalReciever)
from eit_app.plots import (PlotterChannelVoltageMonitoring,
                               PlotterEITChannelVoltage, PlotterEITData,
                               PlotterEITImage2D, PlotterEITImage2Greit,
                               PlotterEITImageElemData)
from eit_model.greit import greit_filter
from eit_model.reconstruction import EITReconstruction
from eit_model.solver_abc import Solver
from eit_model.data import EITReconstructionData, EITFrameMeasuredChannelVoltage
from glob_utils.decorator.decorator import catch_error
from glob_utils.thread_process.threads_worker import Poller
import glob_utils.file.mat_utils

from eit_app.widget_3d import PyVista3DPlot

logger = logging.getLogger(__name__)


class ComputingAgent(SignalReciever, AddToPlotSignal, AddToGuiSignal):
    def __init__(self, reconstruction: EITReconstruction):
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
        self._data_exported=False
        self.eit_rec= reconstruction

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

    @catch_error
    def init_solver(self, solver: Solver, params: Any) -> None:
        """Initialize internal solver, optionaly new solver or reconstruction
        parameters can be set before
        """
        img_rec, data_sim =self.eit_rec.init_solver(solver,params)

        self.to_plot.emit(Data2Plot(self.eit_rec.eit_model, {}, PyVista3DPlot))
        self.to_plot.emit(Data2Plot(img_rec, {}, PlotterEITImage2D))
        self.to_plot.emit(Data2Plot(data_sim, {}, PlotterEITData))

    @catch_error
    def process(self, data: Data2Compute) -> None:
        """Compute the eit image
        - get eit_data for reconstruction
        - reconstruct eit image

        Args:
            data (Data2Compute): data for reconstruction
        """
        self._is_processing= True

        # convert Data2Compute to EITReconatrsuction data
        data_rec= EITReconstructionData(
            ref_frame= EITFrameMeasuredChannelVoltage(
                volt= data.v_ref.volt,
                name=data.v_ref.get_frame_name(),
                freq=data.v_ref.get_frame_freq(),
            ),
            meas_frame= EITFrameMeasuredChannelVoltage(
                volt= data.v_meas.volt,
                name=data.v_meas.get_frame_name(),
                freq=data.v_meas.get_frame_freq(),
            ),
        )
        self.eit_rec.rec_process(data_rec)
        
        # monitoring
        monitoring_data, ch_data, ch_labels= self.eit_rec.monitoring_results()
        self.to_plot.emit(Data2Plot(ch_data, ch_labels, PlotterEITChannelVoltage))
        self.to_plot.emit(
             Data2Plot(monitoring_data, ch_labels, PlotterChannelVoltageMonitoring)
        )
        eit_image, eit_data, plot_labels= self.eit_rec.imaging_results()
        self.to_plot.emit(Data2Plot(eit_data, plot_labels, PlotterEITData))
        if eit_image is not None:
            # EIT data EIT image plot
            self.to_plot.emit(Data2Plot(eit_image, plot_labels, PlotterEITImage2D))
            self.to_plot.emit(Data2Plot(eit_image, plot_labels, PlotterEITImageElemData))
            self.to_plot.emit(Data2Plot(eit_image, plot_labels, PyVista3DPlot))
            self.to_plot.emit(Data2Plot(greit_filter(eit_image), plot_labels, PlotterEITImage2Greit))
        self._is_processing= False

    def export_eit_data(self, path):
        self._data_exported=False
        _, eit_data, _= self.eit_rec.imaging_results()
        data = {'X_h': eit_data.ref_frame,'X_ih': eit_data.frame }
        path= f"{path}"
        glob_utils.file.mat_utils.save_as_mat(path, data)
        self._data_exported=True
        
    def exported(self)->bool:
        return self._data_exported


if __name__ == "__main__":
    """"""
