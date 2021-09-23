import argparse  # parser of the CLI
import metadata  # get_version
import workflow  # main functions here


########################################################################################################################
def main():

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

    parser.add_argument("--logfile",
                        help="Write logfile (default=True)",
                        dest="logfile",
                        action="store_true")
    parser.add_argument("--no-logfile",
                        dest="logfile",
                        action="store_false")
    parser.set_defaults(logfile=True)

    args = parser.parse_args()

    # Format args
    args = workflow.format_args(args)

    # Workflow
    workflow.run(args)
