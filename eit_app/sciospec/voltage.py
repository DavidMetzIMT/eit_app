from dataclasses import dataclass
import numpy as np


@dataclass
class EITVoltageLabels():
    """Gathers informations about an eit voltages 

    Args:
        frame_idx (int): frame indx
        freq (float): frame frequency in Hz
        lab_frame_idx (str): frame indx label string
        lab_frame_freq (str): frame frequency label string

    """    
    frame_idx:int # frame indx
    freq:float # frame frequency in Hz
    lab_frame_idx:str # frame indx label string
    lab_frame_freq:str # frame frequency label string

@dataclass
class EITChannelVoltage():
    """EITChannelVoltage correspond to the Voltages obtained by the eit device:
    - for all excitations
    - for one measuremnet frame
    - one frequency

    Args:
        volt (ndarray): array of eit voltages of shape(n_exc, n_ch), dtype = complex
        labels (EITVoltageLabels): 

    """
    volt: np.ndarray
    labels:EITVoltageLabels
    
    def get_frame_name(self)->str:
        return self.labels.lab_frame_idx
    
    def get_frame_freq(self)->str:
        return self.labels.lab_frame_freq