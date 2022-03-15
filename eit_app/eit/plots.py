from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from logging import getLogger
from queue import Queue
from typing import Any

import matplotlib.backends.backend_qt5agg
import matplotlib.pyplot
import PyQt5.QtWidgets
from glob_utils.thread_process.threads_worker import Poller
from matplotlib.figure import Figure

import eit_model.data
import eit_model.plot.mesh

logger = getLogger(__name__)


@dataclass
class Data2Plot:
    data:Any=None
    labels:dict=field(default_factory=lambda:{})


class CustomLayout(ABC):
    """descripe a sort of plot"""

    allowed_data_type:tuple=()
    plotter:eit_model.plot.mesh.EITCustomPlots=None

    def __init__(self) -> None:
        super().__init__()
        self.allowed_data_type=()
        self._post_init_()  

    @abstractmethod
    def _post_init_(self):
        """Custom initialization"""
        # self.allowed_data_type=()    
        # self.plotter=eit_model.plot.mesh.EITImage2DPlot()

    def build(self, fig:Figure, data:Data2Plot):
        """Plot"""
        if not isinstance(fig, Figure):
            return

        if not isinstance(data.data, self.allowed_data_type):
            return

        fig.clear() # clear figure 

        self._build(fig, data.data, data.labels)
        
    @abstractmethod
    def _build(self, fig:Figure, data:Any, labels:dict):
        """Plot"""

class LayoutEITImage2D(CustomLayout):
    """_summary_

    Args:
        CustomPlots (_type_): _description_
    """
    def _post_init_(self):
        """Custom initialization"""
        self.allowed_data_type=(eit_model.data.EITImage)
        self.plotter=eit_model.plot.mesh.EITImage2DPlot()

    # @abstractmethod
    def _build(self, fig:Figure, data:Any, labels:dict):

        ax = fig.add_subplot(1, 1, 1)
        lab = labels.get(self.plotter.type)
        fig, ax = self.plotter.plot(fig, ax, data, lab)



class LayoutEITData(CustomLayout):
    """_summary_

    Args:
        CustomPlots (_type_): _description_
    """

    def _post_init_(self):
        """Custom initialization"""
        self.allowed_data_type=(eit_model.data.EITData)
        self.plotter=[
            eit_model.plot.mesh.EITUPlot(),
            eit_model.plot.mesh.EITUPlotDiff()
        ]

    # @abstractmethod
    def _build(self, fig:Figure, data:Any, labels:dict):

        ax = [fig.add_subplot(2, 1, 1), fig.add_subplot(2, 1, 2)]

        lab = labels.get(self.plotter[0].type)
        fig, ax[0] = self.plotter[0].plot(fig, ax[0], data, lab)

        lab = labels.get(self.plotter[1].type)
        fig, ax[1] = self.plotter[1].plot(fig, ax[1], data, lab)
        ax[1].sharex(ax[1])
        ax[0].set_xlabel("")
        fig.set_tight_layout(True)

class CanvasLayout(object):

    figure=None
    canvas=None
    toolbar=None

    layout_type:CustomLayout=None

    visible:bool=True

    def __init__(self, app, layout:PyQt5.QtWidgets.QVBoxLayout,layout_type:CustomLayout) -> None:

        if not isinstance(layout, PyQt5.QtWidgets.QVBoxLayout):
            raise TypeError("wrong layout type")

        if not issubclass(layout_type, CustomLayout):
            raise TypeError(f"wrong plot type {layout_type}")
        
        self.figure = matplotlib.pyplot.figure()
        self.canvas = matplotlib.backends.backend_qt5agg.FigureCanvasQTAgg(self.figure)
        self.toolbar = matplotlib.backends.backend_qt5agg.NavigationToolbar2QT(self.canvas, app)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

        self.layout_type= layout_type()

    def set_visible(self,visible:bool=True):
        self.visible=visible
        if not self.visible:
            self.clear_canvas()

    def clear_canvas(self):
        self.figure.clear()
        self.canvas.draw()

    def plot(self, data:Data2Plot):

        if not self.visible:
            self.clear_canvas()
            return

        self.layout_type.build(self.figure,data)
        self.canvas.draw()

class PlottingAgent(object):

    canvaslayout:list[CanvasLayout]

    def __init__(self):
        """Constructor"""
        self.input_buf = Queue()
        self.worker = Poller(
            name="plot", pollfunc=self.poll_input_buffer, sleeptime=0.01
        )
        self.worker.start()
        self.worker.start_polling()
        self.canvaslayout=[]

    def add_layouts(self, canvaslayout:CanvasLayout):
        self.canvaslayout.append(canvaslayout)
    
    def add_data2plot(self, data):
        self.input_buf.put(data)

    def poll_input_buffer(self):
        """Get last RX Frame contained in the input_buffer"""

        if self.input_buf.empty():
            return

        # loosing some informations
        while not self.input_buf.empty():
            data = self.input_buf.get(block=True)
        
        self.process(data)
    
    def process(self, data):
        """"""
        if not isinstance(data, Data2Plot):
            return
        [cl.plot(data) for cl in self.canvaslayout]


if __name__ == "__main__":
    """"""