# standard modules
import logging  # logging lib (terminal & file)

# dependency modules
import pandas   # for DataFrame
import nibabel  # to load nifti header

# local modules
from niix2bids.decision_tree import utils
from niix2bids.classes import Volume

# get logger with current name
log = logging.getLogger(__name__)


########################################################################################################################
def mprage(df: pandas.DataFrame, seq_regex: str) -> None:
    seqinfo = utils.slice_with_seqname(df, seq_regex)           # get list of corresponding sequence
    if seqinfo.empty:                                           # just to run the code faster
        return
    seqinfo = utils.slice_with_mracquistiontype(seqinfo, '3D')  # keep 3D images

    # here is a example of ImageType for all images for 1 sequence :
    # "ImageType": ["ORIGINAL", "PRIMARY", "M", "ND", "NORM"], <--- inv1
    # "ImageType": ["ORIGINAL", "PRIMARY", "M", "ND", "NORM"], <--- inv2
    # "ImageType": ["DERIVED", "PRIMARY", "T1 MAP", "ND"],     <--- T1map
    # "ImageType": ["DERIVED", "PRIMARY", "M", "ND", "UNI"],   <--- UNIT1
    seqinfo_mag   = utils.slice_with_imagetype(seqinfo, 'M')
    seqinfo_T1map = utils.slice_with_imagetype(seqinfo, 'T1 MAP')
    seqinfo_pha   = utils.slice_with_imagetype(seqinfo, 'P')
    if not seqinfo_pha.empty:
        log.warning(f"mp(2)rage part-phase not coded yet. Be careful !")
    seqinfo = pandas.concat([seqinfo_mag, seqinfo_T1map])

    # in case of mp2rage, there are 3 (or 4 wih T1map) images generated
    # the SeriesDescription is automatically generated such as ProtocalName + suffix, where suffix = _INV1, _INV2,
    # _UNI_Images (and _T1_Images)
    descr_regex_list = ['.*_INV1$', '.*_INV2$', '.*_T1_Images$', '.*_UNI_Images$']
    suffix_list      = ['MP2RAGE' ,  'MP2RAGE', 'T1map'        , 'UNIT1'         ]
    for descr_regex in descr_regex_list:
        seq_suffix = utils.slice_with_seriesdescription(seqinfo, descr_regex)
        for _, desc_grp in seq_suffix.groupby('SeriesDescription'):
            run_idx = 0
            for _, ser_grp in desc_grp.groupby('SeriesNumber'):
                run_idx += 1
                for row_idx, seq in ser_grp.iterrows():
                    vol                   = seq['Volume']
                    vol.tag               = 'anat'
                    vol.suffix            = suffix_list[descr_regex_list.index(descr_regex)]
                    vol.sub               = utils.clean_name(seq['PatientName'])
                    vol.bidsfields['acq'] = utils.clean_name(seq['ProtocolName'])
                    vol.bidsfields['run'] = run_idx
                    if vol.suffix            == 'MP2RAGE':
                        # _inv-<index>[_part-<label>]_MP2RAGE.nii
                        vol.bidsfields['inv'] = descr_regex_list.index(descr_regex) + 1
                    vol.ready             = True
                    seqinfo = seqinfo.drop(row_idx)

    # now that we have dealt with the mp2rage@siemens suffix, we can continue
    for _, desc_grp in seqinfo.groupby('SeriesDescription'):
        run_idx = 0
        for _, ser_grp in desc_grp.groupby('SeriesNumber'):
            run_idx += 1
            for row_idx, seq in ser_grp.iterrows():
                vol                   = seq['Volume']
                vol.tag               = 'anat'
                vol.suffix            = 'T1w'
                vol.sub               = utils.clean_name(seq['PatientName'])
                vol.bidsfields['acq'] = utils.clean_name(seq['ProtocolName'])
                vol.bidsfields['run'] = run_idx
                vol.ready             = True


########################################################################################################################
def tse_vfl(df: pandas.DataFrame, seq_regex: str) -> None:
    seqinfo = utils.slice_with_seqname(df, seq_regex)           # get list of corresponding sequence
    if seqinfo.empty:                                           # just to run the code faster
        return
    seqinfo = utils.slice_with_mracquistiontype(seqinfo, '3D')  # keep 3D images

    seqinfo_T2w   = utils.slice_with_seqvariant(seqinfo, '_spc_')
    seqinfo_FLAIR = utils.slice_with_seqvariant(seqinfo, '_spcir_')

    for _, desc_grp in seqinfo_T2w.groupby('SeriesDescription'):
        run_idx = 0
        for _, ser_grp in desc_grp.groupby('SeriesNumber'):
            run_idx += 1
            for row_idx, seq in ser_grp.iterrows():
                vol                   = seq['Volume']
                vol.tag               = 'anat'
                vol.suffix            = 'T2w'
                vol.sub               = utils.clean_name(seq['PatientName'])
                vol.bidsfields['acq'] = utils.clean_name(seq['ProtocolName'])
                vol.bidsfields['run'] = run_idx
                vol.ready             = True

    for _, desc_grp in seqinfo_FLAIR.groupby('SeriesDescription'):
        run_idx = 0
        for _, ser_grp in desc_grp.groupby('SeriesNumber'):
            run_idx += 1
            for row_idx, seq in ser_grp.iterrows():
                vol                   = seq['Volume']
                vol.tag               = 'anat'
                vol.suffix            = 'FLAIR'
                vol.sub               = utils.clean_name(seq['PatientName'])
                vol.bidsfields['acq'] = utils.clean_name(seq['ProtocolName'])
                vol.bidsfields['run'] = run_idx
                vol.ready             = True


########################################################################################################################
def diff(df: pandas.DataFrame, seq_regex: str) -> None:
    seqinfo = utils.slice_with_seqname(df, seq_regex)           # get list of corresponding sequence
    if seqinfo.empty:                                           # just to run the code faster
        return
    seqinfo = utils.slice_with_imagetype_original(seqinfo)      # keep ORIGINAL images, discard ADC, FA, ColFA, ...
    seqinfo = utils.slice_with_mracquistiontype(seqinfo, '2D')  # keep 2D images

    # in case of multiband sequence, SBRef images may be generated
    # therefore, we need to deal with them beforehand
    seqinfo_sbref = utils.slice_with_seriesdescription(seqinfo, '.*_SBRef$')
    for _, desc_grp in seqinfo_sbref.groupby('SeriesDescription'):
        run_idx = 0
        for _, ser_grp in desc_grp.groupby('SeriesNumber'):
            run_idx += 1
            for row_idx, seq in ser_grp.iterrows():
                vol                   = seq['Volume']
                vol.tag               = 'dwi'
                vol.suffix            = 'sbref'
                vol.sub               = utils.clean_name(seq['PatientName'])
                vol.bidsfields['acq'] = utils.clean_name(seq['ProtocolName'])
                vol.bidsfields['run'] = run_idx
                vol.ready             = True
                seqinfo = seqinfo.drop(row_idx)

    # and now the normal volume
    for _, desc_grp in seqinfo.groupby('SeriesDescription'):
        run_idx = 0
        for _, ser_grp in desc_grp.groupby('SeriesNumber'):
            run_idx += 1
            for row_idx, seq in ser_grp.iterrows():
                vol                   = seq['Volume']
                vol.tag               = 'dwi'
                vol.suffix            = 'dwi'
                # check if .bval et .bvec exist
                vol.check_if_bval_exists()
                vol.check_if_bvec_exists()
                vol.sub               = utils.clean_name(seq['PatientName'])
                vol.bidsfields['acq'] = utils.clean_name(seq['ProtocolName'])
                vol.bidsfields['run'] = run_idx
                vol.ready             = True


########################################################################################################################
def bold(df: pandas.DataFrame, seq_regex: str) -> None:
    seqinfo = utils.slice_with_seqname(df, seq_regex)           # get list of corresponding sequence
    if seqinfo.empty:                                           # just to run the code faster
        return
    seqinfo = utils.slice_with_mracquistiontype(seqinfo, '2D')  # keep 2D images

    # in case of multiband sequence, SBRef images may be generated
    # therefore, we need to deal with them beforehand
    seqinfo_sbref = utils.slice_with_seriesdescription(seqinfo, '.*_SBRef$')
    for _, desc_grp in seqinfo_sbref.groupby('SeriesDescription'):
        run_idx = 0
        for _, ser_grp in desc_grp.groupby('SeriesNumber'):
            run_idx += 1
            for row_idx, seq in ser_grp.iterrows():
                vol                    = seq['Volume']
                vol.tag                = 'func'
                vol.suffix             = 'sbref'
                vol.sub                = utils.clean_name(seq['PatientName'])
                vol.bidsfields['task'] = utils.clean_name(seq['ProtocolName'])
                vol.bidsfields['run']  = run_idx
                if not pandas.isna(seq['EchoNumber']):
                    vol.bidsfields['echo'] = int(seq['EchoNumber'])
                vol.ready             = True
                seqinfo = seqinfo.drop(row_idx)

    # only keep 4D data
    # ex : 1 volume can be acquired quickly to check subject position over time, so discard it, its not "BOLD"

    for row_idx, seq in seqinfo.iterrows():
        nii = nibabel.load( seq['Volume'].nii.path )
        if nii.ndim < 4:  # check 4D
            log.warning(f"non 4D volume, discard it : {seq['Volume'].nii.path}")
            seqinfo = seqinfo.drop(row_idx)

    # separate magnitude & phase images

    # magnitude
    seqinfo_mag = utils.slice_with_imagetype(seqinfo, 'M')
    for _, desc_grp in seqinfo_mag.groupby('SeriesDescription'):
        run_idx = 0
        for _, ser_grp in desc_grp.groupby('SeriesNumber'):
            run_idx += 1
            for row_idx, seq in ser_grp.iterrows():
                vol                    = seq['Volume']
                vol.tag                = 'func'
                vol.suffix             = 'bold'
                vol.sub                = utils.clean_name(seq['PatientName'])
                vol.bidsfields['task'] = utils.clean_name(seq['ProtocolName'])
                vol.bidsfields['run']  = run_idx
                if not pandas.isna(seq['EchoNumber']):
                    vol.bidsfields['echo'] = int(seq['EchoNumber'])
                vol.ready             = True

    # phase
    seqinfo_pha = utils.slice_with_imagetype(seqinfo, 'P')
    for _, desc_grp in seqinfo_pha.groupby('SeriesDescription'):
        run_idx = 0
        for _, ser_grp in desc_grp.groupby('SeriesNumber'):
            run_idx += 1
            for row_idx, seq in ser_grp.iterrows():
                vol                    = seq['Volume']
                vol.tag                = 'func'
                vol.suffix             = 'phase'
                vol.sub                = utils.clean_name(seq['PatientName'])
                vol.bidsfields['task'] = utils.clean_name(seq['ProtocolName'])
                vol.bidsfields['run']  = run_idx
                if not pandas.isna(seq['EchoNumber']):
                    vol.bidsfields['echo'] = int(seq['EchoNumber'])
                vol.ready             = True


########################################################################################################################
def fmap(df: pandas.DataFrame, seq_regex: str) -> None:
    seqinfo = utils.slice_with_seqname(df, seq_regex)           # get list of corresponding sequence
    if seqinfo.empty:                                           # just to run the code faster
        return
    seqinfo = utils.slice_with_mracquistiontype(seqinfo, '2D')  # keep 2D images

    # separate magnitude & phase images

    # magnitude
    seqinfo_mag = utils.slice_with_imagetype(seqinfo, 'M')
    for _, desc_grp in seqinfo_mag.groupby('SeriesDescription'):
        run_idx = 0
        for _, ser_grp in desc_grp.groupby('SeriesNumber'):
            run_idx += 1
            for row_idx, seq in ser_grp.iterrows():
                vol                   = seq['Volume']
                vol.tag               = 'fmap'
                vol.suffix            = f"magnitude{int(seq['EchoNumber'])}"  # suffix has to be _magnitude1 _magnitude2
                vol.sub               = utils.clean_name(seq['PatientName'])
                vol.bidsfields['acq'] = utils.clean_name(seq['ProtocolName'])
                vol.bidsfields['run'] = run_idx
                vol.ready             = True

    # phase
    seqinfo_pha = utils.slice_with_imagetype(seqinfo, 'P')
    for _, desc_grp in seqinfo_pha.groupby('SeriesDescription'):
        run_idx = 0
        for _, ser_grp in desc_grp.groupby('SeriesNumber'):
            run_idx += 1
            for row_idx, seq in ser_grp.iterrows():
                vol                   = seq['Volume']
                vol.tag               = 'fmap'
                vol.suffix            = 'phasediff'
                vol.sub               = utils.clean_name(seq['PatientName'])
                vol.bidsfields['acq'] = utils.clean_name(seq['ProtocolName'])
                vol.bidsfields['run'] = run_idx
                vol.ready             = True


########################################################################################################################
def gre(df: pandas.DataFrame, seq_regex: str) -> None:
    seqinfo = utils.slice_with_seqname(df, seq_regex)  # get list of corresponding sequence
    if seqinfo.empty:                                  # just to run the code faster
        return

    # separate magnitude & phase images

    # magnitude
    seqinfo_mag = utils.slice_with_imagetype(seqinfo, 'M')
    for _, desc_grp in seqinfo_mag.groupby('SeriesDescription'):
        run_idx = 0
        for _, ser_grp in desc_grp.groupby('SeriesNumber'):
            run_idx += 1
            for row_idx, seq in ser_grp.iterrows():
                vol                   = seq['Volume']
                vol.tag               = 'anat'
                vol.sub               = utils.clean_name(seq['PatientName'])
                vol.bidsfields['acq'] = utils.clean_name(seq['ProtocolName'])
                vol.bidsfields['run'] = run_idx
                if not pandas.isna(seq['EchoNumber']):
                    vol.bidsfields['echo'] = int(seq['EchoNumber'])
                    vol.bidsfields['part'] = 'mag'
                    vol.suffix             = 'MEGRE'
                else:
                    vol.bidsfields['part'] = 'mag'
                    vol.suffix             = 'T2starw'
                vol.ready             = True

    # magnitude
    seqinfo_pha = utils.slice_with_imagetype(seqinfo, 'P')
    for _, desc_grp in seqinfo_pha.groupby('SeriesDescription'):
        run_idx = 0
        for _, ser_grp in desc_grp.groupby('SeriesNumber'):
            run_idx += 1
            for row_idx, seq in ser_grp.iterrows():
                vol                   = seq['Volume']
                vol.tag               = 'anat'
                vol.sub               = utils.clean_name(seq['PatientName'])
                vol.bidsfields['acq'] = utils.clean_name(seq['ProtocolName'])
                vol.bidsfields['run'] = run_idx
                if not pandas.isna(seq['EchoNumber']):
                    vol.bidsfields['echo'] = int(seq['EchoNumber'])
                    vol.bidsfields['part'] = 'phase'
                    vol.suffix             = 'MEGRE'
                else:
                    vol.bidsfields['part'] = 'phase'
                    vol.suffix             = 'T2starw'
                vol.ready             = True


########################################################################################################################
def tse(df: pandas.DataFrame, seq_regex: str) -> None:
    seqinfo = utils.slice_with_seqname(df, seq_regex)  # get list of corresponding sequence
    if seqinfo.empty:                                  # just to run the code faster
        return

    seqinfo_T2w   = utils.slice_with_seqvariant(seqinfo, '_tse')
    seqinfo_FLAIR = utils.slice_with_seqvariant(seqinfo, '_tir')

    for _, desc_grp in seqinfo_T2w.groupby('SeriesDescription'):
        run_idx = 0
        for _, ser_grp in desc_grp.groupby('SeriesNumber'):
            run_idx += 1
            for row_idx, seq in ser_grp.iterrows():
                vol                   = seq['Volume']
                vol.tag               = 'anat'
                vol.suffix            = 'T2w'
                vol.sub               = utils.clean_name(seq['PatientName'])
                vol.bidsfields['acq'] = utils.clean_name(seq['ProtocolName'])
                vol.bidsfields['run'] = run_idx
                vol.ready             = True

    for _, desc_grp in seqinfo_FLAIR.groupby('SeriesDescription'):
        run_idx = 0
        for _, ser_grp in desc_grp.groupby('SeriesNumber'):
            run_idx += 1
            for row_idx, seq in ser_grp.iterrows():
                vol                   = seq['Volume']
                vol.tag               = 'anat'
                vol.suffix            = 'FLAIR'
                vol.sub               = utils.clean_name(seq['PatientName'])
                vol.bidsfields['acq'] = utils.clean_name(seq['ProtocolName'])
                vol.bidsfields['run'] = run_idx
                vol.ready             = True


########################################################################################################################
def run(volume_list: list[Volume]) -> None:

    log.info(f'starting decision tree for "Siemens"... ')

    list_param = utils.assemble_list_param(volume_list)

    # conversion of list[dict] to pandas.DataFrame
    # to pandas.DataFrame object is like table in matlab, with much more embedded methods
    df = pandas.DataFrame(list_param)

    # eliminate sequences with missing parameters, we cannot parse them
    df = df[ df['PulseSequenceDetails'].isna() == False ]  # this is the basic sequence name : %SiemensSeq%_gre
    df = df[ df['MRAcquisitionType'   ].isna() == False ]  # '2D', '3D'

    # checks
    utils.assert_is_dcm2niix(df)
    utils.assert_has_patientname(df)
    utils.assert_key_val(df, "Modality"    , "MR"     )
    utils.assert_key_val(df, "Manufacturer", "Siemens")

    # make some extraction / conversion
    # %CustomerSeq%_cmrr_mbep2d_bold -> cmrr_mbep2d_bold
    df['PulseSequenceDetails'] = df['PulseSequenceDetails'].apply(lambda s: s.rsplit("%_")[1])

    # the approach is simple : the sequence name ('gre') defines which decision tree to apply
    list_seq_regex = [
        # [seq_regex             fcn name]
        ['^tfl$'              , 'mprage' ],  # mprage & mp2rage
        ['.*mp2rage.*'        , 'mprage' ],  # mp2rage WIP
        ['^tse_vfl$'          , 'tse_vfl'],  # 3DT2 space & 3DFLAIR space_ir
        ['.*diff.*'           , 'diff'   ],  # diffusion
        ['.*(bold)|(pace).*'  , 'bold'   ],  # bold fmri
        ['^gre_field_mapping$', 'fmap'   ],  # dual echo field map, with pre-substracted phase
        ['^gre$'              , 'gre'    ],  # FLASH
        ['^icm_gre$'          , 'gre'    ],  # FLASH specific at ICM, with better phase reconstruction, will be used for QSM
        ['^tse$'              , 'tse'    ],  # tse, usually AX_2DT1 or AX_2DT2
        # ['ep2d_se'          , 'ep2d_se'],  # SpinEcho EPI
        # ['asl'              , 'asl'    ],  # 2D or 3D : ASL, pASL, pCASL
        # ['medic'            , 'medic'  ],  # dual echo T2*
    ]

    # subject by subject sequence group
    df_by_subject = df.groupby('PatientName')

    for name, group in df_by_subject:               # loop over subjects
        for seq_regex, fcn_name in list_seq_regex:  # loop over sequence decision tree
            func = eval(fcn_name)   # fetch the name of the function to call dynamically
            func(group, seq_regex)  # execute the function
