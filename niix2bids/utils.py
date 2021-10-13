# standard modules
import logging                  # logging lib (terminal & file)
import os                       # for path management
from datetime import datetime   # to get current time
import sys                      # to stop script execution on case of error
import re                       # regular expressions
import json                     # to write json files
import time                     # to time execution of code

# dependency modules

# local modules
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
    log.info(f"niix2bids=={metadata.get_niix2bids_version()}")

    # same thing but for a file handler
    if write_file:
        logfile = os.path.join(out_dir, "log_" + datetime.now().strftime('%Y-%m-%d_%Hh%Sm%S') + ".txt")

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

    r = re.compile(r"(.*nii$)|(.*nii.gz$)$")
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
        root, ext = os.path.splitext(file)
        if ext == ".gz":
            jsonfile = os.path.splitext(root)[0] + ".json"
        else:
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

    log = logging.getLogger(__name__)

    log.debug(f"start reading all JSON files...")
    start_time = time.time()
    for volume in volume_list:
        volume.load_json()
    stop_time = time.time()
    log.debug(f"... done")
    log.debug(f"reading all JSON took in {stop_time-start_time: .3f} seconds")


########################################################################################################################
def assemble_bids_key_value_pairs(bidsfields: dict) -> str:

    i = 0
    for key, value in bidsfields.items():
        i += 1
        if i == 1:  # sub- (initialization)
            name = key + '-' + str(value)
        elif key == 'suffix':
            name += '_' + str(value)
        elif key == 'tag':  # this is the name of the dir, like anat, dwi, bold, ...
            pass
        else:
            name += '_' + key + '-' + str(value)

    return name


########################################################################################################################
def apply_bids_architecture(out_dir: str,volume_list: list[Volume]) -> None:

    for vol in volume_list:
        if bool(vol.bidsfields):  # only process correctly parsed volumes

            dir_path = os.path.join(
                out_dir,
                "sub-" + vol.bidsfields['sub'],
                vol.bidsfields["tag"])

            # recursive directory creation, and do not raise error if already exists
            os.makedirs(dir_path, exist_ok=True)

            out_name = assemble_bids_key_value_pairs(vol.bidsfields)

            # ----------------------------------------------------------------------------------------------------------
            # nii
            in_path_nii = vol.nii.path
            out_path_nii = os.path.join(dir_path, out_name + vol.ext)
            if not os.path.exists(out_path_nii):
                os.symlink(in_path_nii, out_path_nii)

            # ----------------------------------------------------------------------------------------------------------
            # json
            in_path_json = vol.json.path
            out_path_json = os.path.join(dir_path, out_name + '.json')

            if vol.bidsfields['tag'] == 'func':
                # for func, the .json file needs to have 'TaskName' field
                json_dict = vol.seqparam                        # copy original the json dict
                del json_dict['Volume']                         # remove the pointer to Volume instance
                json_dict['TaskName'] = vol.bidsfields['task']  # add TaskName
                if not os.path.exists(out_path_json):
                    with open(out_path_json, 'w') as fp:        # write file
                        json.dump(json_dict, fp, indent=4)      # indent for prettiness
                        fp.write('\n')                          # for prettiness too

            elif vol.bidsfields['tag'] == 'fmap' and vol.bidsfields['suffix'] == 'phasediff':
                # for fmap, the phasediff .json must contain EchoTime1 and EchoTime2
                # in Siemens gre_field_mapping, EchoTime2-EchoTime1 = 2.46ms. This seems constant
                json_dict = vol.seqparam
                del json_dict['Volume']
                json_dict['EchoTime1'] = json_dict['EchoTime'] - 0.00246
                json_dict['EchoTime2'] = json_dict['EchoTime']
                if not os.path.exists(out_path_json):
                    with open(out_path_json, 'w') as fp:
                        json.dump(json_dict, fp, indent=4)
                        fp.write('\n')

            else:
                if not os.path.exists(out_path_json):
                    os.symlink(in_path_json, out_path_json)

            # ----------------------------------------------------------------------------------------------------------
            # bval
            if hasattr(vol, 'bval'):
                in_path_bval = vol.bval.path
                out_path_bval = os.path.join(dir_path, out_name + '.bval')
                if not os.path.exists(out_path_bval):
                    os.symlink(in_path_bval, out_path_bval)

            # ----------------------------------------------------------------------------------------------------------
            # bvec
            if hasattr(vol, 'bvec'):
                in_path_bvec = vol.bvec.path
                out_path_bvec = os.path.join(dir_path, out_name + '.bvec')
                if not os.path.exists(out_path_bvec):
                    os.symlink(in_path_bvec, out_path_bvec)


########################################################################################################################
def write_bids_dataset_description(out_dir: str) -> None:

    dataset_description = {
        'Name': '',
        'BIDSVersion': metadata.get_bids_version(),
        'HEDVersion': '',
        'DatasetType': 'raw',
        'License': 'PDDL',
        'Authors': [''],
        'Acknowledgements': '',
        'HowToAcknowledge': '',
        'Funding': [''],
        'EthicsApprovals': [''],
        'ReferencesAndLinks': [''],
        'DatasetDOI': '',
    }

    with open(os.path.join(out_dir, 'dataset_description.json'), 'w') as fp:
        json.dump(dataset_description, fp, indent=4)  # indent is for prettiness
        fp.write('\n')                                # for prettiness too


########################################################################################################################
def write_bids_other_files(out_dir: str) -> None:

    # README
    with open(os.path.join(out_dir,'README'), 'w') as fp:
        fp.write(f"GeneratedBy : niix2bids=={metadata.get_niix2bids_version()} \n")
        fp.write(f"BIDSVersion : {metadata.get_bids_version()} \n")

    # CHANGES
    with open(os.path.join(out_dir,'CHANGES'), 'w') as fp:
        fp.write(f"1.0.0 {datetime.now().strftime('%Y-%m-%d')} \n")
        fp.write(f"  - Initial release \n")

    # LICENSE
    with open(os.path.join(out_dir,'LICENSE'), 'w') as fp:
        fp.write('PDDL \n')
