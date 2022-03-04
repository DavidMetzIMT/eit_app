


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

    def __init__(self) -> None:
        super().__init__()

    def process_data(self,dataset:EitMeasurementSet, eit_model:EITModelClass, idx_frame:int=0,extract_voltages:bool=False):
        
        self.idx_freqs= [list(item.values())[0] for item in self.detail_freqs if item is not None]
        self.idx_freqs.reverse()

        meas_voltages=self.pre_process_data(dataset, eit_model, idx_frame)
        _metadata=self.get_metadata(dataset, idx_frame)
        labels= self.make_labels(_metadata)
        return meas_voltages, labels

    @abstractmethod
    def pre_process_data(self, dataset:EitMeasurementSet, eit_model:EITModelClass, idx_frame:int=0)->List[np.ndarray]:
        """"""
        # return meas_voltage

    def get_metadata(self, dataset:EitMeasurementSet, idx_frame:int=0):
        """provide all posible metadata for ploting """

        freqs_val= [dataset.get_freq_val(idx_freq=_idx_freq) for _idx_freq in self.idx_freqs]
        idx_frames=[] 
        if self.ref_frame_idx is not None:
            idx_frames.append(dataset.get_idx_ref_frame())
        idx_frames.append(dataset.get_idx_frame(idx_frame=idx_frame))

        for key, func in DATA_TRANSFORMATIONS.items():  # for name, age in dictionary.iteritems():  (for Python 2.x)
            if func == self.transform_funcs[0]:
                trans_label=key
    
        label_meas=[
            f'{trans_label}(U)',
            f'{trans_label}({self.label_imaging})'
        ]
        if DATA_TRANSFORMATIONS['Abs'] == self.transform_funcs[1]:
            label_meas=[
                f'||{trans_label}(U)||',
                f'||{trans_label}({self.label_imaging})||'
            ]
        return freqs_val, idx_frames, label_meas

    @abstractmethod
    def make_labels(self, metadata):
        """"""

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
    
    def make_labels(self, metadata):
        
        freqs_val, idx_frames, label_meas= metadata

        if len(idx_frames)!=1:
            raise Exception(f'should be 1 frame idx idx_frames:{idx_frames}')
        if len(freqs_val)!=1:
            raise Exception(f'should be 1 freqences values freqs_val:{freqs_val}')

        frame= f'Frame #{idx_frames[0]}'
        freq_0= f'{freqs_val[0]} Hz'
        # freq_1= f'{freqs_val[1]} Hz'
        return  {
                    PlotType.Image_2D:{
                        'title': f'Absolute Imaging ({label_meas[1]}); {frame} ({freq_0})',
                        'legend': ['',''],
                        'xylabel': ['X', 'Y']
                    },
                    PlotType.U_plot:{
                        'title': f'Voltages ({label_meas[0]}); Frequence: {freq_0}' ,
                        'legend': [f'{frame}',f'{frame}'],
                        'xylabel': ['Measurements', 'Voltages in [V]']
                    },
                    PlotType.Diff_plot:{
                        'title': f'Voltages ({label_meas[1]}); {frame} ({freq_0})',
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
       
    def make_labels(self, metadata):
        
        freqs_val, idx_frames, label_meas= metadata
        
        if len(idx_frames)!=2:
            raise Exception(f'should be 2 frame idx idx_frames:{idx_frames}')
        if len(freqs_val)!=1:
            raise Exception(f'should be 1 freqences values freqs_val:{freqs_val}')

        frame_0 = f'Frame #{idx_frames[0]}'
        frame_1 = f'Frame #{idx_frames[1]}'
        freq = f"Frequency #{eng(freqs_val[0],'Hz','.2g')}"
        # freq_1= f'{freqs_val[1]} Hz'

        return  {
                    PlotType.Image_2D:{
                        # 'title': f'Time difference Imaging ({label_meas[1]}); {frame} ({freq_0} - {freq_1})',
                        'title': f'Time difference Imaging ({label_meas[1]}); {freq} ({frame_0} -{frame_1})',
                        'legend': ['',''],
                        'xylabel': ['X', 'Y', 'Z']
                    },
                    PlotType.U_plot:{
                        'title': f'Voltages ({label_meas[0]}); Frequence: {freq}' ,
                        'legend': [ f'Ref Frequence {frame_0}',f'Frequence {frame_1}'],
                        'xylabel':  ['Measurements', 'Voltages in [V]']
                    },
                    PlotType.Diff_plot:{
                        'title': f'Voltage differences ({label_meas[1]}); {freq} ({frame_0} -{frame_1})',
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
        
        # voltages=[]
        # if self.ref_frame_idx is not None:
        #     voltages.append(dataset.get_voltages_ref_frame(self.idx_freqs[0]))
        # for idx_freq in self.idx_freqs:
        #     voltages.append(dataset.get_voltages(idx_frame=idx_frame, idx_freq=idx_freq))
        # meas_voltage=[]
        # for voltage in voltages:
        #     volt_tmp=make_voltage_from_meas_pattern(eit_model, voltage)
        #     meas_voltage.append(transform_data(volt_tmp, self.transform_funcs))
        # return meas_voltage

    def make_labels(self, metadata):
        
        freqs_val, idx_frames, label_meas= metadata

        if len(idx_frames)!=1:
            raise Exception(f'should be 1 frame idx idx_frames:{idx_frames}')
        if len(freqs_val)!=2:
            raise Exception(f'should be 2 freqences values freqs_val:{freqs_val}')

        frame= f'Frame #{idx_frames[0]}'
        freq_0= f'{freqs_val[0]} Hz'
        freq_1= f'{freqs_val[1]} Hz'

        return  {
                    PlotType.Image_2D:{
                        'title': f'Frequency difference Imaging ({label_meas[1]}); {frame} ({freq_0} - {freq_1})',
                        'legend': ['',''],
                        'xylabel': ['X', 'Y', 'Z']
                    },
                    PlotType.U_plot:{
                        'title': f'Voltages ({label_meas[0]}); {frame} ' ,
                        'legend': [ f'Ref Frequence {freq_0}',f'Frequence {freq_1}'],
                        'xylabel':  ['Measurements', 'Voltages in [V]']
                    },
                    PlotType.Diff_plot:{
                        'title': f'Voltage differences ({label_meas[1]}); {frame} ({freq_0} - {freq_1})',
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
