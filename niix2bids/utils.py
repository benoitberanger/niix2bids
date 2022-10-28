# standard modules
import logging                  # logging lib (terminal & file)
import os                       # for path management
import shutil                   # for copyfile
from datetime import datetime   # to get current time
import sys                      # to stop script execution on case of error
import re                       # regular expressions
import json                     # to write json files
import time                     # to time execution of code
from functools import wraps     # for decorator
import traceback                # to get the current function name
import inspect                  # to get the current module name
from typing import List, Tuple  # for function signature
import runpy                    # to run config script
import io                       # to save in a string the log output

# dependency modules

# local modules
from niix2bids import metadata
from niix2bids.classes import Volume


########################################################################################################################
def init_logger(write_file: bool, out_dir: str, store_report: bool = False) -> None:

    # create logger
    log = logging.getLogger()
    log.setLevel(logging.DEBUG)

    # create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)-55s - %(levelname)-8s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')

    handler_base_name = 'niix2bids'

    # create console handler
    consoleHandler = logging.StreamHandler(sys.stdout)
    consoleHandler.set_name(f'{handler_base_name}_console')
    consoleHandler.setLevel(logging.DEBUG)
    consoleHandler.setFormatter(formatter)
    log.addHandler(consoleHandler)

    # same thing but for a file handler
    if write_file:
        upperstack = inspect.stack()[1]
        mdl_name = inspect.getmodule(upperstack[0]).__name__.split('.')[0]  # get module name of the module calling
        logfile = os.path.join(out_dir, datetime.now().strftime('%Y-%m-%d_%Hh%Sm%S') + "_" + mdl_name + ".log")

        fileHandeler = logging.FileHandler(logfile)
        fileHandeler.set_name(f'{handler_base_name}_file')
        fileHandeler.setLevel(logging.DEBUG)
        fileHandeler.setFormatter(formatter)
        log.addHandler(fileHandeler)

    # store log into a string variable for later usage
    if store_report:
        report_stream = io.StringIO()
        reportHandler = logging.StreamHandler(report_stream)
        reportHandler.set_name(f'{handler_base_name}_report')
        reportHandler.setLevel(logging.DEBUG)
        reportHandler.setFormatter(formatter)
        log.addHandler(reportHandler)


########################################################################################################################
def get_logger() -> logging.Logger:

    fcn_name = traceback.extract_stack(None, 2)[0][2]  # get function name of the caller

    upperstack = inspect.stack()[1]
    mdl_name = inspect.getmodule(upperstack[0]).__name__  # get module name of the caller

    name = mdl_name + ':' + fcn_name  # ex : niix2bids.utils:apply_bids_architecture
    log = logging.getLogger(name)

    return log


########################################################################################################################
def logit(message, level=logging.INFO):

    def log_time(func):

        @wraps(func)  # to keep function info, such as __name__
        def wrapper(*args, **kwargs):

            display_name = func.__module__ + ':' + func.__name__
            log = logging.getLogger(display_name)
            
            log.log(level, message + ' # start...')

            start_time = time.time()
            res = func(*args, **kwargs)
            stop_time = time.time()

            log.log(level, message + f" # ...done in {stop_time-start_time:.3f}s")

            return res

        return wrapper

    return log_time


########################################################################################################################
def load_config_file(config_file: str) -> list:
    log = get_logger()

    fpath = ''
    if type(config_file) is list:
        for idx, file in enumerate(config_file):
            log.info(f"Trying config_file location : {file}")
            if os.path.exists(file):
                fpath = file
    else:
        log.info(f"Trying config_file location : {config_file}")
        if os.path.exists(config_file):
            fpath = config_file

    if fpath == '':
        log.critical(f"No config file found")
        sys.exit(1)

    script_content = runpy.run_path(fpath)
    if "config" in script_content:
        config = script_content['config']
        log.info(f"Using config_file : {fpath}")
        return config
    else:
        log.critical(f"Config_file incorrect (no 'config' variable inside) : {fpath}")
        sys.exit(1)


########################################################################################################################
@logit('Fetch all files recursively. This might take time, it involves exploring the whole disk tree.', logging.INFO)
def fetch_all_files(in_dir: str) -> List[str]:

    file_list = []
    for one_dir in in_dir:
        for root, dirs, files in os.walk(one_dir):
            for file in files:
                file_list.append(os.path.join(root, file))

    if len(file_list) == 0:
        log = get_logger()
        log.error(f"no file found in {in_dir}")
        sys.exit(1)

    file_list.sort()
    return file_list


########################################################################################################################
@logit('Keep only nifti files (.nii, .nii.gz).', logging.INFO)
def isolate_nii_files(in_list: List[str]) -> List[str]:
    log = get_logger()

    r = re.compile(r"(.*nii$)|(.*nii.gz$)$")
    file_list_nii = list(filter(r.match, in_list))

    log.info(f"found {len(file_list_nii)} nifti files")
    if len(file_list_nii) == 0:
        log.error(f"no .nii file found in {in_list}")
        sys.exit(1)

    return file_list_nii


########################################################################################################################
@logit('Check if .json exist for each nifti file.', logging.INFO)
def check_if_json_exists(file_list_nii: List[str]) -> Tuple[List[str], List[str]]:
    log = get_logger()

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
@logit('Creation of internal object that will store all info, 1 per nifti.', logging.DEBUG)
def create_volume_list(file_list_nii: List[str]) -> List[Volume]:

    for file in file_list_nii:
        Volume(file)

    return Volume.instances


########################################################################################################################
@logit('Read all .json files. This step might take time, it involves reading lots of files', logging.INFO)
def read_all_json(volume_list: List[Volume]) -> None:

    log = get_logger()

    to_pop = []
    for volume in volume_list:
        try:
            volume.load_json()
        except json.JSONDecodeError:
            log.critical(f"json have bad syntax : {volume.json.path}")
            to_pop.append(volume)

    # remove the Volume object for the instance list, so it will be "forgotten"
    [Volume.instances.remove(elem) for elem in to_pop]


########################################################################################################################
def assemble_bids_name(vol: Volume) -> str:

    bidsfields = ''
    for key, value in vol.bidsfields.items():
        bidsfields += '_' + key + '-' + str(value)

    if len(vol.suffix) > 0:
        # name = 'sub-' + vol.sub + bidsfields + '_' + vol.suffix
        name = f"sub-{vol.sub}_ses-{vol.ses}{bidsfields}_{vol.suffix}"
    else:
        # name = 'sub-' + vol.sub + bidsfields
        name = f"sub-{vol.sub}{bidsfields}"

    return name


########################################################################################################################
def write_json(out_path_json: str, json_dict: str) -> None:
    if not os.path.exists(out_path_json):
        with open(out_path_json, 'w') as fp:        # write file
            json.dump(json_dict, fp, indent=4)      # indent for prettiness
            fp.write('\n')                          # for prettiness too


########################################################################################################################
def ln_or_cp_file(symlink_or_copyfile: str, in_path: str, out_path: str) -> None:

    if not os.path.exists(out_path):
        if symlink_or_copyfile == "symlink":
            os.symlink(in_path, out_path)
        elif symlink_or_copyfile == "copyfile":
            shutil.copyfile(in_path, out_path)
        else:
            raise RuntimeError('??? coding error')


########################################################################################################################
@logit('Apply BIDS architecture. This might take time, it involves lots of disk writing.', logging.INFO)
def apply_bids_architecture(out_dir: str, volume_list: List[Volume], symlink_or_copyfile: str) -> None:

    log                       = get_logger()
    log_info                  = []
    log_info_discard          = []
    log_warning               = []
    log_warning_unknown       = []
    log_error_not_interpreted = []

    for vol in volume_list:

        if len(vol.tag) > 0:  # only process correctly parsed volumes

            if vol.tag == 'DISCARD':
                dir_path = os.path.join(
                    out_dir,
                    'DISCARD')
                log_info_discard.append(f'{vol.reason_not_ready} : {vol.nii.path}')

            elif vol.tag == 'UNKNOWN':
                dir_path = os.path.join(
                    out_dir,
                    'UNKNOWN')
                log_warning_unknown.append(f'{vol.reason_not_ready} : {vol.nii.path}')

            else:
                dir_path = os.path.join(
                    out_dir,
                    f"sub-{vol.sub}",
                    f"ses-{vol.ses}",
                    vol.tag)

            # recursive directory creation, and do not raise error if already exists
            os.makedirs(dir_path, exist_ok=True)

            out_name = assemble_bids_name(vol)

            # ----------------------------------------------------------------------------------------------------------
            # nii
            in_path_nii = vol.nii.path
            out_path_nii = os.path.join(dir_path, out_name + vol.ext)
            ln_or_cp_file(symlink_or_copyfile, in_path_nii, out_path_nii)

            # ----------------------------------------------------------------------------------------------------------
            # json
            in_path_json = vol.json.path
            out_path_json = os.path.join(dir_path, out_name + '.json')

            if vol.tag == 'func':
                # for func, the .json file needs to have 'TaskName' field
                json_dict = vol.seqparam                        # copy original the json dict
                del json_dict['Volume']                         # remove the pointer to Volume instance
                json_dict['TaskName'] = vol.bidsfields['task']  # add TaskName
                write_json(out_path_json, json_dict)

            elif vol.tag == 'fmap' and vol.suffix == 'phasediff':
                # for fmap, the phasediff .json must contain EchoTime1 and EchoTime2
                # in Siemens gre_field_mapping, EchoTime2-EchoTime1 = 2.46ms. This seems constant
                json_dict = vol.seqparam
                del json_dict['Volume']
                json_dict['EchoTime1'] = json_dict['EchoTime'] - 0.00246
                json_dict['EchoTime2'] = json_dict['EchoTime']
                write_json(out_path_json, json_dict)

            else:
                ln_or_cp_file(symlink_or_copyfile, in_path_json, out_path_json)

            # ----------------------------------------------------------------------------------------------------------
            # bval
            if hasattr(vol, 'bval'):
                in_path_bval = vol.bval.path
                out_path_bval = os.path.join(dir_path, out_name + '.bval')
                ln_or_cp_file(symlink_or_copyfile, in_path_bval, out_path_bval)

            # ----------------------------------------------------------------------------------------------------------
            # bvec
            if hasattr(vol, 'bvec'):
                in_path_bvec = vol.bvec.path
                out_path_bvec = os.path.join(dir_path, out_name + '.bvec')
                ln_or_cp_file(symlink_or_copyfile, in_path_bvec, out_path_bvec)

        elif len(vol.reason_not_ready) > 0:
            log_warning.append(f'{vol.reason_not_ready} : {vol.nii.path}')

        else:
            log_error_not_interpreted.append(f'file not interpreted : {vol.nii.path}')

    # print them all, but in order
    for msg in log_error_not_interpreted:
        log.error(msg)
    for msg in log_warning_unknown:
        log.warning(msg)
    for msg in log_warning:
        log.warning(msg)
    # for msg in log_info_discard:
    #     log.info(msg)
    for msg in log_info:
        log.info(msg)


########################################################################################################################
@logit('Writing dataset_description.json', logging.INFO)
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
@logit('Writing README, CHANGES, LICENSE, .bidsignore files', logging.INFO)
def write_bids_other_files(out_dir: str) -> None:

    # README
    with open(os.path.join(out_dir, 'README'), 'w') as fp:
        fp.write(f"GeneratedBy : niix2bids=={metadata.get_niix2bids_version()} \n")
        fp.write(f"BIDSVersion : {metadata.get_bids_version()} \n")

    # CHANGES
    with open(os.path.join(out_dir, 'CHANGES'), 'w') as fp:
        fp.write(f"1.0.0 {datetime.now().strftime('%Y-%m-%d')} \n")
        fp.write(f"  - Initial release \n")

    # LICENSE
    with open(os.path.join(out_dir, 'LICENSE'), 'w') as fp:
        fp.write('PDDL \n')

    # .bidsignore
    with open(os.path.join(out_dir, '.bidsignore'), 'w') as fp:
        fp.write('*.log \n')
        fp.write('UNKNOWN \n')
        fp.write('DISCARD \n')
