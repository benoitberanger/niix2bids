# standard modules
import logging  # logging lib (terminal & file)

# dependency modules
import pandas

# local modules
from niix2bids.decision_tree import utils


# get logger with current name
log = logging.getLogger(__name__)


########################################################################################################################
def mprage(df: pandas.DataFrame, seq_regex: str) -> str:
    seq_info = utils.slice_with_seqname(df, seq_regex)
    return ""


########################################################################################################################
def run(list_param: list[dict]) -> str:

    log.info(f'starting decision tree for "Siemens"... ')

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
        ['tfl'              , 'mprage' ],  # mprage & mp2rage
        # ['mp2rage'          , 'mprage' ],  # mp2rage WIP
        # ['tse_vfl'          , 'tse_vfl'],  # 3DT2 space & 3DFLAIR space_ir
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
        job = func(df, seq_regex)

    return job
