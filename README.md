# niix2bids
Automatic BIDS architecture


## Background
[BIDS](https://bids.neuroimaging.io/) is widly used for sharing neuroimagind datasets. In particular *nifti* files.
There are several packages that have a semi-automatic approach to conform datasets to BIDS, such as [Dcm2Bids](https://github.com/UNFmontreal/Dcm2Bids)
However this package objective is to be 100% autmotatic.


## Usage
```
usage: niix2bids [-h] -i DIR [DIR ...] -o DIR [-v] [--logfile] [--no-logfile]

Create BIDS architecture from nifti files and .json sidecars. This method
expects DICOM converted by dcm2niix (https://github.com/rordenlab/dcm2niix)

Required arguments:
  -i DIR [DIR ...], --in_dir DIR [DIR ...]
                        Nifti directories that will be parsed and transformed
                        into BIDS architecture. This directory is usually the
                        output directory of dcm2niix. This argument accepts
                        several paths. You can use syntax such as
                        /path/to/nii/2021_*
  -o DIR, --out_dir DIR
                        Output directory, receiving the BIDS architecture.

Optional arguments:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit
  --logfile             write logfile (default=True)
  --no-logfile

niix2bids_version==0.0.1 + bids_version==1.6.0
```

## Limitations

- Only works with:
  - Siemens magnets
  - MRI data
  - dicom converted using [dcm2niix](https://github.com/rordenlab/dcm2niix)
- `PatientName` must be in the JSON file. Use [dcm2niix](https://github.com/rordenlab/dcm2niix) with option `-ba n` to **disable** anonmyzation


## Installation


### Python version

`python >= 3.6` Tested on `3.6` & `3.9`


### Dependecies

- `pandas`
- `nibabel`


### How to

Run the command :
`pip install git+https://github.com/benoitberanger/niix2bids`


## Known issues

Weird things happend to me at installtion due to outdated version of `setuptools`, a packages bundled with `pip`.  
When you create a new python environement, I never had problem. Here is an example of lines to create a fresh `conda` environement :
```
conda create --name niix2bids_python3.9 # python3.9 runs faster than 3.6
conda activate niix2bids_python3.9
conda install pip # to make sure to have a version in the env
pip install git+https://github.com/benoitberanger/niix2bids
```
