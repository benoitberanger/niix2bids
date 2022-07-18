# standard modules
import sys               # to stop script execution on case of error
import re                # regular expressions
from typing import List  # for function signature

# dependency modules
import pandas as pd # for DataFrame

# local modules
from niix2bids.classes import Volume
from niix2bids.utils import get_logger


########################################################################################################################
def assemble_list_param(volume_list: List[Volume]) -> List[dict]:

    return [vol.seqparam for vol in volume_list]


########################################################################################################################
def sanity_check(df: pd.DataFrame) -> pd.DataFrame:

    # ConversionSoftware ? ConversionSoftware == dcm2niix ?
    df = check_key(df=df, key='ConversionSoftware', val='dcm2niix')

    # PatientName ?
    df = check_key(df=df, key='PatientName',
                   msg=f'No .json file has "PatientName" field. When using dcm2niix, use "-ba n" option.')

    # Modality ? Modality == MR ?
    df = check_key(df=df, key='Modality', val='MR')

    # Manufacturer ? Manufacturer == Siemens ?
    df = check_key(df=df, key='Manufacturer', val='Siemens')

    # PulseSequenceDetails ? this is the basic sequence name : %SiemensSeq%_gre
    df = check_key(df=df, key='PulseSequenceDetails')

    # SequenceName ? example : 'fl3d12r_ns'
    df = check_key(df=df, key='SequenceName')

    # MRAcquisitionType ? example : '2D', '3D'
    df = check_key(df=df, key='MRAcquisitionType')

    return df


########################################################################################################################
def check_key(df: pd.DataFrame, key: str, msg: str = '', val: str = '') -> pd.DataFrame:

    log = get_logger()

    if len(msg) == 0:
        msg = f'No .json file has "{key}" field. Please use "dcm2niix" : https://github.com/rordenlab/dcm2niix'

    is_key_present = key in df.columns
    if not is_key_present:
        log.error(msg)
        sys.exit(1)
    for row_idx, seq in df.iterrows():
        if pd.isna(seq[key]):
            vol                   = seq['Volume']
            vol.tag               = ''
            vol.reason_not_ready  = f'no "{key}"'
            df = df.drop(row_idx)
        elif len(val) > 0 and seq[key] != val:
            vol                   = seq['Volume']
            vol.tag               = ''
            vol.reason_not_ready  = f'"{key}" != "{val}"'
            df = df.drop(row_idx)

    return df


########################################################################################################################
def slice_with_genericfield(df: pd.DataFrame, fieldname: str, regex: str) -> pd.DataFrame:
    return df[df[fieldname].str.match(regex)]


########################################################################################################################
def slice_with_mracquistiontype(df: pd.DataFrame, regex: str) -> pd.DataFrame:
    return df[df['MRAcquisitionType'].str.match(regex)]


########################################################################################################################
def slice_with_imagetype(df: pd.DataFrame, imagetype: str) -> pd.DataFrame:
    """
    ImageType example :
    ['ORIGINAL', 'PRIMARY', 'M', 'MB', 'TE1', 'ND', 'MOSAIC']
     0           1         >>2<<
     """
    return df[df['ImageType'].apply(lambda x: x[2] == imagetype)]


########################################################################################################################
def slice_with_imagetype_original(df: pd.DataFrame) -> pd.DataFrame:
    """
    ImageType example :
    ['ORIGINAL', 'PRIMARY', 'M', 'MB', 'TE1', 'ND', 'MOSAIC']
     >>here<<
     """
    return df[df['ImageType'].apply(lambda x: x[0] == "ORIGINAL")]


########################################################################################################################
def clean_name(input_str: str) -> str:
    """
    remove all non-alphanumerical character
    """
    output_str = re.sub(r'[^A-Za-z0-9]+', '', input_str)
    return output_str


########################################################################################################################
def get_phase_encoding_direction(input_str: str) -> str:
    if input_str == 'j':
        return 'PA'
    if input_str == 'j-':
        return 'AP'
    if input_str == 'i':
        return 'LR'
    if input_str == 'i-':
        return 'RL'


########################################################################################################################
def keep_ndim(df: pd.DataFrame, ndim: str) -> pd.DataFrame:
    df_ND = slice_with_genericfield(df, 'MRAcquisitionType', ndim)
    df_bad = df.drop(df_ND.index)
    for _, seq in df_bad.iterrows():
        vol                   = seq['Volume']
        vol.reason_not_ready  = f"non-{ndim} acquisition with PulseSequenceDetails = {seq['PulseSequenceDetails']}"
    return df_ND


########################################################################################################################
def fill_echonumber(df: pd.DataFrame, value: int = -1) -> pd.DataFrame:
    """
    DataFrame CANNOT iterate overs groups with nan.
    So here is a workaround, replace NaN with -1
    """
    nan_in_EchoNumber = pd.isna(df['EchoNumber'])
    if any(nan_in_EchoNumber):
        pd.options.mode.chained_assignment = None  # because of super onnoying warning that appears in some case but not all...
        df['EchoNumber'] = df['EchoNumber'].fillna(value)
        pd.options.mode.chained_assignment = 'warn'
    return df


########################################################################################################################
def get_mag_or_pha(df: pd.DataFrame) -> str:
    mag_or_pha = df["ImageTypeStr"].split('_')[2]
    if mag_or_pha == 'M':
        suffix = 'mag'
    elif mag_or_pha == 'P':
        suffix = 'phase'
    else:
        suffix = ''
    return suffix


########################################################################################################################
def get_echo_number(df: pd.DataFrame, has_EchoNumber: bool) -> int:
    if has_EchoNumber:
        echo = int(df['EchoNumber'])
    else:
        echo = -1
    return echo


########################################################################################################################
def complete_columns_with_echonumber(columns: list, df: pd.DataFrame) -> [list, pd.DataFrame, bool] :
    has_EchoNumber = 'EchoNumber' in df.columns
    if has_EchoNumber:
        columns.append('EchoNumber')
        df = fill_echonumber(df)
    return columns, df, has_EchoNumber
