from genericpath import isdir
import os
import logging
from typing import Any, Tuple, Union

import numpy as np
from eit_app.sciospec.constants import *
from eit_app.sciospec.utils import *

from glob_utils.file.utils import (
    FileExt,
    OpenDialogFileCancelledException,
    dialog_get_file_with_ext,
    search_for_file_with_ext,
)
from glob_utils.directory.utils import (
    get_datetime_s,
    get_dir,
)
from glob_utils.types.dict import visualise, dict_nested
from glob_utils.file.json_utils import save_to_json, read_json

logger = logging.getLogger(__name__)


# ===============================================================================
#     Setup Base Class
# ===============================================================================


class SetupBase(object):
    def set_from_dict(self, **kwargs):
        """Set attributes by passing kwargs or a dict.
        Kwargs should be equivalent to self.__dict__."""
        if not isinstance(kwargs, dict):
            return
        # set all others passed attr
        for k, v in kwargs.items():
            if hasattr(self, k):  # key exist
                if isinstance(getattr(self, k), SetupBase):  # if is
                    getattr(self, k).set_from_dict(**v)
                else:
                    setattr(self, k, v)


# ===============================================================================
#     Device Informations Class
# ===============================================================================


class DeviceInfos(SetupBase):
    """Class regrouping specific infos about the device

    see documentation of Sciospec EIT device
    """

    channel: int
    sn_formated: str
    sn: list[bytes]

    def __init__(self, ch: int = 32) -> None:
        self.channel = ch
        self.reinit()

    def reinit(self) -> None:
        """Reinitialize the serial number"""
        self.sn_formated = "00-0000-0000-0000"
        self.sn = [0, 0, 0, 0, 0, 0, 0]

    def is_sn_sciopec(self):
        """Asset if the device is a sciospec device"""
        # logger.debug(f"{self.sn}")
        return self.sn != [0, 0, 0, 0, 0, 0, 0]

    # ---------------------------------------------------------------------------
    # Getter
    # ---------------------------------------------------------------------------

    def get_sn(self, in_bytes: bool = False) -> Union[list[bytes], str]:
        """Return serial number:
        - in Bytes for sending to the device (NOT USED, SN can't be changed..)
        - in str for simple get
        """
        return self.sn if in_bytes else self.sn_formated

    # ---------------------------------------------------------------------------
    # Setter
    # ---------------------------------------------------------------------------

    def set_sn(
        self, rx_frame: Union[list[bytes], float], in_bytes: bool = True
    ) -> None:
        """Set value of mac adress:
        - out of Bytes from the device (rx_frame)
        - (error)
        """
        if not in_bytes:
            raise Exception("Error in use of this method")
        rx_op_data = rx_frame[OPTION_BYTE_INDX:-1]
        length = LENGTH_SERIAL_NUMBER
        self.sn = rx_op_data[:length]
        self.build_sn_formated()
        # logger.debug(f"SN:{self.sn}, {self.sn_formated}")

    def build_sn_formated(self) -> None:
        ID = mkListOfHex(self.sn)
        self.sn_formated = f"{ID[0]}-{ID[1]}{ID[2]}-{ID[3]}{ID[4]}-{ID[5]}{ID[6]}"

    def set_sn_direct(self, sn: list[bytes]) -> None:
        self.sn = sn
        self.build_sn_formated()


# ===============================================================================
#     Output Configuration Class
# ===============================================================================


class OutputConfig(SetupBase):
    """Class regrouping all info about the ouput configuration of the device

    see documentation of Sciospec EIT device
    """

    exc_stamp: bool
    current_stamp: bool
    time_stamp: bool

    def __init__(self) -> None:
        self.reinit()

    def reinit(self) -> None:  # set all to True!
        self.exc_stamp = True
        self.current_stamp = True
        self.time_stamp = True

    # ---------------------------------------------------------------------------
    # Getter
    # ---------------------------------------------------------------------------

    def get_exc_stamp(self, in_bytes: bool = False) -> Union[list[bytes], bool]:
        """Return excitation stamp from output config:
        - in Bytes for sending to the device
        - in bool for simple get"""
        return [int(self.exc_stamp)] if in_bytes else self.exc_stamp

    def get_current_stamp(self, in_bytes: bool = False) -> Union[list[bytes], bool]:
        """Return current stamp from output config:
        - in Bytes for sending to the device
        - in bool for simple get"""
        return [int(self.current_stamp)] if in_bytes else self.current_stamp

    def get_time_stamp(self, in_bytes: bool = False) -> Union[list[bytes], bool]:
        """Return time stamp from output config:
        - in Bytes for sending to the device
        - in bool for simple get"""
        return [int(self.time_stamp)] if in_bytes else self.time_stamp

    # ---------------------------------------------------------------------------
    # Setter
    # ---------------------------------------------------------------------------
    def set_exc_stamp(self, value: Union[list[bytes], bool], in_bytes: bool = False):
        """Set value of excitation stamp from output config:
        - out of Bytes from the device (rx_frame)
        - from a bool for simple set"""
        # self.exc_stamp = (
        #     bool(value[DATA_START_INDX:-1][0]) if in_bytes else value
        # )

    def set_current_stamp(
        self, value: Union[list[bytes], bool], in_bytes: bool = False
    ):
        """Set value of current stamp from output config:
        - out of Bytes from the device (rx_frame)
        - from a bool for simple set"""
        # self.current_stamp = (
        #     bool(value[DATA_START_INDX:-1][0]) if in_bytes else value
        # )

    def set_time_stamp(self, value: Union[list[bytes], bool], in_bytes: bool = False):
        """Set value of time stamp from output config:
        - out of Bytes from the device (rx_frame)
        - from a bool for simple set"""
        # self.time_stamp = (
        #     bool(value[DATA_START_INDX:-1][0]) if in_bytes else value
        # )


# ===============================================================================
#     Ethernet Configuration Class
# ===============================================================================


class EthernetConfig(SetupBase):
    """Class regrouping all info about the ethernet configuration of the device:
    IPAdress, MAC Adress, etc.

    see documentation of Sciospec EIT device"""

    ip: list[int]
    mac: list[int]
    ip_formated: str
    mac_formated: str
    dhcp: bool

    def __init__(self) -> None:
        self.reinit()

    def reinit(self) -> None:
        self.ip = [0, 0, 0, 0]
        self.mac = [0, 0, 0, 0, 0, 0]
        self.ip_formated = "0.0.0.0"
        self.mac_formated = "00:00:00:00:00:00"
        self.dhcp = True

    # ---------------------------------------------------------------------------
    # Getter
    # ---------------------------------------------------------------------------

    def get_ip(self, in_bytes: bool = False) -> Union[list[bytes], str]:
        """Return ip adress:
        - in Bytes for sending to the device
        - in str for simple get"""
        return self.ip if in_bytes else self.ip_formated

    def get_mac(self, in_bytes: bool = False) -> Union[list[bytes], str]:
        """Return mac adress:
        - in Bytes for sending to the device
        (NOT USED, MAC ADRESS can't be changed..)
        - in str for simple get"""
        return self.mac if in_bytes else self.mac_formated

    def get_dhcp(self, in_bytes: bool = False) -> Union[list[bytes], bool]:
        """Return dhcp:
        - in Bytes for sending to the device
        - in bool for simple get"""
        return [int(self.dhcp)] if in_bytes else self.dhcp

    # ---------------------------------------------------------------------------
    # Setter
    # ---------------------------------------------------------------------------
    def set_ip(self, value: Union[list[bytes], str], in_bytes: bool = False) -> None:
        """Set value of ip adress:
        - out of Bytes from the device (rx_frame)
        - from a str for simple set (NOT IMPLEMENTED)"""
        if in_bytes:
            data = value[DATA_START_INDX:-1]
            length = LENGTH_IP_ADRESS
            self.ip = data[:length]
            self.ip_formated = (
                f"{str(data[0])}.{str(data[1])}.{str(data[2])}.{str(data[3])}"
            )

        else:
            raise Exception("not implemented")  # TODO

    def set_mac(self, value: Union[list[bytes], str], in_bytes: bool = False) -> None:
        """Set value of mac adress:
        - out of Bytes from the device (rx_frame)
        - (error)"""
        if in_bytes:
            data = value[DATA_START_INDX:-1]
            length = LENGTH_MAC_ADRESS
            self.mac = data[:length]
            ID = mkListOfHex(data[:length])
            self.mac_formated = f"{ID[0]}:{ID[1]}:{ID[2]}:{ID[3]}:{ID[4]}:{ID[5]}"

        else:
            raise Exception("Error in use of this method")

    def set_dhcp(self, value: Union[list[bytes], bool], in_bytes: bool = False) -> None:
        """Set value of dhcp:
        - out of Bytes from the device (rx_frame)
        - from a bool for simple set"""
        # self.dhcp = bool(value[DATA_START_INDX:-1][0]) if in_bytes else value


# ===============================================================================
#     Frequency Configuration Class
# ===============================================================================


class FrequencyConfig(SetupBase):
    """Class regrouping all parameters for the frequency sweep configuration
    of the device used during the measurement

    see documentation of Sciospec EIT device"""

    freq_min: float
    freq_max: float
    freq_steps: int
    freq_scale: str

    def __init__(self) -> None:
        self.reinit()

    def reinit(self) -> None:
        self.freq_min = 1000.0
        self.freq_max = 1000.0
        self.freq_steps = 1
        self.freq_scale = OP_LINEAR.name

    @property
    def freqs_list(self) -> list[float]:
        """Make the Frequencies list of frequencies accoreding to the
        frequency sweep configuration

        see documentation of Sciospec EIT device
        """
        if self.freq_scale == OP_LINEAR.name:
            freqs = np.linspace(self.freq_min, self.freq_max, self.freq_steps)
        elif self.freq_scale == OP_LOG.name:
            freq_min = np.log10(self.freq_min)
            freq_max = np.log10(self.freq_max)
            freqs = np.logspace(freq_min, freq_max, self.freq_steps)
        else:
            TypeError("incorrect scale")
        # logger.debug(f"Frequency list{freqs}")
        return freqs

    # ---------------------------------------------------------------------------
    # Getter
    # ---------------------------------------------------------------------------

    def get_data(self, in_bytes: bool = False) -> list[bytes]:
        """Return the used frequence config:
        - in Bytes for sending to the device
        """
        if not in_bytes:
            return []
        data = []
        data = convertFloat2Bytes(self.freq_min)
        data.extend(convertFloat2Bytes(self.freq_max))
        data.extend(convertInt2Bytes(self.freq_steps, 2))  # Steps is defined on 2 bytes
        if self.freq_scale == OP_LINEAR.name:
            data.append(OP_LINEAR.tag)
        elif self.freq_scale == OP_LOG.name:
            data.append(OP_LOG.tag)
        else:
            raise TypeError("wrong Scale Str")
        return data

    # ---------------------------------------------------------------------------
    # Setter
    # ---------------------------------------------------------------------------
    def set_data(
        self, value: list[bytes] = None, in_bytes: bool = False, **kwargs
    ) -> None:
        """Set values of frequence config:
        - out of Bytes from the device (rx_frame)
        - from a **kwargs from freq_config.set_data for simple set
        """
        if in_bytes:
            data = value[DATA_START_INDX:-1]

            freq_max_enable, error = self._set_data(
                freq_min=convert4Bytes2Float(data[:4]),
                freq_max=convert4Bytes2Float(data[4:8]),
                freq_steps=convertBytes2Int(data[8:10]),
                freq_scale=FREQ_SCALE[data[10]],
            )

        else:
            freq_max_enable, error = self._set_data(**kwargs)

        return freq_max_enable, error

    def _set_data(
        self,
        freq_min: float = 1000.0,
        freq_max: float = 10000.0,
        freq_steps: int = 1,
        freq_scale: str = "",
    ) -> Tuple[bool, bool]:
        """Set the values of the frequency config

        Args:
            freq_min (float, optional):  Defaults to 1000.0.
            freq_max (float, optional):  Defaults to 10000.0.
            freq_steps (int, optional):  Defaults to 1.
            freq_scale (str, optional):  Defaults to "".

        Returns:
            Tuple[bool, bool]: enable display flag for the freq_max field, and
            error flag if freq_max is not > freq_min for freq_steps > 1
        """
        self.freq_min = freq_min
        self.freq_max = freq_max
        self.freq_scale = (
            freq_scale
            if freq_scale in [OP_LINEAR.name, OP_LOG.name]
            else OP_LINEAR.name
        )
        self.freq_steps = freq_steps or 1  # atleast 1 step
        set_freq_max_enable = True
        error_freq_max = False
        # Set minF and maxF
        if self.freq_steps == 1:
            self.freq_max = self.freq_min
            set_freq_max_enable = False  # disable the freq_max field
        # for freq_steps > 1 then freq max should be > freq_min
        elif self.freq_max <= self.freq_min:
            self.freq_max = self.freq_min
            error_freq_max = True  # error freq max value
        return set_freq_max_enable, error_freq_max


# ===============================================================================
#     Sciospec Setup Class
# ===============================================================================
# TODO SignalReciever ?
class SciospecSetup(SetupBase):
    """Class regrouping all info (serial number, Ethernet config, etc.),
    meas. parameters (excitation pattern, amplitude, etc.), etc. of the device.

    see documentation of Sciospec EIT device"""

    exc_amp: float
    exc_pattern: list[list[int]]
    exc_pattern_mdl: list[list[int]]
    exc_pattern_idx: int
    frame_rate: float
    burst: int
    device_infos: DeviceInfos
    output_config: OutputConfig
    ethernet_config: EthernetConfig
    freq_config: FrequencyConfig

    def __init__(self, n_channel: int) -> None:
        self.device_infos = DeviceInfos(n_channel)
        self.output_config = OutputConfig()
        self.ethernet_config = EthernetConfig()
        self.freq_config = FrequencyConfig()
        self.reinit()
        self.define_data_access()

    def reinit(self) -> None:
        """Reinit the values of the setup and ist objectss"""
        self.exc_amp = 10.0
        self.exc_pattern = [[1, 2], [2, 3]]
        self.exc_pattern_mdl = [[1, 2], [2, 3]]
        self.exc_pattern_idx = 0
        self.set_frame_rate(1.0)
        self.burst = 0
        self.device_infos.reinit()
        self.output_config.reinit()
        self.ethernet_config.reinit()
        self.freq_config.reinit()
        logger.debug("Reinitialisation of SciospecSetup - DONE")

    def is_sciospec(self) -> bool:
        """Asset if actual setup is from a sciospec device"""
        return self.device_infos.is_sn_sciopec()

    def build_sciospec_device_name(self, port) -> str:
        """Create a generic sciopsec device name"""
        return (
            f'Device (SN: {self.get_sn()}) on "{port}"' if self.is_sciospec() else None
        )

    def define_data_access(self) -> None:
        """Set corresponding callbacks for setting and getting data of setup to
        command and option tags using during communication with sciospec device

        see documentation of Sciospec EIT device
        """
        self._get_data_access = {
            CMD_SET_MEAS_SETUP.tag: {
                # OP_RESET_SETUP.tag: None,
                OP_BURST_COUNT.tag: self.get_burst,
                OP_FRAME_RATE.tag: self.get_frame_rate,
                OP_EXC_FREQUENCIES.tag: self.freq_config.get_data,
                OP_EXC_AMPLITUDE.tag: self.get_exc_amp,
                OP_EXC_PATTERN.tag: self.get_exc_pattern,
            },
            CMD_SET_OUTPUT_CONFIG.tag: {
                OP_EXC_STAMP.tag: self.output_config.get_exc_stamp,
                OP_CURRENT_STAMP.tag: self.output_config.get_current_stamp,
                OP_TIME_STAMP.tag: self.output_config.get_time_stamp,
            },
            CMD_SET_ETHERNET_CONFIG.tag: {
                # OP_IP_ADRESS.tag: None,
                # OP_MAC_ADRESS.tag: None,
                OP_DHCP.tag: self.ethernet_config.get_dhcp,
            },
            # CMD_SET_EXPORT_CHANNEL.tag:{:},
            # CMD_SET_BATTERY_CONTROL.tag:{:},
            # CMD_SET_LED_CONTROL.tag:{:},
            # CMD_SET_CURRENT_SETTING.tag:{:},
        }

        self._set_data_access = {
            CMD_GET_MEAS_SETUP.tag: {
                # OP_RESET_SETUP.tag: None,
                OP_BURST_COUNT.tag: self.set_burst,
                OP_FRAME_RATE.tag: self.set_frame_rate,
                OP_EXC_FREQUENCIES.tag: self.freq_config.set_data,
                OP_EXC_AMPLITUDE.tag: self.set_exc_amp,
                OP_EXC_PATTERN.tag: self.set_exc_pattern,
            },
            CMD_GET_OUTPUT_CONFIG.tag: {
                OP_EXC_STAMP.tag: self.output_config.set_exc_stamp,
                OP_CURRENT_STAMP.tag: self.output_config.set_current_stamp,
                OP_TIME_STAMP.tag: self.output_config.set_time_stamp,
            },
            CMD_GET_ETHERNET_CONFIG.tag: {
                OP_IP_ADRESS.tag: self.ethernet_config.set_ip,
                OP_MAC_ADRESS.tag: self.ethernet_config.set_mac,
                OP_DHCP.tag: self.ethernet_config.set_dhcp,
            },
            # CMD_GET_EXPORT_CHANNEL.tag:{:},
            # CMD_GET_EXPORT_MODULE.tag:{:},
            # CMD_GET_BATTERY_CONTROL.tag:{:},
            # CMD_GET_LED_CONTROL.tag:{:},
            CMD_GET_DEVICE_INFOS.tag: {OP_NULL.tag: self.device_infos.set_sn},
            # CMD_GET_CURRENT_SETTING.tag:{:}
        }

    def get_data(self, cmd: SciospecCmd, op: SciospecOption) -> list[bytes]:
        """Return the corresponding data of the setup for command/option
        to build tx_frame

        Args:
            cmd (SciospecCmd): command
            op (SciospecOption): command option

        Returns:
            list[bytes]: the corresponding data of the setup for command/option
        """
        try:
            return self._get_data_access[cmd.tag][op.tag](in_bytes=True) or [0x00]
        except KeyError as e:
            # if cmd/op key combination not found warning...
            msg = f'Setup data for "{cmd.name}"({cmd.tag})/"{op.name}"({op.tag}) - NOT FOUND'
            logger.warning(msg)
            return [0x00]

    def set_data(self, rx_setup_stream: list[bytes], **kwargs) -> None:
        """Set the values in the setup out of the rx_frame"""
        cmd_tag = rx_setup_stream[CMD_BYTE_INDX]
        if (
            OP_NULL.tag in self._set_data_access[cmd_tag]
        ):  # some answer do not have options (meas, sn)
            op_tag = OP_NULL.tag
        else:
            op_tag = rx_setup_stream[OPTION_BYTE_INDX]

        try:
            self._set_data_access[cmd_tag][op_tag](rx_setup_stream, True)
        except KeyError as e:
            cmd = get_cmd(cmd_tag)
            op = get_op(cmd.options, op_tag)
            msg = f'Setup data for :"{cmd.name}"({cmd.tag})/"{op.name}"({op.tag}) - NOT FOUND'
            logger.error(msg)

        logger.debug(f"RX_SETUP: {rx_setup_stream} -  TREATED")

    def save(self, dir: str = None) -> Union[str, None]:
        """Save the setup a json-file in a diretory.

        Args:
            dir (str, optional): directory path .If `None` the user will be ask to
            select a diretory via a dialog. Defaults to `None`.

        Returns:
            Union[str, None]: return the filpathe of the setup saved, if saving
            cancelled returns `None`
        """
        if not dir:
            dir = get_dir(title="Select a directory, where the setup will be saved")
            if dir is None:
                return None

        path = os.path.join(dir, f"setup_{get_datetime_s()}")

        d = dict_nested(self, ignore_private=True)
        visualise(d)
        save_to_json(path, d)
        logger.info(f"Setup: {self.__dict__} \n saved in file : {dir} ")
        return path

    def load(self, dir: str = None, **kwargs) -> Union[str, None]:
        """Search and load a setup json-file out of directory.

        Args:
            dir (str, optional): directory path .If `None` the user will be ask to
            select a diretory via a dialog. Defaults to `None`.

        Returns:
            Union[str, None]: return the filpath of the setup loaded, if loading
            cancelled or unsuccesful returns `None`
        """
        filepath = None
        try:

            if dir is None:
                filepath = dialog_get_file_with_ext(ext=FileExt.json)

            elif isdir(dir):
                files = search_for_file_with_ext(dir, ext=FileExt.json)
                filepath = [f for f in files if "setup_" in f]

                if not filepath:
                    logger.warning(f"Load setup contained in dir :{dir} - Unsuccesfull")
                    return None

                filepath = os.path.join(dir, filepath[0])

            setup_as_dict = read_json(filepath)
            if setup_as_dict is None:
                return None
            visualise(setup_as_dict)
            self.set_from_dict(**setup_as_dict)

            logger.info(f"Setup: {self.__dict__} \n loaded from file : {filepath} ")
        except OpenDialogFileCancelledException as e:
            # show_msgBox('Loading cancelled','', "I")
            logger.info(f"Loading cancelled {e}")
        return filepath

    @property
    def max_frame_rate(self) -> float:
        """Compute the maximum frame rate corresponding to the actual
        frequencies sweep

        see documentation of Sciospec EIT device
        """
        f_i = self.get_freqs_list()  # ndarray

        n_freq = float(self.freq_config.freq_steps)
        t_freq = float(DELAY_BTW_2FREQ)  # in s

        n_inject = float(len(self.exc_pattern))
        t_inject = float(DELAY_BTW_2INJ)  # in s

        T_fi = np.reciprocal(f_i)  # in s
        T_ms = np.ones_like(f_i) * MIN_SAMPLING_TIME  # in s
        max_Tms_fi = np.maximum(T_ms, T_fi)
        sum_max_Tms_fi = float(max_Tms_fi.sum())
        t_min = n_inject * (t_inject + t_freq * (n_freq - 1) + sum_max_Tms_fi)

        return float(1 / t_min) if t_min != 0.0 else 1.0

    # ---------------------------------------------------------------------------
    # Getter
    # ---------------------------------------------------------------------------

    def get_channel(self):
        """Return the number of channnel used in the device"""
        return self.device_infos.channel

    def get_exc_amp_d(self, in_bytes: bool = False) -> Union[list[bytes], float]:
        """Return excitation amplitude (double precision):
        - in Bytes for sending to the device
        - in float for simple get
        """
        return [0x00] if in_bytes else self.exc_amp

    def get_exc_amp(self, in_bytes: bool = False) -> Union[list[bytes], float]:
        """Return excitation amplitude (single precision):
        - in Bytes for sending to the device
        - in float for simple get
        """
        return convertFloat2Bytes(self.exc_amp) if in_bytes else self.exc_amp

    def get_burst(self, in_bytes: bool = False) -> Union[list[bytes], float]:
        """Return burst:
        - in Bytes for sending to the device
        - in float for simple get
        """
        return convertInt2Bytes(self.burst, 2) if in_bytes else self.burst

    def get_frame_rate(self, in_bytes: bool = False) -> Union[list[bytes], float]:
        """Return frame rate:
        - in Bytes for sending to the device
        - in float for simple get
        """
        return convertFloat2Bytes(self.frame_rate) if in_bytes else self.frame_rate

    def get_max_frame_rate(self) -> float:
        """Return max frame rate computed from the used frequence config"""
        return self.max_frame_rate

    def get_freq_min(self) -> float:
        """Return the min frequency used to build the frequencies list"""
        return self.freq_config.freq_min

    def get_freq_max(self) -> float:
        """Return the max frequency used to build the frequencies list"""
        return self.freq_config.freq_max

    def get_freq_scale(self) -> str:
        """Return the scale used between min and max frequencies to build the
        frequencies list
        """
        return self.freq_config.freq_scale

    def get_freq_steps(self) -> int:
        """Return the number of steps used between min and max frequencies to
        build the frequencies list
        """
        return self.freq_config.freq_steps

    def get_freqs_list(self) -> list[float]:
        """Make the frequencies list and return it"""
        return self.freq_config.freqs_list

    def get_exc_pattern(
        self, in_bytes: bool = False
    ) -> Union[list[bytes], list[list[bytes]]]:
        """Return excitation pattern:
        - in Bytes for sending to the device (only one index)
        - in float for simple get (the whole list)
        """
        return (
            list(self.exc_pattern[self.exc_pattern_idx])
            if in_bytes
            else self.exc_pattern
        )

    def get_exc_pattern_mdl(self):
        """Return excitation pattern from model:"""
        return self.exc_pattern_mdl

    def get_sn(self, in_bytes: bool = False) -> Union[list[bytes], str]:
        """Return serial number
        - in str for simple get
        """
        return self.device_infos.get_sn(in_bytes)

    # ---------------------------------------------------------------------------
    # Setter
    # ---------------------------------------------------------------------------

    def set_sn(self, sn: list[bytes]) -> str:
        """Set directly the serial number"""
        self.device_infos.set_sn_direct(sn)

    def set_exc_amp_d(self, value: Union[list[bytes], float], in_bytes: bool = False):
        """Set value of excitation amplitude (double precision):
        - out of Bytes from the device (rx_frame)
        - from a float for simple set
        """
        self.exc_amp = (
            convert4Bytes2Float(value[DATA_START_INDX:-1]) if in_bytes else value
        )

    def set_exc_amp(self, value: Union[list[bytes], float], in_bytes: bool = False):
        """Set value of excitation amplitude (single precision):
        - out of Bytes from the device (rx_frame)
        - from a float for simple set
        """
        self.exc_amp = (
            convert4Bytes2Float(value[DATA_START_INDX:-1]) if in_bytes else value
        )

    def set_burst(self, value: Union[list[bytes], int], in_bytes: bool = False):
        """Set value of burst:
        - out of Bytes from the device (rx_frame)
        - from an int for simple set
        """
        self.burst = convertBytes2Int(value[DATA_START_INDX:-1]) if in_bytes else value

    def set_frame_rate(self, value: Union[list[bytes], float], in_bytes: bool = False):
        """Set value of frame rate:
        - out of Bytes from the device (rx_frame)
        - from a float for simple set
        """
        self.frame_rate = (
            convert4Bytes2Float(value[DATA_START_INDX:-1])
            if in_bytes
            else value
            if value > 0
            else 1.0
        )
        self._check_frame_rate()

    def _check_frame_rate(self):
        """Check if frame rate is < than max_frame_rate, if not the
        frame rate is set to max_frame_rate
        """
        self.frame_rate = (
            self.frame_rate
            if self.frame_rate < self.max_frame_rate
            else self.max_frame_rate
        )

    def set_exc_pattern(
        self, value: Union[list[bytes], list[list[int]]], in_bytes: bool = False
    ):
        """Set excitation pattern:
        - out of Bytes from the device (rx_frame)
        - from a List for simple set
        """
        if in_bytes:
            data = value[DATA_START_INDX:-1]
            self.exc_pattern = [
                data[i * 2 : (i + 1) * 2] for i in range(len(data) // 2)
            ]
        else:
            self.exc_pattern = value

    def set_exc_pattern_mdl(
        self,
        value: list[list[int]],
    ):
        """Set excitation pattern model:"""
        self.exc_pattern_mdl = value

    def set_exc_pattern_idx(self, idx: int):
        """Set value of idx of actual pattern:
        used to latch each pattern for setting exc_pattern to the device
        """
        self.exc_pattern_idx = idx

    def set_freq_config(self, **kwargs) -> Any:
        """
        kwargs:
            freq_min (float, optional): _description_. Defaults to 1000.0.
            freq_max (float, optional): _description_. Defaults to 10000.0.
            freq_steps (int, optional): _description_. Defaults to 1.
            freq_scale (str, optional): _description_. Defaults to "".
        """
        res = self.freq_config.set_data(**kwargs)
        self._check_frame_rate()
        return res


if __name__ == "__main__":

    s = SciospecSetup(32)
    s.frame_rate = 5.5555
    s.save()
    s.frame_rate = 3.11111
    s.load("E:/Software_dev/Python/eit_app/tests")
    print(s.frame_rate)
