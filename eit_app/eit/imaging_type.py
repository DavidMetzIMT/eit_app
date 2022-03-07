


from abc import ABC
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, List
import numpy as np
from eit_app.eit.plots import PlotType
from eit_app.io.sciospec.device import EitMeasurementSet
from glob_utils.unit.unit import eng
from eit_app.eit.eit_model import EITModelClass



def identity(x:np.ndarray)-> np.ndarray:
    """_summary_

    Args:
        x (np.ndarray): _description_

    Returns:
        np.ndarray: _description_
    """
    return x

DATA_TRANSFORMATIONS={
    'Real':np.real,
    'Image':np.imag,
    'Magnitude':np.abs,
    'Phase':np.angle,
    'Abs':np.abs,
    'Identity':identity
    }

def make_voltage_vector(eit_model:EITModelClass,transform_funcs:list, voltages:np.ndarray)-> np.ndarray:
    """_summary_

    Args:
        eit_model (EITModelClass): _description_
        transform_funcs (list): _description_
        voltages (np.ndarray): _description_

    Returns:
        np.ndarray: _description_
    """
    tmp= make_voltage_from_meas_pattern(eit_model, voltages)
    return transform_data(tmp, transform_funcs)

def transform_data(x:np.ndarray, transform_funcs:list)-> np.ndarray:
    """_summary_

    Args:
        x (np.ndarray): _description_
        transform_funcs (list): _description_

    Raises:
        Exception: _description_

    Returns:
        np.ndarray: _description_
    """
    if len(transform_funcs)!=2:
        raise Exception()
    
    for func in transform_funcs:
        if func is not None:
            x=func(x)
    x= np.reshape(x,(x.shape[0],1))
    return x

def make_voltage_from_meas_pattern(eit_model:EITModelClass, voltages:np.ndarray)->np.ndarray:
    """_summary_

    Args:
        eit_model (EITModelClass): _description_
        voltages (np.ndarray): _description_

    Returns:
        np.ndarray: _description_
    """
    meas_voltage=voltages[:,:eit_model.n_el] # get only the voltages of used electrode (0-n_el)
    return eit_model.meas_pattern.dot(meas_voltage.T).flatten() #get the volgate corresponding to the meas_pattern and flatten


class Imaging(ABC):
    idx_freqs=[None, None]
    ref_frame_idx=None
    transform_funcs=[identity, identity]
    label_imaging:str=''
    freqs_val=None
    idx_frames= None
    label_meas= None

    def __init__(self) -> None:
        super().__init__()

    def process_data(self,dataset:EitMeasurementSet, eit_model:EITModelClass, idx_frame:int=0,extract_voltages:bool=False):
        
        self.idx_freqs= [list(item.values())[0] for item in self.detail_freqs if item is not None]
        self.idx_freqs.reverse()

        meas_voltages=self.pre_process_data(dataset, eit_model, idx_frame)
        self.get_metadata(dataset, idx_frame)
        labels= self.make_labels()
        return meas_voltages, labels

    @abstractmethod
    def pre_process_data(self, dataset:EitMeasurementSet, eit_model:EITModelClass, idx_frame:int=0)->List[np.ndarray]:
        """"""
        # return meas_voltage

    def get_metadata(self, dataset:EitMeasurementSet, idx_frame:int=0):
        """provide all posible metadata for ploting """

        self.freqs_val= [dataset.get_freq_val(idx_freq=_idx_freq) for _idx_freq in self.idx_freqs]
        self.idx_frames=[] 
        if self.ref_frame_idx is not None:
            self.idx_frames.append(dataset.get_idx_ref_frame())
        self.idx_frames.append(dataset.get_idx_frame(idx_frame))

        for key, func in DATA_TRANSFORMATIONS.items():  # for name, age in dictionary.iteritems():  (for Python 2.x)
            if func == self.transform_funcs[0]:
                trans_label=key
    
        self.label_meas=[
            f'{trans_label}(U)',
            f'{trans_label}({self.label_imaging})'
        ]
        if DATA_TRANSFORMATIONS['Abs'] == self.transform_funcs[1]:
            self.label_meas=[f'||{lab}||' for lab in self.label_meas ]

    @abstractmethod
    def make_labels(self, metadata):
        """"""
    def frame_label(self, idx) ->str:
        return f'Frame #{self.idx_frames[idx]}'
    
    def freq_label(self, idx) -> str:
        return f"Frequency #{eng(self.freqs_val[idx],'Hz')}"
    
    def check_data(self, idx_frames_len, freqs_val_len):
        if len(self.idx_frames)!=idx_frames_len:
            raise Exception(f'should be {idx_frames_len} frame idx idx_frames:{self.idx_frames}')
        if len(self.freqs_val)!=freqs_val_len:
            raise Exception(f'should be {freqs_val_len} freqences values freqs_val:{self.freqs_val}')

class AbsoluteImaging(Imaging):

    def __init__(self, idx_freqs:List[int], ref_frame_idx:int=0, transform_funcs: list = None) -> None:
        if transform_funcs is None:
            transform_funcs = []
        self.label_imaging='U'
        self.detail_freqs=[{'Frequence in Hz' : idx_freqs[0]}, None]
        self.ref_frame_idx=None
        self.transform_funcs= transform_funcs
    
    def pre_process_data(self, dataset:EitMeasurementSet, eit_model:EITModelClass, idx_frame:int=0)->np.ndarray:
        """"""
        if len(self.idx_freqs)!=1:
            return np.array([])

        voltages=dataset.get_voltages(idx_frame=idx_frame, idx_freq=self.idx_freqs[0])
        v=make_voltage_vector(eit_model, self.transform_funcs, voltages)
        return np.hstack((v, v))
    
    def make_labels(self)->dict:
        
        self.check_data(1,1)

        t=f'({self.label_meas[1]}); {self.frame_label(0)} ({self.freq_label(0)})'
        return  {
                    PlotType.Image_2D:{
                        'title': f'Absolute Imaging {t}',
                        'legend': ['',''],
                        'xylabel': ['X', 'Y']
                    },
                    PlotType.U_plot:{
                        'title': f'Voltages ({self.label_meas[0]}); {self.freq_label(0)}' ,
                        'legend': [f'{self.frame_label(0)}',f'{self.frame_label(0)}'],
                        'xylabel': ['Measurements', 'Voltages in [V]']
                    },
                    PlotType.Diff_plot:{
                        'title': f'Voltages {t}',
                        'legend': ['',''],
                        'xylabel': ['Measurements', 'Voltages in [V]']
                    }
                }
        

class TimeDifferenceImaging(Imaging):

    def __init__(self, idx_freqs:List[float], ref_frame_idx:int=0, transform_funcs: list = None) -> None:
        if transform_funcs is None:
            transform_funcs = []
        self.label_imaging='\u0394U_t' #ΔU_t
        self.detail_freqs=[{'Frequence in Hz' : idx_freqs[0]}, None]
        self.ref_frame_idx=ref_frame_idx
        self.transform_funcs= transform_funcs

    def pre_process_data(
            self,
            dataset:EitMeasurementSet, 
            eit_model:EITModelClass, 
            idx_frame:int=0) -> np.ndarray:
        """"""

        if self.ref_frame_idx is None or len(self.idx_freqs)!=1:
            return np.array([]) 
            
        v_t0=dataset.get_voltages_ref_frame(self.idx_freqs[0])
        v_t1=dataset.get_voltages(idx_frame=idx_frame, idx_freq=self.idx_freqs[0])
        return np.hstack((
            make_voltage_vector(eit_model, self.transform_funcs, v_t0),
            make_voltage_vector(eit_model, self.transform_funcs, v_t1)))
       
    def make_labels(self):
        
        self.check_data(2,1)

        t=f'({self.label_meas[1]}); {self.freq_label(0)} ({self.frame_label(0)} -{self.frame_label(1)})'

        return  {
                    PlotType.Image_2D:{
                        'title': f'Time difference Imaging {t}',
                        'legend': ['',''],
                        'xylabel': ['X', 'Y', 'Z']
                    },
                    PlotType.U_plot:{
                        'title': f'Voltages ({self.label_meas[0]}); {self.freq_label(0)}' ,
                        'legend': [ f'Ref {self.frame_label(0)}',f'{self.frame_label(1)}'],
                        'xylabel':  ['Measurements', 'Voltages in [V]']
                    },
                    PlotType.Diff_plot:{
                        'title': f'Voltage differences {t}',
                        'legend': ['',''],
                        'xylabel': ['Measurements', 'Voltages in [V]']
                    },
                }
        
class FrequenceDifferenceImaging(Imaging):

    def __init__(self, idx_freqs:List[float], ref_frame_idx:int=0, transform_funcs: list = None) -> None:
        if transform_funcs is None:
            transform_funcs = []
        self.label_imaging='\u0394U_f' #ΔU_f
        self.detail_freqs=[
            {'Frequence (ref) in Hz' : idx_freqs[0]},
            {'Frequence in Hz' : idx_freqs[1]}]
        self.ref_frame_idx=None
        self.transform_funcs= transform_funcs
    
    def pre_process_data(self, dataset:EitMeasurementSet, eit_model:EITModelClass, idx_frame:int=0) -> np.ndarray:
        """"""
        if len(self.idx_freqs)!=2:
            return np.array([]) 
            
        v_f0=dataset.get_voltages(idx_frame=idx_frame, idx_freq=self.idx_freqs[0])
        v_f1=dataset.get_voltages(idx_frame=idx_frame, idx_freq=self.idx_freqs[1])
        return np.hstack((
            make_voltage_vector(eit_model, self.transform_funcs, v_f0),
            make_voltage_vector(eit_model, self.transform_funcs, v_f1)))


    def make_labels(self):
    
        self.check_data(1,2)
        
        t= f' ({self.label_meas[1]}); {self.frame_label(0)} ({self.freq_label(0)} - {self.freq_label(1)})',

        return  {
                    PlotType.Image_2D:{
                        'title': f'Frequency difference Imaging {t}',
                        'legend': ['',''],
                        'xylabel': ['X', 'Y', 'Z']
                    },
                    PlotType.U_plot:{
                        'title': f'Voltages ({self.label_meas[0]}); {self.frame_label(0)} ' ,
                        'legend': [ f'Ref {self.freq_label(0)}',f'{self.freq_label(1)}'],
                        'xylabel':  ['Measurements', 'Voltages in [V]']
                    },
                    PlotType.Diff_plot:{
                        'title': f'Voltage differences {t}',
                        'legend': ['',''],
                        'xylabel': ['Measurements', 'Voltages in [V]']
                    },
                }   



IMAGING_TYPE={
    'Absolute imaging':AbsoluteImaging,
    'Time difference imaging':TimeDifferenceImaging,
    'Frequence difference imaging':FrequenceDifferenceImaging,
}

if __name__ == "__main__":

    print('\u0394U_t')
    a=[np.array([1,1,1,1,1,1,1,]), np.array([1,1,1,1,1,1,1,])]

    print(a)
    print(a[0], type(a[0]))


    print(list(IMAGING_TYPE.keys()))
    print('Absolute imaging' in list(IMAGING_TYPE.keys()))

    a= FrequenceDifferenceImaging([1000.0, 1000.0], [])
    freqs= [list(item.values())[0] for item in a.idx_freqs if item is not None]
    print(freqs)
