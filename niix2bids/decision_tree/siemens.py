# standard modules
from typing import List  # for function signature

# dependency modules
import pandas   # for DataFrame
import nibabel  # to load nifti header

# local modules
from niix2bids.decision_tree import utils
from niix2bids.classes import Volume
from niix2bids.utils import get_logger


########################################################################################################################
def prog_mprage(df: pandas.DataFrame, seq_regex: str) -> None:
    seqinfo = utils.slice_with_seqname(df, seq_regex)           # get list of corresponding sequence
    if seqinfo.empty:                                           # just to run the code faster
        return

    # keep 3D
    seqinfo_3D = utils.slice_with_mracquistiontype(seqinfo, '3D')
    seqinfo_bad = seqinfo.drop(seqinfo_3D.index)
    for _, seq in seqinfo_bad.iterrows():
        vol                   = seq['Volume']
        vol.reason_not_ready  = f"non-3D acquisition with PulseSequenceDetails = {seq_regex}"
    seqinfo = seqinfo_3D

    # here is a example of ImageType for all images for 1 sequence :
    # "ImageType": ["ORIGINAL", "PRIMARY", "M", "ND", "NORM"], <--- inv1
    # "ImageType": ["ORIGINAL", "PRIMARY", "M", "ND", "NORM"], <--- inv2
    # "ImageType": ["DERIVED", "PRIMARY", "T1 MAP", "ND"],     <--- T1map
    # "ImageType": ["DERIVED", "PRIMARY", "M", "ND", "UNI"],   <--- UNIT1
    seqinfo_mag   = utils.slice_with_imagetype(seqinfo, 'M')
    seqinfo_T1map = utils.slice_with_imagetype(seqinfo, 'T1 MAP')
    seqinfo_pha   = utils.slice_with_imagetype(seqinfo, 'P')
    if not seqinfo_pha.empty:
        log = get_logger()
        log.warning(f"mp(2)rage part-phase not coded yet. Be careful !")
    seqinfo = pandas.concat([seqinfo_mag, seqinfo_T1map])

    # in case of mp2rage, there are 3 (or 4 wih T1map) images generated
    # the SeriesDescription is automatically generated such as ProtocolName + suffix, where suffix = _INV1, _INV2,
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
                    seqinfo = seqinfo.drop(row_idx)

    # now that we have dealt with the mp2rage@siemens suffix, we can continue
    for _, desc_grp in seqinfo.groupby('SeriesDescription'):
        desc_grp['ImageType'] = desc_grp['ImageType'].apply(lambda x: '_'.join(x))
        for _, imgtyp_grp in desc_grp.groupby('ImageType'):  # this part will group&build the rec-* field
            image_type = imgtyp_grp['ImageType'].iloc[0]  # take the first one, they are identical
            image_type_list = image_type.split('_')
            image_type_useful_str = ''.join(image_type_list[3:])  # the first 3 items are discarded, the rest is concat
            run_idx = 0
            for _, ser_grp in imgtyp_grp.groupby('SeriesNumber'):
                run_idx += 1
                for row_idx, seq in ser_grp.iterrows():
                    vol                   = seq['Volume']
                    vol.tag               = 'anat'
                    vol.suffix            = 'T1w'
                    vol.sub               = utils.clean_name(seq['PatientName'])
                    vol.bidsfields['acq'] = utils.clean_name(seq['ProtocolName'])
                    vol.bidsfields['rec'] = image_type_useful_str
                    vol.bidsfields['run'] = run_idx


########################################################################################################################
def prog_tse_vfl(df: pandas.DataFrame, seq_regex: str) -> None:
    seqinfo = utils.slice_with_seqname(df, seq_regex)           # get list of corresponding sequence
    if seqinfo.empty:                                           # just to run the code faster
        return

    # keep 3D
    seqinfo_3D = utils.slice_with_mracquistiontype(seqinfo, '3D')
    seqinfo_bad = seqinfo.drop(seqinfo_3D.index)
    for _, seq in seqinfo_bad.iterrows():
        vol                   = seq['Volume']
        vol.reason_not_ready  = f"non-3D acquisition with PulseSequenceDetails = {seq_regex}"
    seqinfo = seqinfo_3D

    seqinfo_T2w   = utils.slice_with_seqvariant(seqinfo, '.spcR?_')
    seqinfo_FLAIR = utils.slice_with_seqvariant(seqinfo, '.spcirR?_')

    for _, desc_grp in seqinfo_T2w.groupby('SeriesDescription'):
        desc_grp['ImageType'] = desc_grp['ImageType'].apply(lambda x: '_'.join(x))
        for _, imgtyp_grp in desc_grp.groupby('ImageType'):  # this part will group&build the rec-* field
            image_type = imgtyp_grp['ImageType'].iloc[0]  # take the first one, they are identical
            image_type_list = image_type.split('_')
            image_type_useful_str = ''.join(image_type_list[3:])  # the first 3 items are discarded, the rest is concat
            run_idx = 0
            for _, ser_grp in imgtyp_grp.groupby('SeriesNumber'):
                run_idx += 1
                for row_idx, seq in ser_grp.iterrows():
                    vol                   = seq['Volume']
                    vol.tag               = 'anat'
                    vol.suffix            = 'T2w'
                    vol.sub               = utils.clean_name(seq['PatientName'])
                    vol.bidsfields['acq'] = utils.clean_name(seq['ProtocolName'])
                    vol.bidsfields['rec'] = image_type_useful_str
                    vol.bidsfields['run'] = run_idx

    for _, desc_grp in seqinfo_FLAIR.groupby('SeriesDescription'):
        desc_grp['ImageType'] = desc_grp['ImageType'].apply(lambda x: '_'.join(x))
        for _, imgtyp_grp in desc_grp.groupby('ImageType'):  # this part will group&build the rec-* field
            image_type = imgtyp_grp['ImageType'].iloc[0]  # take the first one, they are identical
            image_type_list = image_type.split('_')
            image_type_useful_str = ''.join(image_type_list[3:])  # the first 3 items are discarded, the rest is concat
            run_idx = 0
            for _, ser_grp in imgtyp_grp.groupby('SeriesNumber'):
                run_idx += 1
                for row_idx, seq in ser_grp.iterrows():
                    vol                   = seq['Volume']
                    vol.tag               = 'anat'
                    vol.suffix            = 'FLAIR'
                    vol.sub               = utils.clean_name(seq['PatientName'])
                    vol.bidsfields['acq'] = utils.clean_name(seq['ProtocolName'])
                    vol.bidsfields['rec'] = image_type_useful_str
                    vol.bidsfields['run'] = run_idx


########################################################################################################################
def prog_diff(df: pandas.DataFrame, seq_regex: str) -> None:
    seqinfo = utils.slice_with_seqname(df, seq_regex)           # get list of corresponding sequence
    if seqinfo.empty:                                           # just to run the code faster
        return

    # keep 2D
    seqinfo_2D = utils.slice_with_mracquistiontype(seqinfo, '2D')
    seqinfo_bad = seqinfo.drop(seqinfo_2D.index)
    for _, seq in seqinfo_bad.iterrows():
        vol                   = seq['Volume']
        vol.reason_not_ready  = f"non-2D acquisition with PulseSequenceDetails = {seq_regex}"
    seqinfo = seqinfo_2D

    # keep ORIGINAL images, discard ADC, FA, ColFA, ...
    seqinfo_original = utils.slice_with_imagetype_original(seqinfo)
    seqinfo_discard = seqinfo.drop(seqinfo_original.index)
    for row_idx, seq in seqinfo_discard.iterrows():
        vol                   = seq['Volume']
        vol.reason_not_ready  = f"dwi non-ORIGINAL {str(seq['ImageType'])}"
    seqinfo = seqinfo_original

    # in case of multiband sequence, SBRef images may be generated
    # therefore, we need to deal with them beforehand
    seqinfo_sbref = utils.slice_with_seriesdescription(seqinfo, '.*_SBRef$')
    for _, desc_grp in seqinfo_sbref.groupby('SeriesDescription'):
        run_idx = 0
        for _, dir_grp in desc_grp.groupby('PhaseEncodingDirection'):
            direction = dir_grp['PhaseEncodingDirection'].iloc(0)[0]  # just get first element, they are identical
            direction = utils.get_phase_encoding_direction(direction)
            for _, ser_grp in dir_grp.groupby('SeriesNumber'):
                run_idx += 1
                for row_idx, seq in ser_grp.iterrows():
                    vol                   = seq['Volume']
                    vol.tag               = 'dwi'
                    vol.suffix            = 'sbref'
                    vol.sub               = utils.clean_name(seq['PatientName'])
                    vol.bidsfields['acq'] = utils.clean_name(seq['ProtocolName'])
                    vol.bidsfields['dir'] = direction
                    vol.bidsfields['run'] = run_idx
                    seqinfo = seqinfo.drop(row_idx)

    # only keep 4D data
    # ex : 1 volume can be acquired quickly to check subject position over time, so discard it, its not "BOLD"
    for row_idx, seq in seqinfo.iterrows():
        nii = nibabel.load( seq['Volume'].nii.path )
        if nii.ndim < 4:  # check 4D
            seq['Volume'].reason_not_ready = 'non-4D dwi volume'
            seqinfo = seqinfo.drop(row_idx)

    # and now the normal volume
    for _, desc_grp in seqinfo.groupby('SeriesDescription'):
        run_idx = 0
        for _, dir_grp in desc_grp.groupby('PhaseEncodingDirection'):
            direction = dir_grp['PhaseEncodingDirection'].iloc(0)[0]  # just get first element, they are identical
            direction = utils.get_phase_encoding_direction(direction)
            for _, ser_grp in dir_grp.groupby('SeriesNumber'):
                run_idx += 1
                for row_idx, seq in ser_grp.iterrows():
                    vol                   = seq['Volume']
                    vol.tag               = 'dwi'
                    vol.suffix            = 'dwi'
                    # check if .bval et .bvec exist
                    has_bval = vol.check_if_bval_exists()
                    has_bvec = vol.check_if_bvec_exists()
                    if not has_bval:
                        vol.reason_not_ready += '[ no .bval file ] '
                    if not has_bvec:
                        vol.reason_not_ready += '[ no .bvec file ] '
                    vol.sub               = utils.clean_name(seq['PatientName'])
                    vol.bidsfields['acq'] = utils.clean_name(seq['ProtocolName'])
                    vol.bidsfields['dir'] = direction
                    vol.bidsfields['run'] = run_idx
                    if not has_bval and not has_bvec:
                        vol.tag           = ''


########################################################################################################################
def prog_bold(df: pandas.DataFrame, seq_regex: str) -> None:
    seqinfo = utils.slice_with_seqname(df, seq_regex)           # get list of corresponding sequence
    if seqinfo.empty:                                           # just to run the code faster
        return
    seqinfo = utils.slice_with_mracquistiontype(seqinfo, '2D')  # keep 2D images

    # in case of multiband sequence, SBRef images may be generated
    # therefore, we need to deal with them beforehand
    seqinfo_sbref = utils.slice_with_seriesdescription(seqinfo, '.*_SBRef$')
    for _, desc_grp in seqinfo_sbref.groupby('SeriesDescription'):
        run_idx = 0
        for _, dir_grp in desc_grp.groupby('PhaseEncodingDirection'):
            direction = dir_grp['PhaseEncodingDirection'].iloc(0)[0]  # just get first element, they are identical
            direction = utils.get_phase_encoding_direction(direction)
            for _, ser_grp in dir_grp.groupby('SeriesNumber'):
                run_idx += 1
                for row_idx, seq in ser_grp.iterrows():
                    vol                    = seq['Volume']
                    vol.tag                = 'func'
                    vol.suffix             = 'sbref'
                    vol.sub                = utils.clean_name(seq['PatientName'])
                    vol.bidsfields['task'] = utils.clean_name(seq['ProtocolName'])
                    vol.bidsfields['dir'] = direction
                    vol.bidsfields['run']  = run_idx
                    if not pandas.isna(seq['EchoNumber']):
                        vol.bidsfields['echo'] = int(seq['EchoNumber'])
                    seqinfo = seqinfo.drop(row_idx)

    # only keep 4D data
    # ex : 1 volume can be acquired quickly to check subject position over time, so discard it, its not "BOLD"
    for row_idx, seq in seqinfo.iterrows():
        nii = nibabel.load( seq['Volume'].nii.path )
        if nii.ndim < 4:  # check 4D
            seq['Volume'].reason_not_ready = 'non-4D bold volume'
            seqinfo = seqinfo.drop(row_idx)

    # separate magnitude & phase images

    # magnitude
    seqinfo_mag = utils.slice_with_imagetype(seqinfo, 'M')
    for _, desc_grp in seqinfo_mag.groupby('SeriesDescription'):
        run_idx = 0
        for _, dir_grp in desc_grp.groupby('PhaseEncodingDirection'):
            direction = dir_grp['PhaseEncodingDirection'].iloc(0)[0]  # just get first element, they are identical
            direction = utils.get_phase_encoding_direction(direction)
            for _, ser_grp in dir_grp.groupby('SeriesNumber'):
                run_idx += 1
                for row_idx, seq in ser_grp.iterrows():
                    vol                    = seq['Volume']
                    vol.tag                = 'func'
                    vol.suffix             = 'bold'
                    vol.sub                = utils.clean_name(seq['PatientName'])
                    vol.bidsfields['task'] = utils.clean_name(seq['ProtocolName'])
                    vol.bidsfields['dir']  = direction
                    vol.bidsfields['run']  = run_idx
                    if not pandas.isna(seq['EchoNumber']):
                        vol.bidsfields['echo'] = int(seq['EchoNumber'])

    # phase
    seqinfo_pha = utils.slice_with_imagetype(seqinfo, 'P')
    for _, desc_grp in seqinfo_pha.groupby('SeriesDescription'):
        run_idx = 0
        for _, dir_grp in desc_grp.groupby('PhaseEncodingDirection'):
            direction = dir_grp['PhaseEncodingDirection'].iloc(0)[0]  # just get first element, they are identical
            direction = utils.get_phase_encoding_direction(direction)
            for _, ser_grp in dir_grp.groupby('SeriesNumber'):
                run_idx += 1
                for row_idx, seq in ser_grp.iterrows():
                    vol                    = seq['Volume']
                    vol.tag                = 'func'
                    vol.suffix             = 'phase'
                    vol.sub                = utils.clean_name(seq['PatientName'])
                    vol.bidsfields['task'] = utils.clean_name(seq['ProtocolName'])
                    vol.bidsfields['dir']  = direction
                    vol.bidsfields['run']  = run_idx
                    if not pandas.isna(seq['EchoNumber']):
                        vol.bidsfields['echo'] = int(seq['EchoNumber'])


########################################################################################################################
def prog_fmap(df: pandas.DataFrame, seq_regex: str) -> None:
    seqinfo = utils.slice_with_seqname(df, seq_regex)           # get list of corresponding sequence
    if seqinfo.empty:                                           # just to run the code faster
        return

    # keep 2D
    seqinfo_2D = utils.slice_with_mracquistiontype(seqinfo, '2D')
    seqinfo_bad = seqinfo.drop(seqinfo_2D.index)
    for _, seq in seqinfo_bad.iterrows():
        vol                   = seq['Volume']
        vol.reason_not_ready  = f"non-2D acquisition with PulseSequenceDetails = {seq_regex}"
    seqinfo = seqinfo_2D

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


########################################################################################################################
def prog_gre(df: pandas.DataFrame, seq_regex: str) -> None:
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


########################################################################################################################
def prog_tse(df: pandas.DataFrame, seq_regex: str) -> None:
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


########################################################################################################################
def prog_ep2d_se(df: pandas.DataFrame, seq_regex: str) -> None:
    seqinfo = utils.slice_with_seqname(df, seq_regex)           # get list of corresponding sequence
    if seqinfo.empty:                                           # just to run the code faster
        return

    # keep 2D
    seqinfo_2D = utils.slice_with_mracquistiontype(seqinfo, '2D')
    seqinfo_bad = seqinfo.drop(seqinfo_2D.index)
    for _, seq in seqinfo_bad.iterrows():
        vol                   = seq['Volume']
        vol.reason_not_ready  = f"non-2D acquisition with PulseSequenceDetails = {seq_regex}"
    seqinfo = seqinfo_2D

    for _, desc_grp in seqinfo.groupby('SeriesDescription'):
        run_idx = 0
        for _, dir_grp in desc_grp.groupby('PhaseEncodingDirection'):
            direction = dir_grp['PhaseEncodingDirection'].iloc(0)[0]  # just get first element, they are identical
            direction = utils.get_phase_encoding_direction(direction)
            for _, ser_grp in dir_grp.groupby('SeriesNumber'):
                run_idx += 1
                for row_idx, seq in ser_grp.iterrows():
                    vol                   = seq['Volume']
                    vol.tag               = 'fmap'
                    vol.suffix            = 'epi'
                    vol.sub               = utils.clean_name(seq['PatientName'])
                    vol.bidsfields['acq'] = utils.clean_name(seq['ProtocolName'])
                    vol.bidsfields['dir'] = direction
                    vol.bidsfields['run'] = run_idx


########################################################################################################################
def prog_discard(df: pandas.DataFrame, seq_regex: str) -> None:
    seqinfo = utils.slice_with_seqname(df, seq_regex)  # get list of corresponding sequence
    if seqinfo.empty:                                  # just to run the code faster
        return

    for _, desc_grp in seqinfo.groupby('SeriesDescription'):
        run_idx = 0
        for _, ser_grp in desc_grp.groupby('SeriesNumber'):
            run_idx += 1
            for row_idx, seq in ser_grp.iterrows():
                vol                   = seq['Volume']
                vol.tag               = 'DISCARD'
                vol.suffix            = ''
                vol.sub               = utils.clean_name(seq['PatientName'])
                vol.bidsfields['acq'] = utils.clean_name(seq['ProtocolName'])
                vol.bidsfields['run'] = run_idx
                vol.reason_not_ready  = f'discard PulseSequenceDetails = {seq_regex}'


########################################################################################################################
def run(volume_list: List[Volume], config: list) -> None:

    log = get_logger()

    log.info(f'starting decision tree for "Siemens"... ')

    list_param = utils.assemble_list_param(volume_list)

    # conversion of List[dict] to pandas.DataFrame
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

    # subject by subject sequence group
    df_by_subject = df.groupby('PatientName')

    # call each routine depending on the sequence name
    for name, group in df_by_subject:               # loop over subjects
        for seq_regex, fcn_name in config:  # loop over sequence decision tree
            func = eval(fcn_name)   # fetch the name of the function to call dynamically
            func(group, seq_regex)  # execute the function

    # deal with unknown sequences
    for _, desc_grp in df.groupby('SeriesDescription'):
        run_idx = 0
        for _, ser_grp in desc_grp.groupby('SeriesNumber'):
            run_idx += 1
            for row_idx, seq in ser_grp.iterrows():
                vol                       = seq['Volume']
                # here is the important part : if we already parsed the the sequence, then skip it, else tag it UNKNOWN
                if len(vol.tag) > 0:
                    pass
                elif len(vol.reason_not_ready) > 0:
                    pass
                else:
                    vol.tag               = 'UNKNOWN'
                    vol.suffix            = ''
                    vol.sub               = utils.clean_name(seq['PatientName'])
                    vol.bidsfields['acq'] = utils.clean_name(seq['ProtocolName'])
                    vol.bidsfields['run'] = run_idx
                    vol.reason_not_ready  = f"unknown PulseSequenceDetails = {seq['PulseSequenceDetails']}"

    # all done
    log.info(f'"Siemens" decision tree done')
