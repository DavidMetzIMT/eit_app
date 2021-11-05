
import os
import struct
import time

from tkinter import Tk     # from tkinter import Tk for Python 3.x
from tkinter.filedialog import askdirectory, askopenfilename, askopenfilenames
import pickle
import json
import datetime
from os import PathLike, getcwd, listdir
from os.path import isfile, join
from typing import List
from eit_app.utils.constants import FORMAT_DATE_TIME,\
                                    DEFAULT_OUTPUTS_DIR,\
                                    EXT_TXT,\
                                    EXT_IMG,\
                                    EXT_PKL



class CancelledError(Exception):
    """"""
class DataLoadedNotCompatibleError(Exception):
    """"""
class EmptyFileError(Exception):
    """"""

def get_date_time():
    _now = datetime.datetime.now()
    return _now.strftime(FORMAT_DATE_TIME)

def get_time():
    return time.time()

def append_date_time(s:str, datetime:str=None) -> str:

    s= remove_date_time(s)
    if datetime:
        return f'{s}_{datetime}'
    else:
        return f'{s}_{get_date_time()}'

def remove_date_time(s:str)->str:
    length= len(get_date_time())
    if len(s)>= length:
        try:
            datetime.datetime.strptime(s[-length:], FORMAT_DATE_TIME)
            datestring= s[:-length]
            if not datestring:
                s='default'
        except ValueError:
            pass
    return s

def get_POSIX_path(path:str):

    return path.replace('\\','/')


def mk_ouput_dir(name, default_out_dir= DEFAULT_OUTPUTS_DIR, verbose= False ):
    """create and return the path of a folder "name" in the default_out_directory

    Args:
        name ([type]): [description]
        verbose (bool, optional): [description]. Defaults to True.
        default_out_dir (str, optional): [description]. Defaults to 'outputs'.

    Returns:
        [type]: [description]
    """
    if not os.path.isdir(default_out_dir):
        os.mkdir(default_out_dir)

    output_dir= os.path.join(default_out_dir, name)

    if verbose:
        print('\nResults are to found in:\n >> {}'.format(output_dir))

    os.mkdir(output_dir)

    return output_dir

def get_dir(initialdir=None, title='Select a directory'):
    """[summary]

    Args:
        initialdir ([type], optional): [description]. Defaults to os.getcwd().
        title (str, optional): [description]. Defaults to 'Select a directory'.

    Returns:
        [type]: [description]
    """
    Tk().withdraw()
    initialdir = initialdir or os.getcwd()
    path_dir = askdirectory(initialdir=initialdir, title= title)
    if not path_dir:
        raise CancelledError()
    return path_dir

def get_file(filetypes=[("All files","*.*")], verbose= True, initialdir=None, title= 'Select a file'):
    """used to get select files using gui (multiple types of file can be set!)

    Args:
        filetypes (list, optional): [description]. Defaults to [("All files","*.*")].
        verbose (bool, optional): [description]. Defaults to True.
        path ([type], optional): [description]. Defaults to None.

    Returns:
        [type]: [description]
    """

    Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing

    initialdir = initialdir or os.getcwd()

    whole_path = askopenfilename(   initialdir=initialdir,
                                    filetypes=filetypes, title= title) # show an "Open" dialog box and return the path to the selected file
    if not whole_path:
        raise CancelledError()

    path_dir, filename = os.path.split(whole_path)
    if verbose:
        print(path_dir, filename)
    return path_dir, filename

def verify_is_file_with_ext(file:str, ext:str, dir:str=None):
    """file can be a path or an filename, in that case precise dir..

    """
    if dir:
        file=os.path.join(dir, file)
    if not os.path.isfile(file):
        return None
    if os.path.splitext(file)[1]==ext:
        return file

def search_for_file_with_ext(dir:str, ext:str='.dat')-> List[str]:
    """ Return a list of filename (not path) in dir with a specific extension
    Raise file not found if not"""

    filenames = [filename for filename in os.listdir(dir) if verify_is_file_with_ext(filename, ext, dir)]
    if not filenames: # if no files are contains
        raise FileNotFoundError()

    return filenames

def save_as_pickle(filename, class2save, verbose=False, add_ext=True):
    """[summary]

    Args:
        filename ([type]): [description]
        class2save ([type]): [description]
        verbose (bool, optional): [description]. Defaults to True.
    """
    if add_ext:
        filename= os.path.splitext(filename)[0] + EXT_PKL

    with open(filename, 'wb') as file:
        pickle.dump(class2save, file, pickle.HIGHEST_PROTOCOL)
    print_saving_verbose(filename, class2save, verbose)

def load_pickle(filename, class2upload=None, verbose=False):
    """[summary]

    Args:
        filename ([type]): [description]
        class2upload ([type], optional): [description]. Defaults to None.
        verbose (bool, optional): [description]. Defaults to True.

    Returns:
        [type]: [description]
    """
    if os.path.getsize(filename) == 0:
        raise EmptyFileError(f'The file :{filename} is empty!')

    with open(filename, 'rb') as file:
        loaded_class = pickle.load(file)
    print_loading_verbose(filename, loaded_class, verbose)
    if not class2upload:
        return loaded_class
    set_attributes(class2upload,loaded_class)
    return class2upload

def save_as_txt(filepath, class2save, verbose=True, add_ext=True):
    """[summary]

    Args:
        filename ([type]): [description]
        class2save ([type]): [description]
        verbose (bool, optional): [description]. Defaults to True.
        add_ext (bool, optional): [description]. Defaults to True.
    """
    if add_ext:
        filepath= os.path.splitext(filepath)[0] + EXT_TXT
    list_of_strings= []
    if isinstance(class2save,str):
        list_of_strings.append(class2save)
    elif isinstance(class2save, list):
        for item in class2save:
            list_of_strings.append(f'{item}')
    else:

        tmp_dict= class2save.__dict__
        list_of_strings.append('Dictionary form:')
        list_of_strings.append(json.dumps(class2save.__dict__))
        list_of_strings.append('\n\nSingle attributes:')
        list_of_strings.extend([f'{key} = {tmp_dict[key]},' for key in class2save.__dict__ ])

    with open(filepath, 'w') as file:
        [ file.write(f'{st}\n') for st in list_of_strings ]

    print_saving_verbose(filepath, class2save, verbose)

def read_txt(filepath):
    with open(filepath, 'r') as file:
        lines = file.readlines()

    if 'Dictionary form:' in lines[0]:
        return json.loads(lines[1].replace('\n', ''))

def print_saving_verbose(filename, class2save= None, verbose=True):
    """[summary]

    Args:
        filename ([type]): [description]
        class2save ([type], optional): [description]. Defaults to None.
        verbose (bool, optional): [description]. Defaults to True.
    """

    if verbose:
        if hasattr(class2save, 'type'):
            print('\n{} saved in : ...{}'.format(class2save.type, filename[-50:]))
        else:
            print('\n Some data were saved in : ...{}'.format(filename[-50:]))

def print_loading_verbose(filename, classloaded= None, verbose=True):
    """[summary]

    Args:
        filename ([type]): [description]
        classloaded ([type], optional): [description]. Defaults to None.
        verbose (bool, optional): [description]. Defaults to True.
    """
    if verbose:
        if hasattr(classloaded, 'type'):
            print('\n{} object loaded from : ...{}'.format(classloaded.type, filename[-50:]))
        else:
            print('\nSome data were loaded from : ...{}'.format(filename[-50:]))

def createPath(path:str, append_datetime=True) -> str:
    """[summary]

    Args:
        path (str): [description]
        incrementDir (bool, optional): [description]. Defaults to False.
        dateTime (bool, optional): [description]. Defaults to False.

    Returns:
        [type]: [description]
    """
    if append_datetime:        
        path= append_date_time(path)
    if not os.path.exists(path):
        os.mkdir(path)
    return path

def set_attributes(class2upload,loaded_class) -> None:
    if not isinstance(loaded_class, type(class2upload)):
        raise DataLoadedNotCompatibleError(f'loaded data type{type(loaded_class,)}, expected type {type(class2upload)}')

    for key in loaded_class.__dict__.keys():
        setattr(class2upload, key, getattr(loaded_class,key))

if __name__ == "__main__":
    # get_file(filetypes=[(".txt-files", "*.txt")])
    print(os.listdir(getcwd()))

    # print(search_for_file_with_ext(None, ext='.py'))
   
#    import dateutil.parser
#    datestring='aaaaa'#get_date_time()
#    length= len(get_date_time())
#    if len(datestring)>= length:
#         try:
#            yourdate = datetime.datetime.strptime(datestring[-length:], FORMAT_DATE_TIME)
#            print(yourdate)
#            datestring= datestring[:-length]
#            if not datestring:
#                datestring='default'
#         except ValueError:
#             pass

#    print(datestring)



    # path_pkl='E:/EIT_Project/05_Engineering/04_Software/Python/eit_tf_workspace/datasets/20210929_082223_2D_16e_adad_cell3_SNR20dB_50k_dataset/2D_16e_adad_cell3_SNR20dB_50k_infos2py.pkl'
    # # path_pkl=path_pkl.replace('/','\\')
    # print(verify_file(path_pkl, extension=EXT_PKL, debug=True))

    # a= 'print_saving_verbose'
    # print(os.path.splitext('hhhhhhhh'))
    # if os.path.splitext('hhhhhhhh')[1]:
    #     print_saving_verbose('ffffffffffffffffffffff', class2save= None, verbose=True)
    # pass