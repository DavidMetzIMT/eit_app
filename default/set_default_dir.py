

from enum import Enum
from glob_utils.pth.inout_dir import DefaultDir, set_default_dir
import os
import pathlib
from logging import getLogger
logger = getLogger(__name__)

################################################################################
# management of global default directory
################################################################################

DEFAULT_APP_DIR_FILE='app_default_dirs.txt'
APP_DIRS= DefaultDir()

class AppDirs(Enum):
    meas_set='Measurement Sets'
    snapshot='Snapshot'
    export='Export'

def set_ai_default_dir(reset:bool= False):
    local_dir= pathlib.Path(__file__).parent.resolve()
    path= os.path.join(local_dir, DEFAULT_APP_DIR_FILE)
    init_dirs={ d.value:'' for d in AppDirs}
    set_default_dir(reset, APP_DIRS, init_dirs, path)

if __name__ == "__main__":
    """"""
    from glob_utils.log.log import main_log
    main_log()
    set_ai_default_dir(reset=True)  
    print(AppDirs.meas_set.value)
    print(APP_DIRS.get())
    print(APP_DIRS.get(AppDirs.meas_set.value))
    