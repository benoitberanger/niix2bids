# niix2bids

Automatic BIDS architecture. Convert your DICOM with [dcm2niix](https://github.com/rordenlab/dcm2niix), 
then use this package as a command line to organize your dataset into [BIDS](https://bids.neuroimaging.io/).


## Background

[BIDS](https://bids.neuroimaging.io/) is widely used for sharing neuroimaging datasets.
There are several packages that have a semi-automatic approach to organize datasets to BIDS, such as [Dcm2Bids](https://github.com/UNFmontreal/Dcm2Bids).
To transform one or a few cohorts from dicom or nifti to BIDS, I would use [Dcm2Bids](https://github.com/UNFmontreal/Dcm2Bids).

However, for a more automatic approach with no prior on the input directory structure and file names,
[niix2bids](https://github.com/benoitberanger/niix2bids) can be better.
This should be the case for MRI centers that have lots of cohorts from different research protocol.
It may also be useful for clinical data with wide variations in naming conventions and parameters.


## Limitations

- Only works with:
  - MRI data
  - Siemens magnets
  - DICOM converted using [dcm2niix](https://github.com/rordenlab/dcm2niix)
- `PatientName` **must** be in the JSON file. Use [dcm2niix](https://github.com/rordenlab/dcm2niix) with option `-ba n` to **disable** anonymization.


## Usage
```
usage: niix2bids [-h] -i DIR [DIR ...] -o DIR [--symlink | --copyfile] [--logfile | --no-logfile] [-c FILE] [-v]

    Create BIDS architecture from nifti files and .json sidecars.
    This method expects DICOM converted by dcm2niix (https://github.com/rordenlab/dcm2niix)
    

Required arguments:
  -i DIR [DIR ...], --in_dir DIR [DIR ...]
                        Nifti directories that will be parsed and transformed into BIDS architecture.
                        This directory is usually the output directory of dcm2niix.
                        This argument accepts several paths. You can use syntax such as /path/to/nii/2021_*
  -o DIR, --out_dir DIR
                        Output directory, receiving the BIDS architecture.

Optional arguments:
  -h, --help            show this help message and exit
  --symlink             Use symlink (default). The out_dir will contain symlinks, saving disk spaces
  --copyfile            Use copyfile. Original files will be copied in out_dir. !! be careful of disk space !!
  --logfile             Write logfile (default)
  --no-logfile          Disable writing logfile
  -c FILE, --config_file FILE
                        If you want to use non-coded sequences such as new Products, WIP or C2P,
                        you can provide a config file.
                        Default location is ~/niix2bids_config_file/siemens.py
                        If default location is not present, try to use the template file 
                        located in [niix2bids]/config_file/siemens.py
  -v, --version         show program's version number and exit

niix2bids_version==v2.4.0 + bids_version==v1.6.0
```


## Installation

### Python version & other dependencies 

#### Python version

`python >= 3.6` Tested on `3.6`, `3.9`, `3.10`

#### Package dependencies
- `pandas` for [DataFrame](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.html)
- `nibabel` to [load](https://nipy.org/nibabel/gettingstarted.html) the nifti file header


### How to

#### Recommended setup

Use [conda](https://docs.conda.io/en/latest/miniconda.html) to create a new python environment.

**Standard**

```
conda create --name niix2bids
conda activate niix2bids
pip install git+https://github.com/benoitberanger/niix2bids
```

**Developer**

If you want to install in "developer" mode using the Git local repository, clone the repo before, then change the installation line :

```
cd /path/to/mydir/
git clone https://github.com/benoitberanger/niix2bids
conda create --name niix2bids
conda activate niix2bids
pip install -e niix2bids/
```

If you want to make a PR, this the recommended strategy, because you can control branching in your local clone of the repository


**NOT tested**

`pip install git+https://github.com/benoitberanger/niix2bids`  
The installation might crash because of wrong dependency management.
Creating a fresh [conda](https://docs.conda.io/en/latest/miniconda.html) environment is the recommended setup.
See above.


## Notes

`pip install niix2bids` is not possible yet.
I did not register this packaged on https://pypi.org.
