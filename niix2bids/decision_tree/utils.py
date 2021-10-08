# standard modules
import logging  # logging lib (terminal & file)
import sys      # to stop script execution on case of error
import re       # regular expressions

# dependency modules
import pandas   # for DataFrame

# local modules
from niix2bids.classes import Volume


# get logger with current name
log = logging.getLogger(__name__)


########################################################################################################################
def assemble_list_param(volume_list: list[Volume]) -> list[dict]:

    list_param = []
    for volume in volume_list:
        list_param.append(volume.seqparam)

    return list_param


########################################################################################################################
def assert_is_dcm2niix(df: pandas.DataFrame) -> None:

    is_key_ConversionSoftware = 'ConversionSoftware' in df.columns
    if not is_key_ConversionSoftware:
        log.error(f'no .json file has "ConversionSoftware" field')
        sys.exit(1)

    is_dcm2niix = df['ConversionSoftware'] == 'dcm2niix'
    if not all(is_dcm2niix):
        log.error(f'at least one .json was not generated by "dcm2niix"')
        sys.exit(1)

    log.debug(f'checking in all .json if "ConversionSoftware" == "dcm2niix" done')


########################################################################################################################
def assert_key_val(df: pandas.DataFrame, key: str, value: str) -> None:

    if key not in df.columns:
        log.error(f'"{key}" entry is not present in all .json files')
        sys.exit(1)

    is_value = df[key] == value
    if not all(is_value):
        log.error(f'at least one "{key}" is not "{value}"')
        sys.exit(1)

    log.debug(f'checking in all .json if "{key}" == "{value}" done')


########################################################################################################################
def slice_with_seqname(df: pandas.DataFrame, regex: str) -> pandas.DataFrame:
    return df[df['PulseSequenceDetails'].str.match(regex)]


########################################################################################################################
def slice_with_seriesdescription(df: pandas.DataFrame, regex: str) -> pandas.DataFrame:
    return df[df['SeriesDescription'].str.match(regex)]


########################################################################################################################
def slice_with_seqvariant(df: pandas.DataFrame, regex: str) -> pandas.DataFrame:
    return df[df['SequenceName'].str.match(regex)]


########################################################################################################################
def slice_with_mracquistiontype(df: pandas.DataFrame, regex: str) -> pandas.DataFrame:
    return df[df['MRAcquisitionType'].str.match(regex)]


########################################################################################################################
def slice_with_imagetype(df: pandas.DataFrame, type: str) -> pandas.DataFrame:
    # ImageType exemple :
    # ['ORIGINAL', 'PRIMARY', 'M', 'MB', 'TE1', 'ND', 'MOSAIC']
    #  0           1         >>2<<
    return df[df['ImageType'].apply(lambda x: x[2] == type)]


########################################################################################################################
def clean_name(input_str: str) -> str:
    output_str = re.sub(r'[^A-Za-z0-9]+', '', input_str)
    return output_str
