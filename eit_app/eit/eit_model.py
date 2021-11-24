

from dataclasses import dataclass
from enum import Enum, auto
from typing import List
import numpy as np
import os
from numpy.core.shape_base import hstack
from numpy.lib.arraysetops import ediff1d
from numpy.lib.polynomial import RankWarning

from eit_app.utils.constants import DEFAULT_DIR, \
                                    DEFAULT_MEASUREMENTS,\
                                    DEFAULT_INJECTIONS,\
                                    DEFAULT_ELECTRODES_CHIP_RING

from eit_tf_workspace.draw_data import format_inputs, get_elem_nodal_data

## ======================================================================================================================================================
##  
## ======================================================================================================================================================
class BodyTypes(Enum):
    circle_2D=auto()
    cylinder_3D=auto()
    rectangle_2D=auto()
    cubic_3D=auto()


class ElectrodePatternTypes(Enum):
    ring=auto()
    grid=auto()
    polka_dot=auto()

class EletrodeFormtypes(Enum):
    circular=auto()
    rectangle=auto()
    
@dataclass
class EITBox():
    """ define the overall dimensions of the chamber"""
    length:float=2.0 # on x axis
    width:float=2.0 # on y axis
    height:float=0.0 # on z axis (0.0 for 2D models)

@dataclass
class EITBody():
    box:EITBox=EITBox()
    type:BodyTypes=BodyTypes.circle_2D
@dataclass
class ElectrodeForm():
    type:EletrodeFormtypes=EletrodeFormtypes.circular
    size:np.ndarray=np.array([0.1, 0]) # diameter/lenght, width
    
@dataclass
class EITElectrodeConfig():
    type:ElectrodePatternTypes=ElectrodePatternTypes.ring
    number:int=16
    position:int='Wall'
    form:ElectrodeForm=ElectrodeForm()

@dataclass
class EITChamber():
    name:str=''
    body:EITBody=EITBody()
    electrodes_config:EITElectrodeConfig=EITElectrodeConfig()

    def get_chamber_limit(self):
        x=self.body.box.length/2
        y=self.body.box.width/2
        z=self.body.box.height/2
        return [[-x,-y,-z],[x,y,z]] if z else [[-x,-y],[x,y]]


@dataclass
class FEM():
    nodes:np.ndarray=None
    elems:np.ndarray=None
    elems_data:np.ndarray=None
    boundaries:np.ndarray=None
    gnd_node:int=0
    refinement:float=0.1

    def set_perm(self, perm:np.ndarray) -> None:

        if perm.ndim==2:
            data_s1= perm.shape[1]
            nodes_s0=self.nodes.shape[0]
            elems_s0=self.elems.shape[0]
            if data_s1 in [nodes_s0, elems_s0]:
                perm= perm.T
        self.elems_data= perm
    
    def set_mesh(self,pts,tri,perm):
        self.nodes= pts
        self.elems= tri
        self.set_perm(perm)

    def build_mesh_from_matlab(self, fwd_model:dict, perm:np.ndarray):
        perm=format_inputs(fwd_model, perm)
        tri, pts, data= get_elem_nodal_data(fwd_model, perm)
        # model.fem.set_mesh(pts, tri, data['elems_data'])
        self.set_mesh(pts, tri, data['elems_data'])
        # self.nodes= fwd_model['nodes']
        # self.elems= fwd_model['elems']
        # self.set_perm(perm)

    def get_pyeit_mesh(self):
        return {
            'node':self.nodes,
            'element':self.elems,
            'perm':self.elems_data,
        }

    def update_from_pyeit(self, mesh_obj:dict):
        self.nodes= mesh_obj['node']
        self.elems= mesh_obj['element']
        self.set_perm(mesh_obj['perm'])
    
    def get_data_for_plots(self):
        return self.nodes, self.elems, self.elems_data


class Stimulations():
    stim_type:str='Amperes'
    stim_pattern:np.ndarray=None
    meas_pattern:np.ndarray=None

class Electrodes():
    nodes:np.ndarray=None # 1D array
    z_contact:float=None
    position:np.ndarray=None #1Darray x,y,z,nx,ny,nz
    shape:float=None #????
    obj: str=None # to which it belongs



class EITModelClass(object):
    """ Class regrouping all information about the virtual model 
    of the measuremnet chamber used for the reconstruction:
    - chamber
    - mesh
    - 
    """
    def __init__(self):
        self.Name = 'EITModel_defaultName'
        self.InjPattern = [[0,0], [0,0]]
        self.Amplitude= float(1)
        self.meas_pattern=[[0,0], [0,0]]
        self.n_el=16
        self.p=0.5
        self.lamb=0.01
        self.n=64

        pattern='ad'
        path= os.path.join(DEFAULT_DIR,DEFAULT_INJECTIONS[pattern])
        self.InjPattern=np.loadtxt(path, dtype=int)
        # print(type(self.InjPattern))
        path= os.path.join(DEFAULT_DIR,DEFAULT_MEASUREMENTS[pattern])
        self.meas_pattern=np.loadtxt(path)
        # print(type(self.MeasPattern))
        # print(self.MeasPattern)
        self.SolverType= 'none'
        self.FEMRefinement=0.1
        self.translate_inj_pattern_4_chip()

        self.chamber:EITChamber=EITChamber()
        self.fem:FEM=FEM()
        self.stimulations:List[Stimulations]=[Stimulations()]

    
    def set_solver(self, solver_type):
        self.SolverType= solver_type

    def translate_inj_pattern_4_chip(self, path=None):
        if path:
            self.ChipPins=np.loadtxt(path)
        else:
            path= os.path.join(DEFAULT_DIR,DEFAULT_ELECTRODES_CHIP_RING)
            self.ChipPins=np.loadtxt(path)
        
        # test if load data are compatible...
        #todo..
        
        o_num=self.ChipPins[:,0] # Channel number
        n_num=self.ChipPins[:,1] # corresonpint chip pads
        new=np.array(self.InjPattern)
        old=np.array(self.InjPattern)
        for n in range(o_num.size):
            new[old==o_num[n]]= n_num[n]
            
        self.InjPattern= new # to list???
        
    def get_fem_refinement(self):
        return self.fem.refinement
    def get_nd_elecs(self, all:bool=True):
        return self.chamber.electrodes_config.number 




if __name__ == '__main__':
    eit= EITModelClass()
    
    pass
