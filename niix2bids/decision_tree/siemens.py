# standard modules
import logging  # logging lib (terminal & file)
import sys      # to stop script execution on case of error

# dependency modules

# local modules
from niix2bids.decision_tree import check


# get logger with current name
log = logging.getLogger(__name__)


########################################################################################################################
def run(list_param: list[dict]) -> str:

    log.info(f'starting decision tree for "Siemens"... ')

    # checks
    check.assert_is_dcm2niix(list_param)
    check.assert_all_key_val(list_param, "Modality"    , "MR"     )
    check.assert_all_key_val(list_param, "Manufacturer", "Siemens")

    # extract useful parameters for the decision tree
    PulseSequenceDetails = [dic['PulseSequenceDetails'].rsplit("%_")[1] for dic in list_param]
    MRAcquisitionType    = [dic['MRAcquisitionType'   ]                 for dic in list_param]
    ProtocolName         = [dic['ProtocolName'        ]                 for dic in list_param]
    SeriesDescription    = [dic['SeriesDescription'   ]                 for dic in list_param]

    return ""
