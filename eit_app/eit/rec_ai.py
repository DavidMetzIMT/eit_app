



import os
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
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

from eit_app.eit.model import EITModelClass
# from eit_app.io.sciospec.device import *
# from eit_app.io.sciospec.interface.serial4sciospec import 
from eit_app.eit.meas_preprocessing import *

from eit_tf_workspace.path_utils import get_dir
from eit_tf_workspace.train_models import ModelGenerator
from eit_tf_workspace.train_utils import TrainInputs
from eit_tf_workspace.constants import TRAIN_INPUT_FILENAME
from eit_tf_workspace.dataset import get_XY_from_MalabDataSet, dataloader, extract_samples, scale_prepocess
from eit_tf_workspace.draw_data import format_inputs, get_elem_nodal_data

from eit_app.eit.rec_abs import Reconstruction

os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
from eit_app.utils.log import main_log
from logging import getLogger

logger = getLogger(__name__)
## ======================================================================================================================================================
##  Class for EIT Reconstruction
## ======================================================================================================================================================
class ReconstructionAI(Reconstruction):
    """ Class for the EIT reconstruction with the package pyEIT """
    def __post_init__(self):
        
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

    def __post_init__(self):



        
        """ for init"""

    def initialize(self, model:EITModelClass, U:np.ndarray, model_dirpath=None):
        """ should initialize the reconstruction method and return some data to plot"""
        self.initialized.reset()
        verbose= True
        # # stimulation/excitation
        # self.EitModel= eit_model
        # self.plot2Gui=plot2Gui
        # self.FEMRefinement = eit_model.FEMRefinement
        # el_dist= 1 # ad: 1  op: 8    for ElecNb=16
        # self.ex_mat = eit_scan_lines(16, el_dist)
        if model_dirpath:
            path_dir= model_dirpath
        else:
            path_dir=get_dir(title='Select directory of model to evaluate')
            if not path_dir:
                return
        training_settings=TrainInputs()
        training_settings.read(os.path.join(path_dir,TRAIN_INPUT_FILENAME))
        #here pb with linux/win tranfers
        path_pkl=training_settings.dataset_src_file_pkl[1]
        data_sel= training_settings.data_select
        training_settings.use_tf_dataset=False
        # Data loading
        try:
            raw_data=get_XY_from_MalabDataSet(path=path_pkl, data_sel= data_sel,verbose=verbose)#, type2load='.pkl')
        except BaseException as e:
            logger.error(f'file : {path_pkl} - not loaded ({e})')
            raw_data=get_XY_from_MalabDataSet(path='', data_sel= data_sel,verbose=verbose)#, type2load='.pkl')

        eval_dataset = dataloader(raw_data, use_tf_dataset=False,verbose=verbose, train_inputs=training_settings)
        training_settings.set_dataset_src_file(eval_dataset)
        training_settings.save()

        voltages, perm_real=extract_samples(eval_dataset, dataset_part='test', idx_samples=0, elem_idx = 1)
        self.shape_v = voltages.shape
        # print('\nperm_real',perm_real, perm_real.shape)
        # print(self.MeshObj, type(self.MeshObj))
        self.fwd_model= eval_dataset.fwd_model
        # Load model
        self.gen = ModelGenerator()
        self.train_inputs= training_settings
        try: 
            self.gen.load_model(self.train_inputs.model_saving_path)
            print(voltages, voltages.shape)
            perm_real=self.gen.mk_prediction(voltages)

            perm=format_inputs(self.fwd_model, perm_real)
            tri, pts, data= get_elem_nodal_data(self.fwd_model, perm)
            
            # self.MeshObj= self._reconstruct_mesh_struct(self.MeshObj)
            model.fem.set_mesh(pts, tri, data['elems_data'])
            self.initialized.set()
        except:
            print(f'{training_settings.model_saving_path} : model not loaded')
        return model, np.hstack((np.reshape(voltages,(-1,1)), np.reshape(voltages,(-1,1))))

        
    def reconstruct(self, model:EITModelClass, U:np.ndarray):
        """ return the reconstructed reconstructed conductivities values for the FEM"""
        if self.initialized.is_set():
            """ DO SOMETTHING and return data of reconstruction"""
            d= U[:,1]-U[:,0]
            # print(d, d.shape)
            d= np.reshape(d,self.shape_v).T
            # print(d, d.shape)
            ds= scale_prepocess(d, True).T#self.train_inputs.normalize[0])
            # print(ds, ds.shape)
            perm_NN=self.gen.mk_prediction(ds)
            # print(perm_NN)
            perm=format_inputs(self.fwd_model, perm_NN)
            tri, pts, data= get_elem_nodal_data(self.fwd_model, perm)
            model.fem.set_mesh(pts, tri, data['elems_data'])
        return model, U

    
if __name__ == '__main__':
    import random
    v=np.array([random.sample(range((1+i)*1000,(2+i)*1000), 256) for i in range(2)])/1000
    print(v, v.shape)
    main_log()
    
    rec= ReconstructionAI()
    model= EITModelClass()
    rec.initialize(model,[])

    rec.reconstruct(model, v.T)

