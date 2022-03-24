from abc import ABC
from dataclasses import dataclass, field
from queue import Queue
from typing import Any, Callable, Union

from glob_utils.thread_process.signal import Signal
from glob_utils.thread_process.signal import Signal
from glob_utils.thread_process.threads_worker import CustomWorker, Poller
import numpy as np
from eit_app.sciospec.setup import SciospecSetup
from eit_app.update_gui import UPDATE_EVENTS, EventDataClass, UpdateAgent


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
    to_plot: Signal  # use to transmit new rx_meas_stream or cmd to dataset.

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
    to_replay: Signal  # use to transmit new rx_meas_stream or cmd to dataset.

    def __init__(self):
        super().__init__()
        self.to_replay = Signal(self)


################################################################################
# To Computation Signal
################################################################################


@dataclass
class Data2Compute:
    v_ref: np.ndarray = None
    v_meas: np.ndarray = None
    labels: list = None


class AddToComputationSignal(object):
    to_computation: Signal  # use to transmit new rx_meas_stream or cmd to dataset.

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


class AddToDatasetSignal(object):
    to_dataset: Signal  # use to transmit new rx_meas_stream or cmd to dataset.

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
class DataSetStatusWMeas:
    meas_status_dev: bool


@dataclass
class DataSetStatusWReplay:
    replay_status: bool


class AddToCaptureSignal(object):
    to_capture: Signal  # use to transmit new rx_meas_stream or cmd to dataset.

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
    to_device: Signal  # use to transmit new rx_meas_stream or cmd to dataset.

    def __init__(self):
        super().__init__()
        self.to_device = Signal(self)


class SignalRecieverNotInitializated(BaseException):
    """"""


class SignalReciever(object):

    _data_callbacks = list

    def __init__(self) -> None:
        super().__init__()
        self._data_callbacks = None

    def init_reciever(self, data_callbacks: dict[type, Callable]) -> None:
        self._data_callbacks = data_callbacks

    def to_reciever(self, data: Any = None, **kwargs) -> None:
        """Consider only data as 1st arg or as kwargs"""
        self._check_is_init()
        if (data := self._check_data(data)) is not None:
            self._reciever_process_data(data)

    def _reciever_process_data(self, data: Any) -> None:
        """"""
        for cls, func in self._data_callbacks.items():
            if isinstance(data, cls):
                func(data)

    def _check_data(self, data: Any) -> Union[Any, None]:

        if not any(isinstance(data, cls) for cls in self._data_callbacks):
            print()
            return None

        return data

    def _check_is_init(self):
        if self._data_callbacks is None:
            raise SignalRecieverNotInitializated(
                "Please init the Status of the object before using it"
            )


################################################################################
# Update gui channel
################################################################################


class AddToGuiSignal(object):
    """Object contained in a sbcalss of GuiWithUpdateAgent should be sub class
    of ObjWithSignalToGui by emiting

    note that in the gui the signal should be connected to ""
    gui.obj.to_gui.connect(gui.update_gui)"""

    def __init__(self):
        super().__init__()
        self.to_gui = Signal(self)


class AddUpdateAgent(SignalReciever):
    """Base Class for Gui"""

    def __init__(self) -> None:
        """Start all threads used for the GUI"""
        super().__init__()
        self.init_reciever(data_callbacks={EventDataClass: self.update_gui})
        self._data_for_update = Queue(maxsize=256)  # TODO maybe
        self._update_agent = UpdateAgent(self, UPDATE_EVENTS)
        # self.processor = Poller(
        #     name="update_gui",
        #     pollfunc=self._process_data_for_update,
        #     sleeptime=0.5,
        # )
        # self.processor.start()
        # self.processor.start_polling()

        self._worker = CustomWorker(name="update_gui", sleeptime=0.05)
        self._worker.progress.connect(self._process_data_for_update)
        self._worker.start()
        self._worker.start_polling()

    def update_gui(self, data: EventDataClass = None, **kwargs):
        """Add data to the queue data_for_update in order to update the gui

        Args:
            data (EventDataClass, optional): should be a an EvtDataclass . Defaults to None.
        """
        if data is not None:
            # logger.debug('add update_gui_data')
            self._data_for_update.put(data)

    def _process_data_for_update(self) -> None:
        """Post update event if the queue data_for_update contain some data."""
        # self.handle_meas_status_change() # here for the momenet but optimal
        if self._data_for_update.empty():
            return
        data = self._data_for_update.get(block=True)
        # logger.debug(f'_process_data_for_update Update {data}')
        self._update_agent.post_event_data(data)
