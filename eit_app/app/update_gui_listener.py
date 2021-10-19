


from eit_app.app.gui import Ui_MainWindow
from eit_app.app.utils import setItems_comboBox
from eit_app.app.event import subscribe
from eit_app.io.sciospec.device import StatusSWInterface, SWInterface4SciospecDevice
from enum import Enum, auto

#### Update_device tab

class AutoName(Enum):
    def _generate_next_value_(name, start, count, last_values):
        return name

class UpdateDeviceEvents(AutoName):
    device_list_refreshed=auto()
    device_connected=auto()
    device_disconnected=auto()


def handle_device_list_refreshed_event(app:Ui_MainWindow, device:SWInterface4SciospecDevice):
    """ """
    items = [key for key in device.available_devices.keys()] or ['None device']
    setItems_comboBox(app.cB_comport,items)

def handle_device_connected_event(app:Ui_MainWindow, device:SWInterface4SciospecDevice):
    """ """
    # items = [key for key in app.EITDev.available_devices.keys()] or ['None device']
    # setItems_comboBox(app.cB_comport,items)
    ## Update device status
    app.status_device.setText(device.status_prompt)
    app.status_device.adjustSize
    print('teststautu',device.status == StatusSWInterface.NOT_CONNECTED)
    if device.status == StatusSWInterface.NOT_CONNECTED:
        app.status_device.setStyleSheet("background-color: red")
    else:
        app.status_device.setStyleSheet("background-color: green")

def handle_device_disconnected_event(app:Ui_MainWindow,device:SWInterface4SciospecDevice):
    """ """
    handle_device_connected_event(app,device)



update_devices_events={ 
    UpdateDeviceEvents.device_list_refreshed:    [handle_device_list_refreshed_event, True],
    UpdateDeviceEvents.device_connected:         [handle_device_connected_event, True],
    UpdateDeviceEvents.device_disconnected:      [handle_device_disconnected_event, True]
}

def setup_update_event_handlers():
    for key in update_devices_events.keys():
        if update_devices_events[key][1]:
            subscribe(key, update_devices_events[key][0])