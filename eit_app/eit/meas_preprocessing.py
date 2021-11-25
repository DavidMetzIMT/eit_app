from typing import List, ValuesView

import numpy as np
from matplotlib.cbook import flatten
from matplotlib.pyplot import title

from eit_app.io.sciospec.device import EitMeasurementSet
from eit_app.io.sciospec.meas_dataset import EITFrame


def _voltages_preparation(dataset:EitMeasurementSet, frameIndx, imagingParameters, EITModel, liveView=False):
    """
    Extract from the given dataset the corresponding voltages Values and 
    process them for plot/recontruction according to the required immagingData and imagingMode

    Parameters
    ----------
    dataset: EITDataSet() inwhich are contained the all the 
    indx: int
    imagingData: bool list

        imagingData=[   showReal, use real part of the voltage
                        showImag, use imaginary part of the voltage
                        showMagnitude, use magnitude of the voltage
                        showPhase, use phase/angle of the voltage
                        showAbsValue] use absolute val (real, Imag, magnitude, phase) of the voltage
    imagingMode: list
    self.imagingMode= [     [self.rB_rawData.isChecked(),self.cB_Frequency.currentIndex(),0]
                            [self.rB_TimeDiff.isChecked(),self.cB_Frequency4TD.currentIndex(),0],
                            [self.rB_FreqDiff.isChecked(), self.cB_Frequeny4FD_0.currentIndex(), self.cB_Frequeny4FD_1.currentIndex()]]
    Returns
    -------
    U : array N x 1 (N= nb of measurement)
        Voltages vector to use
    
    Notes
    -----
    
    """   
    datatype_available=[np.real, np.imag, abs, np.angle]
    imagingData_labels=['real(U)', 'imag(U)', 'magn(U)', 'angl(U)']
    
    datatype_indx= imagingParameters[3][:4].index(True)
    imagingDataFunc= datatype_available[datatype_indx]
 
    current_label= imagingData_labels[datatype_indx]

    if imagingParameters[3][4]==True:
        current_label= '||' + current_label +'||'
        imagingDataAbs= abs
    else:
        imagingDataAbs= identity

    if liveView==True:
        frame= dataset.meas_frame
    else:
        frame= dataset.rx_meas_frame
        
    ouput_labels=[]
        
    if imagingParameters[0][0]  == True : # raw data/ single measurements
        freqIndx= imagingParameters[0][1]
        voltages_4_plot=_get_meas_voltage_vector(frame,frameIndx, freqIndx, imagingDataAbs,imagingDataFunc, EITModel)*np.ones((1,2))
        frm_indx=frame[frameIndx].idx
        freq_val= frame[frameIndx].meas[freqIndx].frequency
        ouput_labels.append(current_label)#
        ouput_labels.append(current_label)#
        title_plot= 'Measurements of '+ f'Frm: {frm_indx}, frq_0: {freq_val} Hz'
        ouput_labels.append(title_plot)
        title_plot_diff= 'Measurements of'+ f'Frm: {frm_indx}, frq_0: {freq_val} Hz'
        ouput_labels.append(title_plot_diff)
        voltages_4_rec=voltages_4_plot

    if imagingParameters[1][0]==True: # time Diff
        freqIndx= imagingParameters[1][1]
        u_t0=_get_meas_voltage_vector(dataset._frame_TD_ref,0, freqIndx, imagingDataAbs,imagingDataFunc, EITModel)
        u_t1=_get_meas_voltage_vector(frame,frameIndx, freqIndx, imagingDataAbs,imagingDataFunc, EITModel)
        voltages_4_rec=np.hstack((u_t0,u_t1))
        voltages_4_plot = voltages_4_rec[:,1]- voltages_4_rec[:,0]
        frmref_indx=dataset._frame_TD_ref[0].idx
        frm_indx=frame[frameIndx].idx
        freq_val= frame[frameIndx].meas[freqIndx].frequency
        
        ouput_labels.append(current_label + f' ref. frame: {frmref_indx}; {freq_val} Hz')#
        ouput_labels.append(current_label + f' Frm: {frm_indx}; {freq_val} Hz')#
        title_plot= 'Time diff: Measurements of '+ f'Frame #{frm_indx} vs Frame #{frmref_indx}' 
        ouput_labels.append(title_plot)#
        title_plot_diff= 'Time diff: Difference between '+ f'Frame #{frm_indx} - Frame #{frmref_indx}'
        ouput_labels.append(title_plot_diff)

    if imagingParameters[2][0]==True: # freq Diff
        freqIndx0= imagingParameters[2][1]
        freqIndx1= imagingParameters[2][2]
        u_f0=_get_meas_voltage_vector(frame,frameIndx, freqIndx0, imagingDataAbs,imagingDataFunc, EITModel)
        u_f1=_get_meas_voltage_vector(frame,frameIndx, freqIndx1, imagingDataAbs,imagingDataFunc, EITModel)
        voltages_4_rec=np.hstack((u_f0,u_f1))
        voltages_4_plot = voltages_4_rec[:,1]- voltages_4_rec[:,0]
        freq_val_1= frame[frameIndx].meas[freqIndx0].frequency
        freq_val_0= frame[frameIndx].meas[freqIndx1].frequency
        frm_indx=frame[frameIndx].idx
        ouput_labels.append(current_label+ f' Frame: {frm_indx}; {freq_val_0} Hz' )#
        ouput_labels.append(current_label+ f' Frame: {frm_indx}; {freq_val_1} Hz' )#
        title_plot= 'Freq diff: Measurements of '+ f'Frame #{frm_indx} ' 
        ouput_labels.append(title_plot)
        title_plot_diff= 'Freq diff: Difference between '+ f'f:{freq_val_1} Hz - f:{freq_val_0} Hz'
        ouput_labels.append(title_plot_diff)#

    return voltages_4_plot, ouput_labels, voltages_4_rec


def Voltages4Reconstruct(dataset, frameIndx, imagingParameters, EITModel, liveView=False, path=None):
    """
    Extract from the given dataset the corresponding voltages Values and 
    process them for plot/recontruction according to the required imagingParameters
    
    Notes
    -----
    
    """ 
    voltages_4_plot, current_label, voltages_4_rec = _voltages_preparation(dataset, frameIndx, imagingParameters , EITModel, liveView=liveView)
    
    if path!=None:
        extract(voltages_4_rec, path)

    return voltages_4_rec, current_label

    
def _get_meas_voltage_vector(frame:List[EITFrame],frameIndx, freqIndx, imagingDataAbs, imagingDataFunc, EITModel):
    """
    Extract the measured voltage vector out of the given frame
    and transform it value depending the selected imagingDataFunc / imagingDataAbs
    
    Return
    ------
    meas_voltage: v

    Notes
    -----
    
    """ 
    meas_voltage=np.array(frame[frameIndx].meas[freqIndx].voltage_Z) # select the measured voltages on all 32 channels (columns ) for all injections (row)
    meas_voltage=np.array(meas_voltage[:,:EITModel.n_el]) # select the measured voltages on all 32 channels
    meas_voltage=(EITModel.MeasPattern.dot(meas_voltage.T)).flatten()
    meas_voltage=np.reshape(imagingDataAbs(imagingDataFunc(meas_voltage)),(meas_voltage.shape[0],1))
    

    return meas_voltage

def identity(x):
    return x

def extract(x, path):
    np.savetxt(path, x, delimiter='\t') 

if __name__ == '__main__':
    dataset= 1
    indx= 1
    imagingData =[True , False, False, False, True]
    imagingMode=[[True, 0, 0],
                    [False, 0,0]]
    imagingData_labels=['real()', 'image()', 'magnitude()', 'angle()']
    print(imagingData_labels)
    if imagingData[4]==True:
        for i,l in enumerate(imagingData_labels):
            imagingData_labels[i]= '||' +l +'||'
    print(imagingData_labels)
    frameIndx=1
    current_label= imagingData_labels[2]
    current_label= current_label[:-3]+ f'TD U_frame({frameIndx})' +current_label[-3:]
    print(current_label)
    
    pass
