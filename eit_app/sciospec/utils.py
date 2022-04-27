import struct

import numpy as np

################################################################################
##  Functions for Sciopec Device ###############################################
################################################################################


def mkListOfHex(rx_data: list[bytes]) -> list[str]:
    """Return a list of str of the Hex-representation of the list of int8

    Args:
        rx_data (list[bytes]):  list of bytes (e.g. [0xD1, 0x00, 0xD1])

    Returns:
        list[str]: list of str
        which are the Hex representatiopn of the list of int8 (RX_data)
        (e.g. [0xD1, 0x00, 0xD1] >> ['D1', '00', 'D1'])

    Notes: used to generate the str of the serial number and Mac adress
    """
    list_hex = []

    for rx_datum in rx_data:
        tmp = hex(rx_datum).replace("0x", "")
        if len(tmp) == 1:
            list_hex.append(f"0{tmp.capitalize()}")
        else:
            list_hex.append(tmp.capitalize())

    return list_hex


def convert4Bytes2Float(data_4bytes: list[bytes]) -> float:
    """Convert the represention of a single float format (a list of 4 int8 (4 Bytes)) of a number
    to its float value

    Parameters
    ----------
    data_4bytes: list of 4 int8 representing a float value according the single float format

    Returns
    -------
    out_float: corresponding float

    Notes
    -----
    - see documentation of the EIT device"""
    if len(data_4bytes) == 4:
        return struct.unpack(">f", bytearray(data_4bytes))[0]
    else:
        raise TypeError(f"Only 4Bytes allowed: {data_4bytes} transmitted")


def convertFloat2Bytes(float_val: float) -> list[bytes]:
    """Convert a float value to its single float format (a list of 4 int8 (4 Bytes))
    representation

    Parameters
    ----------
    float_val: float

    Returns
    -------
    list of 4 int8 representing float_val according thesingle float format

    Notes
    -----
    - see documentation of the EIT device"""
    return list(struct.pack(">f", float_val))


def convertBytes2Int(data_Bytes: list[bytes]) -> int:
    """Convert a list of int8 to an integer

    Parameters
    ----------
    data_Bytes: list of int8 representing an integer (e.g. [0x00, 0x01] >> int(1))

    Returns
    -------
    out_int: corresponding integer

    Notes
    -----
    - see documentation of the EIT device"""
    """return a list of 4 int (4 Bytes)"""
    return (
        int.from_bytes(bytearray(data_Bytes), "big")
        if len(data_Bytes) > 1
        else int.from_bytes(bytes(data_Bytes), "big")
    )


def convertInt2Bytes(int_val: int, n_bytes: int) -> list[bytes]:
    """Convert an integer to its representaion as a list of int8 with n_bytes

    Parameters
    ----------
    int_val: int
        value to convert in list of int8
    n_bytes: int
        length of the output list

    Returns
    -------
    list of n_bytes int8

    Notes
    -----
    - see documentation of the EIT device"""
    return list((int(int_val)).to_bytes(n_bytes, byteorder="big"))


def convertBoolToByte(val: bool) -> bytes:
    """Convert a boolean in a bytes

    Args:
        val (bool): boolean to convert

    Returns:
        bytes: corresponding bytes value
    """
    val = 1 if val else 0

    return val.to_bytes(1, byteorder="big")


if __name__ == "__main__":

    meas_data = [
        0x3F,
        0x80,
        0,
        0,  # 1
        0x40,
        0x00,
        0,
        0,  # 2
        0x40,
        0x40,
        0,
        0,  # 3
        0x40,
        0x80,
        0,
        0,  # 4
        0x40,
        0xA0,
        0,
        0,  # 5
        0x40,
        0xC0,
        0,
        0,  # 6
        0x40,
        0xE0,
        0,
        0,  # 7
        0x41,
        0x00,
        0,
        0,  # 8
    ]
    meas = np.array(meas_data)
    meas = np.reshape(meas, (-1, 4))
    meas = meas.tolist()
    meas_f = [convert4Bytes2Float(m) for m in meas]
    meas_f = np.array(meas_f)
    meas_r_i = np.reshape(meas_f, (-1, 2))
    voltage = meas_r_i[:, 0] + 1j * meas_r_i[:, 1]

    print(meas_data)
    print(meas)
    print(meas_f)
    print(meas_r_i)
    print(voltage, voltage.shape)

    print(meas)

    meas = [
        [0x3F, 0x80, 0, 0],  # 1
        [0x40, 0x00, 0, 0],  # 2
        [0x40, 0x40, 0, 0],  # 3
        [0x40, 0x80, 0, 0],  # 4
        [0x40, 0xA0, 0, 0],  # 5
        [0x40, 0xC0, 0, 0],  # 6
        [0x40, 0xE0, 0, 0],  # 7
        [0x41, 0x00, 0, 0],  # 8
    ]
    # meas =[bytearray(m) for m in meas]
    print(meas)
    print(convert4Bytes2Float(meas[2]))
    print([convert4Bytes2Float(m) for m in meas])
