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
    seqinfo = utils.slice_with_genericfield(df, 'PulseSequenceDetails', seq_regex)  # get list of corresponding sequence
    if seqinfo.empty: return  # just to run the code faster
    sub = utils.clean_name(seqinfo.iloc[0]['PatientName'])  # this does not change

    # keep 3D
    seqinfo = utils.keep_ndim(seqinfo, '3D', seq_regex)

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

    # ------------------------------------------------------------------------------------------------------------------
    # in case of mp2rage, there are 3 (or 4 wih T1map) images generated
    # the SeriesDescription is automatically generated such as ProtocolName + suffix, where suffix = _INV1, _INV2,
    # _UNI_Images (and _T1_Images)
    descr_regex_list = ['.*_INV1$', '.*_INV2$', '.*_T1_Images$', '.*_UNI_Images$']
    suffix_list      = ['MP2RAGE' ,  'MP2RAGE', 'T1map'        , 'UNIT1'         ]
    for descr_regex in descr_regex_list:

        seqinfo_suffix = utils.slice_with_genericfield(seqinfo, 'SeriesDescription', descr_regex)

        suffix = suffix_list[descr_regex_list.index(descr_regex)]
        if suffix == 'MP2RAGE':
            inv = descr_regex_list.index(descr_regex) + 1
        else:
            inv = ''

        # build groups of parameters
        columns = ['SeriesDescription']
        groups = seqinfo_suffix.groupby(columns)

        # loop over groups
        for grp_name, series in groups:

            first_serie = series.iloc[0]  # they are all the same (except run number), so take the first one

            acq = utils.clean_name(first_serie['ProtocolName'])

            # loop over runs
            run_idx = 0
            for row_idx, seq in series.iterrows():
                run_idx += 1
                vol                   = seq['Volume']
                vol.tag               = 'anat'
                vol.suffix            = suffix
                vol.sub               = sub
                vol.bidsfields['acq'] = acq
                vol.bidsfields['run'] = run_idx
                if bool(inv): vol.bidsfields['inv'] = inv
                seqinfo = seqinfo.drop(row_idx)  ## !! important : drop series that we already flagged !!

    # ------------------------------------------------------------------------------------------------------------------
    # now that we have dealt with the mp2rage@siemens suffix, we can continue

    # build groups of parameters
    columns = ['SeriesDescription', 'ImageTypeStr']
    groups = seqinfo.groupby(columns)

    # loop over groups
    for grp_name, series in groups:

        first_serie = series.iloc[0]  # they are all the same (except run number), so take the first one

        acq = utils.clean_name(first_serie['ProtocolName'])
        image_type_useful = ''.join(first_serie['ImageType'][3:])

        # loop over runs
        run_idx = 0
        for row_idx, seq in series.iterrows():
            run_idx += 1
            vol                   = seq['Volume']
            vol.tag               = 'anat'
            vol.suffix            = 'T1w'
            vol.sub               = sub
            vol.bidsfields['acq'] = acq
            vol.bidsfields['rec'] = image_type_useful
            vol.bidsfields['run'] = run_idx


########################################################################################################################
def prog_tse_vfl(df: pandas.DataFrame, seq_regex: str) -> None:
    seqinfo = utils.slice_with_genericfield(df, 'PulseSequenceDetails', seq_regex)  # get list of corresponding sequence
    if seqinfo.empty: return  # just to run the code faster
    sub = utils.clean_name(seqinfo.iloc[0]['PatientName'])  # this does not change

    # keep 3D
    seqinfo = utils.keep_ndim(seqinfo, '3D', seq_regex)

    seqinfo_T2w   = utils.slice_with_genericfield(seqinfo, 'SequenceName', '.spcR?_'  )
    seqinfo_FLAIR = utils.slice_with_genericfield(seqinfo, 'SequenceName', '.spcirR?_')

    # ------------------------------------------------------------------------------------------------------------------
    # T2w : 3DT2 SPACE

    # build groups of parameters
    columns = ['SeriesDescription', 'ImageTypeStr']
    groups = seqinfo_T2w.groupby(columns)

    # loop over groups
    for grp_name, series in groups:

        first_serie = series.iloc[0]  # they are all the same (except run number), so take the first one

        acq = utils.clean_name(first_serie['ProtocolName'])
        image_type_useful = ''.join(first_serie['ImageType'][3:])

        # loop over runs
        run_idx = 0
        for row_idx, seq in series.iterrows():
            run_idx += 1
            vol                   = seq['Volume']
            vol.tag               = 'anat'
            vol.suffix            = 'T2w'
            vol.sub               = sub
            vol.bidsfields['acq'] = acq
            vol.bidsfields['rec'] = image_type_useful
            vol.bidsfields['run'] = run_idx

    # ------------------------------------------------------------------------------------------------------------------
    # FLAIR : 3DFLAIR SPACE

    # build groups of parameters
    columns = ['SeriesDescription', 'ImageTypeStr']
    groups = seqinfo_FLAIR.groupby(columns)

    # loop over groups
    for grp_name, series in groups:

        first_serie = series.iloc[0]  # they are all the same (except run number), so take the first one

        acq = utils.clean_name(first_serie['ProtocolName'])
        image_type_useful = ''.join(first_serie['ImageType'][3:])

        # loop over runs
        run_idx = 0
        for row_idx, seq in series.iterrows():
            run_idx += 1
            vol                   = seq['Volume']
            vol.tag               = 'anat'
            vol.suffix            = 'FLAIR'
            vol.sub               = sub
            vol.bidsfields['acq'] = acq
            vol.bidsfields['rec'] = image_type_useful
            vol.bidsfields['run'] = run_idx


########################################################################################################################
def prog_diff(df: pandas.DataFrame, seq_regex: str) -> None:
    seqinfo = utils.slice_with_genericfield(df, 'PulseSequenceDetails', seq_regex)  # get list of corresponding sequence
    if seqinfo.empty: return  # just to run the code faster
    sub = utils.clean_name(seqinfo.iloc[0]['PatientName'])  # this does not change

    # keep 2D acquistion type
    seqinfo = utils.keep_ndim(seqinfo, '2D', seq_regex)

    # keep ORIGINAL images, discard ADC, FA, ColFA, ...
    seqinfo_original = utils.slice_with_imagetype_original(seqinfo)
    seqinfo_discard = seqinfo.drop(seqinfo_original.index)
    for row_idx, seq in seqinfo_discard.iterrows():
        vol                   = seq['Volume']
        vol.reason_not_ready  = f"dwi non-ORIGINAL {str(seq['ImageType'])}"
    seqinfo = seqinfo_original

    # ------------------------------------------------------------------------------------------------------------------
    # in case of multiband sequence, SBRef images may be generated
    # therefore, we need to deal with them beforehand

    seqinfo_sbref = utils.slice_with_genericfield(seqinfo, 'SeriesDescription', '.*_SBRef$')

    # build groups of parameters
    columns = ['SeriesDescription', 'PhaseEncodingDirection']
    groups = seqinfo_sbref.groupby(columns)

    # loop over groups
    for grp_name, series in groups:

        first_serie = series.iloc[0]  # they are all the same (except run number), so take the first one

        acq = utils.clean_name(first_serie['ProtocolName'])
        dir = utils.get_phase_encoding_direction(first_serie['PhaseEncodingDirection'])

        # loop over runs
        run_idx = 0
        for row_idx, seq in series.iterrows():
            run_idx += 1
            vol                   = seq['Volume']
            vol.tag               = 'dwi'
            vol.suffix            = 'sbref'
            vol.sub               = sub
            vol.bidsfields['acq'] = acq
            vol.bidsfields['dir'] = dir
            vol.bidsfields['run'] = run_idx
            seqinfo = seqinfo.drop(row_idx)  ## !! important : drop series that we flagged as SBRef !!

    # ------------------------------------------------------------------------------------------------------------------
    # only keep 4D data
    # ex : 1 volume can be acquired quickly to check subject position over time, so discard it, its not "BOLD"
    for row_idx, seq in seqinfo.iterrows():
        nii = nibabel.load( seq['Volume'].nii.path )
        if nii.ndim < 4:  # check 4D
            seq['Volume'].reason_not_ready = 'non-4D dwi volume'
            seqinfo = seqinfo.drop(row_idx)

    # ------------------------------------------------------------------------------------------------------------------
    # and now the normal volume

    # build groups of parameters
    columns = ['SeriesDescription', 'PhaseEncodingDirection']
    groups = seqinfo.groupby(columns)

    # loop over groups
    for grp_name, series in groups:

        first_serie = series.iloc[0]  # they are all the same (except run number), so take the first one

        acq = utils.clean_name(first_serie['ProtocolName'])
        dir = utils.get_phase_encoding_direction(first_serie['PhaseEncodingDirection'])

        # loop over runs
        run_idx = 0
        for row_idx, seq in series.iterrows():
            run_idx += 1
            vol                   = seq['Volume']
            vol.tag               = 'dwi'
            vol.suffix            = 'dwi'
            vol.sub               = sub
            vol.bidsfields['acq'] = acq
            vol.bidsfields['dir'] = dir
            vol.bidsfields['run'] = run_idx
            # check if .bval et .bvec exist
            has_bval = vol.check_if_bval_exists()
            has_bvec = vol.check_if_bvec_exists()
            if not has_bval:
                vol.reason_not_ready += '[ no .bval file ]'
            if not has_bvec:
                vol.reason_not_ready += '[ no .bvec file ]'
            if not has_bval or not has_bvec:
                vol.tag = ''  # move it => this serie will be discarded


########################################################################################################################
def prog_bold(df: pandas.DataFrame, seq_regex: str) -> None:
    seqinfo = utils.slice_with_genericfield(df, 'PulseSequenceDetails', seq_regex)  # get list of corresponding sequence
    if seqinfo.empty: return  # just to run the code faster
    sub = utils.clean_name(seqinfo.iloc[0]['PatientName'])  # this does not change

    # keep 2D acquistion type
    seqinfo = utils.keep_ndim(seqinfo, '2D', seq_regex)

    # ------------------------------------------------------------------------------------------------------------------
    # in case of multiband sequence, SBRef images may be generated
    # therefore, we need to deal with them beforehand
    seqinfo_sbref = utils.slice_with_genericfield(seqinfo, 'SeriesDescription', '.*_SBRef$')

    # build groups of parameters
    columns = ['SeriesDescription', 'PhaseEncodingDirection', 'ImageTypeStr']
    columns, seqinfo_sbref, has_EchoNumber = utils.complete_columns_with_echonumber(columns, seqinfo)
    groups = seqinfo_sbref.groupby(columns)

    # loop over groups
    for grp_name, series in groups:

        first_serie = series.iloc[0]  # they are all the same (except run number), so take the first one

        task = utils.clean_name(first_serie['ProtocolName'])
        dir  = utils.get_phase_encoding_direction(first_serie['PhaseEncodingDirection'])
        echo = utils.get_echo_number(first_serie, has_EchoNumber)
        part = utils.get_mag_or_pha(first_serie)

        # loop over runs
        run_idx = 0
        for row_idx, seq in series.iterrows():
            run_idx += 1
            vol                    = seq['Volume']
            vol.tag                = 'func'
            vol.suffix             = 'sbref'
            vol.sub                = sub
            vol.bidsfields['task'] = task
            vol.bidsfields['dir']  = dir
            vol.bidsfields['run']  = run_idx
            if echo > 0 : vol.bidsfields['echo']  = echo
            vol.bidsfields['part']  = part
            seqinfo = seqinfo.drop(row_idx)  ## !! important : drop series that we flagged as SBRef !!

    # ------------------------------------------------------------------------------------------------------------------
    # only keep 4D data
    # ex : 1 volume can be acquired quickly to check subject position over time, so discard it, its not "BOLD"
    for row_idx, seq in seqinfo.iterrows():
        nii = nibabel.load( seq['Volume'].nii.path )
        if nii.ndim < 4:  # check 4D
            seq['Volume'].reason_not_ready = 'non-4D bold volume'
            seqinfo = seqinfo.drop(row_idx)

    # ------------------------------------------------------------------------------------------------------------------
    # now that we already parsed SBRef and eliminated non-4D volumes, we can continue with the "normal" bold volumes

    # build groups of parameters
    columns = ['SeriesDescription', 'PhaseEncodingDirection', 'ImageTypeStr']
    columns, seqinfo, has_EchoNumber = utils.complete_columns_with_echonumber(columns, seqinfo)
    groups = seqinfo.groupby(columns)

    # loop over groups
    for grp_name, series in groups:

        first_serie = series.iloc[0]  # they are all the same (except run number), so take the first one

        task = utils.clean_name(first_serie['ProtocolName'])
        dir  = utils.get_phase_encoding_direction(first_serie['PhaseEncodingDirection'])
        echo = utils.get_echo_number(first_serie, has_EchoNumber)
        part = utils.get_mag_or_pha(first_serie)

        # loop over runs
        run_idx = 0
        for _, seq in series.iterrows():
            run_idx += 1
            vol                    = seq['Volume']
            vol.tag                = 'func'
            vol.suffix             = 'bold'
            vol.sub                = sub
            vol.bidsfields['task'] = task
            vol.bidsfields['dir']  = dir
            vol.bidsfields['run']  = run_idx
            if echo > 0 : vol.bidsfields['echo']  = echo
            vol.bidsfields['part']  = part


########################################################################################################################
def prog_fmap(df: pandas.DataFrame, seq_regex: str) -> None:
    seqinfo = utils.slice_with_genericfield(df, 'PulseSequenceDetails', seq_regex)  # get list of corresponding sequence
    if seqinfo.empty: return  # just to run the code faster
    sub = utils.clean_name(seqinfo.iloc[0]['PatientName'])  # this does not change

    # keep 2D
    seqinfo = utils.keep_ndim(seqinfo, '2D', seq_regex)

    # separate magnitude & phase images

    # ------------------------------------------------------------------------------------------------------------------
    # magnitude
    seqinfo_mag = utils.slice_with_imagetype(seqinfo, 'M')

    # build groups of parameters
    columns = ['SeriesDescription', 'EchoNumber']
    groups = seqinfo_mag.groupby(columns)

    # loop over groups
    for grp_name, series in groups:

        first_serie = series.iloc[0]  # they are all the same (except run number), so take the first one

        acq = utils.clean_name(first_serie['ProtocolName'])

        # loop over runs
        run_idx = 0
        for row_idx, seq in series.iterrows():
            run_idx += 1
            vol                   = seq['Volume']
            vol.tag               = 'fmap'
            vol.suffix            = f"magnitude{int(seq['EchoNumber'])}"  # suffix has to be _magnitude1 _magnitude2
            vol.sub               = sub
            vol.bidsfields['acq'] = acq
            vol.bidsfields['run'] = run_idx

    # ------------------------------------------------------------------------------------------------------------------
    # phase
    seqinfo_pha = utils.slice_with_imagetype(seqinfo, 'P')

    # build groups of parameters
    columns = ['SeriesDescription']
    groups = seqinfo_pha.groupby(columns)

    # loop over groups
    for grp_name, series in groups:

        first_serie = series.iloc[0]  # they are all the same (except run number), so take the first one

        acq = utils.clean_name(first_serie['ProtocolName'])

        # loop over runs
        run_idx = 0
        for row_idx, seq in series.iterrows():
            run_idx += 1
            vol                   = seq['Volume']
            vol.tag               = 'fmap'
            vol.suffix            = 'phasediff'
            vol.sub               = sub
            vol.bidsfields['acq'] = acq
            vol.bidsfields['run'] = run_idx


########################################################################################################################
def prog_gre(df: pandas.DataFrame, seq_regex: str) -> None:
    seqinfo = utils.slice_with_genericfield(df, 'PulseSequenceDetails', seq_regex)  # get list of corresponding sequence
    if seqinfo.empty: return  # just to run the code faster
    sub = utils.clean_name(seqinfo.iloc[0]['PatientName'])  # this does not change

    # build groups of parameters
    columns = ['SeriesDescription', 'ImageTypeStr']
    columns, seqinfo, has_EchoNumber = utils.complete_columns_with_echonumber(columns, seqinfo)
    groups = seqinfo.groupby(columns)

    # loop over groups
    for grp_name, series in groups:

        first_serie = series.iloc[0]  # they are all the same (except run number), so take the first one

        acq  = utils.clean_name(first_serie['ProtocolName'])
        echo = utils.get_echo_number(first_serie, has_EchoNumber)
        part = utils.get_mag_or_pha(first_serie)

        # loop over runs
        run_idx = 0
        for _, seq in series.iterrows():
            run_idx += 1
            vol                   = seq['Volume']
            vol.tag               = 'anat'
            vol.sub               = sub
            vol.bidsfields['acq'] = acq
            vol.bidsfields['run'] = run_idx
            if echo > 0 :
                vol.bidsfields['echo']  = echo
                vol.bidsfields['part']  = part
                vol.suffix              = 'MEGRE'
            else:
                vol.bidsfields['part']  = part
                vol.suffix              = 'T2starw'


########################################################################################################################
def prog_tse(df: pandas.DataFrame, seq_regex: str) -> None:
    seqinfo = utils.slice_with_genericfield(df, 'PulseSequenceDetails', seq_regex)  # get list of corresponding sequence
    if seqinfo.empty: return  # just to run the code faster
    sub = utils.clean_name(seqinfo.iloc[0]['PatientName'])  # this does not change

    seqinfo_T2w   = utils.slice_with_genericfield(seqinfo, 'SequenceName', '.*tse')
    seqinfo_FLAIR = utils.slice_with_genericfield(seqinfo, 'SequenceName', '.*tir')

    # ------------------------------------------------------------------------------------------------------------------
    # T2w

    # build groups of parameters
    columns = ['SeriesDescription', 'ImageTypeStr']
    groups = seqinfo_T2w.groupby(columns)

    # loop over groups
    for grp_name, series in groups:

        first_serie = series.iloc[0]  # they are all the same (except run number), so take the first one

        acq = utils.clean_name(first_serie['ProtocolName'])
        image_type_useful = ''.join(first_serie['ImageType'][3:])

        # loop over runs
        run_idx = 0
        for row_idx, seq in series.iterrows():
            run_idx += 1
            vol                   = seq['Volume']
            vol.tag               = 'anat'
            vol.suffix            = 'T2w'
            vol.sub               = sub
            vol.bidsfields['acq'] = acq
            vol.bidsfields['rec'] = image_type_useful
            vol.bidsfields['run'] = run_idx

    # ------------------------------------------------------------------------------------------------------------------
    # FLAIR

    # build groups of parameters
    columns = ['SeriesDescription', 'ImageTypeStr']
    groups = seqinfo_FLAIR.groupby(columns)

    # loop over groups
    for grp_name, series in groups:

        first_serie = series.iloc[0]  # they are all the same (except run number), so take the first one

        acq = utils.clean_name(first_serie['ProtocolName'])
        image_type_useful = ''.join(first_serie['ImageType'][3:])

        # loop over runs
        run_idx = 0
        for row_idx, seq in series.iterrows():
            run_idx += 1
            vol                   = seq['Volume']
            vol.tag               = 'anat'
            vol.suffix            = 'FLAIR'
            vol.sub               = sub
            vol.bidsfields['acq'] = acq
            vol.bidsfields['rec'] = image_type_useful
            vol.bidsfields['run'] = run_idx


########################################################################################################################
def prog_ep2d_se(df: pandas.DataFrame, seq_regex: str) -> None:
    seqinfo = utils.slice_with_genericfield(df, 'PulseSequenceDetails', seq_regex)  # get list of corresponding sequence
    if seqinfo.empty: return  # just to run the code faster
    sub = utils.clean_name(seqinfo.iloc[0]['PatientName'])  # this does not change

    # keep 2D
    seqinfo = utils.keep_ndim(seqinfo, '2D', seq_regex)

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
    seqinfo = utils.slice_with_genericfield(df, 'PulseSequenceDetails', seq_regex)  # get list of corresponding sequence
    if seqinfo.empty: return  # just to run the code faster
    sub = utils.clean_name(seqinfo.iloc[0]['PatientName'])  # this does not change

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

    # [ORIGINAL, PRIMARY, M, ND, MOSAIC] -> ORIGINAL_PRIMARY_M_ND_MOSAIC
    df['ImageTypeStr'] = df['ImageType'].apply(lambda s: '_'.join(s))

    # subject by subject sequence group
    df_by_subject = df.groupby('PatientName')

    # call each routine depending on the sequence name
    for name, group in df_by_subject:       # loop over subjects
        for seq_regex, fcn_name in config:  # loop over sequence decision tree
            func = eval(fcn_name)   # fetch the name of the prog_ to call dynamically
            func(group, seq_regex)  # execute the prog_

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
