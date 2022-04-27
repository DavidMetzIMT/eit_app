from dataclasses import dataclass, field
from enum import Enum, auto

################################################################################
##  Diverse CONSTANTS for Sciopec device #######################################
################################################################################

SUCCESS = {True: "SUCCESS", False: "FAIL"}


FRAME_LENGTH_MIN = 4
CMD_BYTE_INDX = 0
LENGTH_BYTE_INDX = 1
OPTION_BYTE_INDX = 2
DATA_START_INDX = 3
LENGTH_SERIAL_NUMBER = 7
LENGTH_IP_ADRESS = 4
LENGTH_MAC_ADRESS = 6

DELAY_BTW_2FREQ = 42 * 10**-6  # in s
MIN_SAMPLING_TIME = 208 * 10**-6  # in s
DELAY_BTW_2INJ = 651 * 10**-6  # in s
UPPER_LIMIT_FRAME_RATE = 100  # in fps


class Answer(Enum):
    WAIT_FOR_ANSWER_AND_ACK = auto()
    WAIT_FOR_ACK = auto()


class CmdTypes(Enum):
    simple = auto()
    set_w_option = auto()
    get_w_option = auto()


################################################################################
##  Class of commands and options for the Sciospec device
################################################################################


@dataclass
class SciospecCmd(object):
    """Command structure description:
    name: str

    tag_byte: CMD Byte

    type:   0 simple set/get/ask command without option
            1 set command with options
            2 get command with options
    """

    name: str = ""
    tag: bytes = 0x00
    type: int = CmdTypes.simple
    answer_type: int = Answer.WAIT_FOR_ACK
    options: list = field(default_factory=lambda: [])

    def set_options(self, options: list = None) -> None:
        if isinstance(options, list):
            self.options = options

    def is_set_cmd(self):
        return self.type == CmdTypes.set_w_option


@dataclass
class SciospecOption(object):
    """Option structure description:

    name: str

    tag: OB Byte

    LL_byte:
        length_byte[0] lenght Byte for set command with options
        length_byte[1] lenght Byte for get command with options

    """

    name: str = ""
    tag: bytes = 0x00
    LL_bytes: list[bytes] = field(default_factory=lambda: [0x00, 0x00])


################################################################################
##  Commands and options CONSTANTS for the Sciospec device
################################################################################

## -----------------------------------------------------------------------------
## Save Settings - 0x90
CMD_SAVE_SETTINGS = SciospecCmd(
    "CMD_Save_Settings", 0x90, CmdTypes.simple, Answer.WAIT_FOR_ACK
)
# Options for "Save_Settings"
OP_NULL = SciospecOption("OP_Null", 0x00, [0x00, 0x00])
CMD_SAVE_SETTINGS.set_options([OP_NULL])

## -----------------------------------------------------------------------------
## Software Reset - 0xA1
CMD_SOFT_RESET = SciospecCmd(
    "CMD_Software_Reset", 0xA1, CmdTypes.simple, Answer.WAIT_FOR_ACK
)
# Options for "Save_Settings"
CMD_SOFT_RESET.set_options([OP_NULL])

## -----------------------------------------------------------------------------
## Set_Measurement_Setup - 0xB0 / Get_Measurement_Setup - 0xB1
CMD_SET_MEAS_SETUP = SciospecCmd(
    "CMD_Set_Measurement_Setup", 0xB0, CmdTypes.set_w_option, Answer.WAIT_FOR_ACK
)
CMD_GET_MEAS_SETUP = SciospecCmd(
    "CMD_Get_Measurement_Setup",
    0xB1,
    CmdTypes.get_w_option,
    Answer.WAIT_FOR_ANSWER_AND_ACK,
)
# Options for "Set_Measurement_Setup"/"Get_Measurement_Setup"
OP_RESET_SETUP = SciospecOption("OP_Reset_Setup", 0x01, [0x01, 0x00])
OP_BURST_COUNT = SciospecOption("OP_Burst_Count", 0x02, [0x03, 0x01])
OP_FRAME_RATE = SciospecOption("OP_Frame_Rate", 0x03, [0x05, 0x01])
OP_EXC_FREQUENCIES = SciospecOption("OP_Excitation_Frequencies", 0x04, [0x0C, 0x01])
OP_EXC_AMPLITUDE_DOUBLE = SciospecOption(
    "OP_Excitation_Amplitude_double", 0x05, [0x09, 0x01]
)  # Double Precision
OP_EXC_AMPLITUDE = SciospecOption(
    "OP_Excitation_Amplitude", 0x05, [0x05, 0x01]
)  # Single Precision
OP_EXC_PATTERN = SciospecOption("OP_Excitation_Sequence", 0x06, [0x03, 0x01])
OP_ACTIVE_GUARD = SciospecOption("OP_Active_Guard", 0x07, [0x01, 0x01])

OP_LINEAR = SciospecOption("LINEAR", 0x00, [0x00, 0x00])
OP_LOG = SciospecOption("LOG", 0x01, [0x00, 0x00])

used_ops = [
    OP_RESET_SETUP,
    OP_BURST_COUNT,
    OP_FRAME_RATE,
    OP_EXC_FREQUENCIES,
    OP_EXC_AMPLITUDE,
    OP_EXC_PATTERN,
]
CMD_SET_MEAS_SETUP.set_options(used_ops)
CMD_GET_MEAS_SETUP.set_options(used_ops[1:])
## -----------------------------------------------------------------------------
## Set_Output_Configuration - 0xB2 / Get_Output_Configuration - 0xB3
CMD_SET_OUTPUT_CONFIG = SciospecCmd(
    "CMD_Set_Output_Configuration", 0xB2, CmdTypes.set_w_option, Answer.WAIT_FOR_ACK
)
CMD_GET_OUTPUT_CONFIG = SciospecCmd(
    "CMD_Get_Output_Configuration",
    0xB3,
    CmdTypes.get_w_option,
    Answer.WAIT_FOR_ANSWER_AND_ACK,
)
# Options for "Set_Output_Configuration"/"Get_Output_Configuration"
OP_EXC_STAMP = SciospecOption("OP_Excitation_Setting", 0x01, [0x02, 0x01])
OP_CURRENT_STAMP = SciospecOption("OP_Current_Row", 0x02, [0x02, 0x01])
OP_TIME_STAMP = SciospecOption("OP_Timestamp", 0x03, [0x02, 0x01])
CMD_SET_OUTPUT_CONFIG.set_options([OP_EXC_STAMP, OP_CURRENT_STAMP, OP_TIME_STAMP])
CMD_GET_OUTPUT_CONFIG.set_options([OP_EXC_STAMP, OP_CURRENT_STAMP, OP_TIME_STAMP])
## -----------------------------------------------------------------------------
## Start_Stop_Measurement - 0xB4
CMD_START_STOP_MEAS = SciospecCmd(
    "CMD_Start_Stop_Measurement", 0xB4, CmdTypes.set_w_option, Answer.WAIT_FOR_ACK
)
# Options for "Start_Stop_Measurement"
OP_STOP_MEAS = SciospecOption("OP_Stop_Measurement", 0x00, [0x01, 0x00])
OP_START_MEAS = SciospecOption("OP_Start_Measurement", 0x01, [0x01, 0x00])
CMD_START_STOP_MEAS.set_options([OP_START_MEAS, OP_STOP_MEAS])
## -----------------------------------------------------------------------------
## Set_Ethernet_Configuration - 0xBD / Get_Ethernet_Configuration - 0xBE
CMD_SET_ETHERNET_CONFIG = SciospecCmd(
    "CMD_Set_Ethernet_Configuration", 0xBD, CmdTypes.set_w_option, Answer.WAIT_FOR_ACK
)  # NOT USED
CMD_GET_ETHERNET_CONFIG = SciospecCmd(
    "CMD_Get_Ethernet_Configuration",
    0xBE,
    CmdTypes.get_w_option,
    Answer.WAIT_FOR_ANSWER_AND_ACK,
)
# Options for "Set_Ethernet_Configuration/Get_Ethernet_Configuration"
OP_IP_ADRESS = SciospecOption(
    "OP_IP_adress", 0x01, [0x05, 0x01]
)  # set get Static IP adress
OP_MAC_ADRESS = SciospecOption(
    "OP_MAC_adress", 0x02, [0x00, 0x01]
)  # only get Mac adress
OP_DHCP = SciospecOption("OP_DHCP", 0x03, [0x02, 0x01])  # activate/deactivate DHCP
CMD_SET_ETHERNET_CONFIG.set_options([OP_IP_ADRESS, OP_MAC_ADRESS, OP_DHCP])
CMD_GET_ETHERNET_CONFIG.set_options([OP_IP_ADRESS, OP_MAC_ADRESS, OP_DHCP])
## -----------------------------------------------------------------------------
## Set_ExtPort_Channel - 0xC2 / Get_ExtPort_Channel - 0xC3
CMD_SET_EXPORT_CHANNEL = SciospecCmd(
    "CMD_Set_ExtPort_Channel", 0xC2, CmdTypes.set_w_option, Answer.WAIT_FOR_ACK
)  # NOT USED
CMD_GET_EXPORT_CHANNEL = SciospecCmd(
    "CMD_Get_ExtPort_Channel", 0xC3, CmdTypes.simple, Answer.WAIT_FOR_ANSWER_AND_ACK
)  # NOT USED
# Options for "Set_ExtPort_Channel /Get_ExtPort_Channel "
OP_CH_1_16_NOT_CONNECTED = SciospecOption(
    "OP_Ch_1_16_not_connected", 0x00, [0x01, 0x01]
)  # set get Static IP adress # NOT USED
OP_CH_1_16_CONNECTED_PORT1 = SciospecOption(
    "OP_Ch_1_16_connected_Port1", 0x01, [0x01, 0x01]
)  # only get Mac adress # NOT USED
OP_CH_1_16_CONNECTED_PORT2 = SciospecOption(
    "OP_Ch_1_16_connected_Port2", 0x02, [0x01, 0x01]
)  # activate/deactivate DHCP # NOT USED
OP_CH_1_16_CONNECTED_PORT3 = SciospecOption(
    "OP_Ch_1_16_connected_Port3", 0x03, [0x01, 0x01]
)  # activate/deactivate DHCP # NOT USED
CMD_SET_EXPORT_CHANNEL.set_options(
    [
        OP_CH_1_16_NOT_CONNECTED,
        OP_CH_1_16_CONNECTED_PORT1,
        OP_CH_1_16_CONNECTED_PORT2,
        OP_CH_1_16_CONNECTED_PORT3,
    ]
)
CMD_GET_EXPORT_CHANNEL.set_options([OP_NULL])

## -----------------------------------------------------------------------------
## Get_ExtPort_Module - 0xC5
CMD_GET_EXPORT_MODULE = SciospecCmd(
    "CMD_Get_ExtPort_Module", 0xC5, CmdTypes.simple, Answer.WAIT_FOR_ANSWER_AND_ACK
)  # NOT USED
# Options for "Get_ExtPort_Module"
CMD_GET_EXPORT_MODULE.set_options([OP_NULL])
## -----------------------------------------------------------------------------
## Set_Battery_Control - 0xC6 / Get_Battery_Control - 0xC7
CMD_SET_BATTERY_CONTROL = SciospecCmd(
    "CMD_Set_Battery_Control", 0xC6, CmdTypes.set_w_option, Answer.WAIT_FOR_ACK
)  # NOT USED
CMD_GET_BATTERY_CONTROL = SciospecCmd(
    "CMD_Get_Battery_Control",
    0xC7,
    CmdTypes.get_w_option,
    Answer.WAIT_FOR_ANSWER_AND_ACK,
)  # NOT USED
# Options for "Set_Battery_Control /Get_Battery_Control "
OP_BATTERY_STATUS = SciospecOption("OP_Battery_Status", 0x01, [0x01, 0x01])  # NOT USED
OP_BATTERY_MODE = SciospecOption("OP_Battery_mode", 0x02, [0x02, 0x01])  # NOT USED
OP_BATTERY_MIN_CAPACITY = SciospecOption(
    "OP_Battery_min_capacity", 0x03, [0x02, 0x01]
)  # NOT USED
CMD_SET_BATTERY_CONTROL.set_options(
    [OP_BATTERY_STATUS, OP_BATTERY_MODE, OP_BATTERY_MIN_CAPACITY]
)
CMD_SET_BATTERY_CONTROL.set_options(
    [OP_BATTERY_STATUS, OP_BATTERY_MODE, OP_BATTERY_MIN_CAPACITY]
)
## -----------------------------------------------------------------------------
## Set_LED_Control - 0xC8 / Get_LED_Control - 0xC9
CMD_SET_LED_CONTROL = SciospecCmd(
    "CMD_Set_LED_Control", 0xC8, CmdTypes.set_w_option, Answer.WAIT_FOR_ACK
)  # NOT USED
CMD_GET_LED_CONTROL = SciospecCmd(
    "CMD_Get_LED_Control", 0xC9, CmdTypes.get_w_option, Answer.WAIT_FOR_ANSWER_AND_ACK
)  # NOT USED
# Options for "Set_ExtPort_Channel /Get_ExtPort_Channel "
OP_AUTOMODE_ON_OFF = SciospecOption(
    "OP_Automode_on_off ", 0x01, [0x02, 0x01]
)  # set get Static IP adress # NOT USED
OP_STATUS_LED = SciospecOption(
    "OP_Status_LED", 0x02, [0x02, 0x02]
)  # set get Static IP adress # NOT USED
OP_MANUAL_LED = SciospecOption(
    "OP_manual_LED", 0x03, [0x03, 0x01]
)  # only get Mac adress # NOT USED

CMD_SET_LED_CONTROL.set_options([OP_AUTOMODE_ON_OFF, OP_STATUS_LED, OP_MANUAL_LED])
CMD_GET_LED_CONTROL.set_options([OP_AUTOMODE_ON_OFF, OP_STATUS_LED, OP_MANUAL_LED])

## -----------------------------------------------------------------------------
## Device_Serial_Number - 0xD1
CMD_GET_DEVICE_INFOS = SciospecCmd(
    "CMD_Device_Serial_Number", 0xD1, CmdTypes.simple, Answer.WAIT_FOR_ANSWER_AND_ACK
)
# Options for "Device_Serial_Number"
CMD_GET_DEVICE_INFOS.set_options([OP_NULL])
## -----------------------------------------------------------------------------
# Set_Current_Source_Setting - 0xB6 / Get_Current_Source_Setting - 0xB7
CMD_SET_CURRENT_SETTING = SciospecCmd(
    "CMD_Set_Current_Source_Setting", 0xB6, CmdTypes.set_w_option, Answer.WAIT_FOR_ACK
)  # NOT USED
CMD_GET_CURRENT_SETTING = SciospecCmd(
    "CMD_Get_Current_Source_Setting",
    0xB7,
    CmdTypes.simple,
    Answer.WAIT_FOR_ANSWER_AND_ACK,
)  # NOT USED
# Options for "Set_Current_Source_Setting"/"Get_Current_Source_Setting"
OP_DC_SOURCE = SciospecOption("DC_Source", 0x01, 0x01)  # NOT USED
OP_AC_SOURCE = SciospecOption("AC_Source", 0x02, 0x01)  # NOT USED
CMD_SET_CURRENT_SETTING.set_options([OP_AC_SOURCE, OP_DC_SOURCE])
CMD_GET_CURRENT_SETTING.set_options([OP_NULL])


# list of used CMD
cmds = [
    CMD_SAVE_SETTINGS,
    CMD_SOFT_RESET,
    CMD_SET_OUTPUT_CONFIG,
    CMD_GET_OUTPUT_CONFIG,
    CMD_START_STOP_MEAS,
    CMD_SET_ETHERNET_CONFIG,
    CMD_GET_ETHERNET_CONFIG,
    CMD_GET_DEVICE_INFOS,
]


FREQ_SCALE = {OP_LINEAR.tag: OP_LINEAR.name, OP_LOG.tag: OP_LOG.name}


def frequency_scales() -> list[str]:
    return list(FREQ_SCALE.values())


def is_start_meas(cmd: SciospecCmd, op: SciospecOption):
    return cmd.tag == CMD_START_STOP_MEAS.tag and op.tag == OP_START_MEAS.tag


def is_stop_meas(cmd: SciospecCmd, op: SciospecOption):
    return cmd.tag == CMD_START_STOP_MEAS.tag and op.tag == OP_STOP_MEAS.tag


def get_cmd(tag) -> SciospecCmd:
    for cmd in cmds:
        if cmd.tag == tag:
            return cmd
    return SciospecCmd("CMD_not_found")


def get_op(ops: list[SciospecOption], tag) -> SciospecOption:
    for op in ops:
        if op.tag == tag:
            return op
    return SciospecOption("OP_not_found")


def build_cmd_frame(cmd: SciospecCmd, op: SciospecOption, data: list[bytes]):
    """Make the command frame to send according to the cmd, op and data"""

    if op not in cmd.options:
        raise TypeError(
            f'Command "{cmd.name}" ({cmd.tag}) not compatible with option "{op.name}"({op.tag})'
        )

    if cmd.type == CmdTypes.simple:  # send simple cmd (without option)
        cmd_frame = [cmd.tag, 0x00, cmd.tag]
    else:
        LL_byte = (
            op.LL_bytes[0] if cmd.type == CmdTypes.set_w_option else op.LL_bytes[1]
        )

        if LL_byte == 0x00:
            raise ValueError("not allowed option for the command")
        elif LL_byte == 0x01:  # send cmd with option
            cmd_frame = [cmd.tag, LL_byte, op.tag, cmd.tag]
        else:
            if len(data) + 1 != LL_byte:
                raise TypeError("Data do not have right lenght")
            cmd_frame = [cmd.tag, LL_byte, op.tag]
            cmd_frame.extend(iter(data))
            cmd_frame.append(cmd.tag)
    return cmd_frame


################################################################################
##  Class of acknoledgments of the Sciospec device##############################
################################################################################


@dataclass
class SciospecAck(object):
    """ACK: Acknowlegement structure description:
    name= str
    ack_byte: OB Byte
    self.error:  0 transmission succeed , >0 transmission error (return ack_byte)
    self.string_out: str (the string which is displaed e.g. ACK: Cmd executed)"""

    name: str = ""
    ack_byte: bytes = 0x00
    error: bool = False
    string_out: str = ""

    def is_nack(self):
        return self.error


################################################################################
##  Acknoledgments CONSTANTS for the Sciospec device############################
################################################################################

## ACK
ACK_INCORRECT_FRAME_SYNTAX = SciospecAck(
    "ACK_Incorrect_Frame_syntax ", 0x01, True, "NACK: Incorrect frame syntax"
)
ACK_COMMUNICATION_TIMEOUT = SciospecAck(
    "ACK_Communication_timeout",
    0x02,
    True,
    "Timeout: Communication-timeout (less data than expected)",
)
ACK_SYSTEM_BOOT_READY = SciospecAck(
    "ACK_System_boot_ready", 0x04, False, "Wake-Up: System boot ready"
)
NACK_CMD_NOT_EXCECUTED = SciospecAck(
    "NACK_Cmd_not_executed", 0x81, True, "NACK: Cmd not executed"
)
NACK_CMD_NOT_REGONIZED = SciospecAck(
    "NACK_Cmd_not_recognized", 0x82, True, "NACK: Cmd not recognized"
)
ACK_CMD_EXCECUTED = SciospecAck("ACK_Cmd_executed", 0x83, False, "ACK: Cmd executed")
ACK_SYSTEM_READY = SciospecAck(
    "ACK_System_Ready", 0x84, False, "System-Ready: System operational and ready"
)

NONE_ACK = SciospecAck(
    "ACK not recieved/not recognized", 0x99, True, "ACK not recieved/not recognized"
)

SCIOSPEC_ACK = [
    ACK_INCORRECT_FRAME_SYNTAX,
    ACK_COMMUNICATION_TIMEOUT,
    ACK_SYSTEM_BOOT_READY,
    NACK_CMD_NOT_EXCECUTED,
    NACK_CMD_NOT_REGONIZED,
    ACK_CMD_EXCECUTED,
    ACK_SYSTEM_READY,
]

ACK_FRAME = [0x18, 0x01, 0x00, 0x18]


if __name__ == "__main__":
    """ """
