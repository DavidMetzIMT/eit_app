

import os
from eit_tf_workspace.train_utils.gen import Generators
from eit_tf_workspace.train_utils.metadata import MetaData, reload_metadata
from eit_app.eit.eit_model import EITModelClass
from eit_app.eit.rec_abs import Reconstruction
from eit_tf_workspace.raw_data.matlab import MatlabSamples
from eit_tf_workspace.raw_data.raw_samples import reload_samples
from eit_tf_workspace.train_utils.select_gen import select_gen
import numpy as np

from logging import getLogger


logger = getLogger(__name__)
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
################################################################################
# Class for EIT Reconstruction
################################################################################
class ReconstructionAI(Reconstruction):
    """ Class for the EIT reconstruction with the package pyEIT """
    def __post_init__(self):
        self.metadata:MetaData=None
        self.gen:Generators=None
        self.fwd_model:dict=None

    def initialize(
        self,
        model:EITModelClass,
        U:np.ndarray,
        model_dirpath:str='') -> tuple[EITModelClass,np.ndarray] :
        """ should initialize the reconstruction method and return some data to plot"""
        self.initialized.reset()
        self.metadata = reload_metadata(dir_path=model_dirpath)
        self.gen= select_gen(self.metadata)
        self.gen.load_model(self.metadata)
        raw_samples= reload_samples(MatlabSamples(),self.metadata)
        self.gen.build_dataset(raw_samples, self.metadata)
        self.fwd_model=self.gen.getattr_dataset('fwd_model')
        voltages, _=self.gen.extract_samples(dataset_part='test', idx_samples='all')
        perm_real=self.gen.get_prediction(metadata=self.metadata,single_X=voltages[2])
        model.fem.build_mesh_from_matlab(self.fwd_model, perm_real)
        self.initialized.set()
        return model, np.hstack((np.reshape(voltages,(-1,1)), np.reshape(voltages,(-1,1))))

    def reconstruct(
        self,
        model:EITModelClass, 
        U:np.ndarray)-> tuple[EITModelClass,np.ndarray] :
        """ return the reconstructed reconstructed conductivities values for the FEM"""
        if self.initialized.is_set():
            ds= U[:,1]-U[:,0]
            perm_real=self.gen.get_prediction(metadata=self.metadata, single_X=ds)
            model.fem.build_mesh_from_matlab(self.fwd_model, perm_real)
        return model, U
    

    
if __name__ == '__main__':
    import random
    from glob_utils.log.log import main_log
    v=np.array([random.sample(range((1+i)*1000,(2+i)*1000), 256) for i in range(2)])/1000
    print(v, v.shape)
    main_log()
    rec= ReconstructionAI()
    model= EITModelClass()
    rec.initialize(model,[])
    rec.reconstruct(model, v.T)

