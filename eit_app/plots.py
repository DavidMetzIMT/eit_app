import logging
from abc import ABC, abstractmethod
from queue import Queue
from typing import Any

import matplotlib.pyplot
from eit_app.com_channels import Data2Plot, SignalReciever
from eit_model.data import EITData, EITImage, EITMeasMonitoringData
from eit_model.plot import (
    EITCustomPlots,
    EITElemsDataPlot,
    EITImage2DPlot,
    EITUPlot,
    EITUPlotDiff,
    MeasErrorPlot,
)
from glob_utils.file.utils import FileExt, append_extension
from glob_utils.thread_process.threads_worker import Poller
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QVBoxLayout

logger = logging.getLogger(__name__)


class Plotter(ABC):

    _allowed_data_type: tuple = None
    _plotting_func: list[EITCustomPlots] = None
    _tag: str = ""

    def __init__(self) -> None:
        """Create a plotter which plot defined type of data using predefined
        plotting function
        """
        super().__init__()
        self._allowed_data_type = ()
        self._post_init_()

    @abstractmethod
    def _post_init_(self):
        """Initialization of each custom Plotter
        here should _allowed_data_type and _plotting_func be defined"""
    
    def set_options(self, **kwargs):
        """Set some plotting options
        valid kwargs:"""
        for p in self._plotting_func:
            p.set_options(**kwargs)

    def build(self, fig: Figure, data: Data2Plot):
        """Build the layout of the figure with the data

        Args:
            fig (matplotlib.pyplot.Figure): figure were to plot
            data (Data2Plot): data to plot
        """

        if not isinstance(fig, Figure):
            return

        if not isinstance(data.data, self._allowed_data_type):
            return

        fig.clear()  # clear figure

        self._build(fig, data.data, data.labels)

    @abstractmethod
    def _build(self, fig: Figure, data: Any, labels: dict):
        """Custom layout build of each custom Plotter"""

    def get_saving_path(self, path: str, ext: FileExt = FileExt.png) -> str:
        """return a fromated path"""
        return append_extension(f"{path}_{self._tag}", ext)


class PlotterEITImage2D(Plotter):
    """Plot a 2D EIT image"""

    def _post_init_(self):
        self._allowed_data_type = EITImage
        self._plotting_func = [EITImage2DPlot()]
        self._tag = "EITImage2D"

    def _build(self, fig: Figure, data: Any, labels: dict):
        ax = fig.add_subplot(1, 1, 1)
        lab = labels.get(self._plotting_func[0].type)
        fig, ax = self._plotting_func[0].plot(fig, ax, data, lab)
        fig.set_tight_layout(True)


class PlotterEITImage2Greit(Plotter):
    """Plot a 2D EIT image"""

    def _post_init_(self):
        self._allowed_data_type = EITImage
        self._plotting_func= [EITImage2DPlot()]
        self._tag = "EITImage2Greit"

    def _build(self, fig: Figure, data: Any, labels: dict):
        ax = fig.add_subplot(1, 1, 1)
        lab = labels.get(self._plotting_func[0].type)
        self._plotting_func[0].set_options(colorbar_range=[-1, 1], cmap="turbo")
        fig, ax = self._plotting_func[0].plot(fig, ax, data, lab   )
        fig.set_tight_layout(True)


class PlotterEITImageElemData(Plotter):
    """Plot a 2D EIT image"""

    def _post_init_(self):
        self._allowed_data_type = EITImage
        self._plotting_func = [EITElemsDataPlot()]
        self._tag = "EITImageElemData"

    def _build(self, fig: Figure, data: Any, labels: dict):
        ax = fig.add_subplot(1, 1, 1)
        lab = labels.get(self._plotting_func[0].type)
        fig, ax = self._plotting_func[0].plot(fig, ax, data, lab)
        fig.set_tight_layout(True)


class PlotterEITData(Plotter):
    """Plots the EIT reconstruction data.
    - Uplot
    - and Diffplot
    """

    def _post_init_(self):
        self._allowed_data_type = EITData
        self._plotting_func = [EITUPlot(), EITUPlotDiff()]
        self._tag = "EITData"

    def _build(self, fig: Figure, data: Any, labels: dict):
        ax = [fig.add_subplot(2, 1, 1), fig.add_subplot(2, 1, 2)]
        lab = labels.get(self._plotting_func[0].type)
        fig, ax[0] = self._plotting_func[0].plot(fig, ax[0], data, lab)
        lab = labels.get(self._plotting_func[1].type)
        fig, ax[1] = self._plotting_func[1].plot(fig, ax[1], data, lab)
        ax[1].sharex(ax[1])
        ax[0].set_xlabel("")
        fig.set_tight_layout(True)


class PlotterEITChannelVoltage(Plotter):
    """Plot the voltages in a Uplot graph"""

    def _post_init_(self):
        self._allowed_data_type = EITData
        self._plotting_func = [EITUPlot()]
        self._tag = "EITChannelVoltage"

    def _build(self, fig: Figure, data: Any, labels: dict):
        ax = fig.add_subplot(1, 1, 1)
        lab = labels.get(self._plotting_func[0].type)
        fig, ax = self._plotting_func[0].plot(fig, ax, data, lab)
        fig.set_tight_layout(True)


class PlotterChannelVoltageMonitoring(Plotter):
    """_summary_"""

    def _post_init_(self):
        self._allowed_data_type = EITMeasMonitoringData
        self._plotting_func = [MeasErrorPlot()]
        self._tag = "ChannelVoltageMonitoring"

    def _build(self, fig: Figure, data: Any, labels: dict):
        ax = fig.add_subplot(1, 1, 1)
        lab = labels.get(self._plotting_func[0].type)
        # fig, ax = self._plotting_func[0].plot(fig, ax, data, lab)
        fig.set_tight_layout(True)


class CanvasLayout(object):

    _figure: Figure = None
    _canvas = None
    _toolbar = None
    _plotter: Plotter = None
    _visible: bool = True
    _gui = None
    _last_data: Data2Plot = None

    def __init__(self, gui, layout: QVBoxLayout, plotter: Plotter) -> None:
        """Create a CanvasLayout object with predefined plotter,
        which build a prefdined gaph layout

        Args:
            gui (_type_): obj in whcoh the layout is defined
            layout (QVBoxLayout): layout where the plotter
            should plot
            plotter(Plotter): predefined layout plotter

        Raises:
            TypeError: is raised if layout is not "QVBoxLayout",
            or if layout_type is not "CustomLayout"
        """

        if not isinstance(layout, QVBoxLayout):
            raise TypeError("wrong layout type")

        if not issubclass(plotter, Plotter):
            raise TypeError(f"wrong plot type {plotter}")

        self._gui = gui
        self._layout = layout
        self._plotter = plotter()
        self._init_layout()
        self._export_path = []

    def _init_layout(self, **kwargs):
        """"""
        dpi = kwargs.pop("dpi", 100)
        self._figure: Figure = matplotlib.pyplot.figure(dpi=dpi)
        self._canvas = FigureCanvasQTAgg(self._figure)
        self._toolbar = NavigationToolbar2QT(self._canvas, self._gui)
        self._layout.addWidget(self._toolbar)
        self._layout.addWidget(self._canvas)
        self.clear_canvas()

    def set_options(self, **kwargs):
        """Set some plotting options
        valid kwargs:
        dpi= val"""
        if dpi := kwargs.pop("dpi", None):
            self._layout.removeWidget(self._toolbar)
            self._layout.removeWidget(self._canvas)
            self._init_layout(dpi=dpi)

        self._plotter.set_options(**kwargs)

        if self._last_data:
            self.plot(self._last_data)

    def set_visible(self, visible: bool = True):
        """Make the Canvas visible or insisible"""
        self._visible = visible
        if not self._visible:
            self.clear_canvas()

    def clear_canvas(self):
        """Make the Canvas visible or insisible"""
        self._figure.clear()
        self._canvas.draw()

    def add_export_path(self, path: str):
        logger.debug(f"{path}")
        self._export_path.append(path)

    def all_exported(self) -> bool:
        return len(self._export_path) == 0

    def auto_export(self):
        if self._export_path:
            self.export_plot(self._export_path.pop(0))

    def export_plot(self, path: str = "test") -> None:
        """"""
        path = self._plotter.get_saving_path(path)
        logger.info(f"figure saved: {path}")
        self._figure.savefig(path)

    def plot(self, data: Data2Plot):
        """Plot the data in Make the Canvas visible or insisible"""
        if not self._visible:
            self.clear_canvas()
            return
        self._plotter.build(self._figure, data)
        self._last_data = data
        self._canvas.draw()
        self.auto_export()


class PlottingAgent(SignalReciever):

    _canvaslayout: list[CanvasLayout]

    def __init__(self) -> None:
        """The PlottingAgent is responsible of actualizating plots in the gui

        It can manage multiple canvas (CanvasLayout) present on the gui.

        The data are put in an input buffer,
        - as soon as some Data2Plot are send to it via a signal

            >> obj.to_plot.connect(plotting_agent.to_reciever)

            >> obj.to_plot.emit(Data2Plot(...))

        - or directly

            >> plotting_agent.add_data2plot(Data2Plot(...))


        They are then retrieved one by one by a Thread and plot in their
        corrresponding Canvas layout destination

        """
        super().__init__()
        self.init_reciever(data_callbacks={Data2Plot: self.add_data2plot})
        self._input_buf = Queue()
        self._worker = Poller(
            name="plot", pollfunc=self._poll_input_buffer, sleeptime=0.01
        )
        self._worker.start()
        self._worker.start_polling()
        self._canvaslayout = []

    def add_canvas(self, canvaslayout: CanvasLayout) -> None:
        """Add a CanvasLayout fro uptatding via this plotting agent"""
        self._canvaslayout.append(canvaslayout)

    def add_data2plot(self, data: Data2Plot, **kwargs) -> None:
        """Add data to plot in input buffer"""
        self._input_buf.put(data)

    def _poll_input_buffer(self) -> None:
        """Retrieve the data to plot one by one"""
        if self._input_buf.empty():
            return
        data = self._input_buf.get(block=True)
        self._process(data)

    def _process(self, data: Data2Plot) -> None:
        """Plot the data in their corrresponding Canvas layout destination"""
        if not isinstance(data, Data2Plot):
            return
        for cl in self._canvaslayout:
            if isinstance(cl._plotter, data.destination):
                cl.plot(data)


if __name__ == "__main__":
    """"""
