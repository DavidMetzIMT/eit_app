from enum import Enum
from glob_utils.directory.inout_dir import DefaultDir, set_default_dir
import os
import pathlib
import logging

logger = logging.getLogger(__name__)

################################################################################
# management of global default directory
################################################################################

DEFAULT_APP_DIR_FILE = "app_default_dirs.txt"
APP_DIRS = DefaultDir()


class AppStdDir(Enum):
    meas_set = "Measurement Sets"
    snapshot = "Snapshot"
    export = "Export"
    eit_model = "EIT Model"
    chips = "Chips"


def set_ai_default_dir(reset: bool = False):
    local_dir = pathlib.Path(__file__).parent.resolve()
    path = os.path.join(local_dir, DEFAULT_APP_DIR_FILE)
    init_dirs = {d.value: "" for d in AppStdDir}
    set_default_dir(reset, APP_DIRS, init_dirs, path)


def get_dir(dir: AppStdDir) -> str:
    return APP_DIRS.get(dir)


if __name__ == "__main__":
    """"""
    from glob_utils.log.log import main_log

    main_log()
    set_ai_default_dir(reset=True)
    print(AppStdDir.meas_set.value)
    print(APP_DIRS.get())
    print(APP_DIRS.get(AppStdDir.meas_set.value))
