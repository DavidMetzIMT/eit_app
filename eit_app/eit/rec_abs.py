



from abc import ABC, abstractmethod
import os
from multiprocessing.queues import Queue

from enum import Enum, auto

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
from glob_utils.flags.flag import CustomFlag
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

# RECONSTRUCTION_EIT={
#     'pyeit':
#     'ai':
# }


class RecCMDs(Enum):
    initialize=auto()
    reconstruct=auto()

class Reconstruction(ABC):
    """ Class for the EIT reconstruction """
    
    def __init__(self):
        self.initialized=CustomFlag()
        self.cmd_func= {
            RecCMDs.initialize:self.initialize,
            RecCMDs.reconstruct:self.reconstruct
        }
        self.__post_init__()

    def run(self, cmd:RecCMDs=None, *args, **kwargs):
        if cmd is None:
            return None
        return self.cmd_func[cmd](*args, **kwargs)

    @abstractmethod
    def __post_init__(self)-> None:
        """ for init"""

    @abstractmethod
    def initialize(self, model:EITModelClass, U:np.ndarray)-> tuple[EITModelClass,np.ndarray] :
        """ should initialize the reconstruction method and return some data to plot"""
        self.initialized.reset()
        self.initialized.set()
        
    @abstractmethod
    def reconstruct(self, model:EITModelClass, U:np.ndarray)-> tuple[EITModelClass,np.ndarray] :
        """ return the reconstructed reconstructed conductivities values for the FEM"""
        if self.initialized.is_set():
            """ DO SOMETTHING and return data of reconstruction"""


if __name__ == '__main__':

    pass
