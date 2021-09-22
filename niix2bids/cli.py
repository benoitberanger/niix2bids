import sys
import argparse
import metadata


########################################################################################################################
def main():

    # ------------------------------------------------------------------------------------------------------------------
    # Parse command line arguments

    parser = argparse.ArgumentParser(description="Create BIDS architecture from nifti files (and .json sidecars)",
                                     epilog=f"niix2bids version {metadata.get_version()}")

    parser.add_argument("nifti_dir",
                        help="nifti directory that will be parsed and transformed into BIDS architecture."
                             "This directory is usually the output directory of dcm2niix.")
    parser.add_argument("out_dir",
                        help="Output directory, receiving the BIDS architecture.")
    parser.add_argument("-v", "--verbose",
                        help="increase output verbosity : -v / -vv / -vvv ...",
                        action="count",
                        default=0)

    args = parser.parse_args()

    # ------------------------------------------------------------------------------------------------------------------
    print(args)
    print("done")
