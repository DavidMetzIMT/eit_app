""" For the communication between Objects(gui inclusive) Signal and 
SignalDataClasses are defined to pass data for specific tasks 
(update, action to do,...)

Each Object to which a signal is send, need to treat it. The class 
"SignalReciever" is intende to be use as Parent class fro thos Objects.
It allows objects to automatically threat the data recieved. 

example of Use is

if main.py

    obj1= Obj1Class()
    obj2= Obj2Class()

    obj1.to_obj2.connect(obj2.to_reciever)

in object1.py

class Obj1Class(AddSignalToObj2)
    ...
    def foo(self):
        ...
        self.to_obj2.emit(Data2Obj2(val1, val2))

in object2.py

class Obj2Class(SignalReciever)
    ...
    def __init__(self):
        ...
        self.init_reciever(
            data_callback= {
                Data2Obj2: self.do_something
            }
        )

    def do_something(self, data:Data2Obj2)
        ....


"""


from abc import ABC
from dataclasses import dataclass, field
from queue import Queue
from typing import Any, Callable

from glob_utils.thread_process.signal import Signal
from glob_utils.thread_process.signal import Signal
from glob_utils.thread_process.threads_worker import CustomWorker
import numpy as np
from eit_app.sciospec.setup import SciospecSetup
from eit_app.update_gui import UPDATE_EVENTS, EventDataClass, UpdateAgent
from eit_app.sciospec.voltage import EITChannelVoltage

class SignalDataClass(ABC):
    """Abstract class of the dataclass defined for each update events"""


################################################################################
# To plot Signal
################################################################################


@dataclass
class Data2Plot:
    data: Any = None
    labels: dict = field(default_factory=lambda: {})
    destination: Any = None


class AddToPlotSignal(object):
    to_plot: Signal

    def __init__(self):
        super().__init__()
        self.to_plot = Signal(self)


################################################################################
# To plot Signal
################################################################################


@dataclass
class DataReplayStart:
    nb_frame: int


class AddToReplaySignal(object):
    to_replay: Signal

    def __init__(self):
        super().__init__()
        self.to_replay = Signal(self)


################################################################################
# To Computation Signal
################################################################################



@dataclass
class Data2Compute:
    """
    v_ref: EITChannelVoltage  
    v_meas: EITChannelVoltage  
    """    
    v_ref: EITChannelVoltage  
    v_meas: EITChannelVoltage  


class AddToComputationSignal(object):
    to_computation: Signal

    def __init__(self):
        super().__init__()
        self.to_computation = Signal(self)


################################################################################
# To Dataset Channel
################################################################################


@dataclass
class DataInit4Start:
    dev_setup: SciospecSetup


@dataclass
class DataReInit4Pause:
    """"""


@dataclass
class DataAddRxMeasStream:
    rx_meas_stream: list[bytes]


@dataclass
class DataEmitFrame4Computation:
    idx: int


@dataclass
class DataLoadLastDataset:
    """"""


class AddToDatasetSignal(object):
    to_dataset: Signal

    def __init__(self):
        super().__init__()
        self.to_dataset = Signal(self)


################################################################################
# To Capture Channel
################################################################################


@dataclass
class DataSaveLoadImage:
    frame_path: str


@dataclass
class SetStatusWMeasStatus:
    meas_status_dev: bool

    def __post_init__(self):
        self.meas_status_dev= bool(self.meas_status_dev)


@dataclass
class SetStatusWReplayStatus:
    replay_playing_status: bool
    replay_loaded_status: bool

    def __post_init__(self):
        self.replay_playing_status= bool(self.replay_playing_status)
        self.replay_loaded_status= bool(self.replay_loaded_status)


class AddToCaptureSignal(object):
    to_capture: Signal

    def __init__(self):
        super().__init__()
        self.to_capture = Signal(self)


################################################################################
# To Device Channel
################################################################################


@dataclass
class DataLoadSetup:
    dir: str


@dataclass
class DataCheckBurst:
    nb_frame_measured: str


class AddToDeviceSignal(object):
    to_device: Signal

    def __init__(self):
        super().__init__()
        self.to_device = Signal(self)


################################################################################
# To gui channel
################################################################################


class AddToGuiSignal(object):
    to_gui: Signal

    def __init__(self):
        super().__init__()
        self.to_gui = Signal(self)


################################################################################
# To gui channel
################################################################################


class SignalRecieverNotInitializated(BaseException):
    """"""


class SignalReciever(object):

    _data_callbacks = list

    def __init__(self) -> None:
        """Add a Signal reciever functionality which automatically
        threat the data recieved. via the definition of callbakc for each data type
        """
        super().__init__()
        self._data_callbacks = None

    def init_reciever(self, data_callbacks: dict[type, Callable]) -> None:
        """Define for each recieved data type an assiociated callback func

        e.g.:
        class Obj2Class(SignalReciever)
            ...
            def __init__(self):
                ...
                self.init_reciever(
                    data_callback= {
                        Data2Obj2: self.do_something
                    }
                )

            def do_something(self, data:Data2Obj2)
                ....

        Args:
            data_callbacks (dict[type, Callable]): _description_
        """
        self._data_callbacks = data_callbacks

    def to_reciever(self, data: Any = None, **kwargs) -> None:
        """Connect this method to the corresponding signal.
        it will only treat data passed as 1. arg or as kwargs (data=Data2Passs)

        e.g.: obj1.to_obj2.connect(obj2.to_reciever)

        Args:
            data (Any, optional): Data recieved from signal, and to be treated.
            Defaults to None.
        """
        self._check_is_init()
        self._treat_data(data)

    def _treat_data(self, data: Any) -> None:
        """Call for the passed data type the assosiated callback, if defined,
        which will proccess this data

        Args:
            data (Any): Data recieved
        """

        if not self._callback_exist(data):
            return
        for cls, func in self._data_callbacks.items():
            if isinstance(data, cls):
                func(data)

    def _callback_exist(self, data: Any) -> bool:
        """Asset if for the recieved data type a callback has been
        defined in _data_callbacks dict.

        Args:
            data (Any): recieved data

        Returns:
            bool: return if a callbakc is available
        """
        return any(isinstance(data, cls) for cls in self._data_callbacks)

    def _check_is_init(self):
        """Check if the reciever has been initializated

        Raises:
            SignalRecieverNotInitializated: raised if not initializated.
        """
        if self._data_callbacks is None:
            raise SignalRecieverNotInitializated(
                "Please init the Status of the object before using it"
            )


################################################################################
# To gui channel
################################################################################


# class AddUpdateAgent(SignalReciever):
#     def __init__(self) -> None:
#         """Special SignalReciever for QT-based GUI update purpose.

#         It accepts only data of type "EventDataClass" used for the
#         update of a the gui.

#         The data are first safe in a buffer. An internal QThread retrieve the
#         data out of the buffer and post them in un update agent responsible of
#         updating the gui"""
#         super().__init__()
#         self.init_reciever(data_callbacks={EventDataClass: self.update_gui})
#         self._data_buffer = Queue(maxsize=2048)  # TODO maybe
#         self._update_agent = UpdateAgent(self, UPDATE_EVENTS)
#         self._worker = CustomWorker(name="update_gui", sleeptime=0.01)
#         self._worker.progress.connect(self._process_data_for_update)
#         self._worker.start()
#         self._worker.start_polling()

#     def update_gui(self, data: EventDataClass = None, **kwargs):
#         """Add data in input buffer

#         Args:
#             data (EventDataClass, optional): data to update gui . Defaults to None.
#         """
#         if data is not None:
#             self._data_buffer.put(data)

#     def _process_data_for_update(self) -> None:
#         """Retrieve EventDataClass out of the input buffer and post them via
#         UpdateAgent.
#         """
#         # self.handle_meas_status_change() # here for the momenet but optimal
#         if self._data_buffer.empty():
#             return
#         data = self._data_buffer.get(block=True)
#         # logger.debug(f'_process_data_for_update Update {data}')
#         self._update_agent.post(data)


class AddUpdateUiAgent(SignalReciever):
    def __init__(self) -> None:
        """Special SignalReciever for QT-based GUI update purpose.

        It accepts only data of type "EventDataClass" used for the
        update of a the gui.

        The data are first safe in a buffer. An internal QThread retrieve the
        data out of the buffer and post them in un update agent responsible of
        updating the gui"""
        super().__init__()
        self.init_reciever(data_callbacks={EventDataClass: self.update_gui})
        self._data_buffer = Queue(maxsize=2048)  # TODO maybe
        self._update_agent = None
        self._worker = CustomWorker(name="update_gui", sleeptime=0.01)
        self._worker.progress.connect(self._process_data_for_update)
        self._worker.start()
        self._worker.start_polling()

    def init_update_ui_agent(self, ui):
        self._update_agent = UpdateAgent(ui, UPDATE_EVENTS)

    def update_gui(self, data: EventDataClass = None, **kwargs):
        """Add data in input buffer

        Args:
            data (EventDataClass, optional): data to update gui . Defaults to None.
        """
        if data is not None:
            self._data_buffer.put(data)

    def _process_data_for_update(self) -> None:
        """Retrieve EventDataClass out of the input buffer and post them via
        UpdateAgent.
        """
        # self.handle_meas_status_change() # here for the momenet but optimal
        if self._data_buffer.empty() or self._update_agent is None:
            return
        data = self._data_buffer.get(block=True)
        # logger.debug(f'_process_data_for_update Update {data}')
        self._update_agent.post(data)
