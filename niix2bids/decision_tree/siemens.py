# standard modules
from typing import List  # for function signature

# dependency modules
import pandas as pd # for DataFrame
import nibabel      # to load nifti header

# local modules
from niix2bids.decision_tree import utils
from niix2bids.classes import Volume
from niix2bids.utils import get_logger


########################################################################################################################
def prog_mprage(seqinfo: pd.DataFrame, sub_name: str, ses: int) -> None:

    # keep 3D
    seqinfo = utils.keep_ndim(seqinfo, '3D')

    # here is a example of ImageType for all images for 1 sequence :
    # "ImageType": ["ORIGINAL", "PRIMARY", "M"     , "ND", "NORM"], <--- inv1
    # "ImageType": ["ORIGINAL", "PRIMARY", "M"     , "ND", "NORM"], <--- inv2
    # "ImageType": ["DERIVED" , "PRIMARY", "T1 MAP", "ND"        ], <--- T1map
    # "ImageType": ["DERIVED" , "PRIMARY", "M"     , "ND", "UNI" ], <--- UNIT1
    seqinfo_mag    = utils.slice_with_imagetype(seqinfo, 'M')
    seqinfo_T1map1 = utils.slice_with_imagetype(seqinfo, 'T1 MAP')  # Siemens mp2rage product
    seqinfo_T1map2 = utils.slice_with_imagetype(seqinfo, 'T1')      # Siemens mp2rage WIP
    seqinfo_pha    = utils.slice_with_imagetype(seqinfo, 'P')
    seqinfo        = pd.concat([seqinfo_mag, seqinfo_pha, seqinfo_T1map1, seqinfo_T1map2])

    # ------------------------------------------------------------------------------------------------------------------
    # in case of mp2rage, there are 3 (or 4 wih T1map) images generated
    # the SeriesDescription is automatically generated such as ProtocolName + suffix, where suffix = _INV1, _INV2,
    # _UNI_Images (and _T1_Images)
    descr_regex_list = ['.*_INV1$', '.*_INV2$', '.*_INV1_PHS$', '.*_INV2_PHS$', '.*_T1_Images$', '.*_UNI_Images$']
    inv_number       = [1         , 2         , 1             , 2             , None           , None            ]
    suffix_list      = ['MP2RAGE' ,  'MP2RAGE', 'MP2RAGE'     ,  'MP2RAGE'    , 'T1map'        , 'UNIT1'         ]
    for idx, descr_regex in enumerate(descr_regex_list):

        seqinfo_suffix = utils.slice_with_genericfield(seqinfo, 'SeriesDescription', descr_regex)

        suffix = suffix_list[idx]
        if suffix == 'MP2RAGE':
            inv  = inv_number[idx]
            if len(seqinfo_suffix)>0: part = utils.get_mag_or_pha(seqinfo_suffix.iloc[0])
        else:
            inv  = ''
            part = ''

        # build groups of parameters
        columns = ['SeriesDescription', 'ImageTypeStr']
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
                vol.ses               = ses
                vol.tag               = 'anat'
                vol.suffix            = suffix
                vol.sub               = sub_name
                vol.bidsfields['acq'] = acq
                vol.bidsfields['run'] = run_idx
                if bool(inv ): vol.bidsfields['inv' ] = inv
                if bool(part): vol.bidsfields['part'] = part
                seqinfo = seqinfo.drop(row_idx)  # !! important : drop series that we already flagged !!

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
            vol.ses               = ses
            vol.tag               = 'anat'
            vol.suffix            = 'T1w'
            vol.sub               = sub_name
            vol.bidsfields['acq'] = acq
            vol.bidsfields['rec'] = image_type_useful
            vol.bidsfields['run'] = run_idx


########################################################################################################################
def prog_tse_vfl(seqinfo: pd.DataFrame, sub_name: str, ses: int) -> None:

    # keep 3D
    seqinfo = utils.keep_ndim(seqinfo, '3D')

    seqinfo_T2w   = utils.slice_with_genericfield(seqinfo, 'SequenceName', '.?spcR?'  )
    seqinfo_FLAIR = utils.slice_with_genericfield(seqinfo, 'SequenceName', '.?spcirR?')

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
            vol.ses               = ses
            vol.tag               = 'anat'
            vol.suffix            = 'T2w'
            vol.sub               = sub_name
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
            vol.ses               = ses
            vol.tag               = 'anat'
            vol.suffix            = 'FLAIR'
            vol.sub               = sub_name
            vol.bidsfields['acq'] = acq
            vol.bidsfields['rec'] = image_type_useful
            vol.bidsfields['run'] = run_idx


########################################################################################################################
def prog_diff(seqinfo: pd.DataFrame, sub_name: str, ses: int) -> None:

    # keep 2D acquistion type
    seqinfo = utils.keep_ndim(seqinfo, '2D')

    # keep ORIGINAL images, discard ADC, FA, ColFA, ...
    seqinfo_original = utils.slice_with_imagetype_original(seqinfo)
    seqinfo_discard = seqinfo.drop(seqinfo_original.index)
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
            vol.ses               = ses
            vol.tag               = 'dwi'
            vol.suffix            = 'sbref'
            vol.sub               = sub_name
            vol.bidsfields['acq'] = acq
            vol.bidsfields['dir'] = dir
            vol.bidsfields['run'] = run_idx
            seqinfo = seqinfo.drop(row_idx)  # !! important : drop series that we flagged as SBRef !!

    # ------------------------------------------------------------------------------------------------------------------
    # only keep 4D data
    # ex : 1 volume can be acquired quickly to check subject position over time, so discard it, its not "BOLD"
    for row_idx, seq in seqinfo.iterrows():
        nii = nibabel.load(seq['Volume'].nii.path)
        if nii.ndim < 4:  # check 4D
            seq['Volume'].reason_not_ready = 'non-4D dwi volume'
            seq['Volume'].tag = 'NON_BIDS'

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
            vol.ses               = ses
            if len(vol.tag) == 0:
                vol.tag           = 'dwi'
            else:
                pass  # because it's a 'DISCARD' from 'non-4D'
            vol.suffix            = 'dwi'
            vol.sub               = sub_name
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
                vol.tag = 'NON_BIDS'  # remove it => this serie will be discarded

    # ------------------------------------------------------------------------------------------------------------------
    # treat non-original

    # build groups of parameters
    columns = ['SeriesDescription', 'PhaseEncodingDirection']
    groups = seqinfo_discard.groupby(columns)

    # loop over groups
    for grp_name, series in groups:

        first_serie = series.iloc[0]  # they are all the same (except run number), so take the first one

        acq = utils.clean_name(first_serie['ProtocolName'])
        dir = utils.get_phase_encoding_direction(first_serie['PhaseEncodingDirection'])

        # loop over runs
        run_idx = 0
        for row_idx, seq in series.iterrows():
            run_idx += 1
            vol = seq['Volume']
            vol.ses = ses
            vol.reason_not_ready = f"dwi non-ORIGINAL {str(seq['ImageType'])}"
            vol.tag = 'NON_BIDS'
            vol.suffix = 'dwi'
            vol.sub = sub_name
            vol.bidsfields['acq'] = acq
            vol.bidsfields['dir'] = dir
            vol.bidsfields['run'] = run_idx


########################################################################################################################
def prog_bold(seqinfo: pd.DataFrame, sub_name: str, ses: int) -> None:

    # keep 2D acquisition type
    seqinfo = utils.keep_ndim(seqinfo, '2D')

    # ------------------------------------------------------------------------------------------------------------------
    # in case of multiband sequence, SBRef images may be generated
    # therefore, we need to deal with them beforehand
    seqinfo_sbref = utils.slice_with_genericfield(seqinfo, 'SeriesDescription', '.*_SBRef$')

    # build groups of parameters
    columns = ['SeriesDescription', 'PhaseEncodingDirection', 'ImageTypeStr']
    columns, seqinfo_sbref, has_EchoNumber = utils.complete_columns_with_echonumber(columns, seqinfo_sbref)
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
            vol                     = seq['Volume']
            vol.ses                 = ses
            vol.tag                 = 'func'
            vol.suffix              = 'sbref'
            vol.sub                 = sub_name
            vol.bidsfields['task']  = task
            vol.bidsfields['dir']   = dir
            vol.bidsfields['run']   = run_idx
            if echo > 0 : vol.bidsfields['echo']  = echo
            vol.bidsfields['part']  = part
            seqinfo = seqinfo.drop(row_idx)  # !! important : drop series that we flagged as SBRef !!

    # ------------------------------------------------------------------------------------------------------------------
    # only keep 4D data
    # ex : 1 volume can be acquired quickly to check subject position over time, so discard it, its not "BOLD"
    for row_idx, seq in seqinfo.iterrows():
        nii = nibabel.load( seq['Volume'].nii.path )
        if nii.ndim < 4:  # check 4D
            seq['Volume'].reason_not_ready = 'non-4D bold volume'
            seq['Volume'].tag = 'NON_BIDS'

    # ------------------------------------------------------------------------------------------------------------------
    # now that we already parsed SBRef and flagged non-4D volumes, we can continue with the "normal" bold volumes

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
            vol.ses                = ses
            if len(vol.tag) == 0:
                vol.tag            = 'func'
            else:
                pass  # because it's a 'DISCARD' from 'non-4D'
            vol.suffix             = 'bold'
            vol.sub                = sub_name
            vol.bidsfields['task'] = task
            vol.bidsfields['dir']  = dir
            vol.bidsfields['run']  = run_idx
            if echo > 0 : vol.bidsfields['echo']  = echo
            vol.bidsfields['part']  = part


########################################################################################################################
def prog_fmap(seqinfo: pd.DataFrame, sub_name: str, ses: int) -> None:

    # keep 2D
    seqinfo = utils.keep_ndim(seqinfo, '2D')

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
            vol.ses               = ses
            vol.tag               = 'fmap'
            vol.suffix            = f"magnitude{int(seq['EchoNumber'])}"  # suffix has to be _magnitude1 _magnitude2
            vol.sub               = sub_name
            vol.bidsfields['acq'] = acq
            vol.bidsfields['run'] = run_idx

    # ------------------------------------------------------------------------------------------------------------------
    # phase
    seqinfo_pha = utils.slice_with_imagetype(seqinfo, 'P')

    # build groups of parameters
    columns = 'SeriesDescription'
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
            vol.ses               = ses
            vol.tag               = 'fmap'
            vol.suffix            = 'phasediff'
            vol.sub               = sub_name
            vol.bidsfields['acq'] = acq
            vol.bidsfields['run'] = run_idx


########################################################################################################################
def prog_gre(seqinfo: pd.DataFrame, sub_name: str, ses: int) -> None:

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
            vol.ses               = ses
            vol.tag               = 'anat'
            vol.sub               = sub_name
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
def prog_tse(seqinfo: pd.DataFrame, sub_name: str, ses: int) -> None:

    seqinfo_T2w   = utils.slice_with_genericfield(seqinfo, 'SequenceName', '.*t?se')
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
            vol.ses               = ses
            vol.tag               = 'anat'
            vol.suffix            = 'T2w'
            vol.sub               = sub_name
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
            vol.ses               = ses
            vol.tag               = 'anat'
            vol.suffix            = 'FLAIR'
            vol.sub               = sub_name
            vol.bidsfields['acq'] = acq
            vol.bidsfields['rec'] = image_type_useful
            vol.bidsfields['run'] = run_idx


########################################################################################################################
def prog_ep2d_se(seqinfo: pd.DataFrame, sub_name: str, ses: int) -> None:

    # keep 2D
    seqinfo = utils.keep_ndim(seqinfo, '2D')

    # keep magnitude, since phase is not part of BIDS specs at the moment
    seqinfo_magnitude = utils.slice_with_imagetype(seqinfo, 'M')
    seqinfo_discard = seqinfo.drop(seqinfo_magnitude.index)
    for _, seq in seqinfo_discard.iterrows():
        vol                   = seq['Volume']
        vol.reason_not_ready  = f"fmap epi non-magnitude {str(seq['ImageType'])}"
        vol.tag               = 'DISCARD'
    seqinfo = seqinfo_magnitude

    # build groups of parameters
    columns = ['SeriesDescription', 'PhaseEncodingDirection']
    groups = seqinfo.groupby(columns)

    # loop over groups
    for grp_name, series in groups:

        first_serie = series.iloc[0]  # they are all the same (except run number), so take the first one

        acq  = utils.clean_name(first_serie['ProtocolName'])
        dir  = utils.get_phase_encoding_direction(first_serie['PhaseEncodingDirection'])

        # loop over runs
        run_idx = 0
        for _, seq in series.iterrows():
            run_idx += 1
            vol                    = seq['Volume']
            vol.ses                = ses
            vol.tag                = 'fmap'
            vol.suffix             = 'epi'
            vol.sub                = sub_name
            vol.bidsfields['acq']  = acq
            vol.bidsfields['dir']  = dir
            vol.bidsfields['run']  = run_idx


########################################################################################################################
def prog_DISCARD(seqinfo: pd.DataFrame, sub_name: str, ses: int) -> None:

    # build groups of parameters
    columns = 'SeriesDescription'
    groups = seqinfo.groupby(columns)

    # loop over groups
    for grp_name, series in groups:

        first_serie = series.iloc[0]  # they are all the same (except run number), so take the first one

        acq = utils.clean_name(first_serie['ProtocolName'])

        # loop over runs
        run_idx = 0
        for _, seq in series.iterrows():
            run_idx += 1
            vol                    = seq['Volume']
            vol.ses                = ses
            vol.tag                = 'DISCARD'
            vol.suffix             = ''
            vol.sub                = sub_name
            vol.bidsfields['acq']  = acq
            vol.bidsfields['run']  = run_idx
            vol.reason_not_ready  = f'discard PulseSequenceName = {first_serie["PulseSequenceName"]}'


########################################################################################################################
def prog_UNKNOWN(df: pd.DataFrame) -> None:

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
                    vol.reason_not_ready  = f"unknown PulseSequenceName = {seq['PulseSequenceName']}"


########################################################################################################################
def run(volume_list: List[Volume], config: list) -> pd.DataFrame:

    log = get_logger()

    log.info(f'starting decision tree for "Siemens"... ')

    list_param = utils.assemble_list_param(volume_list)

    # conversion of List[dict] to pd.DataFrame
    # pd.DataFrame object is like table in matlab, with much more embedded methods
    df = pd.DataFrame(list_param)

    # do all sanity checks
    df = utils.sanity_check(df)

    # make some extraction / conversion --------------------------------------------------------------------------------

    # %CustomerSeq%_cmrr_mbep2d_bold -> cmrr_mbep2d_bold
    df['PulseSequenceName'] = df['PulseSequenceDetails'].apply(lambda s: s.rsplit("%_")[1] if s.find("%_")>0 else s)

    # [ORIGINAL, PRIMARY, M, ND, MOSAIC] -> ORIGINAL_PRIMARY_M_ND_MOSAIC
    df['ImageTypeStr'] = df['ImageType'].apply(lambda s: '_'.join(s))

    # subject by subject group of sequences
    # this is mandatory, otherwise you would mix run numbers when series have same SeriesDescription,
    # which is usual in a cohort
    df_by_subject = df.groupby('PatientName')

    # call each routine depending on the sequence name
    for sub_name, df_subject in df_by_subject:
        sub_name_clean = utils.clean_name(sub_name)

        # also, we split each identical subject group by exam ID, so we can generate ses-<> field
        df_subject_by_ses = df_subject.groupby('StudyInstanceUID')

        ses = 0
        for _, df_by_sess in df_subject_by_ses:
            ses += 1
            
            for seq_regex, fcn_name in config:      # loop over sequence decision tree
    
                # get list of corresponding sequence
                seqinfo = utils.slice_with_genericfield(df_by_sess, 'PulseSequenceName', seq_regex)
                if seqinfo.empty: continue          # just to run the code faster

                func = eval(fcn_name)               # fetch the name of the prog_ to call dynamically
                func(seqinfo, sub_name_clean, ses)  # execute the prog_*

    # deal with unknown sequences
    prog_UNKNOWN(df)

    # all done
    log.info(f'"Siemens" decision tree done')

    return df
