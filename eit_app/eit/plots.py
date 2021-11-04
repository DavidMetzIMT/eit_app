
from abc import ABC, abstractmethod
from enum import Enum
from typing import List
import matplotlib.figure as mfig
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure
from numpy.lib.shape_base import tile
from eit_app.eit.model import EITModelClass
# from eit_app.eit.reconstruction import ReconstructionPyEIT
class PlotType(Enum):
    Image_2D='Image_2D'
    Image_3D='Image_3D'
    U_plot='U_plot'
    Diff_plot='Diff_plot'

class CustomPlots(ABC):
    """ descripe a sort of plot"""

    is_visible:bool=False
    def __init__(self) -> None:
        super().__init__()

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
    def set_legend(self, legend:List[str]=['', '']):
        self.label['legend']= legend
    def set_axis(self, axis:List[str]=['', '']):
        self.label['axis']= axis
    def set(self, title:str='', legend:List[str]=['', ''], axis:List[str]=['', '']):
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

    def __init__(self, is_visible:bool=False) -> None:
        super().__init__()
        self.name=PlotType.Image_2D
        self.is_visible=is_visible
    
    def plot(self, fig, ax, model:EITModelClass, labels):

        label = labels[self.name]
        pts, tri, data= model.fem.get_data_for_plots()

        ax.clear()
        im = ax.tripcolor(pts[:,0], pts[:,1], tri, np.real(data), shading="flat")
        # for i, e in enumerate(rec.ElecPos):
        #     ax.annotate(str(i + 1), xy=(pts[e,0], pts[e,1]), color="r")   
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

    def __init__(self, is_visible:bool=False, y_axis_log:bool=False) -> None:
        super().__init__()
        self.name=PlotType.U_plot
        self.is_visible=is_visible
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

    def __init__(self, is_visible:bool=False, y_axis_log:bool=False) -> None:
        super().__init__()
        self.name=PlotType.Diff_plot
        self.is_visible=is_visible
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

# def plot_conductivity_map(fig, ax, rec:ReconstructionPyEIT, perm_ds=True, nb_plots=3):
#         if rec.InitDone:
#             pts = rec.MeshObjMeas["node"]
#             tri = rec.MeshObjMeas["element"]
#             perm= rec.MeshObjMeas["perm"]
#             ds= rec.MeshObjMeas["ds"]
#             ax.clear()
#             if perm_ds:
#                 im = ax.tripcolor(pts[:,0], pts[:,1], tri, np.real(perm), shading="flat")
#             else:
#                 if hasattr(rec.eit, 'solver_type'):
#                     if rec.eit.solver_type=='GREIT':
#                         ds = rec.MeshObjMeas["ds_greit"]
#                         im = ax.imshow(np.real(ds), interpolation="none", origin='lower', vmin=rec.Scalevmin, vmax=rec.Scalevmax)
#                     else:
#                         im = ax.tripcolor(pts[:,0], pts[:,1], tri, np.real(ds), shading="flat", vmin=rec.Scalevmin, vmax=rec.Scalevmax)
#                 else:
#                     im = ax.tripcolor(pts[:,0], pts[:,1], tri, np.real(ds), shading="flat", vmin=rec.Scalevmin, vmax=rec.Scalevmax)
#             for i, e in enumerate(rec.ElecPos):
#                 ax.annotate(str(i + 1), xy=(pts[e,0], pts[e,1]), color="r")   
#             ax.axis("equal")
#             ax.set_title('Reconstruction')
#             fig.colorbar(im, ax=ax)
#         else:
#             ax.set_title('Reconstruction')
#             ax.text(0.5, 0.5, 'pyEIT not initialized \n please choose an reconstruction algorithm', horizontalalignment='center', verticalalignment='center', transform=ax.transAxes,bbox=dict(facecolor='red', alpha=0.5))
        
#         return fig, ax


def plot_measurements(plot_to_show:List[CustomPlots], fig,  U, labels, model:EITModelClass):
    # figure.clear()???
    fig= fig
    fig.clear()
    ax=[fig.add_subplot(2,1,1),fig.add_subplot(2,1,2)]
    # plot_visible = [p for p in plot_to_show if p.is_visible] # get rid of the plost we dont need

    # nb_sub_plots = len(plot_visible)
    # if nb_sub_plots==0:
    #     ax=fig.add_subplot(111)
    #     ax.set_title('Select the type of plot you want!')
    #     return fig
    
    # if isinstance(plot_visible[0], PlotImage2D) and nb_sub_plots>1:
    #     ax.append(fig.add_subplot(nb_sub_plots+1,1,(1,2)))
    #     for indx in range(nb_sub_plots-1):
    #         ax.append(fig.add_subplot(nb_sub_plots+1,1,indx+3))
    # else:
    #     ax=[fig.add_subplot(nb_sub_plots,1,graph_indx+1) for graph_indx in range(nb_sub_plots)]

    # for  idx_ax, single_plot in enumerate(plot_visible):
        
       
    fig, ax[0]= plot_to_show[1].plot(fig, ax[0], U, labels)
    fig, ax[1]= plot_to_show[2].plot(fig, ax[1], U, labels)
    ax[1].sharex(ax[1])
    ax[0].set_xlabel('')
    fig.set_tight_layout(True)
        #figure.subplots_adjust(left=0.1, bottom=0, right=1, top=1, wspace=0.1, hspace=0.1)
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
    pass
    # 
