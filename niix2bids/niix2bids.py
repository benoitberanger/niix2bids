import logging                  # logging lib (terminal & file)
from argparse import Namespace  # just for function signature
import os                       # for path management
from datetime import datetime   # to get current time


########################################################################################################################
def format_args(args: Namespace) -> Namespace:
    args.nifti_dir = os.path.abspath(args.nifti_dir)
    args.out_dir   = os.path.abspath(args.out_dir  )
    return args


########################################################################################################################
def init_logger(out_dir: str, write_file: bool):

    # create output dir id needed
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)

    # create logger
    log = logging.getLogger()
    log.setLevel(logging.DEBUG)

    # create console handler and set level to debug
    consoleHandler = logging.StreamHandler()
    consoleHandler.setLevel(logging.DEBUG)

    # create file handler and set level to debug
    if write_file:
        timestamp = datetime.now().strftime('%Y-%m-%d_%Hh%Sm%S')
        logfile = os.path.join(out_dir, "log_" + timestamp + ".txt" )
        fileHandeler = logging.FileHandler(logfile)
        fileHandeler.setLevel(logging.DEBUG)

    # create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # add formatter to all handlers
    consoleHandler.setFormatter(formatter)
    if write_file:
        fileHandeler.setFormatter(formatter)

    # add handlers to logger
    log.addHandler(consoleHandler)
    if write_file:
        log.addHandler(fileHandeler)


########################################################################################################################
def workflow(args: Namespace) -> None:

    init_logger(args.out_dir, args.logfile)
    log = logging.getLogger(__name__)

    log.info(f"nifti_dir : {args.nifti_dir}")
    log.info(f"out_dir   : {args.out_dir  }")
    log.info(f"logfile   : {args.out_dir  }")
