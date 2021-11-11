



import os
from multiprocessing.queues import Queue



import matplotlib.pyplot as plt
import numpy as np
from pyeit.eit.base import EitBase

import pyeit.eit.bp as bp
import pyeit.eit.greit as greit
import pyeit.eit.jac as jac
import pyeit.mesh as mesh
import pyeit.mesh.plot as mplot

from pyeit.eit.fem import Forward
from pyeit.eit.interp2d import pts2sim, sim2pts
from pyeit.eit.utils import eit_scan_lines


from eit_app.eit.model import EITModelClass
from eit_app.eit.rec_abs import RecCMDs, Reconstruction
from eit_app.utils.flag import CustomFlag
from logging import getLogger

logger = getLogger(__name__)
# from eit_app.io.sciospec.device import *
# from eit_app.io.sciospec.interface.serial4sciospec import 
# from eit_app.eit.meas_preprocessing import *

# from eit_tf_workspace.path_utils import get_dir
# from eit_tf_workspace.train_models import ModelGenerator
# from eit_tf_workspace.train_utils import TrainInputs
# from eit_tf_workspace.constants import TRAIN_INPUT_FILENAME
# from eit_tf_workspace.dataset import get_XY_from_MalabDataSet, dataloader, extract_samples
# from eit_tf_workspace.draw_data import format_inputs, get_elem_nodal_data
## ======================================================================================================================================================
##  Class for EIT Reconstruction
## ======================================================================================================================================================
class ReconstructionPyEIT(Reconstruction):
    """ Class for the EIT reconstruction with the package pyEIT """

    def __post_init__(self):
        self.eit:EitBase=None

    def initialize(self, model:EITModelClass, U):
        """ should initialize the reconstruction method and return some data to plot"""
        self.initialized.reset()
        MeshObj, ElecPos= self._construct_mesh(
                    model.get_nd_elecs(),
                    model.get_fem_refinement(),
                    model.chamber.get_chamber_limit()
                )
        # model.fem.update_from_pyeit(self.MeshObj)

        ex_mat = eit_scan_lines(ne=model.get_nd_elecs(), dist=1)
        
        logger.info(f'Initialisation of PyEIT; solver:{model.SolverType}')
        
        # if verbose>0:
        #     self._print_mesh_nodes_elemts(self.MeshObj)
        #     self._plot_mesh()
        #     self._plot_conductivity_map(self.MeshObj)
    
        """ 1. problem setup """
        anomaly = [{"x": 0.5, "y": 0.5, "d": 0.1, "perm": 2}]
        MeshObjSim = mesh.set_perm(MeshObj, anomaly=anomaly,background=0.01)
        MeshObjSim= _reconstruct_mesh_struct(MeshObjSim)
        # if verbose>0:
        #     self._print_mesh_nodes_elemts(self.MeshObjSim)
        #     self._plot_conductivity_map(self.MeshObjSim)

        """ 2. FEM simulation """
        # # calculate simulated data
        step_solver = 1
        fwd = Forward(MeshObj, ElecPos)
        f0 = fwd.solve_eit(ex_mat, step=step_solver, perm=MeshObj["perm"])
        f1 = fwd.solve_eit(ex_mat, step=step_solver, perm=MeshObjSim["perm"])

        self.eit=get_solver_pyeit(model.SolverType,MeshObj, ElecPos, ex_mat,step_solver, model.p, model.lamb, model.n)
        # ds=_inv_solve_eit(self.eit,f1.v, f0.v, True)
        MeshObj["perm"]=_inv_solve_eit(self.eit,f1.v, f0.v, True)
        model.fem.update_from_pyeit(MeshObj)
        self._print_mesh_nodes_elemts(MeshObj)
        self.initialized.set()
        return model, np.hstack((np.reshape(f1.v,(f1.v.shape[0],1)), np.reshape(f0.v,(f0.v.shape[0],1))))
        
    def reconstruct(self,  model:EITModelClass, U):
        """ return the reconstructed reconstructed conductivities values for the FEM"""
        if self.initialized.is_set():
            """ DO SOMETTHING and return data of reconstruction"""
            MeshObj=model.fem.get_pyeit_mesh()
            MeshObj["perm"]=_inv_solve_eit(self.eit,U[:,1],U[:,0], True)
            model.fem.update_from_pyeit(MeshObj)
        return model, U

    def _construct_mesh(self, elec_nb, fem_refinement, bbox):
        MeshObj, ElecPos = mesh.create(n_el=elec_nb, h0=fem_refinement, bbox=bbox)
        MeshObj= _reconstruct_mesh_struct(MeshObj)
        return MeshObj, ElecPos

    def _print_mesh_nodes_elemts(self, mesh_obj):

        pts = mesh_obj["node"]
        tri = mesh_obj["element"]
        conduct= mesh_obj["perm"]
        # # report the status of the 2D mesh
        # quality.stats(pts, tri)
        print("mesh status:")
        print("%d nodes, %d elements, %d perm" % (pts.shape[0], tri.shape[0], conduct.shape[0]))
        
    def imageReconstruct(self, v1=None, v0=None):
            if not self.running:
                if self.InitDone:
                    self._inv_solve_eit(U[:,1],U[:,0])
                    # self._plot_conductivity_map(self.MeshObjMeas, perm_ds=False)
                    return True
                else:
                    print('please Init the reconstruction')
            else:
                print('Reconstruction Busy')
                return False

    # def setScalePlot(self, vmax, vmin):
    #     if vmax==0.0 and vmin == 0.0:
    #         self.Scalevmin = None
    #         self.Scalevmax= None
    #     else:
    #         self.Scalevmin = vmin
    #         self.Scalevmax= vmax

    def setNormalize(self, normalize):
        self.Normalize= normalize

    def pollCallback(self, queue_in:Queue, queue_out:Queue):
        if not queue_in.empty():
            data=queue_in.get()
            if data['cmd']=='initpyEIT':
                self.initPyeit(eit_model=data['eit_model'], plot2Gui=data['plot2Gui'])
                queue_out.put({'cmd': 'updatePlot','rec': self})
                print(data)
            elif data['cmd']=='setScalePlot':  
                self.setScalePlot(data['vmax'], data['vmin'])
                self.setNormalize(data['normalize'])
            elif data['cmd']=='recpyEIT':
                self.imageReconstruct(data['v1'], data['v0'])
                queue_out.put({'cmd': 'updatePlot','rec': self})

    # def queue_wrapper(self, queue:Queue, cmd):

    #     if cmd=='initpyEIT':
    #         queue.put({'cmd': 'initpyEIT',
    #                     'eit_model':app.EITModel,
    #                     'plot2Gui': app.figure})
    #     return queue

def _inv_solve_eit(eit:EitBase, v1, v0, normalize:bool=False):

    if eit.solver_type in ['BP', 'JAC']:
        ds = eit.solve(v1, v0, normalize= normalize )
    elif eit.solver_type=='GREIT':
        ds = eit.solve(v1, v0, normalize= normalize)
        x, y, ds = eit.mask_value(ds, mask_value=np.NAN)
        
    return ds

def get_solver_pyeit(SolverType,MeshObj, ElecPos, ex_mat,step_solver, p:int=0.5, lamb:int=0.01, n:int=64):
    """[summary]

    Args:
        p (int, optional): [description]. Defaults to 0.5.
        lamb (int, optional): [description]. Defaults to 0.01.
        n (int, optional): [description]. Defaults to 64.
    """
    if SolverType=='BP':
        eit = bp.BP(MeshObj, ElecPos, ex_mat=ex_mat, step=1, parser="std")
        eit.setup(weight="none")         
    elif SolverType=='JAC':
        eit = jac.JAC(MeshObj, ElecPos, ex_mat=ex_mat, step=step_solver, perm=1.0, parser="std")
        eit.setup(p=p, lamb=lamb, method="kotre")
    elif SolverType=='GREIT':
        eit = greit.GREIT(MeshObj, ElecPos, ex_mat=ex_mat, step=step_solver, parser="std")
        eit.setup(p=p, lamb=lamb, n=n)
    else:
        raise NotImplementedError()
    return eit

def _reconstruct_mesh_struct(mesh_obj):
    mesh_new= mesh_obj
    pts = mesh_obj["node"]
    tri = mesh_obj["element"]
    perm= mesh_obj["perm"]

    if not "ds" in mesh_obj:
        mesh_obj["ds"]=2*np.ones_like(mesh_obj["perm"]) #

    ds= mesh_obj["ds"]
    if ds.shape[0]==tri.shape[0]:
        ds_pts= sim2pts(pts,tri,ds)
    elif ds.shape[0]==pts.shape[0]:
        ds_pts= ds
        ds= pts2sim(tri, ds_pts)
    if perm.shape[0]==tri.shape[0]:
        perm_pts= sim2pts(pts,tri,perm)
    elif perm.shape[0]==pts.shape[0]:
        perm_pts= perm
        perm= pts2sim(tri, perm_pts)

    mesh_new["perm"]= perm
    mesh_new["perm_pts"] = perm_pts
    mesh_new["ds"] = ds
    mesh_new["ds_pts"]= ds_pts

    return mesh_new


if __name__ == '__main__':
    rec= ReconstructionPyEIT()
    rec.initPyeit()
    pts = rec.MeshObj["node"]
    tri = rec.MeshObj["element"]
    mplot.tetplot(pts, tri, edge_color=(0.2, 0.2, 1.0, 1.0), alpha=0.01)
    
    pass
