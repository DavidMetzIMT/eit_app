

from dataclasses import dataclass, field
import itertools
import logging
import os
from typing import Callable
from PyQt5 import QtWidgets
from eit_app.computation import ComputingAgent
from eit_app.gui_utils import get_comboBox_allItemsIndex, set_comboBox_index
from eit_app.sciospec.measurement import MeasurementDataset
from eit_app.sciospec.replay import ReplayMeasurementsAgent
import glob_utils.directory.utils
import eit_app.gui
from threading import Timer
import glob_utils.dialog.Qt_dialogs

logger = logging.getLogger(__name__)


class RepeatTimer(Timer):
    """Thread Timer which start all over again"""

    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)

@dataclass
class ExportFunc:
    enable_func:Callable
    func:Callable # should acccept only a path to export data
    is_exported:Callable # should return a bool about the status of the export
    before_compute:bool= True # determine if the func is called after the computation

    def run(self, *args, **kwargs):
        if self.enable_func():
            self.func(*args, **kwargs)
    
@dataclass
class ParamsToLoopOn:
    enable_func:Callable # fucnion which give if actual param shoul be used to loop on (e.g.: chB.isChecked)
    export_val_in_filename:bool
    combobox:QtWidgets.QComboBox
    func_set:Callable
    tag:str
    block:bool=False # block signal by setting 
    item_idx:int=field(init=False)

    def get_list(self)->list:
        return (
            get_comboBox_allItemsIndex(self.combobox)
            if self.enable_func()
            else [self.combobox.currentIndex()]
        )
    
    def set_val(self, val:int=None):
        set_comboBox_index(self.combobox, val)
        self.func_set()
        # if val is not None:
        #     if self.block:
        #         set_comboBox_index(self.combobox, val)
        #     else:
        #         self.combobox.setCurrentIndex(val)
                
    
    def get_info_text(self):
        return f"_{self.tag}{self.combobox.currentText()}".replace(" ", "_")
            
        
class ExportAgent:#
    replay_agent:ReplayMeasurementsAgent
    dataset:MeasurementDataset
    computing:ComputingAgent
    params_to_loop_on:list[ParamsToLoopOn]
    export_func:list[ExportFunc]

    def __init__(self, replay_agent:ReplayMeasurementsAgent, dataset:MeasurementDataset, computing:ComputingAgent, ui:eit_app.gui.Ui_MainWindow) -> None:
        self.ui=ui
        self.replay_agent=replay_agent
        self.dataset= dataset
        self.computing= computing
        self.params_to_loop_on=[]
        self.export_func=[]

    def add_params(self, param:ParamsToLoopOn)->None:
        self.params_to_loop_on.append(param)

    def add_export(self, export:ExportFunc)->None:
        self.export_func.append(export)
    
    def run_export(self):
        """"""
        if not self.replay_agent.is_idle:
            glob_utils.dialog.Qt_dialogs.infoMsgBox("Export Aborded", "Load a dataset or stop auto replay")
            return

        self._datetime= glob_utils.directory.utils.get_datetime_s()
        a= [p.get_list() for p in self.params_to_loop_on]
        self.combinations=list(itertools.product(*a))
        self._comb_idx=0
        self.timer= RepeatTimer(2.0, self._export_plots)
        self.timer.start()
        

    def _export_plots(self):
        """"""
        c= self.combinations[self._comb_idx]
        t=""
        for val, p in zip(c,self.params_to_loop_on):
            p.set_val(val)
            t=f"{t}{p.get_info_text()}"
        par_text= t
        frame_idx=c[0]
        frame_path= self.dataset.get_meas_path(frame_idx)
        dir_path= os.path.splitext(frame_path)[0]
        dir_path= f"{dir_path}_{self.ui.cB_eit_imaging_type.currentText()}"
        glob_utils.directory.utils.mk_dir(dir_path) 

        path= os.path.join(dir_path, f"{self._datetime}{par_text}")
        [export.run(path) for export in self.export_func if export.before_compute]

        self.replay_agent.compute_meas_frame(frame_idx)
        while not self.computing._is_processing:
            pass
        while self.computing._is_processing:
            pass
        
        [export.run(path) for export in self.export_func if not export.before_compute]
        # logger.debug(f"{frame_idx}: {self.replay_agent.actual_frame_idx}")

        while not any(export.is_exported() for export in self.export_func):
            pass
    
        # [export.run(path) for export in self.export_func if not export.before_compute]

        # while not all(export.is_exported() for export in self.export_func):
        #     pass

        self._comb_idx +=1
        if self._comb_idx>= len(self.combinations):
            self.timer.cancel()
            logger.info('Export - DONE')
            # glob_utils.dialog.Qt_dialogs.infoMsgBox("Export Done", "Export Done")