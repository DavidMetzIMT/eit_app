



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


from eit_app.eit.eit_model import EITModelClass
from eit_app.eit.rec_abs import RecCMDs, Reconstruction
from glob_utils.flags.flag import CustomFlag
from logging import getLogger

logger = getLogger(__name__)
# from eit_app.io.sciospec.device import *
# from eit_app.io.sciospec.interface.serial4sciospec import 
# from eit_app.eit.meas_preprocessing import *

# from eit_ai.path_utils import get_dir
# from eit_ai.train_models import ModelGenerator
# from eit_ai.train_utils import TrainInputs
# from eit_ai.constants import TRAIN_INPUT_FILENAME
# from eit_ai.dataset import get_XY_from_MalabDataSet, dataloader, extract_samples
# from eit_ai.draw_data import format_inputs, get_elem_nodal_data
## ======================================================================================================================================================
##  Class for EIT Reconstruction
## ======================================================================================================================================================
class ReconstructionPyEIT(Reconstruction):
    """ Class for the EIT reconstruction with the package pyEIT """

    def __post_init__(self):
        self.eit:EitBase=None
        self.solver_type=''

    def initialize(self, model:EITModelClass, U:np.ndarray)-> tuple[EITModelClass,np.ndarray]:
        """ should initialize the reconstruction method and return some data to plot"""
        self.initialized.reset()
        MeshObj, ElecPos= self._construct_mesh(
                    model.get_nd_elecs(),
                    model.get_fem_refinement(),
                    model.chamber.get_chamber_limit()
                )

        ex_mat = eit_scan_lines(ne=model.get_nd_elecs(), dist=1)
        
        logger.info(f'Initialisation of PyEIT; solver:{model.SolverType}')
    
    
        """ 1. problem setup """
        anomaly = [{"x": 0.5, "y": 0.5, "d": 0.1, "perm": 10}]
        MeshObjSim = mesh.set_perm(MeshObj, anomaly=anomaly,background=1.0)
        MeshObjSim= _reconstruct_mesh_struct(MeshObjSim)

        """ 2. FEM simulation """
        # # calculate simulated data
        step_solver = 1
        fwd = Forward_all_meas(MeshObj, ElecPos)
        f0 = fwd.solve_eit(ex_mat, step=step_solver, perm=MeshObj["perm"])
        f1 = fwd.solve_eit(ex_mat, step=step_solver, perm=MeshObjSim["perm"])

        self.eit=get_solver_pyeit(
            model.SolverType,MeshObj, ElecPos, ex_mat,step_solver, model.p, model.lamb, model.n)
        # ds=_inv_solve_eit(self.eit,f1.v, f0.v, True)
        MeshObj["perm"]=_inv_solve_eit(model.SolverType,self.eit,f1.v, f0.v, True)
        model.fem.update_from_pyeit(MeshObj)
        self._print_mesh_nodes_elemts(MeshObj)
        self.initialized.set()
        return model, np.hstack((np.reshape(f1.v,(f1.v.shape[0],1)), np.reshape(f0.v,(f0.v.shape[0],1))))
        
    def reconstruct(self,  model:EITModelClass, U:np.ndarray)-> tuple[EITModelClass,np.ndarray]:
        """ return the reconstructed reconstructed conductivities values for the FEM"""
        if self.initialized.is_set():
            MeshObj=model.fem.get_pyeit_mesh()
            logger.debug(f'data send for rec \n{U=}')
            MeshObj["perm"]=_inv_solve_eit(model.SolverType,self.eit,-U[:,1],-U[:,0], False)
            model.fem.update_from_pyeit(MeshObj)
        return model, U

    def _construct_mesh(self, elec_nb, fem_refinement, bbox):
        MeshObj, ElecPos = mesh.create(n_el=elec_nb, h0=fem_refinement, bbox=bbox)
        MeshObj= _reconstruct_mesh_struct(MeshObj)
        return MeshObj, ElecPos

    def _print_mesh_nodes_elemts(self, mesh_obj):
        pts = mesh_obj["node"]
        tri = mesh_obj["element"]
        perm= mesh_obj["perm"]
        logger.info(
            f"mesh status:\n\
            {pts.shape[0]} nodes, {tri.shape[0]} elements, {perm.shape[0]} perm")
        
    # def imageReconstruct(self, v1=None, v0=None):
    #         if not self.running:
    #             if self.InitDone:
    #                 self._inv_solve_eit(U[:,1],U[:,0])
    #                 # self._plot_conductivity_map(self.MeshObjMeas, perm_ds=False)
    #                 return True
    #             else:
    #                 print('please Init the reconstruction')
    #         else:
    #             print('Reconstruction Busy')
    #             return False

    # def setScalePlot(self, vmax, vmin):
    #     if vmax==0.0 and vmin == 0.0:
    #         self.Scalevmin = None
    #         self.Scalevmax= None
    #     else:
    #         self.Scalevmin = vmin
    #         self.Scalevmax= vmax

    # def setNormalize(self, normalize):
    #     self.Normalize= normalize

    # def pollCallback(self, queue_in:Queue, queue_out:Queue):
    #     if not queue_in.empty():
    #         data=queue_in.get()
    #         if data['cmd']=='initpyEIT':
    #             self.initPyeit(eit_model=data['eit_model'], plot2Gui=data['plot2Gui'])
    #             queue_out.put({'cmd': 'updatePlot','rec': self})
    #             print(data)
    #         elif data['cmd']=='setScalePlot':  
    #             self.setScalePlot(data['vmax'], data['vmin'])
    #             self.setNormalize(data['normalize'])
    #         elif data['cmd']=='recpyEIT':
    #             self.imageReconstruct(data['v1'], data['v0'])
    #             queue_out.put({'cmd': 'updatePlot','rec': self})

    # def queue_wrapper(self, queue:Queue, cmd):

    #     if cmd=='initpyEIT':
    #         queue.put({'cmd': 'initpyEIT',
    #                     'eit_model':app.EITModel,
    #                     'plot2Gui': app.figure})
    #     return queue

def _inv_solve_eit(SolverType,eit:EitBase, v1, v0, normalize:bool=False):

    if SolverType in ['BP', 'JAC']:
        ds = eit.solve(v1, v0, normalize= normalize )
    elif SolverType=='GREIT':
        ds = eit.solve(v1, v0, normalize= normalize)
        x, y, ds = eit.mask_value(ds, mask_value=np.NAN)
        
    return ds

def get_solver_pyeit(
    SolverType,
    MeshObj,
    ElecPos,
    ex_mat,
    step_solver,
    p:int=0.5,
    lamb:int=0.01,
    n:int=64):
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

    if "ds" not in mesh_obj:
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


class Forward_all_meas(Forward):
    def __init__(self, mesh, el_pos):
        super().__init__(mesh, el_pos)

    def voltage_meter(ex_line, n_el=16, step=1, parser=None):
        """
        extract subtract_row-voltage measurements on boundary electrodes.
        we direct operate on measurements or Jacobian on electrodes,
        so, we can use LOCAL index in this module, do not require el_pos.

        Notes
        -----
        ABMN Model.
        A: current driving electrode,
        B: current sink,
        M, N: boundary electrodes, where v_diff = v_n - v_m.

        'no_meas_current': (EIDORS3D)
        mesurements on current carrying electrodes are discarded.

        Parameters
        ----------
        ex_line: NDArray
            2x1 array, [positive electrode, negative electrode].
        n_el: int
            number of total electrodes.
        step: int
            measurement method (two adjacent electrodes are used for measuring).
        parser: str
            if parser is 'fmmu', or 'rotate_meas' then data are trimmed,
            boundary voltage measurements are re-indexed and rotated,
            start from the positive stimulus electrodestart index 'A'.
            if parser is 'std', or 'no_rotate_meas' then data are trimmed,
            the start index (i) of boundary voltage measurements is always 0.

        Returns
        -------
        v: NDArray
            (N-1)*2 arrays of subtract_row pairs
        """
        # local node
        drv_a = ex_line[0]
        drv_b = ex_line[1]
        i0 = drv_a if parser in ("fmmu", "rotate_meas") else 0

        # build differential pairs
        v = []
        for a in range(i0, i0 + n_el):
            m = a % n_el
            n = (m + step) % n_el
            # if any of the electrodes is the stimulation electrodes
            # if not (m == drv_a or m == drv_b or n == drv_a or n == drv_b) or True:
                # the order of m, n matters
            v.append([n, m])

        return np.array(v)
    


if __name__ == '__main__':
    rec= ReconstructionPyEIT()
    rec.initPyeit()
    pts = rec.MeshObj["node"]
    tri = rec.MeshObj["element"]
    mplot.tetplot(pts, tri, edge_color=(0.2, 0.2, 1.0, 1.0), alpha=0.01)

