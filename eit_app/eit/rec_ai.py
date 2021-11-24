

import os
from eit_tf_workspace.train_utils.gen import Generators
from eit_tf_workspace.train_utils.metadata import MetaData, reload_metadata
import numpy as np
import pyeit.mesh as mesh
# from eit_app.io.sciospec.device import *
# from eit_app.io.sciospec.interface.serial4sciospec import 
from eit_app.eit.meas_preprocessing import *
from eit_app.eit.eit_model import EITModelClass
from eit_app.eit.rec_abs import Reconstruction
from eit_tf_workspace.raw_data.matlab import MatlabSamples
from eit_tf_workspace.raw_data.raw_samples import reload_samples
from eit_tf_workspace.train_utils.select_gen import select_gen

os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
from logging import getLogger
from eit_app.utils.log import main_log

logger = getLogger(__name__)
## ======================================================================================================================================================
##  Class for EIT Reconstruction
## ======================================================================================================================================================
class ReconstructionAI(Reconstruction):
    """ Class for the EIT reconstruction with the package pyEIT """
    def __post_init__(self):
        
        # self.EitModel = EITModelClass()
        # self.MeshObj,self.ElecPos = mesh.create(16, h0=0.1)
        # self.ElecNb = 16
        # self.ElecPos = []
        # self.FEMRefinement = 0.1
        # self.ChamberLimit = [[-1, -1], [1, 1]]
        # self.plot2Gui = False
        # self.ax = ''
        # self.verbose=0
        # self.Normalize= False
        # self.Scalevmin = None
        # self.Scalevmax= None
        # self.InitDone=False
        # self.running= False
        # self.eit=None

        self.metadata:MetaData=None
        self.gen:Generators=None
        self.fwd_model:dict=None


    def initialize(self, model:EITModelClass, U:np.ndarray, model_dirpath:str=''):
        """ should initialize the reconstruction method and return some data to plot"""
        self.initialized.reset()

        self.metadata = reload_metadata(dir_path=model_dirpath)
        raw_samples= reload_samples(MatlabSamples(),self.metadata)
        self.gen= select_gen(self.metadata)
        self.gen.load_model(self.metadata)
        self.gen.build_dataset(raw_samples, self.metadata)

        self.fwd_model=self.gen.getattr_dataset('fwd_model')
        voltages, true_img_data=self.gen.extract_samples(dataset_part='test', idx_samples='all')

        perm_real=self.gen.get_prediction(metadata=self.metadata,single_X=voltages[2])
        model.fem.build_mesh_from_matlab(self.fwd_model, perm_real)
        self.initialized.set()

        return model, np.hstack((np.reshape(voltages,(-1,1)), np.reshape(voltages,(-1,1))))

        
    def reconstruct(self, model:EITModelClass, U:np.ndarray):
        """ return the reconstructed reconstructed conductivities values for the FEM"""
        if self.initialized.is_set():
            """ DO SOMETTHING and return data of reconstruction"""
            d= U[:,1]-U[:,0]
            perm_real=self.gen.get_prediction(metadata=self.metadata, single_X=d)
            model.fem.build_mesh_from_matlab(self.fwd_model, perm_real)
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

