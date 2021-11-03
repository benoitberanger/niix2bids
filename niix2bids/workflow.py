# standard modules
import argparse                 # just for function signature
import os                       # for path management
import sys                      # to stop script execution on case of error
import time                     # to time execution of code

# dependency modules

# local modules
import niix2bids.decision_tree.siemens
from niix2bids import utils, metadata
from niix2bids.utils import get_logger


########################################################################################################################
def run(args: argparse.Namespace) -> None:

    star_time = time.time()

    # initialize logger (console & file)
    utils.init_logger(args.out_dir, args.logfile)
    log = get_logger()
    log.info(f"niix2bids=={metadata.get_niix2bids_version()}")

    # logs
    log.info(f"in_dir  : {args.in_dir}")
    log.info(f"out_dir : {args.out_dir}")
    if args.logfile:
        log.info(f"logfile : {log.__class__.root.handlers[1].baseFilename}")
    log.info(f"out_dir write method = {args.symlink_or_copyfile}")

    # check if input dir exists
    for one_dir in args.in_dir:
        if not os.path.exists(one_dir):
            log.error(f"in_dir does not exist : {one_dir}")
            sys.exit(1)

    # read all dirs and establish file list
    file_list = utils.fetch_all_files(args.in_dir)

    # isolate .nii files
    file_list_nii = utils.isolate_nii_files(file_list)

    # check if all .nii files have their own .json
    file_list_nii, file_list_json = utils.check_if_json_exists(file_list_nii)

    # create Volume objects
    volume_list = utils.create_volume_list(file_list_nii)

    # read all json files
    utils.read_all_json(volume_list)

    # apply decision tree
    # !! here, only Siemens is implemented !!
    niix2bids.decision_tree.siemens.run(volume_list)

    # perform files operations
    utils.apply_bids_architecture(args.out_dir, volume_list, args.symlink_or_copyfile)

    # write dataset_description.json
    utils.write_bids_dataset_description(args.out_dir)

    # write other files
    utils.write_bids_other_files(args.out_dir)

    stop_time = time.time()

    log.info(f'Total execution time is : {stop_time-star_time:.3f}s')

    # THE END
    sys.exit(0)
