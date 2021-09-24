# standard modules
import logging                  # logging lib (terminal & file)
from argparse import Namespace  # just for function signature
import os                       # for path management
from datetime import datetime   # to get current time
import sys                      # to stop script execution on case of error
import re                       # regular expressions

# local modules
from niix2bids import metadata

# dependency modules


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

    # create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # create console handler
    consoleHandler = logging.StreamHandler()  # create
    consoleHandler.setLevel(logging.DEBUG)    # and set level to debug
    consoleHandler.setFormatter(formatter)    # add formatter handlers
    log.addHandler(consoleHandler)            # add handlers to logger

    # first log msg !
    log.info(f"niix2buids version {metadata.get_version()}")

    # same thing but for a file handler
    if write_file:
        timestamp = datetime.now().strftime('%Y-%m-%d_%Hh%Sm%S')
        logfile = os.path.join(out_dir, "log_" + timestamp + ".txt" )

        fileHandeler = logging.FileHandler(logfile)
        fileHandeler.setLevel(logging.DEBUG)
        fileHandeler.setFormatter(formatter)
        log.addHandler(fileHandeler)


########################################################################################################################
def fetch_all_files(dir: str) -> list:
    file_list = []
    for root, dirs, files in os.walk(dir):
        for file in files:
            file_list.append(os.path.join(root, file))
    file_list.sort()
    return file_list


########################################################################################################################
def run(args: Namespace) -> None:

    # initialize logger (console & file)
    init_logger(args.out_dir, args.logfile)
    log = logging.getLogger(__name__)

    # logs
    log.info(f"nifti_dir : {args.nifti_dir}")
    log.info(f"out_dir   : {args.out_dir  }")
    if args.logfile:
        log.info(f"logfile   : {args.out_dir  }")

    # check if input dir exists
    if not os.path.exists(args.nifti_dir):
        log.error(f"nifti_dir does not exist : {args.nifti_dir}")
        sys.exit()

    # read all dirs and establish file list
    file_list = fetch_all_files(args.nifti_dir)

    # isolate .nii files
    r = re.compile(r".*nii$")
    file_list_nii = list(filter(r.match,file_list))
    log.info(f"found {len(file_list_nii)} nifti files")
    if len(file_list_nii)==0:
        log.error(f"no .nii file found in {args.nifti_dir}")
        sys.exit()