# standard modules
import logging  # logging lib (terminal & file)

# dependency modules
import pandas

# local modules
from niix2bids.decision_tree import utils
from niix2bids.classes import Volume

# get logger with current name
log = logging.getLogger(__name__)


########################################################################################################################
def mprage(df: pandas.DataFrame, seq_regex: str):
    seq_info = utils.slice_with_seqname(df, seq_regex)

    # in case of mp2rage, there are 3 (or 4 wih T1map) images generated
    # the SeriesDescription is automatically generated such as ProtocalName + suffix, where suffix = _INV1, _INV2,
    # _UNI_Images (and _T1_Images)
    suffix_regex = ['.*_INV1$', '.*_INV2$', '.*_T1_Images$', '.*_UNI_Images$']
    suffix_list  = ['inv1'    ,  'inv2'   , 'T1map'        , 'UNIT1'         ]
    for suffix in suffix_regex:
        seq_suffix = utils.slice_with_seriesdescription(seq_info, suffix)
        idx = 0
        for row_idx, seq in seq_suffix.iterrows():
            idx += 1
            vol = seq['Volume']
            vol.bidsfields['sub'] = utils.clean_name(seq['PatientName'])
            vol.bidsfields['ses'] = '01'
            vol.bidsfields['tag'] = 'anat'
            vol.bidsfields['acq'] = utils.clean_name(seq['ProtocolName'])
            vol.bidsfields['run'] = idx
            vol.bidsfields['suffix'] = suffix_list[suffix_regex.index(suffix)]
            seq_info = seq_info.drop(row_idx)

    # now that we have dealt with the mp2rage@siemens suffix, we can continue
    idx = 0
    for row_idx, seq in seq_info.iterrows():
        idx += 1
        vol = seq['Volume']
        vol.bidsfields['sub'] = utils.clean_name(seq['PatientName'])
        vol.bidsfields['ses'] = '01'
        vol.bidsfields['tag'] = 'anat'
        vol.bidsfields['acq'] = utils.clean_name(seq['ProtocolName'])
        vol.bidsfields['run'] = idx
        vol.bidsfields['suffix'] = 'T1w'


########################################################################################################################
def tse_vfl(df: pandas.DataFrame, seq_regex: str):
    seq_info = utils.slice_with_seqname(df, seq_regex)

    seq_info_T2w   = utils.slice_with_seqvariant(seq_info, '_spc_')
    seq_info_FLAIR = utils.slice_with_seqvariant(seq_info, '_spcir_')

    idx = 0
    for row_idx, seq in seq_info_T2w.iterrows():
        idx += 1
        vol = seq['Volume']
        vol.bidsfields['sub'] = utils.clean_name(seq['PatientName'])
        vol.bidsfields['ses'] = '01'
        vol.bidsfields['tag'] = 'anat'
        vol.bidsfields['acq'] = utils.clean_name(seq['ProtocolName'])
        vol.bidsfields['run'] = idx
        vol.bidsfields['suffix'] = 'T2w'

    idx = 0
    for row_idx, seq in seq_info_FLAIR.iterrows():
        idx += 1
        vol = seq['Volume']
        vol.bidsfields['sub'] = utils.clean_name(seq['PatientName'])
        vol.bidsfields['ses'] = '01'
        vol.bidsfields['tag'] = 'anat'
        vol.bidsfields['acq'] = utils.clean_name(seq['ProtocolName'])
        vol.bidsfields['run'] = idx
        vol.bidsfields['suffix'] = 'FLAIR'


########################################################################################################################
def run(volume_list: list[Volume]) -> str:

    log.info(f'starting decision tree for "Siemens"... ')

    list_param = utils.assemble_list_param(volume_list)

    # conversion of list[dict] to pandas.DataFrame
    # to pandas.DataFrame object is like table in matlab, with much more embedded methods
    df = pandas.DataFrame(list_param)

    # checks
    utils.assert_is_dcm2niix(df)
    utils.assert_key_val(df, "Modality"    , "MR"     )
    utils.assert_key_val(df, "Manufacturer", "Siemens")

    # make some extraction / conversion
    # %CustomerSeq%_cmrr_mbep2d_bold -> cmrr_mbep2d_bold
    df['PulseSequenceDetails'] = df['PulseSequenceDetails'].apply(lambda s: s.rsplit("%_")[1])

    list_seq_regex = [
        ['^tfl$'              , 'mprage' ],  # mprage & mp2rage
        ['.*mp2rage.*'        , 'mprage' ],  # mp2rage WIP
        ['^tse_vfl$'          , 'tse_vfl'],  # 3DT2 space & 3DFLAIR space_ir
        # ['diff'             , 'diff'   ],  # diffusion
        # ['(bold)|(pace)'    , 'bold'   ],  # bold fmri
        # ['gre_field_mapping', 'fmap'   ],  # dual echo field map
        # ['^gre$'            , 'gre'    ],  # FLASH
        # ['^icm_gre$'        , 'gre'    ],  # FLASH specific at ICM, with better phase reconstruction, will be used for QSM
        # ['^tse$'            , 'tse'    ],  # tse, usually AX_2DT1 or AX_2DT2
        # ['ep2d_se'          , 'ep2d_se'],  # SpinEcho EPI
        # ['asl'              , 'asl'    ],  # 2D or 3D : ASL, pASL, pCASL
        # ['medic'            , 'medic'  ],  # dual echo T2*
    ]

    for seq_regex, program in list_seq_regex:
        func = eval(program)
        func(df, seq_regex)

    for vol in volume_list:
        if bool(vol.bidsfields):
            print(vol.bidsfields)

    return ""
