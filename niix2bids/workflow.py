# standard modules
import logging                  # logging lib (terminal & file)
import argparse                 # just for function signature
import os                       # for path management
import sys                      # to stop script execution on case of error
import time                     # to time execution of code

# dependency modules

# local modules
import niix2bids.decision_tree.siemens
from niix2bids import utils


########################################################################################################################
def run(args: argparse.Namespace) -> None:

    star_time = time.time()

    # initialize logger (console & file)
    utils.init_logger(args.out_dir, args.logfile)
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
    file_list = utils.fetch_all_files(args.nifti_dir)

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
    utils.apply_bids_architecture(args.out_dir,volume_list)

    # write dataset_description.json
    utils.write_bids_dataset_description(args.out_dir)

    # write other files
    utils.write_bids_other_files(args.out_dir)

    stop_time = time.time()

    log.info(f'Total execution time is : {stop_time-star_time:.3f}s')

    # THE END
    sys.exit(0)
