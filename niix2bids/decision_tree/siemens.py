# standard modules
import logging  # logging lib (terminal & file)
import sys      # to stop script execution on case of error

# dependency modules
import pandas

# local modules
from niix2bids.decision_tree import utils


# get logger with current name
log = logging.getLogger(__name__)


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

    return ""
