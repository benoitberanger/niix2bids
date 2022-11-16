from niix2bids import classes       # contains objects such as Volume
from niix2bids import cli           # Command Line Inputs contains the parser (it's the entry point)
from niix2bids import metadata      # some metadata, mostly for setup.py and the CLI help
from niix2bids import utils         # utility functions for the workflow.run(), so "workflow" remains readable
from niix2bids import workflow      # only contains the .run() function which is the <main> function
from niix2bids import decision_tree # siemens decision tree
