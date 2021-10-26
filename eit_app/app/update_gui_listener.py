


from typing import Callable
from PyQt5 import QtWidgets
from eit_app.app.gui import Ui_MainWindow
from eit_app.app.utils import set_comboBox_items, set_table_widget, change_value_withblockSignal
from eit_app.app.event import CustomEvents
from eit_app.io.sciospec.device import StatusSWInterface, SWInterface4SciospecDevice
from enum import Enum, auto

class AutoName(Enum):
    def _generate_next_value_(name, start, count, last_values):
        return name

#### Update device tab
class UpdateDeviceEvents(AutoName):
    device_list_refreshed=auto()
    device_status=auto()
    device_setup=auto()

def handle_device_refresh_event(app:Ui_MainWindow, device:SWInterface4SciospecDevice):
    """ Handle responsible of refesh the list of devices in the comboBox """
    items = [key for key in device.available_devices.keys()] or ['None device']
    set_comboBox_items(app.cB_ports,items)

def handle_device_status_event(app:Ui_MainWindow, device:SWInterface4SciospecDevice):
    """ Handle responsible of actualize the status label of the device """
    app.lab_device_status.setText(device.status_prompt)
    app.lab_device_status.adjustSize
    if device.status == StatusSWInterface.NOT_CONNECTED:
        app.lab_device_status.setStyleSheet("background-color: red")
    else:
        app.lab_device_status.setStyleSheet("background-color: green")

def handle_device_setup_event(app:Ui_MainWindow, device:SWInterface4SciospecDevice, set_freq_max_enable:bool=True, error:bool=False):
    

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
    




update_devices_events={ 
    UpdateDeviceEvents.device_list_refreshed:    [handle_device_refresh_event, True],
    UpdateDeviceEvents.device_status:         [handle_device_status_event, True],
    UpdateDeviceEvents.device_setup:             [handle_device_setup_event, True]
}

def setup_update_event_handlers(event:CustomEvents):
    for key in update_devices_events.keys():
        if update_devices_events[key][1]:
            event.subscribe(key, update_devices_events[key][0])

#### Update Measurement tab
class UpdateMeasurementsEvents(AutoName):
    """ """


def update_freqs_list_meas(app:Ui_MainWindow, freqs):
    for cB in [ app.cB_freq_abs_meas, 
                app.cB_freq_time_meas, 
                app.cB_freq_freq_meas_0, 
                app.cB_freq_freq_meas_1]:
        set_comboBox_items(cB, [f for f in freqs])


if __name__=="__main__":
    """"""