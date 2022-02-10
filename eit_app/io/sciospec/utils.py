
import struct

import numpy as np
################################################################################
##  Functions for Sciopec Device ###############################################
################################################################################

def mkListOfHex(rx_data:list[bytes])->list[str]:
    """Return a list of str of the Hex-representation of the list of int8

    Args:
        rx_data (list[bytes]):  list of bytes (e.g. [0xD1, 0x00, 0xD1])

    Returns:
        list[str]: list of str
        which are the Hex representatiopn of the list of int8 (RX_data)  
        (e.g. [0xD1, 0x00, 0xD1] >> ['D1', '00', 'D1'])

    Notes: used to generate the str of the serial number and Mac adress
    """    
    list_hex= []

    for i in range(len(rx_data)):
        tmp=hex(rx_data[i]).replace('0x','')
        if len(tmp)==1:
            list_hex.append('0'+tmp.capitalize())
        else:
            list_hex.append(tmp.capitalize())
    return list_hex

def convert4Bytes2Float(data_4bytes:list[bytes])->float:
    
    """ Convert the represention of a single float format (a list of 4 int8 (4 Bytes)) of a number 
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
    if len(data_4bytes)==4:
        return struct.unpack('>f', bytearray(data_4bytes))[0]
    else:
        raise TypeError(f"Only 4Bytes allowed: {data_4bytes} transmitted") 
    

def convertFloat2Bytes(float_val:float)->list[bytes]:

    """ Convert a float value to its single float format (a list of 4 int8 (4 Bytes))
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

def convertBytes2Int(data_Bytes:list[bytes])->int:
    """ Convert a list of int8 to an integer

    Parameters
    ----------
    data_Bytes: list of int8 representing an integer (e.g. [0x00, 0x01] >> int(1))
    
    Returns
    -------
    out_int: corresponding integer

    Notes
    -----
    - see documentation of the EIT device"""
    '''return a list of 4 int (4 Bytes)'''
    if len(data_Bytes)>1:
        out_int=int.from_bytes(bytearray(data_Bytes),"big")
    else:
        out_int=int.from_bytes(bytes(data_Bytes),"big")
    return out_int

def convertInt2Bytes(int_val:int, n_bytes:int)->list[bytes]:
    """ Convert an integer to its representaion as a list of int8 with n_bytes

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
    return list((int(int_val)).to_bytes(n_bytes, byteorder='big'))

# def getAllSubattributes(obj_):
#     """ List all attributes  and subattributes of an object 

#     Parameters
#     ----------
#     obj_: object
#         value to convert in list of int8
    
#     Returns
#     -------
#     data: misc
#         values of the attributes  and subattributes of obj_ 
#     name:  str
#         of the attributes  and subattributes of obj_ 
#     types: str
#         types of the attributes  and subattributes of obj_
    
#     Notes
#     -----
#     - use to load/save the setup of EIT device from/in an excel-file """

#     import inspect
#     attributes = inspect.getmembers(obj_, lambda a:not(inspect.isroutine(a)))
#     attr=[a for a in attributes if not(a[0].startswith('__') and a[0].endswith('__'))]
#     name= []
#     data= []
#     types= []
#     for i in range(len(attr)):
#         if sum([str(type(attr[i][1])).find(t) for t in ['list', 'float', 'int', 'str']])> 0:
#             name.append(attr[i][0])
#             data.append(attr[i][1])
#         else:
#             data_tmp, name_tmp, types_tmp = getAllSubattributes(getattr(obj_, attr[i][0]))
#             name_tmp2=[]
#             for name_i in name_tmp:
#                 name_tmp2.append(attr[i][0] + '.' +name_i)
#             if len(data_tmp)>1:
#                 name.extend(name_tmp2)
#                 data.extend(data_tmp)
#             else:
#                 name.append(name_tmp2)
#                 data.append(data_tmp)
#     types = [type(item) for item in data]        
#     return data, name , types

def convertBoolToByte(val:bool)->bytes:
    """Convert a boolean in a bytes

    Args:
        val (bool): boolean to convert

    Returns:
        bytes: corresponding bytes value
    """    
    val= 1 if val else 0
    return val.to_bytes(1, byteorder='big')

def convertByteToBool(byte:bytes)->bool:
    """Convert a bytes value in bool

    Args:
        byte (bytes): bytes value to convert

    Returns:
        bool: corresponding bool value
    """    
    return byte[0]==1



if __name__=="__main__":

    meas_data= [ 
       0x3F,0x80,0,0, # 1
       0x40,0x00,0,0, # 2
       0x40,0x40,0,0, # 3
       0x40,0x80,0,0, # 4
       0x40,0xA0,0,0, # 5
    0x40,0xC0,0,0, # 6
    0x40,0xE0,0,0, # 7 
       0x41,0x00,0,0] # 8
    meas=np.array(meas_data)
    meas=np.reshape(meas, (-1,4))
    meas=meas.tolist()
    meas_f=[convert4Bytes2Float(m)for m in meas]
    meas_f=np.array(meas_f)
    meas_r_i=np.reshape(meas_f, (-1,2))
    voltage=meas_r_i[:,0]+1j*meas_r_i[:,1]

    print(meas_data)
    print(meas)
    print(meas_f)
    print(meas_r_i)
    print(voltage, voltage.shape)




    print(meas)

    meas= [ 
       [0x3F,0x80,0,0], # 1
       [0x40,0x00,0,0], # 2
       [0x40,0x40,0,0], # 3
       [0x40,0x80,0,0], # 4
       [0x40,0xA0,0,0], # 5
       [0x40,0xC0,0,0], # 6
       [0x40,0xE0,0,0], # 7 
       [0x41,0x00,0,0]] # 8
    # meas =[bytearray(m) for m in meas]
    print(meas)
    print(convert4Bytes2Float(meas[2]))
    print([convert4Bytes2Float(m)for m in meas])

