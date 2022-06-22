import logging
from eit_app.com_channels import (Data2Plot, SignalReciever)
from eit_model.model import EITModel
from eit_model.data import EITImage
from eit_model.pyvista_plot import PyVistaPlotWidget


logger = logging.getLogger(__name__)


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

    def treat_data2plot(self, data2plot: Data2Plot = None, **kwargs):
        """Put the data in the input buffer

        Args:
            data (Data2Compute, optional): data for computation. Defaults to None.
        """
        if not isinstance(data2plot, Data2Plot):
            logger.error(f"wrong type of data, type Data2Plot expected: {data2plot=}")
            return
        if self.w is not None:
            d = data2plot.data
            if isinstance(d, EITImage) and d.is_3D:
                self.w.plot_eit_image(d)
            elif isinstance(d, EITModel) and d.is_3D:
                self.w.set_eit_mdl(d)
            

    def init_window_3d(self, eit_mdl:EITModel) -> None:
        self.w = PyVistaPlotWidget(eit_mdl)

    def set_eit_model(self, eit_mdl:EITModel) -> None:
        if self.w is not None and eit_mdl.is_3D:
            self.w.set_eit_mdl(eit_mdl)


if __name__ == "__main__":
    """"""
