


from typing import Any, Callable, List
from PyQt5 import QtWidgets
import numpy as np
from eit_app.app.gui import Ui_MainWindow
from eit_app.app.utils import set_comboBox_items, set_slider, set_table_widget, change_value_withblockSignal
from eit_app.app.event import CustomEvents
from eit_app.io.sciospec.device import StatusSWInterface, IOInterfaceSciospec
from enum import Enum, auto

from eit_app.eit.imaging_type import DATA_TRANSFORMATIONS, IMAGING_TYPE, Imaging
from eit_app.io.sciospec.meas_dataset import EitMeasurementDataset

from glob_utils.flags.flag import CustomFlag



class UpdateListenerError(Exception):
    """"""




class AutoName(Enum):
    def _generate_next_value_(name, start, count, last_values):
        return name

#### Update device tab

def handle_device_refresh_event(app:Ui_MainWindow, device:IOInterfaceSciospec):
    """ Handle responsible of refesh the list of devices in the comboBox """
    items = [key for key in device.available_devices.keys()] or ['None device']
    set_comboBox_items(app.cB_ports,items)

def handle_device_status_event(app:Ui_MainWindow, device:IOInterfaceSciospec):
    """ Handle responsible of actualize the status label of the device """
    app.lab_device_status.setText(device.status_prompt)
    app.lab_device_status.adjustSize
    if device.status == StatusSWInterface.NOT_CONNECTED:
        app.lab_device_status.setStyleSheet("background-color: red")
    else:
        app.lab_device_status.setStyleSheet("background-color: green")

def handle_device_setup_event(app:Ui_MainWindow, device:IOInterfaceSciospec, set_freq_max_enable:bool=True, error:bool=False):
    
    app.lE_sn.setText(device.setup.get_sn())
    ## Update EthernetConfig
    app.chB_dhcp.setChecked(bool(device.setup.get_dhcp()))
    app.lE_ip.setText(device.setup.get_ip())
    app.lE_mac.setText(device.setup.get_mac())

    ## Update OutputConfig Stamps
    app.chB_exc_stamp.setChecked(bool(device.setup.get_exc_stamp()))
    app.chB_current_stamp.setChecked(bool(device.setup.get_current_stamp()))
    app.chB_time_stamp.setChecked(bool(device.setup.get_time_stamp()))
    
    ## Update Measurement Setups
    change_value_withblockSignal(app.sBd_frame_rate.setValue,device.setup.get_frame_rate())
    change_value_withblockSignal(app.sBd_max_frame_rate.setValue,device.setup.get_max_frame_rate())
    change_value_withblockSignal(app.sB_burst.setValue,device.setup.get_burst())
    change_value_withblockSignal(app.sBd_exc_amp.setValue,device.setup.get_exc_amp()*1000) # from A -> mA
    change_value_withblockSignal(app.sBd_freq_min.setValue,device.setup.get_freq_min())
    change_value_withblockSignal(app.sBd_freq_max.setValue,device.setup.get_freq_max())
    change_value_withblockSignal(app.sB_freq_steps.setValue,device.setup.get_freq_steps())
    change_value_withblockSignal(app.cB_scale.setCurrentText,device.setup.get_freq_scale())

    app.sBd_freq_max.setEnabled(set_freq_max_enable)
    color= 'red' if error else 'white'
    for sB in [app.sBd_freq_min, app.sBd_freq_max, app.sB_freq_steps]: 
        sB.setStyleSheet(f"background-color: {color}")

    set_table_widget(app.tw_exc_pattern,device.setup.get_exc_pattern(),0)
    update_freqs_list_meas(app, device.setup.get_freqs())


#### Update Measurement tab
class UpdateMeasurementsEvents(AutoName):
    """ """

def update_freqs_list_meas(app:Ui_MainWindow, freqs:List[Any]):
    for cB in [ app.cB_freq_meas_0, 
                app.cB_freq_meas_1]:
        set_comboBox_items(cB, [f for f in freqs])

def update_live_view_status(app:Ui_MainWindow, live_meas:CustomFlag):
    if live_meas.is_set():
        app.lab_live_meas_status.setText('MEASUREMENTS ON')
        app.lab_live_meas_status.setStyleSheet("background-color: green")
    else:
        app.lab_live_meas_status.setText('MEASUREMENTS OFF')
        app.lab_live_meas_status.setStyleSheet("background-color: red")
        app.meas_progress_bar.setValue(0)


def update_replay_status(app:Ui_MainWindow, replay:CustomFlag):
    if replay.is_set():
        app.lab_replay_status.setText('REPLAY ON')
        app.lab_replay_status.setStyleSheet("background-color: blue")
    else:
        app.lab_replay_status.setText('REPLAY OFF')
        app.lab_replay_status.setStyleSheet("background-color: grey")
        set_slider(app.slider_replay, slider_pos=0)

def update_imaging_inputs_field(app:Ui_MainWindow, imaging_type:Imaging):
    """"""
    app.cB_ref_frame_idx.setVisible(imaging_type.ref_frame_idx!=None)
    app.lab_ref_frame_idx.setVisible(imaging_type.ref_frame_idx!=None)
    if imaging_type.idx_freqs[0] is not None:
        app.cB_freq_meas_0.setEnabled(True)
        app.lab_freq_meas_0.setText(list(imaging_type.idx_freqs[0].keys())[0])
    
    if imaging_type.idx_freqs[1] is not None:
        app.cB_freq_meas_1.setVisible(True)
        app.lab_freq_meas_1.setVisible(True)
        app.lab_freq_meas_1.setText(list(imaging_type.idx_freqs[1].keys())[0])
    else:
        app.cB_freq_meas_1.setVisible(False)
        app.lab_freq_meas_1.setVisible(False)

def update_plots_to_show_inputs(app:Ui_MainWindow):
    app.chB_Uplot.setEnabled(app.chB_plot_graph.isChecked())
    app.chB_diff.setEnabled(app.chB_plot_graph.isChecked())
    app.chB_y_log.setEnabled(app.chB_plot_graph.isChecked())

def update_progression_acquisition_single_frame(app:Ui_MainWindow, idx_frame:int=0, progression:int=0):
    app.sB_actual_frame_cnt.setValue(idx_frame)
    app.meas_progress_bar.setValue(progression)

def update_info_data_computed(app:Ui_MainWindow, live_meas:CustomFlag=CustomFlag, idx_frame:List[int]=0, info:str=''):
    if live_meas.is_set():
        set_comboBox_items(app.cB_current_idx_frame, [idx_frame], reset_box=False, set_index=-1, block=True ) 
    app.tE_frame_info.setText("\r\n".join(info))
    
def update_autosave_changed(app:Ui_MainWindow):
    app.lE_meas_dataset_dir.setEnabled(app.chB_dataset_autoset.isChecked())
    app.chB_dataset_save_img.setEnabled(app.chB_dataset_autoset.isChecked())

def update_dataset_loaded(app:Ui_MainWindow, dataset:EitMeasurementDataset ):

    app.tE_load_dataset_dir.setText(dataset.output_dir)
    nb_loaded_frame= dataset.frame_cnt
    set_comboBox_items(app.cB_current_idx_frame, [i for i in range(nb_loaded_frame)])
    set_comboBox_items(app.cB_ref_frame_idx, [i for i in range(nb_loaded_frame)])
    set_slider(app.slider_replay,  slider_pos=0, pos_min=0, pos_max=nb_loaded_frame-1, single_step=1)


class UpdateEvents(AutoName):
    device_list_refreshed=auto()
    device_status=auto()
    device_setup=auto()
    live_meas_status=auto()
    replay_status=auto()
    freqs_inputs=auto()
    plots_to_show= auto()
    progress_frame=auto()
    info_data_computed=auto()
    autosave_changed=auto()
    dataset_loaded=auto()


update_devices_events={ 
    UpdateEvents.device_list_refreshed:    [handle_device_refresh_event, True],
    UpdateEvents.device_status:         [handle_device_status_event, True],
    UpdateEvents.device_setup:             [handle_device_setup_event, True],
    UpdateEvents.live_meas_status:             [update_live_view_status, True],
    UpdateEvents.replay_status:             [update_replay_status, True],
    UpdateEvents.freqs_inputs: [update_imaging_inputs_field, True],
    UpdateEvents.plots_to_show: [update_plots_to_show_inputs,True],
    UpdateEvents.progress_frame: [update_progression_acquisition_single_frame,True],
    UpdateEvents.info_data_computed: [update_info_data_computed, True],
    UpdateEvents.autosave_changed: [update_autosave_changed, True],
    UpdateEvents.dataset_loaded: [update_dataset_loaded, True]
}


def setup_update_event_handlers(event:CustomEvents):
    for key in update_devices_events.keys():
        if update_devices_events[key][1]:
            event.subscribe(key, update_devices_events[key][0])


if __name__=="__main__":

    print()