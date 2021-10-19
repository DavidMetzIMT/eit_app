
import struct
################################################################################
##  Functions for Sciopec Device ###############################################
################################################################################

def mkListOfHex(rx_data):
    """ return a list of str of the Hex-representatiopn of the list of int8

    Parameters
    ----------
    rx_data: list of int8 (e.g. [0xD1, 0x00, 0xD1])

    Returns
    -------
    ID: list of str
        which are the Hex representatiopn of the list of int8 (RX_data)  
        (e.g. [0xD1, 0x00, 0xD1] >> ['D1', '00', 'D1'])

    Notes
    -----
    - used to generate the str of the serial number and Mac adress"""
    list_hex= []

    for i in range(len(rx_data)):
        tmp=hex(rx_data[i]).replace('0x','')
        if len(tmp)==1:
            list_hex.append('0'+tmp.capitalize())
        else:
            list_hex.append(tmp.capitalize())
    return list_hex

def convert4Bytes2Float(data_4bytes):
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
    

def convertFloat2Bytes(float_val):
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

def convertBytes2Int(data_Bytes):
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

def convertInt2Bytes(int_val, n_bytes):
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

def getAllSubattributes(obj_):
    """ List all attributes  and subattributes of an object 

    Parameters
    ----------
    obj_: object
        value to convert in list of int8
    
    Returns
    -------
    data: misc
        values of the attributes  and subattributes of obj_ 
    name:  str
        of the attributes  and subattributes of obj_ 
    types: str
        types of the attributes  and subattributes of obj_
    
    Notes
    -----
    - use to load/save the setup of EIT device from/in an excel-file """

    import inspect
    attributes = inspect.getmembers(obj_, lambda a:not(inspect.isroutine(a)))
    attr=[a for a in attributes if not(a[0].startswith('__') and a[0].endswith('__'))]
    name= []
    data= []
    types= []
    for i in range(len(attr)):
        if sum([str(type(attr[i][1])).find(t) for t in ['list', 'float', 'int', 'str']])> 0:
            name.append(attr[i][0])
            data.append(attr[i][1])
        else:
            data_tmp, name_tmp, types_tmp = getAllSubattributes(getattr(obj_, attr[i][0]))
            name_tmp2=[]
            for name_i in name_tmp:
                name_tmp2.append(attr[i][0] + '.' +name_i)
            if len(data_tmp)>1:
                name.extend(name_tmp2)
                data.extend(data_tmp)
            else:
                name.append(name_tmp2)
                data.append(data_tmp)
    types = [type(item) for item in data]        
    return data, name , types

def convertBoolToByte(boolean:bool):
    val= 1 if boolean else 0
    return val.to_bytes(1, byteorder='big')
def convertByteToBool(byte:bytes):
    return byte[0]==1

def convertBoolToByte(boolean:bool):
    val= 1 if boolean else 0
    return val.to_bytes(1, byteorder='big')
def convertByteToBool(byte:bytes):
    return byte[0]==1


if __name__=="__main__":
    print(convertBoolToByte(True))
    print(convertBoolToByte(False))
    print(convertByteToBool(convertBoolToByte(True)))
    print(convertByteToBool(convertBoolToByte(False)))
    print([bytearray(True)])
    print([bytes(True)])




# def _format_sn_ip_mac(type, rx_data):
#         """ Save and make the corresponding str format for display
#         for serial number (SN), IP Adress(IP), and MAC-Adress(MAC)
        
#         Parameters
#         ----------
#         rx_data: list of int8 (byte)
#         type: str 
#             type of data to save and formate: SN, IP, MAC"""
#         if type.upper() == 'SN':
#             length = LENGTH_SERIAL_NUMBER
#             setup.SN= rx_data[:length]
#             ID= mkListOfHex(rx_data[:length], length)
#             setup.SN_str= ID[0]+ '-' +ID[1] +ID[2] +'-' +ID[3] +ID[4]+ '-'+ID[5]+ ID[6]
            
#             print(setup.SN_str)
#         elif type.upper() == 'IP':
#             length= LENGTH_IP_ADRESS
#             setup.EthernetConfig.IPAdress= rx_data[:length]
#             setup.EthernetConfig.IPAdress_str= str(rx_data[0])+ '.' +str(rx_data[1])+ '.' +str(rx_data[2])+ '.' +str(rx_data[3])
            
#             print.setup.EthernetConfig.IPAdress_str)
#         elif type.upper() == 'MAC':
#             length= LENGTH_MAC_ADRESS
#             setup.EthernetConfig.MACAdress= rx_data[:length]
#             ID= mkListOfHex(rx_data, length)
#             setup.EthernetConfig.MACAdress_str= ID[0]+ ':' +ID[1]+ ':' +ID[2] + ':' +ID[3]+ ':' +ID[4]+ ':'+ID[5]
           
#             print(setup.EthernetConfig.MACAdress_str)
