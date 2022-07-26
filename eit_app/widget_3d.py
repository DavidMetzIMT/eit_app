
import logging
from queue import Queue
from eit_app.com_channels import (Data2Plot, SignalReciever)
from eit_model.model import EITModel
from eit_model.data import EITImage
from eit_model.pyvista_plot import PyVistaPlotWidget
from queue import Queue
from glob_utils.thread_process.threads_worker import CustomWorker


logger = logging.getLogger(__name__)

class PyVista3DPlot:
    """"""

class Window3DAgent(SignalReciever):

    w: PyVistaPlotWidget

    def __init__(self):
        """The Window3Dagent is responsible of the creating and dispaching 
        the data to the 3D wigdget using conventioanl signal

        """
        super().__init__()

        self.init_reciever(data_callbacks={
            Data2Plot: self.treat_data2plot
            })
        self.w = None  # PyVistaPlotWidget(self, show=False)

        self._data_buffer = Queue(maxsize=2048)  # TODO maybe
        self._worker = CustomWorker(name="update_windows_3d", sleeptime=0.01)
        self._worker.progress.connect(self._process_data_for_update)
        self._worker.start()
        self._worker.start_polling()
        self.type= PyVista3DPlot()

    def _process_data_for_update(self) -> None:
        """Retrieve 
        """
        if self._data_buffer.empty():
            return
            
        while not self._data_buffer.empty():
            data:EITImage = self._data_buffer.get()
        dat= data.data
        logger.debug(f'{max(dat)=}\n\r{min(dat)=}\n\r{dat=}')
        self.w.plot_eit_image(data)

    def treat_data2plot(self, data2plot: Data2Plot = None, **kwargs):
        """Put the data in the input buffer

        Args:
            data (Data2Compute, optional): data for computation. Defaults to None.
        """
        if not isinstance(data2plot, Data2Plot):
            logger.error(f"wrong type of data, type Data2Plot expected: {data2plot=}")
            return
        if self.w is not None:
            if not isinstance(self.type, data2plot.destination):
                return
            d = data2plot.data
            if isinstance(d, EITImage) and d.is_3D:
                self._data_buffer.put(d)
            elif isinstance(d, EITModel) and d.is_3D:
                self.w.set_eit_mdl(d)
            

    def init_window_3d(self, eit_mdl:EITModel) -> None:
        self.w = PyVistaPlotWidget(eit_mdl)

    def set_eit_model(self, eit_mdl:EITModel) -> None:
        if self.w is not None and eit_mdl.is_3D:
            self.w.set_eit_mdl(eit_mdl)


if __name__ == "__main__":
    """"""
