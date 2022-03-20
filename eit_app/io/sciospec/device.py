#!C:\Anaconda3\envs\py38_app python
# -*- coding: utf-8 -*-

"""  Classes and function to interact with the Sciospec EIT device

Copyright (C) 2021  David Metz

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>. """


from dataclasses import dataclass
from enum import Enum, auto
from logging import getLogger
from queue import Queue
from time import sleep
from typing import Any, Union

from glob_utils.msgbox import infoMsgBox, warningMsgBox, errorMsgBox
# from eit_app.update_event import DevStatus
from eit_app.io.sciospec.com_constants import (ACK_FRAME, CMD_BYTE_INDX,
                                               CMD_GET_DEVICE_INFOS,
                                               CMD_GET_ETHERNET_CONFIG,
                                               CMD_GET_MEAS_SETUP,
                                               CMD_GET_OUTPUT_CONFIG,
                                               CMD_SET_ETHERNET_CONFIG,
                                               CMD_SET_MEAS_SETUP,
                                               CMD_SET_OUTPUT_CONFIG,
                                               CMD_SOFT_RESET,
                                               CMD_START_STOP_MEAS, NONE_ACK,
                                               OP_BURST_COUNT,
                                               OP_CURRENT_STAMP, OP_DHCP,
                                               OP_EXC_AMPLITUDE,
                                               OP_EXC_FREQUENCIES,
                                               OP_EXC_PATTERN, OP_EXC_STAMP,
                                               OP_FRAME_RATE, OP_IP_ADRESS,
                                               OP_MAC_ADRESS, OP_NULL,
                                               OP_RESET_SETUP, OP_START_MEAS,
                                               OP_STOP_MEAS, OP_TIME_STAMP,
                                               OPTION_BYTE_INDX, SCIOSPEC_ACK,
                                               Answer, SciospecAck,
                                               SciospecCmd, SciospecOption,
                                               build_cmd_frame, is_start_meas,
                                               is_stop_meas)
from eit_app.io.sciospec.interface import Interface, SciospecSerialInterface
from eit_app.io.sciospec.setup import SciospecSetup
from glob_utils.flags.flag import CustomFlag, CustomTimer, MultiStatewSignal
from glob_utils.log.log import main_log
from glob_utils.pth.path_utils import get_datetime_s
from glob_utils.thread_process.buffer import BufferList
from glob_utils.thread_process.signal import Signal
from glob_utils.thread_process.threads_worker import Poller
from serial import (  # get from http://pyserial.sourceforge.net/
    PortNotOpenError, SerialException)

from eit_app.update_event import DevAvailables, DevSetup, DevStatus, FrameProgress, LiveStatus

__author__ = "David Metz"
__copyright__ = "Copyright (c) 2021"
__credits__ = ["David Metz"]
__license__ = "GPLv3"
__version__ = "2.0.0"
__maintainer__ = "David Metz"
__email__ = "d.metz@tu-bs.de"
__status__ = "Production"

logger = getLogger(__name__)

NONE_DEVICE = "None Device"

class CommunicatorError(Exception):
    """"""

SUCCESS={
    True: 'SUCCESS',
    False: 'FAIL'
}

@dataclass
class TxCmdOpData:
    """Transmit Command/option data

    gather the transmitted cmd/op and tx_frame and
    the corresponding transmition time"""
    cmd:SciospecCmd
    op:SciospecOption
    tx_frame:list[bytes]
    time_stamp:str

    @property
    def info_long(self)->str:
        return f'TX_CMD : "{self.cmd.name}"/"{self.op.name}", tx_frame :{self.tx_frame} ({self.time_stamp})'
    @property
    def info(self)->str:
        return f'TX_CMD : "{self.cmd.name}"/"{self.op.name}" ({self.time_stamp})'

    def wait_ans_and_ack(self)->bool:
        return self.cmd.answer_type == Answer.WAIT_FOR_ANSWER_AND_ACK

    def wait_ack_only(self)->bool:
        return self.cmd.answer_type == Answer.WAIT_FOR_ACK

@dataclass
class RxRespData:
    """Recieves response data

    gather the recieved response and
    the corresponding recieving time"""
    rx_frame:list[bytes]
    time_stamp:str
    @property
    def info(self)->str:
        return f' RX_RESP : {self.rx_frame[:10]} ({self.time_stamp})'

################################################################################
## Class for Sciopec Device ####################################################
################################################################################

class StatusCommunicator(Enum):
    IDLE = "IDLE"
    WAIT_FOR_DEVICE = "WAIT_FOR_DEVICE"


class SciospecCommunicator:
    """ IOInterface Class provides
    - a sending method of cmd_frame and
    - a processing of the rx_frame 
    """

    def __init__( self)->None:
        """Constructor"""
        # self.queue_out_video_module = Queue()
        
        # self.queue_out = data2computation # Queue()
        # self.send_data4computation_func= send_data4computation_func
        self.rx_frame = Queue(maxsize=256)
        self.processor = Poller(
            name="process_rx_frame", pollfunc=self._process_last_rx_frame, sleeptime=0.01
        )
        self.processor.start()
        self.processor.start_polling()
        self.timer_busy = CustomTimer(5.0, 1)  # max 5s timeout!
        self.cmd_op_hist = BufferList()
        self.resp_hist = BufferList()

        self.new_rx_setup_stream = Signal(self)
        self.new_rx_meas_stream = Signal(self)
        self.status = StatusCommunicator.IDLE

        self.process_meas_enabled= CustomFlag()
        self.process_meas_enabled.clear()

    def _reinit(self)->None:
        """init the"""
        self.status = StatusCommunicator.IDLE
        # self.cmd_op_hist.clear()
        # self.resp_history.clear()


    def wait_not_busy(self) -> None :
        """Wait until the Communicator get all ack fro all commands send
        """
        self.timer_busy.reset()
        while self._is_waiting():
            logger.debug(f'waiting for device {self.timer_busy.cnt}/{self.timer_busy.max_cnt}')
            if self.timer_busy.increment():
                logger.error("Waiting device - Timeout")
                self._reinit()
            sleep(1)
    
    # def processing_activate(self, activate:bool=True):
    #     if activate:
    #         self.processor.start_polling()
    #     else:
    #         self.processor.stop_polling()
    
    def processing_meas_enable(self, cmd: SciospecCmd, op: SciospecOption):
        """Activate or deactivate the processing of measuremnet frame"""
        if is_start_meas(cmd, op):
            self.process_meas_enabled.set()
            # self._hold_listening
        elif is_stop_meas(cmd, op):
            self.process_meas_enabled.clear()

    ## =======================================================================
    ##  Sending of command cmd_frame
    ## =========================================================================

    def send_cmd_frame(self, interface:Interface, cmd: SciospecCmd, op: SciospecOption, data:list[bytes], cmd_append:bool=True)->bool:
        """Send a command frame to the device
        - build the cmd frame
        - write the cmd_frame to the interface
        - add the cmd and op in the history if its successfull"""

        # self.rx_ack = NONE_ACK  # clear last recieved acknolegment
        #TODO activate listening!
        self.processing_meas_enable(cmd, op)
        tx_frame = build_cmd_frame(cmd, op, data)
        
        tx_cmd= TxCmdOpData(cmd, op, tx_frame, get_datetime_s())
        success= interface.write(tx_frame)
        # s='SUCCESS' if success else "ERROR"
        if success:
            self.cmd_op_hist.add(tx_cmd)
            self.status = StatusCommunicator.WAIT_FOR_DEVICE
        logger.debug(f'{tx_cmd.info_long} - {SUCCESS[success]}')
        return success

    ## =========================================================================
    ##  Processing of rx_frame
    ## =========================================================================

    def add_rx_frame(self, rx_frame: list[bytes], **kwargs) -> None:
        """Add a recieved frame in the queue to be treated"""
        logger.debug(f"RX_Frame added to process: {rx_frame[:10]}")
        self.rx_frame.put_nowait(rx_frame)
    
    def empty_buf(self)->None:
        while not self.rx_frame.empty():
            self.rx_frame.get_nowait()

    # @catch_error
    def _process_last_rx_frame(self)->None:
        """Method polled by the processor to process all rx_frames one by one"""
        if self.rx_frame.empty():
            return
        rx_frame = self.rx_frame.get_nowait()
        self._process_rx_frame(rx_frame)
    
    def _process_rx_frame(self, rx_frame: list[bytes])->None:
        """Sort the recieved frames between ACKNOWLEGMENT, MEASURING, RESPONSE
        and process them accordingly"""
        rx_frame = self._check_rx_frame(rx_frame)
        if self._is_ack(rx_frame):
            self._process_rx_ack(rx_frame)
        elif self._is_meas(rx_frame):
            self._process_rx_meas(rx_frame)
        else:  # _is_resp
            self._process_rx_resp(rx_frame)

    def _check_rx_frame(self, rx_frame: list[bytes]):
        """Check the rx_frame, it len should be >= 4"""
        if len(rx_frame) < 4:
            raise CommunicatorError(f"The length of rx_frame: {rx_frame} is < 4")
        return rx_frame

    def _is_ack(self, rx_frame: list[bytes]) -> bool:
        """Return if rx_frame is an ACKNOWLEGMENT frame"""
        tmp = rx_frame[:]
        tmp[OPTION_BYTE_INDX] = 0
        return tmp == ACK_FRAME

    def _is_meas(self, rx_frame: list[bytes]) -> bool:
        """Return if rx_frame is a MEASURING frame"""
        return rx_frame[CMD_BYTE_INDX] == CMD_START_STOP_MEAS.tag

    def _process_rx_ack(self, rx_frame:list[bytes])->None:
        """Treat the recieved ACKNOWLEGMENT frame:
        - identify the ack
        - if NACK > raise error
        - if ACK the oldest cmd and oldest response are processed"""
        rx_ack = self._identify_ack(rx_frame)
        if rx_ack.is_nack():
            self._handle_nack(rx_ack)
        else:
            self._handle_ack(rx_ack)

    def _process_rx_meas(self, rx_frame:list[bytes])->None:
        """Treat the recieved MEASURING frame
        - process of the frame"""
        logger.debug(f"RX_MEAS: {rx_frame[:10]}")
        if self.process_meas_enabled.is_set():
            self._emit_rx_frame(rx_frame)

    def _process_rx_resp(self, rx_frame:list[bytes])->None:
        """Treat the recieved RESPONSE frame
        - add the response to the history (it will be treated after ack)"""
        resp=RxRespData(rx_frame, get_datetime_s())
        logger.debug(f"{resp.info}")
        self.resp_hist.add(resp)

    def _identify_ack(self, rx_frame:list[bytes]) -> SciospecAck:
        """return the corresponding SciospecAck object
        if not found in the list "ACKs", return "NONE_ACK""" ""
        rx_ack = NONE_ACK
        for ack_i in SCIOSPEC_ACK:
            if ack_i.ack_byte == rx_frame[OPTION_BYTE_INDX]:
                rx_ack = ack_i
                break
        logger.debug(f"RX_ACK: {rx_ack.name}, {rx_frame}")
        return rx_ack

    def _handle_nack(self,rx_ack:SciospecAck)-> None:
        """Handle NAck:
        -raise an error ... Handling of NACK is not implemented..."""
        msg = f"RX_NACK: {rx_ack.__dict__} - nothing implemented yet, to handle it!!!"
        logger.error(msg)
        raise CommunicatorError(msg)

    def _handle_ack(self, rx_ack:SciospecAck)->None:
        """Handle Ack:
        - get oldest cmd and tresponse out of the histories
        - process them
        """
        # logger.debug(f"{self.cmd_op_hist.buffer}")
        if self.cmd_op_hist.is_empty() :
            logger.debug(f"No CMD registered: {rx_ack.name} - IGNORED")
            return

        tx_cmd:TxCmdOpData = self.cmd_op_hist.pop_oldest()

        if tx_cmd.wait_ans_and_ack():
            if self.resp_hist.is_empty():
                logger.debug(f"SHOULD NOT HAPPEND ! resp_hist empty {rx_ack.name} - IGNORED")
                return
            rx_resp:RxRespData  = self.resp_hist.pop_oldest()
            msg = f"{rx_ack.name} of:\r\n{tx_cmd.info}\r\n{rx_resp.info} - SUCCESS"
            self._emit_rx_frame(rx_resp.rx_frame)

        elif tx_cmd.wait_ack_only():
            msg = f"{rx_ack.name} of:\r\n{tx_cmd.info} - SUCCESS"

        logger.debug(msg)
        self._update_status()

    def _emit_rx_frame(self, rx_frame: list[bytes]):
        """Emit the rx_frame via the new setup and new_meas signal """
        if not rx_frame:
            logger.warning("Tried to emit a empty rx_frame")
            return

        cmd_tag = rx_frame[CMD_BYTE_INDX]

        if cmd_tag == CMD_START_STOP_MEAS.tag: # a measurement frame
            kwargs= {"rx_meas_stream": rx_frame}
            logger.debug(f"RX_MEAS: {rx_frame} -  EMITTED")
            self.new_rx_meas_stream.fire(False, **kwargs)
        else: # a setup frame
            kwargs= {"rx_setup_stream": rx_frame}
            logger.debug(f"RX_RESPONSE: {rx_frame} -  EMITTED")
            self.new_rx_setup_stream.fire(False, **kwargs)

    def _update_status(self):
        if self.cmd_op_hist.is_empty():
            self.status = StatusCommunicator.IDLE

    def _is_waiting(self):
        return self.status == StatusCommunicator.WAIT_FOR_DEVICE

################################################################################

################################################################################

class MeasuringState(Enum):
    IDLE = 'IDLE'
    MEASURING = 'MEASURING'
    PAUSED = 'PAUSED'

# class StatusConnection(Enum):
#     NOT_CONNECTED = "NOT_CONNECTED"
#     CONNECTED = "CONNECTED"

################################################################################

################################################################################

class SciospecEITDevice:

    """Device Class should only provide simple function to use the device such:
    - get devices
    - connect
    - disconnect
    - start/pause/resume/stop meas
    - set/get setup
    - reset """

    def __init__(self, n_channel:int = 32):

        self.n_channel = n_channel # nb of Channel from the EIT device
        # all sciospec connected to local machine generated by self.get_devices
        self.sciospec_devices = {}
        # Actual name of the device
        self.device_name: str = NONE_DEVICE

        self.meas_status= MultiStatewSignal(list(MeasuringState))
        self.meas_status.change_state(MeasuringState.IDLE)
        
        self.setup = SciospecSetup(self.n_channel)
        self.serial_interface=SciospecSerialInterface()
        
        # The communicator is charged to send cmd to the interface, sort and
        # manage the comunitation (ack, etc). it dispatch the data recivied on 
        # two different Signals new_rx_meas_stream/new_rx_setup_stream
        self.communicator= SciospecCommunicator()

        # signal used to transmit new rx_meas_stream or cmd to dataset.
        self.to_dataset=Signal(self)
        # signal used to transmit update to the gui.
        self.to_gui=Signal(self)

        # all the errors from the interface are catch and send through this 
        # error signal, the error are then here handled. Some of then need 
        # action on the device itself
        self.serial_interface.error.connect(self._handle_interface_error)
        #send the new to be processed by the communicator
        self.serial_interface.new_rx_frame.connect(self.communicator.add_rx_frame)
        # output signal of the communicator
        self.communicator.new_rx_meas_stream.connect(self.emit_to_dataset)
        self.communicator.new_rx_setup_stream.connect(self.setup.set_data)
        self.meas_status.changed.connect(self.emit_meas_status)

    def emit_meas_status(self):
        self.update_gui(LiveStatus(self.meas_status.state))

    def update_gui(self, data):
        kwargs={"update_gui_data": data}
        self.to_dataset.fire(None, **kwargs)

    def emit_to_dataset(self, **kwargs):
        self.to_dataset.fire(None, **kwargs)
    
    def dataset_init_for_pause(self):
        kwargs={'reinit_4_pause': 'reinit_4_pause'} # value is not important
        self.to_dataset.fire(None, **kwargs)
        
    
    def _handle_interface_error(self, error, **kwargs):
        """"""
        if isinstance(error, PortNotOpenError):
            warningMsgBox(
                "no devices available",
                f"{error.__str__()}"
            )
            
        elif isinstance(error, SerialException):
            warningMsgBox(
                "Device not detected",
                f"{error.__str__()}"

            )
        #TODO handle of the disconnection of the device
        # if (
        #     self.device._not_connected()
        #     and self.device.status_prompt != self.lab_device_status.text()
        # ):
        #     self.update_gui(DevStatus(self.device.connected(), self.device.status_prompt))
        #     errorMsgBox(
        #         "Error: Device disconnected",
        #         "The device has been disconnected!"
        #     )
        #     self._refresh_device_list()
        # elif isinstance(error, OSError):
        #     pass

    @property
    def is_connected(self)->bool:
        return self.serial_interface.is_connected.is_set()

    @property
    def connect_prompt(self)->bool:
        return f'{self.device_name} - CONNECTED'

    def is_measuring(self)->bool:
        """"""
        # return self.is_connected.is_set(StatusConnection.MEASURING)

    ## =========================================================================
    ##  Methods on Comunicator
    ## =========================================================================    
    
    def send_communicator(self, cmd: SciospecCmd, op: SciospecOption) -> bool:
        """"""
        data= self.setup.get_data(cmd, op)
        return self.communicator.send_cmd_frame(self.serial_interface, cmd, op, data)
    
    # def listen_activate(self, activate:bool=True):
    #     """"""

    def check_nb_meas_reached(self, idx:int,**kwargs) -> None:
        """Check if the number of Burst(measurements) is reached,
        in that case the measurement mode will be stopped on the device
        
        should be Triggered from meas_dataset"""

        if not self.is_measuring():
            return
        burst = self.setup.get_burst()
        if burst > 0 and idx == burst:
            self.stop_meas()

    def _check_not_measuring(force_stop: bool = False):
        """Decorator: which check if the device is not measuring

        - if device is not measuring >> the function is run
        - if device is measuring:
            - the measurement can be stopped by setting force_stop to `True`. A 
            info msgBox will be popped to inform the user and the 
            function will be run
            - otherwise a info msgBox will be popped to ask the user to stop
            the measuremnet before using that function

        Args:
            force_stop (bool, optional): set to `True` to force the device to 
            run the function after stoping the measurements. Defaults to `False`.
        """
        def _wrap(func):
            def wrap(self, *args, **kwargs) -> Union[Any, None]:
                
                msg=None
                run_func = False
                if not self._is_measuring(): # if not measuring >> run func
                    run_func= True
                elif force_stop:
                    self.stop_meas()
                    msg= "Measurements have been stopped"
                    run_func= True
                else:
                    msg="Please stop measurements first"

                if msg: # show msg only if msg is not empty/None
                    infoMsgBox("Measurements still running!",msg)

                return func(self, *args, **kwargs) if run_func else None
               
            return wrap
        return _wrap
    ## =========================================================================
    ##  Connection with device
    ## =========================================================================
        
    @_check_not_measuring()
    def get_devices(self)->dict:
        """Lists the available Sciospec device is available
        - Device infos are ask and if an ack is get: it is a Sciospec device..."""
        ports = self.serial_interface.get_ports_available()
        self.sciospec_devices = {}
        for port in ports:
            device_name = self._check_is_sciospec_dev(port)
            if device_name is not None:
                self.sciospec_devices[device_name] = port
        logger.info(f"Sciospec devices available: {list(self.sciospec_devices)}")
        self.update_gui(DevAvailables(self.sciospec_devices))
        return self.sciospec_devices

    @_check_not_measuring()
    def connect_device(self, device_name: str= None, baudrate:int=None) -> bool:
        """Connect a sciopec device"""
        
        # (port:= self._get_sciospec_port(device_name))
        if (port:= self._get_sciospec_port(device_name)) is None:
            return False

        if (success:=self._connect_interface(port, baudrate)):        
            self.stop_meas()# in case that the device is still measuring!
            self.get_device_infos()

        self.device_name = device_name if success else NONE_DEVICE
        logger.info(f"Connection to device '{device_name}' - {SUCCESS[success]}")

        self.update_gui(DevStatus(self.is_connected, self.connect_prompt))
        return success

    @_check_not_measuring()
    def disconnect_device(self) -> None:
        """ Disconnect device"""
        if not self.is_connected:
            return
        self._disconnect_interface()
        logger.info(f'{self.device_name}" - DISCONNECTED')
        
        self.device_name = NONE_DEVICE
        # Some reinitializsation of internal objects after disconnection
        self.setup.reinit()
        self.serial_interface.reinit()
        
        self.update_gui(DevStatus(self.is_connected, self.connect_prompt))
        # self.get_devices()  # update the list of Sciospec devices available ????

    ## -------------------------------------------------------------------------
    ##  Internal methods
    ## -------------------------------------------------------------------------

    def _connect_interface(self, port: str= None, baudrate:int=None) -> bool:
        """Connect interface to port"""
        if not (success:= self.serial_interface.open(port, baudrate)):
            return False
        return success
            
    def _disconnect_interface(self) -> None:
        """ " Disconnect actual interface"""
        self.serial_interface.close()

    
    def _check_is_sciospec_dev(self, port) -> Union[str, None]:
        """Return a device name if the device presents on the port is a 
        sciospec device otherwise return `None`"""
        tmp_sn= self.setup.get_sn(in_bytes=True)
        device_name =  None
        self._connect_interface(port)
        self.get_device_infos()
        device_name = self.setup.build_sciospec_device_name(port)
        self._disconnect_interface()
        self.setup.set_sn(tmp_sn)
        return device_name
    
    def _get_sciospec_port(self, device_name: str)-> Union[str, None]:

        if not self.sciospec_devices:
            logger.warning('No Sciospec devices - DETECTED')
            warningMsgBox(
                'No Sciospec devices - DETECTED',
                "Please refresh the list of availables device first and retry!",
            )
            return None
        if device_name not in self.sciospec_devices:
            logger.error(f'Sciospec device "{device_name}" - NOT FOUND')
            errorMsgBox(
                "Sciospec device - NOT FOUND ",
                f'Please reconnect your device "{device_name}"',
            )
            return None
        return self.sciospec_devices[device_name]


    ## =========================================================================
    ##  Measurements with device
    ## =========================================================================
    
    @_check_not_measuring()
    def start_meas(self) -> bool:  # sourcery skip: class-extract-method
        """Start measurements"""
        success= self._start_meas()
        self.meas_status.change_state(MeasuringState.MEASURING)
        logger.info(f"Start Measurements - {SUCCESS[success]}")
        return success

    @_check_not_measuring()
    def resume_meas(self) -> bool:
        """resume measurements"""
        success= self._start_meas()
        self.meas_status.change_state(MeasuringState.MEASURING)
        logger.info(f"Resume Measurements - {SUCCESS[success]}")
        return success

    def pause_meas(self)-> None:
        """Pause measurements"""
        success= self._stop_meas()
        self.meas_status.change_state(MeasuringState.PAUSED)
        self.dataset_init_for_pause()
        logger.info(f"Pause Measurements - {SUCCESS[success]}")

    def stop_meas(self)-> None:
        """Stop measurements"""
        success= self._stop_meas()
        self.meas_status.change_state(MeasuringState.IDLE)
        logger.info(f"Stop Measurements - {SUCCESS[success]}")
        self.update_gui(FrameProgress( 0, 0))

    ## -------------------------------------------------------------------------
    ##  Internal methods
    ## -------------------------------------------------------------------------
        
    def _start_meas(self) -> bool:
        """Start measurements"""
        success = self.send_communicator(CMD_START_STOP_MEAS, OP_START_MEAS)
        self.communicator.wait_not_busy()
        return success

    def _stop_meas(self) -> bool:
        """Stop measurements"""
        success = self.send_communicator(CMD_START_STOP_MEAS, OP_STOP_MEAS)
        self.communicator.wait_not_busy()
        return success

    ## =========================================================================
    ##  Setup device
    ## =========================================================================
    
    @_check_not_measuring()
    def get_device_infos(self)-> None:
        """Ask for the serial nummer of the Device"""
        self.send_communicator(CMD_GET_DEVICE_INFOS, OP_NULL)
        self.communicator.wait_not_busy()
        self.update_gui()
        logger.debug(f' {self.setup.device_infos}')

    @_check_not_measuring()
    def set_setup(self, get_setup:bool=True)-> None:
        """Send the setup to the device"""
        logger.info("Setting device setup - start...")
        self.send_communicator(CMD_SET_OUTPUT_CONFIG, OP_EXC_STAMP)
        self.send_communicator(CMD_SET_OUTPUT_CONFIG, OP_CURRENT_STAMP)
        self.send_communicator(CMD_SET_OUTPUT_CONFIG, OP_TIME_STAMP)
        self.send_communicator(CMD_SET_ETHERNET_CONFIG, OP_DHCP)
        self.send_communicator(CMD_SET_MEAS_SETUP, OP_RESET_SETUP)
        self.send_communicator(CMD_SET_MEAS_SETUP, OP_EXC_AMPLITUDE)
        self.send_communicator(CMD_SET_MEAS_SETUP, OP_BURST_COUNT)
        self.send_communicator(CMD_SET_MEAS_SETUP, OP_FRAME_RATE)
        self.send_communicator(CMD_SET_MEAS_SETUP, OP_EXC_FREQUENCIES)
        for idx in range(len(self.setup.get_exc_pattern())):
            self.setup.set_exc_pattern_idx(idx)
            self.send_communicator(CMD_SET_MEAS_SETUP, OP_EXC_PATTERN)
        self.communicator.wait_not_busy()
        logger.info("Setting device setup - done")
        if get_setup:
            self.get_setup()

    @_check_not_measuring()
    def get_setup(self)-> None:
        """Get the setup of the device"""
        logger.info("Getting device setup - start...")
        self.send_communicator(CMD_GET_MEAS_SETUP, OP_EXC_AMPLITUDE)
        self.send_communicator(CMD_GET_MEAS_SETUP, OP_BURST_COUNT)
        self.send_communicator(CMD_GET_MEAS_SETUP, OP_FRAME_RATE)
        self.send_communicator(CMD_GET_MEAS_SETUP, OP_EXC_FREQUENCIES)
        self.send_communicator(CMD_GET_MEAS_SETUP, OP_EXC_PATTERN)
        self.send_communicator(CMD_GET_OUTPUT_CONFIG, OP_EXC_STAMP)
        self.send_communicator(CMD_GET_OUTPUT_CONFIG, OP_CURRENT_STAMP)
        self.send_communicator(CMD_GET_OUTPUT_CONFIG, OP_TIME_STAMP)
        self.send_communicator(CMD_GET_ETHERNET_CONFIG, OP_IP_ADRESS)
        self.send_communicator(CMD_GET_ETHERNET_CONFIG, OP_MAC_ADRESS)
        self.send_communicator(CMD_GET_ETHERNET_CONFIG, OP_DHCP)
        self.communicator.wait_not_busy()
        self.update_gui(DevSetup(self.setup))
        logger.info("Getting device setup - done")
    
    @_check_not_measuring()
    def software_reset(self)->None:
        """Sofware reset the device
        Notes: a restart is needed after this method"""
        logger.info("Softreset of device - start...")
        self.send_communicator(CMD_SOFT_RESET, OP_NULL)
        self.communicator.wait_not_busy()
        sleep(10)
        self.disconnect_device()
        self.update_gui(DevStatus(self.is_connected, self.connect_prompt))
        logger.info("Softreset of device - done")
        infoMsgBox("Device reset ","Reset done")

    def save_setup(self, dir: str = None)->None:
        self.setup.save(dir)

    def load_setup(self, dir: str = None)->None:
        self.setup.load(dir=dir)
        self.update_gui(DevSetup(self.setup))









if __name__ == "__main__":
    import sys

    from PyQt5.QtWidgets import QApplication

    # app = QApplication(sys.argv)
    print(SUCCESS[True])
    print(SUCCESS[False])

    meas_status= MultiStatewSignal(list(MeasuringState))
    meas_status.change_state(MeasuringState.IDLE)

    print(meas_status.state)

    # def print_e(**kwargs):
    #     print(f"{kwargs=}")

    # main_log()

    # dev = SciospecEITDevice()
    # dev.to_dataset.connect(print_e)
    # print('*+++++++++++++++++++++++++++++++++++++')
    # dev.get_devices()
    # print('*+++++++++++++++++++++++++++++++++++++')
    # dev.connect_device('Device (SN: 01-0019-0132-0A0C) on "COM3"')
    # print('*+++++++++++++++++++++++++++++++++++++')
    # dev.get_setup()
    # print('*+++++++++++++++++++++++++++++++++++++')
    # dev.set_setup()
    # print('*+++++++++++++++++++++++++++++++++++++')
    # dev.start_meas()
    # print('*+++++++++++++++++++++++++++++++++++++')
    # sleep(1)
    # dev.pause_meas()
    # print('*+++++++++++++++++++++++++++++++++++++')
    # sleep(1)
    # dev.resume_meas()
    # print('*+++++++++++++++++++++++++++++++++++++')
    # sleep(1)
    # dev.stop_meas()
    # print('*+++++++++++++++++++++++++++++++++++++')
    # dev.disconnect_device()
    # print('*+++++++++++++++++++++++++++++++++++++')
    # dev.get_devices()


    