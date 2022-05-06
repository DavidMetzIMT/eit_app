from dataclasses import dataclass
from enum import Enum
import logging
from queue import Queue
from time import sleep
from eit_app.sciospec.constants import (
    ACK_FRAME,
    CMD_BYTE_INDX,
    SUCCESS,
    CMD_START_STOP_MEAS,
    NONE_ACK,
    OPTION_BYTE_INDX,
    SCIOSPEC_ACK,
    Answer,
    SciospecAck,
    SciospecCmd,
    SciospecOption,
    build_cmd_frame,
    is_start_meas,
    is_stop_meas,
)
from eit_app.sciospec.interface import Interface
from glob_utils.flags.flag import CustomFlag
from glob_utils.flags.timer import CustomTimer
from glob_utils.directory.utils import get_datetime_s
from glob_utils.thread_process.buffer import BufferList
from glob_utils.thread_process.signal import Signal
from glob_utils.thread_process.threads_worker import Poller

logger = logging.getLogger(__name__)


class CommunicatorError(Exception):
    """"""


@dataclass
class TxCmdOpData:
    """Transmit Command/option data

    gather the transmitted cmd/op and tx_frame and
    the corresponding transmition time"""

    cmd: SciospecCmd
    op: SciospecOption
    tx_frame: list[bytes]
    time_stamp: str

    @property
    def info_long(self) -> str:
        return f'TX_CMD : "{self.cmd.name}"/"{self.op.name}", tx_frame :{self.tx_frame} ({self.time_stamp})'

    @property
    def info(self) -> str:
        return f'TX_CMD : "{self.cmd.name}"/"{self.op.name}" ({self.time_stamp})'

    def wait_ans_and_ack(self) -> bool:
        return self.cmd.answer_type == Answer.WAIT_FOR_ANSWER_AND_ACK

    def wait_ack_only(self) -> bool:
        return self.cmd.answer_type == Answer.WAIT_FOR_ACK


@dataclass
class RxRespData:
    """Recieves response data

    gather the recieved response and
    the corresponding recieving time"""

    rx_frame: list[bytes]
    time_stamp: str

    @property
    def info(self) -> str:
        return f" RX_RESP : {self.rx_frame[:10]} ({self.time_stamp})"


################################################################################
## Class for Sciopec Device ####################################################
################################################################################


class StatusCommunicator(Enum):
    IDLE = "IDLE"
    WAIT_FOR_DEVICE = "WAIT_FOR_DEVICE"


class SciospecCommunicator:  # TODO >> AddStatus
    """IOInterface Class provides
    - a sending method of cmd_frame and
    - a processing of the rx_frame
    """

    def __init__(self) -> None:
        """Constructor"""
        self.rx_frame = Queue(maxsize=2048)
        self.processor = Poller(
            name="process_rx_frame",
            pollfunc=self._process_last_rx_frame,
            sleeptime=0.01,
        )
        self.processor.start()
        self.processor.start_polling()
        self.timer_busy = CustomTimer(5.0, 1)  # max 5s timeout! #TODO >> Timer??

        self.cmd_op_hist = BufferList()
        self.resp_hist = BufferList()

        self.new_rx_setup_stream = Signal(self)
        self.new_rx_meas_stream = Signal(self)
        self.status = StatusCommunicator.IDLE

        self.process_meas_enabled = CustomFlag()
        self.process_meas_enabled.clear()

    def reinit(self) -> None:
        """Reinit the communicator"""
        self.status = StatusCommunicator.IDLE
        self.cmd_op_hist.clear()
        self.resp_hist.clear()

    def wait_not_busy(self) -> None:
        """Wait until the Communicator get all ack fro all commands send"""
        self.timer_busy.reset()
        while self.is_waiting():
            logger.debug(
                f"waiting for device {self.timer_busy.cnt}/{self.timer_busy.max_cnt}"
            )
            if self.timer_busy.increment():
                logger.error("Waiting device - Timeout")
                self.reinit()
            sleep(1)

    def processing_meas_enable(self, cmd: SciospecCmd, op: SciospecOption):
        """Activate or deactivate the processing of measuremnet frame"""
        # if is_start_meas(cmd, op):
        self.process_meas_enabled.set(not is_stop_meas(cmd, op))
        # elif is_stop_meas(cmd, op):
        #     self.process_meas_enabled.clear()

    ## =======================================================================
    ##  Sending of command cmd_frame
    ## =========================================================================

    def send_cmd_frame(
        self,
        interface: Interface,
        cmd: SciospecCmd,
        op: SciospecOption,
        data: list[bytes],
        cmd_append: bool = True,
    ) -> bool:
        """Send a command frame to the device
        - build the cmd frame
        - write the cmd_frame to the interface
        - add the cmd and op in the history if its successfull"""

        # TODO activate listening!
        self.processing_meas_enable(cmd, op)
        tx_frame = build_cmd_frame(cmd, op, data)

        tx_cmd = TxCmdOpData(cmd, op, tx_frame, get_datetime_s())
        success = interface.write(tx_frame)
        # s='SUCCESS' if success else "ERROR"
        if success:
            self.cmd_op_hist.add(tx_cmd)
            self.status = StatusCommunicator.WAIT_FOR_DEVICE
        logger.debug(f"{tx_cmd.info_long} - {SUCCESS[success]}")
        return success

    ## =========================================================================
    ##  Processing of rx_frame
    ## =========================================================================

    def add_rx_frame(self, rx_frame: list[bytes], **kwargs) -> None:
        """Add a recieved frame in the queue to be treated"""
        logger.debug(f"RX_Frame added to process: {rx_frame[:10]}")
        self.rx_frame.put_nowait(rx_frame)

    # @catch_error
    def _process_last_rx_frame(self) -> None:
        """Method polled by the processor to process all rx_frames one by one"""
        if self.rx_frame.empty():
            return
        rx_frame = self.rx_frame.get_nowait()
        self._process_rx_frame(rx_frame)

    def _process_rx_frame(self, rx_frame: list[bytes]) -> None:
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

    def _process_rx_ack(self, rx_frame: list[bytes]) -> None:
        """Treat the recieved ACKNOWLEGMENT frame:
        - identify the ack
        - if NACK > raise error
        - if ACK the oldest cmd and oldest response are processed"""
        rx_ack = self._identify_ack(rx_frame)
        if rx_ack.is_nack():
            self._handle_nack(rx_ack)
        else:
            self._handle_ack(rx_ack)

    def _process_rx_meas(self, rx_frame: list[bytes]) -> None:
        """Treat the recieved MEASURING frame
        - process of the frame"""
        if self.process_meas_enabled.is_set():
            logger.debug(f"RX_MEAS: {rx_frame[:10]}")
            self._emit_rx_frame(rx_frame)

    def _process_rx_resp(self, rx_frame: list[bytes]) -> None:
        """Treat the recieved RESPONSE frame
        - add the response to the history (it will be treated after ack)"""
        resp = RxRespData(rx_frame, get_datetime_s())
        logger.debug(f"{resp.info}")
        self.resp_hist.add(resp)

    def _identify_ack(self, rx_frame: list[bytes]) -> SciospecAck:
        """return the corresponding SciospecAck object
        if not found in the list "ACKs", return "NONE_ACK""" ""
        rx_ack = NONE_ACK
        for ack_i in SCIOSPEC_ACK:
            if ack_i.ack_byte == rx_frame[OPTION_BYTE_INDX]:
                rx_ack = ack_i
                break
        logger.debug(f"RX_ACK: {rx_ack.name}, {rx_frame}")
        return rx_ack

    def _handle_nack(self, rx_ack: SciospecAck) -> None:
        """Handle NAck:
        -raise an error ... Handling of NACK is not implemented..."""
        msg = f"RX_NACK: {rx_ack.__dict__} - nothing implemented yet, to handle it!!!"
        logger.error(msg)
        raise CommunicatorError(msg)

    def _handle_ack(self, rx_ack: SciospecAck) -> None:
        """Handle Ack:
        - get oldest cmd and tresponse out of the histories
        - process them
        """
        # logger.debug(f"{self.cmd_op_hist.buffer}")
        if self.cmd_op_hist.is_empty():
            logger.debug(f"No CMD registered: {rx_ack.name} - IGNORED")
            return

        tx_cmd: TxCmdOpData = self.cmd_op_hist.pop_oldest()

        if tx_cmd.wait_ans_and_ack():
            if self.resp_hist.is_empty():
                logger.debug(
                    f"SHOULD NOT HAPPEND ! resp_hist empty {rx_ack.name} - IGNORED"
                )
                return
            rx_resp: RxRespData = self.resp_hist.pop_oldest()
            msg = f"{rx_ack.name} of:\r\n{tx_cmd.info}\r\n{rx_resp.info} - SUCCESS"
            self._emit_rx_frame(rx_resp.rx_frame)

        elif tx_cmd.wait_ack_only():
            msg = f"{rx_ack.name} of:\r\n{tx_cmd.info} - SUCCESS"

        logger.debug(msg)
        self._update_status()

    def _emit_rx_frame(self, rx_frame: list[bytes]):
        """Emit the rx_frame via the new setup and new_meas signal"""
        if not rx_frame:
            logger.warning("Tried to emit a empty rx_frame")
            return

        cmd_tag = rx_frame[CMD_BYTE_INDX]

        if cmd_tag == CMD_START_STOP_MEAS.tag:  # a measurement frame
            kwargs = {"rx_meas_stream": rx_frame}
            logger.debug(f"RX_MEAS: {rx_frame[:10]} -  EMITTED")
            self.new_rx_meas_stream.emit(**kwargs)
        else:  # a setup frame
            kwargs = {"rx_setup_stream": rx_frame}
            logger.debug(f"RX_RESPONSE: {rx_frame[:10]} -  EMITTED")
            self.new_rx_setup_stream.emit(**kwargs)

    def _update_status(self):
        """Change the status to the commands history and c"""
        if self.cmd_op_hist.is_empty():
            self.status = StatusCommunicator.IDLE

    def is_waiting(self):
        """Asset if the comunicator is waiting for the device"""
        return self.status == StatusCommunicator.WAIT_FOR_DEVICE


if __name__ == "__main__":
    """"""
