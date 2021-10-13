


import numpy as np
import os
from numpy.core.shape_base import hstack
from numpy.lib.arraysetops import ediff1d

import utils.constants as const
## ======================================================================================================================================================
##  
## ======================================================================================================================================================

class EITModelClass(object):
    ''' DeviceSetupClass regroup all Device relevant info, parameters
    '''
    def __init__(self):
        self.Name = 'EITModel_defaultName'
        self.InjPattern = [[0,0], [0,0]]
        self.Amplitude= float(1)
        self.MeasPattern=[[0,0], [0,0]]
        self.n_el=16
        self.p=0.5
        self.lamb=0.01
        self.n=64

        pattern='ad'
        path= os.path.join(const.DEFAULT_DIR,const.DEFAULT_INJECTIONS[pattern])
        self.InjPattern=np.loadtxt(path, dtype=int)
        # print(type(self.InjPattern))
        path= os.path.join(const.DEFAULT_DIR,const.DEFAULT_MEASUREMENTS[pattern])
        self.MeasPattern=np.loadtxt(path)
        # print(type(self.MeasPattern))
        # print(self.MeasPattern)
        self.SolverType= 'none'
        self.FEMRefinement=0.1
        self.translate_inj_pattern_4_chip()

    
    def set_solver(self, solver_type):
        self.SolverType= solver_type

    def translate_inj_pattern_4_chip(self, path=None):
        if path:
            self.ChipPins=np.loadtxt(path)
        else:
            path= os.path.join(const.DEFAULT_DIR,const.DEFAULT_ELECTRODES_CHIP_RING)
            self.ChipPins=np.loadtxt(path)
        
        # test if load data are compatible...
        #todo..
        
        o_num=self.ChipPins[:,0] # Channel number
        n_num=self.ChipPins[:,1] # corresonpint chip pads
        new=np.array(self.InjPattern)
        old=np.array(self.InjPattern)
        for n in range(o_num.size):
            new[old==o_num[n]]= n_num[n]
            
        self.InjPattern= new
        
    



if __name__ == '__main__':
    eit= EITModelClass()
    
    pass
