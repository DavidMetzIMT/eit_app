



import os
from multiprocessing.queues import Queue



import matplotlib.pyplot as plt
import numpy as np

import pyeit.eit.bp as bp
import pyeit.eit.greit as greit
import pyeit.eit.jac as jac
import pyeit.mesh as mesh
import pyeit.mesh.plot as mplot

from pyeit.eit.fem import Forward
from pyeit.eit.interp2d import pts2sim, sim2pts
from pyeit.eit.utils import eit_scan_lines

from eit_app.eit.eit_model import EITModelClass
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
class ReconstructionPyEIT_old():
    """ Class for the EIT reconstruction with the package pyEIT """
    def __init__(self):
        self.EitModel = EITModelClass()
        self.MeshObj,self.ElecPos = mesh.create(16, h0=0.1)
        self.ElecNb = 16
        self.ElecPos = []
        self.FEMRefinement = 0.1
        self.ChamberLimit = [[-1, -1], [1, 1]]
        self.plot2Gui = False
        self.ax = ''
        self.verbose=0
        self.Normalize= False
        self.Scalevmin = None
        self.Scalevmax= None
        self.InitDone=False
        self.running= False
        self.eit=None
        pass

    def initPyeit(self, eit_model:EITModelClass, plot2Gui:bool=False, verbose:int=0):
        
        self.InitDone=False
        self.verbose=verbose
        # stimulation/excitation
        self.EitModel= eit_model
        self.plot2Gui=plot2Gui
        self.FEMRefinement = eit_model.FEMRefinement
        el_dist= 1 # ad: 1  op: 8    for ElecNb=16
        self.ex_mat = eit_scan_lines(16, el_dist)
        
        if  self.EitModel.SolverType=='NN':
            print('Initialisation of Reccontruction with NN')
            
            # title= 'Select directory of model to evaluate'
            # path_dir=get_dir(title=title)
            # if not path_dir:
            #     return
            # # read train inputs instead
            # training_settings=TrainInputs()
            # training_settings.read(os.path.join(path_dir,TRAIN_INPUT_FILENAME))
            # #here pb with linux/win tranfers
            # path_pkl=training_settings.dataset_src_file[1]
            # data_sel= training_settings.data_select
            # # Data loading
            # raw_data=get_XY_from_MalabDataSet(path=path_pkl, data_sel= data_sel,verbose=verbose)#, type2load='.pkl')
            # eval_dataset = dataloader(raw_data, use_tf_dataset=True,verbose=verbose, train_inputs=training_settings)
            
            # # if verbose:
            # #     print(eval_dataset.use_tf_dataset)
            # #     if eval_dataset.use_tf_dataset:
            # #         # extract data for verification?
            # #         for inputs, outputs in eval_dataset.test.as_numpy_iterator():
            # #             print('samples size:',inputs.shape, outputs.shape)
            # #             # Print the first element and the label
            # #             # print(inputs[0])
            # #             # print('label of this input is', outputs[0])
            # #             if eval_dataset.batch_size:
            # #                 plot_EIT_samples(eval_dataset.fwd_model, outputs[0], inputs[0])
            # #             else:
            # #                 plot_EIT_samples(eval_dataset.fwd_model, outputs, inputs)
            # #             break
            
            # # _, perm_real=extract_samples(eval_dataset, dataset_part='test', idx_samples='all', elem_idx = 1)
            # _, perm_real=extract_samples(eval_dataset, dataset_part='test', idx_samples=0, elem_idx = 1)

            # print('\nperm_real',perm_real, perm_real.shape)
            # # print(self.MeshObj, type(self.MeshObj))

            # # Load model
            # gen = ModelGenerator()
            # try: 
            #     gen.load_model(training_settings.model_saving_path)
            #     self.InitDone=True

            #     perm=format_inputs(eval_dataset.fwd_model, perm_real)
            #     tri, pts, data= get_elem_nodal_data(eval_dataset.fwd_model, perm)
                
            #     # self.MeshObj= self._reconstruct_mesh_struct(self.MeshObj)
            #     self.MeshObj["node"]=pts
            #     self.MeshObj["element"]= tri
            #     self.MeshObj["perm"] = data['elems_data']
            #     self.MeshObj["ds"]=data['elems_data']
            #     self.MeshObj= self._reconstruct_mesh_struct(self.MeshObj)
            #     self.MeshObjMeas = self.MeshObj

            # except:
            #     print(f'{training_settings.model_saving_path} : model not loaded')
            
        else:
            print('Initialisation of PyEIT')
            # coding: utf-8
            """ demo on dynamic eit using JAC method """
            # Copyright (c) Benyuan Liu. All Rights Reserved.
            # Distributed under the (new) BSD License. See LICENSE.txt for more info.
            

            # TODO here init the varaible to create the mesh and the solver

            # or from self.EitModel.....
            # print(self.ex_mat)
            self._construct_mesh(self.ElecNb, self.FEMRefinement, self.ChamberLimit)
            if verbose>0:
                self._print_mesh_nodes_elemts(self.MeshObj)
                self._plot_mesh()
                self._plot_conductivity_map(self.MeshObj)
        
            """ 1. problem setup """
            anomaly = [{"x": 0.5, "y": 0.5, "d": 0.1, "perm": 2}]
            self.MeshObjSim = mesh.set_perm(self.MeshObj, anomaly=anomaly,background=0.01)
            self.MeshObjSim= self._reconstruct_mesh_struct(self.MeshObjSim)
            if verbose>0:
                self._print_mesh_nodes_elemts(self.MeshObjSim)
                self._plot_conductivity_map(self.MeshObjSim)

            """ 2. FEM simulation """
            # # calculate simulated data
            self.step_solver = 1
            fwd = Forward(self.MeshObj, self.ElecPos)
            f0 = fwd.solve_eit(self.ex_mat, step=self.step_solver, perm=self.MeshObj["perm"])
            f1 = fwd.solve_eit(self.ex_mat, step=self.step_solver, perm=self.MeshObjSim["perm"])

            self.setEit(self.EitModel.p,self.EitModel.lamb,self.EitModel.n)
            self._inv_solve_eit(f1.v, f0.v)
            self._print_mesh_nodes_elemts(self.MeshObjMeas)
            # self._plot_conductivity_map(self.MeshObjMeas, perm_ds=False)
            # self._plot_conductivity_map(self.MeshObjMeas, perm_ds=False)
            self.InitDone=True

    def setEit(self, p:int=0.5, lamb:int=0.01, n:int=64):
        """[summary]

        Args:
            p (int, optional): [description]. Defaults to 0.5.
            lamb (int, optional): [description]. Defaults to 0.01.
            n (int, optional): [description]. Defaults to 64.
        """
        if self.EitModel.SolverType=='BP':
            eit = bp.BP(self.MeshObj, self.ElecPos, ex_mat=self.ex_mat, step=1, parser="std")
            eit.setup(weight="none")         
        elif self.EitModel.SolverType=='JAC':
            eit = jac.JAC(self.MeshObj, self.ElecPos, ex_mat=self.ex_mat, step=self.step_solver, perm=1.0, parser="std")
            eit.setup(p=p, lamb=lamb, method="kotre")
        elif self.EitModel.SolverType=='GREIT':
            eit = greit.GREIT(self.MeshObj, self.ElecPos, ex_mat=self.ex_mat, step=self.step_solver, parser="std")
            eit.setup(p=p, lamb=lamb, n=n)
        elif  self.EitModel.SolverType=='NN':
            
            pass
        else:
            eit = bp.BP(self.MeshObj, self.ElecPos, ex_mat=self.ex_mat, step=1, parser="std")
            eit.setup(weight="none") 
            self.EitModel.SolverType='BP'
        self.eit= eit

    def _inv_solve_eit(self, v1, v0):
        self.MeshObjMeas = self.MeshObj
        self.running= True
        if self.EitModel.SolverType=='BP' or self.EitModel.SolverType=='JAC':
            self.MeshObjMeas['ds'] = self.eit.solve(v1, v0, normalize=self.Normalize )
        elif  self.EitModel.SolverType=='NN':

            pass   
        elif self.EitModel.SolverType=='GREIT':
            ds = self.eit.solve(v1, v0, normalize=self.Normalize)
            x, y, self.MeshObjMeas["ds_greit"] = self.eit.mask_value(ds, mask_value=np.NAN)
        self.MeshObjMeas= self._reconstruct_mesh_struct(self.MeshObjMeas)
        self.running= False

    def _construct_mesh(self, elec_nb, fem_refinement, bbox):
        self.MeshObj, self.ElecPos = mesh.create(n_el=elec_nb, h0=fem_refinement, bbox=bbox)
        self.MeshObj= self._reconstruct_mesh_struct(self.MeshObj)
        
    def _plot_mesh(self):
        """ plot the mesh with electrode """
        if self.plot2Gui==False:
            pts = self.MeshObj["node"]
            tri = self.MeshObj["element"]

            bbox= np.array(self.ChamberLimit)
            if bbox.shape[1] ==2 : # 2D plot 
                fig, ax = plt.subplots()
                ax.triplot(pts[:, 0], pts[:, 1], tri)
                ax.plot(pts[self.ElecPos, 0], pts[self.ElecPos, 1], "ro")
                ax.set_aspect("equal")
                plt.show()
            else: # 3D plot
                mplot.tetplot(pts, tri, edge_color=(0.2, 0.2, 1.0, 1.0), alpha=0.01)

    def _reconstruct_mesh_struct(self, mesh_obj):
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
    
    def _plot_conductivity_map(self, mesh_obj, perm_ds=True):
        self._print_mesh_nodes_elemts(mesh_obj)
        pts = mesh_obj["node"]
        tri = mesh_obj["element"]
        perm= mesh_obj["perm"]
        ds= mesh_obj["ds"]

        if self.plot2Gui==False  or True:
            fig, ax = plt.subplots()

            if perm_ds:
                im = ax.tripcolor(pts[:,0], pts[:,1], tri, np.real(perm), shading="flat")
            else:
                if self.eit.solver_type=='GREIT':
                    ds = mesh_obj["ds_greit"]
                    im = ax.imshow(np.real(ds), interpolation="none", origin='lower', vmin=self.Scalevmin, vmax=self.Scalevmax)
                else:
                    im = ax.tripcolor(pts[:,0], pts[:,1], tri, np.real(ds), shading="flat", vmin=self.Scalevmin, vmax=self.Scalevmax)
                
            for i, e in enumerate(self.ElecPos):
                ax.annotate(str(i + 1), xy=(pts[e,0], pts[e,1]), color="r")   
            ax.axis("equal")
            fig.colorbar(im)
            plt.show()
        else:
            fig= self.plot2Gui
            fig.clear()
            
            self.ax = fig.add_subplot(3,1,(1,2))

            if perm_ds:
                im = self.ax.tripcolor(pts[:,0], pts[:,1], tri, np.real(perm), shading="flat")
            else:
                if self.eit.solver_type=='GREIT':
                    ds = mesh_obj["ds_greit"]
                    im = self.ax.imshow(np.real(ds), interpolation="none", origin='lower', vmin=self.Scalevmin, vmax=self.Scalevmax)
                else:
                    im = self.ax.tripcolor(pts[:,0], pts[:,1], tri, np.real(ds), shading="flat", vmin=self.Scalevmin, vmax=self.Scalevmax)
                
            for i, e in enumerate(self.ElecPos):
                self.ax.annotate(str(i + 1), xy=(pts[e,0], pts[e,1]), color="r")   
            self.ax.axis("equal")
            self.ax.set_title('Reconstruction')
            fig.colorbar(im)
        self.plot2Gui= fig
            

    def _print_mesh_nodes_elemts(self, mesh_obj):
        if self.plot2Gui==False:
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
                    self._inv_solve_eit(v1, v0)
                    # self._plot_conductivity_map(self.MeshObjMeas, perm_ds=False)
                    return True
                else:
                    print('please Init the reconstruction')
            else:
                print('Reconstruction Busy')
                return False

    def setScalePlot(self, vmax, vmin):
        if vmax==0.0 and vmin == 0.0:
            self.Scalevmin = None
            self.Scalevmax= None
        else:
            self.Scalevmin = vmin
            self.Scalevmax= vmax

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
        # pass
    # def queue_wrapper(self, queue:Queue, cmd):

    #     if cmd=='initpyEIT':
    #         queue.put({'cmd': 'initpyEIT',
    #                     'eit_model':app.EITModel,
    #                     'plot2Gui': app.figure})
    #     return queue



if __name__ == '__main__':
    rec= ReconstructionPyEIT()
    rec.initPyeit()
    pts = rec.MeshObj["node"]
    tri = rec.MeshObj["element"]
    mplot.tetplot(pts, tri, edge_color=(0.2, 0.2, 1.0, 1.0), alpha=0.01)
    
    pass
