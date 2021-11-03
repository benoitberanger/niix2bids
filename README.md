# niix2bids


Automatic BIDS architecture. Convert your DICOM with [dcm2niix](https://github.com/rordenlab/dcm2niix), 
then use this package as a command line to organize your dataset into [BIDS](https://bids.neuroimaging.io/).

## Background

[BIDS](https://bids.neuroimaging.io/) is widely used for sharing neuroimaging datasets. In particular *nifti* files.
There are several packages that have a semi-automatic approach to organize datasets to BIDS, such as [Dcm2Bids](https://github.com/UNFmontreal/Dcm2Bids)
However the objective here is to be 100% automatic.


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
  - MRI data
  - Siemens magnets
  - DICOM converted using [dcm2niix](https://github.com/rordenlab/dcm2niix)
- `PatientName` **must** be in the JSON file. Use [dcm2niix](https://github.com/rordenlab/dcm2niix) with option `-ba n` to **disable** anonymization


## Installation

### Python version & other dependencies 

#### Python version

`python >= 3.6` Tested on `3.6` & `3.9`

#### Package dependencies
- `pandas`
- `nibabel`


### How to

#### Recommended setup

Use [conda](https://docs.conda.io/en/latest/miniconda.html) to create a new python environment.

**Standard**

```
conda create --name niix2bids_python3.9 # python3.9 runs faster than 3.6
conda activate niix2bids_python3.9
conda install pip # to make sure to have a version in the env
pip install git+https://github.com/benoitberanger/niix2bids
```

**Developer**

If you want to install in "developer" mode using the Git local repository, clone the repo before, then change the installation line :

```
cd /path/to/mydir/
git clone https://github.com/benoitberanger/niix2bids
conda create --name niix2bids_python3.9 # python3.9 runs faster than 3.6
conda activate niix2bids_python3.9
conda install pip # to make sure to have a version in the env
pip install -e niix2bids/
```

If you want to make a PR, this the recommended strategy, because you can control branching in your local clone of the repository


#### **NOT** recommended installation procedure

`pip install git+https://github.com/benoitberanger/niix2bids`  
The installation might crash because of wrong dependencies' management. Check [Known issues](https://github.com/benoitberanger/niix2bids#known-issues) section.

## Known issues

Weird things happened to me at installation due to outdated version of `setuptools`, a packages bundled with `pip`.  
When I create a new python environment, I never had problem.

`pip install niix2bids` is not possible yet. I did not register this packaged on https://pypi.org/.

