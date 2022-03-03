
from abc import ABC, abstractmethod
from enum import Enum
from typing import List
import matplotlib.figure as mfig
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from numpy.lib.shape_base import tile
from eit_app.eit.eit_model import EITModelClass
# from eit_app.eit.reconstruction import ReconstructionPyEIT
from logging import getLogger

logger = getLogger(__name__)
class PlotType(Enum):
    Image_2D='Image_2D'
    Image_3D='Image_3D'
    U_plot='U_plot'
    Diff_plot='Diff_plot'

class CustomPlots(ABC):
    """ descripe a sort of plot"""

    visible:bool=False
    def __init__(self) -> None:
        super().__init__()
    
    def is_visible(self):
        return self.visible

    @abstractmethod
    def plot():
        """Plot"""

class CustomLabels():
    """ organize the labels utilized by a plot"""

    def __init__(self) -> None:
        self.label= {}
        self.set()

    def set_title(self, title:str=''):
        self.label['title']=title

    def set_legend(self, legend: List[str] = None):
        if legend is None:
            legend = ['', '']
        self.label['legend']= legend

    def set_axis(self, axis: List[str] = None):
        if axis is None:
            axis = ['', '']
        self.label['axis']= axis

    def set(self, title:str='', legend: List[str] = None, axis: List[str] = None):
        if legend is None:
            legend = ['', '']
        if axis is None:
            axis = ['', '']
        self.set_title(title)
        self.set_legend(legend)
        self.set_axis(axis)

    def get(self)-> dict:
        return self.label

    def get_title(self)->str:
        return self.label['title']

    def get_legend(self)->List[str]:
        return self.label['legend']

    def get_axis(self)->List[str]:
        return self.label['axis']

class PlotImage2D(CustomPlots):
    """_summary_

    Args:
        CustomPlots (_type_): _description_
    """

    def __init__(self, is_visible:bool=False) -> None:
        super().__init__()
        self.name=PlotType.Image_2D
        self.visible=is_visible
    
    def plot(self, fig:Figure, ax:Axes, model:EITModelClass, labels):
        
        logger.debug('PlotImage2D')

        label = labels[self.name]
        pts, tri, data= model.fem.get_data_for_plots()
        ax.clear()
        im = ax.tripcolor(pts[:,0], pts[:,1], tri, np.real(data), shading="flat")
        ax.axis("equal")
        ax.set_title(label['title'])
        ax.set_xlabel(label['xylabel'][0])
        if len(label['xylabel'])==2:
            ax.set_ylabel(label['xylabel'][1])
        fig.colorbar(im, ax=ax)
        # else:
        #     ax.set_title('Reconstruction')
        #     ax.text(0.5, 0.5, 'pyEIT not initialized \n please choose an reconstruction algorithm', horizontalalignment='center', verticalalignment='center', transform=ax.transAxes,bbox=dict(facecolor='red', alpha=0.5))
        return fig, ax

class PlotUPlot(CustomPlots):
    """_summary_

    Args:
        CustomPlots (_type_): _description_
    """

    def __init__(self, is_visible:bool=False, y_axis_log:bool=False) -> None:
        super().__init__()
        self.name=PlotType.U_plot
        self.visible=is_visible
        self.y_axis_log=y_axis_log

    def plot(self, fig, ax, U:np.ndarray, labels):
        """Plot"""
        label = labels[self.name]
        # print(U)
        ax.plot(U[:,0], '-b', label=label['legend'][0])
        ax.plot(U[:,1], '-r', label=label['legend'][1])

        ax.set_title(label['title'])
        ax.set_xlabel(label['xylabel'][0])
        if len(label['xylabel'])==2:
            ax.set_ylabel(label['xylabel'][1])
        if self.y_axis_log:
            ax.set_yscale('log')
        # legend = ax[graph_indx].legend(loc='upper left', bbox_to_anchor=(1.05, 1))
        if label['legend'][0] != '':
            legend = ax.legend(loc='upper left')
        return fig, ax

class PlotDiffPlot(CustomPlots):
    """_summary_

    Args:
        CustomPlots (_type_): _description_
    """

    def __init__(self, is_visible:bool=False, y_axis_log:bool=False) -> None:
        super().__init__()
        self.name=PlotType.Diff_plot
        self.visible=is_visible
        self.y_axis_log=y_axis_log

    def plot(self, fig, ax, U:np.ndarray, labels):
        """Plot"""
        label = labels[self.name]
        # print(U)
        ax.plot(U[:,1]-U[:,0], '-g',  label=label['legend'][0])

        ax.set_title(label['title'])
        ax.set_xlabel(label['xylabel'][0])
        if len(label['xylabel'])==2:
            ax.set_ylabel(label['xylabel'][1])
        if self.y_axis_log:
            ax.set_yscale('log')
        if label['legend'][0] != '':
            legend = ax.legend(loc='upper left')

        return fig, ax

def plot_measurements(plot_to_show:List[CustomPlots], fig,  data):
    """_summary_

    Args:
        plot_to_show (List[CustomPlots]): _description_
        fig (_type_): _description_
        data (_type_): _description_

    Returns:
        _type_: _description_
    """
    if not plot_to_show[1].is_visible() and not plot_to_show[2].is_visible():
        return fig
    U=data['U']
    labels=data['labels']
    # eit_model=data['eit_model']
    fig= fig
    fig.clear()
    ax=[fig.add_subplot(2,1,1),fig.add_subplot(2,1,2)]
    fig, ax[0]= plot_to_show[1].plot(fig, ax[0], U, labels)
    fig, ax[1]= plot_to_show[2].plot(fig, ax[1], U, labels)
    ax[1].sharex(ax[1])
    ax[0].set_xlabel('')
    fig.set_tight_layout(True)
    return fig

def plot_rec(plot_to_show:List[CustomPlots], fig,  data):
    """_summary_

    Args:
        plot_to_show (List[CustomPlots]): _description_
        fig (_type_): _description_
        data (_type_): _description_

    Returns:
        _type_: _description_
    """

    fig= fig
    if not plot_to_show[0].is_visible():
        return fig
    # U=data['U']
    labels=data['labels']
    eit_model=data['eit_model']
    fig.clear()
    ax=[fig.add_subplot(1,1,1)]
    fig, ax[0]= plot_to_show[0].plot(fig, ax[0], eit_model, labels)
    return fig


# def plot_measurements(plot_to_show:List[CustomPlots], fig,  U, labels, model:EITModelClass):
#     # figure.clear()???
#     fig= fig
#     fig.clear()
#     ax=[]
#     plot_visible = [p for p in plot_to_show if p.is_visible] # get rid of the plost we dont need

#     nb_sub_plots = len(plot_visible)
#     if nb_sub_plots==0:
#         ax=fig.add_subplot(111)
#         ax.set_title('Select the type of plot you want!')
#         return fig
    
#     if isinstance(plot_visible[0], PlotImage2D) and nb_sub_plots>1:
#         ax.append(fig.add_subplot(nb_sub_plots+1,1,(1,2)))
#         for indx in range(nb_sub_plots-1):
#             ax.append(fig.add_subplot(nb_sub_plots+1,1,indx+3))
#     else:
#         ax=[fig.add_subplot(nb_sub_plots,1,graph_indx+1) for graph_indx in range(nb_sub_plots)]

#     for  idx_ax, single_plot in enumerate(plot_visible):
        
#         if isinstance(single_plot, PlotImage2D):
#             fig, ax[idx_ax]= single_plot.plot(fig, ax[idx_ax], model, labels)
#         else:
#             fig, ax[idx_ax]= single_plot.plot(fig, ax[idx_ax], U, labels)
#             try:
#                 if idx_ax>=1:
#                     ax[idx_ax].sharex(ax[idx_ax])
#                     ax[idx_ax-1].set_xlabel('')
#             except:
#                 print('sharex failed')
#         fig.set_tight_layout(True)
#         #figure.subplots_adjust(left=0.1, bottom=0, right=1, top=1, wspace=0.1, hspace=0.1)
#     return fig




if __name__ == "__main__":

    """"""
     
