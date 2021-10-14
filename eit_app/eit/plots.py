
import matplotlib.figure
import numpy as np
from matplotlib.figure import Figure
from eit_app.eit.reconstruction import ReconstructionPyEIT


def plot_conductivity_map(fig, ax, rec:ReconstructionPyEIT, perm_ds=True, nb_plots=3):
        if rec.InitDone:
            pts = rec.MeshObjMeas["node"]
            tri = rec.MeshObjMeas["element"]
            perm= rec.MeshObjMeas["perm"]
            ds= rec.MeshObjMeas["ds"]
            ax.clear()
            if perm_ds:
                im = ax.tripcolor(pts[:,0], pts[:,1], tri, np.real(perm), shading="flat")
            else:
                if hasattr(rec.eit, 'solver_type'):
                    if rec.eit.solver_type=='GREIT':
                        ds = rec.MeshObjMeas["ds_greit"]
                        im = ax.imshow(np.real(ds), interpolation="none", origin='lower', vmin=rec.Scalevmin, vmax=rec.Scalevmax)
                    else:
                        im = ax.tripcolor(pts[:,0], pts[:,1], tri, np.real(ds), shading="flat", vmin=rec.Scalevmin, vmax=rec.Scalevmax)
                else:
                    im = ax.tripcolor(pts[:,0], pts[:,1], tri, np.real(ds), shading="flat", vmin=rec.Scalevmin, vmax=rec.Scalevmax)
            for i, e in enumerate(rec.ElecPos):
                ax.annotate(str(i + 1), xy=(pts[e,0], pts[e,1]), color="r")   
            ax.axis("equal")
            ax.set_title('Reconstruction')
            fig.colorbar(im, ax=ax)
        else:
            ax.set_title('Reconstruction')
            ax.text(0.5, 0.5, 'pyEIT not initialized \n please choose an reconstruction algorithm', horizontalalignment='center', verticalalignment='center', transform=ax.transAxes,bbox=dict(facecolor='red', alpha=0.5))
        
        return fig, ax


def plot_measurements(fig, U, rec, current_label, plot_graphs:dict, imaging_parameters):
    figure= fig
    ax=[]
    graph_types=list(plot_graphs.keys())
    # print(graph_types)
    graph_2plot= [graph_type for graph_type in plot_graphs.keys() if plot_graphs[graph_type]==True ]
    # print(graph_2plot)
    nb_sub_plots= len(graph_2plot)
    # print(nb_sub_plots)
    if nb_sub_plots>0:
        if graph_2plot.count(graph_types[0])==1 and nb_sub_plots>1:
            ax.append(figure.add_subplot(nb_sub_plots+1,1,(1,2)))
            for indx in range(nb_sub_plots-1):
                ax.append(figure.add_subplot(nb_sub_plots+1,1,indx+3))
            # ax=[figure.add_subplot(nb_sub_plots+1,1,graph_indx+1) for graph_indx in range(nb_sub_plots+1)]
            # ax[0]= figure.add_subplot(nb_sub_plots+1,1,(1,2))
            # ax[1]= figure.add_subplot(nb_sub_plots+1,1,(1,2))
            # graph_2plot.insert(0,graph_types[0]) # add one fgraph to plot to reserve the place for the image!
        else:
            ax=[figure.add_subplot(nb_sub_plots,1,graph_indx+1) for graph_indx in range(nb_sub_plots)]
    else:
        ax=figure.add_subplot(111)
        ax.set_title('Select the type of plot you want!')
        return

    for  graph_indx, plot_graph in enumerate(graph_2plot):

        if plot_graph == graph_types[0]:
            # if graph_indx==0:
            figure, ax[graph_indx] =plot_conductivity_map(figure, ax[graph_indx], rec, perm_ds=False, nb_plots=nb_sub_plots)
            

        elif plot_graph == graph_types[1]:
            
            ax[graph_indx].plot(U[:,0], '-r', label=current_label[0])
            if not imaging_parameters[0][0]:# print('here secend plot', imaging_mode[0][0])
                ax[graph_indx].plot(U[:,1], '-b', label=current_label[1])
            ax[graph_indx].set_title(current_label[2])
            ax[graph_indx].set_xlabel('Measurements')
            ax[graph_indx].set_ylabel('Voltage U [V]')
            if imaging_parameters[4][0]:
                ax[graph_indx].set_yscale('log')
            # legend = ax[graph_indx].legend(loc='upper left', bbox_to_anchor=(1.05, 1))
            legend = ax[graph_indx].legend(loc='upper left')
        elif plot_graph == graph_types[2]:
            ax[graph_indx].plot((U[:,1]-U[:,0])*10**3, '-b',  label='diff')
            ax[graph_indx].set_title(current_label[3])
            ax[graph_indx].set_xlabel('Measurements')
            ax[graph_indx].set_ylabel('Voltage U [mV]')
            if imaging_parameters[4][0]:
                ax[graph_indx].set_yscale('log')
            # legend = ax[graph_indx].legend(loc='upper left', bbox_to_anchor=(1.05, 1))
            legend = ax[graph_indx].legend(loc='upper left')
            try:
                ax[graph_indx].sharex(ax[graph_2plot.index(graph_types[1])])
                ax[graph_2plot.index(graph_types[1])].set_xlabel('')
            except ValueError:
                pass
        
        
        # figure.subplot.left=0  # the left side of the subplots of the figure
        # figure.subplot.right=0    # the right side of the subplots of the figure
        # figure.subplot.bottom=0   # the bottom of the subplots of the figure
        # figure.subplot.top=0   # the top of the subplots of the figure
        # figure.subplot.wspace=0.2    # the amount of width reserved for space between subplots,
        #                         #expressed as a fraction of the average axis width
        # figure.subplot.hspace=0.2    # the amount of height reserved for space between subplots,
        #                         #expressed as a fraction of the average axis height

        
        # fig=Figure(figsize=None, dpi=None, facecolor=None, edgecolor=None, linewidth=0.0, frameon=None, subplotpars=None, tight_layout=None, constrained_layout=None)
        figure.set_tight_layout(True)
        #figure.subplots_adjust(left=0.1, bottom=0, right=1, top=1, wspace=0.1, hspace=0.1)
    return figure










if __name__ == "__main__":
    pass
    # 
