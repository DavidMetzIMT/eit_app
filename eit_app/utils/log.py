#!/usr/bin/env python3

import logging
import sys

logger = logging.getLogger()

# http://stackoverflow.com/a/24956305/1076493
# filter messages lower than level (exclusive)
class MaxLevelFilter(logging.Filter):
    def __init__(self, level):
        self.level = level

    def filter(self, record):
        return record.levelno < self.level

def main_log(logfile:str='debug.log'):
    # redirect messages to either stdout or stderr based on loglevel
    # stdout < logging.WARNING <= stderr
    format_long = logging.Formatter('%(asctime)s %(levelname)s [%(threadName)s] [%(module)s]: %(message)s')
    format_short = logging.Formatter('%(levelname)s [%(module)s]: %(message)s')
    
    logging_out_h = logging.StreamHandler(sys.stdout)
    logging_err_h = logging.StreamHandler(sys.stderr)
    logging_file_h = logging.FileHandler(logfile)
    logging_out_h.setFormatter(format_short)
    logging_err_h.setFormatter(format_short)
    logging_file_h.setFormatter(format_long)

    logging_out_h.addFilter(MaxLevelFilter(logging.WARNING))
    logging_out_h.setLevel(logging.WARNING)
    logging_err_h.setLevel(logging.WARNING)
    logging_file_h.setLevel(logging.DEBUG)

    # root logger, no __name__ as in submodules further down the hierarchy
    global logger
    logger.addHandler(logging_out_h)
    logger.addHandler(logging_err_h)
    logger.addHandler(logging_file_h)
    logger.setLevel(logging.DEBUG)


if __name__ == '__main__':
    main_log()