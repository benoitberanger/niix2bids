# standard modules
import argparse  # parser of the CLI
import os        # for path management

# dependency modules

# local modules
import niix2bids
from niix2bids import metadata


########################################################################################################################
def format_args(args: argparse.Namespace) -> argparse.Namespace:

    # in
    if isinstance(args.in_dir, str):
        args.in_dir = [args.in_dir]
    args.in_dir = [os.path.abspath(one_dir) for one_dir in args.in_dir]

    # out
    args.out_dir = os.path.abspath(args.out_dir)

    return args


########################################################################################################################
def main():

    niix2bids_version = metadata.get_niix2bids_version()
    bids_version = metadata.get_bids_version()

    description="""
    Create BIDS architecture from nifti files and .json sidecars.
    This method expects DICOM converted by dcm2niix (https://github.com/rordenlab/dcm2niix)
    """

    epilog = f"niix2bids_version=={niix2bids_version} + bids_version=={bids_version}"

    # Parse command line arguments
    parser = argparse.ArgumentParser(description=description,
                                     epilog=epilog)

    # This is a strategy found on stackoverflow to seperate 'Required arguments' and 'Optional arguments'
    # in a way --help display looks more readable
    optional = parser._action_groups.pop()  # extract optonal arguments
    optional.title = "Optional arguments"

    # and now we add 'Required arguments'
    required = parser.add_argument_group("Required arguments")

    required.add_argument("-i", "--in_dir",
                        help="Nifti directories that will be parsed and transformed into BIDS architecture. "
                             "This directory is usually the output directory of dcm2niix. "
                             "This argument accepts several paths. You can use syntax such as /path/to/nii/2021_*",
                        nargs='+',
                        metavar='DIR',
                        required=True)
    required.add_argument("-o","--out_dir",
                        help="Output directory, receiving the BIDS architecture.",
                        metavar='DIR',
                        required=True)

    optional.add_argument("-v", "--version",
                          action="version",
                          version=niix2bids_version)

    optional.add_argument("--logfile",
                        help="write logfile (default=True)",
                        dest="logfile",
                        action="store_true")
    optional.add_argument("--no-logfile",
                        dest="logfile",
                        action="store_false")
    optional.set_defaults(logfile=True)

    parser._action_groups.append(optional) # this trick is just so the --help option appears correctly

    # Parse
    args = parser.parse_args()

    # Format args
    args = format_args(args)

    # Call workflow
    niix2bids.workflow.run(args)
