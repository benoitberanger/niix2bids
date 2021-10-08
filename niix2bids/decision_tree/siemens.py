# standard modules
import logging  # logging lib (terminal & file)

# dependency modules
import pandas   # for DataFrame

# local modules
from niix2bids.decision_tree import utils
from niix2bids.classes import Volume

# get logger with current name
log = logging.getLogger(__name__)


########################################################################################################################
def mprage(df: pandas.DataFrame, seq_regex: str):
    seq_info = utils.slice_with_seqname(df, seq_regex)            # get list of corresponding sequence
    seq_info = utils.slice_with_mracquistiontype(seq_info, '3D')  # keep 3D images

    if seq_info.empty:  # just run the code faster
        return

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
    seq_info = utils.slice_with_seqname(df, seq_regex)            # get list of corresponding sequence
    seq_info = utils.slice_with_mracquistiontype(seq_info, '3D')  # keep 3D images

    if seq_info.empty:  # just run the code faster
        return

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
def diff(df: pandas.DataFrame, seq_regex: str):
    seq_info = utils.slice_with_seqname(df, seq_regex)            # get list of corresponding sequence
    seq_info = utils.slice_with_mracquistiontype(seq_info, '2D')  # keep 2D images

    if seq_info.empty:  # just run the code faster
        return

    # in case of multiband sequence, SBRef images may be generated
    # therefore, we need to deal with them beforehand
    seq_sbref = utils.slice_with_seriesdescription(seq_info, '.*_SBRef$')
    idx = 0
    for row_idx, seq in seq_sbref.iterrows():
        idx += 1
        vol = seq['Volume']
        vol.bidsfields['sub'] = utils.clean_name(seq['PatientName'])
        vol.bidsfields['ses'] = '01'
        vol.bidsfields['tag'] = 'dwi'
        vol.bidsfields['acq'] = utils.clean_name(seq['ProtocolName'])
        vol.bidsfields['run'] = idx
        vol.bidsfields['suffix'] = 'sbref'
        seq_info = seq_info.drop(row_idx)

    # and now the normal volume
    idx = 0
    for row_idx, seq in seq_info.iterrows():
        idx += 1
        vol = seq['Volume']
        # check if .bval et .bvec exist
        vol.check_if_bval_exists()
        vol.check_if_bvec_exists()
        vol.bidsfields['sub'] = utils.clean_name(seq['PatientName'])
        vol.bidsfields['ses'] = '01'
        vol.bidsfields['tag'] = 'dwi'
        vol.bidsfields['acq'] = utils.clean_name(seq['ProtocolName'])
        vol.bidsfields['run'] = idx
        vol.bidsfields['suffix'] = 'dwi'


########################################################################################################################
def bold(df: pandas.DataFrame, seq_regex: str):
    seq_info = utils.slice_with_seqname(df, seq_regex)            # get list of corresponding sequence
    seq_info = utils.slice_with_mracquistiontype(seq_info, '2D')  # keep 2D images

    if seq_info.empty:  # just run the code faster
        return

    # in case of multiband sequence, SBRef images may be generated
    # therefore, we need to deal with them beforehand
    seq_sbref = utils.slice_with_seriesdescription(seq_info, '.*_SBRef$')
    idx = 0
    for row_idx, seq in seq_sbref.iterrows():
        idx += 1
        vol = seq['Volume']
        vol.bidsfields['sub'] = utils.clean_name(seq['PatientName'])
        vol.bidsfields['ses'] = '01'
        vol.bidsfields['tag'] = 'func'
        vol.bidsfields['acq'] = utils.clean_name(seq['ProtocolName'])
        vol.bidsfields['run'] = idx
        if not pandas.isna(seq['EchoNumber']):
            vol.bidsfields['echo'] = int(seq['EchoNumber'])
        vol.bidsfields['suffix'] = 'sbref'
        seq_info = seq_info.drop(row_idx)

    # separate magnitude & phase images

    # magnitude
    mag = utils.slice_with_imagetype(seq_info,'M')
    idx = 0
    for row_idx, seq in mag.iterrows():
        idx += 1
        vol = seq['Volume']
        vol.bidsfields['sub'] = utils.clean_name(seq['PatientName'])
        vol.bidsfields['ses'] = '01'
        vol.bidsfields['tag'] = 'func'
        vol.bidsfields['acq'] = utils.clean_name(seq['ProtocolName'])
        vol.bidsfields['run'] = idx
        if not pandas.isna(seq['EchoNumber']):
            vol.bidsfields['echo'] = int(seq['EchoNumber'])
        vol.bidsfields['suffix'] = 'bold'

    # phase
    pha = utils.slice_with_imagetype(seq_info,'P')
    idx = 0
    for row_idx, seq in pha.iterrows():
        idx += 1
        vol = seq['Volume']
        vol.bidsfields['sub'] = utils.clean_name(seq['PatientName'])
        vol.bidsfields['ses'] = '01'
        vol.bidsfields['tag'] = 'func'
        vol.bidsfields['acq'] = utils.clean_name(seq['ProtocolName'])
        vol.bidsfields['run'] = idx
        if not pandas.isna(seq['EchoNumber']):
            vol.bidsfields['echo'] = int(seq['EchoNumber'])
        vol.bidsfields['suffix'] = 'pha'


########################################################################################################################
def fmap(df: pandas.DataFrame, seq_regex: str):
    seq_info = utils.slice_with_seqname(df, seq_regex)            # get list of corresponding sequence
    seq_info = utils.slice_with_mracquistiontype(seq_info, '2D')  # keep 2D images

    if seq_info.empty:  # just run the code faster
        return


########################################################################################################################
def run(volume_list: list[Volume]):

    log.info(f'starting decision tree for "Siemens"... ')

    list_param = utils.assemble_list_param(volume_list)

    # conversion of list[dict] to pandas.DataFrame
    # to pandas.DataFrame object is like table in matlab, with much more embedded methods
    df = pandas.DataFrame(list_param)

    # eliminate sequences whiteout PulseSequenceDetails, we cannot parse them
    df = df[ df['PulseSequenceDetails'].isna() == False]

    # checks
    utils.assert_is_dcm2niix(df)
    utils.assert_key_val(df, "Modality"    , "MR"     )
    utils.assert_key_val(df, "Manufacturer", "Siemens")

    # make some extraction / conversion
    # %CustomerSeq%_cmrr_mbep2d_bold -> cmrr_mbep2d_bold
    df['PulseSequenceDetails'] = df['PulseSequenceDetails'].apply(lambda s: s.rsplit("%_")[1])

    list_seq_regex = [
        # [seq_regex             fcn name]
        ['^tfl$'              , 'mprage' ],  # mprage & mp2rage
        ['.*mp2rage.*'        , 'mprage' ],  # mp2rage WIP
        ['^tse_vfl$'          , 'tse_vfl'],  # 3DT2 space & 3DFLAIR space_ir
        ['.*diff.*'           , 'diff'   ],  # diffusion
        ['.*(bold)|(pace).*'  , 'bold'   ],  # bold fmri
        ['^gre_field_mapping$', 'fmap'   ],  # dual echo field map, with pre-substracted phase
        # ['^gre$'            , 'gre'    ],  # FLASH
        # ['^icm_gre$'        , 'gre'    ],  # FLASH specific at ICM, with better phase reconstruction, will be used for QSM
        # ['^tse$'            , 'tse'    ],  # tse, usually AX_2DT1 or AX_2DT2
        # ['ep2d_se'          , 'ep2d_se'],  # SpinEcho EPI
        # ['asl'              , 'asl'    ],  # 2D or 3D : ASL, pASL, pCASL
        # ['medic'            , 'medic'  ],  # dual echo T2*
    ]

    df_by_subject = df.groupby('PatientName')  # subject by subject sequence group
    for name, group in df_by_subject:
        for seq_regex, fcn_name in list_seq_regex:
            func = eval(fcn_name)   # fetch the name of the function to call dynamically
            func(group, seq_regex)  # execute the function

    for vol in volume_list:
        if bool(vol.bidsfields):
            print(vol.bidsfields)
