# standard modules
import logging                  # logging lib (terminal & file)
import argparse                 # just for function signature
import os                       # for path management
from datetime import datetime   # to get current time
import sys                      # to stop script execution on case of error
import re                       # regular expressions
import time                     # to time execution of code

# dependency modules

# local modules
import niix2bids.decision_tree.siemens
from niix2bids import metadata
from niix2bids.classes import Volume


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
        logfile = os.path.join(out_dir, "log_" + timestamp + ".txt")

        fileHandeler = logging.FileHandler(logfile)
        fileHandeler.setLevel(logging.DEBUG)
        fileHandeler.setFormatter(formatter)
        log.addHandler(fileHandeler)


########################################################################################################################
def fetch_all_files(in_dir: str) -> list[str]:

    file_list = []
    for root, dirs, files in os.walk(in_dir):
        for file in files:
            file_list.append(os.path.join(root, file))

    if len(file_list) == 0:
        log = logging.getLogger(__name__)
        log.error(f"no file found in {in_dir}")
        sys.exit(1)

    file_list.sort()
    return file_list


########################################################################################################################
def isolate_nii_files(in_list: list[str]) -> list[str]:
    log = logging.getLogger(__name__)

    r = re.compile(r".*nii$")
    file_list_nii = list(filter(r.match, in_list))

    log.info(f"found {len(file_list_nii)} nifti files")
    if len(file_list_nii) == 0:
        log.error(f"no .nii file found in {in_list}")
        sys.exit(1)

    return file_list_nii


########################################################################################################################
def check_if_json_exists(file_list_nii: list[str]) -> tuple[list[str], list[str]]:
    log = logging.getLogger(__name__)

    file_list_json = []
    for file in file_list_nii:
        jsonfile = os.path.splitext(file)[0] + ".json"
        if not os.path.exists(jsonfile):
            log.warning(f"this file has no .json associated : {file}")
            file_list_nii.remove(file)
        else:
            file_list_json.append(jsonfile)

    log.info(f"remaining {len(file_list_nii)} nifti files")
    return file_list_nii, file_list_json


########################################################################################################################
def create_volume_list(file_list_nii: list[str]) -> list[Volume]:

    for file in file_list_nii:
        Volume(file)

    return Volume.instances


########################################################################################################################
def read_all_json(volume_list: list[Volume]) -> None:

    for volume in volume_list:
        volume.load_json()


########################################################################################################################
def assemble_list_param(volume_list: list[Volume]) -> list[dict]:

    list_param = []
    for volume in volume_list:
        list_param.append(volume.param)

    return list_param


########################################################################################################################
def run(args: argparse.Namespace) -> None:

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
        sys.exit(1)

    # read all dirs and establish file list
    file_list = fetch_all_files(args.nifti_dir)

    # isolate .nii files
    file_list_nii = isolate_nii_files(file_list)

    # check if all .nii files have their own .json
    file_list_nii, file_list_json = check_if_json_exists(file_list_nii)

    # create Volume objects
    volume_list = create_volume_list(file_list_nii)

    # read all json files
    log.debug(f"start reading all JSON files...")
    start_time = time.time()
    read_all_json(volume_list)
    stop_time = time.time()
    log.debug(f"... done")
    log.debug(f"reading all JSON took in {stop_time-start_time: .3f} seconds")

    # regroup all param form each json into one list for easy access
    list_param = assemble_list_param(volume_list)

    # apply decision tree
    job = niix2bids.decision_tree.siemens.run(list_param)

    # THE END
    sys.exit(0)
